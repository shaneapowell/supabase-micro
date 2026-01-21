"""Migration script to set up Supabase database for testing.

This script creates sample data using the Supabase REST API.
Run with: micropython migrate.py

Note: You must first create the 'countries' table manually in Supabase SQL Editor.
See setup.sql for the table schema.
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

print("=" * 70)
print("Supabase MicroPython - Database Migration")
print("=" * 70)
print(f"\nProject: {SUPABASE_URL}")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Step 1: Check if table exists
print("\n1. Checking if 'countries' table exists...")
result = client.table("countries").select("*").limit(1).execute()

if result["status_code"] == 200:
    print("   ✓ Table exists!")
elif result["status_code"] == 404:
    print("   ✗ Table doesn't exist yet")
    print("\n   Please create it first by running this SQL in Supabase Dashboard:")
    print("   (Go to SQL Editor and paste the following)\n")
    print("-" * 70)
    print("""
CREATE TABLE IF NOT EXISTS countries (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    continent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE countries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Enable all access for testing" ON countries;

CREATE POLICY "Enable all access for testing" ON countries
    FOR ALL
    USING (true)
    WITH CHECK (true);
""")
    print("-" * 70)
    print("\nAfter creating the table, run this script again.")
    import sys
    sys.exit(1)
else:
    print(f"   ✗ Error checking table: {result['error']}")
    import sys
    sys.exit(1)

# Step 2: Insert sample data
print("\n2. Inserting sample data...")

sample_countries = [
    {"name": "United States", "code": "US", "continent": "North America"},
    {"name": "Canada", "code": "CA", "continent": "North America"},
    {"name": "Mexico", "code": "MX", "continent": "North America"},
    {"name": "Brazil", "code": "BR", "continent": "South America"},
    {"name": "Argentina", "code": "AR", "continent": "South America"},
    {"name": "United Kingdom", "code": "GB", "continent": "Europe"},
    {"name": "France", "code": "FR", "continent": "Europe"},
    {"name": "Germany", "code": "DE", "continent": "Europe"},
    {"name": "Japan", "code": "JP", "continent": "Asia"},
    {"name": "China", "code": "CN", "continent": "Asia"},
    {"name": "India", "code": "IN", "continent": "Asia"},
    {"name": "Australia", "code": "AU", "continent": "Oceania"},
    {"name": "South Africa", "code": "ZA", "continent": "Africa"},
    {"name": "Egypt", "code": "EG", "continent": "Africa"}
]

result = client.table("countries").insert(sample_countries).execute()

if result["status_code"] in [200, 201]:
    print("   ✓ Sample data inserted successfully!")
    inserted = len(result["data"]) if isinstance(result["data"], list) else 1
    print(f"   Inserted {inserted} countries")
else:
    print(f"   ✗ Failed to insert data")
    print(f"   Error: {result['error']}")
    print("\n   This might mean:")
    print("   - Data already exists (that's OK!)")
    print("   - RLS policies are blocking inserts")
    print("   - Check your Supabase policies in Dashboard > Authentication > Policies")

# Step 3: Verify data
print("\n3. Verifying data...")
result = client.table("countries").select("*").execute()

if result["status_code"] == 200:
    count = len(result["data"])
    print(f"   ✓ Found {count} countries in database")

    if count > 0:
        print("\n   Sample records:")
        for country in result["data"][:3]:
            print(f"     - {country.get('name')} ({country.get('code')})")
        if count > 3:
            print(f"     ... and {count - 3} more")
else:
    print(f"   ✗ Could not verify: {result['error']}")

print("\n" + "=" * 70)
print("Migration completed!")
print("\nNext steps:")
print("  1. Create 'test-bucket' in Supabase Dashboard:")
print("     Storage > New bucket > Name: 'test-bucket' > Public: Yes")
print("  2. Run: micropython example.py")
print("=" * 70)
