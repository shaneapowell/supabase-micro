# supabase-micro

A minimal Supabase client for MicroPython and IoT devices.

## Why supabase-micro?

The official [supabase-py](https://github.com/supabase/supabase-py) library is designed for standard Python environments and pulls in many dependencies that won't run on microcontrollers. **supabase-micro** fills this gap:

- **Built for constrained devices** — ESP32, ESP8266, RP2040, and similar microcontrollers
- **Zero dependencies** — Uses only MicroPython built-ins (`socket`, `ssl`, `json`)
- **Tiny footprint** — ~46KB total, runs on devices with 40KB+ free RAM
- **Core features only** — Implements what IoT devices actually need: **PostgREST**, **Auth**, **Storage**

If you're building sensor loggers, smart home devices, or any IoT project that needs to talk to Supabase, this library is for you.

## Installation

```bash
# Using mpremote (recommended)
mpremote cp -r src/supabase_micro :/lib/supabase_micro
```

See [docs/installation.md](docs/installation.md) for alternative methods (Thonny, ampy, WebREPL) and troubleshooting.

## Quick Start

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
    "your-api-key"  # Use publishable key (sb_publishable_...) or anon key
)

# Query data
result = client.table("sensors").select("*").limit(10).execute()

if result["status_code"] == 200:
    for row in result["data"]:
        print(row)
else:
    print("Error:", result["error"])
```

## Basic Usage

### Database (PostgREST)

```python
# Select with filters
result = client.table("readings").select("*").eq("device", "esp32-01").limit(5).execute()

# Insert
result = client.table("readings").insert({
    "device": "esp32-01",
    "temperature": 23.5
}).execute()

# Update
result = client.table("readings").update({"temperature": 24.0}).eq("id", 1).execute()

# Delete
result = client.table("readings").delete().eq("id", 1).execute()
```

### Authentication

```python
# Sign up
result = client.auth.sign_up(email="user@example.com", password="password123")

# Sign in
result = client.auth.sign_in_with_password(email="user@example.com", password="password123")

# After sign-in, all queries automatically use the user's JWT for RLS
result = client.table("user_data").select("*").execute()  # RLS policies apply

# Sign out
client.auth.sign_out()
```

### Storage

```python
# Upload
with open("data.txt", "rb") as f:
    result = client.storage.from_("bucket").upload("data.txt", f.read())

# Download
result = client.storage.from_("bucket").download("data.txt")

# List files
result = client.storage.from_("bucket").list()

# Delete
result = client.storage.from_("bucket").delete("data.txt")
```

## Documentation

- **[Installation Guide](docs/installation.md)** — All installation methods, verification, troubleshooting
- **[API Reference](docs/api-reference.md)** — Complete PostgREST, Auth, and Storage API documentation
- **[Examples](docs/examples.md)** — Ready-to-use examples for common IoT scenarios
- **[Contributing](docs/contributing.md)** — Testing, local development, CI/CD

## Compatibility

**Tested on:**
- MicroPython 1.19+ (ESP32, ESP8266, RP2040)
- CPython 3.x (for development/testing)

**Memory requirements:**
- ESP32: Works well (~240KB+ RAM)
- ESP8266: Works with careful memory management (~40KB free)
- RP2040: Works excellently (264KB RAM)

## Limitations

- **Synchronous only** — No async/await support
- **No connection pooling** — New connection per request
- **Basic Auth** — Email/password only (no OAuth, MFA, magic links)
- **No auto-refresh** — Token refresh must be called manually
- **No Realtime** — WebSocket subscriptions not supported
- **No RPC** — Database function calls not supported

## License

MIT License — See [LICENSE](LICENSE) for details.

## Support

- [GitHub Issues](https://github.com/supabase/supabase-micro/issues)
- [Supabase Discord](https://discord.supabase.com)
