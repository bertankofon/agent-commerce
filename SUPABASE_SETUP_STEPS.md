# 🗄️ Supabase Products Bucket - Step by Step Setup

## ⚠️ IMPORTANT: 2-Step Process

1. **First:** Create bucket via UI (Dashboard)
2. **Then:** Run SQL for policies

---

## STEP 1: Create Bucket (Dashboard)

### Go to Supabase Dashboard:

1. Open your Supabase project
2. Click **"Storage"** in left sidebar
3. Click **"New bucket"** button
4. Fill in settings:

```
Name: products
Public bucket: ✅ (CHECKED - Very important!)
File size limit: 5242880 (5MB in bytes)
Allowed MIME types: image/* (or leave empty for all)
```

5. Click **"Create bucket"**

**✅ Bucket created!**

---

## STEP 2: Create Policies (SQL Editor)

### Go to SQL Editor:

1. Click **"SQL Editor"** in left sidebar
2. Click **"New query"**
3. Copy and paste this **exact SQL**:

```sql
-- Allow public to read product images
CREATE POLICY IF NOT EXISTS "Public can read products"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'products');

-- Allow service role (backend) to manage all
CREATE POLICY IF NOT EXISTS "Service role can manage products"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'products')
WITH CHECK (bucket_id = 'products');

-- Allow authenticated users to upload
CREATE POLICY IF NOT EXISTS "Authenticated can upload products"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'products');
```

4. Click **"Run"** (or press Ctrl/Cmd + Enter)

**✅ Policies created!**

---

## STEP 3: Verify Setup

### Run this verification query:

```sql
-- Check if bucket exists
SELECT * FROM storage.buckets WHERE name = 'products';
```

**Expected result:**
```
name: products
public: true
```

### Check policies:

```sql
-- Check if policies were created
SELECT * FROM storage.policies WHERE bucket_id = 'products';
```

**Expected result:** Should show 3 policies

---

## STEP 4: Test Upload (Optional)

### Upload a test file via Dashboard:

1. Go to **Storage → products** bucket
2. Click **"Upload file"**
3. Create a folder: `test/`
4. Upload any image
5. Click the image → Copy URL
6. Paste URL in browser → Should show the image ✅

**If image shows → Setup is correct!**

---

## 🐛 Common Errors

### Error: "syntax error at or near 'Name'"

**You tried to run:**
```
Name: products  ← This is NOT SQL!
Public: YES
```

**This is documentation text, not SQL!**

**Fix:** Don't try to create bucket via SQL. Use Dashboard UI instead (Step 1).

---

### Error: "Bucket not found"

**You ran SQL before creating bucket in Dashboard.**

**Fix:**
1. Go to Dashboard → Storage
2. Create `products` bucket (Step 1)
3. Then run SQL (Step 2)

---

### Error: "Policy already exists"

**You already ran the SQL.**

**This is OK!** The `IF NOT EXISTS` clause prevents errors. Your policies are already set up.

---

### Error: "Permission denied" when uploading

**Check:**
1. Is bucket public? (Dashboard → Storage → products → Settings)
2. Are policies created? (Run verification query)
3. Is `SUPABASE_SERVICE_KEY` in backend `.env`?

**Fix:**
```bash
# Check .env file
cat backend/.env | grep SUPABASE_SERVICE_KEY

# Should show:
SUPABASE_SERVICE_KEY=eyJ...your-key...
```

---

## ✅ Final Checklist

Before testing product image upload:

- [x] Bucket `products` created in Dashboard
- [x] Bucket is **public** (checked in settings)
- [x] SQL policies ran successfully
- [x] Verification queries show bucket + policies
- [x] `SUPABASE_URL` in backend `.env`
- [x] `SUPABASE_SERVICE_KEY` in backend `.env`
- [x] Backend restarted

**All done? Test image upload now!** 📸

---

## 🚀 Quick Commands

### Check if bucket exists:
```sql
SELECT name, public FROM storage.buckets WHERE name = 'products';
```

### Check policies:
```sql
SELECT name, bucket_id FROM storage.policies WHERE bucket_id = 'products';
```

### Delete policies (if you need to recreate):
```sql
DROP POLICY IF EXISTS "Public can read products" ON storage.objects;
DROP POLICY IF EXISTS "Service role can manage products" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated can upload products" ON storage.objects;
```

### Delete bucket (⚠️ careful!):
```sql
DELETE FROM storage.buckets WHERE name = 'products';
```

---

## 📝 Summary

**What you need to do:**

1. **Dashboard:** Create `products` bucket (public)
2. **SQL Editor:** Run the 3 CREATE POLICY statements
3. **Verify:** Run SELECT queries to confirm
4. **Test:** Deploy merchant with product image

**That's it!** 🎉

