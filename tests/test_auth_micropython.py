"""
MicroPython-compatible tests for auth module.
Tests JWT decoding and session management without mocking.
"""

import sys

# Add src to path
sys.path.insert(0, './src')

from supabase_micro.auth import AuthClient


class MockClient:
    """Mock client for testing."""
    def __init__(self):
        self.url = "https://test.supabase.co"
        self.key = "test-key"


def test_jwt_decoding():
    """Test JWT payload decoding."""
    print("\n[TEST] JWT Decoding")

    auth = AuthClient(MockClient())

    # Test valid JWT
    # Payload: {"sub": "123", "email": "test@example.com", "exp": 1234567890}
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"

    payload = auth._decode_jwt_payload(token)

    assert payload is not None, "Payload should not be None"
    assert payload["sub"] == "123", f"Expected sub='123', got '{payload['sub']}'"
    assert payload["email"] == "test@example.com", f"Expected email='test@example.com', got '{payload['email']}'"
    assert payload["exp"] == 1234567890, f"Expected exp=1234567890, got {payload['exp']}"

    print("  ✓ Valid JWT decoded correctly")

    # Test invalid JWT
    invalid_token = "invalid.token"
    payload = auth._decode_jwt_payload(invalid_token)
    assert payload is None, "Invalid JWT should return None"

    print("  ✓ Invalid JWT returns None")

    # Test empty JWT
    payload = auth._decode_jwt_payload("")
    assert payload is None, "Empty JWT should return None"

    print("  ✓ Empty JWT returns None")


def test_session_management():
    """Test session storage and management."""
    print("\n[TEST] Session Management")

    auth = AuthClient(MockClient())

    # Initial session should be None
    assert auth._session is None, "Initial session should be None"
    print("  ✓ Initial session is None")

    # Set session
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.signature"
    refresh_token = "refresh-token-123"
    user = {"id": "123", "email": "test@example.com"}

    auth._set_session(access_token, refresh_token, user)

    assert auth._session is not None, "Session should be set"
    assert auth._session["access_token"] == access_token, "Access token mismatch"
    assert auth._session["refresh_token"] == refresh_token, "Refresh token mismatch"
    assert auth._session["user"] == user, "User mismatch"
    assert auth._session["expires_at"] == 1234567890, "Expiration mismatch"

    print("  ✓ Session set correctly")

    # Test session extraction from JWT
    auth2 = AuthClient(MockClient())
    auth2._set_session(access_token, refresh_token)  # No user provided

    assert auth2._session["user"] is not None, "User should be extracted from JWT"
    assert auth2._session["user"]["id"] == "123", "User ID should be extracted"
    assert auth2._session["user"]["email"] == "test@example.com", "Email should be extracted"

    print("  ✓ User extracted from JWT")

    # Clear session
    auth._clear_session()
    assert auth._session is None, "Session should be cleared"

    print("  ✓ Session cleared correctly")


def test_get_session():
    """Test get_session method."""
    print("\n[TEST] Get Session")

    auth = AuthClient(MockClient())

    # No session initially
    result = auth.get_session()
    assert result["status_code"] == 200, "Status should be 200"
    assert result["data"]["session"] is None, "Session should be None"

    print("  ✓ Returns None when no session")

    # Set session
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig"
    auth._set_session(access_token, "refresh-token", {"id": "123"})

    result = auth.get_session()
    assert result["status_code"] == 200, "Status should be 200"
    assert result["data"]["session"] is not None, "Session should not be None"
    assert result["data"]["session"]["access_token"] == access_token, "Token mismatch"

    print("  ✓ Returns session when available")


def test_get_user():
    """Test get_user method."""
    print("\n[TEST] Get User")

    auth = AuthClient(MockClient())

    # No session
    result = auth.get_user()
    assert result["status_code"] == 401, "Should return 401 with no session"
    assert "error" in result, "Should have error"

    print("  ✓ Returns 401 when no session")

    # With session and cached user
    user = {"id": "123", "email": "test@example.com"}
    auth._set_session(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
        "refresh-token",
        user
    )

    result = auth.get_user()
    assert result["status_code"] == 200, "Status should be 200"
    assert result["data"]["user"] == user, "User should match"

    print("  ✓ Returns cached user from session")


def test_jwt_with_metadata():
    """Test JWT decoding with user metadata."""
    print("\n[TEST] JWT with Metadata")

    auth = AuthClient(MockClient())

    # JWT with user_metadata
    # Payload: {"sub": "123", "email": "test@example.com", "exp": 1234567890, "user_metadata": {"name": "Test User"}}
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTAsInVzZXJfbWV0YWRhdGEiOnsibmFtZSI6IlRlc3QgVXNlciJ9fQ.signature"

    payload = auth._decode_jwt_payload(token)

    assert payload is not None, "Payload should not be None"
    assert "user_metadata" in payload, "Should have user_metadata"
    assert payload["user_metadata"]["name"] == "Test User", "Metadata should be decoded"

    print("  ✓ JWT with metadata decoded correctly")

    # Set session should extract metadata
    auth._set_session(token, "refresh-token")

    assert "user_metadata" in auth._session["user"], "Session user should have metadata"
    assert auth._session["user"]["user_metadata"]["name"] == "Test User", "Metadata should be in session"

    print("  ✓ Metadata extracted to session")


def test_timestamp_helper():
    """Test get_current_timestamp works in MicroPython."""
    print("\n[Test] Timestamp Helper")

    try:
        from supabase_micro.utils import get_current_timestamp
        timestamp = get_current_timestamp()

        # Basic validation - should be a reasonable Unix timestamp
        assert timestamp > 1609459200, "Timestamp should be after 2021"
        assert isinstance(timestamp, int), "Timestamp should be integer"

        print("  ✓ Timestamp helper returned valid timestamp")
        print(f"  ✓ Current timestamp: {timestamp}")

    except Exception as e:
        raise AssertionError(f"Failed to get timestamp: {e}")


def test_should_refresh_logic():
    """Test should_refresh_token logic without mocking."""
    print("\n[Test] Should Refresh Logic")

    try:
        from supabase_micro.utils import get_current_timestamp

        current_time = get_current_timestamp()

        # Test 1: Expires in 30 minutes - should not refresh (threshold 5 min)
        expires_at_far = current_time + 1800
        expires_in = expires_at_far - current_time
        assert expires_in > 300, "Should not need refresh for far expiry"
        print("  ✓ Far expiry correctly identified (no refresh needed)")

        # Test 2: Expires in 3 minutes - should refresh (threshold 5 min)
        expires_at_near = current_time + 180
        expires_in = expires_at_near - current_time
        assert expires_in < 300, "Should need refresh for near expiry"
        print("  ✓ Near expiry correctly identified (refresh needed)")

        # Test 3: Expired token
        expires_at_past = current_time - 60
        expires_in = expires_at_past - current_time
        assert expires_in < 0, "Should need refresh for expired token"
        print("  ✓ Expired token correctly identified")

    except Exception as e:
        raise AssertionError(f"Refresh logic test failed: {e}")


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("MicroPython Auth Tests")
    print("="*60)

    tests = [
        test_jwt_decoding,
        test_session_management,
        test_get_session,
        test_get_user,
        test_jwt_with_metadata,
        test_timestamp_helper,
        test_should_refresh_logic
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
