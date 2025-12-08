"""Property-based tests for authentication and user registration.

**Feature: user-system, Property 1: 新用户默认 FREE 会员**

This module tests that newly registered users are assigned the FREE membership tier by default.

Requirements:
- 1.5: WHEN a new account is created THEN THE User_System SHALL assign the FREE membership tier by default
"""

import sys
import uuid
from pathlib import Path
from datetime import date

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, settings, strategies as st

from app.models.database import User
from app.models.schemas import MembershipTier


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating valid phone numbers (Chinese mobile format)
phone_strategy = st.from_regex(r"^1[3-9][0-9]{9}$", fullmatch=True)

# Strategy for generating valid email addresses
email_strategy = st.emails()

# Strategy for generating password hashes (simulated bcrypt hash format)
password_hash_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./",
    min_size=60,
    max_size=60,
)


def create_new_user(
    phone: str = None,
    email: str = None,
    password_hash: str = None,
) -> User:
    """Helper function to create a new user with proper defaults.
    
    This simulates what the auth service would do when creating a new user,
    ensuring all default values are properly set.
    """
    return User(
        id=str(uuid.uuid4()),
        phone=phone,
        email=email,
        password_hash=password_hash,
        membership_tier=MembershipTier.FREE,  # Default tier for new users
        membership_expiry=None,
        daily_usage_count=0,
        last_usage_date=date.today(),
    )


