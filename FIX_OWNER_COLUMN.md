# 🔧 URGENT FIX: Owner Column Type Error

## ❌ Error
```
Internal server error: invalid input syntax for type uuid: "0x21a7AAf3FcE9AE75A8A262F639fE096E90af9F7b"
```

## 🔍 Problem
The `owner` column in Supabase `agents` table is UUID type, but we're trying to store wallet addresses (TEXT).

## ✅ Solution

**Run this SQL in Supabase immediately:**

```sql
-- Drop existing owner column (if it exists)
ALTER TABLE agents DROP COLUMN IF EXISTS owner;

-- Add owner column as TEXT (not UUID)
ALTER TABLE agents 
ADD COLUMN owner TEXT;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner);
```

## 📍 Where to Run

1. Open Supabase Dashboard
2. Go to **SQL Editor**
3. Paste the SQL above
4. Click **Run**

## ✅ After Running SQL

Try deploying an agent again - it should work!

## 📊 Column Types Reference

The `agents` table should have these types:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Auto-generated |
| `owner` | **TEXT** | Wallet address or Privy ID |
| `name` | TEXT | Agent name |
| `agent_type` | TEXT | "merchant" or "client" |
| `status` | TEXT | "live", "paused", or "draft" |
| `public_address` | TEXT | Agent's blockchain address |
| `private_key` | TEXT | Encrypted private key |

---

**Note**: The `owner` field stores:
- Wallet addresses: `0x...` (42 characters)
- Privy user IDs: `did:privy:...`
- Both are TEXT, NOT UUID!

