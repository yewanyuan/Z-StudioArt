"""JWT Token utilities for authentication.

This module implements JWT token generation, validation, and parsing.

Requirements:
- 2.1: WHEN a user submits correct phone number and verification code 
       THEN THE Auth_Service SHALL return a valid Access_Token and Refresh_Token
- 2.3: WHEN an Access_Token expires THEN THE Auth_Service SHALL allow 
       token refresh using a valid Refresh_Token
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


@dataclass
class TokenPair:
    """Token pair containing access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0  # Access token expiry in seconds


@dataclass
class TokenPayload:
    """Decoded token payload."""
    user_id: str
    token_type: str  # "access" or "refresh"
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token identification


class JWTError(Exception):
    """Base exception for JWT errors."""
    pass


class TokenExpiredError(JWTError):
    """Raised when a token has expired."""
    pass


class InvalidTokenError(JWTError):
    """Raised when a token is invalid."""
    pass


class JWTService:
    """JWT Token service for generating and validating tokens.
    
    Requirements:
    - 2.1: Generate valid access and refresh tokens
    - 2.3: Support token refresh with valid refresh tokens
    """
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None,
    ):
        """Initialize JWT service.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token expiry in minutes
            refresh_token_expire_days: Refresh token expiry in days
        """
        self._secret_key = secret_key or settings.jwt_secret_key
        self._algorithm = algorithm or settings.jwt_algorithm
        self._access_token_expire_minutes = (
            access_token_expire_minutes or settings.access_token_expire_minutes
        )
        self._refresh_token_expire_days = (
            refresh_token_expire_days or settings.refresh_token_expire_days
        )
    
    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create an access token for a user.
        
        Args:
            user_id: The user's ID
            expires_delta: Optional custom expiry time
            
        Returns:
            Encoded JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self._access_token_expire_minutes)
        
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
        remember_me: bool = False,
    ) -> str:
        """Create a refresh token for a user.
        
        Args:
            user_id: The user's ID
            expires_delta: Optional custom expiry time
            remember_me: If True, use extended expiry (30 days)
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta is None:
            if remember_me:
                expires_delta = timedelta(days=settings.refresh_token_remember_me_days)
            else:
                expires_delta = timedelta(days=self._refresh_token_expire_days)
        
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    def create_token_pair(
        self,
        user_id: str,
        remember_me: bool = False,
    ) -> TokenPair:
        """Create both access and refresh tokens for a user.
        
        Args:
            user_id: The user's ID
            remember_me: If True, use extended refresh token expiry
            
        Returns:
            TokenPair containing both tokens
        """
        access_token = self.create_access_token(user_id)
        refresh_token = self.create_refresh_token(user_id, remember_me=remember_me)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self._access_token_expire_minutes * 60,
        )
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode a JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            TokenPayload with decoded information
            
        Raises:
            TokenExpiredError: If the token has expired
            InvalidTokenError: If the token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            
            return TokenPayload(
                user_id=payload["sub"],
                token_type=payload["type"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload["jti"],
            )
        except ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify an access token.
        
        Args:
            token: The access token to verify
            
        Returns:
            TokenPayload with decoded information
            
        Raises:
            TokenExpiredError: If the token has expired
            InvalidTokenError: If the token is invalid or not an access token
        """
        payload = self.verify_token(token)
        
        if payload.token_type != "access":
            raise InvalidTokenError("Token is not an access token")
        
        return payload
    
    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify a refresh token.
        
        Args:
            token: The refresh token to verify
            
        Returns:
            TokenPayload with decoded information
            
        Raises:
            TokenExpiredError: If the token has expired
            InvalidTokenError: If the token is invalid or not a refresh token
        """
        payload = self.verify_token(token)
        
        if payload.token_type != "refresh":
            raise InvalidTokenError("Token is not a refresh token")
        
        return payload
    
    def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Refresh tokens using a valid refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            New TokenPair with fresh access and refresh tokens
            
        Raises:
            TokenExpiredError: If the refresh token has expired
            InvalidTokenError: If the refresh token is invalid
        """
        payload = self.verify_refresh_token(refresh_token)
        return self.create_token_pair(payload.user_id)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for secure storage.
        
        Args:
            token: The token to hash
            
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def get_token_expiry(self, token: str) -> datetime:
        """Get the expiry time of a token.
        
        Args:
            token: The token to check
            
        Returns:
            Expiry datetime
            
        Raises:
            InvalidTokenError: If the token is invalid
        """
        payload = self.verify_token(token)
        return payload.exp


# Global JWT service instance
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """Get the global JWT service instance (singleton).
    
    Returns:
        JWTService instance
    """
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service
