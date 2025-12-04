"""Pydantic schemas for PopGraph API."""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class MembershipTier(str, Enum):
    """用户会员等级枚举"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"


class TemplateCategory(str, Enum):
    """模板分类枚举"""
    PROMOTIONAL = "promotional"  # 促销类
    PREMIUM = "premium"          # 高级类
    HOLIDAY = "holiday"          # 节日类


class HolidayType(str, Enum):
    """节日类型枚举"""
    SPRING_FESTIVAL = "spring_festival"  # 春节
    VALENTINES = "valentines"            # 情人节
    DOUBLE_ELEVEN = "double_eleven"      # 双十一


class GenerationType(str, Enum):
    """生成类型枚举"""
    POSTER = "poster"
    SCENE_FUSION = "scene_fusion"


# ============================================================================
# Poster Generation Schemas
# ============================================================================

class PosterGenerationRequest(BaseModel):
    """海报生成请求 Schema
    
    Requirements: 1.1, 1.2 - 支持中英文文案输入
    """
    scene_description: str = Field(..., description="画面描述")
    marketing_text: str = Field(..., description="指定文案")
    language: Literal["zh", "en"] = Field(..., description="语言")
    template_id: Optional[str] = Field(None, description="可选模板ID")
    aspect_ratio: str = Field(..., description="输出尺寸比例 (支持 1:1, 9:16, 16:9, custom)")
    custom_width: Optional[int] = Field(None, description="自定义宽度 (仅当 aspect_ratio 为 custom 时有效)")
    custom_height: Optional[int] = Field(None, description="自定义高度 (仅当 aspect_ratio 为 custom 时有效)")
    batch_size: Literal[1, 4] = Field(1, description="生成数量")


class GeneratedImage(BaseModel):
    """生成的图像信息 Schema"""
    id: str = Field(..., description="图像唯一标识")
    url: str = Field(..., description="图像URL")
    thumbnail_url: str = Field(..., description="缩略图URL")
    has_watermark: bool = Field(..., description="是否有水印")
    width: int = Field(..., description="图像宽度")
    height: int = Field(..., description="图像高度")
    image_base64: Optional[str] = Field(None, description="图像Base64数据")


class PosterGenerationResponse(BaseModel):
    """海报生成响应 Schema"""
    request_id: str = Field(..., description="请求唯一标识")
    images: list[GeneratedImage] = Field(..., description="生成的图像列表")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")


# ============================================================================
# Template Schemas
# ============================================================================

class PromptModifiers(BaseModel):
    """Prompt 修饰参数 Schema
    
    Requirements: 3.1, 3.2, 3.3 - 模板参数定义
    """
    style_keywords: list[str] = Field(..., description="风格关键词")
    color_scheme: str = Field(..., description="配色方案")
    layout_hints: str = Field(..., description="排版提示")
    font_style: str = Field(..., description="字体风格")


class Template(BaseModel):
    """模板 Schema
    
    Requirements: 3.1, 3.2, 3.3 - 预设商业模板
    """
    id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    category: TemplateCategory = Field(..., description="模板分类")
    holiday_type: Optional[HolidayType] = Field(None, description="节日类型(仅节日模板)")
    prompt_modifiers: PromptModifiers = Field(..., description="Prompt修饰参数")
    preview_url: str = Field(..., description="预览图URL")


# ============================================================================
# Content Filter Schemas
# ============================================================================

class ContentFilterResult(BaseModel):
    """内容过滤结果 Schema
    
    Requirements: 6.1 - 敏感内容过滤
    """
    is_allowed: bool = Field(..., description="是否允许")
    blocked_keywords: list[str] = Field(default_factory=list, description="被阻止的关键词")
    warning_message: Optional[str] = Field(None, description="警告消息")


# ============================================================================
# Rate Limit Schemas
# ============================================================================

class RateLimitResult(BaseModel):
    """限流结果 Schema
    
    Requirements: 7.2 - 免费用户每日限额
    """
    allowed: bool = Field(..., description="是否允许")
    remaining_quota: int = Field(..., description="剩余配额")
    reset_time: Optional[datetime] = Field(None, description="配额重置时间")


# ============================================================================
# Scene Fusion Schemas
# ============================================================================

class SceneFusionRequest(BaseModel):
    """场景融合请求 Schema
    
    Requirements: 4.1, 4.2, 4.3 - 商品图场景融合
    """
    product_image_url: str = Field(..., description="商品白底图URL")
    target_scene: str = Field(..., description="目标场景描述")
    aspect_ratio: str = Field(..., description="输出尺寸比例 (支持 1:1, 9:16, 16:9, custom)")
    custom_width: Optional[int] = Field(None, description="自定义宽度")
    custom_height: Optional[int] = Field(None, description="自定义高度")


class ExtractedProduct(BaseModel):
    """提取的商品信息 Schema"""
    image_data: bytes = Field(..., description="商品图像数据")
    mask: bytes = Field(..., description="商品遮罩")
    bounding_box: tuple[int, int, int, int] = Field(..., description="边界框(x, y, w, h)")


class SceneFusionResponse(BaseModel):
    """场景融合响应 Schema"""
    request_id: str = Field(..., description="请求唯一标识")
    fused_image_url: str = Field(..., description="融合后图像URL")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")
    image_base64: Optional[str] = Field(None, description="图像Base64数据")


# ============================================================================
# Z-Image-Turbo Client Schemas
# ============================================================================

class GenerationOptions(BaseModel):
    """图像生成选项 Schema"""
    width: int = Field(..., description="图像宽度")
    height: int = Field(..., description="图像高度")
    seed: Optional[int] = Field(None, description="随机种子")
    guidance_scale: Optional[float] = Field(None, description="引导比例")


class GeneratedImageData(BaseModel):
    """生成的图像数据 Schema"""
    image_buffer: bytes = Field(..., description="图像二进制数据")
    generation_time_ms: int = Field(..., description="生成时间(毫秒)")
    model_version: str = Field(..., description="模型版本")


# ============================================================================
# Rate Limit Configuration
# ============================================================================

RATE_LIMIT_CONFIG: dict[MembershipTier, dict] = {
    MembershipTier.FREE: {"daily_limit": 5, "priority": "low"},
    MembershipTier.BASIC: {"daily_limit": 100, "priority": "normal"},
    MembershipTier.PROFESSIONAL: {"daily_limit": -1, "priority": "high"},  # -1 表示无限
}
