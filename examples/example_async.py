"""Async example usage of supabase-micro library.

Demonstrates async/await patterns for non-blocking I/O on MicroPython devices.
Requires uasyncio (built into MicroPython 1.19+).
"""

import sys
sys.path.insert(0, 'src')

import uasyncio as asyncio
from supabase_micro import create_client

# Load credentials
def load_env():
    env_vars = {}
    paths = ["../.env", ".env"]
    for filename in paths:
        try:
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
            if env_vars:
                break
        except:
            continue
    return env_vars

env = load_env()
SUPABASE_URL = env.get("SUPABASE_URL") or ""
SUPABASE_KEY = env.get("SUPABASE_KEY") or ""

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Please provide Supabase credentials via .env file")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-anon-key")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def main():
    print("=" * 50)
    print("Supabase MicroPython Client - Async Example")
    print("=" * 50)

    # Example 1: Basic async query
    print("\n1. ASYNC SELECT - Fetch countries")
    result = await client.table("countries").select("*").limit(5).execute_async()

    if result["status_code"] == 200:
        print(f"   Success! Got {len(result['data'])} rows")
        for row in result["data"]:
            print(f"   - {row}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    # Example 2: Concurrent queries with asyncio.gather
    print("\n2. CONCURRENT QUERIES - Fetch multiple tables at once")
    results = await asyncio.gather(
        client.table("countries").select("name,code").limit(3).execute_async(),
        client.table("countries").select("name,code").eq("continent", "Asia").limit(3).execute_async(),
    )

    for i, res in enumerate(results):
        if res["status_code"] == 200:
            print(f"   Query {i + 1}: Got {len(res['data'])} rows")

    # Example 3: Async insert
    print("\n3. ASYNC INSERT - Add a new country")
    result = await client.table("countries").insert({
        "name": "Async Test Country",
        "code": "AT",
        "continent": "Async"
    }).execute_async()

    if 200 <= result["status_code"] < 300:
        print(f"   Success! Inserted: {result['data']}")
        test_id = None
        if isinstance(result["data"], list) and len(result["data"]) > 0:
            test_id = result["data"][0].get("id")
        elif isinstance(result["data"], dict):
            test_id = result["data"].get("id")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
        test_id = None

    # Example 4: Async update
    if test_id:
        print("\n4. ASYNC UPDATE - Update the test country")
        result = await (
            client.table("countries")
            .update({"name": "Async Updated Country"})
            .eq("id", test_id)
            .execute_async()
        )

        if 200 <= result["status_code"] < 300:
            print(f"   Success! Updated: {result['data']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    # Example 5: Async storage list
    print("\n5. ASYNC STORAGE - List files in bucket")
    result = await client.storage.from_("test-bucket").list_async(limit=5)

    if result["status_code"] == 200:
        print(f"   Found {len(result['data'])} files:")
        for file in result["data"]:
            print(f"   - {file.get('name', 'unknown')}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    # Example 6: Async storage upload
    print("\n6. ASYNC STORAGE - Upload a test file")
    test_data = b"Hello from async MicroPython!"
    result = await client.storage.from_("test-bucket").upload_async(
        "async_test.txt",
        test_data,
        "text/plain"
    )

    if 200 <= result["status_code"] < 300:
        print("   Success! File uploaded")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    # Example 7: Async storage download
    print("\n7. ASYNC STORAGE - Download the test file")
    result = await client.storage.from_("test-bucket").download_async("async_test.txt")

    if result["status_code"] == 200:
        downloaded_data = result["data"]
        print(f"   Success! Downloaded {len(downloaded_data)} bytes")
        print(f"   Content: {downloaded_data.decode('utf-8')}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")

    # Example 8: Mixing sync and async on same client
    print("\n8. MIXED MODE - Sync and async on same client")
    sync_result = client.table("countries").select("*").limit(1).execute()
    async_result = await client.table("countries").select("*").limit(1).execute_async()
    print(f"   Sync result status: {sync_result['status_code']}")
    print(f"   Async result status: {async_result['status_code']}")

    print("\n" + "=" * 50)
    print("Async example completed!")
    print("=" * 50)


asyncio.run(main())
