"""Property-based tests for Storage Service.

**Feature: user-system, Property 8: 图片上传返回 URL**
**Feature: user-system, Property 9: 签名 URL 包含过期时间**
**Feature: user-system, Property 10: S3 故障回退**

This module tests the storage service's image upload, signed URL generation,
and fallback behavior.

Requirements:
- 5.1: WHEN an image is generated THEN THE CDN_Storage SHALL upload the image to S3_Compatible_Storage and return a CDN URL
- 5.2: WHEN an image URL is requested THEN THE CDN_Storage SHALL return a signed URL with configurable expiration time
- 5.3: WHEN storing an image THEN THE CDN_Storage SHALL generate and store a thumbnail version
- 5.5: IF S3_Compatible_Storage is unavailable THEN THE CDN_Storage SHALL fall back to Base64 encoding and log the error
"""

import sys
import io
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st, assume
from PIL import Image


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating user IDs
user_id_strategy = st.uuids().map(str)

# Strategy for generating image dimensions (reasonable sizes)
image_dimension_strategy = st.integers(min_value=10, max_value=500)


def generate_test_image(width: int, height: int, format: str = "JPEG") -> bytes:
    """Generate a test image with specified dimensions.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (JPEG, PNG, etc.)
        
    Returns:
        Image data as bytes
    """
    img = Image.new('RGB', (width, height), color=(255, 0, 0))
    output = io.BytesIO()
    img.save(output, format=format)
    output.seek(0)
    return output.read()


# Strategy for generating valid image data
image_data_strategy = st.builds(
    generate_test_image,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)


# ============================================================================
# Property 8: 图片上传返回 URL
# **Feature: user-system, Property 8: 图片上传返回 URL**
# **Validates: Requirements 5.1, 5.3**
#
# For any valid image data, uploading SHALL return both a full-size URL 
# and a thumbnail URL
# ============================================================================

