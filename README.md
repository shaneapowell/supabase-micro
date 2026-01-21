# supabase-micro

A minimal, dependency-free Supabase client library for MicroPython.

## Features

- **Zero dependencies**: Uses only MicroPython built-ins (`socket`, `ssl`, `json`)
- **PostgREST support**: Full database CRUD operations with query builder
- **Storage support**: Upload, download, list, and delete files
- **Memory efficient**: Designed for constrained devices (ESP32, ESP8266, RP2040)
- **Synchronous API**: Simple blocking operations, no async complexity
- **Method chaining**: Familiar query builder pattern like supabase-py

## Installation

### Option 1: Manual Installation

Copy the `supabase-micro` directory to your MicroPython device:

```bash
# Copy all files to your device
mpremote cp -r supabase-micro :/lib/supabase-micro
```

### Option 2: Direct Copy

Download and copy individual files to your device's `/lib` directory.

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
- Base library: ~10-15KB
- Per request overhead: ~2-5KB
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
- **No Auth**: Sign up/in methods not implemented
- **No Realtime**: WebSocket subscriptions not supported

## Future Enhancements

- Advanced filters (like, ilike, in, is)
- RPC support for PostgreSQL functions
- Auth methods (sign_up, sign_in, sign_out)
- Streaming uploads for large files
- Connection pooling option
- Async/await version

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
