# 🚨 IMPORTANT: Run This SQL Migration in Supabase

## Problem
Product images are not showing because the `images` column doesn't exist in the `products` table yet.

## Solution
Run this SQL in your Supabase SQL Editor:

```sql
-- Add images column to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS images TEXT[];

-- Add comment for documentation
COMMENT ON COLUMN products.images IS 'Array of image URLs (up to 3 per product)';

-- Optional: Add constraint to limit to 3 images
ALTER TABLE products 
ADD CONSTRAINT products_images_max_3 CHECK (array_length(images, 1) IS NULL OR array_length(images, 1) <= 3);
```

## How to Run

1. Go to your Supabase Dashboard
2. Select your project
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Paste the SQL above
6. Click **Run** or press `Cmd/Ctrl + Enter`

## Verification

After running, verify the column was added:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' 
AND column_name = 'images';
```

Should return:
```
column_name | data_type
------------|----------
images      | ARRAY
```

## After Migration

1. The `images` column will now exist on the `products` table
2. New products with images will store URLs in this array
3. ProductsModal will display images properly
4. Old products without images will show a placeholder 📦

## Test

1. Deploy a new agent with products
2. Upload 1-3 images per product
3. Go to Market → View Products
4. Images should now appear!

---

**Status**: ⚠️ **REQUIRED** - Must run before product images will work

