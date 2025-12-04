"""Unit tests for SceneFusionService.

This module tests the scene fusion service with specific examples
to verify product extraction and scene fusion logic.

Requirements:
- 4.1: WHEN a user uploads a product image with white background THEN the 
       PopGraph System SHALL extract and preserve the product subject accurately
- 4.2: WHEN a user specifies a target scene description THEN the PopGraph System 
       SHALL generate a new background matching the description while maintaining 
       the original product appearance
- 4.3: WHEN the PopGraph System performs scene fusion THEN the PopGraph System 
       SHALL ensure seamless integration between product and background with 
       consistent lighting and perspective
"""

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.scene_fusion_service import (
    ProductExtractor,
    ProductExtractionError,
    InvalidImageError,
    SceneFusionService,
    FeatureNotAvailableError,
    ContentBlockedError,
)
from app.models.schemas import MembershipTier, ExtractedProduct


def create_white_background_image_with_product(
    width: int = 200,
    height: int = 200,
    product_color: tuple = (255, 0, 0),  # Red product
    product_size: float = 0.3,  # Product takes 30% of image
) -> bytes:
    """创建带有商品的白底测试图像
    
    Args:
        width: 图像宽度
        height: 图像高度
        product_color: 商品颜色 (R, G, B)
        product_size: 商品占图像的比例
        
    Returns:
        PNG 格式的图像字节数据
    """
    # 创建白色背景
    img = Image.new("RGB", (width, height), (255, 255, 255))
    pixels = img.load()
    
    # 在中心绘制商品（矩形）
    product_w = int(width * product_size)
    product_h = int(height * product_size)
    start_x = (width - product_w) // 2
    start_y = (height - product_h) // 2
    
    for x in range(start_x, start_x + product_w):
        for y in range(start_y, start_y + product_h):
            pixels[x, y] = product_color
    
    # 保存为 PNG
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_pure_white_image(width: int = 200, height: int = 200) -> bytes:
    """创建纯白色图像（无商品）"""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_non_white_background_image(width: int = 200, height: int = 200) -> bytes:
    """创建非白色背景图像"""
    img = Image.new("RGB", (width, height), (100, 100, 100))  # Gray background
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestProductExtractor:
    """测试商品主体提取器"""

    def test_extract_product_from_white_background(self) -> None:
        """测试从白底图中提取商品主体
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product()
        
        result = extractor.extract(image_data)
        
        assert isinstance(result, ExtractedProduct)
        assert result.image_data is not None
        assert len(result.image_data) > 0
        assert result.mask is not None
        assert len(result.mask) > 0
        assert len(result.bounding_box) == 4

    def test_extract_product_bounding_box_is_valid(self) -> None:
        """测试提取的边界框有效
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product(
            width=200, height=200, product_size=0.3
        )
        
        result = extractor.extract(image_data)
        x, y, w, h = result.bounding_box
        
        # 边界框应该在图像范围内
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0
        assert x + w <= 200
        assert y + h <= 200

    def test_extract_product_preserves_product_pixels(self) -> None:
        """测试提取的商品图像保留了商品像素
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        product_color = (255, 0, 0)  # Red
        image_data = create_white_background_image_with_product(
            product_color=product_color
        )
        
        result = extractor.extract(image_data)
        
        # 打开提取的商品图像
        product_img = Image.open(io.BytesIO(result.image_data))
        product_array = np.array(product_img)
        
        # 检查是否有红色像素（商品）
        red_pixels = (
            (product_array[:, :, 0] == 255) &
            (product_array[:, :, 1] == 0) &
            (product_array[:, :, 2] == 0)
        )
        assert np.any(red_pixels), "商品像素应该被保留"

    def test_extract_product_makes_background_transparent(self) -> None:
        """测试提取的商品图像背景透明
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product()
        
        result = extractor.extract(image_data)
        
        # 打开提取的商品图像
        product_img = Image.open(io.BytesIO(result.image_data))
        assert product_img.mode == "RGBA", "应该是 RGBA 模式"
        
        product_array = np.array(product_img)
        
        # 检查是否有透明像素（alpha = 0）
        transparent_pixels = product_array[:, :, 3] == 0
        assert np.any(transparent_pixels), "背景应该是透明的"

    def test_extract_product_mask_is_binary(self) -> None:
        """测试生成的遮罩是二值图像"""
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product()
        
        result = extractor.extract(image_data)
        
        # 打开遮罩图像
        mask_img = Image.open(io.BytesIO(result.mask))
        mask_array = np.array(mask_img)
        
        # 遮罩应该只有 0 和 255 两个值
        unique_values = np.unique(mask_array)
        assert all(v in [0, 255] for v in unique_values), "遮罩应该是二值图像"

    def test_extract_fails_for_pure_white_image(self) -> None:
        """测试纯白图像（无商品）提取失败
        
        Requirements: 4.1 - 需要有明显的商品主体
        """
        extractor = ProductExtractor()
        image_data = create_pure_white_image()
        
        with pytest.raises(ProductExtractionError) as exc_info:
            extractor.extract(image_data)
        
        assert "未检测到" in str(exc_info.value) or "商品主体" in str(exc_info.value)

    def test_extract_fails_for_invalid_image_data(self) -> None:
        """测试无效图像数据提取失败"""
        extractor = ProductExtractor()
        invalid_data = b"not an image"
        
        with pytest.raises(InvalidImageError):
            extractor.extract(invalid_data)

    def test_extract_with_different_product_colors(self) -> None:
        """测试不同颜色商品的提取
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (128, 128, 128), # Gray
            (0, 0, 0),      # Black
        ]
        
        for color in colors:
            image_data = create_white_background_image_with_product(product_color=color)
            result = extractor.extract(image_data)
            
            assert result.image_data is not None
            assert len(result.bounding_box) == 4

    def test_extract_with_different_product_sizes(self) -> None:
        """测试不同大小商品的提取
        
        Requirements: 4.1 - 准确提取商品主体
        """
        extractor = ProductExtractor()
        sizes = [0.1, 0.3, 0.5, 0.7]
        
        for size in sizes:
            image_data = create_white_background_image_with_product(product_size=size)
            result = extractor.extract(image_data)
            
            assert result.image_data is not None
            x, y, w, h = result.bounding_box
            # 边界框大小应该与商品大小成比例
            assert w > 0 and h > 0


class TestProductExtractorRefineMask:
    """测试遮罩优化功能"""

    def test_refine_mask_returns_valid_mask(self) -> None:
        """测试遮罩优化返回有效遮罩"""
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product()
        
        result = extractor.extract(image_data)
        refined_mask = extractor.refine_mask(result.mask)
        
        assert refined_mask is not None
        assert len(refined_mask) > 0
        
        # 验证是有效的图像
        mask_img = Image.open(io.BytesIO(refined_mask))
        assert mask_img.mode == "L"

    def test_refine_mask_preserves_shape(self) -> None:
        """测试遮罩优化保持形状"""
        extractor = ProductExtractor()
        image_data = create_white_background_image_with_product()
        
        result = extractor.extract(image_data)
        refined_mask = extractor.refine_mask(result.mask)
        
        original_img = Image.open(io.BytesIO(result.mask))
        refined_img = Image.open(io.BytesIO(refined_mask))
        
        assert original_img.size == refined_img.size


class TestSceneFusionServicePermissions:
    """测试场景融合服务权限检查"""

    def test_professional_member_can_access(self) -> None:
        """测试专业会员可以访问场景融合
        
        Requirements: 7.4 - 专业会员可以使用场景融合功能
        """
        service = SceneFusionService()
        
        # 专业会员应该可以访问
        assert service._membership_service.can_access_scene_fusion(
            MembershipTier.PROFESSIONAL
        ) is True

    def test_basic_member_cannot_access(self) -> None:
        """测试基础会员无法访问场景融合
        
        Requirements: 7.4 - 只有专业会员可以使用场景融合功能
        """
        service = SceneFusionService()
        
        assert service._membership_service.can_access_scene_fusion(
            MembershipTier.BASIC
        ) is False

    def test_free_member_cannot_access(self) -> None:
        """测试免费用户无法访问场景融合
        
        Requirements: 7.4 - 只有专业会员可以使用场景融合功能
        """
        service = SceneFusionService()
        
        assert service._membership_service.can_access_scene_fusion(
            MembershipTier.FREE
        ) is False


class TestSceneFusionServiceExtractProduct:
    """测试场景融合服务的商品提取功能"""

    def test_extract_product_from_bytes(self) -> None:
        """测试从字节数据提取商品
        
        Requirements: 4.1 - 准确提取商品主体
        """
        service = SceneFusionService()
        image_data = create_white_background_image_with_product()
        
        result = service.extract_product_from_bytes(image_data)
        
        assert isinstance(result, ExtractedProduct)
        assert result.image_data is not None
        assert result.mask is not None
        assert len(result.bounding_box) == 4

    def test_extract_product_from_bytes_with_invalid_data(self) -> None:
        """测试无效数据提取失败"""
        service = SceneFusionService()
        
        with pytest.raises(InvalidImageError):
            service.extract_product_from_bytes(b"invalid data")


class TestSceneFusionServiceContentFilter:
    """测试场景融合服务的内容过滤"""

    def test_normal_scene_description_passes_filter(self) -> None:
        """测试正常场景描述通过过滤"""
        service = SceneFusionService()
        
        result = service._content_filter.check_content("现代简约客厅场景")
        assert result.is_allowed is True

    def test_sensitive_scene_description_blocked(self) -> None:
        """测试敏感场景描述被阻止
        
        Requirements: 6.1 - 敏感内容过滤
        """
        service = SceneFusionService()
        
        result = service._content_filter.check_content("赌博场景")
        assert result.is_allowed is False
        assert len(result.blocked_keywords) > 0
