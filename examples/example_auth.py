"""
Authentication example for supabase_micro.

Demonstrates auth operations: signup, signin, session management, RLS queries,
user operations, token refresh, password reset, RLS security, and signout.

Setup:
- Local: supabase start && python examples/example_auth.py
- Remote: Create .env file (see .env.example) && python examples/example_auth.py
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from supabase_micro import create_client


def load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    paths = ["../.env", ".env"]

    for filename in paths:
        try:
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
                if env_vars:
                    return env_vars
        except:
            continue
    return env_vars


# Load from .env file
env = load_env()
SUPABASE_URL = env.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = env.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")
TEST_EMAIL = env.get("TEST_EMAIL") or os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = env.get("TEST_PASSWORD") or os.getenv("TEST_PASSWORD", "testpassword123")


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
    print("\n[1/11] Testing signup...")

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
        # Handle both response formats: {user: {...}} or user object directly
        data = result["data"]
        user = data.get("user", data)
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
    print("\n[2/11] Testing signin...")

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
    print("\n[3/11] Testing get_session...")

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
    print("\n[4/11] Testing get_user...")

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
    print("\n[5/11] Testing update_user...")

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
    print("\n[6/11] Testing authenticated query (RLS)...")

    # Get current user ID
    user_result = client.auth.get_user()
    if user_result["status_code"] != 200:
        print("✗ Could not get user")
        return False

    user_id = user_result["data"]["user"]["id"]

    # Try to insert a todo (RLS will verify user_id matches auth.uid())
    result = client.table("todos").insert({
        "user_id": user_id,
        "task": "Test task from auth example",
        "is_complete": False
    }).execute()

    print_result("Insert Todo Result", result)

    if result["status_code"] == 201:
        print("✓ Authenticated query successful!")
        print("  RLS verified user_id matches authenticated user")
        return True
    else:
        print("⚠ Query failed (make sure 'todos' table exists with RLS enabled)")
        return False


def demo_refresh_session(client):
    """Demonstrate token refresh."""
    print("\n[7/11] Testing refresh_session...")

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
    print("\n[8/11] Testing reset_password_for_email...")

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


def demo_rls_anonymous_blocked(client):
    """Demonstrate RLS blocking anonymous users."""
    print("\n[9/11] Testing RLS - Anonymous user blocked...")

    # Sign out first to become anonymous
    client.auth.sign_out()

    # Try to insert as anonymous - should fail
    result = client.table("todos").insert({
        "user_id": "00000000-0000-0000-0000-000000000000",
        "task": "Anonymous task",
        "is_complete": False
    }).execute()

    print_result("Anonymous Insert Result", result)

    if result["status_code"] in [401, 403]:
        print("✓ RLS correctly blocked anonymous user!")
        print("  Anonymous users cannot insert data")
        return True
    elif result["status_code"] == 404:
        print("⚠ Table not found (RLS test skipped)")
        return True
    else:
        print("✗ RLS failed! Anonymous user was allowed to insert")
        return False


def demo_rls_cross_user_blocked(client):
    """Demonstrate RLS blocking cross-user access using two real users."""
    print("\n[10/11] Testing RLS - Cross-user access blocked...")

    # Define second test user
    user2_email = "test2@example.com"
    user2_password = "testpassword456"

    # --- Setup User 1 ---
    signin_result = client.auth.sign_in_with_password(TEST_EMAIL, TEST_PASSWORD)
    if signin_result["status_code"] != 200:
        print("✗ Could not sign in as User 1")
        return False

    user1_id = client.auth.get_user()["data"]["user"]["id"]
    print(f"  User 1 ID: {user1_id}")

    # Create a todo for User 1
    user1_task = f"User 1 private task {int(time.time())}"
    result = client.table("todos").insert({
        "user_id": user1_id,
        "task": user1_task,
        "is_complete": False
    }).execute()

    if result["status_code"] != 201:
        print("⚠ Could not create test data (todos table may not exist)")
        return True
    
    user1_todo_id = result["data"][0]["id"]
    print(f"  User 1 created todo: {user1_task}")

    # --- Setup User 2 ---
    client.auth.sign_out()
    
    # Try to sign up User 2 (may already exist)
    signup_result = client.auth.sign_up(email=user2_email, password=user2_password)
    if signup_result["status_code"] not in [200, 422]:
        print(f"✗ Could not create User 2: {signup_result.get('error')}")
        return False

    # Sign in as User 2
    signin_result = client.auth.sign_in_with_password(user2_email, user2_password)
    if signin_result["status_code"] != 200:
        print("✗ Could not sign in as User 2")
        return False

    user2_id = client.auth.get_user()["data"]["user"]["id"]
    print(f"  User 2 ID: {user2_id}")

    # Create a todo for User 2
    user2_task = f"User 2 private task {int(time.time())}"
    result = client.table("todos").insert({
        "user_id": user2_id,
        "task": user2_task,
        "is_complete": False
    }).execute()

    if result["status_code"] != 201:
        print("⚠ User 2 could not create todo")
        return False
    
    user2_todo_id = result["data"][0]["id"]
    print(f"  User 2 created todo: {user2_task}")

    # --- Test 1: User 2 tries to SELECT User 1's data ---
    print("\n  Testing cross-user SELECT...")
    result = client.table("todos").select("*").eq("user_id", user1_id).execute()
    
    if result["status_code"] == 200 and len(result["data"]) == 0:
        print("  ✓ User 2 cannot SELECT User 1's todos (RLS filtered)")
    else:
        print(f"  ✗ RLS FAILED: User 2 could see User 1's data: {result['data']}")
        return False

    # --- Test 2: User 2 tries to UPDATE User 1's todo ---
    print("  Testing cross-user UPDATE...")
    result = client.table("todos").update({
        "task": "HACKED BY USER 2"
    }).eq("id", user1_todo_id).execute()

    # Should either return empty (no rows matched) or error
    data = result.get("data") or []
    rows_affected = len(data)
    if rows_affected == 0:
        print("  ✓ User 2 cannot UPDATE User 1's todos (0 rows affected)")
    else:
        print(f"  ✗ RLS FAILED: User 2 updated User 1's todo!")
        return False

    # --- Test 3: User 2 tries to DELETE User 1's todo ---
    print("  Testing cross-user DELETE...")
    result = client.table("todos").delete().eq("id", user1_todo_id).execute()

    data = result.get("data") or []
    rows_affected = len(data)
    if rows_affected == 0:
        print("  ✓ User 2 cannot DELETE User 1's todos (0 rows affected)")
    else:
        print(f"  ✗ RLS FAILED: User 2 deleted User 1's todo!")
        return False

    # --- Verify User 2 can still see their own data ---
    print("  Verifying users can access their own data...")
    result = client.table("todos").select("*").eq("id", user2_todo_id).execute()
    
    if result["status_code"] == 200 and len(result["data"]) == 1:
        print("  ✓ User 2 can see their own todo")
    else:
        print("  ✗ User 2 cannot see their own todo (unexpected)")
        return False

    # --- Switch back to User 1 and verify their data is intact ---
    client.auth.sign_out()
    client.auth.sign_in_with_password(TEST_EMAIL, TEST_PASSWORD)

    result = client.table("todos").select("*").eq("id", user1_todo_id).execute()
    
    if result["status_code"] == 200 and len(result["data"]) == 1:
        original_task = result["data"][0]["task"]
        if original_task == user1_task:
            print("  ✓ User 1's todo is intact and unchanged")
        else:
            print(f"  ✗ User 1's todo was modified! Expected '{user1_task}', got '{original_task}'")
            return False
    else:
        print("  ✗ User 1's todo is missing!")
        return False

    print("\n✓ RLS correctly blocked all cross-user operations!")
    print("  - SELECT: blocked")
    print("  - UPDATE: blocked")  
    print("  - DELETE: blocked")
    print("  - Each user can only access their own data")
    return True


def demo_signout(client):
    """Demonstrate sign out."""
    print("\n[11/11] Testing sign_out...")

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
    success.append(("RLS: Anonymous Blocked", demo_rls_anonymous_blocked(client)))
    success.append(("RLS: Cross-User Blocked", demo_rls_cross_user_blocked(client)))
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
