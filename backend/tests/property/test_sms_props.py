"""Property-based tests for SMS verification code service.

**Feature: user-system, Property 2: 验证码发送频率限制**

This module tests that verification code requests are rate-limited to one per 60 seconds.

Requirements:
- 1.6: WHEN a user requests a verification code THEN THE Auth_Service SHALL 
       send an SMS to the phone number and limit requests to one per 60 seconds
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.services.sms_service import SMSService, SendCodeResult


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating valid Chinese phone numbers
phone_strategy = st.from_regex(r"^1[3-9][0-9]{9}$", fullmatch=True)

# Strategy for generating time intervals within rate limit (0-59 seconds)
within_rate_limit_seconds = st.integers(min_value=0, max_value=59)

# Strategy for generating time intervals beyond rate limit (60+ seconds)
beyond_rate_limit_seconds = st.integers(min_value=60, max_value=3600)


# ============================================================================
# Property 2: 验证码发送频率限制
# **Feature: user-system, Property 2: 验证码发送频率限制**
# **Validates: Requirements 1.6**
#
# For any phone number, requesting a verification code within 60 seconds of 
# the previous request SHALL be rejected
# ============================================================================


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    seconds_elapsed=within_rate_limit_seconds,
)
@pytest.mark.asyncio
async def test_rate_limit_rejects_within_60_seconds(
    phone: str,
    seconds_elapsed: int,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: For any phone number, requesting a verification code within 60 
    seconds of the previous request SHALL be rejected.
    """
    # Arrange: Create SMS service and send first code
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Act: Send first code
    first_result = await service.send_code(phone, current_time=base_time)
    
    # Assert: First request should succeed
    assert first_result.success, (
        f"First code request should succeed. Got: {first_result.message}"
    )
    
    # Act: Try to send second code within rate limit
    second_time = base_time + timedelta(seconds=seconds_elapsed)
    second_result = await service.send_code(phone, current_time=second_time)
    
    # Assert: Second request should be rejected
    assert not second_result.success, (
        f"Second code request within {seconds_elapsed}s should be rejected. "
        f"Got success=True"
    )
    assert second_result.cooldown_remaining > 0, (
        f"Cooldown remaining should be positive. Got: {second_result.cooldown_remaining}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    seconds_elapsed=beyond_rate_limit_seconds,
)
@pytest.mark.asyncio
async def test_rate_limit_allows_after_60_seconds(
    phone: str,
    seconds_elapsed: int,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: For any phone number, requesting a verification code after 60 
    seconds of the previous request SHALL be allowed.
    """
    # Arrange: Create SMS service and send first code
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Act: Send first code
    first_result = await service.send_code(phone, current_time=base_time)
    
    # Assert: First request should succeed
    assert first_result.success, (
        f"First code request should succeed. Got: {first_result.message}"
    )
    
    # Act: Try to send second code after rate limit expires
    second_time = base_time + timedelta(seconds=seconds_elapsed)
    second_result = await service.send_code(phone, current_time=second_time)
    
    # Assert: Second request should succeed
    assert second_result.success, (
        f"Second code request after {seconds_elapsed}s should succeed. "
        f"Got: {second_result.message}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
@pytest.mark.asyncio
async def test_rate_limit_exactly_at_60_seconds(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: For any phone number, requesting a verification code exactly at 
    60 seconds after the previous request SHALL be allowed.
    """
    # Arrange: Create SMS service and send first code
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Act: Send first code
    first_result = await service.send_code(phone, current_time=base_time)
    
    # Assert: First request should succeed
    assert first_result.success, (
        f"First code request should succeed. Got: {first_result.message}"
    )
    
    # Act: Try to send second code exactly at 60 seconds
    second_time = base_time + timedelta(seconds=60)
    second_result = await service.send_code(phone, current_time=second_time)
    
    # Assert: Second request should succeed (60 seconds is the boundary)
    assert second_result.success, (
        f"Second code request at exactly 60s should succeed. "
        f"Got: {second_result.message}"
    )


@settings(max_examples=100)
@given(
    phone1=phone_strategy,
    phone2=phone_strategy,
)
@pytest.mark.asyncio
async def test_rate_limit_is_per_phone_number(
    phone1: str,
    phone2: str,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: Rate limiting SHALL be applied per phone number, not globally.
    Different phone numbers can request codes independently.
    """
    # Skip if phone numbers are the same
    assume(phone1 != phone2)
    
    # Arrange: Create SMS service
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Act: Send code to first phone
    result1 = await service.send_code(phone1, current_time=base_time)
    
    # Assert: First phone request should succeed
    assert result1.success, (
        f"First phone code request should succeed. Got: {result1.message}"
    )
    
    # Act: Immediately send code to second phone
    result2 = await service.send_code(phone2, current_time=base_time)
    
    # Assert: Second phone request should also succeed (different phone)
    assert result2.success, (
        f"Second phone code request should succeed (different phone). "
        f"Got: {result2.message}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    seconds_elapsed=within_rate_limit_seconds,
)
def test_is_rate_limited_returns_true_within_60_seconds(
    phone: str,
    seconds_elapsed: int,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: is_rate_limited SHALL return True for any phone number that 
    requested a code within the last 60 seconds.
    """
    # Arrange: Create SMS service and record a send time
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Simulate a previous send by directly setting the last send time
    service._last_send_time[phone] = base_time
    
    # Act: Check rate limit within 60 seconds
    check_time = base_time + timedelta(seconds=seconds_elapsed)
    is_limited = service.is_rate_limited(phone, current_time=check_time)
    
    # Assert: Should be rate limited
    assert is_limited, (
        f"is_rate_limited should return True within {seconds_elapsed}s. "
        f"Got: {is_limited}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    seconds_elapsed=beyond_rate_limit_seconds,
)
def test_is_rate_limited_returns_false_after_60_seconds(
    phone: str,
    seconds_elapsed: int,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: is_rate_limited SHALL return False for any phone number that 
    requested a code more than 60 seconds ago.
    """
    # Arrange: Create SMS service and record a send time
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Simulate a previous send by directly setting the last send time
    service._last_send_time[phone] = base_time
    
    # Act: Check rate limit after 60 seconds
    check_time = base_time + timedelta(seconds=seconds_elapsed)
    is_limited = service.is_rate_limited(phone, current_time=check_time)
    
    # Assert: Should not be rate limited
    assert not is_limited, (
        f"is_rate_limited should return False after {seconds_elapsed}s. "
        f"Got: {is_limited}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_is_rate_limited_returns_false_for_new_phone(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: is_rate_limited SHALL return False for any phone number that 
    has never requested a code.
    """
    # Arrange: Create fresh SMS service
    service = SMSService()
    current_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Act: Check rate limit for new phone
    is_limited = service.is_rate_limited(phone, current_time=current_time)
    
    # Assert: Should not be rate limited
    assert not is_limited, (
        f"is_rate_limited should return False for new phone. Got: {is_limited}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    seconds_elapsed=within_rate_limit_seconds,
)
def test_cooldown_remaining_is_accurate(
    phone: str,
    seconds_elapsed: int,
) -> None:
    """
    **Feature: user-system, Property 2: 验证码发送频率限制**
    **Validates: Requirements 1.6**
    
    Property: get_cooldown_remaining SHALL return the accurate number of 
    seconds remaining until the rate limit expires.
    """
    # Arrange: Create SMS service and record a send time
    service = SMSService()
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    
    # Simulate a previous send
    service._last_send_time[phone] = base_time
    
    # Act: Get cooldown remaining
    check_time = base_time + timedelta(seconds=seconds_elapsed)
    remaining = service.get_cooldown_remaining(phone, current_time=check_time)
    
    # Assert: Remaining should be accurate
    expected_remaining = 60 - seconds_elapsed
    assert remaining == expected_remaining, (
        f"Cooldown remaining should be {expected_remaining}s. Got: {remaining}s"
    )
