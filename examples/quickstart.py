"""
Quickstart Example - Basic usage of supabase-micro
This is the simplest way to get started with the library
"""

import network
import time
from supabase_micro import create_client

# ===== STEP 1: Connect to WiFi =====
print("Connecting to WiFi...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("your-wifi-ssid", "your-wifi-password")

# Wait for connection
timeout = 10
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1
    print('.', end='')

if not wlan.isconnected():
    print("\n✗ Failed to connect to WiFi")
    raise Exception("WiFi connection failed")

print('\n✓ WiFi Connected!')

# ===== STEP 2: Create Supabase Client =====
client = create_client(
    "https://your-project.supabase.co",  # Replace with your project URL
    "your-anon-key-here"                  # Replace with your anon key
)
print("✓ Supabase client ready!")

# ===== STEP 3: Try Database Operations =====

# SELECT - Read data
print("\n1. Reading data...")
result = client.table("your_table").select("*").limit(5).execute()
if result["status_code"] == 200:
    print(f"✓ Got {len(result['data'])} rows")
    for row in result["data"]:
        print(f"  - {row}")
else:
    print(f"✗ Error: {result['error']}")

# INSERT - Create new data
print("\n2. Inserting data...")
result = client.table("your_table").insert({
    "name": "Test from MicroPython",
    "value": 42,
    "timestamp": time.time()
}).execute()

if result["status_code"] in [200, 201]:
    print("✓ Data inserted successfully!")
    print(f"  New row: {result['data']}")
else:
    print(f"✗ Error: {result['error']}")

# UPDATE - Modify data
print("\n3. Updating data...")
result = (
    client.table("your_table")
    .update({"value": 100})
    .eq("name", "Test from MicroPython")
    .execute()
)

if result["status_code"] == 200:
    print("✓ Data updated!")
else:
    print(f"✗ Error: {result['error']}")

# DELETE - Remove data
print("\n4. Deleting data...")
result = (
    client.table("your_table")
    .delete()
    .eq("name", "Test from MicroPython")
    .execute()
)

if result["status_code"] in [200, 204]:
    print("✓ Data deleted!")
else:
    print(f"✗ Error: {result['error']}")

# ===== STEP 4: Try Storage Operations =====

# Upload a file
print("\n5. Uploading file to storage...")
file_data = b"Hello from MicroPython!"
result = client.storage.from_("your-bucket").upload(
    "test.txt",
    file_data,
    "text/plain"
)

if result["status_code"] in [200, 201]:
    print("✓ File uploaded!")
else:
    print(f"✗ Error: {result['error']}")

# Download the file
print("\n6. Downloading file...")
result = client.storage.from_("your-bucket").download("test.txt")

if result["status_code"] == 200:
    print("✓ File downloaded!")
    print(f"  Content: {result['data'].decode('utf-8')}")
else:
    print(f"✗ Error: {result['error']}")

# Delete the file
print("\n7. Deleting file...")
result = client.storage.from_("your-bucket").delete("test.txt")

if result["status_code"] in [200, 204]:
    print("✓ File deleted!")
else:
    print(f"✗ Error: {result['error']}")

print("\n" + "="*40)
print("✓ Quickstart completed!")
print("="*40)
