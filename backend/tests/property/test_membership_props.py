"""Property-based tests for MembershipService watermark rules.

**Feature: popgraph, Property 8: 会员等级水印规则**

This module tests that the MembershipService correctly applies watermark rules
based on user membership tier.

Requirements:
- 7.1: WHEN a free-tier user generates a poster THEN the PopGraph System 
       SHALL add a visible watermark to the output image
- 7.3: WHEN a basic member generates a poster THEN the PopGraph System 
       SHALL produce output without watermark and with priority processing
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st

from app.models.schemas import MembershipTier
from app.services.membership_service import MembershipService, WatermarkRule


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating membership tiers
membership_tier_strategy = st.sampled_from([
    MembershipTier.FREE,
    MembershipTier.BASIC,
    MembershipTier.PROFESSIONAL,
])

# Strategy for generating watermark text
watermark_text_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
    min_size=1,
    max_size=50,
)


# ============================================================================
# Property 8: 会员等级水印规则
# **Feature: popgraph, Property 8: 会员等级水印规则**
# **Validates: Requirements 7.1, 7.3**
#
# For any poster generation request, the hasWatermark flag in the response SHALL be:
# - true if user.membershipTier equals 'free'
# - false if user.membershipTier equals 'basic' or 'professional'
# ============================================================================


@settings(max_examples=100)
@given(
    watermark_text=watermark_text_strategy,
)
def test_free_tier_always_has_watermark(
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any free-tier user, should_add_watermark must return True.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    tier = MembershipTier.FREE
    
    # Act
    result = service.should_add_watermark(tier)
    
    # Assert: Free tier should always have watermark
    assert result is True, (
        f"Free tier user should have watermark. Got should_add_watermark={result}"
    )


@settings(max_examples=100)
@given(
    watermark_text=watermark_text_strategy,
)
def test_basic_tier_no_watermark(
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any basic member, should_add_watermark must return False.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    tier = MembershipTier.BASIC
    
    # Act
    result = service.should_add_watermark(tier)
    
    # Assert: Basic tier should not have watermark
    assert result is False, (
        f"Basic tier user should not have watermark. Got should_add_watermark={result}"
    )


@settings(max_examples=100)
@given(
    watermark_text=watermark_text_strategy,
)
def test_professional_tier_no_watermark(
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any professional member, should_add_watermark must return False.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    tier = MembershipTier.PROFESSIONAL
    
    # Act
    result = service.should_add_watermark(tier)
    
    # Assert: Professional tier should not have watermark
    assert result is False, (
        f"Professional tier user should not have watermark. Got should_add_watermark={result}"
    )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
    watermark_text=watermark_text_strategy,
)
def test_watermark_rule_consistency(
    tier: MembershipTier,
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any membership tier, the watermark rule must be:
    - hasWatermark = True if tier == FREE
    - hasWatermark = False if tier == BASIC or PROFESSIONAL
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    
    # Act
    result = service.should_add_watermark(tier)
    
    # Assert: Verify watermark rule based on tier
    if tier == MembershipTier.FREE:
        assert result is True, (
            f"Free tier should have watermark. Got {result}"
        )
    else:
        assert result is False, (
            f"Tier {tier.value} should not have watermark. Got {result}"
        )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
    watermark_text=watermark_text_strategy,
)
def test_get_watermark_rule_returns_correct_structure(
    tier: MembershipTier,
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any membership tier, get_watermark_rule must return
    a WatermarkRule with consistent should_add_watermark flag.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    
    # Act
    rule = service.get_watermark_rule(tier)
    
    # Assert: Verify rule structure
    assert isinstance(rule, WatermarkRule), (
        f"Expected WatermarkRule, got {type(rule)}"
    )
    
    # Assert: Verify consistency with should_add_watermark
    expected_watermark = service.should_add_watermark(tier)
    assert rule.should_add_watermark == expected_watermark, (
        f"WatermarkRule.should_add_watermark ({rule.should_add_watermark}) "
        f"should match should_add_watermark ({expected_watermark})"
    )


@settings(max_examples=100)
@given(
    watermark_text=watermark_text_strategy,
)
def test_free_tier_watermark_rule_has_text(
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For free-tier users, the watermark rule must include
    the watermark text and opacity.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    tier = MembershipTier.FREE
    
    # Act
    rule = service.get_watermark_rule(tier)
    
    # Assert: Free tier should have watermark with text
    assert rule.should_add_watermark is True, (
        "Free tier should have watermark"
    )
    assert rule.watermark_text == watermark_text, (
        f"Watermark text should be '{watermark_text}', got '{rule.watermark_text}'"
    )
    assert rule.watermark_opacity == MembershipService.DEFAULT_WATERMARK_OPACITY, (
        f"Watermark opacity should be {MembershipService.DEFAULT_WATERMARK_OPACITY}, "
        f"got {rule.watermark_opacity}"
    )


@settings(max_examples=100)
@given(
    tier=st.sampled_from([MembershipTier.BASIC, MembershipTier.PROFESSIONAL]),
    watermark_text=watermark_text_strategy,
)
def test_paid_tier_watermark_rule_no_text(
    tier: MembershipTier,
    watermark_text: str,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For paid members (basic or professional), the watermark rule
    must have should_add_watermark=False and no watermark text.
    """
    # Arrange
    service = MembershipService(watermark_text=watermark_text)
    
    # Act
    rule = service.get_watermark_rule(tier)
    
    # Assert: Paid tiers should not have watermark
    assert rule.should_add_watermark is False, (
        f"Tier {tier.value} should not have watermark"
    )
    assert rule.watermark_text is None, (
        f"Tier {tier.value} should have no watermark text, got '{rule.watermark_text}'"
    )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
)
def test_watermark_rule_idempotent(
    tier: MembershipTier,
) -> None:
    """
    **Feature: popgraph, Property 8: 会员等级水印规则**
    **Validates: Requirements 7.1, 7.3**
    
    Property: For any membership tier, calling should_add_watermark
    multiple times must return the same result (idempotent).
    """
    # Arrange
    service = MembershipService()
    
    # Act: Call multiple times
    result1 = service.should_add_watermark(tier)
    result2 = service.should_add_watermark(tier)
    result3 = service.should_add_watermark(tier)
    
    # Assert: All results should be identical
    assert result1 == result2 == result3, (
        f"should_add_watermark should be idempotent. "
        f"Got {result1}, {result2}, {result3}"
    )


