"""Basic tests for supabase-micro library.

This script tests the library components without requiring a real Supabase instance.
Run this to verify the library is working correctly.
"""

import sys

print("Testing supabase-micro library components...")
print("=" * 60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from client import SupabaseClient
    from utils import parse_url, url_encode, url_encode_value
    from utils import generate_boundary, build_multipart_body, guess_content_type

    def create_client(url, key):
        return SupabaseClient(url, key)

    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: URL parsing
print("\n2. Testing URL parsing...")
test_urls = [
    "https://example.supabase.co",
    "https://example.supabase.co/path",
    "http://localhost:3000",
    "https://example.com:8443/api"
]

for url in test_urls:
    parsed = parse_url(url)
    print(f"   {url}")
    print(f"     → host: {parsed['host']}, port: {parsed['port']}, scheme: {parsed['scheme']}")

# Test 3: URL encoding
print("\n3. Testing URL encoding...")
test_cases = [
    ({"name": "John Doe", "age": "30"}, "name=John+Doe&age=30"),
    ({"id": "eq.1", "status": "active"}, "id=eq.1&status=active"),
    ({"email": "test@example.com"}, "email=test%40example.com"),
]

for params, expected in test_cases:
    encoded = url_encode(params)
    status = "✓" if encoded == expected else "✗"
    print(f"   {status} {params} → {encoded}")

# Test 4: Content type guessing
print("\n4. Testing content type detection...")
test_files = [
    ("image.jpg", "image/jpeg"),
    ("document.pdf", "application/pdf"),
    ("data.json", "application/json"),
    ("style.css", "text/css"),
    ("unknown.xyz", "application/octet-stream"),
]

for filename, expected in test_files:
    detected = guess_content_type(filename)
    status = "✓" if detected == expected else "✗"
    print(f"   {status} {filename} → {detected}")

# Test 5: Multipart boundary generation
print("\n5. Testing multipart boundary generation...")
boundary1 = generate_boundary()
boundary2 = generate_boundary()
print(f"   Generated boundary 1: {boundary1}")
print(f"   Generated boundary 2: {boundary2}")
if boundary1 != boundary2:
    print("   ✓ Boundaries are unique")
else:
    print("   ✗ Boundaries should be unique")

# Test 6: Multipart body building
print("\n6. Testing multipart body building...")
test_data = b"Hello, World!"
boundary = "----TestBoundary123"
body = build_multipart_body(boundary, "test.txt", test_data, "text/plain")

if b"----TestBoundary123" in body and test_data in body:
    print("   ✓ Multipart body built correctly")
    print(f"   Body size: {len(body)} bytes")
else:
    print("   ✗ Multipart body is malformed")

# Test 7: Client initialization
print("\n7. Testing client initialization...")
try:
    client = create_client("https://example.supabase.co", "test-key-123")
    print("   ✓ Client created successfully")
    print(f"     URL: {client.url}")
    print(f"     Host: {client.host}")
    print(f"     Port: {client.port}")
    print(f"     SSL: {client.use_ssl}")
except Exception as e:
    print(f"   ✗ Client creation failed: {e}")

# Test 8: Client validation
print("\n8. Testing client validation...")
try:
    client = create_client("", "key")
    print("   ✗ Should have raised exception for empty URL")
except Exception as e:
    print(f"   ✓ Correctly rejected empty URL: {e}")

try:
    client = create_client("https://example.supabase.co", "")
    print("   ✗ Should have raised exception for empty key")
except Exception as e:
    print(f"   ✓ Correctly rejected empty key: {e}")

# Test 9: Query builder chaining
print("\n9. Testing query builder method chaining...")
try:
    client = create_client("https://example.supabase.co", "test-key")
    query = (
        client.table("users")
        .select("id,name,email")
        .eq("status", "active")
        .gt("age", 18)
        .limit(10)
        .order("name")
    )
    print("   ✓ Query builder chaining works")
    print(f"     Method: {query.method}")
    print(f"     Table: {query.table_name}")
    print(f"     Params: {query.params}")
except Exception as e:
    print(f"   ✗ Query builder error: {e}")

# Test 10: Storage client
print("\n10. Testing storage client...")
try:
    client = create_client("https://example.supabase.co", "test-key")
    bucket = client.storage.from_("test-bucket")
    print("   ✓ Storage client initialized")
    print(f"     Bucket name: {bucket.bucket_name}")
except Exception as e:
    print(f"   ✗ Storage client error: {e}")

# Test 11: Auth headers
print("\n11. Testing auth headers...")
try:
    client = create_client("https://example.supabase.co", "test-key-123")
    headers = client._get_auth_headers()

    has_apikey = "apiKey" in headers and headers["apiKey"] == "test-key-123"
    has_auth = "Authorization" in headers and headers["Authorization"] == "Bearer test-key-123"

    if has_apikey and has_auth:
        print("   ✓ Auth headers generated correctly")
        print(f"     Headers: {headers}")
    else:
        print("   ✗ Auth headers are incorrect")
        print(f"     Headers: {headers}")
except Exception as e:
    print(f"   ✗ Auth header error: {e}")

print("\n" + "=" * 60)
print("Basic tests completed!")
print("\nNote: These tests verify library components only.")
print("To test actual API calls, use example.py with real credentials.")
print("=" * 60)
