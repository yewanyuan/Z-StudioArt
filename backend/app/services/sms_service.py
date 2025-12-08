"""SMS Service for PopGraph.

This module implements SMS verification code functionality including:
- Verification code generation (6-digit numeric)
- Code storage and validation
- 60-second rate limiting for code requests
- Integration with Aliyun SMS and Tencent Cloud SMS

Requirements:
- 1.3: WHEN a user submits an invalid or expired verification code THEN THE 
       Auth_Service SHALL reject the registration and return a validation error
- 1.6: WHEN a user requests a verification code THEN THE Auth_Service SHALL 
       send an SMS to the phone number and limit requests to one per 60 seconds
"""

import hashlib
import hmac
import json
import logging
import random
import string
import time
import urllib.parse
from abc import ABC, abstractmethod
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class VerificationCodeData:
    """验证码数据"""
    phone: str
    code: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False


@dataclass
class SendCodeResult:
    """发送验证码结果"""
    success: bool
    message: str
    code: Optional[str] = None  # 仅用于测试环境
    cooldown_remaining: int = 0  # 剩余冷却时间（秒）


@dataclass
class VerifyCodeResult:
    """验证码验证结果"""
    success: bool
    message: str


# ============================================================================
# SMS Provider Interface
# ============================================================================

class SMSProvider(ABC):
    """短信服务商抽象接口"""
    
    @abstractmethod
    async def send_sms(self, phone: str, code: str) -> bool:
        """发送短信验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        pass


class MockSMSProvider(SMSProvider):
    """模拟短信服务商（用于开发和测试）"""
    
    async def send_sms(self, phone: str, code: str) -> bool:
        """模拟发送短信，总是返回成功"""
        logger.info(f"[MockSMS] Sending code {code} to {phone}")
        return True


class AliyunSMSProvider(SMSProvider):
    """阿里云短信服务商
    
    使用阿里云短信服务发送验证码。
    文档: https://help.aliyun.com/document_detail/101414.html
    """
    
    API_URL = "https://dysmsapi.aliyuncs.com/"
    
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        sign_name: str,
        template_code: str,
    ):
        """初始化阿里云短信服务商
        
        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            sign_name: 短信签名
            template_code: 短信模板ID
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._sign_name = sign_name
        self._template_code = template_code
    
    def _sign(self, params: dict) -> str:
        """生成签名
        
        Args:
            params: 请求参数
            
        Returns:
            签名字符串
        """
        # 按参数名排序
        sorted_params = sorted(params.items())
        
        # 构造待签名字符串
        query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        string_to_sign = f"GET&%2F&{urllib.parse.quote(query_string, safe='')}"
        
        # 计算签名
        key = f"{self._access_key_secret}&"
        signature = hmac.new(
            key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return b64encode(signature).decode('utf-8')
    
    async def send_sms(self, phone: str, code: str) -> bool:
        """发送短信验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        # 构造请求参数
        params = {
            "AccessKeyId": self._access_key_id,
            "Action": "SendSms",
            "Format": "JSON",
            "PhoneNumbers": phone,
            "SignName": self._sign_name,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(int(time.time() * 1000)),
            "SignatureVersion": "1.0",
            "TemplateCode": self._template_code,
            "TemplateParam": json.dumps({"code": code}),
            "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Version": "2017-05-25",
        }
        
        # 添加签名
        params["Signature"] = self._sign(params)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_URL, params=params, timeout=10.0)
                result = response.json()
                
                if result.get("Code") == "OK":
                    logger.info(f"[AliyunSMS] Successfully sent code to {phone}")
                    return True
                else:
                    logger.error(
                        f"[AliyunSMS] Failed to send code to {phone}: "
                        f"{result.get('Code')} - {result.get('Message')}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[AliyunSMS] Exception sending code to {phone}: {e}")
            return False


class TencentSMSProvider(SMSProvider):
    """腾讯云短信服务商
    
    使用腾讯云短信服务发送验证码。
    文档: https://cloud.tencent.com/document/product/382/55981
    """
    
    API_URL = "https://sms.tencentcloudapi.com/"
    
    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        app_id: str,
        sign_name: str,
        template_id: str,
    ):
        """初始化腾讯云短信服务商
        
        Args:
            secret_id: 腾讯云 SecretId
            secret_key: 腾讯云 SecretKey
            app_id: 短信应用ID
            sign_name: 短信签名
            template_id: 短信模板ID
        """
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._app_id = app_id
        self._sign_name = sign_name
        self._template_id = template_id
    
    def _sign(self, timestamp: int, payload: str) -> str:
        """生成签名 (TC3-HMAC-SHA256)
        
        Args:
            timestamp: 时间戳
            payload: 请求体
            
        Returns:
            签名字符串
        """
        service = "sms"
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        
        # 步骤1: 拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json\nhost:sms.tencentcloudapi.com\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"
        )
        
        # 步骤2: 拼接待签名字符串
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
        
        # 步骤3: 计算签名
        def hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
        
        secret_date = hmac_sha256(f"TC3{self._secret_key}".encode("utf-8"), date)
        secret_service = hmac_sha256(secret_date, service)
        secret_signing = hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # 步骤4: 拼接 Authorization
        authorization = (
            f"{algorithm} Credential={self._secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        
        return authorization
    
    async def send_sms(self, phone: str, code: str) -> bool:
        """发送短信验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        timestamp = int(time.time())
        
        # 构造请求体
        payload = json.dumps({
            "SmsSdkAppId": self._app_id,
            "SignName": self._sign_name,
            "TemplateId": self._template_id,
            "TemplateParamSet": [code],
            "PhoneNumberSet": [f"+86{phone}"],
        })
        
        # 构造请求头
        headers = {
            "Content-Type": "application/json",
            "Host": "sms.tencentcloudapi.com",
            "X-TC-Action": "SendSms",
            "X-TC-Version": "2021-01-11",
            "X-TC-Timestamp": str(timestamp),
            "Authorization": self._sign(timestamp, payload),
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    content=payload,
                    timeout=10.0
                )
                result = response.json()
                
                # 检查响应
                if "Response" in result:
                    send_status = result["Response"].get("SendStatusSet", [])
                    if send_status and send_status[0].get("Code") == "Ok":
                        logger.info(f"[TencentSMS] Successfully sent code to {phone}")
                        return True
                    else:
                        error_msg = send_status[0].get("Message") if send_status else "Unknown error"
                        logger.error(f"[TencentSMS] Failed to send code to {phone}: {error_msg}")
                        return False
                else:
                    logger.error(f"[TencentSMS] Invalid response: {result}")
                    return False
        except Exception as e:
            logger.error(f"[TencentSMS] Exception sending code to {phone}: {e}")
            return False


# ============================================================================
# SMS Service
# ============================================================================

class SMSService:
    """短信验证码服务
    
    负责处理验证码的生成、存储、验证和发送频率限制。
    
    Attributes:
        CODE_LENGTH: 验证码长度（6位）
        CODE_EXPIRY_MINUTES: 验证码有效期（5分钟）
        RATE_LIMIT_SECONDS: 发送频率限制（60秒）
    """
    
    CODE_LENGTH = 6
    CODE_EXPIRY_MINUTES = 5
    RATE_LIMIT_SECONDS = 60
    
    def __init__(
        self,
        sms_provider: Optional[SMSProvider] = None,
        code_expiry_minutes: int = CODE_EXPIRY_MINUTES,
        rate_limit_seconds: int = RATE_LIMIT_SECONDS,
    ):
        """初始化短信服务
        
        Args:
            sms_provider: 短信服务商实例，默认使用 MockSMSProvider
            code_expiry_minutes: 验证码有效期（分钟）
            rate_limit_seconds: 发送频率限制（秒）
        """
        self._provider = sms_provider or MockSMSProvider()
        self._code_expiry_minutes = code_expiry_minutes
        self._rate_limit_seconds = rate_limit_seconds
        
        # 内存存储（生产环境应使用 Redis 或数据库）
        self._codes: dict[str, VerificationCodeData] = {}
        self._last_send_time: dict[str, datetime] = {}
    
    def generate_code(self) -> str:
        """生成6位数字验证码
        
        Returns:
            6位数字字符串
        """
        return ''.join(random.choices(string.digits, k=self.CODE_LENGTH))
    
    def is_rate_limited(self, phone: str, current_time: Optional[datetime] = None) -> bool:
        """检查手机号是否在冷却期内
        
        Args:
            phone: 手机号
            current_time: 当前时间（用于测试）
            
        Returns:
            True 如果在冷却期内，False 如果可以发送
            
        Requirements:
            - 1.6: 限制请求频率为每60秒一次
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        last_send = self._last_send_time.get(phone)
        if last_send is None:
            return False
            
        elapsed = (current_time - last_send).total_seconds()
        return elapsed < self._rate_limit_seconds
    
    def get_cooldown_remaining(
        self, 
        phone: str, 
        current_time: Optional[datetime] = None
    ) -> int:
        """获取剩余冷却时间（秒）
        
        Args:
            phone: 手机号
            current_time: 当前时间（用于测试）
            
        Returns:
            剩余冷却秒数，如果不在冷却期则返回0
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        last_send = self._last_send_time.get(phone)
        if last_send is None:
            return 0
            
        elapsed = (current_time - last_send).total_seconds()
        remaining = self._rate_limit_seconds - elapsed
        return max(0, int(remaining))
    
    async def send_code(
        self, 
        phone: str, 
        current_time: Optional[datetime] = None
    ) -> SendCodeResult:
        """发送验证码
        
        Args:
            phone: 手机号
            current_time: 当前时间（用于测试）
            
        Returns:
            SendCodeResult: 发送结果
            
        Requirements:
            - 1.6: 发送短信并限制请求频率为每60秒一次
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # 检查频率限制
        if self.is_rate_limited(phone, current_time):
            cooldown = self.get_cooldown_remaining(phone, current_time)
            return SendCodeResult(
                success=False,
                message=f"请求过于频繁，请在 {cooldown} 秒后重试",
                cooldown_remaining=cooldown,
            )
        
        # 生成验证码
        code = self.generate_code()
        expires_at = current_time + timedelta(minutes=self._code_expiry_minutes)
        
        # 存储验证码
        self._codes[phone] = VerificationCodeData(
            phone=phone,
            code=code,
            created_at=current_time,
            expires_at=expires_at,
            is_used=False,
        )
        
        # 记录发送时间
        self._last_send_time[phone] = current_time
        
        # 发送短信
        try:
            sent = await self._provider.send_sms(phone, code)
            if not sent:
                return SendCodeResult(
                    success=False,
                    message="短信发送失败，请稍后重试",
                )
        except Exception as e:
            return SendCodeResult(
                success=False,
                message=f"短信发送异常: {str(e)}",
            )
        
        return SendCodeResult(
            success=True,
            message="验证码已发送",
            code=code,  # 仅用于测试环境
        )
    
    def verify_code(
        self, 
        phone: str, 
        code: str, 
        current_time: Optional[datetime] = None
    ) -> VerifyCodeResult:
        """验证验证码
        
        Args:
            phone: 手机号
            code: 用户输入的验证码
            current_time: 当前时间（用于测试）
            
        Returns:
            VerifyCodeResult: 验证结果
            
        Requirements:
            - 1.3: 验证码无效或过期时拒绝并返回错误
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # 获取存储的验证码
        stored = self._codes.get(phone)
        
        # 检查验证码是否存在
        if stored is None:
            return VerifyCodeResult(
                success=False,
                message="验证码不存在，请先获取验证码",
            )
        
        # 检查验证码是否已使用
        if stored.is_used:
            return VerifyCodeResult(
                success=False,
                message="验证码已使用，请重新获取",
            )
        
        # 检查验证码是否过期
        if current_time > stored.expires_at:
            return VerifyCodeResult(
                success=False,
                message="验证码已过期，请重新获取",
            )
        
        # 检查验证码是否匹配
        if stored.code != code:
            return VerifyCodeResult(
                success=False,
                message="验证码错误",
            )
        
        # 标记验证码为已使用
        stored.is_used = True
        
        return VerifyCodeResult(
            success=True,
            message="验证成功",
        )
    
    def clear_expired_codes(self, current_time: Optional[datetime] = None) -> int:
        """清理过期的验证码
        
        Args:
            current_time: 当前时间（用于测试）
            
        Returns:
            清理的验证码数量
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        expired_phones = [
            phone for phone, data in self._codes.items()
            if current_time > data.expires_at
        ]
        
        for phone in expired_phones:
            del self._codes[phone]
        
        return len(expired_phones)
    
    def get_code_data(self, phone: str) -> Optional[VerificationCodeData]:
        """获取验证码数据（仅用于测试）
        
        Args:
            phone: 手机号
            
        Returns:
            验证码数据，如果不存在则返回 None
        """
        return self._codes.get(phone)


# ============================================================================
# Provider Factory
# ============================================================================

def create_sms_provider(provider_type: str = "mock") -> SMSProvider:
    """根据配置创建短信服务商实例
    
    Args:
        provider_type: 服务商类型 ("mock", "aliyun", "tencent")
        
    Returns:
        SMSProvider 实例
        
    Raises:
        ValueError: 如果服务商类型不支持或配置缺失
    """
    from app.core.config import settings
    
    if provider_type == "mock":
        return MockSMSProvider()
    
    elif provider_type == "aliyun":
        if not all([
            settings.aliyun_access_key_id,
            settings.aliyun_access_key_secret,
            settings.aliyun_sms_sign_name,
            settings.aliyun_sms_template_code,
        ]):
            raise ValueError(
                "Aliyun SMS configuration is incomplete. "
                "Please set ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, "
                "ALIYUN_SMS_SIGN_NAME, and ALIYUN_SMS_TEMPLATE_CODE."
            )
        return AliyunSMSProvider(
            access_key_id=settings.aliyun_access_key_id,
            access_key_secret=settings.aliyun_access_key_secret,
            sign_name=settings.aliyun_sms_sign_name,
            template_code=settings.aliyun_sms_template_code,
        )
    
    elif provider_type == "tencent":
        if not all([
            settings.tencent_secret_id,
            settings.tencent_secret_key,
            settings.tencent_sms_app_id,
            settings.tencent_sms_sign_name,
            settings.tencent_sms_template_id,
        ]):
            raise ValueError(
                "Tencent SMS configuration is incomplete. "
                "Please set TENCENT_SECRET_ID, TENCENT_SECRET_KEY, "
                "TENCENT_SMS_APP_ID, TENCENT_SMS_SIGN_NAME, and TENCENT_SMS_TEMPLATE_ID."
            )
        return TencentSMSProvider(
            secret_id=settings.tencent_secret_id,
            secret_key=settings.tencent_secret_key,
            app_id=settings.tencent_sms_app_id,
            sign_name=settings.tencent_sms_sign_name,
            template_id=settings.tencent_sms_template_id,
        )
    
    else:
        raise ValueError(f"Unsupported SMS provider type: {provider_type}")


# ============================================================================
# Global Instance
# ============================================================================

_default_service: Optional[SMSService] = None


def get_sms_service() -> SMSService:
    """获取默认的短信服务实例（单例模式）
    
    根据配置自动选择短信服务商。
    
    Returns:
        SMSService 实例
    """
    global _default_service
    if _default_service is None:
        from app.core.config import settings
        provider = create_sms_provider(settings.sms_provider)
        _default_service = SMSService(sms_provider=provider)
    return _default_service


def reset_sms_service() -> None:
    """重置短信服务实例（用于测试）"""
    global _default_service
    _default_service = None
