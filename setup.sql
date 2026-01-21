-- Setup SQL for supabase-micro examples
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)

-- Create countries table
CREATE TABLE IF NOT EXISTS countries (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    continent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE countries ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (for testing)
-- WARNING: In production, use more restrictive policies
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

-- Verify data
SELECT COUNT(*) as total_countries FROM countries;
