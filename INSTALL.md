# Installation Guide

## For MicroPython Devices (ESP32, ESP8266, RP2040, etc.)

### Method 1: Using mpremote (Recommended)

```bash
# 1. Install mpremote
pip install mpremote

# 2. Connect your device via USB

# 3. Copy the library to your device
mpremote cp -r src/supabase_micro :/lib/supabase_micro

# 4. Verify installation
mpremote exec "import supabase_micro; print('✓ Library installed!')"
```

### Method 2: Using ampy

```bash
# 1. Install ampy
pip install adafruit-ampy

# 2. Find your device port
# macOS/Linux: usually /dev/ttyUSB0 or /dev/ttyACM0
# Windows: usually COM3, COM4, etc.

# 3. Copy each file (ampy doesn't support directories)
ampy --port /dev/ttyUSB0 mkdir /lib
ampy --port /dev/ttyUSB0 mkdir /lib/supabase_micro
ampy --port /dev/ttyUSB0 put src/supabase_micro/__init__.py /lib/supabase_micro/__init__.py
ampy --port /dev/ttyUSB0 put src/supabase_micro/client.py /lib/supabase_micro/client.py
ampy --port /dev/ttyUSB0 put src/supabase_micro/http.py /lib/supabase_micro/http.py
ampy --port /dev/ttyUSB0 put src/supabase_micro/postgrest.py /lib/supabase_micro/postgrest.py
ampy --port /dev/ttyUSB0 put src/supabase_micro/storage.py /lib/supabase_micro/storage.py
ampy --port /dev/ttyUSB0 put src/supabase_micro/utils.py /lib/supabase_micro/utils.py

# 4. Verify
ampy --port /dev/ttyUSB0 ls /lib/supabase_micro
```

### Method 3: Using Thonny IDE

1. Open [Thonny IDE](https://thonny.org/)
2. Connect your MicroPython device
3. Click **View → Files** to show the file browser
4. In the left pane (your computer), navigate to `src/supabase_micro` folder
5. Right-click the `supabase_micro` folder
6. Select **Upload to /lib/** (creates `/lib/supabase_micro` on device)
7. Wait for upload to complete

### Method 4: Manual File Copy (WebREPL)

For ESP8266/ESP32 with WebREPL enabled:

1. Enable WebREPL on your device:
```python
import webrepl_setup
# Follow the prompts
```

2. Connect to your device's WiFi AP
3. Open http://micropython.org/webrepl/
4. Upload each `.py` file from `src/supabase_micro/` to `/lib/supabase_micro/` on device

## For Local Development/Testing

See [TESTING.md](TESTING.md) for complete local testing guide.

Quick install for Python developers:

```bash
cd /path/to/supabase-micro
pip install -e .
```

## Verify Installation

### On MicroPython Device

```python
# In REPL or main.py
from supabase_micro import create_client
print("✓ supabase-micro is installed!")

# Check version
import supabase_micro
print(f"Version: {supabase_micro.__version__}")
```

### Test Basic Functionality

```python
from supabase_micro import create_client

# This should work (creates client, doesn't connect yet)
client = create_client(
    "https://example.supabase.co",
    "test-key"
)
print(f"✓ Client created: {client.host}")
```

## File Size

Total library size: ~35KB (source files only)

Individual files:
- `__init__.py`: 1.3 KB
- `client.py`: 1.8 KB
- `http.py`: 5.4 KB
- `postgrest.py`: 6.8 KB
- `storage.py`: 7.0 KB
- `utils.py`: 4.7 KB

## Memory Requirements

- **ESP32**: ✓ Works well (~240KB+ RAM)
- **ESP8266**: ✓ Works with careful memory management (~40KB free)
- **RP2040**: ✓ Works excellently (264KB RAM)
- **Other boards**: Should work if you have 40KB+ free RAM

## Troubleshooting

### "ImportError: no module named 'supabase_micro'"

**Problem**: Library not in the correct location

**Solutions**:
1. Check the library is in `/lib/supabase_micro/` on your device
2. List files: `mpremote ls /lib/supabase_micro`
3. Verify `__init__.py` exists

### "MemoryError" on ESP8266

**Problem**: ESP8266 has limited RAM

**Solutions**:
1. Free up RAM: `import gc; gc.collect()`
2. Use `.limit()` in queries to get smaller datasets
3. Don't store large result sets in memory
4. Process data immediately and discard

### "OSError: [Errno 2] ENOENT"

**Problem**: Files not found or wrong path

**Solutions**:
1. Use absolute paths: `/lib/supabase_micro/`
2. Check spelling of directory name (underscore not hyphen)
3. Verify all files were uploaded

### Upload fails with mpremote

**Problem**: Connection issues

**Solutions**:
1. Try different USB cable (data cable, not charging-only)
2. Check device is in bootloader mode if needed
3. Try: `mpremote connect /dev/ttyUSB0 cp -r src/supabase_micro :/lib/supabase_micro`
4. On macOS, use `/dev/cu.usbserial-*` instead of `/dev/tty.*`

## Next Steps

1. ✓ Library installed
2. See [examples/README.md](examples/README.md) for usage examples
3. Check [README.md](README.md) for full API documentation
4. Run [examples/quickstart.py](examples/quickstart.py) to test

## Uninstall

To remove the library from your device:

```bash
# Using mpremote
mpremote rm -r /lib/supabase_micro

# Using ampy
ampy --port /dev/ttyUSB0 rmdir /lib/supabase_micro

# Using Thonny
# Right-click folder in Files view → Delete
```
