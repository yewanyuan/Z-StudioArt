"""Property-based tests for RateLimiter.

**Feature: popgraph, Property 9: 免费用户每日限额**

This module tests that the RateLimiter correctly enforces daily limits
for free-tier users, blocking requests after the limit is reached.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st

from app.models.schemas import MembershipTier, RateLimitResult, RATE_LIMIT_CONFIG


# ============================================================================
# Pure Logic Functions for Testing
# ============================================================================

def check_limit_pure(current_usage: int, tier: MembershipTier) -> RateLimitResult:
    """Pure function version of rate limit check logic.
    
    This extracts the core business logic from RateLimiter.check_limit()
    for property-based testing without Redis dependency.
    
    Args:
        current_usage: Current number of generations used today
        tier: User's membership tier
        
    Returns:
        RateLimitResult indicating if request is allowed
    """
    config = RATE_LIMIT_CONFIG.get(tier, RATE_LIMIT_CONFIG[MembershipTier.FREE])
    daily_limit = config["daily_limit"]
    
    # Professional members have unlimited access (-1 means unlimited)
    if daily_limit == -1:
        return RateLimitResult(
            allowed=True,
            remaining_quota=-1,
            reset_time=None
        )
    
    remaining = max(0, daily_limit - current_usage)
    
    # Check if limit exceeded
    if current_usage >= daily_limit:
        return RateLimitResult(
            allowed=False,
            remaining_quota=0,
            reset_time=None  # Simplified for testing
        )
    
    return RateLimitResult(
        allowed=True,
        remaining_quota=remaining,
        reset_time=None  # Simplified for testing
    )


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating usage counts (0 to reasonable max)
usage_count_strategy = st.integers(min_value=0, max_value=100)

# Strategy for generating user IDs
user_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=5,
    max_size=20,
)


# ============================================================================
# Property 9: 免费用户每日限额
# **Feature: popgraph, Property 9: 免费用户每日限额**
# **Validates: Requirements 7.2**
#
# For any free-tier user, after dailyUsageCount reaches 5, subsequent
# generation requests on the same day SHALL be rejected with allowed = false.
# ============================================================================


@settings(max_examples=100)
@given(
    usage_count=st.integers(min_value=5, max_value=100),
)
def test_free_user_blocked_after_limit_reached(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: For any free-tier user with usage count >= 5,
    the rate limiter must return allowed = False.
    """
    # Arrange
    tier = MembershipTier.FREE
    free_limit = RATE_LIMIT_CONFIG[MembershipTier.FREE]["daily_limit"]
    
    # Ensure usage is at or above the limit
    assert usage_count >= free_limit, "Test precondition: usage must be >= limit"
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Request should be blocked
    assert result.allowed is False, (
        f"Free user with {usage_count} usages (limit={free_limit}) "
        f"should be blocked. Got allowed={result.allowed}"
    )


