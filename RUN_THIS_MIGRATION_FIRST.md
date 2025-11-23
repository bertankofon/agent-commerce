# 🚨 URGENT: Run This Migration First!

## Error You're Seeing:
```
Could not find the 'category' column of 'agents' in the schema cache
```

## Why?
The `category` column doesn't exist in your Supabase `agents` table yet.

## Solution:
Run the migration SQL in Supabase SQL Editor.

---

## 📝 STEP-BY-STEP:

### 1. Go to Supabase Dashboard
- Open your project
- Click **SQL Editor** in left sidebar
- Click **New Query**

### 2. Copy & Paste This SQL:

```sql
-- Migration: Create Pixel Marketplace System
-- File: 005_create_pixel_marketplace.sql

-- 1. Create pixel_claims table (50x20 grid - wide rectangle)
CREATE TABLE IF NOT EXISTS pixel_claims (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  x INT NOT NULL CHECK (x >= 0 AND x < 50),
  y INT NOT NULL CHECK (y >= 0 AND y < 20),
  claimed_at TIMESTAMP DEFAULT NOW(),
  
  -- Each pixel can only be claimed once
  UNIQUE(x, y)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_pixel_claims_agent ON pixel_claims(agent_id);
CREATE INDEX IF NOT EXISTS idx_pixel_claims_coords ON pixel_claims(x, y);

-- 2. Add category column to agents table
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS category TEXT;

-- Add comment
COMMENT ON COLUMN agents.category IS 'Merchant category: TECH, FASHION, HOME, FOOD, HEALTH';

-- 3. Add pixel_count column to agents table
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS pixel_count INT DEFAULT 0;

-- Add comment
COMMENT ON COLUMN agents.pixel_count IS 'Number of pixels claimed by this merchant (max 100 for 50x20 grid)';

-- Create index for category filtering
CREATE INDEX IF NOT EXISTS idx_agents_category ON agents(category);

-- Add constraint for max pixels (drop first if exists)
ALTER TABLE agents 
DROP CONSTRAINT IF EXISTS agents_pixel_count_max_50;

ALTER TABLE agents 
ADD CONSTRAINT agents_pixel_count_max_100 CHECK (pixel_count >= 0 AND pixel_count <= 100);
```

### 3. Click **Run** (or press Cmd/Ctrl + Enter)

### 4. Verify Success:
Should see: `Success. No rows returned`

---

## ✅ Verification Query:

Run this to confirm columns exist:

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'agents' 
AND column_name IN ('category', 'pixel_count');
```

Should return:
```
category     | text    | NULL
pixel_count  | integer | 0
```

---

## 🔄 After Migration:

Then I'll refactor the app to:
1. Make home page (/) the pixel marketplace
2. Create dashboard for "My Agents"
3. Simplify deployment flow
4. Add smart modals for merchant/client deploy

---

**Run the migration now, then tell me when done!** 🚀

