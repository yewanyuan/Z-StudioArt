"""Auth API Integration Tests for PopGraph.

Tests the authentication HTTP API endpoints including:
- Send verification code (/api/auth/send-code)
- Phone registration (/api/auth/register/phone)
- Email registration (/api/auth/register/email)
- Phone login (/api/auth/login/phone)
- Email login (/api/auth/login/email)
- Token refresh (/api/auth/refresh)
- Logout (/api/auth/logout)
- Get current user (/api/auth/me)

Requirements: 1.1, 1.7, 2.1, 2.6, 3.1
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import MembershipTier
from app.services.auth_service import AuthService, get_auth_service, reset_auth_service
from app.services.sms_service import SMSService, get_sms_service, reset_sms_service


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_services():
    """Reset auth and SMS services before each test."""
    reset_auth_service()
    reset_sms_service()
    yield
    reset_auth_service()
    reset_sms_service()


@pytest.fixture
def auth_service():
    """Get a fresh auth service instance."""
    return get_auth_service()


@pytest.fixture
def sms_service():
    """Get a fresh SMS service instance."""
    return get_sms_service()


# ============================================================================
# Test: Send Verification Code
# ============================================================================

class TestSendVerificationCode:
    """Test send verification code endpoint."""

    def test_send_code_success(self, client):
        """Test successful verification code sending.
        
        Requirements: 1.6 - Send SMS verification code
        """
        response = client.post(
            "/api/auth/send-code",
            json={"phone": "13800138000"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "验证码已发送" in data["message"]

    def test_send_code_invalid_phone(self, client):
        """Test sending code to invalid phone number.
        
        Requirements: 1.4 - Validate phone format
        """
        response = client.post(
            "/api/auth/send-code",
            json={"phone": "12345"},
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_send_code_invalid_phone_format(self, client):
        """Test sending code to phone with invalid format."""
        response = client.post(
            "/api/auth/send-code",
            json={"phone": "23800138000"},  # Doesn't start with 1[3-9]
        )
        
        assert response.status_code == 422


# ============================================================================
# Test: Phone Registration
# ============================================================================

class TestPhoneRegistration:
    """Test phone registration endpoint."""

    def test_register_phone_success(self, client, sms_service):
        """Test successful phone registration.
        
        Requirements: 1.1 - Create user with phone and verification code
        Requirements: 1.5 - Assign FREE membership tier
        """
        phone = "13800138001"
        
        # First send verification code
        send_response = client.post(
            "/api/auth/send-code",
            json={"phone": phone},
        )
        assert send_response.status_code == 200
        
        # Get the code from SMS service (for testing)
        code_data = sms_service.get_code_data(phone)
        assert code_data is not None
        
        # Register with the code
        response = client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["user"]["phone"] == phone
        assert data["user"]["membership_tier"] == MembershipTier.FREE.value
        
        # Check tokens
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"

    def test_register_phone_already_exists(self, client, sms_service):
        """Test registration with existing phone number.
        
        Requirements: 1.2 - Reject if phone already exists
        """
        phone = "13800138002"
        
        # First registration
        client.post("/api/auth/send-code", json={"phone": phone})
        code_data = sms_service.get_code_data(phone)
        client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        # Wait for rate limit and send new code
        import time
        time.sleep(0.1)  # Small delay
        
        # Try to register again (need new code since old one is used)
        # This should fail because phone already exists
        response = client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": "123456"},
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "PHONE_EXISTS"

    def test_register_phone_invalid_code(self, client):
        """Test registration with invalid verification code.
        
        Requirements: 1.3 - Reject invalid verification code
        """
        phone = "13800138003"
        
        # Send code first
        client.post("/api/auth/send-code", json={"phone": phone})
        
        # Try to register with wrong code
        response = client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": "000000"},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CODE"


# ============================================================================
# Test: Email Registration
# ============================================================================

class TestEmailRegistration:
    """Test email registration endpoint."""

    def test_register_email_success(self, client):
        """Test successful email registration.
        
        Requirements: 1.7 - Support email registration
        Requirements: 1.5 - Assign FREE membership tier
        """
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["membership_tier"] == MembershipTier.FREE.value
        
        # Check tokens
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_register_email_already_exists(self, client):
        """Test registration with existing email."""
        email = "duplicate@example.com"
        
        # First registration
        client.post(
            "/api/auth/register/email",
            json={"email": email, "password": "password123"},
        )
        
        # Try to register again
        response = client.post(
            "/api/auth/register/email",
            json={"email": email, "password": "password456"},
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "EMAIL_EXISTS"

    def test_register_email_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "weak@example.com",
                "password": "short",  # Less than 8 characters
            },
        )
        
        assert response.status_code == 422  # Pydantic validation

    def test_register_email_invalid_format(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )
        
        assert response.status_code == 422


# ============================================================================
# Test: Phone Login
# ============================================================================

class TestPhoneLogin:
    """Test phone login endpoint."""

    def test_login_phone_success(self, client, sms_service):
        """Test successful phone login.
        
        Requirements: 2.1 - Return valid tokens on successful login
        """
        phone = "13800138010"
        
        # Register first
        client.post("/api/auth/send-code", json={"phone": phone})
        code_data = sms_service.get_code_data(phone)
        client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        # Wait for rate limit
        import time
        time.sleep(61)  # Wait for rate limit to expire
        
        # Send new code for login
        client.post("/api/auth/send-code", json={"phone": phone})
        code_data = sms_service.get_code_data(phone)
        
        # Login
        response = client.post(
            "/api/auth/login/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["phone"] == phone
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_login_phone_user_not_found(self, client, sms_service):
        """Test login with non-existent phone number."""
        phone = "13800138011"
        
        # Send code but don't register
        client.post("/api/auth/send-code", json={"phone": phone})
        code_data = sms_service.get_code_data(phone)
        
        # Try to login
        response = client.post(
            "/api/auth/login/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "USER_NOT_FOUND"

    def test_login_phone_invalid_code(self, client, sms_service):
        """Test login with invalid verification code."""
        phone = "13800138012"
        
        # Register first
        client.post("/api/auth/send-code", json={"phone": phone})
        code_data = sms_service.get_code_data(phone)
        client.post(
            "/api/auth/register/phone",
            json={"phone": phone, "code": code_data.code},
        )
        
        # Try to login with wrong code
        response = client.post(
            "/api/auth/login/phone",
            json={"phone": phone, "code": "000000"},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CODE"


# ============================================================================
# Test: Email Login
# ============================================================================

class TestEmailLogin:
    """Test email login endpoint."""

    def test_login_email_success(self, client):
        """Test successful email login.
        
        Requirements: 2.6 - Support email login
        """
        email = "login@example.com"
        password = "password123"
        
        # Register first
        client.post(
            "/api/auth/register/email",
            json={"email": email, "password": password},
        )
        
        # Login
        response = client.post(
            "/api/auth/login/email",
            json={"email": email, "password": password},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == email
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    def test_login_email_wrong_password(self, client):
        """Test login with wrong password."""
        email = "wrongpass@example.com"
        
        # Register first
        client.post(
            "/api/auth/register/email",
            json={"email": email, "password": "correctpassword"},
        )
        
        # Try to login with wrong password
        response = client.post(
            "/api/auth/login/email",
            json={"email": email, "password": "wrongpassword"},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"

    def test_login_email_not_found(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login/email",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"


# ============================================================================
# Test: Token Refresh
# ============================================================================

class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_token_success(self, client):
        """Test successful token refresh.
        
        Requirements: 2.3 - Allow token refresh with valid refresh token
        """
        # Register to get tokens
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "refresh@example.com",
                "password": "password123",
            },
        )
        tokens = response.json()["tokens"]
        
        # Refresh tokens
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != tokens["refresh_token"]

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token.
        
        Requirements: 2.4 - Require re-authentication if token invalid
        """
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "TOKEN_INVALID"

    def test_refresh_token_after_logout(self, client):
        """Test refresh with revoked token (after logout).
        
        Requirements: 3.1 - Invalidate refresh token on logout
        """
        # Register to get tokens
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "logout-refresh@example.com",
                "password": "password123",
            },
        )
        tokens = response.json()["tokens"]
        
        # Logout
        client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        # Try to refresh with revoked token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "TOKEN_REVOKED"


