"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PopGraph"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/popgraph"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Z-Image-Turbo (ModelScope API)
    modelscope_api_key: str = ""
    modelscope_base_url: str = "https://api-inference.modelscope.cn/"
    zimage_timeout: int = 30000  # milliseconds (异步API需要更长超时)

    # Storage (S3 Compatible)
    s3_bucket: str = "popgraph-images"
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"
    s3_public_url: str = ""  # CDN URL prefix, e.g., https://cdn.example.com
    s3_signed_url_expires: int = 3600  # 签名 URL 过期时间（秒）

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    refresh_token_remember_me_days: int = 30

    # SMS Service (Aliyun)
    sms_provider: str = "mock"  # "mock", "aliyun", "tencent"
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    aliyun_sms_sign_name: str = ""  # 短信签名
    aliyun_sms_template_code: str = ""  # 短信模板ID

    # SMS Service (Tencent Cloud)
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_sms_app_id: str = ""
    tencent_sms_sign_name: str = ""
    tencent_sms_template_id: str = ""

    # Payment - Alipay
    alipay_app_id: str = ""
    alipay_private_key: str = ""  # 应用私钥
    alipay_public_key: str = ""  # 支付宝公钥
    alipay_notify_url: str = ""  # 异步通知地址
    alipay_return_url: str = ""  # 同步跳转地址
    alipay_sandbox: bool = True  # 是否使用沙箱环境

    # Payment - WeChat Pay
    wechat_app_id: str = ""
    wechat_mch_id: str = ""  # 商户号
    wechat_api_key: str = ""  # API密钥
    wechat_cert_serial_no: str = ""  # 证书序列号
    wechat_private_key: str = ""  # 商户私钥
    wechat_notify_url: str = ""  # 异步通知地址

    # Payment - UnionPay
    unionpay_merchant_id: str = ""
    unionpay_cert_path: str = ""
    unionpay_cert_password: str = ""
    unionpay_notify_url: str = ""
    unionpay_return_url: str = ""
    unionpay_sandbox: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
