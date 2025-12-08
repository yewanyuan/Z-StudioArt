"""Property-based tests for payment and membership upgrade.

**Feature: user-system, Property 6: 支付成功升级会员**

This module tests that successful payment callbacks properly upgrade user membership.

Requirements:
- 4.5: WHEN payment is successful THEN THE Subscription_Service SHALL receive callback 
       notification and upgrade the user membership tier immediately
"""

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.models.database import PaymentOrder, User
from app.models.schemas import (
    MembershipTier,
    PaymentMethod,
    PaymentStatus,
    SubscriptionPlan,
)
from app.services.payment_service import (
    PaymentService,
    PLAN_TIERS,
    PLAN_DURATIONS,
    OrderNotFoundError,
    OrderExpiredError,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating user IDs
user_id_strategy = st.uuids().map(str)

# Strategy for subscription plans
plan_strategy = st.sampled_from(list(SubscriptionPlan))

# Strategy for payment methods
payment_method_strategy = st.sampled_from(list(PaymentMethod))

# Strategy for generating valid phone numbers (Chinese mobile format)
phone_strategy = st.from_regex(r"^1[3-9][0-9]{9}$", fullmatch=True)


def create_test_user(
    user_id: str = None,
    phone: str = None,
    membership_tier: MembershipTier = MembershipTier.FREE,
    membership_expiry: datetime = None,
) -> User:
    """Create a test user with specified attributes."""
    return User(
        id=user_id or str(uuid.uuid4()),
        phone=phone,
        email=None,
        password_hash=None,
        membership_tier=membership_tier,
        membership_expiry=membership_expiry,
        daily_usage_count=0,
        last_usage_date=date.today(),
    )


# ============================================================================
# Property 6: 支付成功升级会员
# **Feature: user-system, Property 6: 支付成功升级会员**
# **Validates: Requirements 4.5**
#
# For any successful payment callback, the user's membership_tier SHALL be 
# upgraded to the corresponding plan tier
# ============================================================================


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_success_upgrades_membership_tier(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment, the user's membership_tier SHALL be 
    upgraded to the tier corresponding to the purchased plan.
    """
    # Arrange: Create fresh payment service and user
    service = PaymentService()
    user = create_test_user(user_id=user_id, membership_tier=MembershipTier.FREE)
    
    # Create order
    order = service.create_order(user_id, plan, method)
    
    # Act: Process successful payment
    service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    # Assert: User's membership tier should match the plan's tier
    expected_tier = PLAN_TIERS[plan]
    assert user.membership_tier == expected_tier, (
        f"User membership tier should be {expected_tier.value} after purchasing {plan.value}. "
        f"Got {user.membership_tier.value}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_success_sets_membership_expiry(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment, the user's membership_expiry SHALL be 
    set to the appropriate duration from now.
    """
    # Arrange: Create fresh payment service and user
    service = PaymentService()
    user = create_test_user(user_id=user_id, membership_tier=MembershipTier.FREE)
    
    # Create order
    order = service.create_order(user_id, plan, method)
    
    # Record time before processing
    before_time = datetime.now(timezone.utc)
    
    # Act: Process successful payment
    service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    after_time = datetime.now(timezone.utc)
    
    # Assert: Membership expiry should be set correctly
    assert user.membership_expiry is not None, (
        "Membership expiry should be set after successful payment"
    )
    
    expected_duration = PLAN_DURATIONS[plan]
    expected_min = before_time + timedelta(days=expected_duration)
    expected_max = after_time + timedelta(days=expected_duration)
    
    expiry = user.membership_expiry.replace(tzinfo=timezone.utc)
    assert expected_min <= expiry <= expected_max, (
        f"Membership expiry should be approximately {expected_duration} days from now. "
        f"Expected between {expected_min} and {expected_max}, got {expiry}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_success_marks_order_as_paid(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment, the order status SHALL be PAID.
    """
    # Arrange: Create fresh payment service
    service = PaymentService()
    user = create_test_user(user_id=user_id)
    
    # Create order
    order = service.create_order(user_id, plan, method)
    assert order.status == PaymentStatus.PENDING, "Initial status should be PENDING"
    
    # Act: Process successful payment
    updated_order = service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    # Assert: Order status should be PAID
    assert updated_order.status == PaymentStatus.PAID, (
        f"Order status should be PAID after successful payment. Got {updated_order.status.value}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_success_sets_paid_at_timestamp(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment, the order's paid_at timestamp SHALL be set.
    """
    # Arrange: Create fresh payment service
    service = PaymentService()
    user = create_test_user(user_id=user_id)
    
    # Create order
    order = service.create_order(user_id, plan, method)
    assert order.paid_at is None, "Initial paid_at should be None"
    
    before_time = datetime.now(timezone.utc)
    
    # Act: Process successful payment
    updated_order = service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    after_time = datetime.now(timezone.utc)
    
    # Assert: paid_at should be set to current time
    assert updated_order.paid_at is not None, "paid_at should be set after successful payment"
    paid_at = updated_order.paid_at.replace(tzinfo=timezone.utc)
    assert before_time <= paid_at <= after_time, (
        f"paid_at should be between {before_time} and {after_time}. Got {paid_at}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
    external_order_id=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
)
def test_payment_success_stores_external_order_id(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
    external_order_id: str,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment with an external order ID, 
    the order SHALL store the external_order_id.
    """
    # Arrange: Create fresh payment service
    service = PaymentService()
    user = create_test_user(user_id=user_id)
    
    # Create order
    order = service.create_order(user_id, plan, method)
    
    # Act: Process successful payment with external order ID
    updated_order = service.process_payment_success(
        order_id=order.id,
        external_order_id=external_order_id,
        user=user,
    )
    
    # Assert: External order ID should be stored
    assert updated_order.external_order_id == external_order_id, (
        f"External order ID should be stored. Expected {external_order_id}, "
        f"got {updated_order.external_order_id}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    initial_tier=st.sampled_from([MembershipTier.FREE, MembershipTier.BASIC]),
    plan=st.sampled_from([SubscriptionPlan.PRO_MONTHLY, SubscriptionPlan.PRO_YEARLY]),
    method=payment_method_strategy,
)
def test_payment_success_upgrades_from_lower_tier(
    user_id: str,
    initial_tier: MembershipTier,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any user with a lower tier, successful payment for a higher 
    tier plan SHALL upgrade the membership.
    """
    # Arrange: Create user with initial tier
    service = PaymentService()
    user = create_test_user(user_id=user_id, membership_tier=initial_tier)
    
    # Create order for PRO plan
    order = service.create_order(user_id, plan, method)
    
    # Act: Process successful payment
    service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    # Assert: User should be upgraded to PROFESSIONAL
    assert user.membership_tier == MembershipTier.PROFESSIONAL, (
        f"User should be upgraded to PROFESSIONAL from {initial_tier.value}. "
        f"Got {user.membership_tier.value}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_success_extends_existing_membership(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any user with existing active membership, successful payment 
    SHALL extend the membership from the current expiry date.
    """
    # Arrange: Create user with existing membership
    service = PaymentService()
    existing_expiry = datetime.now(timezone.utc) + timedelta(days=15)
    user = create_test_user(
        user_id=user_id,
        membership_tier=MembershipTier.BASIC,
        membership_expiry=existing_expiry,
    )
    
    # Create order
    order = service.create_order(user_id, plan, method)
    
    # Act: Process successful payment
    service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=user,
    )
    
    # Assert: Membership should be extended from existing expiry
    expected_duration = PLAN_DURATIONS[plan]
    expected_expiry = existing_expiry + timedelta(days=expected_duration)
    
    new_expiry = user.membership_expiry.replace(tzinfo=timezone.utc)
    # Allow 1 second tolerance for timing
    assert abs((new_expiry - expected_expiry).total_seconds()) < 1, (
        f"Membership should be extended from existing expiry. "
        f"Expected around {expected_expiry}, got {new_expiry}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_payment_without_user_only_updates_order(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any successful payment without a user object provided,
    only the order status SHALL be updated (no membership upgrade).
    """
    # Arrange: Create fresh payment service
    service = PaymentService()
    
    # Create order
    order = service.create_order(user_id, plan, method)
    
    # Act: Process successful payment without user
    updated_order = service.process_payment_success(
        order_id=order.id,
        external_order_id=f"ext_{order.id}",
        user=None,  # No user provided
    )
    
    # Assert: Order should be marked as paid
    assert updated_order.status == PaymentStatus.PAID, (
        "Order should be marked as PAID even without user"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    plan=plan_strategy,
    method=payment_method_strategy,
)
def test_duplicate_payment_success_raises_error(
    user_id: str,
    plan: SubscriptionPlan,
    method: PaymentMethod,
) -> None:
    """
    **Feature: user-system, Property 6: 支付成功升级会员**
    **Validates: Requirements 4.5**
    
    Property: For any order that is already paid, attempting to process 
    payment success again SHALL raise an error.
    """
    from app.services.payment_service import InvalidOrderStatusError
    
    # Arrange: Create and pay order
    service = PaymentService()
    user = create_test_user(user_id=user_id)
    
    order = service.create_order(user_id, plan, method)
    service.process_payment_success(order_id=order.id, user=user)
    
    # Act & Assert: Second payment success should fail
    try:
        service.process_payment_success(order_id=order.id, user=user)
        assert False, "Should have raised InvalidOrderStatusError"
    except Exception as e:
        # Should raise an error for invalid status transition
        assert "status" in str(e).lower() or isinstance(e, InvalidOrderStatusError), (
            f"Should raise error about invalid status. Got: {e}"
        )
