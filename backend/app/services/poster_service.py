"""Poster Generation Service for PopGraph.

This module implements the core poster generation functionality,
integrating PromptBuilder, ContentFilter, TemplateService, ZImageClient,
and MembershipService to provide a complete poster generation workflow.

Requirements:
- 1.1, 1.2: 支持中英文文案的海报生成
- 1.3: 确保人脸自然无变形
- 1.4: 文字自动排版避免遮挡主体
- 1.5: 商业广告风格的专业视觉质量
- 2.1: 单张生成 5 秒内返回
- 2.2: 预览模式生成 4 张变体图
- 5.1: 生成图片后上传到 S3，返回 CDN URL
- 7.1, 7.3: 根据会员等级添加水印
"""

import base64
import io
import logging
import time
import uuid
from typing import TYPE_CHECKING, Literal, Optional

from PIL import Image, ImageDraw, ImageFont

from app.clients.zimage_client import (
    ZImageTurboClient,
    calculate_image_dimensions,
)
from app.models.schemas import (
    ContentFilterResult,
    GeneratedImage,
    GenerationOptions,
    MembershipTier,
    PosterGenerationRequest,
    PosterGenerationResponse,
    PromptModifiers,
)
from app.services.content_filter import ContentFilterService, get_content_filter
from app.services.membership_service import (
    MembershipService,
    WatermarkRule,
    get_membership_service,
)
from app.services.template_service import TemplateService
from app.utils.prompt_builder import PromptBuilder

if TYPE_CHECKING:
    from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class PosterGenerationError(Exception):
    """海报生成错误基类"""
    pass


class ContentBlockedError(PosterGenerationError):
    """内容被阻止错误"""
    def __init__(self, filter_result: ContentFilterResult):
        self.filter_result = filter_result
        super().__init__(filter_result.warning_message or "内容包含敏感词")


class TemplateNotFoundError(PosterGenerationError):
    """模板未找到错误"""
    def __init__(self, template_id: str):
        self.template_id = template_id
        super().__init__(f"模板未找到: {template_id}")


class WatermarkProcessor:
    """水印处理器
    
    使用 Pillow 实现水印叠加功能。
    
    Requirements:
    - 7.1: 免费用户生成的海报需要添加水印
    - 7.3: 基础会员和专业会员生成的海报无水印
    """
    
    DEFAULT_FONT_SIZE = 36
    DEFAULT_OPACITY = 128  # 0-255, 128 = 50%
    DEFAULT_MARGIN = 20
    
    def __init__(
        self,
        font_path: Optional[str] = None,
        font_size: int = DEFAULT_FONT_SIZE,
    ):
        """初始化水印处理器
        
        Args:
            font_path: 字体文件路径，如果为 None 则使用默认字体
            font_size: 字体大小
        """
        self._font_path = font_path
        self._font_size = font_size
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """获取字体对象
        
        Args:
            size: 字体大小
            
        Returns:
            字体对象
        """
        if self._font_path:
            try:
                return ImageFont.truetype(self._font_path, size)
            except (IOError, OSError):
                pass
        # 使用默认字体
        return ImageFont.load_default()
    
    def add_watermark(
        self,
        image_data: bytes,
        watermark_rule: WatermarkRule,
    ) -> bytes:
        """为图像添加水印
        
        Args:
            image_data: 原始图像数据
            watermark_rule: 水印规则
            
        Returns:
            添加水印后的图像数据
            
        Requirements: 7.1 - 免费用户添加水印
        """
        if not watermark_rule.should_add_watermark:
            return image_data
        
        # 打开图像
        image = Image.open(io.BytesIO(image_data))
        
        # 确保图像是 RGBA 模式以支持透明度
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 创建水印层
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 获取字体
        font = self._get_font(self._font_size)
        
        # 获取水印文本
        text = watermark_rule.watermark_text or "PopGraph"
        
        # 计算文本边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算水印位置（右下角）
        x = image.width - text_width - self.DEFAULT_MARGIN
        y = image.height - text_height - self.DEFAULT_MARGIN
        
        # 计算透明度
        opacity = int(watermark_rule.watermark_opacity * 255)
        
        # 绘制水印文本（白色带透明度）
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, opacity),
        )
        
        # 合并水印层
        watermarked = Image.alpha_composite(image, watermark_layer)
        
        # 转换回 RGB 并保存
        if watermarked.mode == "RGBA":
            # 创建白色背景
            background = Image.new("RGB", watermarked.size, (255, 255, 255))
            background.paste(watermarked, mask=watermarked.split()[3])
            watermarked = background
        
        # 保存为 PNG
        output = io.BytesIO()
        watermarked.save(output, format="PNG")
        return output.getvalue()


