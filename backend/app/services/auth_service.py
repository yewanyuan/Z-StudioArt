"""Authentication Service for PopGraph.

This module implements user authentication functionality including:
- Phone number registration with SMS verification
- Email registration with password
- Phone number login with SMS verification
- Email login with password
- Token refresh and logout

Requirements:
- 1.1: WHEN a user submits valid phone number and verification code THEN THE 
       Auth_Service SHALL create a new user account and return authentication tokens
- 1.2: WHEN a user submits a phone number that already exists THEN THE Auth_Service 
       SHALL reject the registration and return an error message indicating phone is taken
- 1.7: WHERE a user prefers email registration THEN THE Auth_Service SHALL support 
       email and password registration as an alternative method
- 2.1: WHEN a user submits correct phone number and verification code THEN THE 
       Auth_Service SHALL return a valid Access_Token and Refresh_Token
- 2.3: WHEN an Access_Token expires THEN THE Auth_Service SHALL allow token refresh 
       using a valid Refresh_Token
- 2.4: WHEN a Refresh_Token is invalid or expired THEN THE Auth_Service SHALL require 
       the user to re-authenticate
- 2.6: WHERE a user registered with email THEN THE Auth_Service SHALL support email 
       and password login
- 3.1: WHEN a user requests logout THEN THE Auth_Service SHALL invalidate the current 
       Refresh_Token
"""

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

import bcrypt

