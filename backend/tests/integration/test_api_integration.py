"""API Integration Tests for PopGraph.

Tests the HTTP API endpoints including:
- Poster generation API (/api/poster)
- Templates API (/api/templates)
- Scene fusion API (/api/scene-fusion)
- Error handling and response formats

Requirements: 1.1, 2.1, 3.1, 4.1, 6.1, 7.1
"""

import io
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models.schemas import (
    ContentFilterResult,
    GeneratedImage,
    GeneratedImageData,
    MembershipTier,
    PosterGenerationResponse,
    RateLimitResult,
)
from app.services.poster_service import (
    ContentBlockedError,
    PosterService,
    get_poster_service,
)
from app.utils.rate_limiter import RateLimiter, get_rate_limiter


# ============================================================================
# Test Fixtures
# ============================================================================

def create_test_image(width: int = 100, height: int = 100, color: str = "white") -> bytes:
    """Create a test image for mocking."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock = AsyncMock(spec=RateLimiter)
    mock.check_limit.return_value = RateLimitResult(allowed=True, remaining_quota=4)
    mock.increment_usage.return_value = None
    mock.get_remaining_quota.return_value = 3
    mock.get_current_usage.return_value = 2
    return mock


@pytest.fixture
def mock_poster_service():
    """Create a mock poster service."""
    mock = AsyncMock(spec=PosterService)
    mock.generate_poster.return_value = PosterGenerationResponse(
        request_id="test-123",
        images=[
            GeneratedImage(
                id="img-1",
                url="/generated/img-1.png",
                thumbnail_url="/generated/img-1_thumb.png",
                has_watermark=True,
                width=1024,
                height=1024,
            )
        ],
        processing_time_ms=500,
    )
    return mock


# ============================================================================
# Test: Health Check and Root Endpoints
# ============================================================================

class TestHealthEndpoints:
    """Test health check and root endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PopGraph API"
        assert "version" in data


# ============================================================================
# Test: Poster Generation API
# ============================================================================

