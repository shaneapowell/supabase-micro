# Auth Example Usage

## Local Testing (Default)

Just run it:
```bash
python examples/example_auth.py
```

Uses local Supabase at `http://127.0.0.1:54321`

## Remote Testing (Production)

### Step 1: Create User in Remote Supabase

1. Go to your Supabase Dashboard → **Authentication** → **Users**
2. Click **Add user** → **Create new user**
3. Enter:
   - Email: `test@example.com` (or your choice)
   - Password: `testpassword123` (or your choice)
   - Confirm email: ✓ (check this)
4. Click **Create user**

### Step 2: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Update with your values:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key-here
TEST_EMAIL=test@example.com
TEST_PASSWORD=testpassword123
```

**Where to find your credentials:**
- Dashboard → **Settings** → **API**
- URL: "Project URL"
- Key: "anon public" key

### Step 3: Install python-dotenv (Optional)

```bash
pip install python-dotenv
```

If not installed, you can use environment variables directly:
```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=testpassword123
python examples/example_auth.py
```

### Step 4: Run

```bash
python examples/example_auth.py
```

You should see:
```
Loaded configuration from .env file
Connecting to: https://your-project.supabase.co
...
Passed: 9/9
🎉 All tests passed!
```

## Troubleshooting

**"User already exists"**
- Normal after first run
- User is already created in your database

**"Invalid credentials"**
- Password doesn't match
- Check TEST_EMAIL and TEST_PASSWORD in .env

**"Could not find the table 'public.todos'"**
- Table doesn't exist in remote database
- Push migration: `supabase db push`
- Or create manually in Dashboard → **Table Editor**

**403 RLS violation**
- RLS policies not set up
- Ensure policies allow authenticated users to insert/select their own rows
