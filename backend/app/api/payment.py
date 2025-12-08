"""Payment API for PopGraph.

This module implements the payment API endpoints for subscription management.

Requirements:
- 4.1: WHEN a user selects a subscription plan THEN THE Subscription_Service SHALL 
       display payment options including Alipay, WeChat Pay, and UnionPay
- 4.2: WHEN a user chooses Alipay THEN THE Subscription_Service SHALL generate 
       an Alipay payment QR code or redirect to Alipay app
- 4.3: WHEN a user chooses WeChat Pay THEN THE Subscription_Service SHALL 
       generate a WeChat payment QR code
- 4.4: WHEN a user chooses UnionPay THEN THE Subscription_Service SHALL 
       redirect to UnionPay payment page
- 4.9: WHEN a user requests payment status THEN THE Subscription_Service SHALL 
       query the payment gateway and return the current status
"""

import logging
from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.models.database import User
from app.models.schemas import (
    MembershipTier,
    PaymentMethod,
    PaymentStatus,
    SubscriptionPlan,
)
from app.services.payment_service import (
    OrderExpiredError,
    OrderNotFoundError,
    PaymentService,
    PlanInfo,
    get_payment_service,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class PlanResponse(BaseModel):
    """订阅计划响应"""
    plan: SubscriptionPlan
    name: str
    price: int = Field(..., description="价格（分）")
    price_display: str = Field(..., description="显示价格（元）")
    tier: MembershipTier
    duration_days: int
    description: str


class PlansListResponse(BaseModel):
    """订阅计划列表响应"""
    plans: list[PlanResponse]


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    plan: SubscriptionPlan = Field(..., description="订阅计划")
    method: PaymentMethod = Field(..., description="支付方式")


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: str
    user_id: str
    plan: SubscriptionPlan
    method: PaymentMethod
    amount: int = Field(..., description="金额（分）")
    amount_display: str = Field(..., description="显示金额（元）")
    status: PaymentStatus
    payment_url: Optional[str] = None
    qrcode_content: Optional[str] = None
    created_at: datetime
    expires_in_seconds: int = Field(..., description="订单过期剩余秒数")


class OrderStatusResponse(BaseModel):
    """订单状态响应"""
    order_id: str
    status: PaymentStatus
    paid_at: Optional[datetime] = None


class CallbackResponse(BaseModel):
    """回调响应"""
    success: bool
    message: str


# ============================================================================
# Error Codes
# ============================================================================

class ErrorCode:
    """错误码定义"""
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ORDER_EXPIRED = "ORDER_EXPIRED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CALLBACK_INVALID = "CALLBACK_INVALID"
    INVALID_PLAN = "INVALID_PLAN"
    INVALID_METHOD = "INVALID_METHOD"


# ============================================================================
# Helper Functions
# ============================================================================

def plan_info_to_response(plan_info: PlanInfo) -> PlanResponse:
    """将 PlanInfo 转换为 PlanResponse"""
    return PlanResponse(
        plan=plan_info.plan,
        name=plan_info.name,
        price=plan_info.price,
        price_display=f"¥{plan_info.price / 100:.2f}",
        tier=plan_info.tier,
        duration_days=plan_info.duration_days,
        description=plan_info.description,
    )


def calculate_expires_in_seconds(created_at: datetime, expiry_minutes: int) -> int:
    """计算订单过期剩余秒数"""
    from datetime import timezone, timedelta
    
    now = datetime.now(timezone.utc)
    created_utc = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
    expiry_time = created_utc + timedelta(minutes=expiry_minutes)
    remaining = (expiry_time - now).total_seconds()
    return max(0, int(remaining))


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/plans",
    response_model=PlansListResponse,
    summary="获取订阅计划列表",
    description="获取所有可用的订阅计划及其价格信息",
)
async def get_plans(
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PlansListResponse:
    """获取订阅计划列表
    
    Requirements:
    - 4.1: WHEN a user selects a subscription plan THEN THE Subscription_Service 
           SHALL display payment options including Alipay, WeChat Pay, and UnionPay
    
    Returns:
        订阅计划列表
    """
    plans = payment_service.get_all_plans()
    return PlansListResponse(
        plans=[plan_info_to_response(p) for p in plans]
    )


@router.post(
    "/create-order",
    response_model=OrderResponse,
    summary="创建支付订单",
    description="创建新的支付订单并获取支付链接或二维码",
    responses={
        400: {"description": "请求参数无效"},
        401: {"description": "未认证"},
    },
)
async def create_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> OrderResponse:
    """创建支付订单
    
    Requirements:
    - 4.1: Create order with selected plan and payment method
    - 4.2: Generate Alipay payment QR code or redirect
    - 4.3: Generate WeChat payment QR code
    - 4.4: Redirect to UnionPay payment page
    
    Args:
        request: 创建订单请求
        current_user: 当前认证用户
        payment_service: 支付服务
        
    Returns:
        订单信息（包含支付链接或二维码）
    """
    # 创建订单并获取支付信息
    order, payment_result = payment_service.create_order_with_payment(
        user_id=current_user.id,
        plan=request.plan,
        method=request.method,
    )
    
    if not payment_result.success:
        logger.error(f"Failed to create payment: {payment_result.error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PAYMENT_FAILED,
                "message": payment_result.error_message or "创建支付失败",
            },
        )
    
    return OrderResponse(
        order_id=order.id,
        user_id=order.user_id,
        plan=order.plan,
        method=order.method,
        amount=order.amount,
        amount_display=f"¥{order.amount / 100:.2f}",
        status=order.status,
        payment_url=payment_result.payment_url,
        qrcode_content=payment_result.qrcode_content,
        created_at=order.created_at,
        expires_in_seconds=calculate_expires_in_seconds(
            order.created_at, 
            payment_service.ORDER_EXPIRY_MINUTES
        ),
    )


