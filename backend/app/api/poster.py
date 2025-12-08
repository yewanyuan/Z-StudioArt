"""Poster Generation API for PopGraph.

This module implements the poster generation API endpoints.

Requirements:
- 1.1, 1.2: 支持中英文文案的海报生成
- 2.1: 单张生成 5 秒内返回
- 2.2: 预览模式生成 4 张变体图
- 6.1: 敏感内容过滤
- 6.2: 生成成功后保存历史记录
- 7.1, 7.2, 7.3: 会员水印和限流系统
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user_id_hybrid as get_current_user_id,
    get_current_user_tier_hybrid as get_current_user_tier,
)
from app.models.database import get_db_session
from app.models.schemas import (
    GenerationType,
    MembershipTier,
    PosterGenerationRequest,
    PosterGenerationResponse,
    RateLimitResult,
)
from app.services.content_filter import ContentFilterService, get_content_filter
from app.services.history_service import HistoryService
from app.services.membership_service import MembershipService, get_membership_service
from app.services.poster_service import (
    ContentBlockedError,
    PosterService,
    TemplateNotFoundError,
    get_poster_service,
)
from app.services.storage_service import StorageService, get_storage_service
from app.utils.rate_limiter import RateLimiter, get_rate_limiter

logger = logging.getLogger(__name__)


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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PosterGenerationResponse:
    """生成海报 API 端点
    
    完整的海报生成流程：
    1. 认证检查（通过依赖注入）
    2. 限流检查（通过依赖注入）
    3. 内容过滤（在服务层处理）
    4. 调用海报生成服务
    5. 增加用户使用计数
    6. 保存历史记录
    
    Args:
        request: 海报生成请求
        user_id: 当前用户 ID
        user_tier: 当前用户会员等级
        rate_limit_result: 限流检查结果
        poster_service: 海报生成服务
        rate_limiter: 限流服务
        db: 数据库会话
        
    Returns:
        PosterGenerationResponse: 生成结果
        
    Raises:
        HTTPException: 各种错误情况
        
    Requirements:
    - 1.1, 1.2: 支持中英文文案
    - 2.1: 5 秒内返回
    - 2.2: 批量生成 4 张
    - 6.1: 敏感内容过滤
    - 6.2: 生成成功后保存历史记录
    - 7.1, 7.2, 7.3: 会员系统
    """
    try:
        # 调用海报生成服务（传递 user_id 用于 S3 存储路径）
        # Requirements: 5.1 - 生成图片后上传到 S3，返回 CDN URL
        response = await poster_service.generate_poster(
            request=request,
            user_tier=user_tier,
            user_id=user_id,
        )
        
        # 生成成功后增加使用计数
        await rate_limiter.increment_usage(user_id)
        
        # 保存历史记录 - Requirements: 6.2
        try:
            history_service = HistoryService(db)
            
            # 构建输入参数
            input_params = {
                "scene_description": request.scene_description,
                "marketing_text": request.marketing_text,
                "language": request.language,
                "template_id": request.template_id,
                "aspect_ratio": request.aspect_ratio,
                "batch_size": request.batch_size,
            }
            
            # 获取输出 URL 列表
            output_urls = [img.url for img in response.images]
            
            # 检查是否有水印
            has_watermark = any(img.has_watermark for img in response.images)
            
            await history_service.create_record(
                user_id=user_id,
                generation_type=GenerationType.POSTER,
                input_params=input_params,
                output_urls=output_urls,
                processing_time_ms=response.processing_time_ms,
                has_watermark=has_watermark,
            )
            logger.info(f"Saved poster generation history for user {user_id}")
        except Exception as history_error:
            # 历史记录保存失败不应影响主流程
            # 需要回滚数据库会话以清除错误状态
            await db.rollback()
            logger.warning(f"Failed to save history record: {history_error}")
        
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
