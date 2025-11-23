# Quick Start: A2A Payments with ChaosChain SDK

## ✅ Correct Usage (Production Ready)

### 1. Import the utility function

```python
from utils.chaoschain import get_agent_sdk, execute_x402_payment
from utils.wallet import decrypt_pk
```

### 2. Initialize SDKs for both agents

```python
# Get agent data from database
client_agent = agents_ops.get_agent_by_id(client_agent_id)
merchant_agent = agents_ops.get_agent_by_id(merchant_agent_id)

# Decrypt private keys
client_pk = decrypt_pk(client_agent["private_key"])
merchant_pk = decrypt_pk(merchant_agent["private_key"])

# Initialize SDKs
client_sdk = get_agent_sdk(
    agent_name=client_name,
    agent_domain=client_domain,
    private_key=client_pk,
    agent_role=AgentRole.CLIENT,
    enable_payments=True
)

merchant_sdk = get_agent_sdk(
    agent_name=merchant_name,
    agent_domain=merchant_domain,
    private_key=merchant_pk,
    agent_role=AgentRole.MERCHANT,
    enable_payments=True
)
```

### 3. Execute payment

```python
payment_result = execute_x402_payment(
    client_sdk=client_sdk,
    merchant_sdk=merchant_sdk,
    product_name="Playstation 5",
    final_price=0.35,
    negotiation_id=negotiation_uuid,
    client_name=client_name,
    client_public_address=client_agent["public_address"],
    merchant_public_address=merchant_agent["public_address"]
)

# Check result
if payment_result["status"] == "success":
    print(f"✅ Payment successful!")
    print(f"   TX: {payment_result['transaction_hash']}")
    print(f"   To: {payment_result['settlement_address']}")
else:
    print(f"❌ Payment failed: {payment_result.get('error')}")
```

## 📋 What Happens Behind the Scenes

1. **Merchant creates payment request**
   - Contains correct `settlement_address` (merchant's wallet)
   
2. **Client SDK is monkey-patched**
   - `wallet_manager.get_wallet_address()` patched to recognize merchant's address
   
3. **PaymentManager called directly**
   - Bypasses buggy A2A extension
   - `from_agent=client, to_agent=merchant` explicitly set
   
4. **Payment executed**
   - Protocol fee sent to ChaosChain treasury
   - Main payment sent to merchant
   
5. **On-chain verification**
   - Actual USDC Transfer event checked
   - Confirms recipient is merchant ✅
   
6. **Evidence stored on IPFS**
   - Payment proof
   - Transaction details
   - Negotiation context

## 🚫 What NOT to Do

```python
# ❌ DON'T call SDK's execute_x402_crypto_payment directly
payment_result = client_sdk.execute_x402_crypto_payment(
    payment_request=payment_request,
    payer_agent=client_name,
    service_description="Purchase"
)
# This will send funds to WRONG address due to SDK bug!
```

```python
# ❌ DON'T use merchant SDK to execute payment
payment_result = merchant_sdk.execute_x402_crypto_payment(...)
# Merchant SDK doesn't have client's wallet - will create new empty wallet!
```

## 🔍 Verify Transactions

Check on Base Sepolia block explorer:
```
https://sepolia.basescan.org/tx/{transaction_hash}
```

Look for USDC Transfer event:
- **From:** Client address
- **To:** Merchant address ✅
- **Token:** USDC (0x036CbD53842c5426634e7929541eC2318f3dCF7e)

## 📚 Complete Example

See `scripts/test_negotiation_with_payment.py` for full working example including:
- Agent initialization
- Negotiation flow
- Payment execution
- Error handling
- On-chain verification

## 🛠️ Testing

Run the test script:
```bash
python scripts/test_negotiation_with_payment.py \
  --product-query "Playstation 5" \
  --budget 0.4
```

Expected output:
```
✅ Payment complete!
   FROM: Client_xxx (0x5363...)
   TO:   Merchant_xxx (0xF8e8...)
   TX:   0x9064...
   ✅ Recipient verified: 0xF8e8... (matches merchant)
```

## 📖 More Information

- **Full implementation:** `utils/chaoschain.py` - `execute_x402_payment()`
- **Complete documentation:** `docs/PAYMENT_FIX_SUMMARY.md`
- **API usage:** `routes/negotiation/routes.py` - `/negotiate-and-pay` endpoint
- **ChaosChain docs:** https://docs.chaoscha.in/sdk/quickstart

## 💡 Key Points

1. ✅ Always use `execute_x402_payment()` utility function
2. ✅ Merchant creates payment request
3. ✅ Client SDK executes (has payer's wallet)
4. ✅ Verify on-chain (don't trust SDK response alone)
5. ❌ Never call `sdk.execute_x402_crypto_payment()` directly

