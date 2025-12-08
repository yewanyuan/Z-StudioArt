"""Authentication API for PopGraph.

This module implements the authentication API endpoints.

Requirements:
- 1.1: WHEN a user submits valid phone number and verification code THEN THE 
       Auth_Service SHALL create a new user account and return authentication tokens
- 1.7: WHERE a user prefers email registration THEN THE Auth_Service SHALL support 
       email and password registration as an alternative method
- 2.1: WHEN a user submits correct phone number and verification code THEN THE 
       Auth_Service SHALL return a valid Access_Token and Refresh_Token
- 2.5: WHILE a user is authenticated THEN THE User_System SHALL include the 
       Access_Token in all API requests
- 2.6: WHERE a user registered with email THEN THE Auth_Service SHALL support 
       email and password login
- 3.1: WHEN a user requests logout THEN THE Auth_Service SHALL invalidate the 
       current Refresh_Token
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.models.database import User
from app.models.schemas import MembershipTier
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidEmailFormatError,
    InvalidPhoneFormatError,
    InvalidVerificationCodeError,
    PhoneAlreadyExistsError,
    TokenRevokedError,
    UserNotFoundError,
    WeakPasswordError,
    get_auth_service,
)
from app.utils.jwt import (
    InvalidTokenError,
    TokenExpiredError,
    get_jwt_service,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# ============================================================================
# Request/Response Schemas
# ============================================================================

class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool
    message: str
    cooldown_remaining: int = 0


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class EmailRegisterRequest(BaseModel):
    """邮箱注册请求"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, description="密码")


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class EmailLoginRequest(BaseModel):
    """邮箱登录请求"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseModel):
    """登出请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    membership_tier: MembershipTier
    membership_expiry: Optional[datetime] = None
    created_at: datetime


class AuthResponse(BaseModel):
    """认证响应（包含用户信息和 Token）"""
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """通用消息响应"""
    success: bool
    message: str


# ============================================================================
# Error Codes
# ============================================================================

class ErrorCode:
    """错误码定义"""
    INVALID_PHONE = "INVALID_PHONE"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_CODE = "INVALID_CODE"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    PHONE_EXISTS = "PHONE_EXISTS"
    EMAIL_EXISTS = "EMAIL_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAUTHORIZED = "UNAUTHORIZED"


# ============================================================================
# Helper Functions
# ============================================================================

def user_to_response(user: User) -> UserResponse:
    """将 User 对象转换为 UserResponse"""
    return UserResponse(
        id=user.id,
        phone=user.phone,
        email=user.email,
        membership_tier=user.membership_tier,
        membership_expiry=user.membership_expiry,
        created_at=user.created_at,
    )


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """获取当前认证用户
    
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
            detail={"code": ErrorCode.UNAUTHORIZED, "message": "未提供认证信息"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = auth_service.get_current_user(credentials.credentials)
        return user
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_EXPIRED, "message": "Token 已过期"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_INVALID, "message": "Token 无效"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "用户不存在"},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Optional[User]:
    """获取当前用户（可选）
    
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


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/send-code",
    response_model=SendCodeResponse,
    summary="发送验证码",
    description="向指定手机号发送短信验证码",
    responses={
        400: {"description": "手机号格式无效"},
        429: {"description": "请求过于频繁"},
    },
)
async def send_verification_code(
    request: SendCodeRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SendCodeResponse:
    """发送短信验证码
    
    Requirements:
    - 1.6: WHEN a user requests a verification code THEN THE Auth_Service SHALL 
           send an SMS to the phone number and limit requests to one per 60 seconds
    
    Args:
        request: 发送验证码请求
        auth_service: 认证服务
        
    Returns:
        发送结果
    """
    try:
        success = await auth_service.send_verification_code(request.phone)
        return SendCodeResponse(
            success=success,
            message="验证码已发送" if success else "发送失败，请稍后重试",
        )
    except InvalidPhoneFormatError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_PHONE, "message": "手机号格式无效"},
        )


@router.post(
    "/register/phone",
    response_model=AuthResponse,
    summary="手机号注册",
    description="使用手机号和验证码注册新用户",
    responses={
        400: {"description": "请求参数无效"},
        409: {"description": "手机号已注册"},
    },
)
async def register_with_phone(
    request: PhoneRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """手机号注册
    
    Requirements:
    - 1.1: WHEN a user submits valid phone number and verification code THEN THE 
           Auth_Service SHALL create a new user account and return authentication tokens
    - 1.2: WHEN a user submits a phone number that already exists THEN THE Auth_Service 
           SHALL reject the registration and return an error message indicating phone is taken
    - 1.5: WHEN a new account is created THEN THE User_System SHALL assign the FREE 
           membership tier by default
    
    Args:
        request: 手机号注册请求
        auth_service: 认证服务
        
    Returns:
        认证响应（包含用户信息和 Token）
    """
    try:
        result = await auth_service.register_with_phone(request.phone, request.code)
        return AuthResponse(
            user=user_to_response(result.user),
            tokens=TokenResponse(
                access_token=result.tokens.access_token,
                refresh_token=result.tokens.refresh_token,
                token_type=result.tokens.token_type,
                expires_in=result.tokens.expires_in,
            ),
        )
    except InvalidPhoneFormatError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_PHONE, "message": "手机号格式无效"},
        )
    except PhoneAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": ErrorCode.PHONE_EXISTS, "message": "手机号已注册"},
        )
    except InvalidVerificationCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_CODE, "message": str(e)},
        )


