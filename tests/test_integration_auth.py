"""
Quick integration test to verify auth works with the main client.
"""

import sys
sys.path.insert(0, './src')

from supabase_micro import create_client


def test_client_has_auth():
    """Test that client has auth attribute."""
    print("\n[TEST] Client Integration")

    client = create_client("https://test.supabase.co", "test-key")

    # Check auth exists
    assert hasattr(client, 'auth'), "Client should have auth attribute"
    print("  ✓ Client has auth attribute")

    # Check auth methods exist
    assert hasattr(client.auth, 'sign_up'), "Auth should have sign_up"
    assert hasattr(client.auth, 'sign_in_with_password'), "Auth should have sign_in_with_password"
    assert hasattr(client.auth, 'sign_out'), "Auth should have sign_out"
    assert hasattr(client.auth, 'get_user'), "Auth should have get_user"
    assert hasattr(client.auth, 'get_session'), "Auth should have get_session"
    assert hasattr(client.auth, 'refresh_session'), "Auth should have refresh_session"
    assert hasattr(client.auth, 'update_user'), "Auth should have update_user"
    assert hasattr(client.auth, 'reset_password_for_email'), "Auth should have reset_password_for_email"

    print("  ✓ All auth methods available")


def test_auth_headers_without_session():
    """Test that auth headers use anon key when no session."""
    print("\n[TEST] Auth Headers (No Session)")

    client = create_client("https://test.supabase.co", "test-anon-key")

    headers = client._get_auth_headers()

    assert headers["apiKey"] == "test-anon-key", "Should have apiKey"
    assert headers["Authorization"] == "Bearer test-anon-key", "Should use anon key"

    print("  ✓ Uses anon key when no session")


def test_auth_headers_with_session():
    """Test that auth headers use access token when session exists."""
    print("\n[TEST] Auth Headers (With Session)")

    client = create_client("https://test.supabase.co", "test-anon-key")

    # Set a session
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig"
    client.auth._set_session(access_token, "refresh-token", {"id": "123"})

    headers = client._get_auth_headers()

    assert headers["apiKey"] == "test-anon-key", "Should still have apiKey"
    assert headers["Authorization"] == f"Bearer {access_token}", "Should use access token"

    print("  ✓ Uses access token when session exists")


def run_all_tests():
    """Run all integration tests."""
    print("="*60)
    print("Auth Integration Tests")
    print("="*60)

    tests = [
        test_client_has_auth,
        test_auth_headers_without_session,
        test_auth_headers_with_session
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
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
