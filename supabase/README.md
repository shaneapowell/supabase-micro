# Supabase Setup for supabase-micro

This directory contains the Supabase configuration and migrations for testing the supabase-micro library.

## Quick Setup

### 1. Link to your Supabase project

```bash
supabase link --project-ref YOUR_PROJECT_REF
```

To find your project ref:
- Go to your [Supabase Dashboard](https://supabase.com/dashboard)
- Select your project
- Look at the URL: `https://supabase.com/dashboard/project/YOUR_PROJECT_REF`
- Or go to Settings > General > Reference ID

### 2. Push the migration to your remote database

```bash
supabase db push
```

This will:
- Create the `countries` table
- Set up Row Level Security policies
- Insert sample data (14 countries)
- Create the `test-bucket` storage bucket

### 3. Verify the setup

```bash
# Check migration status
supabase migration list

# Or test with MicroPython
cd ..
micropython example.py
```

## Alternative: Run migrations manually

If you prefer to run migrations through the Supabase Dashboard:

```bash
# View the migration SQL
cat migrations/20260121094303_create_countries_table.sql

# Copy and paste into: Dashboard > SQL Editor > New Query > Run
```

## Local Development (Optional)

You can also test locally with Supabase:

```bash
# Start local Supabase (requires Docker)
supabase start

# This will give you local URLs like:
# API URL: http://localhost:54321
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres

# Update your .env file to use local URLs for testing
```

## Migration Files

- `migrations/20260121094303_create_countries_table.sql` - Creates countries table and storage bucket

## Troubleshooting

### "Project not linked"
Run: `supabase link --project-ref YOUR_PROJECT_REF`

### "Permission denied"
Make sure you're logged in: `supabase login`

### "Migration already applied"
That's OK! The migration is idempotent and safe to run multiple times.

### Storage bucket creation fails
The migration will create the storage bucket automatically. If it fails, you can create it manually in the Dashboard.

## Next Steps

After running migrations:
1. Set up your `.env` file (see parent directory)
2. Run: `micropython example.py`
3. Build your IoT project!
