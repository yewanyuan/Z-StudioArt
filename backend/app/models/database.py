"""SQLAlchemy database models for PopGraph.

Requirements: 7.1, 7.2, 7.3, 7.4 - 会员与水印系统
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from app.core.config import settings
from app.models.schemas import (
    GenerationType,
    MembershipTier,
    PaymentMethod,
    PaymentStatus,
    SubscriptionPlan,
    TemplateCategory,
)


# ============================================================================
# Database Engine and Session (Lazy Initialization)
# ============================================================================

_engine = None
_async_session_local = None


def get_engine():
    """获取数据库引擎（延迟初始化）"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
        )
    return _engine


def get_async_session_maker():
    """获取异步会话工厂（延迟初始化）"""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _async_session_local


# Aliases for backward compatibility
@property
def engine():
    return get_engine()


@property
def AsyncSessionLocal():
    return get_async_session_maker()


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


# ============================================================================
# User Model
# ============================================================================

class User(Base):
    """用户模型
    
    Requirements: 7.1, 7.2, 7.3, 7.4 - 会员等级和权限管理
    Requirements: 1.1, 1.5, 2.1 - 用户认证和注册
    """
    __tablename__ = "users"

    id: str = Column(String(36), primary_key=True)
    phone: Optional[str] = Column(String(20), unique=True, nullable=True, index=True)
    email: Optional[str] = Column(String(255), unique=True, nullable=True, index=True)
    password_hash: Optional[str] = Column(String(255), nullable=True)
    membership_tier: MembershipTier = Column(
        Enum(MembershipTier),
        default=MembershipTier.FREE,
        nullable=False,
    )
    membership_expiry: Optional[datetime] = Column(DateTime, nullable=True)
    daily_usage_count: int = Column(Integer, default=0, nullable=False)
    last_usage_date: date = Column(Date, nullable=False, default=func.current_date())
    created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
    )
    updated_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    generation_records = relationship("GenerationRecord", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, email={self.email}, tier={self.membership_tier})>"


# ============================================================================
# Generation Record Model
# ============================================================================

class GenerationRecord(Base):
    """生成记录模型
    
    记录用户的每次图像生成请求和结果
    """
    __tablename__ = "generation_records"

    id: str = Column(String(36), primary_key=True)
    user_id: str = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: GenerationType = Column(
        Enum(GenerationType),
        nullable=False,
    )
    input_params: dict = Column(JSON, nullable=False)
    output_urls: list[str] = Column(JSON, nullable=False)
    processing_time_ms: int = Column(Integer, nullable=False)
    has_watermark: bool = Column(Boolean, nullable=False)
    created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="generation_records")
    images = relationship("GeneratedImageRecord", back_populates="generation_record")

    def __repr__(self) -> str:
        return f"<GenerationRecord(id={self.id}, type={self.type}, user_id={self.user_id})>"


# ============================================================================
# Generated Image Record Model
# ============================================================================

class GeneratedImageRecord(Base):
    """生成图片记录模型
    
    存储生成的图片数据
    """
    __tablename__ = "generated_images"

    id: str = Column(String(36), primary_key=True)
    generation_id: str = Column(
        String(36),
        ForeignKey("generation_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_data: bytes = Column(LargeBinary, nullable=False)  # 图片二进制数据
    width: int = Column(Integer, nullable=False)
    height: int = Column(Integer, nullable=False)
    has_watermark: bool = Column(Boolean, nullable=False)
    created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
    )

    # Relationships
    generation_record = relationship("GenerationRecord", back_populates="images")

    def __repr__(self) -> str:
        return f"<GeneratedImageRecord(id={self.id}, generation_id={self.generation_id})>"


# ============================================================================
# Template Record Model
# ============================================================================

class TemplateRecord(Base):
    """模板记录模型
    
    Requirements: 3.1, 3.2, 3.3 - 预设商业模板存储
    """
    __tablename__ = "templates"

    id: str = Column(String(36), primary_key=True)
    name: str = Column(String(100), nullable=False)
    category: TemplateCategory = Column(
        Enum(TemplateCategory),
        nullable=False,
    )
    holiday_type: Optional[str] = Column(String(50), nullable=True)
    prompt_modifiers: dict = Column(JSON, nullable=False)
    preview_url: str = Column(String(500), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
    )
    updated_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<TemplateRecord(id={self.id}, name={self.name}, category={self.category})>"


# ============================================================================
# Authentication Models
# ============================================================================

class RefreshToken(Base):
    """刷新令牌模型
    
    Requirements: 2.1, 2.3, 3.1 - Token 管理和登出
    """
    __tablename__ = "refresh_tokens"

    id: str = Column(String(36), primary_key=True)
    user_id: str = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: str = Column(String(255), nullable=False, index=True)
    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    is_revoked: bool = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class VerificationCode(Base):
    """短信验证码模型
    
    Requirements: 1.1, 1.6 - 验证码发送和验证
    """
    __tablename__ = "verification_codes"

    id: str = Column(String(36), primary_key=True)
    phone: str = Column(String(20), nullable=False, index=True)
    code: str = Column(String(6), nullable=False)
    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    is_used: bool = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<VerificationCode(id={self.id}, phone={self.phone}, used={self.is_used})>"


# ============================================================================
# Payment Models
# ============================================================================

class PaymentOrder(Base):
    """支付订单模型
    
    Requirements: 4.1, 4.5, 4.9 - 支付订单管理
    """
    __tablename__ = "payment_orders"

    id: str = Column(String(36), primary_key=True)
    user_id: str = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan: SubscriptionPlan = Column(Enum(SubscriptionPlan), nullable=False)
    method: PaymentMethod = Column(Enum(PaymentMethod), nullable=False)
    amount: int = Column(Integer, nullable=False)  # 金额（分）
    status: PaymentStatus = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    external_order_id: Optional[str] = Column(String(100), nullable=True)
    paid_at: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    updated_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder(id={self.id}, user_id={self.user_id}, status={self.status})>"


# ============================================================================
# Database Utilities
# ============================================================================

async def get_db_session():
    """获取数据库会话的依赖注入函数"""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """删除所有数据库表（仅用于测试）"""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
