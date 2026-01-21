# Setup Guide for Testing supabase-micro

This guide will help you set up your Supabase project to test the supabase-micro library.

## Prerequisites

- A Supabase account (sign up at https://supabase.com)
- A Supabase project created
- MicroPython installed (`brew install micropython`)

## Step 1: Get Your Supabase Credentials

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** > **API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

## Step 2: Configure Environment Variables

Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## Step 3: Run SQL Migration

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor** (in the left sidebar)
3. Click **New Query**
4. Copy the contents of `setup.sql`
5. Paste it into the SQL Editor
6. Click **Run** or press `Ctrl+Enter`

This will:
- Create a `countries` table
- Enable Row Level Security
- Create policies for testing
- Insert sample data

## Step 4: Create Storage Bucket

1. In your Supabase Dashboard, go to **Storage**
2. Click **New bucket**
3. Name: `test-bucket`
4. Public bucket: **Yes** (for easier testing)
5. Click **Create bucket**

## Step 5: Verify Setup

Run the setup verification script:

```bash
micropython setup.py
```

This will check:
- Database table exists
- Data was inserted
- Permissions are configured
- Your credentials work

## Step 6: Run Examples

Now you can run the example script:

```bash
micropython example.py
```

This will test:
- SELECT queries with filters
- INSERT operations
- UPDATE operations
- DELETE operations
- Storage upload/download
- File listing

## Troubleshooting

### "Table not found" error
- Make sure you ran `setup.sql` in the SQL Editor
- Check that you're using the correct project URL

### "Bucket not found" error
- Create the `test-bucket` in Storage (Step 4)
- Make sure the bucket is public

### "Permission denied" error
- Check Row Level Security policies in your Supabase Dashboard
- Verify you're using the `anon` key, not the `service_role` key

### "UnicodeDecodeError" or import errors
- Make sure you're using `micropython` command, not `python`
- Verify all library files are in the same directory

## What's Next?

Once setup is complete, you can:
1. Modify `example.py` to test your own queries
2. Deploy the library to actual MicroPython devices (ESP32, RP2040)
3. Build your IoT project with Supabase backend!

## Cleanup

To remove test data:

```sql
-- Run in SQL Editor
DROP TABLE IF EXISTS countries CASCADE;
```

To delete the storage bucket:
1. Go to Storage in Dashboard
2. Click the bucket settings
3. Delete bucket
