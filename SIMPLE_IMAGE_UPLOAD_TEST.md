# 📸 Simple Product Image Upload - Ready to Test!

## ✅ What Changed (Completely Rewritten)

### Before (Complex):
- Multiple file inputs
- Complex preview logic
- Drag & drop areas
- URL fallback options
- Hard to debug

### After (Simple):
- Single file input per product
- One button: "Choose Image"
- Clear preview with remove button
- Direct Supabase upload
- **Easy to debug!**

---

## 🎯 How It Works Now

### Frontend (`deploy/page.tsx`):

```typescript
// 1. User clicks "Choose Image" button
<label htmlFor={`img-${product.id}`}>
  📷 Choose Image
</label>

// 2. File input (hidden)
<input
  id={`img-${product.id}`}
  type="file"
  accept="image/*"
  onChange={(e) => {
    const file = e.target.files?.[0];
    if (file && file.size <= 5MB) {
      updateProduct(product.id, "imageFile", file);
    }
  }}
/>

// 3. Show preview
{product.imageFile && (
  <img src={URL.createObjectURL(product.imageFile)} />
  <button onClick={() => remove()}>✕</button>
)}

// 4. On deploy, send to backend
formData.append(`product_image_${index}`, product.imageFile);
```

### Backend (`routes/agent/routes.py`):

```python
# 1. Extract product images from FormData
for idx, product in enumerate(products_data):
    image_key = f"product_image_{idx}"  # Simple!
    
    if image_key in form_data:
        image_file = form_data[image_key]
        
        # 2. Upload to Supabase Storage
        image_url = await upload_product_image(
            image_file,
            str(agent_id),
            idx
        )
        
        # 3. Save URL to database
        products_ops.create_product(
            ...,
            images=[image_url]  # Array with 1 image
        )
```

### New Upload Utility (`utils/image_upload.py`):

```python
async def upload_product_image(image_file, agent_id, product_index):
    """
    Simple image upload to Supabase Storage
    """
    # Read file
    file_content = await image_file.read()
    
    # Create path: images/{agent_id}/product_{index}.jpg
    file_path = f"images/{agent_id}/product_{product_index}.jpg"
    
    # Upload to products bucket
    client.storage.from_("products").upload(
        path=file_path,
        file=file_content,
        file_options={"upsert": "true"}
    )
    
    # Get public URL
    return client.storage.from_("products").get_public_url(file_path)
```

---

## 🧪 Test Steps

### Step 1: Check Supabase Storage Bucket

Go to **Supabase Dashboard → Storage**

**Check if `products` bucket exists:**
- ✅ If YES → Continue to Step 2
- ❌ If NO → Create it:
  ```
  Name: products
  Public: ✅ YES
  ```

### Step 2: Set Storage Policies

Run this in **SQL Editor**:

```sql
-- Allow public read
CREATE POLICY IF NOT EXISTS "Public can read products"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

-- Allow service_role to upload
CREATE POLICY IF NOT EXISTS "Service role can manage products"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');
```

### Step 3: Restart Backend

```bash
cd backend
# Kill old process if running
# Restart
python -m uvicorn main:app --reload
```

**Look for this log on startup:**
```
INFO: Application startup complete.
```

### Step 4: Deploy Merchant with Image

1. **Go to:** `http://localhost:3000/deploy?type=merchant`

2. **Fill in:**
   - Agent Name: "Test Store"
   - Category: Pick one (e.g., TECH)
   - Select some pixels on map

3. **Add Product:**
   - Name: "Test Product"
   - Price: 100
   - Stock: 50
   - Max Discount: 10
   - **Click "📷 Choose Image"**
   - **Select an image** (< 5MB, JPG/PNG)
   - **See preview** ✅

4. **Click "DEPLOY AGENT"**

### Step 5: Check Backend Logs

