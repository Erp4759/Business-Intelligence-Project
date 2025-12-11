-- ============================================
-- SUPABASE STORAGE POLICIES (FIXED FOR PUBLISHABLE KEY)
-- ============================================
-- Run this in Supabase SQL Editor after creating 'wardrobe-images' bucket
-- This allows uploads using publishable key (no auth required)

-- IMPORTANT: Make sure bucket is PUBLIC first!

-- Allow anyone to upload (for publishable key access)
CREATE POLICY "Allow public uploads to wardrobe-images"
ON storage.objects FOR INSERT
TO public
WITH CHECK (bucket_id = 'wardrobe-images');

-- Allow anyone to view images (public bucket)
CREATE POLICY "Public images are viewable"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'wardrobe-images');

-- Allow anyone to delete (optional - for cleanup)
CREATE POLICY "Allow public deletes from wardrobe-images"
ON storage.objects FOR DELETE
TO public
USING (bucket_id = 'wardrobe-images');

-- If you get "policy already exists" error, drop old policies first:
-- DROP POLICY IF EXISTS "Users can upload to own folder" ON storage.objects;
-- DROP POLICY IF EXISTS "Public images are viewable" ON storage.objects;
-- DROP POLICY IF EXISTS "Users can delete own images" ON storage.objects;
