# Supabase Database Changes Required

## 🎯 Quick Start - What You Need to Do in Supabase

### 1️⃣ Update `users` Table

Go to **Supabase Dashboard → SQL Editor** and run this SQL:

```sql
-- Add privy_user_id column (unique identifier from Privy)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS privy_user_id TEXT UNIQUE;

-- Add email column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email TEXT;

-- Ensure wallet_address exists
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS wallet_address TEXT;

-- Drop unused columns
ALTER TABLE users DROP COLUMN IF EXISTS country;
ALTER TABLE users DROP COLUMN IF EXISTS code;
ALTER TABLE users DROP COLUMN IF EXISTS surname;
ALTER TABLE users DROP COLUMN IF EXISTS address;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_privy_user_id ON users(privy_user_id);
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);
```

### ✅ Final `users` Table Schema

After migration, your table should have these columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `created_at` | TIMESTAMP | Creation time (auto-generated) |
| `privy_user_id` | TEXT (UNIQUE) | Privy user ID |
| `wallet_address` | TEXT | User's wallet address |
| `user_type` | TEXT | "merchant" or "client" |
| `email` | TEXT | User's email (optional) |
| `name` | TEXT | User's name (optional) |

## 📋 Verification Checklist

After running the migration, verify:

- [ ] `privy_user_id` column exists and has UNIQUE constraint
- [ ] `email` column exists
- [ ] `wallet_address` column exists
- [ ] Unused columns (`country`, `code`, `surname`, `address`) are removed
- [ ] Indexes are created on `privy_user_id` and `wallet_address`

## 🧪 Test the Integration

### 1. Start Backend Server

```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
python main.py
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

### 3. Test User Flow

1. Go to `http://localhost:3000`
2. Click **"CONNECT WALLET"**
3. Complete Privy authentication
4. Check Supabase `users` table - you should see a new row with:
   - ✅ `privy_user_id` populated
   - ✅ `wallet_address` populated
   - ✅ `user_type` = "merchant"
   - ✅ `email` (if you logged in with email/Google)
   - ✅ `name` (if you logged in with Google)

### 4. Test Agent Deployment

1. Click **"DEPLOY AGENT"**
2. Fill in agent details
3. Deploy agent
4. Check Supabase `agents` table:
   - ✅ `owner` field should be populated with user's wallet address

## 🔍 Troubleshooting

### Issue: Migration fails with "column already exists"

**Solution:** The migration script uses `IF NOT EXISTS` - it should be safe. If it still fails, check which columns already exist and remove those lines from the migration.

### Issue: User registration fails

**Solution:** Check:
1. Backend logs for errors
2. Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set in `.env`
3. Verify the `privy_user_id` column exists in Supabase

### Issue: Old users without privy_user_id

**Solution:** Old users will continue to work. When they log in with Privy, a new user record will be created with `privy_user_id`. You can manually link old users if needed.

## 📊 Example Data

After successful integration, your `users` table might look like:

```json
[
  {
    "id": "uuid-1",
    "created_at": "2025-11-23T10:00:00Z",
    "privy_user_id": "did:privy:clp...",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "user_type": "merchant",
    "email": "john@example.com",
    "name": "John Doe"
  },
  {
    "id": "uuid-2",
    "created_at": "2025-11-23T11:00:00Z",
    "privy_user_id": "did:privy:abc...",
    "wallet_address": "0x6B9506F9FD5caa811961EDECb0a8B5D35A5E6c42",
    "user_type": "client",
    "email": "alice@example.com",
    "name": null
  }
]
```

## 🎉 Done!

Your users table is now integrated with Privy authentication! Users will be automatically created when they log in, and all agent deployments will be linked to the correct user.

