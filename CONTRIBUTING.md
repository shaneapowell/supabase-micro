# Contributing & Testing

This guide explains how to test the supabase-micro library locally and contribute to development.

## Prerequisites

- [MicroPython](https://micropython.org/) (`brew install micropython`)
- [Node.js](https://nodejs.org/) (for npx to run Supabase CLI)
- A Supabase account and project

**Note:** For MicroPython testing, you don't need `pip install`. The tests use `sys.path` to load the library. However, if you're a Python developer and want better IDE support, you can optionally run `pip install -e .`

## Quick Start

### 1. Get Supabase Credentials

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Settings** > **API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Project Reference ID** (e.g., `xxxxx` from the URL)
   - **Publishable key** (`sb_publishable_...`) or legacy **anon key** (`eyJ...`)

### 2. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/supabase/supabase-micro.git
cd supabase-micro

# Create .env file
cp .env.example .env

# Edit .env and add your credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-publishable-or-anon-key
```

### 3. Run Database Migrations

```bash
# Link to your Supabase project (using npx, no installation required)
npx supabase link --project-ref YOUR_PROJECT_REF

# Push migrations to create tables and sample data
npx supabase db push
```

This will:
- Create a `countries` table with 14 sample countries
- Set up Row Level Security policies for testing
- Create a `test-bucket` storage bucket
- Configure public access policies

### 4. Run Tests

#### Basic Tests (Offline)

Test library components without network calls:

```bash
micropython tests/test_basic.py
```

This tests:
- Module imports
- URL parsing and encoding
- Query builder
- Client initialization
- Content type detection

#### Integration Tests (Online)

Test actual Supabase API calls:

```bash
micropython examples/example.py
```

This tests:
- SELECT queries with filters
- INSERT operations
- UPDATE operations
- Storage upload/download
- File listing

**Note:** The script intentionally leaves test data in your database so you can verify in the Supabase Dashboard.

### 5. Verify Results

Check your Supabase Dashboard:

1. **Database**: Table Editor > countries
   - Should see 14 countries + "Updated Test Country"

2. **Storage**: Storage > test-bucket
   - Should see "test.txt" file

## Test Output

Successful test output looks like:

```
==================================================
Supabase MicroPython Client - Example
==================================================

1. SELECT - Fetch all countries (limited to 5)
   Success! Got 5 rows
   - {'name': 'United States', 'code': 'US', ...}
   ...

2. SELECT with filters - Countries in Asia
   Found 3 Asian countries:
   - Japan (JP)
   - China (CN)
   - India (IN)

3. INSERT - Add a new country
   Success! Inserted: [{'id': 15, 'name': 'Test Country', ...}]

...

Example completed!
```

## Troubleshooting

### "Table not found" error

**Problem:** Migration not applied

**Solution:**
```bash
npx supabase db push
```

### "Bucket not found" error

**Problem:** Storage bucket not created

**Solution:** The migration should create it automatically. If not, manually create:
- Dashboard > Storage > New bucket
- Name: `test-bucket`
- Public: Yes

### "Permission denied" error

**Problem:** RLS policies not set up correctly

**Solution:** Check Row Level Security policies in Dashboard > Authentication > Policies

### Import errors

**Problem:** Not using MicroPython or wrong directory

**Solution:**
1. Use `micropython` command, not `python`
2. Run from project root directory
```bash
micropython tests/test_basic.py       # Correct
python tests/test_basic.py            # Wrong (not MicroPython)
cd tests && micropython test_basic.py # Wrong (wrong directory)
```

## Cleaning Up Test Data

### Remove test records

```sql
-- In Supabase SQL Editor
DELETE FROM countries WHERE name LIKE '%Test%';
```

### Delete storage files

```bash
# In Supabase Dashboard
Storage > test-bucket > Select test.txt > Delete
```

### Drop everything

```sql
-- In Supabase SQL Editor
DROP TABLE IF EXISTS countries CASCADE;
DELETE FROM storage.objects WHERE bucket_id = 'test-bucket';
DELETE FROM storage.buckets WHERE id = 'test-bucket';
```

## Local Development with Supabase

You can also test with local Supabase (requires Docker):

```bash
# Start local Supabase
npx supabase start

# Update .env to use local URLs
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<shown in terminal after start>

# Run tests
micropython examples/example.py
```

This gives you a fully local development environment without using your production Supabase project.

## Running Tests on CI/CD

For automated testing:

```bash
#!/bin/bash
# test.sh

# Install dependencies
brew install micropython  # or apt-get install micropython

# Configure
export SUPABASE_URL="$YOUR_SUPABASE_URL"
export SUPABASE_KEY="$YOUR_SUPABASE_KEY"
export SUPABASE_PROJECT_REF="$YOUR_PROJECT_REF"

# Run migrations
npx supabase link --project-ref "$SUPABASE_PROJECT_REF"
npx supabase db push

# Run tests
micropython tests/test_basic.py
micropython examples/example.py
```

## Contributing Guidelines

1. **Test on actual hardware** before submitting PRs (if possible)
2. **Keep memory usage low** — this library runs on constrained devices
3. **No external dependencies** — only use MicroPython built-ins
4. **Maintain compatibility** with MicroPython 1.19+
5. **Follow existing code style**

## Project Structure

```
supabase-micro/
├── src/supabase_micro/    # Library source code
│   ├── __init__.py
│   ├── client.py          # Main client
│   ├── http.py            # HTTP implementation
│   ├── postgrest.py       # Database operations
│   ├── storage.py         # File storage
│   ├── auth.py            # Authentication
│   └── utils.py           # Utilities
├── tests/                 # Test files
├── examples/              # Example scripts
├── supabase/              # Supabase config and migrations
└── docs/                  # Documentation
```

## Support

- [GitHub Issues](https://github.com/supabase/supabase-micro/issues)
- [Supabase Discord](https://discord.supabase.com)
