"""Example usage of supabase-micro library.

This script demonstrates basic database and storage operations.
Replace the URL and KEY with your actual Supabase credentials.
"""

from supabase_micro import create_client

# Configuration - REPLACE THESE WITH YOUR CREDENTIALS
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"

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
    print(f"   Error {result['status_code']}: {result['error']}")

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
    print(f"   Error: {result['error']}")

# Example 3: INSERT
print("\n3. INSERT - Add a new country")
result = client.table("countries").insert({
    "name": "Test Country",
    "code": "TC",
    "continent": "Test"
}).execute()

if result["status_code"] == 201:
    print(f"   Success! Inserted: {result['data']}")
    test_id = result["data"][0]["id"] if isinstance(result["data"], list) else result["data"]["id"]
else:
    print(f"   Error: {result['error']}")
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

    if result["status_code"] == 200:
        print(f"   Success! Updated: {result['data']}")
    else:
        print(f"   Error: {result['error']}")

# Example 5: DELETE
if test_id:
    print("\n5. DELETE - Remove the test country")
    result = (
        client.table("countries")
        .delete()
        .eq("id", test_id)
        .execute()
    )

    if result["status_code"] == 200:
        print("   Success! Deleted the test record")
    else:
        print(f"   Error: {result['error']}")

# Example 6: Storage - List files
print("\n6. STORAGE - List files in bucket")
result = client.storage.from_("test-bucket").list(limit=5)

if result["status_code"] == 200:
    print(f"   Found {len(result['data'])} files:")
    for file in result["data"]:
        print(f"   - {file.get('name', 'unknown')}")
else:
    print(f"   Error: {result['error']}")

# Example 7: Storage - Upload
print("\n7. STORAGE - Upload a test file")
test_data = b"Hello from MicroPython! This is a test file."
result = client.storage.from_("test-bucket").upload(
    "test.txt",
    test_data,
    "text/plain"
)

if result["status_code"] == 200:
    print("   Success! File uploaded")
else:
    print(f"   Error: {result['error']}")

# Example 8: Storage - Download
print("\n8. STORAGE - Download the test file")
result = client.storage.from_("test-bucket").download("test.txt")

if result["status_code"] == 200:
    downloaded_data = result["data"]
    print(f"   Success! Downloaded {len(downloaded_data)} bytes")
    print(f"   Content: {downloaded_data.decode('utf-8')}")
else:
    print(f"   Error: {result['error']}")

# Example 9: Storage - Delete
print("\n9. STORAGE - Delete the test file")
result = client.storage.from_("test-bucket").delete("test.txt")

if result["status_code"] == 200:
    print("   Success! File deleted")
else:
    print(f"   Error: {result['error']}")

print("\n" + "=" * 50)
print("Example completed!")
print("=" * 50)
