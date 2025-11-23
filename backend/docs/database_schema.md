# Database Schema for Negotiations

This document describes the database tables needed for storing negotiation history and agent chat messages.

## Overview

The negotiation system uses two main tables:
1. **`negotiations`** - Stores negotiation sessions (one per client-merchant-product combination)
2. **`agent_chat_history`** - Stores individual messages/exchanges during negotiations (one per round)

## Tables

### 1. `negotiations` Table

Stores negotiation sessions between client and merchant agents for a specific product.

**Columns:**
- `id` (UUID, PRIMARY KEY) - Unique negotiation ID
- `session_id` (TEXT, NOT NULL) - Shopping session ID (links multiple negotiations in one shopping session)
- `client_agent_id` (UUID, NOT NULL, FK → agents.id) - Client agent participating
- `merchant_agent_id` (UUID, NOT NULL, FK → agents.id) - Merchant agent participating
- `product_id` (UUID, NOT NULL, FK → products.id) - Product being negotiated
- `initial_price` (NUMERIC, NOT NULL) - Initial product price
- `final_price` (NUMERIC, nullable) - Final negotiated price (set when negotiation completes)
- `negotiation_percentage` (NUMERIC, nullable) - Max discount % merchant can offer (from product)
- `budget` (NUMERIC, nullable) - Client's budget limit
- `agreed` (BOOLEAN, default: false) - Whether agreement was reached
- `status` (TEXT, NOT NULL, default: 'in_progress') - Status: "in_progress", "agreed", "rejected", "failed"
- `created_at` (TIMESTAMP, default: now())
- `updated_at` (TIMESTAMP, default: now())

**Indexes:**
- Index on `session_id` - For querying all negotiations in a session
- Index on `client_agent_id` - For querying client's negotiations
- Index on `merchant_agent_id` - For querying merchant's negotiations
- Index on `product_id` - For querying negotiations for a product
- Index on `status` - For filtering by status

**Example Record:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_123",
  "client_agent_id": "client-uuid",
  "merchant_agent_id": "merchant-uuid",
  "product_id": "product-uuid",
  "initial_price": 1000.00,
  "final_price": 870.00,
  "negotiation_percentage": 30.0,
  "budget": 870.00,
  "agreed": true,
  "status": "agreed",
  "created_at": "2025-01-23T00:00:00Z",
  "updated_at": "2025-01-23T00:05:00Z"
}
```

### 2. `agent_chat_history` Table

Stores individual messages/exchanges during negotiations. Each round has 2 messages (client → merchant, merchant → client).

**Columns:**
- `id` (UUID, PRIMARY KEY) - Unique message ID
- `negotiation_id` (UUID, NOT NULL, FK → negotiations.id, ON DELETE CASCADE) - Parent negotiation
- `round_number` (INTEGER, NOT NULL, CHECK 1-5) - Round number (1-5)
- `sender_agent_id` (UUID, NOT NULL, FK → agents.id) - Agent sending message
- `receiver_agent_id` (UUID, NOT NULL, FK → agents.id) - Agent receiving message
- `message` (TEXT, NOT NULL) - The message text from the agent
- `proposed_price` (NUMERIC, NOT NULL) - Price proposed in this message
- `accept` (BOOLEAN, default: false) - Whether this message accepts the offer
- `reason` (TEXT, nullable) - Reason for the decision (from agent)
- `created_at` (TIMESTAMP, default: now())

**Indexes:**
- Index on `negotiation_id` - For querying all messages in a negotiation
- Index on `sender_agent_id` - For querying messages sent by an agent
- Index on `receiver_agent_id` - For querying messages received by an agent
- Index on `round_number` - For filtering by round
- Composite index on (`negotiation_id`, `round_number`) - For efficient round-based queries

**Example Records (Round 1):**
```json
[
  {
    "id": "msg-1",
    "negotiation_id": "550e8400-e29b-41d4-a716-446655440000",
    "round_number": 1,
    "sender_agent_id": "client-uuid",
    "receiver_agent_id": "merchant-uuid",
    "message": "I would like to propose a price of $800.00 for the Playstation 5.",
    "proposed_price": 800.00,
    "accept": false,
    "reason": "The current price exceeds my budget",
    "created_at": "2025-01-23T00:01:00Z"
  },
  {
    "id": "msg-2",
    "negotiation_id": "550e8400-e29b-41d4-a716-446655440000",
    "round_number": 1,
    "sender_agent_id": "merchant-uuid",
    "receiver_agent_id": "client-uuid",
    "message": "I can offer you a price of $900.00, which reflects a 10% discount.",
    "proposed_price": 900.00,
    "accept": false,
    "reason": "Counter-offer to maximize profit",
    "created_at": "2025-01-23T00:02:00Z"
  }
]
```

## SQL Schema

```sql
-- Negotiations table
CREATE TABLE negotiations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    client_agent_id UUID NOT NULL REFERENCES agents(id),
    merchant_agent_id UUID NOT NULL REFERENCES agents(id),
    product_id UUID NOT NULL REFERENCES products(id),
    initial_price NUMERIC NOT NULL,
    final_price NUMERIC,
    negotiation_percentage NUMERIC,
    budget NUMERIC,
    agreed BOOLEAN DEFAULT false,
    status TEXT NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_negotiations_session ON negotiations(session_id);
CREATE INDEX idx_negotiations_client ON negotiations(client_agent_id);
CREATE INDEX idx_negotiations_merchant ON negotiations(merchant_agent_id);
CREATE INDEX idx_negotiations_product ON negotiations(product_id);
CREATE INDEX idx_negotiations_status ON negotiations(status);

-- Agent chat history table
CREATE TABLE agent_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    negotiation_id UUID NOT NULL REFERENCES negotiations(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL CHECK (round_number >= 1 AND round_number <= 5),
    sender_agent_id UUID NOT NULL REFERENCES agents(id),
    receiver_agent_id UUID NOT NULL REFERENCES agents(id),
    message TEXT NOT NULL,
    proposed_price NUMERIC NOT NULL,
    accept BOOLEAN DEFAULT false,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_negotiation ON agent_chat_history(negotiation_id);
CREATE INDEX idx_chat_sender ON agent_chat_history(sender_agent_id);
CREATE INDEX idx_chat_receiver ON agent_chat_history(receiver_agent_id);
CREATE INDEX idx_chat_round ON agent_chat_history(round_number);
CREATE INDEX idx_chat_negotiation_round ON agent_chat_history(negotiation_id, round_number);
```

## Relationships

```
shopping_sessions (session_id)
    ↓
negotiations (one session → many negotiations)
    ↓
agent_chat_history (one negotiation → many messages)
```

## Usage Example

1. Create negotiation when starting negotiation with a merchant
2. Save each chat message as agents exchange messages
3. Update negotiation with final_price and status when complete
4. Query chat_history to retrieve full conversation

