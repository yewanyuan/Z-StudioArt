"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_poster_request():
    """Sample poster generation request data."""
    return {
        "scene_description": "现代简约风格的办公桌",
        "marketing_text": "限时特惠 立减50%",
        "language": "zh",
        "aspect_ratio": "1:1",
        "batch_size": 1,
    }


@pytest.fixture
def sample_template():
    """Sample template data."""
    return {
        "id": "promo_001",
        "name": "促销爆款",
        "category": "promotional",
        "prompt_modifiers": {
            "style_keywords": ["红色背景", "爆炸贴纸", "促销风格"],
            "color_scheme": "red-gold",
            "layout_hints": "大字号居中",
            "font_style": "bold",
        },
        "preview_url": "https://example.com/preview.jpg",
    }