# ============================================================================
# Test: Logout
# ============================================================================

class TestLogout:
    """Test logout endpoint."""

    def test_logout_success(self, client):
        """Test successful logout.
        
        Requirements: 3.1 - Invalidate refresh token on logout
        """
        # Register to get tokens
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "logout@example.com",
                "password": "password123",
            },
        )
        tokens = response.json()["tokens"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "登出成功" in data["message"]

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token."""
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": "invalid-token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


# ============================================================================
# Test: Get Current User
# ============================================================================

class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_me_success(self, client):
        """Test getting current user info."""
        # Register to get tokens
        response = client.post(
            "/api/auth/register/email",
            json={
                "email": "me@example.com",
                "password": "password123",
            },
        )
        tokens = response.json()["tokens"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["membership_tier"] == MembershipTier.FREE.value

    def test_get_me_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "UNAUTHORIZED"

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "TOKEN_INVALID"


# ============================================================================
# Test: Full Authentication Flow
# ============================================================================

class TestFullAuthFlow:
    """Test complete authentication flows."""

    def test_email_registration_login_refresh_logout_flow(self, client):
        """Test complete email authentication flow.
        
        Requirements: 1.7, 2.6, 2.3, 3.1
        """
        email = "fullflow@example.com"
        password = "password123"
        
        # 1. Register
        response = client.post(
            "/api/auth/register/email",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        tokens = response.json()["tokens"]
        
        # 2. Access protected endpoint
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == email
        
        # 3. Refresh tokens
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        new_tokens = response.json()
        
        # 4. Access with new token
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert response.status_code == 200
        
        # 5. Logout
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert response.status_code == 200
        
        # 6. Old refresh token should be invalid
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert response.status_code == 401
        
        # 7. Login again
        response = client.post(
            "/api/auth/login/email",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["tokens"]
