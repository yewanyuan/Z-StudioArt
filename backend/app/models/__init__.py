"""Database models and Pydantic schemas package."""

from app.models.schemas import (
    # Enums
    GenerationType,
    HolidayType,
    MembershipTier,
    TemplateCategory,
    # Poster Generation
    GeneratedImage,
    PosterGenerationRequest,
    PosterGenerationResponse,
    # Template
    PromptModifiers,
    Template,
    # Content Filter
    ContentFilterResult,
    # Rate Limit
    RateLimitResult,
    RATE_LIMIT_CONFIG,
    # Scene Fusion
    ExtractedProduct,
    SceneFusionRequest,
    SceneFusionResponse,
    # Z-Image Client
    GeneratedImageData,
    GenerationOptions,
)

from app.models.database import (
    # Database utilities
    Base,
    get_async_session_maker,
    get_db_session,
    get_engine,
    init_db,
    drop_db,
    # Database models
    GenerationRecord,
    TemplateRecord,
    User,
)

__all__ = [
    # Enums
    "GenerationType",
    "HolidayType",
    "MembershipTier",
    "TemplateCategory",
    # Poster Generation
    "GeneratedImage",
    "PosterGenerationRequest",
    "PosterGenerationResponse",
    # Template
    "PromptModifiers",
    "Template",
    # Content Filter
    "ContentFilterResult",
    # Rate Limit
    "RateLimitResult",
    "RATE_LIMIT_CONFIG",
    # Scene Fusion
    "ExtractedProduct",
    "SceneFusionRequest",
    "SceneFusionResponse",
    # Z-Image Client
    "GeneratedImageData",
    "GenerationOptions",
    # Database utilities
    "Base",
    "get_async_session_maker",
    "get_db_session",
    "get_engine",
    "init_db",
    "drop_db",
    # Database models
    "GenerationRecord",
    "TemplateRecord",
    "User",
]
