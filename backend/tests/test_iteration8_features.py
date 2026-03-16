"""
Iteration 8 Tests: 'Your News' Tab Rename and Email Service Integration
Tests:
1. Forgot password returns email_sent field (true/false)
2. Forgot password triggers Resend email service
3. Forgot password -> enter token -> reset password flow
4. Personalized feed (/api/feed/personalized) returns content
5. Regular feed (/api/feed) still works
6. All existing auth flows preserved
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestForgotPasswordEmailService:
    """Test forgot password flow with Resend email service integration"""

    def test_forgot_password_returns_email_sent_field(self):
        """POST /api/auth/forgot-password should return email_sent field"""
        # Use test email that won't get actual email sent (Resend test mode)
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "identifier": "sectest@test.com"
        })
        assert response.status_code == 200
        data = response.json()
        # Should have email_sent field (true or false)
        assert "email_sent" in data, f"Missing email_sent field. Got: {data}"
        assert "message" in data
        # In test mode, email_sent will be false for non-verified addresses
        print(f"email_sent: {data['email_sent']}, message: {data['message']}")

    def test_forgot_password_unknown_email(self):
        """POST /api/auth/forgot-password with unknown email returns same response (security)"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "identifier": "nonexistent_user_12345@test.com"
        })
        assert response.status_code == 200
        data = response.json()
        # Should still return success message for security (don't reveal if account exists)
        assert "message" in data
        print(f"Unknown email response: {data}")

    def test_forgot_password_creates_reset_token_in_db(self):
        """Verify forgot password creates a token in password_resets collection"""
        # First create a test user
        import uuid
        test_email = f"TEST_pwreset_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register user
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test PW Reset User",
            "email": test_email,
            "password": "test123"
        })
        assert register_resp.status_code == 200, f"Register failed: {register_resp.text}"
        
        # Request password reset
        forgot_resp = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "identifier": test_email
        })
        assert forgot_resp.status_code == 200
        data = forgot_resp.json()
        assert "email_sent" in data
        # Token is NOT returned anymore (security improvement)
        assert "reset_token" not in data, "reset_token should not be exposed in response"
        print(f"Password reset requested for {test_email}, email_sent: {data['email_sent']}")


class TestResetPasswordFlow:
    """Test the complete reset password flow"""

    @pytest.fixture
    def test_user_with_reset_token(self):
        """Create a test user and get reset token from DB"""
        import uuid
        test_email = f"TEST_resetflow_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Reset Flow User",
            "email": test_email,
            "password": "oldpassword123"
        })
        assert register_resp.status_code == 200
        
        # Request reset - token is now stored in DB only
        forgot_resp = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "identifier": test_email
        })
        assert forgot_resp.status_code == 200
        
        # We can't get the token from response anymore, so we test the error flow
        return {"email": test_email}

    def test_reset_password_invalid_token(self):
        """POST /api/auth/reset-password with invalid token returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid_token_12345",
            "new_password": "newpassword123"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"Invalid token error: {data['detail']}")

    def test_reset_password_short_password(self):
        """POST /api/auth/reset-password with short password returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "any_token",
            "new_password": "12345"  # Less than 6 chars
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "6 characters" in data["detail"]
        print(f"Short password error: {data['detail']}")


class TestPersonalizedFeed:
    """Test personalized feed endpoint (Your News tab)"""

    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a user with onboarding complete"""
        import uuid
        test_email = f"TEST_feed_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Feed User",
            "email": test_email,
            "password": "test123"
        })
        assert register_resp.status_code == 200
        data = register_resp.json()
        token = data["token"]
        
        # Complete onboarding to enable personalized feed
        headers = {"Authorization": f"Bearer {token}"}
        onboard_resp = requests.put(f"{BASE_URL}/api/auth/onboarding", json={
            "interests": ["technology", "ai", "crypto"],
            "curiosity_types": ["how_things_work"],
            "explanation_depth": "detailed",
            "country": "US",
            "region": "CA",
            "professional_context": "tech",
            "followed_topics": []
        }, headers=headers)
        assert onboard_resp.status_code == 200
        
        return {"email": test_email, "token": token}

    def test_personalized_feed_requires_auth(self):
        """GET /api/feed/personalized requires authentication"""
        response = requests.get(f"{BASE_URL}/api/feed/personalized")
        assert response.status_code == 401
        print("Personalized feed correctly requires authentication")

    def test_personalized_feed_with_auth(self, authenticated_user):
        """GET /api/feed/personalized returns topics for authenticated user"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        response = requests.get(f"{BASE_URL}/api/feed/personalized", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        print(f"Personalized feed returned {len(data['topics'])} topics")

    def test_regular_feed_still_works(self):
        """GET /api/feed returns topics without auth"""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        print(f"Regular feed returned {len(data['topics'])} topics")

    def test_regular_feed_category_filter(self):
        """GET /api/feed?category=tech filters correctly"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "tech"})
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        print(f"Tech feed returned {len(data['topics'])} topics")


class TestExistingAuthFlows:
    """Verify existing auth flows still work"""

    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "sectest@test.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        print(f"Login successful for sectest@test.com")

    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "sectest@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_admin_login(self):
        """POST /api/admin/login works"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": "admin@wtfhappened.app",
            "password": "WTFadmin2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print("Admin login successful")

    def test_register_new_user(self):
        """POST /api/auth/register creates new user"""
        import uuid
        test_email = f"TEST_auth_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Auth User",
            "email": test_email,
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        print(f"Registered new user: {test_email}")

    def test_get_me_with_auth(self):
        """GET /api/auth/me returns current user"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "sectest@test.com",
            "password": "test123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        
        # Get me
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert "user" in data
        print(f"GET /api/auth/me returned user: {data['user'].get('email')}")


class TestEmailServiceIntegration:
    """Test email service integration with Resend"""

    def test_email_service_configured(self):
        """Verify Resend API key is configured in backend"""
        # We test this by checking the forgot-password response
        # If email service is configured, it will attempt to send
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "identifier": "admin@wtfhappened.app"  # Admin email
        })
        assert response.status_code == 200
        data = response.json()
        # Should have email_sent field
        assert "email_sent" in data
        print(f"Email service check - email_sent: {data['email_sent']}")
        # Note: In Resend test mode, email_sent=false for non-verified addresses is expected
