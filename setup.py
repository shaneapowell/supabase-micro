"""Setup script for supabase-micro testing.

This script creates the necessary storage bucket for testing.
Run this after executing setup.sql in your Supabase dashboard.
"""

def load_env(filename=".env"):
    """Load environment variables from .env file."""
    env_vars = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    except:
        pass
    return env_vars

# Load credentials
env = load_env()
SUPABASE_URL = env.get("SUPABASE_URL")
SUPABASE_KEY = env.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        import os
        SUPABASE_URL = SUPABASE_URL or os.getenv("SUPABASE_URL")
        SUPABASE_KEY = SUPABASE_KEY or os.getenv("SUPABASE_KEY")
    except:
        pass

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Please set SUPABASE_URL and SUPABASE_KEY in .env file")
    import sys
    sys.exit(1)

from client import SupabaseClient

def create_client(url, key):
    return SupabaseClient(url, key)

print("=" * 60)
print("Supabase MicroPython - Setup Script")
print("=" * 60)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Step 1: Create storage bucket
print("\n1. Creating 'test-bucket' storage bucket...")
try:
    # Note: MicroPython Supabase client doesn't have bucket creation yet
    # You need to create it manually in Supabase Dashboard:
    # Storage > Create a new bucket > Name: "test-bucket" > Public: Yes
    print("   ⚠ Storage bucket creation not yet supported in library")
    print("   Please create 'test-bucket' manually in Supabase Dashboard:")
    print("   1. Go to Storage in your Supabase Dashboard")
    print("   2. Click 'New bucket'")
    print("   3. Name: 'test-bucket'")
    print("   4. Public bucket: Yes")
    print("   5. Click 'Create bucket'")
except Exception as e:
    print(f"   Error: {e}")

# Step 2: Verify countries table
print("\n2. Verifying 'countries' table...")
result = client.table("countries").select("*").limit(1).execute()

if result["status_code"] == 200:
    print("   ✓ Table exists and is accessible")

    # Check row count
    count_result = client.table("countries").select("*").execute()
    if count_result["status_code"] == 200:
        row_count = len(count_result["data"])
        print(f"   ✓ Found {row_count} countries in table")
        if row_count == 0:
            print("   ⚠ Table is empty - did you run setup.sql?")
    else:
        print(f"   ✗ Could not count rows: {count_result['error']}")
else:
    print(f"   ✗ Table not found: {result['error']}")
    print("   Please run setup.sql in your Supabase SQL Editor first")

# Step 3: Test insert permission
print("\n3. Testing insert permission...")
result = client.table("countries").insert({
    "name": "Test Country Setup",
    "code": "TS",
    "continent": "Test"
}).execute()

if result["status_code"] == 201:
    print("   ✓ Insert permission works")
    test_id = result["data"][0]["id"] if isinstance(result["data"], list) else result["data"]["id"]

    # Clean up test record
    delete_result = client.table("countries").delete().eq("id", test_id).execute()
    if delete_result["status_code"] == 200:
        print("   ✓ Delete permission works")
    else:
        print(f"   ⚠ Could not delete test record: {delete_result['error']}")
else:
    print(f"   ✗ Insert failed: {result['error']}")
    print("   Check RLS policies in your Supabase Dashboard")

print("\n" + "=" * 60)
print("Setup check completed!")
print("\nNext steps:")
print("1. If you haven't already, run setup.sql in Supabase SQL Editor")
print("2. Create 'test-bucket' storage bucket manually (see above)")
print("3. Run: micropython example.py")
print("=" * 60)
