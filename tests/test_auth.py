"""
Unit tests for supabase_micro auth module.
"""

import sys
import os
import unittest
import time
import json
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from supabase_micro.auth import AuthClient


class TestJWTDecoding(unittest.TestCase):
    """Test JWT payload decoding."""

    def setUp(self):
        """Set up test client."""
        self.mock_client = Mock()
        self.mock_client.url = "https://test.supabase.co"
        self.mock_client.key = "test-key"
        self.auth = AuthClient(self.mock_client)

    def test_decode_valid_jwt(self):
        """Test decoding a valid JWT."""
        # Sample JWT with payload: {"sub": "123", "email": "test@example.com", "exp": 1234567890}
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"

        payload = self.auth._decode_jwt_payload(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "123")
        self.assertEqual(payload["email"], "test@example.com")
        self.assertEqual(payload["exp"], 1234567890)

    def test_decode_invalid_jwt(self):
        """Test decoding an invalid JWT."""
        invalid_token = "invalid.token"

        payload = self.auth._decode_jwt_payload(invalid_token)

        self.assertIsNone(payload)

    def test_decode_empty_jwt(self):
        """Test decoding an empty JWT."""
        payload = self.auth._decode_jwt_payload("")

        self.assertIsNone(payload)


class TestSessionManagement(unittest.TestCase):
    """Test session storage and management."""

    def setUp(self):
        """Set up test client."""
        self.mock_client = Mock()
        self.mock_client.url = "https://test.supabase.co"
        self.mock_client.key = "test-key"
        self.auth = AuthClient(self.mock_client)

    def test_initial_session_is_none(self):
        """Test that session is initially None."""
        self.assertIsNone(self.auth._session)

    def test_set_session(self):
        """Test setting a session."""
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"
        refresh_token = "refresh-token-123"
        user = {"id": "123", "email": "test@example.com"}

        self.auth._set_session(access_token, refresh_token, user)

        self.assertIsNotNone(self.auth._session)
        self.assertEqual(self.auth._session["access_token"], access_token)
        self.assertEqual(self.auth._session["refresh_token"], refresh_token)
        self.assertEqual(self.auth._session["user"], user)
        self.assertEqual(self.auth._session["expires_at"], 1234567890)

    def test_set_session_extracts_user_from_jwt(self):
        """Test that _set_session extracts user from JWT if not provided."""
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTAsInVzZXJfbWV0YWRhdGEiOnsibmFtZSI6IlRlc3QifX0.signature"
        refresh_token = "refresh-token-123"

        self.auth._set_session(access_token, refresh_token)

        self.assertIsNotNone(self.auth._session)
        self.assertIsNotNone(self.auth._session["user"])
        self.assertEqual(self.auth._session["user"]["id"], "123")
        self.assertEqual(self.auth._session["user"]["email"], "test@example.com")
        self.assertIn("user_metadata", self.auth._session["user"])

    def test_clear_session(self):
        """Test clearing a session."""
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"
        self.auth._set_session(access_token, "refresh-token", {"id": "123"})

        self.auth._clear_session()

        self.assertIsNone(self.auth._session)

    def test_get_session_returns_current_session(self):
        """Test get_session returns current session."""
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"
        self.auth._set_session(access_token, "refresh-token", {"id": "123"})

        result = self.auth.get_session()

        self.assertEqual(result["status_code"], 200)
        self.assertIsNotNone(result["data"]["session"])
        self.assertEqual(result["data"]["session"]["access_token"], access_token)

    def test_get_session_returns_none_when_no_session(self):
        """Test get_session returns None when no session exists."""
        result = self.auth.get_session()

        self.assertEqual(result["status_code"], 200)
        self.assertIsNone(result["data"]["session"])


