# Negotiation Storage Summary

## Overview

The system now saves all negotiation steps to Supabase database for complete audit trail and history.

## Database Tables

### 1. `negotiations` Table
- **Purpose**: Stores negotiation sessions between client and merchant agents
- **One record per**: Client-Merchant-Product combination in a shopping session
- **Contains**: Initial price, final price, budget, status, agreement status

### 2. `agent_chat_history` Table  
- **Purpose**: Stores every message/exchange during negotiations
- **One record per**: Each message sent (client or merchant)
- **Contains**: Message text, proposed price, accept flag, reason, round number

## Data Flow

```
Shopping Session (session_id)
    ↓
For each merchant:
    ↓
Create negotiation record (status: "in_progress")
    ↓
For each round (1-5):
    ├─ Client sends message → Save to agent_chat_history
    └─ Merchant sends message → Save to agent_chat_history
    ↓
Update negotiation record (final_price, agreed, status: "agreed"/"failed")
```

## What Gets Saved

### Negotiation Record
- Created when negotiation starts with a merchant
- Updated when negotiation completes with:
  - `final_price`: Final negotiated price
  - `agreed`: Whether agreement reached
  - `status`: "agreed", "failed", "rejected", or "in_progress"

### Chat History Records
- Every message from client agent (5 rounds max)
- Every message from merchant agent (5 rounds max)
- Each message includes:
  - Round number (1-5)
  - Sender and receiver agent IDs
  - Message text
  - Proposed price
  - Accept flag
  - Reason (if provided)

## Querying Data

### Get all negotiations for a session:
```python
negotiations = negotiations_ops.get_negotiations_by_session(session_id)
```

### Get full conversation for a negotiation:
```python
chat_history = chat_history_ops.get_chat_history_by_negotiation(negotiation_id)
```

### Get all chat messages for a session:
```python
chat_history = chat_history_ops.get_chat_history_by_session(session_id)
```

## Integration

The `ShoppingService` automatically:
1. Creates negotiation record when starting negotiation with each merchant
2. Saves each chat message as agents exchange messages
3. Updates negotiation record with final results when complete

No additional code needed - it's all handled automatically!

