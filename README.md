# supabase-micro

A minimal, dependency-free Supabase client library for MicroPython.

## Features

- **Zero dependencies**: Uses only MicroPython built-ins (`socket`, `ssl`, `json`)
- **PostgREST support**: Full database CRUD operations with query builder
- **Storage support**: Upload, download, list, and delete files
- **Authentication**: Email/password auth, session management, user operations
- **Memory efficient**: Designed for constrained devices (ESP32, ESP8266, RP2040)
- **Synchronous API**: Simple blocking operations, no async complexity
- **Method chaining**: Familiar query builder pattern like supabase-py

## Installation

### For MicroPython Devices (ESP32, ESP8266, RP2040)

Copy the library to your device:

```bash
# Using mpremote (recommended)
mpremote cp -r src/supabase_micro :/lib/supabase_micro
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions including Thonny, ampy, and WebREPL methods.

### For Local Testing (Without Hardware)

```bash
# Install MicroPython
brew install micropython  # macOS

# Clone and test
git clone https://github.com/supabase/supabase-micro.git
cd supabase-micro
micropython tests/test_basic.py
```

See [TESTING.md](TESTING.md) for complete testing guide including Supabase setup and integration tests.

## Quick Start

```python
from supabase_micro import create_client

# Initialize client
client = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# Query data
result = client.table("countries").select("*").limit(5).execute()
print(result["data"])
```

## API Reference

### Client Initialization

```python
from supabase_micro import create_client

client = create_client(url, key)
```

**Parameters:**
- `url` (str): Your Supabase project URL
- `key` (str): Your Supabase anon or service role key

### PostgREST (Database Operations)

#### SELECT

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

#### INSERT

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

#### UPDATE

```python
result = (
    client.table("countries")
    .update({"name": "Updated Name"})
    .eq("id", 1)
    .execute()
)
```

#### DELETE

```python
result = (
    client.table("countries")
    .delete()
    .eq("id", 1)
    .execute()
)
```

#### Filters

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
.order("column")          # Ascending
.order("column", desc=True)  # Descending
```

#### Response Format

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

### Authentication

#### Sign Up

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

#### Sign In

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

#### Get User

```python
# Get current user
result = client.auth.get_user()

if result["status_code"] == 200:
    user = result["data"]["user"]
    print(f"User: {user['email']}")
    print(f"Metadata: {user.get('user_metadata', {})}")
```

#### Update User

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

#### Session Management

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

#### Authenticated Queries (RLS)

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

#### Password Reset

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

#### Sign Out

```python
# Sign out current user
result = client.auth.sign_out()

if result["status_code"] == 204:
    print("Signed out successfully!")
```

### Storage (File Operations)

#### Upload

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

#### Download

```python
result = client.storage.from_("avatars").download("user1.jpg")

if result["status_code"] == 200:
    with open("downloaded.jpg", "wb") as f:
        f.write(result["data"])
```

#### List Files

```python
# List all files in bucket
result = client.storage.from_("avatars").list()

# List files in folder
result = client.storage.from_("avatars").list("folder/", limit=50)

# Access file info
for file in result["data"]:
    print(file["name"], file["id"])
```

#### Delete Files

```python
# Delete single file
result = client.storage.from_("avatars").delete("user1.jpg")

# Delete multiple files
result = client.storage.from_("avatars").delete([
    "user1.jpg",
    "user2.jpg"
])
```

## Complete Examples

### ESP32 WiFi Example

```python
import network
from supabase_micro import create_client

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("your-ssid", "your-password")

while not wlan.isconnected():
    pass

print("Connected:", wlan.ifconfig())

# Initialize Supabase client
client = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# Query data
result = client.table("sensors").select("*").limit(10).execute()

if result["status_code"] == 200:
    for row in result["data"]:
        print(f"Sensor {row['id']}: {row['value']}")
else:
    print("Error:", result["error"])

# Insert sensor reading
result = client.table("sensors").insert({
    "device_id": "esp32-001",
    "temperature": 23.5,
    "humidity": 65.2
}).execute()

print("Insert status:", result["status_code"])
```

### Temperature Logger

```python
import machine
import time
from supabase_micro import create_client

# Setup
client = create_client("https://your-project.supabase.co", "your-key")
sensor = machine.ADC(0)

# Log temperature every minute
while True:
    temp = sensor.read() * 0.1  # Convert to celsius

    result = client.table("readings").insert({
        "device": "living-room",
        "temperature": temp,
        "timestamp": time.time()
    }).execute()

    if result["status_code"] == 201:
        print(f"Logged: {temp}°C")
    else:
        print("Error:", result["error"])

    time.sleep(60)
```

### Image Upload from Camera

```python
import camera
from supabase_micro import create_client

# Initialize
cam = camera.init()
client = create_client("https://your-project.supabase.co", "your-key")

# Capture and upload
img = cam.capture()

result = client.storage.from_("camera-images").upload(
    f"snapshot-{time.time()}.jpg",
    img,
    "image/jpeg"
)

if result["status_code"] == 200:
    print("Uploaded successfully!")
```

### ESP32 with Authentication and RLS

```python
import network
from supabase_micro import create_client

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("your-ssid", "your-password")

while not wlan.isconnected():
    pass

print("Connected:", wlan.ifconfig())

# Initialize client
client = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# Sign in user
result = client.auth.sign_in_with_password(
    "user@example.com",
    "password123"
)

if result["status_code"] == 200:
    print("Signed in as:", result["data"]["user"]["email"])

    # Now all queries use user's JWT - RLS policies apply
    # Insert data (user_id automatically set by RLS)
    result = client.table("sensor_data").insert({
        "temperature": 23.5,
        "humidity": 65.0,
        "device": "esp32-living-room"
    }).execute()

    if result["status_code"] == 201:
        print("Data logged successfully!")

    # Query only this user's data (RLS filters automatically)
    result = client.table("sensor_data").select("*").limit(10).execute()
    print(f"Retrieved {len(result['data'])} readings")
else:
    print("Login failed:", result["error"])
```

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

## Compatibility

**Tested on:**
- MicroPython 1.19+ (ESP32, ESP8266, RP2040)
- CPython 3.x (for development/testing)

**Required modules:**
- `socket` - Network communication
- `ssl` - HTTPS support
- `json` / `ujson` - JSON parsing

## Limitations

- **Synchronous only**: No async/await support
- **No connection pooling**: New connection per request
- **Basic filtering**: Supports eq, neq, gt, gte, lt, lte, limit, order
- **No RPC**: Function calls not supported
- **Basic Auth**: Email/password only (no OAuth, MFA, or magic links)
- **No auto-refresh**: Token refresh must be called manually
- **No session persistence**: Sessions stored in memory only (cleared on reboot)
- **No Realtime**: WebSocket subscriptions not supported

## License

MIT License

## Contributing

Contributions welcome! Please test on actual MicroPython hardware before submitting PRs.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/supabase/supabase-micro/issues)
- Supabase Discord: [Join here](https://discord.supabase.com)

## Credits

Based on [supabase-py](https://github.com/supabase/supabase-py) and designed for MicroPython environments.