class TestAuthMethods(unittest.TestCase):
    """Test authentication methods with mocked HTTP."""

    def setUp(self):
        """Set up test client with mocked HTTP."""
        self.mock_http_client = Mock()
        self.mock_client = Mock()
        self.mock_client.url = "https://test.supabase.co"
        self.mock_client.key = "test-key"
        self.mock_client.http_client = self.mock_http_client
        self.auth = AuthClient(self.mock_client)

    def test_sign_up_success(self):
        """Test successful signup."""
        # Mock HTTP response
        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps({
                "user": {"id": "123", "email": "test@example.com"},
                "session": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                    "refresh_token": "refresh-token-123"
                }
            }).encode('utf-8')
        }

        result = self.auth.sign_up("test@example.com", "password123")

        self.assertEqual(result["status_code"], 200)
        self.assertIn("user", result["data"])
        self.assertEqual(result["data"]["user"]["email"], "test@example.com")
        # Session should be stored
        self.assertIsNotNone(self.auth._session)

    def test_sign_up_with_metadata(self):
        """Test signup with user metadata."""
        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps({
                "user": {"id": "123", "email": "test@example.com", "user_metadata": {"name": "Test"}},
                "session": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                    "refresh_token": "refresh-token-123"
                }
            }).encode('utf-8')
        }

        result = self.auth.sign_up(
            "test@example.com",
            "password123",
            options={"data": {"name": "Test"}}
        )

        self.assertEqual(result["status_code"], 200)
        # Check that request was made with metadata
        call_args = self.mock_http_client.request.call_args
        body = call_args[1]["body"]
        body_dict = json.loads(body)
        self.assertIn("data", body_dict)

    def test_sign_in_success(self):
        """Test successful signin."""
        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps({
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                "refresh_token": "refresh-token-123",
                "user": {"id": "123", "email": "test@example.com"}
            }).encode('utf-8')
        }

        result = self.auth.sign_in_with_password("test@example.com", "password123")

        self.assertEqual(result["status_code"], 200)
        self.assertIn("access_token", result["data"])
        # Session should be stored
        self.assertIsNotNone(self.auth._session)
        self.assertEqual(self.auth._session["access_token"], result["data"]["access_token"])

    def test_sign_in_failure(self):
        """Test failed signin."""
        self.mock_http_client.request.return_value = {
            "status_code": 400,
            "body": {"message": "Invalid credentials"}
        }

        result = self.auth.sign_in_with_password("test@example.com", "wrongpassword")

        self.assertEqual(result["status_code"], 400)
        self.assertIn("error", result)
        # Session should not be stored
        self.assertIsNone(self.auth._session)

    def test_sign_out(self):
        """Test sign out."""
        # Set up a session first
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-token-123",
            {"id": "123"}
        )

        self.mock_http_client.request.return_value = {
            "status_code": 204,
            "body": {}
        }

        result = self.auth.sign_out()

        self.assertEqual(result["status_code"], 204)
        # Session should be cleared
        self.assertIsNone(self.auth._session)

    def test_get_user_from_session(self):
        """Test getting user from cached session."""
        user = {"id": "123", "email": "test@example.com"}
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-token-123",
            user
        )

        result = self.auth.get_user()

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["data"]["user"], user)
        # Should not make HTTP request
        self.mock_http_client.request.assert_not_called()

    def test_get_user_from_api(self):
        """Test getting user from API when not cached."""
        # Bypass _set_session to avoid JWT-based user extraction
        self.auth._session = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh_token": "refresh-token-123",
            "expires_at": None,
            "user": None  # No cached user, forces API call
        }

        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps({"user": {"id": "123", "email": "test@example.com"}}).encode('utf-8')
        }

        result = self.auth.get_user()

        self.assertEqual(result["status_code"], 200)
        # Should make HTTP request
        self.mock_http_client.request.assert_called_once()

    def test_get_user_no_session(self):
        """Test getting user with no session."""
        result = self.auth.get_user()

        self.assertEqual(result["status_code"], 401)
        self.assertIn("error", result)

    def test_refresh_session(self):
        """Test refreshing session."""
        self.auth._set_session(
            "old-access-token",
            "refresh-token-123",
            {"id": "123"}
        )

        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                "refresh_token": "new-refresh-token",
                "user": {"id": "123", "email": "test@example.com"}
            }
        }

        result = self.auth.refresh_session()

        self.assertEqual(result["status_code"], 200)
        # Session should be updated
        self.assertNotEqual(self.auth._session["access_token"], "old-access-token")

    def test_refresh_session_no_token(self):
        """Test refresh with no refresh token."""
        result = self.auth.refresh_session()

        self.assertEqual(result["status_code"], 400)
        self.assertIn("error", result)

    def test_update_user(self):
        """Test updating user."""
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-token-123",
            {"id": "123", "email": "test@example.com"}
        )

        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps({
                "user": {"id": "123", "email": "test@example.com", "user_metadata": {"name": "Updated"}}
            }).encode('utf-8')
        }

        result = self.auth.update_user({"data": {"name": "Updated"}})

        self.assertEqual(result["status_code"], 200)
        # Cached user should be updated
        self.assertEqual(self.auth._session["user"]["user_metadata"]["name"], "Updated")

    def test_update_user_no_session(self):
        """Test updating user with no session."""
        result = self.auth.update_user({"data": {"name": "Test"}})

        self.assertEqual(result["status_code"], 401)
        self.assertIn("error", result)

    def test_reset_password_for_email(self):
        """Test password reset."""
        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": {}
        }

        result = self.auth.reset_password_for_email(
            "test@example.com",
            options={"redirect_to": "http://localhost:3000/reset"}
        )

        self.assertEqual(result["status_code"], 200)


