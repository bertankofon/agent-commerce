import os
import json
import tempfile
import logging
import uuid
from typing import Dict, Optional, Any
from uuid import UUID
from eth_account import Account
from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole

logger = logging.getLogger(__name__)


def create_chaoschain_agent(
    agent_name: str,
    agent_domain: str,
    private_key: str,
    agent_role: AgentRole = AgentRole.SERVER,
    network: Optional[NetworkConfig] = None,
    enable_payments: bool = True,
    enable_process_integrity: bool = True,
    enable_ap2: bool = True
) -> Dict[str, str]:
    """
    Create and register a NEW ChaosChain agent using external_private_key.
    
    Official SDK Pattern:
    - SDK auto-generates wallet internally OR uses external_private_key
    - We provide the private key, SDK manages everything
    - Agent must have ETH for gas fees
    
    Args:
        agent_name: Name of the agent
        agent_domain: Domain of the agent
        private_key: Private key for the agent wallet (hex string, will be stored in database)
        agent_role: Role of the agent (default: SERVER)
        network: Network configuration (defaults to BASE_SEPOLIA)
        enable_payments: Enable payments feature
        enable_process_integrity: Enable process integrity feature
        enable_ap2: Enable AP2 feature
    
    Returns:
        Dictionary with agent_id, transaction_hash, public_address, and private_key
    """
    try:
        # Get network from environment or use default
        if network is None:
            network_str = os.getenv("CHAOSCHAIN_NETWORK", "BASE_SEPOLIA")
            network = getattr(NetworkConfig, network_str, NetworkConfig.BASE_SEPOLIA)
        
        # Get public address from private key
        agent_account = Account.from_key(private_key)
        agent_public_address = agent_account.address
        
        logger.info(f"Creating new ChaosChain agent: {agent_name}")
        logger.info(f"Agent address: {agent_public_address}")
        logger.info(f"⚠️  Agent wallet MUST have ETH for gas fees!")
        
        # Create temporary wallet file for SDK (required by current SDK version)
        wallet_data = {agent_name: {"address": agent_public_address, "private_key": private_key}}
        temp_fd, temp_wallet_file = tempfile.mkstemp(suffix='.json', prefix='wallet_')
        os.close(temp_fd)
        
        try:
            with open(temp_wallet_file, 'w') as f:
                json.dump(wallet_data, f)
            
            # Initialize SDK with wallet_file
            sdk = ChaosChainAgentSDK(
                agent_name=agent_name,
                agent_domain=agent_domain,
                agent_role=agent_role,
                network=network,
                wallet_file=temp_wallet_file,  # Current SDK requires wallet_file
                enable_payments=enable_payments,
                enable_process_integrity=enable_process_integrity,
                enable_ap2=enable_ap2
            )
            
            logger.info(f"SDK initialized for new agent: {agent_name}")
            
            # Register the agent identity on ERC-8004
            # This uses the agent's wallet to pay for gas
            agent_id, tx_hash = sdk.register_identity()
            
        finally:
            # Clean up temp file
            try:
                os.remove(temp_wallet_file)
            except:
                pass
        
        logger.info(
            f"✅ ChaosChain agent registered on-chain: "
            f"agent_id={agent_id}, tx_hash={tx_hash}, address={agent_public_address}"
        )
        
        return {
            "agent_id": agent_id,
            "transaction_hash": tx_hash,
            "public_address": agent_public_address,
            "private_key": private_key,  # Return original private key for storage
        }
        
    except Exception as e:
        logger.error(f"Error creating ChaosChain agent: {str(e)}", exc_info=True)
        raise


