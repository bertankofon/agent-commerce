# Grid Expansion Migration (50x20 → 75x30)

## What This Does

This migration expands the pixel marketplace grid from **50x20** (1,000 pixels) to **75x30** (2,250 pixels) - a 1.5x increase in both dimensions.

## Changes Made

### Database (Migration 006)
- ✅ Updated `pixel_claims` table constraints (x < 75, y < 30)
- ✅ Added `UNIQUE(x, y)` constraint for race condition prevention
- ✅ Updated `agents.pixel_count` max limit (100 → 150)
- ✅ Preserved existing pixel claims during migration

### Backend
- ✅ Updated `backend/database/supabase/operations/pixels.py`
  - Grid bounds validation: 75x30
  - Max pixels per agent: 150
  - Total marketplace pixels: 2,250
  - Race condition protection in `claim_pixels()`
- ✅ Updated `backend/routes/market/routes.py` documentation

### Frontend
- ✅ Updated `frontend/app/components/PixelGrid.tsx`
  - Default gridWidth: 75, gridHeight: 30
  - Changed from square grid to rectangular grid
- ✅ Updated `frontend/app/components/PixelSelector.tsx`
  - Default gridWidth: 75, gridHeight: 30
  - Max pixels: 150
- ✅ Updated `frontend/app/market/page.tsx`
  - Grid display: 75x30
  - Grid template columns: repeat(75, 20px)

## Race Condition Prevention

The migration adds `UNIQUE(x, y)` constraint on `pixel_claims` table, ensuring that:
1. Two agents cannot claim the same pixel simultaneously
2. Database-level protection against race conditions
3. Insert will fail if pixel already exists (handled gracefully in backend)

## Run Migration

```bash
# Connect to Supabase
psql $DATABASE_URL

# Or use Supabase Dashboard SQL Editor
```

Copy and paste the contents of:
```
backend/database/migrations/006_expand_grid_to_75x30.sql
```

## Verify Migration

```bash
# Check table structure
\d pixel_claims

# Check constraint
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'pixel_claims'::regclass;

# Check existing data
SELECT COUNT(*), MAX(x), MAX(y) FROM pixel_claims;
```

## Testing

1. **Test pixel claiming** - Try to claim pixels at various positions
2. **Test boundaries** - Try claiming pixels at (74, 29) - should work
3. **Test beyond boundaries** - Try claiming pixels at (75, 30) - should fail
4. **Test race conditions** - Try claiming same pixel twice simultaneously
5. **Test max limit** - Try claiming more than 150 pixels for one agent

## Rollback (If Needed)

If you need to revert:

```sql
-- Restore from backup
DROP TABLE pixel_claims;
ALTER TABLE pixel_claims_backup RENAME TO pixel_claims;

-- Restore old constraint
ALTER TABLE agents DROP CONSTRAINT agents_pixel_count_max_150;
ALTER TABLE agents ADD CONSTRAINT agents_pixel_count_max_100 
  CHECK (pixel_count >= 0 AND pixel_count <= 100);
```

