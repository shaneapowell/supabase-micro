# Examples

Ready-to-use examples for supabase-micro on MicroPython devices.

## Prerequisites

1. **MicroPython device** (ESP32, ESP8266, RP2040, etc.)
2. **WiFi credentials**
3. **Supabase project** ([create one free](https://supabase.com))
4. **supabase-micro library** installed on your device (see [installation.md](installation.md))

## Getting Your Supabase Credentials

1. Go to [supabase.com](https://supabase.com)
2. Create a new project (or use existing)
3. Go to **Settings → API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Publishable key** (`sb_publishable_...`) or legacy **anon key** (`eyJ...`)

---

## WiFi Connection Template

All examples use this pattern:

```python
import network
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("SSID", "PASSWORD")

while not wlan.isconnected():
    time.sleep(0.5)

print("Connected! IP:", wlan.ifconfig()[0])
```

---

## Example 1: Basic Usage (quickstart.py)

The simplest example showing all basic operations.

**Setup:**
1. Create a table in your Supabase project
2. Create a storage bucket
3. Update credentials in the file

**Run:**
```bash
mpremote run examples/quickstart.py
```

---

## Example 2: Temperature Logger (temperature_logger.py)

Logs temperature readings to Supabase every 60 seconds. Perfect for IoT sensor projects.

**Setup:**

1. Create a table in Supabase:
```sql
CREATE TABLE temperature_readings (
  id SERIAL PRIMARY KEY,
  device_name TEXT NOT NULL,
  temperature FLOAT NOT NULL,
  timestamp BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

2. Enable Row Level Security and add a policy:
```sql
-- Enable RLS
ALTER TABLE temperature_readings ENABLE ROW LEVEL SECURITY;

-- Allow inserts from anyone (adjust for production!)
CREATE POLICY "Allow public inserts" ON temperature_readings
  FOR INSERT
  WITH CHECK (true);
```

3. Update WiFi credentials and Supabase URL/key in the file

4. Connect your temperature sensor to your ESP32/ESP8266

**Run:**
```bash
# Upload to device and run
mpremote cp examples/temperature_logger.py :main.py
mpremote reset
```

---

## Example 3: Authentication with RLS (example_auth.py)

Tests all authentication features: signup, signin, sessions, RLS, user operations, token refresh, password reset, signout.

**Quick Start (Local Supabase):**
```bash
supabase start
python examples/example_auth.py
```

**Quick Start (Remote Supabase):**
```bash
# 1. Copy and update credentials
cp .env.example .env
nano .env  # Add your URL and API key

# 2. Run
python examples/example_auth.py
```

On first run, signup creates the test user automatically.

---

## Complete Example: ESP32 WiFi + Database

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
    "your-api-key"  # publishable or anon key
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

---

## Complete Example: Temperature Logger Loop

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

---

## Complete Example: Image Upload from Camera

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

---

## Complete Example: ESP32 with Authentication and RLS

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
    "your-api-key"  # publishable or anon key
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

---

## Tips for Production

### 1. Store credentials separately

```python
# config.py
WIFI_SSID = "your-ssid"
WIFI_PASSWORD = "your-password"
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "your-key"

# main.py
from config import WIFI_SSID, WIFI_PASSWORD, SUPABASE_URL, SUPABASE_KEY
```

### 2. Add retry logic

```python
def insert_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        result = client.table("data").insert(data).execute()
        if result["status_code"] in [200, 201]:
            return result
        time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

### 3. Buffer data offline

```python
# Store readings locally if network fails
buffer = []

def log_reading(data):
    result = client.table("data").insert(data).execute()
    if result["status_code"] not in [200, 201]:
        buffer.append(data)  # Save for later
    else:
        # Try to send buffered data
        send_buffer()
```

### 4. Other recommendations

- **Use Row Level Security (RLS)** in production
- **Monitor device status** with periodic heartbeat inserts
- **Handle deep sleep** for battery-powered devices
- **Use `.limit()`** on queries to reduce memory usage
- **Call `gc.collect()`** between operations on ESP8266