class PosterService:
    """海报生成服务
    
    整合 PromptBuilder, ContentFilter, TemplateService, ZImageClient
    实现完整的海报生成流程。
    
    Requirements:
    - 1.1, 1.2, 1.3, 1.4, 1.5: 智能文案海报生成
    - 2.1, 2.2: 极速生成模式
    - 5.1: 生成图片后上传到 S3，返回 CDN URL
    - 7.1, 7.3: 会员水印系统
    """
    
    def __init__(
        self,
        prompt_builder: Optional[PromptBuilder] = None,
        content_filter: Optional[ContentFilterService] = None,
        template_service: Optional[TemplateService] = None,
        zimage_client: Optional[ZImageTurboClient] = None,
        membership_service: Optional[MembershipService] = None,
        watermark_processor: Optional[WatermarkProcessor] = None,
        storage_service: Optional["StorageService"] = None,
    ):
        """初始化海报生成服务
        
        Args:
            prompt_builder: Prompt 构建器
            content_filter: 内容过滤服务
            template_service: 模板服务
            zimage_client: Z-Image-Turbo 客户端
            membership_service: 会员服务
            watermark_processor: 水印处理器
            storage_service: 存储服务（用于上传图片到 S3）
        """
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._content_filter = content_filter or get_content_filter()
        self._template_service = template_service or TemplateService(self._prompt_builder)
        self._zimage_client = zimage_client or ZImageTurboClient()
        self._membership_service = membership_service or get_membership_service()
        self._watermark_processor = watermark_processor or WatermarkProcessor()
        self._storage_service = storage_service
    
    async def generate_poster(
        self,
        request: PosterGenerationRequest,
        user_tier: MembershipTier = MembershipTier.FREE,
        user_id: Optional[str] = None,
        storage_base_url: str = "/generated",
    ) -> PosterGenerationResponse:
        """生成海报
        
        完整的海报生成流程：
        1. 内容过滤检查
        2. 构建 Prompt（可选应用模板）
        3. 调用 AI 模型生成图像
        4. 根据会员等级添加水印
        5. 上传到 S3 存储（如果可用）
        6. 返回生成结果
        
        Args:
            request: 海报生成请求
            user_tier: 用户会员等级
            user_id: 用户 ID（用于存储路径）
            storage_base_url: 图像存储基础 URL
            
        Returns:
            PosterGenerationResponse: 生成结果
            
        Raises:
            ContentBlockedError: 内容包含敏感词
            TemplateNotFoundError: 指定的模板不存在
            
        Requirements:
        - 1.1, 1.2: 支持中英文文案
        - 2.1: 5 秒内返回
        - 2.2: 批量生成 4 张
        - 5.1: 生成图片后上传到 S3，返回 CDN URL
        - 7.1, 7.3: 水印规则
        """
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        
        # Step 1: 内容过滤检查
        await self._check_content(request)
        
        # Step 2: 构建 Prompt
        prompt = await self._build_prompt(request)
        
        # Step 3: 计算图像尺寸
        width, height = calculate_image_dimensions(
            request.aspect_ratio,
            custom_width=request.custom_width,
            custom_height=request.custom_height,
        )
        options = GenerationOptions(width=width, height=height)
        
        # Step 4: 调用 AI 模型生成图像
        if request.batch_size == 1:
            image_data_list = [await self._zimage_client.generate_image(prompt, options)]
        else:
            image_data_list = await self._zimage_client.generate_batch(
                prompt, request.batch_size, options
            )
        
        # Step 5: 获取水印规则
        watermark_rule = self._membership_service.get_watermark_rule(user_tier)
        
        # Step 6: 处理生成的图像（添加水印、上传到 S3）
        generated_images = []
        for i, image_data in enumerate(image_data_list):
            # 添加水印
            processed_image = self._watermark_processor.add_watermark(
                image_data.image_buffer,
                watermark_rule,
            )
            
            # 创建图像记录
            image_id = f"{request_id}-{i}"
            
            # 尝试上传到 S3，如果失败则回退到 Base64
            url, thumbnail_url, image_base64 = await self._upload_or_fallback(
                processed_image, user_id or "anonymous", image_id
            )
            
            generated_images.append(
                GeneratedImage(
                    id=image_id,
                    url=url,
                    thumbnail_url=thumbnail_url,
                    has_watermark=watermark_rule.should_add_watermark,
                    width=width,
                    height=height,
                    image_base64=image_base64,
                )
            )
        
        # 计算处理时间
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        return PosterGenerationResponse(
            request_id=request_id,
            images=generated_images,
            processing_time_ms=processing_time_ms,
        )
    
    async def _upload_or_fallback(
        self,
        image_data: bytes,
        user_id: str,
        image_id: str,
    ) -> tuple[str, str, Optional[str]]:
        """上传图片到 S3，失败时回退到 Base64
        
        Args:
            image_data: 图片二进制数据
            user_id: 用户 ID
            image_id: 图片 ID
            
        Returns:
            (url, thumbnail_url, image_base64) 元组
            - 如果 S3 上传成功，返回 CDN URL，image_base64 为 None
            - 如果 S3 不可用，返回 data URL，image_base64 为 Base64 字符串
            
        Requirements: 5.1, 5.5 - 上传到 S3，S3 不可用时回退到 Base64
        """
        # 如果没有配置存储服务，使用 Base64 回退
        if self._storage_service is None:
            logger.debug("存储服务未配置，使用 Base64 回退")
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:image/png;base64,{image_base64}"
            return data_url, data_url, image_base64
        
        try:
            # 尝试上传到 S3
            url, thumbnail_url = await self._storage_service.upload_image(
                image_data, user_id
            )
            
            # S3 上传成功，检查是否返回的是 CDN URL 还是 Base64 回退
            if url.startswith("data:"):
                # 存储服务内部已经回退到 Base64
                image_base64 = url.split(",", 1)[1] if "," in url else None
                return url, thumbnail_url, image_base64
            
            # 返回 CDN URL，不需要 Base64
            logger.info(f"图片上传成功: {url}")
            return url, thumbnail_url, None
            
        except Exception as e:
            # S3 上传失败，回退到 Base64
            logger.warning(f"S3 上传失败，使用 Base64 回退: {e}")
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:image/png;base64,{image_base64}"
            return data_url, data_url, image_base64
    
    async def _check_content(self, request: PosterGenerationRequest) -> None:
        """检查请求内容是否包含敏感词
        
        Args:
            request: 海报生成请求
            
        Raises:
            ContentBlockedError: 内容包含敏感词
            
        Requirements: 6.1 - 敏感内容过滤
        """
        # 检查场景描述
        scene_result = self._content_filter.check_content(request.scene_description)
        if not scene_result.is_allowed:
            raise ContentBlockedError(scene_result)
        
        # 检查营销文案
        text_result = self._content_filter.check_content(request.marketing_text)
        if not text_result.is_allowed:
            raise ContentBlockedError(text_result)
    
    async def _build_prompt(self, request: PosterGenerationRequest) -> str:
        """构建生成 Prompt
        
        如果指定了模板，则应用模板参数；否则使用基础 Prompt 构建。
        
        Args:
            request: 海报生成请求
            
        Returns:
            完整的 Prompt 字符串
            
        Raises:
            TemplateNotFoundError: 指定的模板不存在
            
        Requirements:
        - 1.1, 1.2, 1.4, 1.5: 文案和风格
        - 3.1, 3.2, 3.3, 3.4: 模板应用
        """
        if request.template_id:
            # 使用模板
            template = await self._template_service.get_template(request.template_id)
            if template is None:
                raise TemplateNotFoundError(request.template_id)
            
            return await self._template_service.apply_template(
                request.template_id,
                request,
            )
        else:
            # 不使用模板，直接构建 Prompt
            return self._prompt_builder.build_poster_prompt(request)
    
    async def generate_poster_with_storage(
        self,
        request: PosterGenerationRequest,
        user_tier: MembershipTier = MembershipTier.FREE,
        storage_service: Optional[object] = None,
    ) -> tuple[PosterGenerationResponse, list[bytes]]:
        """生成海报并返回图像数据
        
        与 generate_poster 类似，但同时返回处理后的图像数据，
        方便调用方进行存储。
        
        Args:
            request: 海报生成请求
            user_tier: 用户会员等级
            storage_service: 可选的存储服务
            
        Returns:
            (PosterGenerationResponse, list[bytes]): 响应和图像数据列表
        """
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        
        # 内容过滤检查
        await self._check_content(request)
        
        # 构建 Prompt
        prompt = await self._build_prompt(request)
        
        # 计算图像尺寸
        width, height = calculate_image_dimensions(
            request.aspect_ratio,
            custom_width=request.custom_width,
            custom_height=request.custom_height,
        )
        options = GenerationOptions(width=width, height=height)
        
        # 调用 AI 模型生成图像
        if request.batch_size == 1:
            image_data_list = [await self._zimage_client.generate_image(prompt, options)]
        else:
            image_data_list = await self._zimage_client.generate_batch(
                prompt, request.batch_size, options
            )
        
        # 获取水印规则
        watermark_rule = self._membership_service.get_watermark_rule(user_tier)
        
        # 处理生成的图像
        generated_images = []
        processed_image_data = []
        
        for i, image_data in enumerate(image_data_list):
            # 添加水印
            processed_image = self._watermark_processor.add_watermark(
                image_data.image_buffer,
                watermark_rule,
            )
            processed_image_data.append(processed_image)
            
            # 创建图像记录
            image_id = f"{request_id}-{i}"
            generated_images.append(
                GeneratedImage(
                    id=image_id,
                    url=f"/generated/{image_id}.png",
                    thumbnail_url=f"/generated/{image_id}_thumb.png",
                    has_watermark=watermark_rule.should_add_watermark,
                    width=width,
                    height=height,
                )
            )
        
        # 计算处理时间
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        response = PosterGenerationResponse(
            request_id=request_id,
            images=generated_images,
            processing_time_ms=processing_time_ms,
        )
        
        return response, processed_image_data


# 创建默认的全局实例
_default_service: Optional[PosterService] = None


def get_poster_service() -> PosterService:
    """获取默认的海报生成服务实例（单例模式）
    
    Returns:
        PosterService 实例
    """
    global _default_service
    if _default_service is None:
        # 延迟导入以避免循环依赖
        from app.services.storage_service import get_storage_service
        _default_service = PosterService(
            storage_service=get_storage_service()
        )
    return _default_service