@router.get(
    "/order/{order_id}",
    response_model=OrderStatusResponse,
    summary="查询订单状态",
    description="查询指定订单的支付状态",
    responses={
        401: {"description": "未认证"},
        404: {"description": "订单不存在"},
    },
)
async def get_order_status(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> OrderStatusResponse:
    """查询订单状态
    
    Requirements:
    - 4.9: WHEN a user requests payment status THEN THE Subscription_Service 
           SHALL query the payment gateway and return the current status
    
    Args:
        order_id: 订单 ID
        current_user: 当前认证用户
        payment_service: 支付服务
        
    Returns:
        订单状态
    """
    try:
        order = payment_service.get_order_or_raise(order_id)
        
        # 验证订单属于当前用户
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": ErrorCode.ORDER_NOT_FOUND, "message": "订单不存在"},
            )
        
        # 获取最新状态（会检查是否过期）
        current_status = payment_service.get_order_status(order_id)
        
        return OrderStatusResponse(
            order_id=order.id,
            status=current_status,
            paid_at=order.paid_at,
        )
        
    except OrderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": ErrorCode.ORDER_NOT_FOUND, "message": "订单不存在"},
        )


@router.post(
    "/callback/alipay",
    response_model=CallbackResponse,
    summary="支付宝回调",
    description="处理支付宝支付结果回调",
)
async def alipay_callback(
    request: Request,
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CallbackResponse:
    """支付宝回调
    
    Requirements:
    - 4.5: WHEN payment is successful THEN THE Subscription_Service SHALL receive 
           callback notification and upgrade the user membership tier immediately
    
    Args:
        request: FastAPI 请求对象
        payment_service: 支付服务
        
    Returns:
        回调处理结果
    """
    # 解析回调数据
    form_data = await request.form()
    callback_data: dict[str, Any] = dict(form_data)
    
    logger.info(f"Received Alipay callback: order_id={callback_data.get('out_trade_no')}")
    
    # 处理回调
    success, order, error_message = payment_service.process_callback(
        method=PaymentMethod.ALIPAY,
        data=callback_data,
        user=None,  # 回调中不需要用户对象，会在后续处理中获取
    )
    
    if success:
        logger.info(f"Alipay callback processed successfully: order_id={order.id if order else 'unknown'}")
        return CallbackResponse(success=True, message="success")
    else:
        logger.warning(f"Alipay callback failed: {error_message}")
        return CallbackResponse(success=False, message=error_message or "处理失败")


@router.post(
    "/callback/wechat",
    response_model=CallbackResponse,
    summary="微信支付回调",
    description="处理微信支付结果回调",
)
async def wechat_callback(
    request: Request,
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CallbackResponse:
    """微信支付回调
    
    Requirements:
    - 4.5: WHEN payment is successful THEN THE Subscription_Service SHALL receive 
           callback notification and upgrade the user membership tier immediately
    
    Args:
        request: FastAPI 请求对象
        payment_service: 支付服务
        
    Returns:
        回调处理结果
    """
    # 解析回调数据（微信使用 JSON）
    try:
        callback_data = await request.json()
    except Exception:
        callback_data = {}
    
    logger.info(f"Received WeChat callback: order_id={callback_data.get('out_trade_no')}")
    
    # 处理回调
    success, order, error_message = payment_service.process_callback(
        method=PaymentMethod.WECHAT,
        data=callback_data,
        user=None,
    )
    
    if success:
        logger.info(f"WeChat callback processed successfully: order_id={order.id if order else 'unknown'}")
        return CallbackResponse(success=True, message="success")
    else:
        logger.warning(f"WeChat callback failed: {error_message}")
        return CallbackResponse(success=False, message=error_message or "处理失败")


@router.post(
    "/callback/unionpay",
    response_model=CallbackResponse,
    summary="银联回调",
    description="处理银联支付结果回调",
)
async def unionpay_callback(
    request: Request,
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CallbackResponse:
    """银联回调
    
    Requirements:
    - 4.5: WHEN payment is successful THEN THE Subscription_Service SHALL receive 
           callback notification and upgrade the user membership tier immediately
    
    Args:
        request: FastAPI 请求对象
        payment_service: 支付服务
        
    Returns:
        回调处理结果
    """
    # 解析回调数据（银联使用表单）
    form_data = await request.form()
    callback_data: dict[str, Any] = dict(form_data)
    
    logger.info(f"Received UnionPay callback: order_id={callback_data.get('orderId')}")
    
    # 处理回调
    success, order, error_message = payment_service.process_callback(
        method=PaymentMethod.UNIONPAY,
        data=callback_data,
        user=None,
    )
    
    if success:
        logger.info(f"UnionPay callback processed successfully: order_id={order.id if order else 'unknown'}")
        return CallbackResponse(success=True, message="success")
    else:
        logger.warning(f"UnionPay callback failed: {error_message}")
        return CallbackResponse(success=False, message=error_message or "处理失败")
