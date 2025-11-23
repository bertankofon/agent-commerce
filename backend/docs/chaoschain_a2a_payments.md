# ChaosChain A2A Payments & x402 Integration Guide

This document explains how to implement Agent-to-Agent (A2A) deals using ChaosChain's x402 payment protocol, based on the [ChaosChain SDK Quickstart](https://docs.chaoscha.in/sdk/quickstart).

## ⚠️ IMPORTANT: Correct A2A Payment Implementation

**SDK Issue Discovered:** The ChaosChain SDK's `execute_x402_crypto_payment` method has a design flaw where calling it on an SDK instance uses `self.agent_name` as the recipient, not the `payment_request.settlement_address`.

**Our Solution (Implemented in `utils/chaoschain.py`):**
1. Merchant SDK creates `x402_payment_request` (contains correct merchant settlement_address)
2. Client SDK's `wallet_manager` is monkey-patched to recognize merchant's address
3. Client SDK's `PaymentManager` is called directly (bypassing buggy A2A extension)
4. Result: Correct flow `from_agent=client → to_agent=merchant` ✅

**Working Code:** See `execute_x402_payment()` in `utils/chaoschain.py` for full implementation.

**Do NOT use:** `sdk.execute_x402_crypto_payment()` directly - it will send funds to wrong address!

---

## Overview

ChaosChain enables agents to:
1. **Register on-chain identities** (ERC-8004)
2. **Execute verifiable work** with process integrity proofs
3. **Make crypto payments** to each other using x402 protocol (A2A-x402)
4. **Store evidence** on IPFS for auditability

## Agent Architecture

### 1. Agent Registration (ERC-8004)

Agents must be registered on-chain to participate in the network:

```python
from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole

# Initialize SDK
sdk = ChaosChainAgentSDK(
    agent_name="MyAgent",
    agent_domain="myagent.example.com",
    agent_role=AgentRole.SERVER,  # or CLIENT, MERCHANT, etc.
    network=NetworkConfig.BASE_SEPOLIA,
    enable_payments=True,  # Required for x402
    enable_process_integrity=True,
    enable_ap2=True
)

# Register agent identity on-chain
agent_id, tx_hash = sdk.register_identity()
print(f"Agent registered with ID: {agent_id}")
```

**Key Points:**
- Each agent gets a unique `agent_id` (on-chain identifier)
- Agents need funded wallets (ETH for gas fees)
- Registration creates an ERC-8004 identity that can be discovered by other agents

### 2. Agent Roles

- **SERVER**: Service provider (merchant)
- **CLIENT**: Service consumer (buyer)
- **MERCHANT**: Sells products/services
- **VALIDATOR**: Validates other agents' work
- **WORKER**: Executes tasks
- **VERIFIER**: Verifies integrity proofs
- **ORCHESTRATOR**: Coordinates multiple agents

## A2A Payments with x402 Protocol

### What is x402?

x402 is a W3C-compliant payment protocol for Agent-to-Agent transactions. It enables:
- **Direct crypto payments** between agents (USDC on Base Sepolia)
- **Automated settlement** without intermediaries
- **On-chain verification** of payments
- **Protocol fees** handled automatically

### Payment Flow

#### Step 1: Create Payment Request

The **merchant agent** (seller) creates a payment request:

```python
# Merchant agent creates payment request
x402_request = sdk.create_x402_payment_request(
    cart_id="payment_cart_456",
    total_amount=25.99,  # Amount in USDC
    currency="USDC",
    items=[
        {
            "name": "AI Analysis Service",
            "price": 25.99
        }
    ]
)

print(f"Payment Request ID: {x402_request.request_id}")
print(f"Cart ID: {x402_request.cart_id}")
print(f"Total Amount: {x402_request.total_amount} {x402_request.currency}")
```

#### Step 2: Execute Payment

The **client agent** (buyer) executes the payment:

```python
# Client agent executes payment
crypto_payment = sdk.execute_x402_crypto_payment(
    payment_request=x402_request,
    payer_agent="ClientAgent",  # Name of paying agent
    service_description="AI Analysis Service"
)

print(f"Transaction Hash: {crypto_payment.transaction_hash}")
print(f"Settlement Address: {crypto_payment.settlement_address}")
print(f"Protocol Fee: ${crypto_payment.protocol_fee}")
print(f"Amount Paid: ${crypto_payment.amount_paid}")
```

**What Happens:**
1. Client agent's wallet sends USDC to merchant's settlement address
2. Protocol fee is automatically deducted
3. Transaction is recorded on-chain (Base Sepolia)
4. Both agents receive transaction confirmation

### Complete A2A Deal Example

Here's a complete flow for a negotiation-based purchase:

