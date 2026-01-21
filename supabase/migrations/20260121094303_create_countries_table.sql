-- Create countries table for supabase-micro testing
CREATE TABLE IF NOT EXISTS countries (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    continent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE countries ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for testing
-- WARNING: In production, use more restrictive policies
DROP POLICY IF EXISTS "Enable all access for testing" ON countries;
CREATE POLICY "Enable all access for testing" ON countries
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Insert sample data
INSERT INTO countries (name, code, continent) VALUES
    ('United States', 'US', 'North America'),
    ('Canada', 'CA', 'North America'),
    ('Mexico', 'MX', 'North America'),
    ('Brazil', 'BR', 'South America'),
    ('Argentina', 'AR', 'South America'),
    ('United Kingdom', 'GB', 'Europe'),
    ('France', 'FR', 'Europe'),
    ('Germany', 'DE', 'Europe'),
    ('Japan', 'JP', 'Asia'),
    ('China', 'CN', 'Asia'),
    ('India', 'IN', 'Asia'),
    ('Australia', 'AU', 'Oceania'),
    ('South Africa', 'ZA', 'Africa'),
    ('Egypt', 'EG', 'Africa')
ON CONFLICT DO NOTHING;

-- Create storage bucket for testing (if not exists)
-- Note: This requires the storage schema to be available
INSERT INTO storage.buckets (id, name, public)
VALUES ('test-bucket', 'test-bucket', true)
ON CONFLICT (id) DO NOTHING;

-- Enable public access to test-bucket
DROP POLICY IF EXISTS "Public Access" ON storage.objects;
CREATE POLICY "Public Access"
ON storage.objects FOR ALL
USING (bucket_id = 'test-bucket');
