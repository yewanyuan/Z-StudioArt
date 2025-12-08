"""Payment Service for PopGraph.

This module implements payment functionality including:
- Order creation for subscription plans
- Order status management
- Payment gateway integration (Alipay, WeChat Pay, UnionPay)

Requirements:
- 4.1: WHEN a user selects a subscription plan THEN THE Subscription_Service SHALL 
       display payment options including Alipay, WeChat Pay, and UnionPay
- 4.2: WHEN a user chooses Alipay THEN THE Subscription_Service SHALL generate 
       an Alipay payment QR code or redirect to Alipay app
- 4.3: WHEN a user chooses WeChat Pay THEN THE Subscription_Service SHALL 
       generate a WeChat payment QR code
- 4.4: WHEN a user chooses UnionPay THEN THE Subscription_Service SHALL 
       redirect to UnionPay payment page
- 4.5: WHEN payment is successful THEN THE Subscription_Service SHALL receive callback 
       notification and upgrade the user membership tier immediately
- 4.9: WHEN a user requests payment status THEN THE Subscription_Service SHALL query 
       the payment gateway and return the current status
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.models.database import PaymentOrder, User
from app.models.schemas import (
    MembershipTier,
    PaymentMethod,
    PaymentStatus,
    SubscriptionPlan,
)
from app.services.payment_gateway import (
    CallbackResult,
    PaymentGateway,
    PaymentRequest,
    PaymentResult,
    get_payment_gateway,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# 订阅计划价格配置（单位：分）
PLAN_PRICES: dict[SubscriptionPlan, int] = {
    SubscriptionPlan.BASIC_MONTHLY: 2900,      # 29元/月
    SubscriptionPlan.BASIC_YEARLY: 29900,      # 299元/年
    SubscriptionPlan.PRO_MONTHLY: 9900,        # 99元/月
    SubscriptionPlan.PRO_YEARLY: 99900,        # 999元/年
}

# 订阅计划对应的会员等级
PLAN_TIERS: dict[SubscriptionPlan, MembershipTier] = {
    SubscriptionPlan.BASIC_MONTHLY: MembershipTier.BASIC,
    SubscriptionPlan.BASIC_YEARLY: MembershipTier.BASIC,
    SubscriptionPlan.PRO_MONTHLY: MembershipTier.PROFESSIONAL,
    SubscriptionPlan.PRO_YEARLY: MembershipTier.PROFESSIONAL,
}

# 订阅计划有效期（天数）
PLAN_DURATIONS: dict[SubscriptionPlan, int] = {
    SubscriptionPlan.BASIC_MONTHLY: 30,
    SubscriptionPlan.BASIC_YEARLY: 365,
    SubscriptionPlan.PRO_MONTHLY: 30,
    SubscriptionPlan.PRO_YEARLY: 365,
}

# 订单过期时间（分钟）
ORDER_EXPIRY_MINUTES = 30


# ============================================================================
# Exceptions
# ============================================================================

class PaymentError(Exception):
    """Base exception for payment errors."""
    pass


class OrderNotFoundError(PaymentError):
    """Raised when order is not found."""
    pass


class OrderExpiredError(PaymentError):
    """Raised when order has expired."""
    pass


class InvalidOrderStatusError(PaymentError):
    """Raised when order status transition is invalid."""
    pass


class UserNotFoundError(PaymentError):
    """Raised when user is not found."""
    pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PlanInfo:
    """Subscription plan information."""
    plan: SubscriptionPlan
    name: str
    price: int  # 价格（分）
    tier: MembershipTier
    duration_days: int
    description: str


@dataclass
class OrderResult:
    """Order creation result."""
    order: PaymentOrder
    payment_url: Optional[str] = None
    qrcode_url: Optional[str] = None


# ============================================================================
# Plan Information
# ============================================================================

PLAN_INFO: dict[SubscriptionPlan, PlanInfo] = {
    SubscriptionPlan.BASIC_MONTHLY: PlanInfo(
        plan=SubscriptionPlan.BASIC_MONTHLY,
        name="基础会员月付",
        price=PLAN_PRICES[SubscriptionPlan.BASIC_MONTHLY],
        tier=MembershipTier.BASIC,
        duration_days=PLAN_DURATIONS[SubscriptionPlan.BASIC_MONTHLY],
        description="每月100次生成，无水印，优先处理",
    ),
    SubscriptionPlan.BASIC_YEARLY: PlanInfo(
        plan=SubscriptionPlan.BASIC_YEARLY,
        name="基础会员年付",
        price=PLAN_PRICES[SubscriptionPlan.BASIC_YEARLY],
        tier=MembershipTier.BASIC,
        duration_days=PLAN_DURATIONS[SubscriptionPlan.BASIC_YEARLY],
        description="每月100次生成，无水印，优先处理，年付更优惠",
    ),
    SubscriptionPlan.PRO_MONTHLY: PlanInfo(
        plan=SubscriptionPlan.PRO_MONTHLY,
        name="专业会员月付",
        price=PLAN_PRICES[SubscriptionPlan.PRO_MONTHLY],
        tier=MembershipTier.PROFESSIONAL,
        duration_days=PLAN_DURATIONS[SubscriptionPlan.PRO_MONTHLY],
        description="无限生成，无水印，优先处理，场景融合功能",
    ),
    SubscriptionPlan.PRO_YEARLY: PlanInfo(
        plan=SubscriptionPlan.PRO_YEARLY,
        name="专业会员年付",
        price=PLAN_PRICES[SubscriptionPlan.PRO_YEARLY],
        tier=MembershipTier.PROFESSIONAL,
        duration_days=PLAN_DURATIONS[SubscriptionPlan.PRO_YEARLY],
        description="无限生成，无水印，优先处理，场景融合功能，年付更优惠",
    ),
}


# ============================================================================
# Payment Service
# ============================================================================

class PaymentService:
    """Payment service for subscription management.
    
    This service handles:
    - Order creation for subscription plans
    - Order status management
    - Payment callback processing
    - User membership upgrade
    
    Attributes:
        ORDER_EXPIRY_MINUTES: Time in minutes before an order expires
    """
    
    ORDER_EXPIRY_MINUTES = ORDER_EXPIRY_MINUTES
    
    def __init__(self):
        """Initialize payment service."""
        # In-memory storage (production should use database)
        self._orders: dict[str, PaymentOrder] = {}  # order_id -> PaymentOrder
        self._orders_by_user: dict[str, list[str]] = {}  # user_id -> [order_ids]
        self._users: dict[str, User] = {}  # user_id -> User (for testing)
    
    # ========================================================================
    # Plan Information
    # ========================================================================
    
    def get_all_plans(self) -> list[PlanInfo]:
        """Get all available subscription plans.
        
        Returns:
            List of PlanInfo for all plans
            
        Requirements:
            - 4.1: Display subscription plan options
        """
        return list(PLAN_INFO.values())
    
    def get_plan_info(self, plan: SubscriptionPlan) -> PlanInfo:
        """Get information for a specific plan.
        
        Args:
            plan: Subscription plan
            
        Returns:
            PlanInfo for the plan
        """
        return PLAN_INFO[plan]
    
    def get_plan_price(self, plan: SubscriptionPlan) -> int:
        """Get price for a subscription plan.
        
        Args:
            plan: Subscription plan
            
        Returns:
            Price in cents (分)
        """
        return PLAN_PRICES[plan]
    
    def get_plan_tier(self, plan: SubscriptionPlan) -> MembershipTier:
        """Get membership tier for a subscription plan.
        
        Args:
            plan: Subscription plan
            
        Returns:
            Corresponding MembershipTier
        """
        return PLAN_TIERS[plan]
    
    def get_plan_duration(self, plan: SubscriptionPlan) -> int:
        """Get duration in days for a subscription plan.
        
        Args:
            plan: Subscription plan
            
        Returns:
            Duration in days
        """
        return PLAN_DURATIONS[plan]
    
    # ========================================================================
    # Order Creation
    # ========================================================================
    
    def create_order(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        method: PaymentMethod,
    ) -> PaymentOrder:
        """Create a new payment order.
        
        Args:
            user_id: User's ID
            plan: Subscription plan to purchase
            method: Payment method
            
        Returns:
            Created PaymentOrder
            
        Requirements:
            - 4.1: Create order with selected plan and payment method
        """
        now = datetime.now(timezone.utc)
        order_id = str(uuid.uuid4())
        
        order = PaymentOrder(
            id=order_id,
            user_id=user_id,
            plan=plan,
            method=method,
            amount=self.get_plan_price(plan),
            status=PaymentStatus.PENDING,
            external_order_id=None,
            paid_at=None,
            created_at=now,
            updated_at=now,
        )
        
        # Store order
        self._orders[order_id] = order
        if user_id not in self._orders_by_user:
            self._orders_by_user[user_id] = []
        self._orders_by_user[user_id].append(order_id)
        
        logger.info(
            f"Created order: id={order_id}, user={user_id}, "
            f"plan={plan.value}, method={method.value}, amount={order.amount}"
        )
        
        return order
    
    # ========================================================================
    # Order Retrieval
    # ========================================================================
    
    def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            PaymentOrder if found, None otherwise
        """
        return self._orders.get(order_id)
    
    def get_order_or_raise(self, order_id: str) -> PaymentOrder:
        """Get order by ID or raise exception.
        
        Args:
            order_id: Order ID
            
        Returns:
            PaymentOrder
            
        Raises:
            OrderNotFoundError: If order not found
        """
        order = self.get_order(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order not found: {order_id}")
        return order
    
    def get_user_orders(
        self,
        user_id: str,
        status: Optional[PaymentStatus] = None,
    ) -> list[PaymentOrder]:
        """Get all orders for a user.
        
        Args:
            user_id: User's ID
            status: Optional status filter
            
        Returns:
            List of PaymentOrder
        """
        order_ids = self._orders_by_user.get(user_id, [])
        orders = [self._orders[oid] for oid in order_ids if oid in self._orders]
        
        if status is not None:
            orders = [o for o in orders if o.status == status]
        
        return sorted(orders, key=lambda o: o.created_at, reverse=True)
    
    # ========================================================================
    # Order Status Management
    # ========================================================================
    
    def is_order_expired(self, order: PaymentOrder) -> bool:
        """Check if order has expired.
        
        Args:
            order: PaymentOrder to check
            
        Returns:
            True if expired, False otherwise
        """
        if order.status != PaymentStatus.PENDING:
            return False
        
        expiry_time = order.created_at.replace(tzinfo=timezone.utc) + timedelta(
            minutes=self.ORDER_EXPIRY_MINUTES
        )
        return datetime.now(timezone.utc) > expiry_time
    
    def get_order_status(self, order_id: str) -> PaymentStatus:
        """Get current status of an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Current PaymentStatus
            
        Raises:
            OrderNotFoundError: If order not found
            
        Requirements:
            - 4.9: Query and return current payment status
        """
        order = self.get_order_or_raise(order_id)
        
        # Check if pending order has expired
        if order.status == PaymentStatus.PENDING and self.is_order_expired(order):
            self._update_order_status(order, PaymentStatus.EXPIRED)
        
        return order.status
    
    def _update_order_status(
        self,
        order: PaymentOrder,
        new_status: PaymentStatus,
    ) -> None:
        """Update order status.
        
        Args:
            order: PaymentOrder to update
            new_status: New status
        """
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            f"Order status updated: id={order.id}, "
            f"{old_status.value} -> {new_status.value}"
        )
    
    def mark_order_paid(
        self,
        order_id: str,
        external_order_id: Optional[str] = None,
    ) -> PaymentOrder:
        """Mark order as paid.
        
        Args:
            order_id: Order ID
            external_order_id: External payment gateway order ID
            
        Returns:
            Updated PaymentOrder
            
        Raises:
            OrderNotFoundError: If order not found
            OrderExpiredError: If order has expired
            InvalidOrderStatusError: If order is not in PENDING status
            
        Requirements:
            - 4.5: Process successful payment
        """
        order = self.get_order_or_raise(order_id)
        
        # Check if expired
        if self.is_order_expired(order):
            self._update_order_status(order, PaymentStatus.EXPIRED)
            raise OrderExpiredError(f"Order has expired: {order_id}")
        
        # Check current status
        if order.status != PaymentStatus.PENDING:
            raise InvalidOrderStatusError(
                f"Cannot mark order as paid, current status: {order.status.value}"
            )
        
        # Update order
        order.status = PaymentStatus.PAID
        order.external_order_id = external_order_id
        order.paid_at = datetime.now(timezone.utc)
        order.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Order marked as paid: id={order_id}")
        
        return order
    
    def mark_order_failed(self, order_id: str) -> PaymentOrder:
        """Mark order as failed.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated PaymentOrder
            
        Raises:
            OrderNotFoundError: If order not found
            InvalidOrderStatusError: If order is not in PENDING status
        """
        order = self.get_order_or_raise(order_id)
        
        if order.status != PaymentStatus.PENDING:
            raise InvalidOrderStatusError(
                f"Cannot mark order as failed, current status: {order.status.value}"
            )
        
        self._update_order_status(order, PaymentStatus.FAILED)
        
        return order
    
    # ========================================================================
    # Membership Upgrade
    # ========================================================================
    
    def calculate_membership_expiry(
        self,
        plan: SubscriptionPlan,
        current_expiry: Optional[datetime] = None,
    ) -> datetime:
        """Calculate new membership expiry date.
        
        If user has existing membership, extend from current expiry.
        Otherwise, start from now.
        
        Args:
            plan: Subscription plan
            current_expiry: Current membership expiry (if any)
            
        Returns:
            New expiry datetime
        """
        duration_days = self.get_plan_duration(plan)
        
        # If user has active membership, extend from current expiry
        now = datetime.now(timezone.utc)
        if current_expiry and current_expiry.replace(tzinfo=timezone.utc) > now:
            base_date = current_expiry.replace(tzinfo=timezone.utc)
        else:
            base_date = now
        
        return base_date + timedelta(days=duration_days)
    
    def upgrade_user_membership(
        self,
        user: User,
        plan: SubscriptionPlan,
    ) -> User:
        """Upgrade user's membership tier.
        
        Args:
            user: User to upgrade
            plan: Subscription plan purchased
            
        Returns:
            Updated User
            
        Requirements:
            - 4.5: Upgrade membership tier immediately after payment
        """
        new_tier = self.get_plan_tier(plan)
        new_expiry = self.calculate_membership_expiry(plan, user.membership_expiry)
        
        user.membership_tier = new_tier
        user.membership_expiry = new_expiry
        user.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            f"User membership upgraded: user_id={user.id}, "
            f"tier={new_tier.value}, expiry={new_expiry}"
        )
        
        return user
    
    # ========================================================================
    # Payment Gateway Integration
    # ========================================================================
    
    def get_payment_url(
        self,
        order: PaymentOrder,
        subject: str = "PopGraph 会员订阅",
    ) -> PaymentResult:
        """Get payment URL or QR code for an order.
        
        Args:
            order: Payment order
            subject: Payment subject/title
            
        Returns:
            PaymentResult with payment URL or QR code
            
        Requirements:
            - 4.2: Generate Alipay payment QR code or redirect
            - 4.3: Generate WeChat payment QR code
            - 4.4: Redirect to UnionPay payment page
        """
        gateway = get_payment_gateway(order.method)
        
        plan_info = self.get_plan_info(order.plan)
        request = PaymentRequest(
            order_id=order.id,
            amount=order.amount,
            subject=subject,
            body=plan_info.description,
            user_id=order.user_id,
        )
        
        result = gateway.create_payment(request)
        
        if result.success:
            logger.info(
                f"Payment URL generated: order_id={order.id}, "
                f"method={order.method.value}"
            )
        else:
            logger.error(
                f"Failed to generate payment URL: order_id={order.id}, "
                f"error={result.error_message}"
            )
        
        return result
    
    def create_order_with_payment(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        method: PaymentMethod,
    ) -> tuple[PaymentOrder, PaymentResult]:
        """Create order and get payment URL in one call.
        
        Args:
            user_id: User's ID
            plan: Subscription plan
            method: Payment method
            
        Returns:
            Tuple of (PaymentOrder, PaymentResult)
            
        Requirements:
            - 4.1: Create order with selected plan and payment method
            - 4.2, 4.3, 4.4: Generate payment URL/QR code
        """
        order = self.create_order(user_id, plan, method)
        payment_result = self.get_payment_url(order)
        return order, payment_result
    
    # ========================================================================
    # Payment Callback Processing
    # ========================================================================
    
    def verify_callback(
        self,
        method: PaymentMethod,
        data: dict[str, Any],
    ) -> CallbackResult:
        """Verify payment callback from gateway.
        
        Args:
            method: Payment method
            data: Callback data
            
        Returns:
            CallbackResult with verification status
            
        Requirements:
            - 4.5: Receive callback notification
        """
        gateway = get_payment_gateway(method)
        return gateway.verify_callback(data)
    
    def process_payment_success(
        self,
        order_id: str,
        external_order_id: Optional[str] = None,
        user: Optional[User] = None,
    ) -> PaymentOrder:
        """Process successful payment callback.
        
        Args:
            order_id: Order ID
            external_order_id: External payment gateway order ID
            user: User object (if available)
            
        Returns:
            Updated PaymentOrder
            
        Raises:
            OrderNotFoundError: If order not found
            OrderExpiredError: If order has expired
            
        Requirements:
            - 4.5: Receive callback and upgrade membership
        """
        # Mark order as paid
        order = self.mark_order_paid(order_id, external_order_id)
        
        # Upgrade user membership if user provided
        if user is not None:
            self.upgrade_user_membership(user, order.plan)
        
        return order
    
    def process_callback(
        self,
        method: PaymentMethod,
        data: dict[str, Any],
        user: Optional[User] = None,
    ) -> tuple[bool, Optional[PaymentOrder], Optional[str]]:
        """Process payment callback end-to-end.
        
        Args:
            method: Payment method
            data: Callback data
            user: User object (if available)
            
        Returns:
            Tuple of (success, order, error_message)
            
        Requirements:
            - 4.5: Receive callback and upgrade membership
        """
        # Verify callback
        result = self.verify_callback(method, data)
        
        if not result.success:
            logger.warning(
                f"Callback verification failed: method={method.value}, "
                f"error={result.error_message}"
            )
            return False, None, result.error_message
        
        # Process successful payment
        try:
            order = self.process_payment_success(
                order_id=result.order_id,
                external_order_id=result.external_order_id,
                user=user,
            )
            return True, order, None
        except Exception as e:
            logger.error(f"Failed to process payment success: {e}")
            return False, None, str(e)
    
    def process_payment_failure(self, order_id: str) -> PaymentOrder:
        """Process failed payment callback.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated PaymentOrder
            
        Requirements:
            - 4.6: Maintain current tier on payment failure
        """
        return self.mark_order_failed(order_id)
    
    # ========================================================================
    # Testing Helpers
    # ========================================================================
    
    def register_user_for_testing(self, user: User) -> None:
        """Register a user for testing purposes.
        
        Args:
            user: User to register
        """
        self._users[user.id] = user
    
    def get_user_for_testing(self, user_id: str) -> Optional[User]:
        """Get a user for testing purposes.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self._users.get(user_id)


# ============================================================================
# Global Instance
# ============================================================================

_default_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get the default payment service instance (singleton).
    
    Returns:
        PaymentService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = PaymentService()
    return _default_service


def reset_payment_service() -> None:
    """Reset the payment service instance (for testing)."""
    global _default_service
    _default_service = None
