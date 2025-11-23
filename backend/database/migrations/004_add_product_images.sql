-- Migration: Add images array column to products table
-- This enables storing multiple image URLs (up to 3) per product

-- Add images column as TEXT array
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS images TEXT[];

-- Add comment
COMMENT ON COLUMN products.images IS 'Array of image URLs (up to 3 per product)';

-- Optional: If you want to add a check constraint for max 3 images
-- ALTER TABLE products 
-- ADD CONSTRAINT products_images_max_3 CHECK (array_length(images, 1) <= 3);