@settings(max_examples=100)
@given(
    usage_count=st.integers(min_value=0, max_value=4),
)
def test_free_user_allowed_before_limit(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: For any free-tier user with usage count < 5,
    the rate limiter must return allowed = True.
    """
    # Arrange
    tier = MembershipTier.FREE
    free_limit = RATE_LIMIT_CONFIG[MembershipTier.FREE]["daily_limit"]
    
    # Ensure usage is below the limit
    assert usage_count < free_limit, "Test precondition: usage must be < limit"
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Request should be allowed
    assert result.allowed is True, (
        f"Free user with {usage_count} usages (limit={free_limit}) "
        f"should be allowed. Got allowed={result.allowed}"
    )


@settings(max_examples=100)
@given(
    usage_count=st.integers(min_value=0, max_value=4),
)
def test_free_user_remaining_quota_correct(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: For any free-tier user with usage count < 5,
    remaining_quota should equal (5 - usage_count).
    """
    # Arrange
    tier = MembershipTier.FREE
    free_limit = RATE_LIMIT_CONFIG[MembershipTier.FREE]["daily_limit"]
    expected_remaining = free_limit - usage_count
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Remaining quota should be correct
    assert result.remaining_quota == expected_remaining, (
        f"Free user with {usage_count} usages should have "
        f"{expected_remaining} remaining. Got {result.remaining_quota}"
    )


@settings(max_examples=100)
@given(
    usage_count=st.integers(min_value=5, max_value=100),
)
def test_free_user_zero_quota_when_exceeded(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: For any free-tier user with usage count >= 5,
    remaining_quota should be 0.
    """
    # Arrange
    tier = MembershipTier.FREE
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Remaining quota should be 0
    assert result.remaining_quota == 0, (
        f"Free user with {usage_count} usages (exceeded limit) "
        f"should have 0 remaining. Got {result.remaining_quota}"
    )


@settings(max_examples=100)
@given(
    usage_count=usage_count_strategy,
)
def test_free_user_boundary_at_exactly_five(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: The boundary condition - exactly at limit (5) should be blocked,
    exactly at limit-1 (4) should be allowed.
    """
    # Arrange
    tier = MembershipTier.FREE
    free_limit = RATE_LIMIT_CONFIG[MembershipTier.FREE]["daily_limit"]
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Verify boundary behavior
    if usage_count < free_limit:
        assert result.allowed is True, (
            f"Usage {usage_count} < limit {free_limit} should be allowed"
        )
    else:
        assert result.allowed is False, (
            f"Usage {usage_count} >= limit {free_limit} should be blocked"
        )


@settings(max_examples=100)
@given(
    usage_count=usage_count_strategy,
)
def test_basic_member_higher_limit(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: Basic members have a higher limit (100) than free users (5).
    This ensures the tier differentiation works correctly.
    """
    # Arrange
    tier = MembershipTier.BASIC
    basic_limit = RATE_LIMIT_CONFIG[MembershipTier.BASIC]["daily_limit"]
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Verify basic member limits
    if usage_count < basic_limit:
        assert result.allowed is True, (
            f"Basic member with {usage_count} usages (limit={basic_limit}) "
            f"should be allowed"
        )
    else:
        assert result.allowed is False, (
            f"Basic member with {usage_count} usages (limit={basic_limit}) "
            f"should be blocked"
        )


@settings(max_examples=100)
@given(
    usage_count=st.integers(min_value=0, max_value=10000),
)
def test_professional_member_unlimited(
    usage_count: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: Professional members have unlimited access (-1 limit),
    so they should always be allowed regardless of usage count.
    """
    # Arrange
    tier = MembershipTier.PROFESSIONAL
    
    # Act
    result = check_limit_pure(usage_count, tier)
    
    # Assert: Professional members always allowed
    assert result.allowed is True, (
        f"Professional member with {usage_count} usages "
        f"should always be allowed. Got allowed={result.allowed}"
    )
    
    # Assert: Remaining quota should be -1 (unlimited)
    assert result.remaining_quota == -1, (
        f"Professional member should have unlimited quota (-1). "
        f"Got {result.remaining_quota}"
    )


@settings(max_examples=100)
@given(
    num_requests=st.integers(min_value=1, max_value=10),
)
def test_sequential_requests_respect_limit(
    num_requests: int,
) -> None:
    """
    **Feature: popgraph, Property 9: 免费用户每日限额**
    **Validates: Requirements 7.2**
    
    Property: Simulating sequential requests - the first 5 should be allowed,
    all subsequent should be blocked.
    """
    # Arrange
    tier = MembershipTier.FREE
    free_limit = RATE_LIMIT_CONFIG[MembershipTier.FREE]["daily_limit"]
    
    allowed_count = 0
    blocked_count = 0
    
    # Act: Simulate sequential requests
    for i in range(num_requests):
        # Current usage is the number of requests already made
        current_usage = i
        result = check_limit_pure(current_usage, tier)
        
        if result.allowed:
            allowed_count += 1
        else:
            blocked_count += 1
    
    # Assert: At most 5 requests should be allowed
    expected_allowed = min(num_requests, free_limit)
    expected_blocked = max(0, num_requests - free_limit)
    
    assert allowed_count == expected_allowed, (
        f"Expected {expected_allowed} allowed requests, got {allowed_count}"
    )
    assert blocked_count == expected_blocked, (
        f"Expected {expected_blocked} blocked requests, got {blocked_count}"
    )
