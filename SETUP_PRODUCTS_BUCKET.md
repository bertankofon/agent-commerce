# 🗄️ Supabase Products Bucket - Quick Setup

## ✅ Database Table Already Exists!

The `products` table is already set up with:
```sql
images text[] null,  -- Array of image URLs (max 3)
constraint products_images_max_3 check (
  (array_length(images, 1) is null) OR (array_length(images, 1) <= 3)
)
```

**Perfect!** ✅

---

## 🪣 Create Storage Bucket

### Step 1: Create Bucket in Supabase Dashboard

1. Go to **Supabase Dashboard** → **Storage**
2. Click **"New bucket"**
3. Settings:
   ```
   Name: products
   Public bucket: ✅ YES (checked)
   File size limit: 5MB
   Allowed MIME types: image/*
   ```
4. Click **Create bucket**

---

### Step 2: Set Storage Policies

Go to **Storage** → **products** bucket → **Policies** → Click **"New Policy"**

Or run this SQL in **SQL Editor**:

```sql
-- 1. Allow public to READ product images
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

-- 2. Allow authenticated users to INSERT images
CREATE POLICY "Authenticated can upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'products');

-- 3. Allow service_role (backend) to manage all
CREATE POLICY "Service role can manage"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');

-- 4. Allow users to delete their own images (optional)
CREATE POLICY "Users can delete own images"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'products' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);
```

---

## ✅ Verify Setup

### Check 1: Bucket Exists
```sql
SELECT * FROM storage.buckets WHERE name = 'products';
```

**Expected Result:**
```
name: products
public: true
```

### Check 2: Policies Active
```sql
SELECT * FROM storage.policies WHERE bucket_id = 'products';
```

**Expected Result:** 3-4 policies (public read, authenticated write, service_role manage)

---

## 🧪 Test Product Image Upload

### Test 1: Deploy Merchant with Product Image

1. Go to `/deploy?type=merchant`
2. Fill in agent details
3. Add a product
4. **Click "📸 Upload Image"**
5. Select an image (< 5MB)
6. See preview ✅
7. Click **DEPLOY AGENT**

### Test 2: Check Backend Logs

Look for:
```
[INFO] Uploading product image...
[INFO] Uploaded product 0 image 0: https://<project>.supabase.co/storage/v1/object/public/products/images/<agent_id>/product_0/image.png
[INFO] Successfully inserted 1 products with images
```

### Test 3: Verify in Supabase

**Storage:**
1. Go to **Storage** → **products** bucket
2. Navigate to `images/<agent_id>/product_0/`
3. See uploaded image ✅

**Database:**
```sql
SELECT id, name, images 
FROM products 
WHERE agent_id = '<your_agent_id>'
LIMIT 1;
```

**Expected Result:**
```json
{
  "id": "uuid",
  "name": "MacBook Pro",
  "images": [
    "https://<project>.supabase.co/storage/v1/object/public/products/images/<agent_id>/product_0/image.png"
  ]
}
```

### Test 4: View in UI

1. Go to **Market** page
2. Find your merchant agent
3. Click **"View Products"**
4. **Product image should display!** 🎉

---

## 🐛 Troubleshooting

### Issue: "Failed to upload image"

**Backend Error:**
```
StorageException: The resource already exists
```

**Fix:** Delete old images first or use unique filenames

**Backend Error:**
```
StorageException: new row violates row-level security policy
```

**Fix:** Check policies are created and service_role key is correct in `.env`

---

### Issue: "Images not showing in UI"

**Check:**
```sql
-- 1. Check if images array is populated
SELECT images FROM products WHERE id = '<product_id>';

-- 2. Test URL accessibility (copy URL and open in browser)
-- Should show the image, not 404
```

**Fix:**
- Ensure bucket is **public**
- Check image URLs are complete (not truncated)
- Verify policies allow public SELECT

---

### Issue: "CORS error in browser"

**Fix:** Supabase handles CORS automatically for public buckets. If you see CORS errors:

1. Check bucket is public
2. Verify URL format: `https://<project>.supabase.co/storage/v1/object/public/products/...`
3. Use public URL, not signed URL

---

## 📂 Storage Structure

```
products/
└── images/
    └── <agent_uuid>/
        ├── product_0/
        │   └── image.png
        ├── product_1/
        │   └── photo.jpg
        └── product_2/
            └── pic.webp
```

---

## 🚀 Ready to Test!

**Checklist:**
- [x] `products` table exists with `images text[]` column ✅
- [ ] `products` bucket created in Storage
- [ ] Storage policies set (public read, service_role write)
- [ ] `.env` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- [ ] Backend running
- [ ] Frontend running

**Once bucket is created, product images will work immediately!** 📸✨

---

## 💡 Quick SQL Setup (All-in-One)

Run this in Supabase SQL Editor:

```sql
-- Create policies for products bucket (bucket should exist first via UI)
CREATE POLICY IF NOT EXISTS "Public can read products"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

CREATE POLICY IF NOT EXISTS "Service role can manage products"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');

CREATE POLICY IF NOT EXISTS "Authenticated can upload products"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'products');
```

**Done! 🎉**