from app.models.database import RefreshToken, User
from app.models.schemas import MembershipTier
from app.services.sms_service import SMSService, get_sms_service
from app.utils.jwt import (
    JWTService,
    TokenPair,
    TokenExpiredError,
    InvalidTokenError,
    get_jwt_service,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class PhoneAlreadyExistsError(AuthError):
    """Raised when phone number is already registered."""
    pass


class EmailAlreadyExistsError(AuthError):
    """Raised when email is already registered."""
    pass


class InvalidPhoneFormatError(AuthError):
    """Raised when phone number format is invalid."""
    pass


class InvalidEmailFormatError(AuthError):
    """Raised when email format is invalid."""
    pass


class InvalidVerificationCodeError(AuthError):
    """Raised when verification code is invalid or expired."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""
    pass


class UserNotFoundError(AuthError):
    """Raised when user is not found."""
    pass


class TokenRevokedError(AuthError):
    """Raised when token has been revoked."""
    pass


class WeakPasswordError(AuthError):
    """Raised when password does not meet requirements."""
    pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AuthResult:
    """Authentication result containing user and tokens."""
    user: User
    tokens: TokenPair


@dataclass
class UserData:
    """User data for registration/login operations."""
    id: str
    phone: Optional[str]
    email: Optional[str]
    password_hash: Optional[str]
    membership_tier: MembershipTier
    membership_expiry: Optional[datetime]
    daily_usage_count: int
    last_usage_date: date
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Auth Service
# ============================================================================

class AuthService:
    """Authentication service for user registration, login, and token management.
    
    This service handles:
    - Phone number registration with SMS verification
    - Email registration with password
    - Phone number login with SMS verification
    - Email login with password
    - Token refresh and logout
    
    Attributes:
        PHONE_PATTERN: Regex pattern for valid Chinese phone numbers
        EMAIL_PATTERN: Regex pattern for valid email addresses
        MIN_PASSWORD_LENGTH: Minimum password length requirement
    """
    
    PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    MIN_PASSWORD_LENGTH = 8
    
    def __init__(
        self,
        jwt_service: Optional[JWTService] = None,
        sms_service: Optional[SMSService] = None,
    ):
        """Initialize authentication service.
        
        Args:
            jwt_service: JWT service for token operations
            sms_service: SMS service for verification codes
        """
        self._jwt_service = jwt_service or get_jwt_service()
        self._sms_service = sms_service or get_sms_service()
        
        # In-memory storage for users and tokens (production should use database)
        self._users: dict[str, User] = {}  # user_id -> User
        self._users_by_phone: dict[str, str] = {}  # phone -> user_id
        self._users_by_email: dict[str, str] = {}  # email -> user_id
        self._refresh_tokens: dict[str, RefreshToken] = {}  # token_hash -> RefreshToken
    
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(self.PHONE_PATTERN.match(phone))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(self.EMAIL_PATTERN.match(email))
    
    def validate_password(self, password: str) -> bool:
        """Validate password meets requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if valid, False otherwise
        """
        return len(password) >= self.MIN_PASSWORD_LENGTH
    
    def is_phone_registered(self, phone: str) -> bool:
        """Check if phone number is already registered.
        
        Args:
            phone: Phone number to check
            
        Returns:
            True if registered, False otherwise
            
        Requirements:
            - 1.2: Check for existing phone number
        """
        return phone in self._users_by_phone
    
    def is_email_registered(self, email: str) -> bool:
        """Check if email is already registered.
        
        Args:
            email: Email to check
            
        Returns:
            True if registered, False otherwise
        """
        return email.lower() in self._users_by_email
    
    # ========================================================================
    # Password Hashing
    # ========================================================================
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    # ========================================================================
    # User Creation
    # ========================================================================
    
    def _create_user(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
    ) -> User:
        """Create a new user with default FREE membership.
        
        Args:
            phone: User's phone number
            email: User's email address
            password_hash: Hashed password (for email registration)
            
        Returns:
            Created User object
            
        Requirements:
            - 1.5: New users get FREE membership tier by default
        """
        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid.uuid4()),
            phone=phone,
            email=email.lower() if email else None,
            password_hash=password_hash,
            membership_tier=MembershipTier.FREE,
            membership_expiry=None,
            daily_usage_count=0,
            last_usage_date=date.today(),
            created_at=now,
            updated_at=now,
        )
        
        # Store user
        self._users[user.id] = user
        if phone:
            self._users_by_phone[phone] = user.id
        if email:
            self._users_by_email[email.lower()] = user.id
        
        logger.info(f"Created new user: id={user.id}, phone={phone}, email={email}")
        return user
    
    # ========================================================================
    # Token Management
    # ========================================================================
    
    def _create_and_store_tokens(
        self,
        user_id: str,
        remember_me: bool = False,
    ) -> TokenPair:
        """Create token pair and store refresh token.
        
        Args:
            user_id: User's ID
            remember_me: Whether to extend refresh token validity
            
        Returns:
            TokenPair with access and refresh tokens
        """
        tokens = self._jwt_service.create_token_pair(user_id, remember_me=remember_me)
        
        # Store refresh token hash
        token_hash = self._jwt_service.hash_token(tokens.refresh_token)
        expiry = self._jwt_service.get_token_expiry(tokens.refresh_token)
        
        refresh_token_record = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expiry,
            created_at=datetime.now(timezone.utc),
            is_revoked=False,
        )
        self._refresh_tokens[token_hash] = refresh_token_record
        
        return tokens
    
    def _is_refresh_token_valid(self, token: str) -> bool:
        """Check if refresh token is valid and not revoked.
        
        Args:
            token: Refresh token to check
            
        Returns:
            True if valid and not revoked, False otherwise
        """
        token_hash = self._jwt_service.hash_token(token)
        record = self._refresh_tokens.get(token_hash)
        
        if record is None:
            return False
        
        if record.is_revoked:
            return False
        
        if datetime.now(timezone.utc) > record.expires_at.replace(tzinfo=timezone.utc):
            return False
        
        return True
    
    def _revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token.
        
        Args:
            token: Refresh token to revoke
            
        Returns:
            True if revoked successfully, False if token not found or already revoked
            
        Requirements:
            - 3.1: Invalidate refresh token on logout
        """
        token_hash = self._jwt_service.hash_token(token)
        record = self._refresh_tokens.get(token_hash)
        
        if record is None:
            return False
        
        # Return False if already revoked
        if record.is_revoked:
            return False
        
        record.is_revoked = True
        logger.info(f"Revoked refresh token for user: {record.user_id}")
        return True
    
    # ========================================================================
    # Registration Methods
    # ========================================================================
    
    async def send_verification_code(self, phone: str) -> bool:
        """Send verification code to phone number.
        
        Args:
            phone: Phone number to send code to
            
        Returns:
            True if sent successfully
            
        Raises:
            InvalidPhoneFormatError: If phone format is invalid
        """
        if not self.validate_phone(phone):
            raise InvalidPhoneFormatError(f"Invalid phone format: {phone}")
        
        result = await self._sms_service.send_code(phone)
        return result.success
    
    async def register_with_phone(
        self,
        phone: str,
        code: str,
    ) -> AuthResult:
        """Register a new user with phone number and verification code.
        
        Args:
            phone: User's phone number
            code: SMS verification code
            
        Returns:
            AuthResult with user and tokens
            
        Raises:
            InvalidPhoneFormatError: If phone format is invalid
            PhoneAlreadyExistsError: If phone is already registered
            InvalidVerificationCodeError: If code is invalid or expired
            
        Requirements:
            - 1.1: Create user and return tokens on valid registration
            - 1.2: Reject if phone already exists
            - 1.5: Assign FREE membership tier
        """
        # Validate phone format
        if not self.validate_phone(phone):
            raise InvalidPhoneFormatError(f"Invalid phone format: {phone}")
        
        # Check if phone already registered
        if self.is_phone_registered(phone):
            raise PhoneAlreadyExistsError(f"Phone number already registered: {phone}")
        
        # Verify SMS code
        verify_result = self._sms_service.verify_code(phone, code)
        if not verify_result.success:
            raise InvalidVerificationCodeError(verify_result.message)
        
        # Create user
        user = self._create_user(phone=phone)
        
        # Create tokens
        tokens = self._create_and_store_tokens(user.id)
        
        logger.info(f"User registered with phone: {phone}")
        return AuthResult(user=user, tokens=tokens)
    
    async def register_with_email(
        self,
        email: str,
        password: str,
    ) -> AuthResult:
        """Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            AuthResult with user and tokens
            
        Raises:
            InvalidEmailFormatError: If email format is invalid
            EmailAlreadyExistsError: If email is already registered
            WeakPasswordError: If password doesn't meet requirements
            
        Requirements:
            - 1.7: Support email registration as alternative
            - 1.5: Assign FREE membership tier
        """
        # Validate email format
        if not self.validate_email(email):
            raise InvalidEmailFormatError(f"Invalid email format: {email}")
        
        # Check if email already registered
        if self.is_email_registered(email):
            raise EmailAlreadyExistsError(f"Email already registered: {email}")
        
        # Validate password
        if not self.validate_password(password):
            raise WeakPasswordError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
            )
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        user = self._create_user(email=email, password_hash=password_hash)
        
        # Create tokens
        tokens = self._create_and_store_tokens(user.id)
        
        logger.info(f"User registered with email: {email}")
        return AuthResult(user=user, tokens=tokens)
    
    # ========================================================================
    # Login Methods
    # ========================================================================
    
    async def login_with_phone(
        self,
        phone: str,
        code: str,
    ) -> AuthResult:
        """Login with phone number and verification code.
        
        Args:
            phone: User's phone number
            code: SMS verification code
            
        Returns:
            AuthResult with user and tokens
            
        Raises:
            InvalidPhoneFormatError: If phone format is invalid
            UserNotFoundError: If user not found
            InvalidVerificationCodeError: If code is invalid or expired
            
        Requirements:
            - 2.1: Return valid tokens on successful login
        """
        # Validate phone format
        if not self.validate_phone(phone):
            raise InvalidPhoneFormatError(f"Invalid phone format: {phone}")
        
        # Find user
        user_id = self._users_by_phone.get(phone)
        if user_id is None:
            raise UserNotFoundError(f"User not found with phone: {phone}")
        
        # Verify SMS code
        verify_result = self._sms_service.verify_code(phone, code)
        if not verify_result.success:
            raise InvalidVerificationCodeError(verify_result.message)
        
        user = self._users[user_id]
        
        # Create tokens
        tokens = self._create_and_store_tokens(user.id)
        
        logger.info(f"User logged in with phone: {phone}")
        return AuthResult(user=user, tokens=tokens)
    
    async def login_with_email(
        self,
        email: str,
        password: str,
    ) -> AuthResult:
        """Login with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            AuthResult with user and tokens
            
        Raises:
            InvalidEmailFormatError: If email format is invalid
            InvalidCredentialsError: If credentials are invalid
            
        Requirements:
            - 2.6: Support email login for email-registered users
        """
        # Validate email format
        if not self.validate_email(email):
            raise InvalidEmailFormatError(f"Invalid email format: {email}")
        
        # Find user
        user_id = self._users_by_email.get(email.lower())
        if user_id is None:
            raise InvalidCredentialsError("Invalid email or password")
        
        user = self._users[user_id]
        
        # Verify password
        if not user.password_hash or not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # Create tokens
        tokens = self._create_and_store_tokens(user.id)
        
        logger.info(f"User logged in with email: {email}")
        return AuthResult(user=user, tokens=tokens)
    
    # ========================================================================
    # Token Operations
    # ========================================================================
    
    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenPair with fresh tokens
            
        Raises:
            TokenExpiredError: If refresh token has expired
            InvalidTokenError: If refresh token is invalid
            TokenRevokedError: If refresh token has been revoked
            
        Requirements:
            - 2.3: Allow token refresh with valid refresh token
            - 2.4: Require re-authentication if token invalid/expired
        """
        # Verify token is valid JWT
        try:
            payload = self._jwt_service.verify_refresh_token(refresh_token)
        except TokenExpiredError:
            raise TokenExpiredError("Refresh token has expired, please login again")
        except InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {e}")
        
        # Check if token is revoked
        if not self._is_refresh_token_valid(refresh_token):
            raise TokenRevokedError("Refresh token has been revoked")
        
        # Revoke old refresh token
        self._revoke_refresh_token(refresh_token)
        
        # Create new token pair
        new_tokens = self._create_and_store_tokens(payload.user_id)
        
        logger.info(f"Tokens refreshed for user: {payload.user_id}")
        return new_tokens
    
    async def logout(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if logout successful
            
        Requirements:
            - 3.1: Invalidate refresh token on logout
        """
        # Verify token format (but don't fail if expired)
        try:
            self._jwt_service.verify_refresh_token(refresh_token)
        except TokenExpiredError:
            # Still revoke expired tokens
            pass
        except InvalidTokenError:
            return False
        
        # Revoke the token
        revoked = self._revoke_refresh_token(refresh_token)
        
        if revoked:
            logger.info("User logged out successfully")
        
        return revoked
    
    # ========================================================================
    # User Retrieval
    # ========================================================================
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User if found, None otherwise
        """
        return self._users.get(user_id)
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number.
        
        Args:
            phone: User's phone number
            
        Returns:
            User if found, None otherwise
        """
        user_id = self._users_by_phone.get(phone)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        user_id = self._users_by_email.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_current_user(self, access_token: str) -> User:
        """Get current user from access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User associated with the token
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
            UserNotFoundError: If user not found
        """
        payload = self._jwt_service.verify_access_token(access_token)
        user = self.get_user_by_id(payload.user_id)
        
        if user is None:
            raise UserNotFoundError(f"User not found: {payload.user_id}")
        
        return user


# ============================================================================
# Global Instance
# ============================================================================

_default_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the default auth service instance (singleton).
    
    Returns:
        AuthService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = AuthService()
    return _default_service


def reset_auth_service() -> None:
    """Reset the auth service instance (for testing)."""
    global _default_service
    _default_service = None
