"""Poster Generation API for PopGraph.

This module implements the poster generation API endpoints.

Requirements:
- 1.1, 1.2: 支持中英文文案的海报生成
- 2.1: 单张生成 5 秒内返回
- 2.2: 预览模式生成 4 张变体图
- 6.1: 敏感内容过滤
- 7.1, 7.2, 7.3: 会员水印和限流系统
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.models.schemas import (
    GenerationType,
    MembershipTier,
    PosterGenerationRequest,
    PosterGenerationResponse,
    RateLimitResult,
)
from app.services.content_filter import ContentFilterService, get_content_filter
from app.services.membership_service import MembershipService, get_membership_service
from app.services.poster_service import (
    ContentBlockedError,
    PosterService,
    TemplateNotFoundError,
    get_poster_service,
)
from app.services.storage_service import StorageService, get_storage_service
from app.utils.rate_limiter import RateLimiter, get_rate_limiter


router = APIRouter(prefix="/api/poster", tags=["poster"])


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorCode:
    """错误码定义"""
    INVALID_INPUT = "INVALID_INPUT"
    CONTENT_BLOCKED = "CONTENT_BLOCKED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user_id(
    x_user_id: Annotated[Optional[str], Header()] = None,
) -> str:
    """获取当前用户 ID
    
    从请求头中获取用户 ID。在实际应用中，这应该从 JWT token 或 session 中获取。
    
    Args:
        x_user_id: 请求头中的用户 ID
        
    Returns:
        用户 ID
        
    Raises:
        HTTPException: 如果未提供用户 ID
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "未提供用户认证信息"},
        )
    return x_user_id


async def get_current_user_tier(
    x_user_tier: Annotated[Optional[str], Header()] = None,
) -> MembershipTier:
    """获取当前用户会员等级
    
    从请求头中获取用户会员等级。在实际应用中，这应该从数据库或缓存中查询。
    
    Args:
        x_user_tier: 请求头中的会员等级
        
    Returns:
        会员等级枚举值
    """
    if not x_user_tier:
        return MembershipTier.FREE
    
    try:
        return MembershipTier(x_user_tier.lower())
    except ValueError:
        return MembershipTier.FREE


async def check_rate_limit(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_tier: Annotated[MembershipTier, Depends(get_current_user_tier)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> RateLimitResult:
    """检查用户限流状态
    
    Requirements: 7.2 - 免费用户每日限额检查
    
    Args:
        user_id: 用户 ID
        user_tier: 用户会员等级
        rate_limiter: 限流服务
        
    Returns:
        限流检查结果
        
    Raises:
        HTTPException: 如果超出限额
    """
    result = await rate_limiter.check_limit(user_id, user_tier)
    
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                "message": "已超出每日生成限额，请明天再试或升级会员",
                "remaining_quota": result.remaining_quota,
                "reset_time": result.reset_time.isoformat() if result.reset_time else None,
            },
        )
    
    return result


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/generate",
    response_model=PosterGenerationResponse,
    summary="生成海报",
    description="根据场景描述和营销文案生成商业海报",
    responses={
        400: {"description": "请求参数无效或内容被阻止"},
        401: {"description": "未授权"},
        404: {"description": "模板未找到"},
        429: {"description": "超出限额"},
        500: {"description": "服务器内部错误"},
    },
)
async def generate_poster(
    request: PosterGenerationRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_tier: Annotated[MembershipTier, Depends(get_current_user_tier)],
    rate_limit_result: Annotated[RateLimitResult, Depends(check_rate_limit)],
    poster_service: Annotated[PosterService, Depends(get_poster_service)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
) -> PosterGenerationResponse:
    """生成海报 API 端点
    
    完整的海报生成流程：
    1. 认证检查（通过依赖注入）
    2. 限流检查（通过依赖注入）
    3. 内容过滤（在服务层处理）
    4. 调用海报生成服务
    5. 增加用户使用计数
    
    Args:
        request: 海报生成请求
        user_id: 当前用户 ID
        user_tier: 当前用户会员等级
        rate_limit_result: 限流检查结果
        poster_service: 海报生成服务
        rate_limiter: 限流服务
        
    Returns:
        PosterGenerationResponse: 生成结果
        
    Raises:
        HTTPException: 各种错误情况
        
    Requirements:
    - 1.1, 1.2: 支持中英文文案
    - 2.1: 5 秒内返回
    - 2.2: 批量生成 4 张
    - 6.1: 敏感内容过滤
    - 7.1, 7.2, 7.3: 会员系统
    """
    try:
        # 调用海报生成服务
        response = await poster_service.generate_poster(
            request=request,
            user_tier=user_tier,
        )
        
        # 保存到数据库
        try:
            await storage_service.save_generation(
                user_id=user_id,
                request=request,
                response=response,
                generation_type=GenerationType.POSTER,
            )
        except Exception as e:
            # 保存失败不影响返回结果，只记录日志
            import logging
            logging.warning(f"Failed to save generation to database: {e}")
        
        # 生成成功后增加使用计数
        await rate_limiter.increment_usage(user_id)
        
        return response
        
    except ContentBlockedError as e:
        # 内容被阻止 - Requirements: 6.1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.CONTENT_BLOCKED,
                "message": e.filter_result.warning_message,
                "blocked_keywords": e.filter_result.blocked_keywords,
            },
        )
    except TemplateNotFoundError as e:
        # 模板未找到
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.TEMPLATE_NOT_FOUND,
                "message": f"模板未找到: {e.template_id}",
            },
        )
    except Exception as e:
        # 其他错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "服务器内部错误，请稍后重试",
            },
        )


@router.get(
    "/quota",
    summary="获取剩余配额",
    description="获取当前用户的剩余生成配额",
)
async def get_quota(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_tier: Annotated[MembershipTier, Depends(get_current_user_tier)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> dict:
    """获取用户剩余配额
    
    Args:
        user_id: 当前用户 ID
        user_tier: 当前用户会员等级
        rate_limiter: 限流服务
        
    Returns:
        包含剩余配额信息的字典
    """
    remaining = await rate_limiter.get_remaining_quota(user_id, user_tier)
    current_usage = await rate_limiter.get_current_usage(user_id)
    
    return {
        "user_id": user_id,
        "membership_tier": user_tier.value,
        "remaining_quota": remaining,
        "current_usage": current_usage,
        "is_unlimited": remaining == -1,
    }


@router.get(
    "/image/{image_id}",
    summary="获取生成的图片",
    description="根据图片 ID 获取保存的图片",
)
async def get_image(
    image_id: str,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
):
    """获取保存的图片
    
    Args:
        image_id: 图片 ID
        storage_service: 存储服务
        
    Returns:
        图片二进制数据
    """
    from fastapi.responses import Response
    
    image_data = await storage_service.get_image(image_id)
    if image_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "IMAGE_NOT_FOUND", "message": "图片不存在"},
        )
    
    return Response(content=image_data, media_type="image/png")