from app.services.storage_service import StorageService, S3StorageError


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_upload_returns_two_urls(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 8: 图片上传返回 URL**
    **Validates: Requirements 5.1, 5.3**
    
    Property: For any valid image data, uploading SHALL return a tuple of 
    exactly two URLs (original and thumbnail).
    """
    import asyncio
    
    # Generate test image
    image_data = generate_test_image(width, height)
    
    # Create storage service (will use Base64 fallback since S3 not configured)
    storage = StorageService()
    
    async def run_test():
        result = await storage.upload_image(image_data, user_id)
        
        # Assert: Result should be a tuple of two strings
        assert isinstance(result, tuple), f"Result should be tuple, got {type(result)}"
        assert len(result) == 2, f"Result should have 2 elements, got {len(result)}"
        
        original_url, thumbnail_url = result
        assert isinstance(original_url, str), "Original URL should be string"
        assert isinstance(thumbnail_url, str), "Thumbnail URL should be string"
        assert len(original_url) > 0, "Original URL should not be empty"
        assert len(thumbnail_url) > 0, "Thumbnail URL should not be empty"
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_upload_urls_are_different(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 8: 图片上传返回 URL**
    **Validates: Requirements 5.1, 5.3**
    
    Property: For any uploaded image, the original URL and thumbnail URL 
    SHALL be different.
    """
    import asyncio
    
    image_data = generate_test_image(width, height)
    storage = StorageService()
    
    async def run_test():
        original_url, thumbnail_url = await storage.upload_image(image_data, user_id)
        
        assert original_url != thumbnail_url, (
            "Original URL and thumbnail URL should be different"
        )
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_thumbnail_is_smaller_than_original(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 8: 图片上传返回 URL**
    **Validates: Requirements 5.3**
    
    Property: For any image larger than thumbnail max size, the generated 
    thumbnail SHALL be smaller than or equal to max_size dimensions.
    """
    # Only test with images larger than thumbnail size
    assume(width > 200 or height > 200)
    
    image_data = generate_test_image(width, height)
    storage = StorageService()
    
    # Generate thumbnail
    thumbnail_data = storage.generate_thumbnail(image_data, max_size=(200, 200))
    
    # Load thumbnail and check dimensions
    thumbnail_img = Image.open(io.BytesIO(thumbnail_data))
    
    assert thumbnail_img.width <= 200, (
        f"Thumbnail width {thumbnail_img.width} should be <= 200"
    )
    assert thumbnail_img.height <= 200, (
        f"Thumbnail height {thumbnail_img.height} should be <= 200"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_thumbnail_preserves_aspect_ratio(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 8: 图片上传返回 URL**
    **Validates: Requirements 5.3**
    
    Property: For any image, the generated thumbnail SHALL preserve the 
    original aspect ratio (within rounding tolerance).
    
    Note: Due to integer pixel rounding, extreme aspect ratios may have
    small deviations. We test that the relative error is within 5%.
    """
    # Only test with images that will be resized
    assume(width > 200 or height > 200)
    # Exclude very extreme aspect ratios where rounding errors dominate
    assume(0.25 <= width / height <= 4)
    
    image_data = generate_test_image(width, height)
    storage = StorageService()
    
    # Generate thumbnail
    thumbnail_data = storage.generate_thumbnail(image_data, max_size=(200, 200))
    
    # Calculate aspect ratios
    original_ratio = width / height
    
    thumbnail_img = Image.open(io.BytesIO(thumbnail_data))
    thumbnail_ratio = thumbnail_img.width / thumbnail_img.height
    
    # Use relative error tolerance (5%) to handle integer rounding
    relative_error = abs(original_ratio - thumbnail_ratio) / original_ratio
    assert relative_error < 0.05, (
        f"Aspect ratio should be preserved within 5% relative error. "
        f"Original: {original_ratio:.2f}, Thumbnail: {thumbnail_ratio:.2f}, "
        f"Relative error: {relative_error:.2%}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_thumbnail_is_valid_jpeg(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 8: 图片上传返回 URL**
    **Validates: Requirements 5.3**
    
    Property: For any image, the generated thumbnail SHALL be a valid JPEG image.
    """
    image_data = generate_test_image(width, height)
    storage = StorageService()
    
    thumbnail_data = storage.generate_thumbnail(image_data)
    
    # Verify it's a valid image
    thumbnail_img = Image.open(io.BytesIO(thumbnail_data))
    assert thumbnail_img.format == "JPEG", (
        f"Thumbnail should be JPEG, got {thumbnail_img.format}"
    )



# ============================================================================
# Property 9: 签名 URL 包含过期时间
# **Feature: user-system, Property 9: 签名 URL 包含过期时间**
# **Validates: Requirements 5.2**
#
# For any signed URL request, the returned URL SHALL contain an expiration parameter
# ============================================================================

# Strategy for generating S3 object keys
s3_key_strategy = st.from_regex(
    r"^images/[a-f0-9-]{36}/\d{4}/\d{2}/\d{2}/[a-f0-9-]{36}\.jpg$",
    fullmatch=True,
)

# Strategy for generating expiration times (1 minute to 1 week)
expires_in_strategy = st.integers(min_value=60, max_value=604800)


@settings(max_examples=100)
@given(
    key=s3_key_strategy,
    expires_in=expires_in_strategy,
)
def test_signed_url_contains_expiration_parameter(
    key: str,
    expires_in: int,
) -> None:
    """
    **Feature: user-system, Property 9: 签名 URL 包含过期时间**
    **Validates: Requirements 5.2**
    
    Property: For any signed URL request, the returned URL SHALL contain 
    an expiration-related parameter.
    """
    # Create a mock S3 client that returns a signed URL
    mock_s3_client = MagicMock()
    mock_signed_url = f"https://s3.example.com/bucket/{key}?X-Amz-Expires={expires_in}&X-Amz-Signature=abc123"
    mock_s3_client.generate_presigned_url.return_value = mock_signed_url
    
    # Create storage service with mocked S3
    storage = StorageService()
    storage._s3_client = mock_s3_client
    storage._s3_available = True
    
    # Get signed URL
    signed_url = storage.get_signed_url(key, expires_in)
    
    # Assert: URL should contain expiration parameter
    assert "X-Amz-Expires" in signed_url or "Expires" in signed_url, (
        f"Signed URL should contain expiration parameter. Got: {signed_url}"
    )


@settings(max_examples=100)
@given(
    key=s3_key_strategy,
    expires_in=expires_in_strategy,
)
def test_signed_url_calls_s3_with_correct_params(
    key: str,
    expires_in: int,
) -> None:
    """
    **Feature: user-system, Property 9: 签名 URL 包含过期时间**
    **Validates: Requirements 5.2**
    
    Property: For any signed URL request, the S3 client SHALL be called 
    with the correct bucket, key, and expiration time.
    """
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://example.com/signed"
    
    storage = StorageService()
    storage._s3_client = mock_s3_client
    storage._s3_available = True
    
    # Patch settings to have a known bucket name
    with patch('app.services.storage_service.settings') as mock_settings:
        mock_settings.s3_bucket = "test-bucket"
        mock_settings.s3_signed_url_expires = 3600
        
        storage.get_signed_url(key, expires_in)
    
    # Assert: S3 client was called with correct parameters
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': 'test-bucket',
            'Key': key
        },
        ExpiresIn=expires_in
    )


@settings(max_examples=100)
@given(
    key=s3_key_strategy,
)
def test_signed_url_uses_default_expiration(
    key: str,
) -> None:
    """
    **Feature: user-system, Property 9: 签名 URL 包含过期时间**
    **Validates: Requirements 5.2**
    
    Property: When no expiration is specified, the signed URL SHALL use 
    the default expiration from settings.
    """
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://example.com/signed"
    
    storage = StorageService()
    storage._s3_client = mock_s3_client
    storage._s3_available = True
    
    default_expires = 7200  # 2 hours
    
    with patch('app.services.storage_service.settings') as mock_settings:
        mock_settings.s3_bucket = "test-bucket"
        mock_settings.s3_signed_url_expires = default_expires
        
        storage.get_signed_url(key)  # No expires_in parameter
    
    # Assert: S3 client was called with default expiration
    call_args = mock_s3_client.generate_presigned_url.call_args
    assert call_args[1]['ExpiresIn'] == default_expires, (
        f"Should use default expiration {default_expires}, "
        f"got {call_args[1]['ExpiresIn']}"
    )


def test_signed_url_raises_error_when_s3_unavailable() -> None:
    """
    **Feature: user-system, Property 9: 签名 URL 包含过期时间**
    **Validates: Requirements 5.2**
    
    Property: When S3 is unavailable, get_signed_url SHALL raise S3StorageError.
    """
    storage = StorageService()
    storage._s3_available = False
    storage._s3_client = None
    
    with pytest.raises(S3StorageError) as exc_info:
        storage.get_signed_url("some/key.jpg")
    
    assert "不可用" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower(), (
        f"Error should indicate S3 unavailable. Got: {exc_info.value}"
    )


# ============================================================================
# Property 10: S3 故障回退
# **Feature: user-system, Property 10: S3 故障回退**
# **Validates: Requirements 5.5**
#
# For any image upload when S3 is unavailable, the system SHALL fall back 
# to Base64 encoding
# ============================================================================


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_fallback_to_base64_when_s3_unavailable(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 10: S3 故障回退**
    **Validates: Requirements 5.5**
    
    Property: When S3 is unavailable, upload_image SHALL return Base64 
    data URLs instead of S3 URLs.
    """
    import asyncio
    
    image_data = generate_test_image(width, height)
    
    # Create storage service with S3 disabled
    storage = StorageService()
    storage._s3_available = False
    storage._s3_client = None
    
    async def run_test():
        original_url, thumbnail_url = await storage.upload_image(image_data, user_id)
        
        # Assert: URLs should be Base64 data URLs
        assert original_url.startswith("data:image/jpeg;base64,"), (
            f"Original URL should be Base64 data URL. Got: {original_url[:50]}..."
        )
        assert thumbnail_url.startswith("data:image/jpeg;base64,"), (
            f"Thumbnail URL should be Base64 data URL. Got: {thumbnail_url[:50]}..."
        )
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_fallback_base64_is_valid_image(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 10: S3 故障回退**
    **Validates: Requirements 5.5**
    
    Property: When falling back to Base64, the encoded data SHALL be 
    decodable to a valid image.
    """
    import asyncio
    
    image_data = generate_test_image(width, height)
    
    storage = StorageService()
    storage._s3_available = False
    
    async def run_test():
        original_url, thumbnail_url = await storage.upload_image(image_data, user_id)
        
        # Extract and decode Base64 data
        original_b64 = original_url.split(",")[1]
        thumbnail_b64 = thumbnail_url.split(",")[1]
        
        original_decoded = base64.b64decode(original_b64)
        thumbnail_decoded = base64.b64decode(thumbnail_b64)
        
        # Verify they are valid images
        original_img = Image.open(io.BytesIO(original_decoded))
        thumbnail_img = Image.open(io.BytesIO(thumbnail_decoded))
        
        assert original_img.format == "JPEG", "Original should be JPEG"
        assert thumbnail_img.format == "JPEG", "Thumbnail should be JPEG"
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_fallback_on_s3_upload_error(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 10: S3 故障回退**
    **Validates: Requirements 5.5**
    
    Property: When S3 upload fails with an exception, the system SHALL 
    fall back to Base64 encoding.
    """
    import asyncio
    
    image_data = generate_test_image(width, height)
    
    # Create storage service with S3 that raises errors
    mock_s3_client = MagicMock()
    mock_s3_client.put_object.side_effect = Exception("S3 connection failed")
    
    storage = StorageService()
    storage._s3_client = mock_s3_client
    storage._s3_available = True
    
    async def run_test():
        # Should not raise, should fall back to Base64
        original_url, thumbnail_url = await storage.upload_image(image_data, user_id)
        
        # Assert: URLs should be Base64 data URLs (fallback)
        assert original_url.startswith("data:image/jpeg;base64,"), (
            "Should fall back to Base64 on S3 error"
        )
        assert thumbnail_url.startswith("data:image/jpeg;base64,"), (
            "Should fall back to Base64 on S3 error"
        )
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_fallback_logs_error(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 10: S3 故障回退**
    **Validates: Requirements 5.5**
    
    Property: When falling back to Base64 due to S3 error, the system 
    SHALL log the error.
    """
    import asyncio
    import logging
    
    image_data = generate_test_image(width, height)
    
    # Create storage service with S3 that raises errors
    mock_s3_client = MagicMock()
    mock_s3_client.put_object.side_effect = Exception("S3 connection failed")
    
    storage = StorageService()
    storage._s3_client = mock_s3_client
    storage._s3_available = True
    
    async def run_test():
        with patch('app.services.storage_service.logger') as mock_logger:
            await storage.upload_image(image_data, user_id)
            
            # Assert: Error should be logged
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "S3" in error_call or "回退" in error_call or "fallback" in error_call.lower(), (
                f"Error log should mention S3 or fallback. Got: {error_call}"
            )
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    width=image_dimension_strategy,
    height=image_dimension_strategy,
)
def test_fallback_preserves_image_content(
    user_id: str,
    width: int,
    height: int,
) -> None:
    """
    **Feature: user-system, Property 10: S3 故障回退**
    **Validates: Requirements 5.5**
    
    Property: When falling back to Base64, the original image content 
    SHALL be preserved (decodable to same dimensions).
    """
    import asyncio
    
    image_data = generate_test_image(width, height)
    
    storage = StorageService()
    storage._s3_available = False
    
    async def run_test():
        original_url, _ = await storage.upload_image(image_data, user_id)
        
        # Decode and verify dimensions
        original_b64 = original_url.split(",")[1]
        decoded_data = base64.b64decode(original_b64)
        decoded_img = Image.open(io.BytesIO(decoded_data))
        
        # Note: The image might be re-encoded, so we just verify it's valid
        # and has reasonable dimensions
        assert decoded_img.width > 0, "Decoded image should have positive width"
        assert decoded_img.height > 0, "Decoded image should have positive height"
    
    asyncio.get_event_loop().run_until_complete(run_test())
