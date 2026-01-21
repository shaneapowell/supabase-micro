# Testing Guide

This guide explains how to test the supabase-micro library locally without physical hardware.

## Prerequisites

- [MicroPython](https://micropython.org/) (`brew install micropython`)
- [Node.js](https://nodejs.org/) (for npx to run Supabase CLI)
- A Supabase account and project

## Quick Start

### 0. Install the package

```bash
# Install in editable mode for development
pip install -e .
```

This makes the package importable so tests and examples can use `from supabase_micro import ...`

### 1. Get Supabase Credentials

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Settings** > **API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Project Reference ID** (e.g., `xxxxx` from the URL)
   - **anon/public key** (starts with `eyJ...`)

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
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

**Problem:** Not using MicroPython

**Solution:** Use `micropython` command, not `python`:
```bash
micropython test_basic.py  # ✓ Correct
python test_basic.py       # ✗ Wrong
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

## Next Steps

Once tests pass:

1. **Deploy to hardware**: See [INSTALL.md](INSTALL.md) for device installation
2. **Build your project**: Use the examples as templates
3. **Customize**: Modify `example.py` to test your own use cases

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

## Local Development with Supabase

You can also test with local Supabase (requires Docker):

```bash
# Start local Supabase
npx supabase start

# Update .env to use local URLs
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<shown in terminal after start>

# Run tests
micropython example.py
```

This gives you a fully local development environment without using your production Supabase project.