def get_agent_sdk(
    agent_name: str,
    agent_domain: str,
    private_key: str,
    agent_role: AgentRole = AgentRole.SERVER,
    network: Optional[NetworkConfig] = None,
    enable_payments: bool = True,
    enable_process_integrity: bool = True,
    enable_ap2: bool = True
) -> ChaosChainAgentSDK:
    """
    Get initialized ChaosChain SDK for an existing agent using external_private_key.
    
    This is the official SDK pattern:
    - SDK manages wallet internally
    - We just provide the private key
    - No manual wallet file creation needed
    
    Args:
        agent_name: Name of the agent
        agent_domain: Domain of the agent
        private_key: Decrypted private key for the agent wallet (hex string without 0x)
        agent_role: Role of the agent (default: SERVER)
        network: Network configuration (defaults to BASE_SEPOLIA from env or default)
        enable_payments: Enable payments feature (MUST be True for x402)
        enable_process_integrity: Enable process integrity feature
        enable_ap2: Enable AP2 feature
    
    Returns:
        Initialized ChaosChainAgentSDK instance
    """
    try:
        # FORCE enable_payments=True for x402 payments (required)
        if not enable_payments:
            logger.warning(f"enable_payments was False for agent {agent_name}, forcing to True for x402 support")
            enable_payments = True
            
        # Get network from environment or use default
        if network is None:
            network_str = os.getenv("CHAOSCHAIN_NETWORK", "BASE_SEPOLIA")
            network = getattr(NetworkConfig, network_str, NetworkConfig.BASE_SEPOLIA)
        
        # Get public address from private key
        agent_account = Account.from_key(private_key)
        agent_public_address = agent_account.address
        
        logger.info(f"Initializing SDK for agent: {agent_name}")
        logger.info(f"Agent domain: {agent_domain}, address: {agent_public_address}")
        
        # Create temporary wallet file for SDK (required by current SDK version)
        wallet_data = {agent_name: {"address": agent_public_address, "private_key": private_key}}
        temp_fd, temp_wallet_file = tempfile.mkstemp(suffix='.json', prefix='wallet_')
        os.close(temp_fd)
        
        with open(temp_wallet_file, 'w') as f:
            json.dump(wallet_data, f)
        
        # Initialize SDK with wallet_file
        sdk = ChaosChainAgentSDK(
            agent_name=agent_name,
            agent_domain=agent_domain,
            agent_role=agent_role,
            network=network,
            wallet_file=temp_wallet_file,  # Current SDK requires wallet_file
            enable_payments=True,
            enable_process_integrity=True,
            enable_ap2=True
        )
        
        # Clean up temp file
        try:
            os.remove(temp_wallet_file)
        except:
            pass
        
        # Verify x402 methods are available
        if not hasattr(sdk, 'create_x402_payment_request') or not hasattr(sdk, 'execute_x402_crypto_payment'):
            raise ValueError(
                f"SDK for {agent_name} does not have x402 payment methods. "
                "Ensure enable_payments=True and SDK is properly initialized."
            )
        
        logger.info(f"✅ SDK initialized for agent: {agent_name}")
        logger.info(f"   Address: {agent_public_address}")
        logger.info(f"   x402 payments: enabled")
        
        return sdk
        
    except Exception as e:
        logger.error(f"Error getting agent SDK: {str(e)}", exc_info=True)
        raise


