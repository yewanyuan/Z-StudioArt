"""Scene Fusion API for PopGraph.

This module implements the scene fusion API endpoints for product visualization.

Requirements:
- 4.1: 准确提取商品主体
- 4.2: 生成匹配描述的新背景
- 4.3: 确保无缝融合
- 7.4: 专业会员权限检查
"""

from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Header, UploadFile, status

from app.models.schemas import (
    MembershipTier,
    SceneFusionRequest,
    SceneFusionResponse,
)
from app.services.membership_service import (
    Feature,
    MembershipService,
    get_membership_service,
)
from app.services.scene_fusion_service import (
    ContentBlockedError,
    FeatureNotAvailableError,
    InvalidImageError,
    ProductExtractionError,
    SceneFusionService,
    get_scene_fusion_service,
)


router = APIRouter(prefix="/api/scene-fusion", tags=["scene-fusion"])


# ============================================================================
# Error Codes
# ============================================================================

class ErrorCode:
    """错误码定义"""
    FEATURE_NOT_AVAILABLE = "FEATURE_NOT_AVAILABLE"
    CONTENT_BLOCKED = "CONTENT_BLOCKED"
    INVALID_IMAGE = "INVALID_IMAGE"
    PRODUCT_EXTRACTION_FAILED = "PRODUCT_EXTRACTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user_id(
    x_user_id: Annotated[Optional[str], Header()] = None,
) -> str:
    """获取当前用户 ID"""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "未提供用户认证信息"},
        )
    return x_user_id


async def get_current_user_tier(
    x_user_tier: Annotated[Optional[str], Header()] = None,
) -> MembershipTier:
    """获取当前用户会员等级"""
    if not x_user_tier:
        return MembershipTier.FREE
    
    try:
        return MembershipTier(x_user_tier.lower())
    except ValueError:
        return MembershipTier.FREE


async def check_scene_fusion_access(
    user_tier: Annotated[MembershipTier, Depends(get_current_user_tier)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipTier:
    """检查场景融合功能访问权限
    
    Requirements: 7.4 - 只有专业会员可以访问场景融合功能
    
    Args:
        user_tier: 用户会员等级
        membership_service: 会员服务
        
    Returns:
        用户会员等级（如果有权限）
        
    Raises:
        HTTPException: 如果用户无权访问
    """
    if not membership_service.can_access_scene_fusion(user_tier):
        access_result = membership_service.check_feature_access(
            user_tier, Feature.SCENE_FUSION
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FEATURE_NOT_AVAILABLE,
                "message": access_result.message or "场景融合功能需要专业会员",
                "required_tier": MembershipTier.PROFESSIONAL.value,
            },
        )
    
    return user_tier


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "",
    response_model=SceneFusionResponse,
    summary="场景融合",
    description="将商品白底图与新场景背景融合，生成专业的商品场景图",
    responses={
        200: {"description": "成功返回融合结果"},
        400: {"description": "请求参数无效、内容被阻止或图像处理失败"},
        401: {"description": "未授权"},
        403: {"description": "功能不可用（需要专业会员）"},
        500: {"description": "服务器内部错误"},
    },
)
async def scene_fusion(
    request: SceneFusionRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_tier: Annotated[MembershipTier, Depends(check_scene_fusion_access)],
    scene_fusion_service: Annotated[SceneFusionService, Depends(get_scene_fusion_service)],
) -> SceneFusionResponse:
    """场景融合 API 端点
    
    将商品白底图与新场景背景融合。
    
    流程：
    1. 认证检查（通过依赖注入）
    2. 权限检查（通过依赖注入）- 只有专业会员可用
    3. 内容过滤（在服务层处理）
    4. 提取商品主体
    5. 生成场景融合图像
    
    Args:
        request: 场景融合请求
        user_id: 当前用户 ID
        user_tier: 当前用户会员等级
        scene_fusion_service: 场景融合服务
        
    Returns:
        SceneFusionResponse: 融合结果
        
    Raises:
        HTTPException: 各种错误情况
        
    Requirements:
    - 4.1: 准确提取商品主体
    - 4.2: 生成匹配描述的新背景
    - 4.3: 确保无缝融合
    - 7.4: 专业会员权限检查
    """
    try:
        return await scene_fusion_service.process_scene_fusion(
            request=request,
            user_tier=user_tier,
        )
        
    except FeatureNotAvailableError as e:
        # 功能不可用 - Requirements: 7.4
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FEATURE_NOT_AVAILABLE,
                "message": str(e),
                "required_tier": e.required_tier.value,
            },
        )
    except ContentBlockedError as e:
        # 内容被阻止
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.CONTENT_BLOCKED,
                "message": str(e),
                "blocked_keywords": e.blocked_keywords,
            },
        )
    except InvalidImageError as e:
        # 图像无效
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.INVALID_IMAGE,
                "message": str(e),
            },
        )
    except ProductExtractionError as e:
        # 商品提取失败
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PRODUCT_EXTRACTION_FAILED,
                "message": str(e),
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