**You should see:**
```
[INFO] Found image for product 0: test-image.jpg
[INFO] Uploading image to products bucket: images/<agent_id>/product_0.jpg
[INFO] ✓ Image uploaded successfully: https://...
[INFO] ✓ Product 'Test Product' created with 1 image(s)
[INFO] ✓ Successfully inserted 1 products
```

**If you see errors:**
- Check bucket exists
- Check policies are set
- Check SUPABASE_SERVICE_KEY in `.env`

### Step 6: Verify in Supabase

**Storage:**
1. Go to **Storage → products**
2. Navigate to `images/<agent_id>/`
3. You should see `product_0.jpg` ✅
4. Click it → Preview should show your image

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
  "name": "Test Product",
  "images": [
    "https://<project>.supabase.co/storage/v1/object/public/products/images/<agent_id>/product_0.jpg"
  ]
}
```

### Step 7: View in UI

1. Go to **Market** page
2. Find your "Test Store" agent
3. Click **"View Products"**
4. **You should see the product image!** 🎉

---

## 🐛 Troubleshooting

### Issue: No image preview after selecting

**Check:**
- Browser console for errors
- File size (must be < 5MB)
- File type (must be image/*)

**Debug:**
```javascript
// Add this to onChange handler:
console.log('File selected:', file.name, file.size, file.type);
```

### Issue: "Failed to upload product image"

**Backend logs show:**
```
StorageException: Bucket not found
```

**Fix:**
1. Go to Supabase Dashboard → Storage
2. Create `products` bucket (public)
3. Run policies SQL
4. Restart backend

### Issue: "Image URL not saved"

**Check database:**
```sql
SELECT images FROM products WHERE id = '<product_id>';
```

**If empty (`[]`):**
- Check backend logs for upload errors
- Verify `SUPABASE_SERVICE_KEY` in `.env`
- Check storage policies

**If has URL but 404 when opening:**
- Check bucket is public
- Check URL format (should include `/public/`)

### Issue: Image shows in Supabase but not in UI

**Check `ProductsModal.tsx`:**
```typescript
// Make sure it's displaying images from product.images array
{product.images && product.images[0] && (
  <img src={product.images[0]} />
)}
```

---

## 📊 Summary of Changes

| Component | Change |
|-----------|--------|
| **Frontend UI** | ✅ Simplified to single button + preview |
| **Frontend Logic** | ✅ Single `imageFile` per product |
| **Backend Upload** | ✅ New `upload_product_image()` utility |
| **Backend Processing** | ✅ Simple loop: `product_image_0`, `product_image_1`, etc. |
| **Database** | ✅ Already has `images text[]` column |
| **Storage** | ⚠️ Needs `products` bucket + policies |

---

## ✅ Quick Checklist

Before testing:
- [ ] `products` bucket exists in Supabase Storage
- [ ] Storage policies are set (public read, service_role manage)
- [ ] `SUPABASE_SERVICE_KEY` in backend `.env`
- [ ] Backend restarted
- [ ] Frontend running

Test flow:
- [ ] Deploy page loads
- [ ] Can add product
- [ ] Can click "Choose Image"
- [ ] File picker opens
- [ ] Can select image
- [ ] Preview appears
- [ ] Can remove image (✕ button)
- [ ] Can deploy agent
- [ ] Backend logs show upload success
- [ ] Image appears in Supabase Storage
- [ ] Image URL in database
- [ ] Image displays in Market → View Products

---

## 🎉 Expected Result

**Frontend:**
```
┌─────────────────────────┐
│ PRODUCT 1               │
├─────────────────────────┤
│ Name: MacBook Pro       │
│ Price: 1000             │
│                         │
│ [Preview Image]    ✕    │
│                         │
│ 📷 Choose Image         │
│ Max 5MB • JPG, PNG...   │
└─────────────────────────┘
```

**After Deploy:**
- ✅ Image in Supabase Storage: `/products/images/<agent_id>/product_0.jpg`
- ✅ Image URL in database: `products.images = ["https://..."]`
- ✅ Image shows in Market → View Products

**Simple, clean, and working!** 📸✨

