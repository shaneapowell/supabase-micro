# Auth Example

Tests all authentication features: signup, signin, sessions, RLS, user operations, token refresh, password reset, signout.

## Quick Start

**Local:** (uses http://127.0.0.1:54321)
```bash
supabase start
python examples/example_auth.py
```

**Remote:**
```bash
# 1. Copy and update credentials
cp .env.example .env
nano .env  # Add your URL and anon key from Dashboard → Settings → API

# 2. Run
python examples/example_auth.py
```

On first run, signup creates the test user automatically.

## Troubleshooting

- **Table not found**: Push migration with `supabase db push` or create todos table manually
- **Invalid credentials**: Check anon key in .env (long token starting with `eyJ...`)
- **403 RLS violation**: Ensure RLS policies allow authenticated users to manage their own rows
