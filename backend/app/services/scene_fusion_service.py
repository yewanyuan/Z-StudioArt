"""Scene Fusion Service for PopGraph.

This module implements the scene fusion functionality that allows users
to upload product images with white backgrounds and generate new scene
backgrounds while preserving the product appearance.

Requirements:
- 4.1: WHEN a user uploads a product image with white background THEN the 
       PopGraph System SHALL extract and preserve the product subject accurately
- 4.2: WHEN a user specifies a target scene description THEN the PopGraph System 
       SHALL generate a new background matching the description while maintaining 
       the original product appearance
- 4.3: WHEN the PopGraph System performs scene fusion THEN the PopGraph System 
       SHALL ensure seamless integration between product and background with 
       consistent lighting and perspective
- 5.1: 生成图片后上传到 S3，返回 CDN URL
"""

import base64
import io
import logging
import time
import uuid
from typing import TYPE_CHECKING, Literal, Optional

import httpx
from PIL import Image
import numpy as np

from app.clients.zimage_client import (
    ZImageTurboClient,
    calculate_image_dimensions,
)
from app.core.config import settings
from app.models.schemas import (
    ExtractedProduct,
    GenerationOptions,
    MembershipTier,
    SceneFusionRequest,
    SceneFusionResponse,
)
from app.services.content_filter import ContentFilterService, get_content_filter
from app.services.membership_service import (
    Feature,
    MembershipService,
    get_membership_service,
)
from app.utils.prompt_builder import PromptBuilder

if TYPE_CHECKING:
    from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class SceneFusionError(Exception):
    """场景融合错误基类"""
    pass


class ProductExtractionError(SceneFusionError):
    """商品提取错误"""
    def __init__(self, message: str = "无法从图像中提取商品主体"):
        super().__init__(message)


class InvalidImageError(SceneFusionError):
    """无效图像错误"""
    def __init__(self, message: str = "图像格式无效或无法处理"):
        super().__init__(message)


class FeatureNotAvailableError(SceneFusionError):
    """功能不可用错误"""
    def __init__(self, required_tier: MembershipTier = MembershipTier.PROFESSIONAL):
        self.required_tier = required_tier
        super().__init__(f"场景融合功能需要{required_tier.value}会员")


class ContentBlockedError(SceneFusionError):
    """内容被阻止错误"""
    def __init__(self, blocked_keywords: list[str]):
        self.blocked_keywords = blocked_keywords
        super().__init__(f"内容包含敏感词: {', '.join(blocked_keywords)}")


