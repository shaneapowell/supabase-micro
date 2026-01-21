"""Example usage of supabase-micro library.

This script demonstrates basic database and storage operations.
Create a .env file with SUPABASE_URL and SUPABASE_KEY or set environment variables.
"""

def load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    # Try multiple paths
    paths = ["../.env", ".env", "../.env"]

    for filename in paths:
        try:
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
                if env_vars:  # Found and loaded
                    break
        except:
            continue  # Try next path
    return env_vars

# Load from .env file
env = load_env()
SUPABASE_URL = env.get("SUPABASE_URL")
SUPABASE_KEY = env.get("SUPABASE_KEY")

# Fallback to environment variables if .env not found
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        import os
        SUPABASE_URL = SUPABASE_URL or os.getenv("SUPABASE_URL")
        SUPABASE_KEY = SUPABASE_KEY or os.getenv("SUPABASE_KEY")
    except:
        pass

# Validate credentials
if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Please provide Supabase credentials")
    print("\nOption 1 - Create a .env file:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-anon-key")
    print("\nOption 2 - Set environment variables:")
    print("  export SUPABASE_URL='https://your-project.supabase.co'")
    print("  export SUPABASE_KEY='your-anon-key'")
    import sys
    sys.exit(1)

import sys

# Add src to path for MicroPython
# Works when run from root: micropython examples/example.py
sys.path.insert(0, 'src')

from supabase_micro.client import SupabaseClient

def create_client(url, key):
    return SupabaseClient(url, key)

# Initialize client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 50)
print("Supabase MicroPython Client - Example")
print("=" * 50)

# Example 1: SELECT query
print("\n1. SELECT - Fetch all countries (limited to 5)")
result = client.table("countries").select("*").limit(5).execute()

if result["status_code"] == 200:
    print(f"   Success! Got {len(result['data'])} rows")
    for row in result["data"]:
        print(f"   - {row}")
else:
    print(f"   Error {result['status_code']}: {result.get('error', 'Unknown error')}")

# Example 2: SELECT with filters
print("\n2. SELECT with filters - Countries in Asia")
result = (
    client.table("countries")
    .select("name,code")
    .eq("continent", "Asia")
    .limit(3)
    .execute()
)

if result["status_code"] == 200:
    print(f"   Found {len(result['data'])} Asian countries:")
    for row in result["data"]:
        print(f"   - {row['name']} ({row['code']})")
else:
    print(f"   Error: {result.get('error', 'Unknown error')}")

# Example 3: INSERT
print("\n3. INSERT - Add a new country")
result = client.table("countries").insert({
    "name": "Test Country",
    "code": "TC",
    "continent": "Test"
}).execute()

if 200 <= result["status_code"] < 300:
    print(f"   Success! Inserted: {result['data']}")
    test_id = result["data"][0]["id"] if isinstance(result["data"], list) else result["data"]["id"]
else:
    print(f"   Error: {result.get('error', 'Unknown error')}")
    test_id = None

# Example 4: UPDATE
if test_id:
    print("\n4. UPDATE - Update the test country")
    result = (
        client.table("countries")
        .update({"name": "Updated Test Country"})
        .eq("id", test_id)
        .execute()
    )

    if 200 <= result["status_code"] < 300:
        print(f"   Success! Updated: {result['data']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

# Example 5: Verify INSERT
if test_id:
    print("\n5. VERIFY - Check the inserted country in your dashboard")
    print(f"   Visit your Supabase Dashboard > Table Editor > countries")
    print(f"   Look for country with ID: {test_id} named 'Updated Test Country'")

# Example 6: Storage - List files
print("\n6. STORAGE - List files in bucket")
result = client.storage.from_("test-bucket").list(limit=5)

if result["status_code"] == 200:
    print(f"   Found {len(result['data'])} files:")
    for file in result["data"]:
        print(f"   - {file.get('name', 'unknown')}")
else:
    print(f"   Error: {result.get('error', 'Unknown error')}")

# Example 7: Storage - Upload
print("\n7. STORAGE - Upload a test file")
test_data = b"Hello from MicroPython! This is a test file."
result = client.storage.from_("test-bucket").upload(
    "test.txt",
    test_data,
    "text/plain"
)

if 200 <= result["status_code"] < 300:
    print("   Success! File uploaded")
else:
    print(f"   Error: {result.get('error', 'Unknown error')}")

# Example 8: Storage - Download
print("\n8. STORAGE - Download the test file")
result = client.storage.from_("test-bucket").download("test.txt")

if result["status_code"] == 200:
    downloaded_data = result["data"]
    print(f"   Success! Downloaded {len(downloaded_data)} bytes")
    print(f"   Content: {downloaded_data.decode('utf-8')}")
else:
    print(f"   Error: {result.get('error', 'Unknown error')}")

# Example 9: Verify Upload
print("\n9. VERIFY - Check uploaded file in your dashboard")
print("   Visit your Supabase Dashboard > Storage > test-bucket")
print("   You should see 'test.txt' file")

print("\n" + "=" * 50)
print("Example completed!")
print("\nVerify in your Supabase Dashboard:")
print("  • Table Editor > countries - Should have 'Updated Test Country'")
print("  • Storage > test-bucket - Should have 'test.txt' file")
print("=" * 50)