```python
from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole
import asyncio

async def execute_a2a_deal():
    # ===== MERCHANT AGENT (Seller) =====
    merchant_sdk = ChaosChainAgentSDK(
        agent_name="MerchantAgent",
        agent_domain="merchant.example.com",
        agent_role=AgentRole.MERCHANT,
        network=NetworkConfig.BASE_SEPOLIA,
        enable_payments=True,
        wallet_file="merchant_wallet.json"  # Merchant's wallet
    )
    
    # Merchant creates payment request after negotiation
    negotiated_price = 25.99  # From negotiation
    payment_request = merchant_sdk.create_x402_payment_request(
        cart_id=f"cart_{uuid.uuid4()}",
        total_amount=negotiated_price,
        currency="USDC",
        items=[{
            "name": "Playstation 5",
            "price": negotiated_price
        }]
    )
    
    # ===== CLIENT AGENT (Buyer) =====
    client_sdk = ChaosChainAgentSDK(
        agent_name="ClientAgent",
        agent_domain="client.example.com",
        agent_role=AgentRole.CLIENT,
        network=NetworkConfig.BASE_SEPOLIA,
        enable_payments=True,
        wallet_file="client_wallet.json"  # Client's wallet
    )
    
    # Client executes payment
    payment_result = client_sdk.execute_x402_crypto_payment(
        payment_request=payment_request,
        payer_agent="ClientAgent",
        service_description="Playstation 5 Purchase"
    )
    
    # ===== STORE EVIDENCE =====
    # Both agents can store evidence of the transaction
    evidence = {
        "payment_request": payment_request.__dict__,
        "payment_result": payment_result.__dict__,
        "negotiation_id": "negotiation_123",
        "product": "Playstation 5",
        "final_price": negotiated_price
    }
    
    evidence_cid = merchant_sdk.store_evidence(evidence)
    print(f"Evidence stored on IPFS: {evidence_cid}")
    
    return payment_result

# Run the deal
result = asyncio.run(execute_a2a_deal())
```

## Integration with Your Negotiation System

### Current Flow (Without Payments)

1. **Product Search** → Find products via Supabase
2. **Negotiation** → Agents negotiate price
3. **Offer Selection** → Client selects best offer
4. **❌ Payment Missing** → No actual money transfer

### Enhanced Flow (With x402 Payments)

1. **Product Search** → Find products via Supabase
2. **Negotiation** → Agents negotiate price
3. **Offer Selection** → Client selects best offer
4. **✅ Payment Execution** → Client pays merchant via x402
5. **Evidence Storage** → Store transaction proof on IPFS

### Implementation Steps

#### 1. Initialize SDK for Each Agent

```python
# In your agent creation/initialization
from utils.chaoschain import create_chaoschain_agent
from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole
import json
import tempfile

def get_agent_sdk(agent_id: str, agent_name: str, private_key: str):
    """Get initialized SDK for an agent"""
    # Create temporary wallet file
    wallet_data = {
        agent_name: {
            "address": Account.from_key(private_key).address,
            "private_key": private_key
        }
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(wallet_data, temp_file)
    temp_file.close()
    
    sdk = ChaosChainAgentSDK(
        agent_name=agent_name,
        agent_domain=f"{agent_name.lower()}.example.com",
        agent_role=AgentRole.SERVER,
        network=NetworkConfig.BASE_SEPOLIA,
        enable_payments=True,
        wallet_file=temp_file.name
    )
    
    return sdk
```

#### 2. Add Payment to Shopping Service

```python
# In services/shopping_service.py

async def execute_payment(
    self,
    client_agent_id: UUID,
    merchant_agent_id: UUID,
    product_id: UUID,
    final_price: float,
    negotiation_id: UUID
) -> Dict[str, Any]:
    """
    Execute x402 payment from client to merchant after successful negotiation.
    """
    # Get agent data from database
    client_agent = self.agents_ops.get_agent_by_id(client_agent_id)
    merchant_agent = self.agents_ops.get_agent_by_id(merchant_agent_id)
    
    # Get private keys (decrypted)
    client_private_key = decrypt_pk(client_agent["encrypted_private_key"])
    merchant_private_key = decrypt_pk(merchant_agent["encrypted_private_key"])
    
    # Initialize SDKs
    merchant_sdk = get_agent_sdk(
        str(merchant_agent_id),
        merchant_agent["metadata"]["name"],
        merchant_private_key
    )
    
    client_sdk = get_agent_sdk(
        str(client_agent_id),
        client_agent["metadata"]["name"],
        client_private_key
    )
    
    # Merchant creates payment request
    payment_request = merchant_sdk.create_x402_payment_request(
        cart_id=f"cart_{negotiation_id}",
        total_amount=final_price,
        currency="USDC",
        items=[{
            "name": product_name,
            "price": final_price
        }]
    )
    
    # Client executes payment
    payment_result = client_sdk.execute_x402_crypto_payment(
        payment_request=payment_request,
        payer_agent=client_agent["metadata"]["name"],
        service_description=f"Purchase: {product_name}"
    )
    
    # Store evidence
    evidence = {
        "negotiation_id": str(negotiation_id),
        "client_agent_id": str(client_agent_id),
        "merchant_agent_id": str(merchant_agent_id),
        "product_id": str(product_id),
        "final_price": final_price,
        "payment_request": payment_request.__dict__,
        "payment_result": payment_result.__dict__
    }
    
    evidence_cid = merchant_sdk.store_evidence(evidence)
    
    return {
        "transaction_hash": payment_result.transaction_hash,
        "settlement_address": payment_result.settlement_address,
        "amount_paid": payment_result.amount_paid,
        "protocol_fee": payment_result.protocol_fee,
        "evidence_cid": evidence_cid,
        "status": "success"
    }
```