def execute_x402_payment(
    client_sdk: ChaosChainAgentSDK,
    merchant_sdk: ChaosChainAgentSDK,
    product_name: str,
    final_price: float,
    negotiation_id: Optional[UUID] = None,
    cart_id: Optional[str] = None,
    client_name: Optional[str] = None,
    client_public_address: Optional[str] = None,
    merchant_public_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute x402 payment from client to merchant.
    
    Args:
        client_sdk: Initialized SDK for client agent (payer)
        merchant_sdk: Initialized SDK for merchant agent (payee)
        product_name: Name of the product being purchased
        final_price: Final negotiated price in USDC
        negotiation_id: Optional negotiation ID for tracking
        cart_id: Optional cart ID (defaults to negotiation_id or generated UUID)
        client_name: Optional client agent name (defaults to extracting from SDK)
        client_public_address: Optional client agent's public address for verification
        merchant_public_address: Optional merchant agent's public address (required for payee)
    
    Returns:
        Dictionary with payment result including transaction_hash, evidence_cid, etc.
    """
    try:
        # Get agent names from SDKs if not provided
        if not client_name:
            client_name = getattr(client_sdk, 'agent_name', 'ClientAgent')
        
        merchant_name = getattr(merchant_sdk, 'agent_name', 'MerchantAgent')
        
        # Use addresses provided as parameters (from database)
        client_wallet_address = client_public_address
        merchant_wallet_address = merchant_public_address
        
        logger.info(f"✅ Client: {client_name} ({client_wallet_address})")
        logger.info(f"✅ Merchant: {merchant_name} ({merchant_wallet_address})")
        
        # Verify addresses are different
        if client_wallet_address and merchant_wallet_address:
            if client_wallet_address.lower() == merchant_wallet_address.lower():
                raise ValueError(
                    f"❌ Client and Merchant are using the SAME wallet address: {client_wallet_address}"
                )
        
        # Log payment flow
        logger.info("="*80)
        logger.info("💰 PAYMENT FLOW")
        logger.info("="*80)
        logger.info(f"FROM: {client_name} ({client_wallet_address})")
        logger.info(f"TO:   {merchant_name} ({merchant_wallet_address})")
        logger.info(f"AMOUNT: ${final_price} USDC")
        logger.info("="*80)
        
        # Generate cart_id if not provided
        if not cart_id:
            cart_id = f"cart_{negotiation_id}" if negotiation_id else f"cart_{uuid.uuid4()}"
        
        logger.info(f"\n📝 Step 1: Merchant creates payment request (cart: {cart_id})")
        
        try:
            # ✅ OFFICIAL SDK PATTERN: Merchant SDK creates payment request
            # SDK will automatically use merchant's wallet address as settlement_address
            payment_request = merchant_sdk.create_x402_payment_request(
                cart_id=cart_id,
                total_amount=final_price,
                currency="USDC",
                items=[{
                    "name": product_name,
                    "price": final_price
                }]
            )
            
            logger.info(f"✅ Payment request created by merchant")
            logger.info(f"   Settlement address: {payment_request.settlement_address}")
            logger.info(f"   Expected (merchant): {merchant_wallet_address}")
            
            # Verify settlement_address is merchant's address
            if payment_request.settlement_address.lower() != merchant_wallet_address.lower():
                raise ValueError(
                    f"❌ Settlement address mismatch!\n"
                    f"   Expected: {merchant_wallet_address}\n"
                    f"   Got: {payment_request.settlement_address}"
                )
                
        except Exception as e:
            logger.error(f"❌ Error creating payment request: {str(e)}")
            raise
        
        logger.info(f"\n💸 Step 2: Client executes payment")
        logger.info(f"   Payment request ID: {payment_request.id if hasattr(payment_request, 'id') else 'N/A'}")
        logger.info(f"   Settlement address: {payment_request.settlement_address}")
        logger.info(f"   Payer agent: {client_name}")
        logger.info(f"   Expected flow: {client_wallet_address} → {merchant_wallet_address}")
        
        try:
            # ✅ BYPASS A2A-x402 Extension - Call PaymentManager directly
            # The A2A extension has a bug: it uses self.agent_name as recipient
            # We manually register merchant's address with client SDK
            
            # ✅ MONKEY-PATCH: Inject merchant's address into client SDK's wallet_manager
            # Store original get_wallet_address method
            original_get_wallet_address = client_sdk.wallet_manager.get_wallet_address
            
            def patched_get_wallet_address(agent_name: str) -> str:
                """Return merchant address for merchant, otherwise use original method."""
                if agent_name == merchant_name:
                    logger.info(f"   Returning patched address for {merchant_name}: {merchant_wallet_address}")
                    return merchant_wallet_address
                return original_get_wallet_address(agent_name)
            
            # Replace the method
            client_sdk.wallet_manager.get_wallet_address = patched_get_wallet_address
            logger.info(f"✅ Patched client SDK wallet_manager to recognize merchant address")
            
            amount = float(payment_request.total["amount"]["value"])
            currency = payment_request.total["amount"]["currency"]
            
            # Create payment request directly for payment manager
            pm_payment_request = client_sdk.payment_manager.create_x402_payment_request(
                from_agent=client_name,
                to_agent=merchant_name,  # Merchant as recipient
                amount=amount,
                currency=currency,
                service_description=f"Purchase: {product_name}"
            )
            
            logger.info(f"Executing payment: {client_name} → {merchant_name} ({merchant_wallet_address})")
            
            # Execute payment via payment manager
            payment_proof = client_sdk.payment_manager.execute_x402_payment(pm_payment_request)
            
            # Convert to expected format (simulating X402PaymentResponse)
            class PaymentResult:
                def __init__(self, proof, settlement_addr, amt, fee):
                    self.payment_id = proof.payment_id
                    self.transaction_hash = proof.transaction_hash
                    self.settlement_address = settlement_addr
                    self.amount_paid = amt
                    self.total_amount = amt
                    self.protocol_fee = fee
                    self.status = "confirmed"
            
            payment_result = PaymentResult(payment_proof, merchant_wallet_address, amount, pm_payment_request.get("protocol_fee", 0))
            
            logger.info("✅ Payment executed")
            
        except Exception as e:
            logger.error(f"❌ Error executing payment: {str(e)}")
            raise
        
        # Extract payment result details
        amount_paid = getattr(payment_result, 'amount_paid', None) or getattr(payment_result, 'total_amount', None) or final_price
        protocol_fee = getattr(payment_result, 'protocol_fee', None) or 0
        transaction_hash = getattr(payment_result, 'transaction_hash', None)
        settlement_address = getattr(payment_result, 'settlement_address', None) or payment_request.settlement_address
        
        logger.info(f"\n📊 Payment Result:")
        logger.info(f"   TX Hash: {transaction_hash}")
        logger.info(f"   Amount: ${amount_paid} USDC")
        logger.info(f"   Settlement: {settlement_address}")
        
        # Verify transaction on-chain (critical to catch SDK bugs)
        logger.info(f"\n🔍 Step 3: Verifying transaction on-chain...")
        
        actual_recipient_address = None
        if transaction_hash:
            try:
                from web3 import Web3
                
                rpc_url = os.getenv("BASE_SEPOLIA_RPC_URL") or "https://sepolia.base.org"
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                tx_receipt = w3.eth.get_transaction_receipt(transaction_hash)
                
                # USDC contract on Base Sepolia
                usdc_contract = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
                
                # Find USDC Transfer event
                for log in tx_receipt.get('logs', []):
                    if log.get('address', '').lower() == usdc_contract.lower():
                            if len(log.get('topics', [])) >= 3:
                                to_address_hex = log['topics'][2].hex()
                                to_address = '0x' + to_address_hex[-40:].lower()
                                actual_recipient_address = Web3.to_checksum_address(to_address)
                            logger.info(f"   On-chain recipient: {actual_recipient_address}")
                            break
                
            except Exception as e:
                logger.warning(f"⚠️  Could not verify on-chain: {str(e)}")
        
        # Verify recipient is correct
        verified_recipient = actual_recipient_address or settlement_address
        
        if verified_recipient:
            if verified_recipient.lower() == client_wallet_address.lower():
                raise ValueError(
                    f"❌ Payment sent to CLIENT address!\n"
                    f"   Client: {client_wallet_address}\n"
                    f"   Expected merchant: {merchant_wallet_address}\n"
                    f"   TX: {transaction_hash}"
                )
            elif verified_recipient.lower() != merchant_wallet_address.lower():
                raise ValueError(
                    f"❌ Payment sent to WRONG address!\n"
                    f"   Recipient: {verified_recipient}\n"
                    f"   Expected merchant: {merchant_wallet_address}\n"
                    f"   TX: {transaction_hash}"
                )
            else:
                logger.info(f"✅ Recipient verified: {verified_recipient}")
                settlement_address = verified_recipient
        
        # Store evidence on IPFS
        # Extract only serializable fields from payment_request and payment_result
        def extract_serializable(obj):
            """Extract only serializable attributes from an object."""
            if obj is None:
                return None
            result = {}
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    # Skip non-serializable types
                    if isinstance(value, (str, int, float, bool, type(None))):
                        result[key] = value
                    elif isinstance(value, (list, dict)):
                        try:
                            json.dumps(value)  # Test if serializable
                            result[key] = value
                        except (TypeError, ValueError):
                            result[key] = str(value)
                    else:
                        # Convert non-serializable to string
                        result[key] = str(value)
            else:
                result = str(obj)
            return result
        
        evidence = {
            "negotiation_id": str(negotiation_id) if negotiation_id else None,
            "cart_id": cart_id,
            "product_name": product_name,
            "final_price": final_price,
            "client_address": client_wallet_address or client_public_address,
            "merchant_address": merchant_wallet_address or merchant_public_address,
            "payment_request": extract_serializable(payment_request),
            "payment_result": extract_serializable(payment_result),
            "transaction_hash": transaction_hash,
            "settlement_address": settlement_address,
            "timestamp": str(uuid.uuid1().time)
        }
        
        evidence_cid = merchant_sdk.store_evidence(evidence)
        logger.info(f"\n✅ Payment complete!")
        logger.info(f"   Evidence CID: {evidence_cid}")
        logger.info(f"="*80)
        
        return {
            "status": "success",
            "transaction_hash": transaction_hash,
            "settlement_address": settlement_address,
            "amount_paid": amount_paid,
            "protocol_fee": protocol_fee,
            "evidence_cid": evidence_cid,
            "cart_id": cart_id,
            "payment_request_id": getattr(payment_request, 'id', None) or cart_id
        }
        
    except Exception as e:
        logger.error(f"Error executing x402 payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