class TestRequestBuilding(unittest.TestCase):
    """Test request building and headers."""

    def setUp(self):
        """Set up test client."""
        self.mock_http_client = Mock()
        self.mock_client = Mock()
        self.mock_client.url = "https://test.supabase.co"
        self.mock_client.key = "test-anon-key"
        self.mock_client.http_client = self.mock_http_client
        self.auth = AuthClient(self.mock_client)

    def test_request_without_session_uses_anon_key(self):
        """Test that requests without session use anon key."""
        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": {}
        }

        self.auth._request("POST", "/signup", {"email": "test@example.com"})

        call_args = self.mock_http_client.request.call_args
        headers = call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test-anon-key")

    def test_request_with_session_uses_access_token(self):
        """Test that requests with session use access token."""
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-token-123",
            {"id": "123"}
        )

        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": {}
        }

        self.auth._request("GET", "/user")

        call_args = self.mock_http_client.request.call_args
        headers = call_args[1]["headers"]
        self.assertIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", headers["Authorization"])


class TestAutoRefresh(unittest.TestCase):
    """Test auto-refresh functionality."""

    def setUp(self):
        """Set up mock client for testing."""
        self.mock_http_client = Mock()
        self.mock_client = Mock()
        self.mock_client.http_client = self.mock_http_client
        self.mock_client.url = "https://test.supabase.co"
        self.mock_client.key = "test-key"

        self.auth = AuthClient(self.mock_client)

    def test_should_refresh_token_no_session(self):
        """Test should_refresh_token with no active session."""
        result = self.auth.should_refresh_token()

        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["data"]["should_refresh"])

    def test_should_refresh_token_not_expired(self):
        """Test should_refresh_token when token is fresh."""
        # Set up session that expires in 30 minutes
        current_time = int(time.time())
        expires_at = current_time + 1800  # 30 minutes

        self.auth._session = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        # Check with 5 minute threshold - should not need refresh
        result = self.auth.should_refresh_token(threshold_seconds=300)

        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["data"]["should_refresh"])
        self.assertGreater(result["data"]["expires_in"], 300)

    def test_should_refresh_token_near_expiry(self):
        """Test should_refresh_token when token expires soon."""
        # Set up session that expires in 3 minutes
        current_time = int(time.time())
        expires_at = current_time + 180  # 3 minutes

        self.auth._session = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        # Check with 5 minute threshold - should need refresh
        result = self.auth.should_refresh_token(threshold_seconds=300)

        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["data"]["should_refresh"])
        self.assertLess(result["data"]["expires_in"], 300)

    def test_should_refresh_token_expired(self):
        """Test should_refresh_token when token is already expired."""
        # Set up session that expired 1 minute ago
        current_time = int(time.time())
        expires_at = current_time - 60  # 1 minute ago

        self.auth._session = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        result = self.auth.should_refresh_token()

        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["data"]["should_refresh"])
        self.assertEqual(result["data"]["expires_in"], 0)  # Already expired

    def test_refresh_if_needed_does_not_refresh_fresh_token(self):
        """Test refresh_if_needed skips refresh for fresh tokens."""
        # Set up session that expires in 30 minutes
        current_time = int(time.time())
        expires_at = current_time + 1800

        self.auth._session = {
            "access_token": "old-token",
            "refresh_token": "refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        result = self.auth.refresh_if_needed(threshold_seconds=300)

        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["data"]["refreshed"])
        self.assertEqual(self.auth._session["access_token"], "old-token")
        # Should not have called refresh endpoint
        self.mock_http_client.request.assert_not_called()

    def test_refresh_if_needed_refreshes_expiring_token(self):
        """Test refresh_if_needed refreshes tokens near expiry."""
        # Set up session that expires in 2 minutes
        current_time = int(time.time())
        expires_at = current_time + 120

        self.auth._session = {
            "access_token": "old-token",
            "refresh_token": "old-refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        # Mock refresh response
        new_expires_at = current_time + 3600  # New token expires in 1 hour
        refresh_response = {
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "user": {"id": "123"},
            "expires_at": new_expires_at
        }

        self.mock_http_client.request.return_value = {
            "status_code": 200,
            "body": json.dumps(refresh_response).encode('utf-8')
        }

        result = self.auth.refresh_if_needed(threshold_seconds=300)

        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["data"]["refreshed"])
        self.assertEqual(self.auth._session["access_token"], "new-token")
        self.assertEqual(self.auth._session["refresh_token"], "new-refresh")

    def test_refresh_if_needed_handles_refresh_failure(self):
        """Test refresh_if_needed handles refresh errors gracefully."""
        # Set up expiring session
        current_time = int(time.time())
        expires_at = current_time + 120

        self.auth._session = {
            "access_token": "old-token",
            "refresh_token": "old-refresh",
            "expires_at": expires_at,
            "user": {"id": "123"}
        }

        # Mock refresh failure
        self.mock_http_client.request.return_value = {
            "status_code": 401,
            "body": json.dumps({"message": "Invalid refresh token"}).encode('utf-8')
        }

        result = self.auth.refresh_if_needed(threshold_seconds=300)

        self.assertEqual(result["status_code"], 401)
        self.assertIn("error", result)
        # Session should remain unchanged on failure
        self.assertEqual(self.auth._session["access_token"], "old-token")


if __name__ == "__main__":
    unittest.main()
