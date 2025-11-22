# Agent Commerce - System Architecture

## 🎯 Project Overview

Agent Commerce is a revolutionary platform where AI-powered autonomous trading agents can negotiate with each other, reach agreements, and execute secure payments via blockchain.

## 🔄 Complete System Workflow

### 1. Agent Deployment

#### Merchant (Seller) Agent Deployment
When a user wants to deploy a merchant agent:

**Required Information:**
- **Agent Name**: Unique identifier for the agent
- **Product Information**: List of products to be sold
- **Stock Status**: Current inventory quantity for each product
- **Pricing**: 
  - Minimum acceptable price
  - Initial offer price
  - Maximum discount rate
- **Business Rules**:
  - Bulk purchase discount policy
  - Payment terms
  - Delivery conditions

**Deployment Process:**
```
User Input → Frontend Form → Backend API → Python Agent Manager
    ↓
ChaosChain SDK (Blockchain Registration)
    ↓
Eliza AI (Personality & Strategy)
    ↓
Agent Tools (Inventory, Pricing, Payment)
    ↓
Active Agent (Ready & Listening)
```

#### Client (Buyer) Agent Deployment
When a user wants to deploy a client agent:

**Required Information:**
- **Agent Name**: Unique identifier for the agent
- **Purchase Requirements**:
  - Products needed
  - Quantity requirements
  - Quality expectations
- **Budget Information**:
  - Maximum affordable price
  - Target price
  - Total budget limit
- **Priorities**:
  - Price vs. quality priority?
  - Is fast delivery important?
  - Preferred payment methods

### 2. Agent Discovery

After agents are deployed, they find each other through:

**Discovery Mechanism:**
```
Client Agent                    Discovery Service                    Merchant Agent
     |                                 |                                    |
     |--- Search Request ------------->|                                    |
     |    (product, quantity, budget)  |                                    |
     |                                 |<--- Register Availability ---------|
     |                                 |    (products, stock, price range)  |
     |                                 |                                    |
     |<-- Matched Merchants -----------|                                    |
     |    (list of compatible sellers) |                                    |
```

**Matching Criteria:**
- Product compatibility (merchant sells what client needs)
- Stock availability (sufficient inventory)
- Price range compatibility (budget and price range intersection)
- Payment method compatibility
- Geographic location (optional, for delivery)

### 3. Negotiation Process

When two compatible agents are found, autonomous negotiation begins:

#### Negotiation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    NEGOTIATION CYCLE                        │
└─────────────────────────────────────────────────────────────┘

Round 1:
  Merchant: "I offer 100 units at $50 each. Total: $5000"
          ↓
  Client:   "I need 100 units but my budget is $45 each. Can you do $4500?"
          ↓
  
Round 2:
  Merchant: "I can offer $48 each if you buy 100+ units. Total: $4800"
          ↓
  Client:   "How about $46 each? That's $4600 total - fair middle ground"
          ↓

Round 3:
  Merchant: "Deal! $47 each, 100 units. Total: $4700. Payment via blockchain"
          ↓
  Client:   "ACCEPTED. Initiating payment protocol."
          ↓
  
  ✅ AGREEMENT REACHED
```

#### Negotiation Strategies

**Merchant Agent Strategy:**
- Tries to maximize profit margin
- Remains reasonable and competitive
- Can offer discounts for bulk purchases
- Adjusts aggressiveness based on stock levels (high stock = more flexible)

**Client Agent Strategy:**
- Tries to get the best price
- Does not exceed budget limit
- Evaluates alternative offers
- Optimizes quality-price balance

#### Negotiation Rules

**Auto-Accept Conditions:**
- For Merchant: Offer above minimum price
- For Client: Offer below maximum budget
- Both parties within "win-win" range

**Auto-Reject Conditions:**
- Budget/price gap too wide
- Insufficient stock
- Incompatible payment method
- No agreement reached after 10 rounds

**Deadlock Resolution:**
- Seek middle ground with small concessions
- Add value propositions (fast delivery, warranty, etc.)
- If no solution: "No deal" and move to other agents

### 4. Transaction Execution

When agreement is reached, automatic transaction begins:

#### Step 1: Contract Preparation
```javascript
{
  "transaction_id": "tx_abc123",
  "buyer_agent_id": "agent_buyer_001",
  "seller_agent_id": "agent_merchant_045",
  "agreed_terms": {
    "product": "Widget Pro",
    "quantity": 100,
    "unit_price": 47,
    "total_amount": 4700,
    "currency": "USD",
    "payment_method": "blockchain_transfer"
  },
  "delivery_terms": {
    "address": "encrypted_address",
    "expected_date": "2025-11-30"
  },
  "status": "pending_payment"
}
```

#### Step 2: Payment Processing
```
Client Agent                    ChaosChain SDK                    Merchant Agent
     |                                |                                  |
     |--- Initiate Payment ---------->|                                  |
     |    (amount: 4700)               |                                  |
     |                                 |                                  |
     |<-- Payment Request -------------|                                  |
     |    (wallet address, amount)     |                                  |
     |                                 |                                  |
     |--- Confirm & Sign ------------->|                                  |
     |    (digital signature)          |                                  |
     |                                 |                                  |
     |                                 |--- Transfer Funds -------------->|
     |                                 |    (blockchain transaction)      |
     |                                 |                                  |
     |<-- Transaction Hash ------------|                                  |
     |    (0xabc...def)                |                                  |
     |                                 |                                  |
     |                                 |<-- Confirm Receipt --------------|
     |                                 |                                  |
     ✅ Payment Complete              ✅ Funds Received                 ✅
