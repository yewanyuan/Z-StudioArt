"""Integration tests for poster generation workflow.

Tests the complete poster generation flow including:
- Content filtering
- Template application
- Image generation
- Watermark processing
- Error handling

Requirements: 1.1, 1.2, 2.1, 2.2
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.models.schemas import (
    GeneratedImageData,
    GenerationOptions,
    MembershipTier,
    PosterGenerationRequest,
    PromptModifiers,
    Template,
    TemplateCategory,
)
from app.services.content_filter import ContentFilterService
from app.services.membership_service import MembershipService
from app.services.poster_service import (
    ContentBlockedError,
    PosterService,
    TemplateNotFoundError,
    WatermarkProcessor,
)
from app.services.template_service import TemplateService
from app.utils.prompt_builder import PromptBuilder


# ============================================================================
# Test Fixtures
# ============================================================================

def create_test_image(width: int = 100, height: int = 100) -> bytes:
    """Create a test image for mocking AI model responses."""
    img = Image.new("RGB", (width, height), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def mock_zimage_client():
    """Create a mock Z-Image-Turbo client."""
    client = AsyncMock()
    
    # Mock single image generation
    async def mock_generate_image(prompt, options):
        return GeneratedImageData(
            image_buffer=create_test_image(options.width, options.height),
            generation_time_ms=100,
            model_version="test-v1",
        )
    
    # Mock batch generation
    async def mock_generate_batch(prompt, count, options):
        return [
            GeneratedImageData(
                image_buffer=create_test_image(options.width, options.height),
                generation_time_ms=100 + i * 10,
                model_version="test-v1",
            )
            for i in range(count)
        ]
    
    client.generate_image = mock_generate_image
    client.generate_batch = mock_generate_batch
    return client


@pytest.fixture
def content_filter():
    """Create a content filter with test blocklist."""
    return ContentFilterService(blocklist={"敏感词", "违禁内容", "banned"})


@pytest.fixture
def prompt_builder():
    """Create a prompt builder instance."""
    return PromptBuilder()


@pytest.fixture
def template_service(prompt_builder):
    """Create a template service instance."""
    return TemplateService(prompt_builder)


@pytest.fixture
def membership_service():
    """Create a membership service instance."""
    return MembershipService()


@pytest.fixture
def watermark_processor():
    """Create a watermark processor instance."""
    return WatermarkProcessor()


@pytest.fixture
def poster_service(
    prompt_builder,
    content_filter,
    template_service,
    mock_zimage_client,
    membership_service,
    watermark_processor,
):
    """Create a poster service with all dependencies."""
    return PosterService(
        prompt_builder=prompt_builder,
        content_filter=content_filter,
        template_service=template_service,
        zimage_client=mock_zimage_client,
        membership_service=membership_service,
        watermark_processor=watermark_processor,
    )


# ============================================================================
# Test: Complete Poster Generation Flow
# ============================================================================

class TestPosterGenerationFlow:
    """Test complete poster generation workflow."""

    @pytest.mark.asyncio
    async def test_generate_single_poster_chinese(self, poster_service):
        """Test single poster generation with Chinese text.
        
        Requirements: 1.1 - Chinese text rendering
        """
        request = PosterGenerationRequest(
            scene_description="现代简约风格的办公桌",
            marketing_text="限时特惠 立减50%",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert response.request_id is not None
        assert len(response.images) == 1
        assert response.processing_time_ms >= 0
        
        image = response.images[0]
        assert image.width == 1024
        assert image.height == 1024

    @pytest.mark.asyncio
    async def test_generate_single_poster_english(self, poster_service):
        """Test single poster generation with English text.
        
        Requirements: 1.2 - English text rendering
        """
        request = PosterGenerationRequest(
            scene_description="Modern minimalist office desk",
            marketing_text="Limited Time Offer - 50% OFF",
            language="en",
            aspect_ratio="16:9",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert response.request_id is not None
        assert len(response.images) == 1
        
        image = response.images[0]
        assert image.width == 1024
        assert image.height == 576  # 16:9 ratio

    @pytest.mark.asyncio
    async def test_generate_batch_posters(self, poster_service):
        """Test batch poster generation (preview mode).
        
        Requirements: 2.2 - Generate 4 variant posters
        """
        request = PosterGenerationRequest(
            scene_description="时尚服装展示",
            marketing_text="新品上市",
            language="zh",
            aspect_ratio="9:16",
            batch_size=4,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert len(response.images) == 4
        
        # Verify all images have correct dimensions
        for image in response.images:
            assert image.width == 576  # 9:16 ratio
            assert image.height == 1024


# ============================================================================
# Test: Watermark Processing
# ============================================================================

class TestWatermarkProcessing:
    """Test watermark rules based on membership tier."""

    @pytest.mark.asyncio
    async def test_free_user_has_watermark(self, poster_service):
        """Test that free users get watermarked images.
        
        Requirements: 7.1 - Free tier watermark
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="优惠促销",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(
            request, user_tier=MembershipTier.FREE
        )
        
        assert response.images[0].has_watermark is True

    @pytest.mark.asyncio
    async def test_basic_member_no_watermark(self, poster_service):
        """Test that basic members get images without watermark.
        
        Requirements: 7.3 - Basic member no watermark
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="优惠促销",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(
            request, user_tier=MembershipTier.BASIC
        )
        
        assert response.images[0].has_watermark is False

    @pytest.mark.asyncio
    async def test_professional_member_no_watermark(self, poster_service):
        """Test that professional members get images without watermark.
        
        Requirements: 7.3 - Professional member no watermark
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="优惠促销",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(
            request, user_tier=MembershipTier.PROFESSIONAL
        )
        
        assert response.images[0].has_watermark is False


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in poster generation."""

    @pytest.mark.asyncio
    async def test_content_blocked_scene_description(self, poster_service):
        """Test that sensitive content in scene description is blocked.
        
        Requirements: 6.1 - Content filtering
        """
        request = PosterGenerationRequest(
            scene_description="包含敏感词的描述",
            marketing_text="正常文案",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        with pytest.raises(ContentBlockedError) as exc_info:
            await poster_service.generate_poster(request)
        
        assert "敏感词" in exc_info.value.filter_result.blocked_keywords

    @pytest.mark.asyncio
    async def test_content_blocked_marketing_text(self, poster_service):
        """Test that sensitive content in marketing text is blocked.
        
        Requirements: 6.1 - Content filtering
        """
        request = PosterGenerationRequest(
            scene_description="正常场景描述",
            marketing_text="包含违禁内容的文案",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        with pytest.raises(ContentBlockedError) as exc_info:
            await poster_service.generate_poster(request)
        
        assert "违禁内容" in exc_info.value.filter_result.blocked_keywords

    @pytest.mark.asyncio
    async def test_template_not_found(self, poster_service):
        """Test error when template ID is invalid."""
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="优惠促销",
            language="zh",
            template_id="non-existent-template",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        with pytest.raises(TemplateNotFoundError) as exc_info:
            await poster_service.generate_poster(request)
        
        assert "non-existent-template" in str(exc_info.value)


# ============================================================================
# Test: Template Application
# ============================================================================

class TestTemplateApplication:
    """Test template application in poster generation."""

    @pytest.mark.asyncio
    async def test_generate_with_promotional_template(self, poster_service):
        """Test poster generation with promotional template.
        
        Requirements: 3.1 - Promotional template
        """
        request = PosterGenerationRequest(
            scene_description="商品展示",
            marketing_text="限时抢购",
            language="zh",
            template_id="promo-sale-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert response.request_id is not None
        assert len(response.images) == 1

    @pytest.mark.asyncio
    async def test_generate_with_premium_template(self, poster_service):
        """Test poster generation with premium template.
        
        Requirements: 3.2 - Premium template
        """
        request = PosterGenerationRequest(
            scene_description="高端产品",
            marketing_text="尊享品质",
            language="zh",
            template_id="premium-minimal-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert response.request_id is not None
        assert len(response.images) == 1

    @pytest.mark.asyncio
    async def test_generate_with_holiday_template(self, poster_service):
        """Test poster generation with holiday template.
        
        Requirements: 3.3 - Holiday template
        """
        request = PosterGenerationRequest(
            scene_description="节日促销",
            marketing_text="新春特惠",
            language="zh",
            template_id="holiday-spring-01",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        
        assert response.request_id is not None
        assert len(response.images) == 1


# ============================================================================
# Test: Aspect Ratio Handling
# ============================================================================

class TestAspectRatioHandling:
    """Test different aspect ratio outputs."""

    @pytest.mark.asyncio
    async def test_square_aspect_ratio(self, poster_service):
        """Test 1:1 aspect ratio output.
        
        Requirements: 5.1 - Square format
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="促销",
            language="zh",
            aspect_ratio="1:1",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        image = response.images[0]
        
        assert image.width == image.height

    @pytest.mark.asyncio
    async def test_mobile_poster_aspect_ratio(self, poster_service):
        """Test 9:16 aspect ratio output.
        
        Requirements: 5.2 - Mobile poster format
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="促销",
            language="zh",
            aspect_ratio="9:16",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        image = response.images[0]
        
        # 9:16 ratio check
        expected_ratio = 9 / 16
        actual_ratio = image.width / image.height
        assert abs(actual_ratio - expected_ratio) < 0.01

    @pytest.mark.asyncio
    async def test_video_cover_aspect_ratio(self, poster_service):
        """Test 16:9 aspect ratio output.
        
        Requirements: 5.3 - Video cover format
        """
        request = PosterGenerationRequest(
            scene_description="产品展示",
            marketing_text="促销",
            language="zh",
            aspect_ratio="16:9",
            batch_size=1,
        )
        
        response = await poster_service.generate_poster(request)
        image = response.images[0]
        
        # 16:9 ratio check
        expected_ratio = 16 / 9
        actual_ratio = image.width / image.height
        assert abs(actual_ratio - expected_ratio) < 0.01