@router.post(
    "/upload",
    response_model=SceneFusionResponse,
    summary="上传图片进行场景融合",
    description="直接上传商品图片进行场景融合，无需提供 URL",
    responses={
        200: {"description": "成功返回融合结果"},
        400: {"description": "请求参数无效、内容被阻止或图像处理失败"},
        401: {"description": "未授权"},
        403: {"description": "功能不可用（需要专业会员）"},
        500: {"description": "服务器内部错误"},
    },
)
async def scene_fusion_upload(
    product_image: Annotated[UploadFile, File(description="商品白底图")],
    target_scene: Annotated[str, Form(description="目标场景描述")],
    aspect_ratio: Annotated[
        Literal["1:1", "9:16", "16:9"],
        Form(description="输出尺寸比例")
    ] = "1:1",
    user_id: Annotated[str, Depends(get_current_user_id)] = None,
    user_tier: Annotated[MembershipTier, Depends(check_scene_fusion_access)] = None,
    scene_fusion_service: Annotated[SceneFusionService, Depends(get_scene_fusion_service)] = None,
) -> SceneFusionResponse:
    """上传图片进行场景融合
    
    支持直接上传商品图片，无需先上传到存储服务获取 URL。
    
    Args:
        product_image: 上传的商品白底图
        target_scene: 目标场景描述
        aspect_ratio: 输出尺寸比例
        user_id: 当前用户 ID
        user_tier: 当前用户会员等级
        scene_fusion_service: 场景融合服务
        
    Returns:
        SceneFusionResponse: 融合结果
        
    Requirements:
    - 4.1, 4.2, 4.3: 场景融合功能
    - 7.4: 专业会员权限检查
    """
    # 验证文件类型
    if product_image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.INVALID_IMAGE,
                "message": "不支持的图片格式，请上传 PNG 或 JPEG 格式的图片",
            },
        )
    
    try:
        # 读取上传的图片数据
        image_data = await product_image.read()
        
        # 调用服务处理
        response, _ = await scene_fusion_service.process_scene_fusion_with_bytes(
            image_data=image_data,
            target_scene=target_scene,
            aspect_ratio=aspect_ratio,
            user_tier=user_tier,
        )
        
        return response
        
    except FeatureNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FEATURE_NOT_AVAILABLE,
                "message": str(e),
                "required_tier": e.required_tier.value,
            },
        )
    except ContentBlockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.CONTENT_BLOCKED,
                "message": str(e),
                "blocked_keywords": e.blocked_keywords,
            },
        )
    except InvalidImageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.INVALID_IMAGE,
                "message": str(e),
            },
        )
    except ProductExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PRODUCT_EXTRACTION_FAILED,
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "服务器内部错误，请稍后重试",
            },
        )


@router.get(
    "/access",
    summary="检查场景融合访问权限",
    description="检查当前用户是否有权访问场景融合功能",
)
async def check_access(
    user_tier: Annotated[MembershipTier, Depends(get_current_user_tier)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> dict:
    """检查场景融合访问权限
    
    返回当前用户是否有权访问场景融合功能。
    
    Args:
        user_tier: 当前用户会员等级
        membership_service: 会员服务
        
    Returns:
        访问权限信息
        
    Requirements: 7.4 - 专业会员权限检查
    """
    has_access = membership_service.can_access_scene_fusion(user_tier)
    
    result = {
        "has_access": has_access,
        "current_tier": user_tier.value,
        "required_tier": MembershipTier.PROFESSIONAL.value,
    }
    
    if not has_access:
        access_result = membership_service.check_feature_access(
            user_tier, Feature.SCENE_FUSION
        )
        result["message"] = access_result.message
    
    return result
