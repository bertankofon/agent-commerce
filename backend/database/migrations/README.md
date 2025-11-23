# Database Migrations

This directory contains SQL migration scripts for creating database tables.

## Migration Files

### `001_create_negotiations_tables.sql`

Creates the tables for storing negotiation history:
- `negotiations` - Negotiation sessions between agents
- `agent_chat_history` - Individual messages during negotiations

## How to Run

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy and paste the contents of `001_create_negotiations_tables.sql`
4. Execute the script

## Tables Created

### negotiations
- Foreign keys to `agents` table (client_agent_id, merchant_agent_id)
- Links to products via `product_id` (add FK constraint if products table exists)

### agent_chat_history
- Foreign key to `negotiations` table (cascade delete)
- Foreign keys to `agents` table (sender_agent_id, receiver_agent_id)

## Notes

- All foreign keys use `ON DELETE CASCADE` to maintain referential integrity
- Indexes are created for efficient querying
- Triggers automatically update `updated_at` timestamp
- Constraints ensure data validity (round_number 1-5, status values, etc.)

