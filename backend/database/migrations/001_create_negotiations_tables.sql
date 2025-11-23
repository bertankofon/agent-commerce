-- Migration: Create negotiations and agent_chat_history tables
-- Run this script in Supabase SQL Editor

-- ============================================================================
-- 1. NEGOTIATIONS TABLE
-- ============================================================================
-- Stores negotiation sessions between client and merchant agents

CREATE TABLE IF NOT EXISTS negotiations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    client_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    merchant_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,  -- FK to products table (add REFERENCES products(id) ON DELETE CASCADE if products table exists)
    initial_price NUMERIC NOT NULL CHECK (initial_price >= 0),
    final_price NUMERIC CHECK (final_price >= 0),
    negotiation_percentage NUMERIC CHECK (negotiation_percentage >= 0 AND negotiation_percentage <= 100),
    budget NUMERIC CHECK (budget >= 0),
    agreed BOOLEAN DEFAULT false,
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'agreed', 'rejected', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for negotiations table
CREATE INDEX IF NOT EXISTS idx_negotiations_session ON negotiations(session_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_client ON negotiations(client_agent_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_merchant ON negotiations(merchant_agent_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_product ON negotiations(product_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_status ON negotiations(status);
CREATE INDEX IF NOT EXISTS idx_negotiations_created_at ON negotiations(created_at DESC);

-- ============================================================================
-- 2. AGENT_CHAT_HISTORY TABLE
-- ============================================================================
-- Stores individual messages/exchanges during negotiations

CREATE TABLE IF NOT EXISTS agent_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    negotiation_id UUID NOT NULL REFERENCES negotiations(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL CHECK (round_number >= 1 AND round_number <= 5),
    sender_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    receiver_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    proposed_price NUMERIC NOT NULL CHECK (proposed_price >= 0),
    accept BOOLEAN DEFAULT false,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for agent_chat_history table
CREATE INDEX IF NOT EXISTS idx_chat_negotiation ON agent_chat_history(negotiation_id);
CREATE INDEX IF NOT EXISTS idx_chat_sender ON agent_chat_history(sender_agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_receiver ON agent_chat_history(receiver_agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_round ON agent_chat_history(round_number);
CREATE INDEX IF NOT EXISTS idx_chat_negotiation_round ON agent_chat_history(negotiation_id, round_number);
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON agent_chat_history(created_at DESC);

-- ============================================================================
-- 3. TRIGGERS
-- ============================================================================
-- Auto-update updated_at timestamp for negotiations

CREATE OR REPLACE FUNCTION update_negotiations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_negotiations_updated_at
    BEFORE UPDATE ON negotiations
    FOR EACH ROW
    EXECUTE FUNCTION update_negotiations_updated_at();

-- ============================================================================
-- 4. COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE negotiations IS 'Stores negotiation sessions between client and merchant agents for products';
COMMENT ON TABLE agent_chat_history IS 'Stores individual messages/exchanges during negotiations (up to 5 rounds)';

COMMENT ON COLUMN negotiations.session_id IS 'Shopping session ID - links multiple negotiations in one shopping session';
COMMENT ON COLUMN negotiations.negotiation_percentage IS 'Maximum discount percentage merchant can offer (from product)';
COMMENT ON COLUMN negotiations.budget IS 'Client agent budget limit';
COMMENT ON COLUMN negotiations.status IS 'Negotiation status: in_progress, agreed, rejected, failed';

COMMENT ON COLUMN agent_chat_history.round_number IS 'Round number in negotiation (1-5)';
COMMENT ON COLUMN agent_chat_history.proposed_price IS 'Price proposed by sender in this message';
COMMENT ON COLUMN agent_chat_history.accept IS 'Whether this message accepts the current offer';

-- ============================================================================
-- VERIFICATION QUERIES (Optional - can be run to verify tables)
-- ============================================================================

-- Verify tables were created
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('negotiations', 'agent_chat_history');

-- Verify foreign keys
-- SELECT 
--     tc.table_name, 
--     kcu.column_name, 
--     ccu.table_name AS foreign_table_name,
--     ccu.column_name AS foreign_column_name 
-- FROM information_schema.table_constraints AS tc 
-- JOIN information_schema.key_column_usage AS kcu
--   ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage AS ccu
--   ON ccu.constraint_name = tc.constraint_name
-- WHERE tc.constraint_type = 'FOREIGN KEY' 
-- AND tc.table_name IN ('negotiations', 'agent_chat_history');