@router.post(
    "/register/email",
    response_model=AuthResponse,
    summary="邮箱注册",
    description="使用邮箱和密码注册新用户",
    responses={
        400: {"description": "请求参数无效"},
        409: {"description": "邮箱已注册"},
    },
)
async def register_with_email(
    request: EmailRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """邮箱注册
    
    Requirements:
    - 1.7: WHERE a user prefers email registration THEN THE Auth_Service SHALL support 
           email and password registration as an alternative method
    - 1.5: WHEN a new account is created THEN THE User_System SHALL assign the FREE 
           membership tier by default
    
    Args:
        request: 邮箱注册请求
        auth_service: 认证服务
        
    Returns:
        认证响应（包含用户信息和 Token）
    """
    try:
        result = await auth_service.register_with_email(request.email, request.password)
        return AuthResponse(
            user=user_to_response(result.user),
            tokens=TokenResponse(
                access_token=result.tokens.access_token,
                refresh_token=result.tokens.refresh_token,
                token_type=result.tokens.token_type,
                expires_in=result.tokens.expires_in,
            ),
        )
    except InvalidEmailFormatError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_EMAIL, "message": "邮箱格式无效"},
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": ErrorCode.EMAIL_EXISTS, "message": "邮箱已注册"},
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.WEAK_PASSWORD, "message": str(e)},
        )


@router.post(
    "/login/phone",
    response_model=AuthResponse,
    summary="手机号登录",
    description="使用手机号和验证码登录",
    responses={
        400: {"description": "请求参数无效"},
        401: {"description": "认证失败"},
    },
)
async def login_with_phone(
    request: PhoneLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """手机号登录
    
    Requirements:
    - 2.1: WHEN a user submits correct phone number and verification code THEN THE 
           Auth_Service SHALL return a valid Access_Token and Refresh_Token
    
    Args:
        request: 手机号登录请求
        auth_service: 认证服务
        
    Returns:
        认证响应（包含用户信息和 Token）
    """
    try:
        result = await auth_service.login_with_phone(request.phone, request.code)
        return AuthResponse(
            user=user_to_response(result.user),
            tokens=TokenResponse(
                access_token=result.tokens.access_token,
                refresh_token=result.tokens.refresh_token,
                token_type=result.tokens.token_type,
                expires_in=result.tokens.expires_in,
            ),
        )
    except InvalidPhoneFormatError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_PHONE, "message": "手机号格式无效"},
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "用户不存在"},
        )
    except InvalidVerificationCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.INVALID_CODE, "message": str(e)},
        )


@router.post(
    "/login/email",
    response_model=AuthResponse,
    summary="邮箱登录",
    description="使用邮箱和密码登录",
    responses={
        400: {"description": "请求参数无效"},
        401: {"description": "认证失败"},
    },
)
async def login_with_email(
    request: EmailLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """邮箱登录
    
    Requirements:
    - 2.6: WHERE a user registered with email THEN THE Auth_Service SHALL support 
           email and password login
    
    Args:
        request: 邮箱登录请求
        auth_service: 认证服务
        
    Returns:
        认证响应（包含用户信息和 Token）
    """
    try:
        result = await auth_service.login_with_email(request.email, request.password)
        return AuthResponse(
            user=user_to_response(result.user),
            tokens=TokenResponse(
                access_token=result.tokens.access_token,
                refresh_token=result.tokens.refresh_token,
                token_type=result.tokens.token_type,
                expires_in=result.tokens.expires_in,
            ),
        )
    except InvalidEmailFormatError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_EMAIL, "message": "邮箱格式无效"},
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.INVALID_CREDENTIALS, "message": "邮箱或密码错误"},
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新 Token",
    description="使用 refresh_token 获取新的 access_token",
    responses={
        401: {"description": "Token 无效或已过期"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """刷新 Token
    
    Requirements:
    - 2.3: WHEN an Access_Token expires THEN THE Auth_Service SHALL allow token 
           refresh using a valid Refresh_Token
    - 2.4: WHEN a Refresh_Token is invalid or expired THEN THE Auth_Service SHALL 
           require the user to re-authenticate
    
    Args:
        request: 刷新 Token 请求
        auth_service: 认证服务
        
    Returns:
        新的 Token 对
    """
    try:
        tokens = await auth_service.refresh_token(request.refresh_token)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_EXPIRED, "message": "Refresh Token 已过期，请重新登录"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_INVALID, "message": "Refresh Token 无效"},
        )
    except TokenRevokedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_REVOKED, "message": "Refresh Token 已被撤销"},
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="登出",
    description="登出当前用户，使 refresh_token 失效",
    responses={
        401: {"description": "Token 无效"},
    },
)
async def logout(
    request: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """登出
    
    Requirements:
    - 3.1: WHEN a user requests logout THEN THE Auth_Service SHALL invalidate 
           the current Refresh_Token
    
    Args:
        request: 登出请求
        auth_service: 认证服务
        
    Returns:
        登出结果
    """
    success = await auth_service.logout(request.refresh_token)
    
    if success:
        return MessageResponse(success=True, message="登出成功")
    else:
        return MessageResponse(success=False, message="登出失败，Token 可能已失效")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前认证用户的详细信息",
    responses={
        401: {"description": "未认证"},
    },
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """获取当前用户信息
    
    Args:
        current_user: 当前认证的用户
        
    Returns:
        用户信息
    """
    return user_to_response(current_user)