#### 3. Update Shopping Service to Call Payment

```python
# In services/shopping_service.py, after selecting best offer

# After best_offer is selected and deal_successful is True
if deal_successful:
    try:
        payment_result = await self.execute_payment(
            client_agent_id=client_agent_id,
            merchant_agent_id=UUID(best_offer["merchant_agent_id"]),
            product_id=UUID(best_offer["product_id"]),
            final_price=best_offer["negotiated_price"],
            negotiation_id=UUID(best_offer.get("negotiation_id"))
        )
        
        # Update result with payment info
        result["payment"] = payment_result
        logger.info(f"Payment executed: {payment_result['transaction_hash']}")
    except Exception as e:
        logger.error(f"Payment failed: {str(e)}", exc_info=True)
        result["payment"] = {"status": "failed", "error": str(e)}
```

## Wallet Requirements

### For Each Agent

1. **ETH Balance**: Needed for gas fees (registration, transactions)
   - Minimum: ~0.001 ETH on Base Sepolia
   - Recommended: 0.01 ETH for multiple transactions

2. **USDC Balance** (for client agents):
   - Client agents need USDC to pay merchants
   - Amount depends on purchase price
   - Must be USDC on Base Sepolia network

3. **Wallet Storage**:
   - Private keys are encrypted in database
   - Decrypt when needed for SDK initialization
   - Never log or expose private keys

## Environment Variables

```bash
# Network Configuration
NETWORK=base-sepolia
BASE_SEPOLIA_RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_API_KEY

# IPFS Storage (Pinata)
PINATA_JWT=your_pinata_jwt_token
PINATA_GATEWAY=https://your-gateway.mypinata.cloud

# Wallet Encryption
USER_SECRET_KEY=your_secret_key_for_encryption

# Optional: Custom wallet file location
CHAOSCHAIN_WALLET_FILE=my_agent_wallets.json
```

## Error Handling

```python
from chaoschain_sdk.exceptions import (
    ChaosChainSDKError,
    PaymentError,
    StorageError
)

try:
    payment_result = client_sdk.execute_x402_crypto_payment(...)
except PaymentError as e:
    # Handle payment-specific errors
    logger.error(f"Payment failed: {e}")
    # Check if wallet has sufficient USDC
    # Retry with different amount
except ChaosChainSDKError as e:
    # Handle general SDK errors
    logger.error(f"SDK error: {e}")
```

## Security Best Practices

1. **Never store private keys in plaintext**
   - Always encrypt using `encrypt_pk()`
   - Use strong `USER_SECRET_KEY`

2. **Validate payment amounts**
   - Double-check negotiated price matches payment amount
   - Verify currency (USDC)

3. **Store transaction evidence**
   - Always store payment evidence on IPFS
   - Link evidence to negotiation records

4. **Monitor wallet balances**
   - Check ETH balance before transactions
   - Check USDC balance before payments
   - Alert when balances are low

## Testing

### Test Payment Flow

```python
# Test script: test_x402_payment.py
import asyncio
from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole

async def test_payment():
    # Create test merchant SDK
    merchant_sdk = ChaosChainAgentSDK(
        agent_name="TestMerchant",
        agent_domain="test.merchant.com",
        agent_role=AgentRole.MERCHANT,
        network=NetworkConfig.BASE_SEPOLIA,
        enable_payments=True
    )
    
    # Create payment request
    request = merchant_sdk.create_x402_payment_request(
        cart_id="test_cart_123",
        total_amount=1.0,  # Small test amount
        currency="USDC",
        items=[{"name": "Test Product", "price": 1.0}]
    )
    
    print(f"Payment request created: {request.request_id}")
    print(f"Share this with client agent to execute payment")

if __name__ == "__main__":
    asyncio.run(test_payment())
```

## Summary

**Key Concepts:**
- **Agents** = On-chain identities (ERC-8004) with wallets
- **x402** = W3C-compliant A2A payment protocol
- **USDC** = Payment currency on Base Sepolia
- **Evidence** = IPFS-stored transaction proofs

**Payment Flow:**
1. Merchant creates payment request
2. Client executes payment (sends USDC)
3. Transaction recorded on-chain
4. Evidence stored on IPFS

**Integration Points:**
- After successful negotiation → Execute payment
- Store payment evidence → Link to negotiation record
- Update database → Mark negotiation as "paid"

For more details, see the [ChaosChain SDK Quickstart](https://docs.chaoscha.in/sdk/quickstart).

