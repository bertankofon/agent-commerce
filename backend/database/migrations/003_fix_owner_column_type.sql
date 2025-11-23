-- Migration: Fix owner column type in agents table
-- The owner field should be TEXT to store wallet addresses or Privy user IDs
-- Not UUID

-- First, check if owner column exists and what type it is
-- If it's UUID, we need to drop and recreate it as TEXT

-- Drop the column if it exists (data will be lost, but this is for development)
ALTER TABLE agents DROP COLUMN IF EXISTS owner;

-- Add owner column as TEXT
ALTER TABLE agents 
ADD COLUMN owner TEXT;

-- Create index for owner lookups
CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner);

-- Add comment
COMMENT ON COLUMN agents.owner IS 'Owner wallet address or Privy user ID (TEXT, not UUID)';

