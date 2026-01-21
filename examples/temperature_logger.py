"""
Temperature Logger Example for ESP32/ESP8266
Reads temperature from a sensor and logs it to Supabase every 60 seconds
"""

import network
import time
import machine
from supabase_micro import create_client

# ===== CONFIGURATION =====
WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
DEVICE_NAME = "esp32-sensor-01"
LOG_INTERVAL = 60  # seconds

# ===== CONNECT TO WIFI =====
print("Connecting to WiFi...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

while not wlan.isconnected():
    time.sleep(0.5)
    print('.', end='')

print('\n✓ WiFi Connected!')
print('IP:', wlan.ifconfig()[0])

# ===== INITIALIZE SUPABASE CLIENT =====
print("\nInitializing Supabase client...")
client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✓ Client ready!")

# ===== SETUP TEMPERATURE SENSOR =====
# For ESP32 internal temperature sensor
if hasattr(machine, 'ADC'):
    # ESP32/ESP8266 - adjust pin as needed
    adc = machine.ADC(machine.Pin(34))  # Use your sensor pin
    adc.atten(machine.ADC.ATTN_11DB)
else:
    # Simulated sensor for testing
    print("⚠ No ADC found, using simulated temperature")
    adc = None

def read_temperature():
    """Read temperature from sensor"""
    if adc:
        # Read ADC value and convert to temperature
        # Adjust this formula for your specific sensor
        raw_value = adc.read()
        temp_celsius = (raw_value / 4095.0) * 100  # Example conversion
        return round(temp_celsius, 2)
    else:
        # Simulated temperature for testing
        import random
        return round(20 + random.random() * 10, 2)

# ===== MAIN LOOP =====
print("\n" + "="*40)
print("Starting temperature logging...")
print(f"Device: {DEVICE_NAME}")
print(f"Interval: {LOG_INTERVAL}s")
print("="*40 + "\n")

reading_count = 0

while True:
    try:
        # Read temperature
        temp = read_temperature()
        reading_count += 1

        print(f"[{reading_count}] Temperature: {temp}°C")

        # Log to Supabase
        result = client.table("temperature_readings").insert({
            "device_name": DEVICE_NAME,
            "temperature": temp,
            "timestamp": time.time()
        }).execute()

        if result["status_code"] in [200, 201]:
            print(f"  ✓ Logged to Supabase (ID: {result['data'][0]['id']})")
        else:
            print(f"  ✗ Error: {result.get('error')}")

        # Wait before next reading
        time.sleep(LOG_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopping logger...")
        break
    except Exception as e:
        print(f"  ✗ Error: {e}")
        time.sleep(5)  # Wait 5s before retry

print("Logger stopped.")
