"""API Dependencies for PopGraph.

This module provides common dependencies for API endpoints, including
authentication middleware that can be used across all API routers.

Requirements:
- 2.5: WHILE a user is authenticated THEN THE User_System SHALL include 
       the Access_Token in all API requests
"""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.database import User
from app.models.schemas import MembershipTier
from app.services.auth_service import (
    AuthService,
    UserNotFoundError,
    get_auth_service,
)
from app.utils.jwt import (
    InvalidTokenError,
    TokenExpiredError,
)


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# ============================================================================
# Error Codes
# ============================================================================

class AuthErrorCode:
    """认证错误码定义"""
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    USER_NOT_FOUND = "USER_NOT_FOUND"


# ============================================================================
# JWT Authentication Dependencies
# ============================================================================

async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """获取当前认证用户（JWT 认证）
    
    从 Authorization header 中提取 Bearer token 并验证。
    
    Requirements:
    - 2.5: WHILE a user is authenticated THEN THE User_System SHALL include 
           the Access_Token in all API requests
    
    Args:
        credentials: HTTP Bearer 认证凭据
        auth_service: 认证服务
        
    Returns:
        当前认证的用户
        
    Raises:
        HTTPException: 如果未认证或 token 无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": AuthErrorCode.UNAUTHORIZED, "message": "未提供认证信息"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = auth_service.get_current_user(credentials.credentials)
        return user
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": AuthErrorCode.TOKEN_EXPIRED, "message": "Token 已过期"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": AuthErrorCode.TOKEN_INVALID, "message": "Token 无效"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": AuthErrorCode.USER_NOT_FOUND, "message": "用户不存在"},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Optional[User]:
    """获取当前用户（可选，JWT 认证）
    
    如果提供了有效的 token 则返回用户，否则返回 None。
    
    Args:
        credentials: HTTP Bearer 认证凭据
        auth_service: 认证服务
        
    Returns:
        当前认证的用户或 None
    """
    if credentials is None:
        return None
    
    try:
        return auth_service.get_current_user(credentials.credentials)
    except (TokenExpiredError, InvalidTokenError, UserNotFoundError):
        return None


async def get_current_user_id(
    current_user: Annotated[User, Depends(get_current_user)],
) -> str:
    """获取当前用户 ID（JWT 认证）
    
    Args:
        current_user: 当前认证的用户
        
    Returns:
        用户 ID
    """
    return current_user.id


async def get_current_user_tier(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MembershipTier:
    """获取当前用户会员等级（JWT 认证）
    
    Args:
        current_user: 当前认证的用户
        
    Returns:
        会员等级
    """
    return current_user.membership_tier


# ============================================================================
# Legacy Header Authentication Dependencies (for backward compatibility)
# ============================================================================

async def get_current_user_id_from_header(
    x_user_id: Annotated[Optional[str], Header()] = None,
) -> str:
    """获取当前用户 ID（从 Header，向后兼容）
    
    从请求头中获取用户 ID。这是旧的认证方式，保留用于向后兼容。
    
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


async def get_current_user_tier_from_header(
    x_user_tier: Annotated[Optional[str], Header()] = None,
) -> MembershipTier:
    """获取当前用户会员等级（从 Header，向后兼容）
    
    从请求头中获取用户会员等级。这是旧的认证方式，保留用于向后兼容。
    
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


# ============================================================================
# Hybrid Authentication Dependencies
# ============================================================================

async def get_current_user_id_hybrid(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    x_user_id: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> str:
    """获取当前用户 ID（混合认证）
    
    优先使用 JWT 认证，如果没有则回退到 Header 认证。
    这允许在迁移期间同时支持两种认证方式。
    
    Args:
        credentials: HTTP Bearer 认证凭据
        x_user_id: 请求头中的用户 ID（向后兼容）
        auth_service: 认证服务
        
    Returns:
        用户 ID
        
    Raises:
        HTTPException: 如果未认证
    """
    # 优先使用 JWT 认证
    if credentials is not None:
        try:
            user = auth_service.get_current_user(credentials.credentials)
            return user.id
        except (TokenExpiredError, InvalidTokenError, UserNotFoundError):
            pass  # 回退到 Header 认证
    
    # 回退到 Header 认证
    if x_user_id:
        return x_user_id
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": "未提供认证信息"},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_tier_hybrid(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    x_user_tier: Annotated[Optional[str], Header()] = None,
    auth_service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> MembershipTier:
    """获取当前用户会员等级（混合认证）
    
    优先使用 JWT 认证，如果没有则回退到 Header 认证。
    
    Args:
        credentials: HTTP Bearer 认证凭据
        x_user_tier: 请求头中的会员等级（向后兼容）
        auth_service: 认证服务
        
    Returns:
        会员等级
    """
    # 优先使用 JWT 认证
    if credentials is not None:
        try:
            user = auth_service.get_current_user(credentials.credentials)
            return user.membership_tier
        except (TokenExpiredError, InvalidTokenError, UserNotFoundError):
            pass  # 回退到 Header 认证
    
    # 回退到 Header 认证
    if x_user_tier:
        try:
            return MembershipTier(x_user_tier.lower())
        except ValueError:
            pass
    
    return MembershipTier.FREE
