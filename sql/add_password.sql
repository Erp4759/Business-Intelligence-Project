-- ============================================
-- Add Password Authentication to VAESTA
-- Run this in Supabase SQL Editor
-- ============================================

-- Add password_hash column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Add last_login tracking
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Update the updated_at timestamp when user logs in
-- (The trigger already exists from initial setup)
