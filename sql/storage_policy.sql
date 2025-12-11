-- ============================================
-- SUPABASE STORAGE POLICIES
-- ============================================
-- Run these after creating the 'wardrobe-images' bucket

-- Allow authenticated users to upload images to their own folder
CREATE POLICY "Users can upload to own folder"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'wardrobe-images' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow anyone to view images (public bucket)
CREATE POLICY "Public images are viewable"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'wardrobe-images');

-- Allow users to delete their own images
CREATE POLICY "Users can delete own images"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'wardrobe-images' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
