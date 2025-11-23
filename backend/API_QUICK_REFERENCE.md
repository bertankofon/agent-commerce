# Agent Commerce API - Quick Reference

## 🎯 Negotiation Endpoints

### 1. Multi-Product Search & Negotiate
**Endpoint:** `POST /negotiation/negotiate-and-pay`

Find best deal across multiple products and merchants.

```bash
curl -X POST http://localhost:8000/negotiation/negotiate-and-pay \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "client-uuid",
    "product_query": "Playstation 5",
    "budget": 500.0,
    "rounds": 5
  }'
```

**Use Case:** Client searches for product, system negotiates with all merchants, selects best offer, executes payment.

---

### 2. Direct Agent-to-Agent Negotiation ⭐ NEW
**Endpoint:** `POST /negotiation/single-negotiation`

Direct negotiation between specific client and merchant.

```bash
curl -X POST http://localhost:8000/negotiation/single-negotiation \
  -H "Content-Type: application/json" \
  -d '{
    "client_agent_id": "client-uuid",
    "merchant_agent_id": "merchant-uuid",
    "product_id": "product-uuid",
    "budget": 0.50,
    "rounds": 5
  }'
```

**Use Case:** Direct deal between known parties for specific product.

---

## 📋 Request Parameters

### `/negotiate-and-pay`
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | ✅ | Client agent UUID |
| `product_query` | string | ✅ | Product search query |
| `budget` | float | ❌ | Max budget (default: 870) |
| `rounds` | int | ❌ | Negotiation rounds (default: 5) |
| `dry_run` | bool | ❌ | Skip payment (default: false) |

### `/single-negotiation`
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_agent_id` | string | ✅ | Client UUID |
| `merchant_agent_id` | string | ✅ | Merchant UUID |
| `product_id` | string | ✅ | Product UUID |
| `budget` | float | ✅ | Max budget |
| `rounds` | int | ❌ | Rounds (default: 5) |
| `dry_run` | bool | ❌ | Skip payment (default: false) |

---

## 📤 Response Format

### Successful Negotiation + Payment

```json
{
  "status": "completed_with_payment",
  "client_agent_id": "uuid",
  "merchant_agent_id": "uuid",
  "product_name": "Playstation 5",
  "initial_price": 0.50,
  "final_price": 0.35,
  "agreed": true,
  "payment_result": {
    "status": "success",
    "transaction_hash": "0x123...",
    "settlement_address": "0xabc...",
    "amount_paid": 0.35,
    "protocol_fee": 0.00875,
    "evidence_cid": "Qm...",
    "cart_id": "cart_..."
  }
}
```

### Failed Negotiation

```json
{
  "status": "negotiation_failed",
  "agreed": false,
  "final_price": 1000.00,
  "error": "No agreement reached"
}
```

---

## 🚀 Quick Start

### 1. Start Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Test Multi-Product Search

```bash
python scripts/test_negotiation_with_payment.py \
  --product-query "Playstation 5" \
  --budget 0.5
```

### 3. Test Direct Negotiation

```bash
python scripts/test_single_negotiation.py \
  --budget 0.5
```

---

## 🔐 Authentication

Currently: **No authentication required** (development mode)

Future: Will require API key or JWT token.

---

## 💳 Payment System

### ChaosChain x402 Payments

- **Network:** Base Sepolia (testnet)
- **Currency:** USDC
- **Protocol:** x402 (W3C standard)
- **Settlement:** On-chain (verifiable)

### Requirements

- ✅ Client wallet: USDC balance + ETH for gas
- ✅ Merchant wallet: ETH for gas
- ✅ Both agents: Encrypted private keys in database

### Verification

Check transaction on blockchain:
```
https://sepolia.basescan.org/tx/{transaction_hash}
```

Look for USDC Transfer event:
- **From:** Client address
- **To:** Merchant address ✅

---

## 📊 Response Status Codes

| Status | Description |
|--------|-------------|
| `completed_with_payment` | Deal made + payment successful |
| `completed` | Generic success |
| `negotiation_success_payment_failed` | Deal made but payment failed |
| `negotiation_success_over_budget` | Deal made but exceeds budget |
| `negotiation_success_dry_run` | Dry run mode (no payment) |
| `negotiation_failed` | No agreement reached |
| `error` | System error occurred |

---

## 🔧 Environment Setup

Required environment variables:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI (for agent intelligence)
OPENAI_API_KEY=sk-...

# Encryption (for private keys)
USER_SECRET_KEY=your-32-byte-hex-key
```

---

## 📚 Full Documentation

- **Single Negotiation:** `docs/SINGLE_NEGOTIATION_ENDPOINT.md`
- **Payment Fix:** `docs/PAYMENT_FIX_SUMMARY.md`
- **Quick Start:** `docs/QUICK_START_PAYMENTS.md`
- **ChaosChain SDK:** `docs/chaoschain_a2a_payments.md`
- **Complete Update:** `PAYMENT_UPDATE_SUMMARY.md`

---

## ⚡ Examples

### Python

```python
import requests

# Single negotiation
response = requests.post(
    "http://localhost:8000/negotiation/single-negotiation",
    json={
        "client_agent_id": "uuid1",
        "merchant_agent_id": "uuid2",
        "product_id": "uuid3",
        "budget": 0.50
    }
)

result = response.json()
if result["status"] == "completed_with_payment":
    print(f"✅ Deal made! TX: {result['payment_result']['transaction_hash']}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/negotiation/single-negotiation', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_agent_id: 'uuid1',
    merchant_agent_id: 'uuid2',
    product_id: 'uuid3',
    budget: 0.50
  })
});

const result = await response.json();
if (result.status === 'completed_with_payment') {
  console.log('✅ Deal made! TX:', result.payment_result.transaction_hash);
}
```

### cURL

```bash
# Multi-product search
curl -X POST http://localhost:8000/negotiation/negotiate-and-pay \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"uuid","product_query":"Xbox","budget":300}'

# Direct negotiation
curl -X POST http://localhost:8000/negotiation/single-negotiation \
  -H "Content-Type: application/json" \
  -d '{"client_agent_id":"uuid1","merchant_agent_id":"uuid2","product_id":"uuid3","budget":0.5}'
```

---

## 🐛 Debugging

### Check Logs

```bash
# View negotiation logs
tail -f backend/logs/negotiation.log

# View payment logs  
tail -f backend/logs/payment.log
```

### Common Issues

**"Insufficient USDC balance"**
- Top up client wallet with testnet USDC
- Get from: https://faucet.circle.com/

**"Agent not found"**
- Verify agent UUID exists in `agents` table
- Check agent has `private_key` and `public_address`

**"Product does not belong to merchant"**
- Verify `products.agent_id` matches `merchant_agent_id`

---

**Last Updated:** November 23, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready

