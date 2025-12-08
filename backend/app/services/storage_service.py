"""Storage Service for PopGraph.

实现图片的 S3 存储、缩略图生成和签名 URL。
当 S3 不可用时回退到 Base64 编码。
"""

import base64
import io
import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageError(Exception):
    """S3 存储错误"""
    pass


class StorageService:
    """图片存储服务
    
    支持 S3 兼容存储，当 S3 不可用时回退到 Base64。
    """
    
    def __init__(self):
        self._s3_client = None
        self._s3_available = False
        self._init_s3_client()
    
    def _init_s3_client(self):
        """初始化 S3 客户端"""
        if not settings.s3_endpoint or not settings.s3_access_key or not settings.s3_secret_key:
            logger.warning("S3 配置不完整，将使用 Base64 回退模式")
            self._s3_available = False
            return
        
        try:
            import boto3
            from botocore.config import Config
            
            self._s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                config=Config(signature_version='s3v4')
            )
            self._s3_available = True
            logger.info(f"S3 客户端初始化成功: {settings.s3_endpoint}")
        except Exception as e:
            logger.error(f"S3 客户端初始化失败: {e}")
            self._s3_available = False

    
    @property
    def is_s3_available(self) -> bool:
        """检查 S3 是否可用"""
        return self._s3_available and self._s3_client is not None
    
    def generate_thumbnail(
        self, 
        image_data: bytes, 
        max_size: Tuple[int, int] = (200, 200)
    ) -> bytes:
        """生成缩略图
        
        Args:
            image_data: 原始图片二进制数据
            max_size: 缩略图最大尺寸 (width, height)
            
        Returns:
            缩略图二进制数据 (JPEG 格式)
        """
        img = Image.open(io.BytesIO(image_data))
        
        # 转换为 RGB（处理 RGBA 等格式）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 生成缩略图（保持宽高比）
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 保存为 JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        return output.read()
    
    def _generate_key(self, user_id: str, suffix: str = "") -> str:
        """生成 S3 对象键
        
        格式: images/{user_id}/{date}/{uuid}{suffix}.jpg
        """
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())
        return f"images/{user_id}/{date_str}/{unique_id}{suffix}.jpg"
    
    async def upload_image(
        self, 
        image_data: bytes, 
        user_id: str
    ) -> Tuple[str, str]:
        """上传图片到 S3，同时生成缩略图
        
        Args:
            image_data: 图片二进制数据
            user_id: 用户 ID
            
        Returns:
            (原图 URL, 缩略图 URL) 元组
            
        Raises:
            S3StorageError: 当 S3 上传失败且无法回退时
        """
        if not self.is_s3_available:
            logger.warning("S3 不可用，使用 Base64 回退")
            return self._fallback_to_base64(image_data)
        
        try:
            # 生成缩略图
            thumbnail_data = self.generate_thumbnail(image_data)
            
            # 生成对象键
            original_key = self._generate_key(user_id)
            thumbnail_key = self._generate_key(user_id, "_thumb")
            
            # 上传原图
            self._s3_client.put_object(
                Bucket=settings.s3_bucket,
                Key=original_key,
                Body=image_data,
                ContentType='image/jpeg'
            )
            
            # 上传缩略图
            self._s3_client.put_object(
                Bucket=settings.s3_bucket,
                Key=thumbnail_key,
                Body=thumbnail_data,
                ContentType='image/jpeg'
            )
            
            # 生成 URL
            original_url = self._get_public_url(original_key)
            thumbnail_url = self._get_public_url(thumbnail_key)
            
            logger.info(f"图片上传成功: {original_key}")
            return (original_url, thumbnail_url)
            
        except Exception as e:
            logger.error(f"S3 上传失败: {e}，使用 Base64 回退")
            return self._fallback_to_base64(image_data)

    
    def _get_public_url(self, key: str) -> str:
        """获取公开访问 URL
        
        如果配置了 CDN URL，使用 CDN；否则使用 S3 endpoint。
        """
        if settings.s3_public_url:
            return f"{settings.s3_public_url.rstrip('/')}/{key}"
        return f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{key}"
    
    def _fallback_to_base64(self, image_data: bytes) -> Tuple[str, str]:
        """回退到 Base64 编码
        
        当 S3 不可用时，返回 data URL 格式的图片。
        """
        # 生成缩略图
        thumbnail_data = self.generate_thumbnail(image_data)
        
        # 编码为 Base64 data URL
        original_b64 = base64.b64encode(image_data).decode('utf-8')
        thumbnail_b64 = base64.b64encode(thumbnail_data).decode('utf-8')
        
        original_url = f"data:image/jpeg;base64,{original_b64}"
        thumbnail_url = f"data:image/jpeg;base64,{thumbnail_b64}"
        
        return (original_url, thumbnail_url)
    
    def get_signed_url(
        self, 
        key: str, 
        expires_in: int = None
    ) -> str:
        """获取带过期时间的签名 URL
        
        Args:
            key: S3 对象键
            expires_in: 过期时间（秒），默认使用配置值
            
        Returns:
            签名 URL，包含过期时间参数
            
        Raises:
            S3StorageError: 当 S3 不可用时
        """
        if not self.is_s3_available:
            raise S3StorageError("S3 服务不可用")
        
        if expires_in is None:
            expires_in = settings.s3_signed_url_expires
        
        try:
            signed_url = self._s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.s3_bucket,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return signed_url
        except Exception as e:
            logger.error(f"生成签名 URL 失败: {e}")
            raise S3StorageError(f"生成签名 URL 失败: {e}")
    
    async def delete_image(self, key: str) -> bool:
        """删除 S3 中的图片
        
        Args:
            key: S3 对象键
            
        Returns:
            是否删除成功
        """
        if not self.is_s3_available:
            logger.warning("S3 不可用，无法删除图片")
            return False
        
        try:
            self._s3_client.delete_object(
                Bucket=settings.s3_bucket,
                Key=key
            )
            logger.info(f"图片删除成功: {key}")
            return True
        except Exception as e:
            logger.error(f"删除图片失败: {e}")
            return False
    
    def extract_key_from_url(self, url: str) -> Optional[str]:
        """从 URL 中提取 S3 对象键
        
        Args:
            url: 图片 URL
            
        Returns:
            S3 对象键，如果无法提取返回 None
        """
        if url.startswith("data:"):
            # Base64 data URL，没有 key
            return None
        
        # 尝试从 CDN URL 提取
        if settings.s3_public_url and url.startswith(settings.s3_public_url):
            return url[len(settings.s3_public_url):].lstrip('/')
        
        # 尝试从 S3 endpoint URL 提取
        prefix = f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/"
        if url.startswith(prefix):
            return url[len(prefix):]
        
        return None


# 单例实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """获取存储服务实例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
