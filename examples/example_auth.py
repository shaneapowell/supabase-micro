"""
Authentication example for supabase_micro.

Demonstrates:
- User signup and signin
- Session management
- Authenticated queries (RLS)
- User operations
- Token refresh
- Password reset
- Sign out

Setup:
1. Start local Supabase: cd supabase && supabase start
2. Create a 'todos' table with RLS enabled (see schema.sql)
3. Update SUPABASE_URL and SUPABASE_KEY below
4. Run: python examples/example_auth.py
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from supabase_micro import create_client

# Configuration (update with your local Supabase instance)
SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


def print_result(title, result):
    """Pretty print result."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {result['status_code']}")
    if 'data' in result:
        print(f"Data: {result['data']}")
    if 'error' in result:
        print(f"Error: {result['error']}")


def demo_signup(client):
    """Demonstrate user signup."""
    print("\n[1/9] Testing signup...")

    # Sign up new user
    result = client.auth.sign_up(
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        options={
            "data": {
                "username": "testuser",
                "age": 25
            }
        }
    )

    print_result("Sign Up Result", result)

    if result["status_code"] == 200:
        print("✓ User signed up successfully!")
        user = result["data"]["user"]
        print(f"  User ID: {user['id']}")
        print(f"  Email: {user['email']}")
        if "user_metadata" in user:
            print(f"  Metadata: {user['user_metadata']}")
        return True
    elif result["status_code"] == 422:
        # User already exists
        print("⚠ User already exists, will use for signin")
        return True
    else:
        print("✗ Signup failed!")
        return False


def demo_signin(client):
    """Demonstrate user signin."""
    print("\n[2/9] Testing signin...")

    result = client.auth.sign_in_with_password(
        email=TEST_EMAIL,
        password=TEST_PASSWORD
    )

    print_result("Sign In Result", result)

    if result["status_code"] == 200:
        print("✓ User signed in successfully!")
        session = result["data"]
        print(f"  Access token: {session['access_token'][:50]}...")
        print(f"  Refresh token: {session['refresh_token'][:50]}...")
        return True
    else:
        print("✗ Signin failed!")
        return False


def demo_get_session(client):
    """Demonstrate getting current session."""
    print("\n[3/9] Testing get_session...")

    result = client.auth.get_session()
    print_result("Get Session Result", result)

    if result["status_code"] == 200 and result["data"]["session"]:
        print("✓ Got session successfully!")
        session = result["data"]["session"]
        print(f"  User ID: {session['user']['id']}")
        print(f"  Email: {session['user']['email']}")
        print(f"  Expires at: {session['expires_at']}")
        return True
    else:
        print("✗ No active session!")
        return False


def demo_get_user(client):
    """Demonstrate getting current user."""
    print("\n[4/9] Testing get_user...")

    result = client.auth.get_user()
    print_result("Get User Result", result)

    if result["status_code"] == 200:
        print("✓ Got user successfully!")
        user = result["data"]["user"]
        print(f"  User ID: {user['id']}")
        print(f"  Email: {user['email']}")
        return True
    else:
        print("✗ Failed to get user!")
        return False


def demo_update_user(client):
    """Demonstrate updating user metadata."""
    print("\n[5/9] Testing update_user...")

    result = client.auth.update_user({
        "data": {
            "username": "testuser_updated",
            "age": 26,
            "theme": "dark"
        }
    })

    print_result("Update User Result", result)

    if result["status_code"] == 200:
        print("✓ User updated successfully!")
        user = result["data"]["user"]
        print(f"  Updated metadata: {user.get('user_metadata', {})}")
        return True
    else:
        print("✗ Failed to update user!")
        return False


def demo_authenticated_query(client):
    """Demonstrate authenticated query with RLS."""
    print("\n[6/9] Testing authenticated query (RLS)...")

    # Try to insert a todo (user context will be applied by RLS)
    result = client.table("todos").insert({
        "task": "Test task from auth example",
        "is_complete": False
    }).execute()

    print_result("Insert Todo Result", result)

    if result["status_code"] == 201:
        print("✓ Authenticated query successful!")
        print("  Note: user_id will be automatically set by RLS")
        return True
    else:
        print("⚠ Query failed (make sure 'todos' table exists with RLS enabled)")
        return False


def demo_refresh_session(client):
    """Demonstrate token refresh."""
    print("\n[7/9] Testing refresh_session...")

    result = client.auth.refresh_session()
    print_result("Refresh Session Result", result)

    if result["status_code"] == 200:
        print("✓ Session refreshed successfully!")
        session = result["data"]["session"]
        print(f"  New access token: {session['access_token'][:50]}...")
        return True
    else:
        print("✗ Failed to refresh session!")
        return False


def demo_password_reset(client):
    """Demonstrate password reset email."""
    print("\n[8/9] Testing reset_password_for_email...")

    result = client.auth.reset_password_for_email(
        email=TEST_EMAIL,
        options={
            "redirect_to": "http://localhost:3000/reset-password"
        }
    )

    print_result("Password Reset Result", result)

    if result["status_code"] == 200:
        print("✓ Password reset email sent!")
        print("  Check your email inbox (or local Supabase Inbucket)")
        return True
    else:
        print("✗ Failed to send password reset email!")
        return False


def demo_signout(client):
    """Demonstrate sign out."""
    print("\n[9/9] Testing sign_out...")

    result = client.auth.sign_out()
    print_result("Sign Out Result", result)

    # Verify session is cleared
    session_result = client.auth.get_session()
    has_session = session_result["data"]["session"] is not None

    if result["status_code"] == 204 and not has_session:
        print("✓ User signed out successfully!")
        print("  Session cleared from memory")
        return True
    else:
        print("✗ Failed to sign out properly!")
        return False


def main():
    """Run all auth examples."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Supabase MicroPython Auth Example                 ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Create client
    print(f"Connecting to: {SUPABASE_URL}")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Run demos in sequence
    success = []

    success.append(("Signup", demo_signup(client)))
    success.append(("Signin", demo_signin(client)))
    success.append(("Get Session", demo_get_session(client)))
    success.append(("Get User", demo_get_user(client)))
    success.append(("Update User", demo_update_user(client)))
    success.append(("Authenticated Query", demo_authenticated_query(client)))
    success.append(("Refresh Session", demo_refresh_session(client)))
    success.append(("Password Reset", demo_password_reset(client)))
    success.append(("Sign Out", demo_signout(client)))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, result in success:
        status = "✓" if result else "✗"
        print(f"{status} {name}")

    passed = sum(1 for _, r in success if r)
    total = len(success)
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
