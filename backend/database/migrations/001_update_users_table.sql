-- Migration: Update users table to match Privy integration
-- This script updates the users table structure to work with Privy authentication

-- 1. Add privy_user_id column (unique identifier from Privy)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS privy_user_id TEXT UNIQUE;

-- 2. Add email column (from Privy login - email or Google)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email TEXT;

-- 3. Rename wallet_address to ensure consistency (if needed)
-- Already exists, just ensure it's there
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS wallet_address TEXT;

-- 4. Drop unused columns (country, code, surname, address)
-- Note: Only drop if you're sure they're not needed
ALTER TABLE users DROP COLUMN IF EXISTS country;
ALTER TABLE users DROP COLUMN IF EXISTS code;
ALTER TABLE users DROP COLUMN IF EXISTS surname;
ALTER TABLE users DROP COLUMN IF EXISTS address;

-- 5. Create index on privy_user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_privy_user_id ON users(privy_user_id);

-- 6. Create index on wallet_address for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);

-- 7. Add comment to table
COMMENT ON TABLE users IS 'Users table integrated with Privy authentication';

-- 8. Add comments to columns
COMMENT ON COLUMN users.privy_user_id IS 'Unique Privy user ID from authentication';
COMMENT ON COLUMN users.wallet_address IS 'User wallet address from Privy';
COMMENT ON COLUMN users.email IS 'User email from Privy login (email or Google)';
COMMENT ON COLUMN users.name IS 'User name from Privy (Google or other providers)';

-- Final schema should be:
-- users (
--   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--   privy_user_id TEXT UNIQUE NOT NULL,
--   wallet_address TEXT NOT NULL,
--   email TEXT,
--   name TEXT
-- )