class ProductExtractor:
    """商品主体提取器
    
    从白底商品图中提取商品主体，生成遮罩和边界框。
    
    Requirements:
    - 4.1: 准确提取和保留商品主体
    """
    
    # 白色背景阈值（RGB 值接近 255 视为白色）
    WHITE_THRESHOLD = 240
    
    # 最小商品区域比例（商品至少占图像的这个比例）
    MIN_PRODUCT_RATIO = 0.01
    
    def extract(self, image_data: bytes) -> ExtractedProduct:
        """从白底图中提取商品主体
        
        使用颜色阈值分割方法识别白色背景，
        将非白色区域作为商品主体提取出来。
        
        Args:
            image_data: 原始图像数据（PNG/JPEG 格式）
            
        Returns:
            ExtractedProduct: 包含商品图像、遮罩和边界框
            
        Raises:
            InvalidImageError: 图像格式无效
            ProductExtractionError: 无法提取商品主体
            
        Requirements: 4.1 - 准确提取商品主体
        """
        try:
            # 打开图像
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise InvalidImageError(f"无法打开图像: {str(e)}")
        
        # 转换为 RGBA 模式
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 转换为 numpy 数组进行处理
        img_array = np.array(image)
        
        # 创建遮罩：非白色区域为商品
        # 检查 RGB 通道是否都接近白色
        is_white = (
            (img_array[:, :, 0] >= self.WHITE_THRESHOLD) &
            (img_array[:, :, 1] >= self.WHITE_THRESHOLD) &
            (img_array[:, :, 2] >= self.WHITE_THRESHOLD)
        )
        
        # 商品遮罩（非白色区域）
        product_mask = ~is_white
        
        # 检查是否提取到了商品
        product_pixels = np.sum(product_mask)
        total_pixels = product_mask.size
        
        if product_pixels / total_pixels < self.MIN_PRODUCT_RATIO:
            raise ProductExtractionError("图像中未检测到明显的商品主体，请确保使用白底商品图")
        
        # 计算边界框
        rows = np.any(product_mask, axis=1)
        cols = np.any(product_mask, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            raise ProductExtractionError("无法确定商品边界")
        
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        # 边界框 (x, y, width, height)
        bounding_box = (
            int(x_min),
            int(y_min),
            int(x_max - x_min + 1),
            int(y_max - y_min + 1)
        )
        
        # 创建带透明背景的商品图像
        product_image = img_array.copy()
        # 将白色背景设为透明
        product_image[is_white, 3] = 0
        
        # 转换回 PIL Image 并保存为 bytes
        product_pil = Image.fromarray(product_image, mode="RGBA")
        product_buffer = io.BytesIO()
        product_pil.save(product_buffer, format="PNG")
        product_bytes = product_buffer.getvalue()
        
        # 创建遮罩图像（黑白）
        mask_image = Image.fromarray(
            (product_mask * 255).astype(np.uint8),
            mode="L"
        )
        mask_buffer = io.BytesIO()
        mask_image.save(mask_buffer, format="PNG")
        mask_bytes = mask_buffer.getvalue()
        
        return ExtractedProduct(
            image_data=product_bytes,
            mask=mask_bytes,
            bounding_box=bounding_box
        )
    
    def refine_mask(
        self,
        mask: bytes,
        dilation_iterations: int = 2,
        erosion_iterations: int = 1
    ) -> bytes:
        """优化遮罩边缘
        
        使用形态学操作平滑遮罩边缘，减少锯齿。
        
        Args:
            mask: 原始遮罩数据
            dilation_iterations: 膨胀迭代次数
            erosion_iterations: 腐蚀迭代次数
            
        Returns:
            优化后的遮罩数据
        """
        # 打开遮罩图像
        mask_image = Image.open(io.BytesIO(mask))
        mask_array = np.array(mask_image)
        
        # 简单的形态学操作（不依赖 OpenCV）
        # 使用 PIL 的滤镜进行近似处理
        from PIL import ImageFilter
        
        # 轻微模糊以平滑边缘
        mask_pil = Image.fromarray(mask_array, mode="L")
        mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=1))
        
        # 重新二值化
        mask_array = np.array(mask_pil)
        mask_array = (mask_array > 127).astype(np.uint8) * 255
        
        # 保存结果
        result_image = Image.fromarray(mask_array, mode="L")
        result_buffer = io.BytesIO()
        result_image.save(result_buffer, format="PNG")
        
        return result_buffer.getvalue()


