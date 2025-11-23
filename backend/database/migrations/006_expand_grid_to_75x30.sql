-- Migration: Expand Grid from 50x20 to 75x30
-- This migration expands the pixel marketplace grid by 1.5x

-- 1. Drop and recreate the pixel_claims table with new dimensions (75x30)
-- We need to drop because we're changing CHECK constraints

-- Backup existing claims (optional, for safety)
CREATE TABLE IF NOT EXISTS pixel_claims_backup AS 
SELECT * FROM pixel_claims;

-- Drop the old table
DROP TABLE IF EXISTS pixel_claims CASCADE;

-- Recreate with new dimensions
CREATE TABLE pixel_claims (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  x INT NOT NULL CHECK (x >= 0 AND x < 75),
  y INT NOT NULL CHECK (y >= 0 AND y < 30),
  claimed_at TIMESTAMP DEFAULT NOW(),
  
  -- Each pixel can only be claimed once (prevents race conditions)
  UNIQUE(x, y)
);

-- Create indexes for fast lookups
CREATE INDEX idx_pixel_claims_agent ON pixel_claims(agent_id);
CREATE INDEX idx_pixel_claims_coords ON pixel_claims(x, y);

-- Restore backed up data (if any exists and fits in new bounds)
INSERT INTO pixel_claims (id, agent_id, x, y, claimed_at)
SELECT id, agent_id, x, y, claimed_at
FROM pixel_claims_backup
WHERE x < 75 AND y < 30
ON CONFLICT (x, y) DO NOTHING;

-- Drop backup table
DROP TABLE IF EXISTS pixel_claims_backup;

-- 2. Update agents table pixel_count constraint
-- Remove old constraint
ALTER TABLE agents 
DROP CONSTRAINT IF EXISTS agents_pixel_count_max_100;

-- Add new constraint for 75x30 = 2250 total pixels, max 150 per agent
ALTER TABLE agents 
ADD CONSTRAINT agents_pixel_count_max_150 CHECK (pixel_count >= 0 AND pixel_count <= 150);

-- Add comment
COMMENT ON TABLE pixel_claims IS 'Pixel marketplace claims on a 75x30 grid (2250 total pixels)';
COMMENT ON COLUMN agents.pixel_count IS 'Number of pixels claimed by this merchant (max 150 for 75x30 grid)';

