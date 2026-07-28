# Asyncio Support

`supabase-micro` supports both synchronous (blocking) and asynchronous (non-blocking) operation. The async API uses `uasyncio`, which is built into MicroPython — no additional dependencies needed.

## Why Async?

On microcontrollers, network I/O can take hundreds of milliseconds or seconds. With synchronous calls, your device sits idle during that time. Async lets the event loop schedule other work while waiting:

```python
import uasyncio as asyncio
from supabase_micro import create_client

client = create_client(url, key)

async def main():
    # Multiple queries run concurrently, not sequentially
    countries, users = await asyncio.gather(
        client.table("countries").select("*").limit(5).execute_async(),
        client.table("users").select("*").limit(5).execute_async(),
    )
    print(f"Got {len(countries['data'])} countries and {len(users['data'])} users")

asyncio.run(main())
```

Two sequential sync requests take `2 x latency`. With `asyncio.gather()`, they complete in `1 x latency`.

## Dual-Mode API

Every I/O method has both a sync and async variant. The fluent query builder stays identical — only the terminal method changes:

| Operation | Sync | Async |
|-----------|------|-------|
| Database query | `.execute()` | `.execute_async()` |
| Sign up | `client.auth.sign_up()` | `client.auth.sign_up_async()` |
| Sign in | `client.auth.sign_in_with_password()` | `client.auth.sign_in_with_password_async()` |
| Sign out | `client.auth.sign_out()` | `client.auth.sign_out_async()` |
| Get user | `client.auth.get_user()` | `client.auth.get_user_async()` |
| Refresh session | `client.auth.refresh_session()` | `client.auth.refresh_session_async()` |
| Update user | `client.auth.update_user()` | `client.auth.update_user_async()` |
| Reset password | `client.auth.reset_password_for_email()` | `client.auth.reset_password_for_email_async()` |
| Refresh if needed | `client.auth.refresh_if_needed()` | `client.auth.refresh_if_needed_async()` |
| Storage upload | `bucket.upload()` | `bucket.upload_async()` |
| Storage download | `bucket.download()` | `bucket.download_async()` |
| Storage list | `bucket.list()` | `bucket.list_async()` |
| Storage delete | `bucket.delete()` | `bucket.delete_async()` |

**Pure methods** like `get_session()` and `should_refresh_token()` do no I/O — they work the same in both contexts.

## Usage Patterns

### Basic async query

```python
result = await client.table("sensors").select("*").eq("active", True).execute_async()
```

### Concurrent queries

```python
results = await asyncio.gather(
    client.table("sensors").select("*").execute_async(),
    client.table("config").select("*").execute_async(),
    client.table("alerts").select("*").execute_async(),
)
```

### Async auth flow

```python
# Sign in without blocking
result = await client.auth.sign_in_with_password_async(email, password)

if result["status_code"] == 200:
    # Queries use the authenticated session automatically
    result = await client.table("user_data").select("*").execute_async()
```

### Async storage

```python
# Upload
result = await client.storage.from_("bucket").upload_async("data.txt", file_bytes, "text/plain")

# Download
result = await client.storage.from_("bucket").download_async("data.txt")

# List
result = await client.storage.from_("bucket").list_async()
```

### Sensor logging with non-blocking I/O

```python
async def sensor_loop(client, interval=60):
    while True:
        # Refresh auth if needed (non-blocking)
        await client.auth.refresh_if_needed_async()

        # Read sensor (blocking on device, but fast)
        temp = read_temperature()

        # Upload reading without blocking the loop
        await client.table("readings").insert({
            "device": "esp32-01",
            "temperature": temp,
            "ts": get_timestamp()
        }).execute_async()

        # Sleep yields to event loop
        await asyncio.sleep(interval)
```

## Mixing Sync and Async

You can mix sync and async calls on the same client instance. The sync methods block; the async methods yield. Choose per-call based on your needs:

```python
# Sync — simple, blocking
result = client.table("config").select("*").execute()

# Async — non-blocking
result = await client.table("sensors").select("*").execute_async()
```

## Migration from Sync to Async

Converting existing code is straightforward:

1. Wrap your main logic in an `async def main():` function
2. Replace terminal methods with `_async` variants
3. Add `await` before each async call
4. Entry point: `asyncio.run(main())`

**Before (sync):**
```python
result = client.table("readings").select("*").limit(10).execute()
```

**After (async):**
```python
result = await client.table("readings").select("*").limit(10).execute_async()
```

## Compatibility

- Requires MicroPython with `uasyncio` built-in (v1.19+)
- `uasyncio` is imported lazily — sync-only usage has zero overhead
- Works on ESP32, ESP8266, RP2040, and other MicroPython targets

## Architecture

Async methods share internal logic with their sync counterparts via extracted helper functions. The only difference is the I/O layer:

```
execute()       → http_client.request()       → socket I/O (blocking)
execute_async() → http_client.request_async() → uasyncio I/O (non-blocking)
```

Request building and response parsing are shared — no code duplication between sync and async paths.