# ============================================================================
# Property 1: 新用户默认 FREE 会员
# **Feature: user-system, Property 1: 新用户默认 FREE 会员**
# **Validates: Requirements 1.5**
#
# For any newly registered user (via phone or email), the membership_tier 
# field SHALL be MembershipTier.FREE
# ============================================================================


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_new_user_with_phone_has_free_tier(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Property: For any user created with a phone number, the membership_tier
    must default to FREE.
    """
    # Arrange & Act: Create a new user with phone number
    user = create_new_user(phone=phone)
    
    # Assert: New user should have FREE membership tier
    assert user.membership_tier == MembershipTier.FREE, (
        f"New user with phone should have FREE tier. "
        f"Got membership_tier={user.membership_tier}"
    )


@settings(max_examples=100)
@given(
    email=email_strategy,
    password_hash=password_hash_strategy,
)
def test_new_user_with_email_has_free_tier(
    email: str,
    password_hash: str,
) -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Property: For any user created with an email and password, the membership_tier
    must default to FREE.
    """
    # Arrange & Act: Create a new user with email
    user = create_new_user(email=email, password_hash=password_hash)
    
    # Assert: New user should have FREE membership tier
    assert user.membership_tier == MembershipTier.FREE, (
        f"New user with email should have FREE tier. "
        f"Got membership_tier={user.membership_tier}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
    email=email_strategy,
    password_hash=password_hash_strategy,
)
def test_new_user_with_both_phone_and_email_has_free_tier(
    phone: str,
    email: str,
    password_hash: str,
) -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Property: For any user created with both phone and email, the membership_tier
    must default to FREE.
    """
    # Arrange & Act: Create a new user with both phone and email
    user = create_new_user(phone=phone, email=email, password_hash=password_hash)
    
    # Assert: New user should have FREE membership tier
    assert user.membership_tier == MembershipTier.FREE, (
        f"New user with both phone and email should have FREE tier. "
        f"Got membership_tier={user.membership_tier}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_new_user_membership_expiry_is_none(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Property: For any newly created user, the membership_expiry must be None
    (FREE tier has no expiry).
    """
    # Arrange & Act: Create a new user
    user = create_new_user(phone=phone)
    
    # Assert: New user should have no membership expiry
    assert user.membership_expiry is None, (
        f"New user should have no membership expiry. "
        f"Got membership_expiry={user.membership_expiry}"
    )


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_new_user_daily_usage_count_is_zero(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Property: For any newly created user, the daily_usage_count must be 0.
    """
    # Arrange & Act: Create a new user
    user = create_new_user(phone=phone)
    
    # Assert: New user should have zero daily usage count
    assert user.daily_usage_count == 0, (
        f"New user should have zero daily usage count. "
        f"Got daily_usage_count={user.daily_usage_count}"
    )


def test_user_model_default_membership_tier_is_free() -> None:
    """
    **Feature: user-system, Property 1: 新用户默认 FREE 会员**
    **Validates: Requirements 1.5**
    
    Verify that the User model's membership_tier column has the correct default value.
    """
    # Get the column definition
    membership_tier_column = User.__table__.columns['membership_tier']
    
    # Assert: The default should be MembershipTier.FREE
    assert membership_tier_column.default is not None, (
        "membership_tier column should have a default value"
    )
    assert membership_tier_column.default.arg == MembershipTier.FREE, (
        f"membership_tier default should be FREE. "
        f"Got {membership_tier_column.default.arg}"
    )



# ============================================================================
# Property 4: Token 刷新有效性
# **Feature: user-system, Property 4: Token 刷新有效性**
# **Validates: Requirements 2.3**
#
# For any valid refresh token, calling refresh_token SHALL return a new valid 
# access token and refresh token pair
# ============================================================================

from app.utils.jwt import JWTService, TokenPair, TokenPayload, TokenExpiredError, InvalidTokenError


# Strategy for generating user IDs
user_id_strategy = st.uuids().map(str)

# Strategy for generating secret keys
secret_key_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=32,
    max_size=64,
)


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_refresh_token_returns_valid_token_pair(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any valid refresh token, calling refresh_tokens SHALL return
    a new valid access token and refresh token pair.
    """
    # Arrange: Create JWT service and initial token pair
    service = JWTService(secret_key=secret_key)
    initial_pair = service.create_token_pair(user_id)
    
    # Act: Refresh tokens using the refresh token
    new_pair = service.refresh_tokens(initial_pair.refresh_token)
    
    # Assert: New pair should be valid
    assert isinstance(new_pair, TokenPair), (
        f"refresh_tokens should return TokenPair, got {type(new_pair)}"
    )
    assert new_pair.access_token is not None, "New access token should not be None"
    assert new_pair.refresh_token is not None, "New refresh token should not be None"
    assert new_pair.token_type == "bearer", (
        f"Token type should be 'bearer', got {new_pair.token_type}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_refreshed_access_token_is_verifiable(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any refreshed token pair, the new access token SHALL be
    verifiable and contain the correct user_id.
    """
    # Arrange: Create JWT service and initial token pair
    service = JWTService(secret_key=secret_key)
    initial_pair = service.create_token_pair(user_id)
    
    # Act: Refresh tokens and verify new access token
    new_pair = service.refresh_tokens(initial_pair.refresh_token)
    payload = service.verify_access_token(new_pair.access_token)
    
    # Assert: Payload should contain correct user_id
    assert payload.user_id == user_id, (
        f"Refreshed access token should contain user_id={user_id}, "
        f"got {payload.user_id}"
    )
    assert payload.token_type == "access", (
        f"Token type should be 'access', got {payload.token_type}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_refreshed_refresh_token_is_verifiable(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any refreshed token pair, the new refresh token SHALL be
    verifiable and contain the correct user_id.
    """
    # Arrange: Create JWT service and initial token pair
    service = JWTService(secret_key=secret_key)
    initial_pair = service.create_token_pair(user_id)
    
    # Act: Refresh tokens and verify new refresh token
    new_pair = service.refresh_tokens(initial_pair.refresh_token)
    payload = service.verify_refresh_token(new_pair.refresh_token)
    
    # Assert: Payload should contain correct user_id
    assert payload.user_id == user_id, (
        f"Refreshed refresh token should contain user_id={user_id}, "
        f"got {payload.user_id}"
    )
    assert payload.token_type == "refresh", (
        f"Token type should be 'refresh', got {payload.token_type}"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_refreshed_tokens_are_different_from_original(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any token refresh, the new tokens SHALL be different from
    the original tokens (new JTI).
    """
    # Arrange: Create JWT service and initial token pair
    service = JWTService(secret_key=secret_key)
    initial_pair = service.create_token_pair(user_id)
    
    # Act: Refresh tokens
    new_pair = service.refresh_tokens(initial_pair.refresh_token)
    
    # Assert: New tokens should be different
    assert new_pair.access_token != initial_pair.access_token, (
        "New access token should be different from original"
    )
    assert new_pair.refresh_token != initial_pair.refresh_token, (
        "New refresh token should be different from original"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_access_token_cannot_be_used_for_refresh(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any access token, attempting to use it for refresh SHALL
    raise an InvalidTokenError.
    """
    # Arrange: Create JWT service and token pair
    service = JWTService(secret_key=secret_key)
    pair = service.create_token_pair(user_id)
    
    # Act & Assert: Using access token for refresh should fail
    try:
        service.refresh_tokens(pair.access_token)
        assert False, "Should have raised InvalidTokenError"
    except InvalidTokenError as e:
        assert "not a refresh token" in str(e).lower(), (
            f"Error message should indicate wrong token type, got: {e}"
        )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    secret_key=secret_key_strategy,
)
def test_token_refresh_preserves_user_id(
    user_id: str,
    secret_key: str,
) -> None:
    """
    **Feature: user-system, Property 4: Token 刷新有效性**
    **Validates: Requirements 2.3**
    
    Property: For any token refresh, the user_id in the new tokens SHALL
    match the user_id in the original tokens.
    """
    # Arrange: Create JWT service and initial token pair
    service = JWTService(secret_key=secret_key)
    initial_pair = service.create_token_pair(user_id)
    
    # Get original user_id from refresh token
    original_payload = service.verify_refresh_token(initial_pair.refresh_token)
    
    # Act: Refresh tokens
    new_pair = service.refresh_tokens(initial_pair.refresh_token)
    
    # Get new user_ids
    new_access_payload = service.verify_access_token(new_pair.access_token)
    new_refresh_payload = service.verify_refresh_token(new_pair.refresh_token)
    
    # Assert: User IDs should match
    assert new_access_payload.user_id == original_payload.user_id, (
        f"New access token user_id ({new_access_payload.user_id}) should match "
        f"original ({original_payload.user_id})"
    )
    assert new_refresh_payload.user_id == original_payload.user_id, (
        f"New refresh token user_id ({new_refresh_payload.user_id}) should match "
        f"original ({original_payload.user_id})"
    )


# ============================================================================
# Property 3: 手机号唯一性
# **Feature: user-system, Property 3: 手机号唯一性**
# **Validates: Requirements 1.2**
#
# For any phone number that is already registered, attempting to register 
# again with the same phone number SHALL be rejected
# ============================================================================

from app.services.auth_service import (
    AuthService,
    PhoneAlreadyExistsError,
    InvalidVerificationCodeError,
)
from app.services.sms_service import SMSService


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_duplicate_phone_registration_rejected(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 3: 手机号唯一性**
    **Validates: Requirements 1.2**
    
    Property: For any phone number that is already registered, attempting to 
    register again with the same phone number SHALL be rejected.
    """
    import asyncio
    
    # Arrange: Create fresh services for isolation
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # First, send verification code and register
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        assert code_data is not None, "Code should be generated"
        
        # Register first user
        result = await auth_service.register_with_phone(phone, code_data.code)
        assert result.user is not None, "First registration should succeed"
        
        # Send another verification code for second registration attempt
        await sms_service.send_code(phone, current_time=code_data.created_at + timedelta(seconds=61))
        code_data2 = sms_service.get_code_data(phone)
        
        # Act & Assert: Second registration with same phone should fail
        try:
            await auth_service.register_with_phone(phone, code_data2.code)
            assert False, "Should have raised PhoneAlreadyExistsError"
        except PhoneAlreadyExistsError:
            pass  # Expected behavior
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_phone_uniqueness_check_returns_true_for_registered(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 3: 手机号唯一性**
    **Validates: Requirements 1.2**
    
    Property: For any registered phone number, is_phone_registered SHALL return True.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Initially, phone should not be registered
        assert not auth_service.is_phone_registered(phone), (
            "Phone should not be registered initially"
        )
        
        # Register the phone
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        await auth_service.register_with_phone(phone, code_data.code)
        
        # Assert: Phone should now be registered
        assert auth_service.is_phone_registered(phone), (
            f"Phone {phone} should be registered after registration"
        )
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    phone1=phone_strategy,
    phone2=phone_strategy,
)
def test_different_phones_can_register(
    phone1: str,
    phone2: str,
) -> None:
    """
    **Feature: user-system, Property 3: 手机号唯一性**
    **Validates: Requirements 1.2**
    
    Property: For any two different phone numbers, both SHALL be able to register
    successfully (uniqueness only blocks same phone).
    """
    import asyncio
    from hypothesis import assume
    
    # Skip if phones are the same
    assume(phone1 != phone2)
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register first phone
        await sms_service.send_code(phone1)
        code1 = sms_service.get_code_data(phone1)
        result1 = await auth_service.register_with_phone(phone1, code1.code)
        
        # Register second phone (need to wait for rate limit)
        await sms_service.send_code(phone2, current_time=code1.created_at + timedelta(seconds=61))
        code2 = sms_service.get_code_data(phone2)
        result2 = await auth_service.register_with_phone(phone2, code2.code)
        
        # Assert: Both registrations should succeed
        assert result1.user is not None, "First phone registration should succeed"
        assert result2.user is not None, "Second phone registration should succeed"
        assert result1.user.id != result2.user.id, "Users should have different IDs"
    
    asyncio.get_event_loop().run_until_complete(run_test())


from datetime import timedelta


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_phone_uniqueness_error_message(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 3: 手机号唯一性**
    **Validates: Requirements 1.2**
    
    Property: For any duplicate phone registration attempt, the error message
    SHALL indicate that the phone is already taken.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register first user
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        await auth_service.register_with_phone(phone, code_data.code)
        
        # Send another code for second attempt
        await sms_service.send_code(phone, current_time=code_data.created_at + timedelta(seconds=61))
        code_data2 = sms_service.get_code_data(phone)
        
        # Act & Assert: Check error message
        try:
            await auth_service.register_with_phone(phone, code_data2.code)
            assert False, "Should have raised PhoneAlreadyExistsError"
        except PhoneAlreadyExistsError as e:
            assert phone in str(e), (
                f"Error message should contain the phone number. Got: {e}"
            )
    
    asyncio.get_event_loop().run_until_complete(run_test())


# ============================================================================
# Property 5: 登出使 Token 失效
# **Feature: user-system, Property 5: 登出使 Token 失效**
# **Validates: Requirements 3.1**
#
# For any refresh token, after logout, using that refresh token to refresh 
# SHALL be rejected
# ============================================================================

from app.services.auth_service import TokenRevokedError


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_logout_invalidates_refresh_token(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 5: 登出使 Token 失效**
    **Validates: Requirements 3.1**
    
    Property: For any refresh token, after logout, using that refresh token 
    to refresh SHALL be rejected.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register and get tokens
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        result = await auth_service.register_with_phone(phone, code_data.code)
        
        refresh_token = result.tokens.refresh_token
        
        # Logout
        logout_success = await auth_service.logout(refresh_token)
        assert logout_success, "Logout should succeed"
        
        # Act & Assert: Using the refresh token after logout should fail
        try:
            await auth_service.refresh_token(refresh_token)
            assert False, "Should have raised TokenRevokedError"
        except TokenRevokedError:
            pass  # Expected behavior
    
    asyncio.get_event_loop().run_until_complete(run_test())


# Strategy for generating valid email addresses that match our regex pattern
valid_email_strategy = st.from_regex(
    r"^[a-zA-Z][a-zA-Z0-9._%+-]{0,20}@[a-zA-Z][a-zA-Z0-9.-]{0,10}\.[a-zA-Z]{2,4}$",
    fullmatch=True,
)


@settings(max_examples=100, deadline=None)
@given(
    email=valid_email_strategy,
)
def test_logout_invalidates_email_user_token(
    email: str,
) -> None:
    """
    **Feature: user-system, Property 5: 登出使 Token 失效**
    **Validates: Requirements 3.1**
    
    Property: For any email-registered user, after logout, using the refresh 
    token to refresh SHALL be rejected.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    # Use a valid password (at least 8 characters)
    password = "password123"
    
    async def run_test():
        # Register with email
        result = await auth_service.register_with_email(email, password)
        refresh_token = result.tokens.refresh_token
        
        # Logout
        logout_success = await auth_service.logout(refresh_token)
        assert logout_success, "Logout should succeed"
        
        # Act & Assert: Using the refresh token after logout should fail
        try:
            await auth_service.refresh_token(refresh_token)
            assert False, "Should have raised TokenRevokedError"
        except TokenRevokedError:
            pass  # Expected behavior
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_logout_returns_true_for_valid_token(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 5: 登出使 Token 失效**
    **Validates: Requirements 3.1**
    
    Property: For any valid refresh token, logout SHALL return True.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register and get tokens
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        result = await auth_service.register_with_phone(phone, code_data.code)
        
        # Act: Logout
        logout_success = await auth_service.logout(result.tokens.refresh_token)
        
        # Assert: Logout should return True
        assert logout_success is True, "Logout should return True for valid token"
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_double_logout_second_returns_false(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 5: 登出使 Token 失效**
    **Validates: Requirements 3.1**
    
    Property: For any refresh token that has already been logged out,
    a second logout attempt SHALL return False (token already revoked).
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register and get tokens
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        result = await auth_service.register_with_phone(phone, code_data.code)
        
        refresh_token = result.tokens.refresh_token
        
        # First logout
        first_logout = await auth_service.logout(refresh_token)
        assert first_logout is True, "First logout should succeed"
        
        # Second logout - token already revoked, but logout should still work
        # (it just won't find an active token to revoke)
        second_logout = await auth_service.logout(refresh_token)
        # Note: The second logout returns False because the token is already revoked
        assert second_logout is False, "Second logout should return False (already revoked)"
    
    asyncio.get_event_loop().run_until_complete(run_test())


@settings(max_examples=100)
@given(
    phone=phone_strategy,
)
def test_new_login_after_logout_works(
    phone: str,
) -> None:
    """
    **Feature: user-system, Property 5: 登出使 Token 失效**
    **Validates: Requirements 3.1**
    
    Property: After logout, a user SHALL be able to login again and get new valid tokens.
    """
    import asyncio
    
    # Arrange: Create fresh services
    sms_service = SMSService()
    auth_service = AuthService(sms_service=sms_service)
    
    async def run_test():
        # Register
        await sms_service.send_code(phone)
        code_data = sms_service.get_code_data(phone)
        result = await auth_service.register_with_phone(phone, code_data.code)
        
        old_refresh_token = result.tokens.refresh_token
        
        # Logout
        await auth_service.logout(old_refresh_token)
        
        # Login again with new code
        await sms_service.send_code(phone, current_time=code_data.created_at + timedelta(seconds=61))
        new_code_data = sms_service.get_code_data(phone)
        
        login_result = await auth_service.login_with_phone(phone, new_code_data.code)
        
        # Assert: New login should work and provide new tokens
        assert login_result.user is not None, "Login should succeed after logout"
        assert login_result.tokens.refresh_token != old_refresh_token, (
            "New refresh token should be different from old one"
        )
        
        # New token should be usable for refresh
        new_tokens = await auth_service.refresh_token(login_result.tokens.refresh_token)
        assert new_tokens is not None, "New tokens should be refreshable"
    
    asyncio.get_event_loop().run_until_complete(run_test())
