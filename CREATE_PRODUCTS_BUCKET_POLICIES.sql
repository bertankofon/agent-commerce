-- SQL to create storage policies for products bucket
-- Run this in Supabase SQL Editor AFTER creating the bucket via UI

-- Note: The bucket must be created first via Supabase Dashboard -> Storage
-- Bucket name: products
-- Public: YES (checked)

-- 1. Allow public to read product images
CREATE POLICY IF NOT EXISTS "Public can read products"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

-- 2. Allow service role (backend) to manage all operations
CREATE POLICY IF NOT EXISTS "Service role can manage products"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');

-- 3. Allow authenticated users to upload (optional)
CREATE POLICY IF NOT EXISTS "Authenticated can upload products"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'products');

-- Verify policies were created
SELECT * FROM storage.policies WHERE bucket_id = 'products';