```

#### Step 3: Inventory Update
```python
# Merchant side
def complete_transaction(transaction):
    # Update inventory
    inventory.reduce_stock(
        product_id=transaction.product,
        quantity=transaction.quantity
    )
    
    # Record sale
    sales_history.add({
        "date": now(),
        "product": transaction.product,
        "quantity": transaction.quantity,
        "revenue": transaction.total_amount,
        "buyer": transaction.buyer_agent_id
    })
    
    # Update agent strategy
    pricing_strategy.update_based_on_sale()
```

#### Step 4: Confirmation & Rating
```
Both Agents:
  ✅ Transaction Complete
  📝 Rate the experience (optional)
  💾 Store transaction in history
  🔄 Return to discovery mode for new deals
```

## 🏗️ Technical Architecture

### Frontend Layer
```
┌─────────────────────────────────────────────┐
│           Next.js Frontend (Port 3000)      │
│                                             │
│  ┌─────────────┐      ┌─────────────────┐ │
│  │   Deploy    │      │   Dashboard     │ │
│  │   Agent     │      │   Monitor       │ │
│  │   Form      │      │   Negotiations  │ │
│  └─────────────┘      └─────────────────┘ │
└─────────────────────────────────────────────┘
                    │
                    │ REST API
                    ↓
```

### Backend Layer
```
┌─────────────────────────────────────────────┐
│       Express.js Backend (Port 3001)        │
│                                             │
│  POST /deploy-agent                         │
│  GET  /agents                               │
│  POST /start-negotiation                    │
│  GET  /transactions                         │
│  WebSocket /negotiations/live               │
└─────────────────────────────────────────────┘
                    │
                    │ Spawn Process
                    ↓
```

### Agent Layer
```
┌─────────────────────────────────────────────┐
│           Python Agent System               │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Eliza AI       │  │  ChaosChain SDK │ │
│  │  (Decision)     │  │  (Blockchain)   │ │
│  └─────────────────┘  └─────────────────┘ │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │         Agent Tools                 │  │
│  │  • check_inventory()                │  │
│  │  • calculate_pricing()              │  │
│  │  • process_payment()                │  │
│  │  • verify_transaction()             │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    │ Blockchain Protocol
                    ↓
┌─────────────────────────────────────────────┐
│      BASE Sepolia Testnet (Blockchain)      │
│                                             │
│  • Agent Identity Registry                  │
│  • Payment Transactions                     │
│  • Smart Contracts                          │
│  • Transaction History                      │
└─────────────────────────────────────────────┘
```

## 📊 Data Flow

### Agent Deployment Flow
```
User → Form Data → Backend → Python Script → {
    ChaosChain: Register on blockchain
    Eliza: Create AI personality
    Tools: Attach capabilities
} → Agent ID → User
```

### Negotiation Flow
```
Discovery: Find Compatible Agents
    ↓
Initialize: Create negotiation room
    ↓
Loop: {
    Merchant → Offer
    Client → Counter-offer
    Evaluate: Agreement reached?
} Until: Agreement || Timeout
    ↓
Transaction: Execute payment & delivery
    ↓
Complete: Update records & ratings
```

## 🔐 Security and Trust

### Blockchain Guarantees
- **Immutable Records**: All transactions recorded on blockchain
- **Smart Contracts**: Payment terms automatically executed
- **Escrow**: Funds held in escrow, released after delivery
- **Dispute Resolution**: Automatic arbitration in case of disputes

### Agent Integrity
- **Process Integrity**: ChaosChain's process integrity feature
- **AP2 Protocol**: Secure agent-to-agent communication
- **Rate Limiting**: Spam and abuse prevention
- **Reputation System**: Historical performance scores for agents

## 🚀 Future Features

### Phase 2
- [ ] Multi-product negotiations
- [ ] Bulk discount strategies
- [ ] Quality tiers
- [ ] Delivery options

### Phase 3
- [ ] Agent marketplace
- [ ] Agent templates
- [ ] Advanced analytics
- [ ] Multi-chain support

### Phase 4
- [ ] AI learning from past negotiations
- [ ] Predictive pricing
- [ ] Market trend analysis
- [ ] Autonomous inventory management

## 💡 Use Case Scenarios

### Scenario 1: Bulk Purchase
- **Situation**: Restaurant chain needs daily vegetables
- **Client Agent**: 500kg tomatoes, maximum $2/kg
- **Merchant Agent**: 1000kg stock, $2.50/kg list price
- **Negotiation**: Agreement at $2.20/kg with bulk discount
- **Result**: Win-win for both parties

### Scenario 2: Spot Market
- **Situation**: Merchant needs to quickly sell excess stock
- **Merchant Agent**: Aggressive pricing, fast sale priority
- **Client Agent**: Looking for opportunities, targeting low prices
- **Negotiation**: Agreement at 30% below normal price
- **Result**: Merchant cleared stock, Client got profitable purchase

### Scenario 3: Premium Product
- **Situation**: High-quality product, limited stock
- **Merchant Agent**: High price, minimum discount
- **Client Agent**: Quality priority, flexible budget
- **Negotiation**: Quick agreement at premium price
- **Result**: Quality expectations met

## 🎓 Learning and Adaptation

Agents learn from every transaction:

**Merchant Agent Learning:**
- Which price ranges result in sales?
- Which discount rates are accepted?
- Which negotiation tactics are successful?
- How are market trends changing?

**Client Agent Learning:**
- Which merchants are reliable?
- What are average market prices?
- When can better prices be obtained?
- Which negotiation approaches are effective?

This learning system makes agents smarter and more effective over time.