class TestPosterGenerationAPI:
    """Test poster generation API endpoints."""

    def test_generate_poster_requires_auth(self, client):
        """Test that poster generation requires authentication.
        
        Requirements: 7.1 - Authentication required
        """
        response = client.post(
            "/api/poster/generate",
            json={
                "scene_description": "现代办公桌",
                "marketing_text": "限时特惠",
                "language": "zh",
                "aspect_ratio": "1:1",
                "batch_size": 1,
            },
        )
        
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"

    def test_generate_poster_success(
        self, client, mock_rate_limiter, mock_poster_service
    ):
        """Test successful poster generation.
        
        Requirements: 1.1 - Chinese text poster generation
        """
        # Override dependencies
        app.dependency_overrides[get_rate_limiter] = lambda: mock_rate_limiter
        app.dependency_overrides[get_poster_service] = lambda: mock_poster_service
        
        try:
            response = client.post(
                "/api/poster/generate",
                json={
                    "scene_description": "现代办公桌",
                    "marketing_text": "限时特惠",
                    "language": "zh",
                    "aspect_ratio": "1:1",
                    "batch_size": 1,
                },
                headers={"X-User-Id": "user-123", "X-User-Tier": "free"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == "test-123"
            assert len(data["images"]) == 1
            assert data["images"][0]["has_watermark"] is True
        finally:
            app.dependency_overrides.clear()

    def test_generate_poster_rate_limit_exceeded(self, client, mock_poster_service):
        """Test rate limit exceeded error.
        
        Requirements: 7.2 - Free user daily limit
        """
        mock_limiter = AsyncMock(spec=RateLimiter)
        mock_limiter.check_limit.return_value = RateLimitResult(
            allowed=False,
            remaining_quota=0,
            reset_time=datetime(2025, 12, 5, 0, 0, 0),
        )
        
        app.dependency_overrides[get_rate_limiter] = lambda: mock_limiter
        app.dependency_overrides[get_poster_service] = lambda: mock_poster_service
        
        try:
            response = client.post(
                "/api/poster/generate",
                json={
                    "scene_description": "现代办公桌",
                    "marketing_text": "限时特惠",
                    "language": "zh",
                    "aspect_ratio": "1:1",
                    "batch_size": 1,
                },
                headers={"X-User-Id": "user-123", "X-User-Tier": "free"},
            )
            
            assert response.status_code == 429
            data = response.json()
            assert data["detail"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert data["detail"]["remaining_quota"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_generate_poster_content_blocked(self, client, mock_rate_limiter):
        """Test content blocked error.
        
        Requirements: 6.1 - Content filtering
        """
        mock_service = AsyncMock(spec=PosterService)
        mock_service.generate_poster.side_effect = ContentBlockedError(
            ContentFilterResult(
                is_allowed=False,
                blocked_keywords=["敏感词"],
                warning_message="内容包含敏感词",
            )
        )
        
        app.dependency_overrides[get_rate_limiter] = lambda: mock_rate_limiter
        app.dependency_overrides[get_poster_service] = lambda: mock_service
        
        try:
            response = client.post(
                "/api/poster/generate",
                json={
                    "scene_description": "包含敏感词的描述",
                    "marketing_text": "正常文案",
                    "language": "zh",
                    "aspect_ratio": "1:1",
                    "batch_size": 1,
                },
                headers={"X-User-Id": "user-123"},
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["code"] == "CONTENT_BLOCKED"
            assert "敏感词" in data["detail"]["blocked_keywords"]
        finally:
            app.dependency_overrides.clear()

    def test_get_quota(self, client, mock_rate_limiter):
        """Test get quota endpoint."""
        app.dependency_overrides[get_rate_limiter] = lambda: mock_rate_limiter
        
        try:
            response = client.get(
                "/api/poster/quota",
                headers={"X-User-Id": "user-123", "X-User-Tier": "free"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-123"
            assert data["membership_tier"] == "free"
            assert data["remaining_quota"] == 3
            assert data["current_usage"] == 2
        finally:
            app.dependency_overrides.clear()

    def test_generate_poster_batch_mode(
        self, client, mock_rate_limiter
    ):
        """Test batch poster generation (preview mode).
        
        Requirements: 2.2 - Generate 4 variant posters
        """
        mock_service = AsyncMock(spec=PosterService)
        mock_service.generate_poster.return_value = PosterGenerationResponse(
            request_id="test-batch-123",
            images=[
                GeneratedImage(
                    id=f"img-{i}",
                    url=f"/generated/img-{i}.png",
                    thumbnail_url=f"/generated/img-{i}_thumb.png",
                    has_watermark=False,
                    width=1024,
                    height=1024,
                )
                for i in range(4)
            ],
            processing_time_ms=800,
        )
        
        app.dependency_overrides[get_rate_limiter] = lambda: mock_rate_limiter
        app.dependency_overrides[get_poster_service] = lambda: mock_service
        
        try:
            response = client.post(
                "/api/poster/generate",
                json={
                    "scene_description": "时尚服装展示",
                    "marketing_text": "新品上市",
                    "language": "zh",
                    "aspect_ratio": "1:1",
                    "batch_size": 4,
                },
                headers={"X-User-Id": "user-123", "X-User-Tier": "basic"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["images"]) == 4
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# Test: Templates API
# ============================================================================

class TestTemplatesAPI:
    """Test templates API endpoints."""

    def test_list_templates(self, client):
        """Test listing all templates.
        
        Requirements: 3.1 - Template listing
        """
        response = client.get("/api/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_templates_by_category(self, client):
        """Test listing templates by category.
        
        Requirements: 3.1, 3.2, 3.3 - Template categories
        """
        # Test promotional templates
        response = client.get("/api/templates?category=promotional")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["category"] == "promotional"
        
        # Test premium templates
        response = client.get("/api/templates?category=premium")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["category"] == "premium"
        
        # Test holiday templates
        response = client.get("/api/templates?category=holiday")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["category"] == "holiday"

    def test_get_template_by_id(self, client):
        """Test getting a specific template by ID."""
        # First get list to find a valid ID
        list_response = client.get("/api/templates")
        templates = list_response.json()
        
        if templates:
            template_id = templates[0]["id"]
            response = client.get(f"/api/templates/{template_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == template_id

    def test_get_template_not_found(self, client):
        """Test getting a non-existent template."""
        response = client.get("/api/templates/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "TEMPLATE_NOT_FOUND"

    def test_get_holiday_templates(self, client):
        """Test getting templates by holiday type.
        
        Requirements: 3.3 - Holiday templates
        """
        response = client.get("/api/templates/holiday/spring_festival")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_categories_summary(self, client):
        """Test getting template categories summary."""
        response = client.get("/api/templates/categories/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_category" in data


# ============================================================================
# Test: Scene Fusion API
# ============================================================================

class TestSceneFusionAPI:
    """Test scene fusion API endpoints."""

    def test_scene_fusion_requires_auth(self, client):
        """Test that scene fusion requires authentication."""
        response = client.post(
            "/api/scene-fusion",
            json={
                "product_image_url": "https://example.com/product.png",
                "target_scene": "现代客厅",
                "aspect_ratio": "1:1",
            },
        )
        
        assert response.status_code == 401

    def test_scene_fusion_requires_professional_tier(self, client):
        """Test that scene fusion requires professional membership.
        
        Requirements: 7.4 - Professional member access
        """
        response = client.post(
            "/api/scene-fusion",
            json={
                "product_image_url": "https://example.com/product.png",
                "target_scene": "现代客厅",
                "aspect_ratio": "1:1",
            },
            headers={"X-User-Id": "user-123", "X-User-Tier": "free"},
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "FEATURE_NOT_AVAILABLE"
        assert data["detail"]["required_tier"] == "professional"

    def test_scene_fusion_basic_member_denied(self, client):
        """Test that basic members cannot access scene fusion.
        
        Requirements: 7.4 - Only professional members
        """
        response = client.post(
            "/api/scene-fusion",
            json={
                "product_image_url": "https://example.com/product.png",
                "target_scene": "现代客厅",
                "aspect_ratio": "1:1",
            },
            headers={"X-User-Id": "user-123", "X-User-Tier": "basic"},
        )
        
        assert response.status_code == 403

    def test_check_scene_fusion_access_free(self, client):
        """Test access check for free user."""
        response = client.get(
            "/api/scene-fusion/access",
            headers={"X-User-Tier": "free"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is False
        assert data["current_tier"] == "free"
        assert data["required_tier"] == "professional"

    def test_check_scene_fusion_access_professional(self, client):
        """Test access check for professional user.
        
        Requirements: 7.4 - Professional member access
        """
        response = client.get(
            "/api/scene-fusion/access",
            headers={"X-User-Tier": "professional"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is True
        assert data["current_tier"] == "professional"

    def test_scene_fusion_upload_invalid_format(self, client):
        """Test scene fusion upload with invalid image format."""
        response = client.post(
            "/api/scene-fusion/upload",
            data={"target_scene": "现代客厅", "aspect_ratio": "1:1"},
            files={"product_image": ("test.txt", b"not an image", "text/plain")},
            headers={"X-User-Id": "user-123", "X-User-Tier": "professional"},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_IMAGE"


# ============================================================================
# Test: Error Response Format
# ============================================================================

class TestErrorResponseFormat:
    """Test that error responses follow consistent format."""

    def test_not_found_error_format(self, client):
        """Test 404 error response format."""
        response = client.get("/api/templates/non-existent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "code" in data["detail"]
        assert "message" in data["detail"]

    def test_unauthorized_error_format(self, client):
        """Test 401 error response format."""
        response = client.post(
            "/api/poster/generate",
            json={
                "scene_description": "测试",
                "marketing_text": "测试",
                "language": "zh",
                "aspect_ratio": "1:1",
                "batch_size": 1,
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "code" in data["detail"]

    def test_forbidden_error_format(self, client):
        """Test 403 error response format."""
        response = client.post(
            "/api/scene-fusion",
            json={
                "product_image_url": "https://example.com/product.png",
                "target_scene": "现代客厅",
                "aspect_ratio": "1:1",
            },
            headers={"X-User-Id": "user-123", "X-User-Tier": "free"},
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "code" in data["detail"]
        assert "required_tier" in data["detail"]