# ============================================================================
# Property 10: 专业会员功能权限
# **Feature: popgraph, Property 10: 专业会员功能权限**
# **Validates: Requirements 7.4**
#
# For any scene fusion request, access SHALL be granted if and only if
# user.membershipTier equals 'professional'.
# ============================================================================

from app.services.membership_service import Feature


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
)
def test_scene_fusion_access_professional_only(
    tier: MembershipTier,
) -> None:
    """
    **Feature: popgraph, Property 10: 专业会员功能权限**
    **Validates: Requirements 7.4**
    
    Property: For any membership tier, scene fusion access SHALL be granted
    if and only if tier equals 'professional'.
    """
    # Arrange
    service = MembershipService()
    
    # Act
    has_access = service.can_access_scene_fusion(tier)
    
    # Assert: Only professional tier should have access
    if tier == MembershipTier.PROFESSIONAL:
        assert has_access is True, (
            f"Professional tier should have scene fusion access. "
            f"Got has_access={has_access}"
        )
    else:
        assert has_access is False, (
            f"Tier {tier.value} should NOT have scene fusion access. "
            f"Got has_access={has_access}"
        )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
)
def test_scene_fusion_feature_access_consistency(
    tier: MembershipTier,
) -> None:
    """
    **Feature: popgraph, Property 10: 专业会员功能权限**
    **Validates: Requirements 7.4**
    
    Property: For any membership tier, has_feature_access(SCENE_FUSION) must
    return the same result as can_access_scene_fusion().
    """
    # Arrange
    service = MembershipService()
    
    # Act
    via_convenience_method = service.can_access_scene_fusion(tier)
    via_generic_method = service.has_feature_access(tier, Feature.SCENE_FUSION)
    
    # Assert: Both methods should return the same result
    assert via_convenience_method == via_generic_method, (
        f"can_access_scene_fusion ({via_convenience_method}) should match "
        f"has_feature_access(SCENE_FUSION) ({via_generic_method})"
    )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
)
def test_scene_fusion_check_feature_access_result(
    tier: MembershipTier,
) -> None:
    """
    **Feature: popgraph, Property 10: 专业会员功能权限**
    **Validates: Requirements 7.4**
    
    Property: For any membership tier, check_feature_access(SCENE_FUSION) must
    return allowed=True only for professional tier, and provide upgrade message
    for other tiers.
    """
    # Arrange
    service = MembershipService()
    
    # Act
    result = service.check_feature_access(tier, Feature.SCENE_FUSION)
    
    # Assert
    if tier == MembershipTier.PROFESSIONAL:
        assert result.allowed is True, (
            f"Professional tier should be allowed scene fusion access. "
            f"Got allowed={result.allowed}"
        )
    else:
        assert result.allowed is False, (
            f"Tier {tier.value} should NOT be allowed scene fusion access. "
            f"Got allowed={result.allowed}"
        )
        # Non-professional tiers should get upgrade message
        assert result.required_tier == MembershipTier.PROFESSIONAL, (
            f"Required tier for scene fusion should be PROFESSIONAL. "
            f"Got {result.required_tier}"
        )
        assert result.message is not None, (
            f"Non-professional tiers should receive an upgrade message"
        )


@settings(max_examples=100)
@given(
    tier=membership_tier_strategy,
)
def test_scene_fusion_access_idempotent(
    tier: MembershipTier,
) -> None:
    """
    **Feature: popgraph, Property 10: 专业会员功能权限**
    **Validates: Requirements 7.4**
    
    Property: For any membership tier, calling can_access_scene_fusion
    multiple times must return the same result (idempotent).
    """
    # Arrange
    service = MembershipService()
    
    # Act: Call multiple times
    result1 = service.can_access_scene_fusion(tier)
    result2 = service.can_access_scene_fusion(tier)
    result3 = service.can_access_scene_fusion(tier)
    
    # Assert: All results should be identical
    assert result1 == result2 == result3, (
        f"can_access_scene_fusion should be idempotent. "
        f"Got {result1}, {result2}, {result3}"
    )

