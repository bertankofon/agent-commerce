-- Migration: Add status column to agents table
-- This enables agent lifecycle management (live, paused, draft)

-- Add status column with default 'live'
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'live';

-- Create index for performance when filtering by status
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Create index for filtering by owner (to get user's agents quickly)
CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner);

-- Add comment
COMMENT ON COLUMN agents.status IS 'Agent status: live, paused, or draft';

-- Valid status values: 'live', 'paused', 'draft'
-- live: Agent is active and visible in market
-- paused: Agent is temporarily disabled
-- draft: Agent is not yet published

