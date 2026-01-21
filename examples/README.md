# Examples

Ready-to-use examples for supabase-micro on MicroPython devices.

## Prerequisites

1. **MicroPython device** (ESP32, ESP8266, RP2040, etc.)
2. **WiFi credentials**
3. **Supabase project** ([create one free](https://supabase.com))
4. **supabase-micro library** installed on your device

## Installation

Copy the library to your device:

```bash
# Using mpremote (recommended)
mpremote cp -r supabase_micro :/lib/supabase_micro

# Or using Thonny IDE - drag and drop the folder
```

## Examples

### 1. quickstart.py - Basic Usage

The simplest example showing all basic operations.

**Setup:**
1. Create a table in your Supabase project (e.g., "test_data")
2. Create a storage bucket (e.g., "test-bucket")
3. Edit the file and replace:
   - `your-wifi-ssid` with your WiFi name
   - `your-wifi-password` with your WiFi password
   - `your-project.supabase.co` with your Supabase project URL
   - `your-anon-key-here` with your anon key
   - `your_table` with your table name
   - `your-bucket` with your bucket name

**Run:**
```bash
mpremote run examples/quickstart.py
```

### 2. temperature_logger.py - IoT Sensor Logger

Logs temperature readings to Supabase every 60 seconds.

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

3. Edit the configuration in the file:
   - WiFi credentials
   - Supabase URL and key
   - Device name
   - Log interval

4. Connect your temperature sensor to your ESP32/ESP8266
   - Update the ADC pin in the code
   - Adjust the temperature conversion formula for your sensor

**Run:**
```bash
# Upload to device and run
mpremote cp examples/temperature_logger.py :main.py
mpremote reset
```

## Common Setup

### Get Your Supabase Credentials

1. Go to [supabase.com](https://supabase.com)
2. Create a new project (or use existing)
3. Go to **Settings → API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key**

### WiFi Connection Template

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

### Error Handling Pattern

```python
result = client.table("data").select("*").execute()

if result["status_code"] == 200:
    # Success
    data = result["data"]
    print(f"Got {len(data)} rows")
else:
    # Error
    print(f"Error: {result['error']}")
```

## Troubleshooting

### "No module named 'supabase_micro'"
- Library not installed on device
- Solution: Copy the library to `/lib/supabase_micro` on your device

### "WiFi connection failed"
- Wrong SSID/password
- Device out of range
- Solution: Check credentials and WiFi signal

### "OSError: -2" or connection errors
- Network issues
- Wrong Supabase URL
- Firewall blocking
- Solution: Test with `http://` first, then `https://`

### Memory errors on ESP8266
- Limited RAM (~40KB free)
- Solution:
  - Use `.limit()` on queries
  - Process data immediately
  - Call `gc.collect()` between operations
  - Use smaller data payloads

### "401 Unauthorized"
- Wrong API key
- Solution: Check your anon key in Supabase dashboard

### "404 Not Found"
- Table or bucket doesn't exist
- Wrong table/bucket name
- Solution: Check table/bucket exists in Supabase dashboard

## Tips for Production

1. **Store credentials separately:**
```python
# config.py
WIFI_SSID = "your-ssid"
WIFI_PASSWORD = "your-password"
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "your-key"

# main.py
from config import WIFI_SSID, WIFI_PASSWORD, SUPABASE_URL, SUPABASE_KEY
```

2. **Add retry logic:**
```python
def insert_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        result = client.table("data").insert(data).execute()
        if result["status_code"] in [200, 201]:
            return result
        time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

3. **Buffer data offline:**
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

4. **Use Row Level Security (RLS)** in production
5. **Monitor device status** with periodic heartbeat inserts
6. **Handle deep sleep** for battery-powered devices

## More Examples Coming Soon

- Motion sensor with image capture
- Multi-sensor dashboard
- Two-way communication (commands from Supabase)
- Offline buffering
- OTA updates

## Need Help?

- Check the main [README.md](../README.md)
- Open an issue on GitHub
- Ask in Supabase Discord