class SceneFusionService:
    """场景融合服务
    
    将商品白底图与新场景背景融合，生成专业的商品场景图。
    
    Requirements:
    - 4.1: 准确提取商品主体
    - 4.2: 生成匹配描述的新背景
    - 4.3: 确保无缝融合，光照和透视一致
    - 5.1: 生成图片后上传到 S3，返回 CDN URL
    """
    
    def __init__(
        self,
        prompt_builder: Optional[PromptBuilder] = None,
        content_filter: Optional[ContentFilterService] = None,
        zimage_client: Optional[ZImageTurboClient] = None,
        membership_service: Optional[MembershipService] = None,
        product_extractor: Optional[ProductExtractor] = None,
        storage_service: Optional["StorageService"] = None,
    ):
        """初始化场景融合服务
        
        Args:
            prompt_builder: Prompt 构建器
            content_filter: 内容过滤服务
            zimage_client: Z-Image-Turbo 客户端
            membership_service: 会员服务
            product_extractor: 商品提取器
            storage_service: 存储服务（用于上传图片到 S3）
        """
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._content_filter = content_filter or get_content_filter()
        self._zimage_client = zimage_client or ZImageTurboClient()
        self._membership_service = membership_service or get_membership_service()
        self._product_extractor = product_extractor or ProductExtractor()
        self._storage_service = storage_service
    
    async def extract_product(self, image_url: str) -> ExtractedProduct:
        """从 URL 加载图像并提取商品主体
        
        Args:
            image_url: 商品白底图 URL（支持 http/https URL 或 data URL）
            
        Returns:
            ExtractedProduct: 提取的商品信息
            
        Raises:
            InvalidImageError: 无法加载或处理图像
            ProductExtractionError: 无法提取商品主体
            
        Requirements: 4.1 - 准确提取商品主体
        """
        import base64
        
        # 检查是否是 data URL
        if image_url.startswith("data:"):
            try:
                # 解析 data URL: data:image/png;base64,xxxxx
                header, data = image_url.split(",", 1)
                image_data = base64.b64decode(data)
            except Exception as e:
                raise InvalidImageError(f"无法解析 data URL: {str(e)}")
        else:
            # 下载图像
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_data = response.content
            except httpx.HTTPError as e:
                raise InvalidImageError(f"无法下载图像: {str(e)}")
        
        # 提取商品主体
        return self._product_extractor.extract(image_data)
    
    def extract_product_from_bytes(self, image_data: bytes) -> ExtractedProduct:
        """从字节数据提取商品主体
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            ExtractedProduct: 提取的商品信息
            
        Requirements: 4.1 - 准确提取商品主体
        """
        return self._product_extractor.extract(image_data)
    
    async def fuse_with_scene(
        self,
        product: ExtractedProduct,
        scene: str,
        aspect_ratio: Literal["1:1", "9:16", "16:9"] = "1:1",
        user_id: Optional[str] = None,
    ) -> SceneFusionResponse:
        """将商品与场景融合
        
        生成新的场景背景，并将商品无缝融合到场景中。
        
        Args:
            product: 提取的商品信息
            scene: 目标场景描述
            aspect_ratio: 输出尺寸比例
            user_id: 用户 ID（用于存储路径）
            
        Returns:
            SceneFusionResponse: 融合结果
            
        Requirements:
        - 4.2: 生成匹配描述的新背景
        - 4.3: 确保无缝融合
        - 5.1: 生成图片后上传到 S3，返回 CDN URL
        """
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        
        # 构建场景融合 prompt
        prompt = self._prompt_builder.build_scene_fusion_prompt(
            scene=scene,
            product_description="product from uploaded image"
        )
        
        # 计算输出尺寸
        width, height = calculate_image_dimensions(aspect_ratio)
        options = GenerationOptions(width=width, height=height)
        
        # 使用图生图模式进行场景融合
        result = await self._zimage_client.image_to_image(
            source_image=product.image_data,
            prompt=prompt,
            options=options
        )
        
        # 计算处理时间
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        # 尝试上传到 S3，如果失败则回退到 Base64
        fused_image_url, _, image_base64 = await self._upload_or_fallback(
            result.image_buffer, user_id or "anonymous", request_id
        )
        
        return SceneFusionResponse(
            request_id=request_id,
            fused_image_url=fused_image_url,
            processing_time_ms=processing_time_ms,
            image_base64=image_base64
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
    
    async def process_scene_fusion(
        self,
        request: SceneFusionRequest,
        user_tier: MembershipTier = MembershipTier.PROFESSIONAL,
        user_id: Optional[str] = None,
    ) -> SceneFusionResponse:
        """处理完整的场景融合请求
        
        完整的场景融合流程：
        1. 检查用户权限
        2. 检查内容安全
        3. 提取商品主体
        4. 生成场景融合图像
        5. 上传到 S3 存储（如果可用）
        
        Args:
            request: 场景融合请求
            user_tier: 用户会员等级
            user_id: 用户 ID（用于存储路径）
            
        Returns:
            SceneFusionResponse: 融合结果
            
        Raises:
            FeatureNotAvailableError: 用户无权使用此功能
            ContentBlockedError: 内容包含敏感词
            InvalidImageError: 图像无效
            ProductExtractionError: 无法提取商品
            
        Requirements:
        - 4.1, 4.2, 4.3: 场景融合功能
        - 5.1: 生成图片后上传到 S3，返回 CDN URL
        - 7.4: 专业会员权限检查
        """
        # Step 1: 检查用户权限
        if not self._membership_service.can_access_scene_fusion(user_tier):
            raise FeatureNotAvailableError(MembershipTier.PROFESSIONAL)
        
        # Step 2: 检查内容安全
        filter_result = self._content_filter.check_content(request.target_scene)
        if not filter_result.is_allowed:
            raise ContentBlockedError(filter_result.blocked_keywords)
        
        # Step 3: 提取商品主体
        product = await self.extract_product(request.product_image_url)
        
        # Step 4: 执行场景融合（包含 S3 上传）
        return await self.fuse_with_scene(
            product=product,
            scene=request.target_scene,
            aspect_ratio=request.aspect_ratio,
            user_id=user_id,
        )
    
    async def process_scene_fusion_with_bytes(
        self,
        image_data: bytes,
        target_scene: str,
        aspect_ratio: Literal["1:1", "9:16", "16:9"],
        user_tier: MembershipTier = MembershipTier.PROFESSIONAL,
        user_id: Optional[str] = None,
    ) -> tuple[SceneFusionResponse, bytes]:
        """处理场景融合并返回图像数据
        
        与 process_scene_fusion 类似，但接受字节数据并返回融合后的图像。
        
        Args:
            image_data: 商品图像字节数据
            target_scene: 目标场景描述
            aspect_ratio: 输出尺寸比例
            user_tier: 用户会员等级
            user_id: 用户 ID（用于存储路径）
            
        Returns:
            (SceneFusionResponse, bytes): 响应和融合后的图像数据
            
        Requirements:
        - 4.1, 4.2, 4.3: 场景融合功能
        - 5.1: 生成图片后上传到 S3，返回 CDN URL
        """
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        
        # 检查用户权限
        if not self._membership_service.can_access_scene_fusion(user_tier):
            raise FeatureNotAvailableError(MembershipTier.PROFESSIONAL)
        
        # 检查内容安全
        filter_result = self._content_filter.check_content(target_scene)
        if not filter_result.is_allowed:
            raise ContentBlockedError(filter_result.blocked_keywords)
        
        # 提取商品主体
        product = self._product_extractor.extract(image_data)
        
        # 构建 prompt
        prompt = self._prompt_builder.build_scene_fusion_prompt(
            scene=target_scene,
            product_description="product from uploaded image"
        )
        
        # 计算输出尺寸
        width, height = calculate_image_dimensions(aspect_ratio)
        options = GenerationOptions(width=width, height=height)
        
        # 执行图生图
        result = await self._zimage_client.image_to_image(
            source_image=product.image_data,
            prompt=prompt,
            options=options
        )
        
        # 计算处理时间
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        # 尝试上传到 S3，如果失败则回退到 Base64
        fused_image_url, _, image_base64 = await self._upload_or_fallback(
            result.image_buffer, user_id or "anonymous", request_id
        )
        
        response = SceneFusionResponse(
            request_id=request_id,
            fused_image_url=fused_image_url,
            processing_time_ms=processing_time_ms,
            image_base64=image_base64,
        )
        
        return response, result.image_buffer


# 创建默认的全局实例
_default_service: Optional[SceneFusionService] = None


def get_scene_fusion_service() -> SceneFusionService:
    """获取默认的场景融合服务实例（单例模式）
    
    Returns:
        SceneFusionService 实例
    """
    global _default_service
    if _default_service is None:
        # 延迟导入以避免循环依赖
        from app.services.storage_service import get_storage_service
        _default_service = SceneFusionService(
            storage_service=get_storage_service()
        )
    return _default_service
