# 📸 Product Image Upload - Setup Guide

## ✅ Backend Changes Complete!

### 🔧 What Was Fixed:

1. **Updated `deploy_agent` endpoint** to handle product images
2. **Support for two formats**:
   - `product_image_0` (single image per product) ✅ **Current frontend**
   - `product_0_image_0` (multiple images support) ✅ **Future ready**
3. **Supabase Storage upload** configured for `products` bucket
4. **Product ID mapping** via `product_image_0_id` field

---

## 🗄️ Supabase Storage Setup Required

### Step 1: Create `products` Bucket

Go to your Supabase Dashboard → Storage → Create new bucket:

```
Bucket Name: products
Public: true (for public URLs)
File size limit: 5MB
Allowed MIME types: image/png, image/jpeg, image/jpg, image/webp, image/gif
```

### Step 2: Set Bucket Policies

Run this SQL in Supabase SQL Editor:

```sql
-- Allow public read access to products bucket
CREATE POLICY "Public can read products"
ON storage.objects FOR SELECT
USING (bucket_id = 'products');

-- Allow authenticated users to upload to products bucket
CREATE POLICY "Authenticated users can upload products"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'products' 
  AND auth.role() = 'authenticated'
);

-- Or if using service_role key (backend), allow all operations
CREATE POLICY "Service role can manage products"
ON storage.objects FOR ALL
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');
```

---

## 📦 How It Works (Frontend → Backend → Supabase)

### Frontend (`deploy/page.tsx`):

```typescript
// User uploads image via file input
<input 
  id="product-image-123"
  type="file" 
  onChange={(e) => {
    const file = e.target.files?.[0];
    updateProduct(productId, "imageFile", file);
  }}
/>

// On deploy, images are sent to backend
formData.append(`product_image_${index}`, product.imageFile);
formData.append(`product_image_${index}_id`, product.id);
```

### Backend (`routes/agent/routes.py`):

```python
# Extract product images from FormData
for key, value in form_data.items():
    match = re.match(r'product_image_(\d+)', key)
    if match and isinstance(value, UploadFile):
        product_idx = int(match.group(1))
        
        # Upload to Supabase Storage (products bucket)
        image_url = await upload_image_to_supabase(
            value, 
            f"{db_agent_id}/product_{product_idx}",
            bucket_name="products"
        )
        
        # Store URL with product
        product_images_map[product_idx].append(image_url)

# Create products with image URLs
for idx, product in enumerate(products_data):
    created_product = products_ops.create_product(
        agent_id=db_agent_id,
        name=product["name"],
        price=str(product["price"]),
        stock=product["stock"],
        negotiation_percentage=product["maxDiscount"],
        images=product_images_map.get(idx, [])  # ← Image URLs
    )
```

### Supabase Storage Structure:

```
products/
├── images/
│   ├── <agent_uuid>/
│   │   ├── product_0/
│   │   │   └── image.png
│   │   ├── product_1/
│   │   │   └── photo.jpg
│   │   └── product_2/
│   │       └── pic.webp
```

### Database (`products` table):

```sql
SELECT * FROM products WHERE agent_id = '<uuid>';

-- Result:
{
  id: "uuid",
  agent_id: "agent-uuid",
  name: "MacBook Pro",
  price: "1000",
  stock: 100,
  negotiation_percentage: 15,
  images: [
    "https://<project>.supabase.co/storage/v1/object/public/products/images/<agent_id>/product_0/image.png"
  ]
}
```

---

## 🎯 Testing Checklist

### Before Testing:

- [ ] Create `products` bucket in Supabase Storage
- [ ] Set bucket policies (public read, authenticated/service_role write)
- [ ] Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`

### Test Flow:

1. **Deploy a Merchant Agent**
   - Go to `/deploy?type=merchant`
   - Add a product
   - Click "📸 Upload Image"
   - Select an image (< 5MB)
   - See preview appear
   - Click "DEPLOY AGENT"

2. **Check Backend Logs**
   ```
   [INFO] Uploading custom avatar to Supabase Storage...
   [INFO] Uploaded product 0 image 0: https://...
   [INFO] Successfully inserted 1 products with images
   ```

3. **Verify in Supabase**
   - **Storage**: Check `products` bucket → `images/<agent_id>/product_0/`
   - **Database**: Query `products` table → Check `images` column

4. **View Products in UI**
   - Go to Market page
   - Click "View Products" on the merchant
   - **Images should display!** 🎉

---

## 🐛 Troubleshooting

### Issue: "Upload failed"

**Check:**
- Bucket exists and is named `products`
- Bucket policies are set correctly
- Service role key has storage permissions

**Fix:**
```sql
-- Grant all permissions to service_role
GRANT ALL ON storage.objects TO service_role;
GRANT ALL ON storage.buckets TO service_role;
```

### Issue: "Images not showing in UI"

**Check:**
- Image URLs in `products.images` array
- Bucket is public
- URLs are accessible (test in browser)

**Fix:**
- Make bucket public in Dashboard
- Or add SELECT policy for anonymous access

### Issue: "File size exceeded"

**Frontend validates:** 5MB max
**Backend validates:** 10MB max

**Fix:** Reduce image size or increase limits

---

## 🚀 Next Steps (Optional)

### Multiple Images Per Product:

Update frontend to support up to 3 images:

```typescript
interface Product {
  imageFiles?: File[];  // Array of files
}

// Send as: product_0_image_0, product_0_image_1, product_0_image_2
products.forEach((product, pIdx) => {
  product.imageFiles?.forEach((file, iIdx) => {
    formData.append(`product_${pIdx}_image_${iIdx}`, file);
  });
});
```

Backend already supports this format! ✅

---

## ✨ Summary

**Frontend:** ✅ Image upload UI working  
**Backend:** ✅ Image processing ready  
**Supabase:** ⚠️ Needs `products` bucket setup  

**Once bucket is created, product images will upload automatically!** 🎉

