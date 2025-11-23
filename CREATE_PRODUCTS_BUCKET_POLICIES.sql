-- SQL to create storage policies for products bucket
-- Run this in Supabase SQL Editor AFTER creating the bucket via UI

-- Note: The bucket must be created first via Supabase Dashboard -> Storage
-- Bucket name: products
-- Public: YES (checked)

-- Drop existing policies first (if they exist)
DROP POLICY IF EXISTS "Public can read products" ON storage.objects;
DROP POLICY IF EXISTS "Service role can manage products" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated can upload products" ON storage.objects;

-- 1. Allow public to read product images
CREATE POLICY "Public can read products"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

-- 2. Allow service role (backend) to manage all operations
CREATE POLICY "Service role can manage products"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');

-- 3. Allow authenticated users to upload (optional)
CREATE POLICY "Authenticated can upload products"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'products');

-- Verify policies were created
SELECT 
  policyname as name, 
  'products' as bucket_id,
  CASE 
    WHEN cmd = 'r' THEN 'SELECT'
    WHEN cmd = 'a' THEN 'INSERT'
    WHEN cmd = 'w' THEN 'UPDATE'
    WHEN cmd = 'd' THEN 'DELETE'
    WHEN cmd = '*' THEN 'ALL'
  END as command
FROM pg_policies 
WHERE schemaname = 'storage' 
  AND tablename = 'objects'
  AND policyname LIKE '%products%';

