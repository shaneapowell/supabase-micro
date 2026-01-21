# API Reference

## Client Initialization

```python
from supabase_micro import create_client

client = create_client(url, key)
```

**Parameters:**
- `url` (str): Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
- `key` (str): Your Supabase API key (see below)

### Which API key to use?

For IoT devices and client applications, use the **publishable key** (`sb_publishable_...`) or the legacy **anon key**. Both provide the same low-privilege access and are safe to embed in device firmware.

| Key type | Format | Safe for IoT? |
|----------|--------|---------------|
| Publishable | `sb_publishable_...` | Yes (recommended) |
| anon (legacy) | JWT starting with `eyJ...` | Yes |
| Secret / service_role | `sb_secret_...` or JWT | **No** - server-side only |

**Important:** Never use secret or service_role keys on IoT devices. These bypass Row Level Security and provide full database access.

When users authenticate via `client.auth.sign_in_with_password()`, the library automatically uses their JWT for subsequent requests, and RLS policies apply with the `authenticated` role.

See the official [Supabase API Keys documentation](https://supabase.com/docs/guides/api/api-keys) for full details on key types and security considerations.

---

## PostgREST (Database Operations)

### SELECT

```python
# Select all columns
result = client.table("countries").select("*").execute()

# Select specific columns
result = client.table("countries").select("name,code").execute()

# With filters
result = (
    client.table("countries")
    .select("*")
    .eq("continent", "Asia")
    .limit(10)
    .execute()
)
```

### INSERT

```python
# Insert single row
result = client.table("countries").insert({
    "name": "Test Country",
    "code": "TC",
    "continent": "Test"
}).execute()

# Insert multiple rows
result = client.table("countries").insert([
    {"name": "Country 1", "code": "C1"},
    {"name": "Country 2", "code": "C2"}
]).execute()
```

### UPDATE

```python
result = (
    client.table("countries")
    .update({"name": "Updated Name"})
    .eq("id", 1)
    .execute()
)
```

### DELETE

```python
result = (
    client.table("countries")
    .delete()
    .eq("id", 1)
    .execute()
)
```

### Filters

```python
# Equal
.eq("column", value)

# Not equal
.neq("column", value)

# Greater than
.gt("column", value)

# Greater than or equal
.gte("column", value)

# Less than
.lt("column", value)

# Less than or equal
.lte("column", value)

# Limit results
.limit(count)

# Order by
.order("column")              # Ascending
.order("column", desc=True)   # Descending
```

### Response Format

**Success:**
```python
{
    "data": [...] or {...},
    "status_code": 200
}
```

**Error:**
```python
{
    "error": "Error message" or {...},
    "status_code": 400
}
```

---

## Authentication

### Sign Up

```python
# Sign up with email and password
result = client.auth.sign_up(
    email="user@example.com",
    password="password123"
)

# Sign up with user metadata
result = client.auth.sign_up(
    email="user@example.com",
    password="password123",
    options={
        "data": {
            "username": "john_doe",
            "age": 25
        }
    }
)

if result["status_code"] == 200:
    user = result["data"]["user"]
    print(f"User created: {user['email']}")
```

### Sign In

```python
# Sign in with email and password
result = client.auth.sign_in_with_password(
    email="user@example.com",
    password="password123"
)

if result["status_code"] == 200:
    print("Signed in successfully!")
    access_token = result["data"]["access_token"]
```

### Get User

```python
# Get current user
result = client.auth.get_user()

if result["status_code"] == 200:
    user = result["data"]["user"]
    print(f"User: {user['email']}")
    print(f"Metadata: {user.get('user_metadata', {})}")
```

### Update User

```python
# Update user metadata
result = client.auth.update_user({
    "data": {
        "theme": "dark",
        "notifications": True
    }
})

# Update email or password
result = client.auth.update_user({
    "email": "newemail@example.com",
    "password": "newpassword123"
})
```

### Session Management

```python
# Get current session
result = client.auth.get_session()
session = result["data"]["session"]

if session:
    print(f"Token expires at: {session['expires_at']}")

# Refresh session before token expires
result = client.auth.refresh_session()

if result["status_code"] == 200:
    print("Session refreshed!")
```

### Authenticated Queries (RLS)

Once signed in, all database queries automatically use the user's JWT token, enabling Row Level Security (RLS) policies:

```python
# Sign in first
client.auth.sign_in_with_password("user@example.com", "password123")

# Now queries use user context - RLS policies apply
result = client.table("todos").select("*").execute()

# Insert with automatic user_id from RLS
result = client.table("todos").insert({
    "task": "Buy groceries",
    "is_complete": False
}).execute()
```

### Password Reset

```python
# Send password reset email
result = client.auth.reset_password_for_email(
    email="user@example.com",
    options={
        "redirect_to": "https://yourapp.com/reset-password"
    }
)

if result["status_code"] == 200:
    print("Password reset email sent!")
```

### Sign Out

```python
# Sign out current user
result = client.auth.sign_out()

if result["status_code"] == 204:
    print("Signed out successfully!")
```

---

## Storage (File Operations)

### Upload

```python
# Upload file
with open("image.jpg", "rb") as f:
    file_data = f.read()

result = client.storage.from_("avatars").upload(
    "user1.jpg",
    file_data,
    "image/jpeg"  # Optional, auto-detected if not provided
)
```

### Download

```python
result = client.storage.from_("avatars").download("user1.jpg")

if result["status_code"] == 200:
    with open("downloaded.jpg", "wb") as f:
        f.write(result["data"])
```

### List Files

```python
# List all files in bucket
result = client.storage.from_("avatars").list()

# List files in folder
result = client.storage.from_("avatars").list("folder/", limit=50)

# Access file info
for file in result["data"]:
    print(file["name"], file["id"])
```

### Delete Files

```python
# Delete single file
result = client.storage.from_("avatars").delete("user1.jpg")

# Delete multiple files
result = client.storage.from_("avatars").delete([
    "user1.jpg",
    "user2.jpg"
])
```

---

## Error Handling

The library returns status codes instead of raising exceptions for API errors:

```python
result = client.table("users").select("*").execute()

if 200 <= result["status_code"] < 300:
    # Success
    data = result["data"]
    print(f"Got {len(data)} rows")
else:
    # Error
    print(f"Error {result['status_code']}: {result['error']}")
```

Network errors (connection failures, timeouts) will raise Python exceptions:

```python
try:
    result = client.table("users").select("*").execute()
except OSError as e:
    print("Network error:", e)
```

---

## Memory Considerations

The library is designed for memory-constrained devices:

- **No connection pooling**: Sockets are opened/closed per request
- **Streaming parsing**: HTTP responses parsed line-by-line
- **Minimal buffering**: Only necessary data kept in memory
- **No external dependencies**: Reduces overall memory footprint

**Typical memory usage:**
- Base library: ~20-25KB (including auth)
- Per request overhead: ~2-5KB
- Active session: ~1-2KB
- Response data: Depends on data size

**Tips for low-memory devices (ESP8266):**
- Query smaller datasets with `.limit()`
- Process results immediately, don't store large lists
- Use `gc.collect()` between operations
- Consider chunking large file uploads/downloads
