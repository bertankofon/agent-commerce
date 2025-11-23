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
    Create and register a ChaosChain agent.
    
    Wallet Configuration:
    - The agent's own wallet (private_key parameter) is always used for registration and fees
    - The agent's wallet must be funded with ETH before calling this function
    - The agent's wallet is stored in the database for future use
    
    Args:
        agent_name: Name of the agent
        agent_domain: Domain of the agent
        private_key: Private key for the agent wallet (will be stored in database, must be funded)
        agent_role: Role of the agent (default: SERVER)
        network: Network configuration (defaults to BASE_SEPOLIA from env or default)
        enable_payments: Enable payments feature
        enable_process_integrity: Enable process integrity feature
        enable_ap2: Enable AP2 feature
    
    Returns:
        Dictionary with agent_id, transaction_hash, public_address, and private_key
    
    Environment Variables:
        CHAOSCHAIN_NETWORK: (Optional) Network name, defaults to BASE_SEPOLIA
    """
    try:
        # Get network from environment or use default
        if network is None:
            network_str = os.getenv("CHAOSCHAIN_NETWORK", "BASE_SEPOLIA")
            network = getattr(NetworkConfig, network_str, NetworkConfig.BASE_SEPOLIA)
        
        # Get public address from the agent's private key (the one we created and will store)
        from eth_account import Account
        agent_account = Account.from_key(private_key)
        agent_public_address = agent_account.address
        
        # Always use the agent's own wallet for registration and fees
        wallet_to_use = private_key
        wallet_address = agent_public_address
        
        logger.info(
            f"Using agent's own wallet for registration: {wallet_address}. "
            f"Make sure this wallet has ETH for gas fees."
        )
        
        # Create a temporary wallet file in the format expected by the SDK
        # Format: {"agent_name": {"address": "...", "private_key": "..."}}
        wallet_data = {
            agent_name: {
                "address": wallet_address,
                "private_key": wallet_to_use
            }
        }
        
        # Create temporary wallet file
        temp_wallet_file = None
        try:
            # Create a temporary file for the wallet
            temp_fd, temp_wallet_file = tempfile.mkstemp(suffix='.json', prefix='chaoschain_wallet_')
            os.close(temp_fd)  # Close the file descriptor, we'll write using the path
            
            # Write wallet data to temporary file
            with open(temp_wallet_file, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            logger.info(f"Created temporary wallet file: {temp_wallet_file}")
            
            # Initialize SDK with wallet_file parameter
            # This tells the SDK which wallet to use for transactions
            sdk = ChaosChainAgentSDK(
                agent_name=agent_name,
                agent_domain=agent_domain,
                agent_role=agent_role,
                network=network,
                enable_payments=enable_payments,
                enable_process_integrity=enable_process_integrity,
                enable_ap2=enable_ap2,
                wallet_file=temp_wallet_file  # Pass wallet file to SDK
            )
            
            logger.info(f"SDK initialized with agent wallet from file")
            
            # Register the agent identity (ERC-8004)
            # This will use the wallet specified in wallet_file to pay for gas
            agent_id, tx_hash = sdk.register_identity()
            
        finally:
            # Clean up temporary wallet file
            if temp_wallet_file and os.path.exists(temp_wallet_file):
                try:
                    os.remove(temp_wallet_file)
                    logger.debug(f"Cleaned up temporary wallet file: {temp_wallet_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove temporary wallet file: {str(e)}")
        
        public_address = agent_public_address
        
        logger.info(
            f"ChaosChain agent registered: agent_id={agent_id}, "
            f"tx_hash={tx_hash}, address={public_address}"
        )
        
        return {
            "agent_id": agent_id,
            "transaction_hash": tx_hash,
            "public_address": public_address,
            "private_key": private_key,  # Return original private key for encryption
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
    Get initialized ChaosChain SDK for an existing agent.
    
    Note: enable_payments MUST be True for x402 crypto payments to work.
    If False is passed, it will be forced to True.
    
    Args:
        agent_name: Name of the agent
        agent_domain: Domain of the agent
        private_key: Decrypted private key for the agent wallet
        agent_role: Role of the agent (default: SERVER)
        network: Network configuration (defaults to BASE_SEPOLIA from env or default)
        enable_payments: Enable payments feature (MUST be True for x402, will be forced if False)
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
        
        # Create a temporary wallet file in the format expected by the SDK
        wallet_data = {
            agent_name: {
                "address": agent_public_address,
                "private_key": private_key
            }
        }
        
        # Create temporary wallet file
        temp_fd, temp_wallet_file = tempfile.mkstemp(suffix='.json', prefix='chaoschain_wallet_')
        os.close(temp_fd)
        
        # Write wallet data to temporary file
        with open(temp_wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info(f"Created temporary wallet file for SDK: {temp_wallet_file}")
        
        # Initialize SDK with wallet_file parameter
        logger.info(f"DEBUG: Initializing SDK with enable_payments={enable_payments}, enable_process_integrity={enable_process_integrity}, enable_ap2={enable_ap2}")
        logger.info(f"DEBUG: Agent name={agent_name}, domain={agent_domain}, role={agent_role}")
        
        sdk = ChaosChainAgentSDK(
            agent_name=agent_name,
            agent_domain=agent_domain,
            agent_role=agent_role,
            network=network,
            enable_payments=True,
            enable_process_integrity=True,
            enable_ap2=True,
            wallet_file=temp_wallet_file
        )
        
        # CRITICAL: Verify payments are actually enabled (should always be True)
        if not enable_payments:
            raise ValueError(
                "enable_payments MUST be True for x402 payments. "
                "This should never happen as it's forced to True above."
            )
        
        # Verify x402 methods exist and are available
        logger.info("DEBUG: Verifying SDK x402 payment methods...")
        has_create_x402 = hasattr(sdk, 'create_x402_payment_request')
        has_execute_x402 = hasattr(sdk, 'execute_x402_crypto_payment')
        
        logger.info(f"DEBUG: SDK has create_x402_payment_request: {has_create_x402}")
        logger.info(f"DEBUG: SDK has execute_x402_crypto_payment: {has_execute_x402}")
        
        # Strict validation: x402 methods MUST exist
        if not has_create_x402:
            error_msg = (
                "SDK does not have create_x402_payment_request method despite enable_payments=True. "
                "This may indicate: "
                "1) SDK version issue - update chaoschain-sdk package, "
                "2) SDK configuration problem, "
                "3) x402 extension not properly loaded. "
                f"SDK type: {type(sdk)}, SDK attributes: {[attr for attr in dir(sdk) if 'payment' in attr.lower() or 'x402' in attr.lower()][:10]}"
            )
            logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        
        if not has_execute_x402:
            error_msg = (
                "SDK does not have execute_x402_crypto_payment method despite enable_payments=True. "
                "This may indicate: "
                "1) SDK version issue - update chaoschain-sdk package, "
                "2) SDK configuration problem, "
                "3) x402 extension not properly loaded. "
                f"SDK type: {type(sdk)}, SDK attributes: {[attr for attr in dir(sdk) if 'payment' in attr.lower() or 'x402' in attr.lower()][:10]}"
            )
            logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("✓ x402 payment methods are available and verified")
        
        # Store temp file path for cleanup (we'll clean it up later)
        sdk._temp_wallet_file = temp_wallet_file
        
        logger.info(f"SDK initialized for agent: {agent_name} ({agent_public_address})")
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
        # CRITICAL: Verify wallet addresses before payment
        client_wallet_address = None
        merchant_wallet_address = None
        
        # Get wallet addresses from SDK wallet files
        if hasattr(client_sdk, '_temp_wallet_file') and os.path.exists(client_sdk._temp_wallet_file):
            with open(client_sdk._temp_wallet_file, 'r') as f:
                client_wallet_data = json.load(f)
                client_wallet_address = list(client_wallet_data.values())[0].get('address') if client_wallet_data else None
        
        if hasattr(merchant_sdk, '_temp_wallet_file') and os.path.exists(merchant_sdk._temp_wallet_file):
            with open(merchant_sdk._temp_wallet_file, 'r') as f:
                merchant_wallet_data = json.load(f)
                merchant_wallet_address = list(merchant_wallet_data.values())[0].get('address') if merchant_wallet_data else None
        
        # Verify addresses match if provided
        if client_public_address and client_wallet_address:
            if client_public_address.lower() != client_wallet_address.lower():
                raise ValueError(
                    f"Client address mismatch! "
                    f"Expected: {client_public_address}, "
                    f"Wallet file has: {client_wallet_address}"
                )
        
        if merchant_public_address and merchant_wallet_address:
            if merchant_public_address.lower() != merchant_wallet_address.lower():
                raise ValueError(
                    f"Merchant address mismatch! "
                    f"Expected: {merchant_public_address}, "
                    f"Wallet file has: {merchant_wallet_address}"
                )
        
        # Log payment flow
        logger.info("="*80)
        logger.info("💰 PAYMENT FLOW VERIFICATION")
        logger.info("="*80)
        logger.info(f"FROM (Client/Payer): {client_wallet_address or client_public_address or 'N/A'}")
        logger.info(f"TO (Merchant/Payee): {merchant_wallet_address or merchant_public_address or 'N/A'}")
        logger.info(f"Amount: ${final_price} USDC")
        logger.info("="*80)
        
        if client_wallet_address and merchant_wallet_address:
            if client_wallet_address.lower() == merchant_wallet_address.lower():
                raise ValueError(
                    f"CRITICAL ERROR: Client and Merchant are using the SAME wallet address! "
                    f"Address: {client_wallet_address}. Payment cannot proceed."
                )
            logger.info("✓ Wallet addresses verified - they are different")
        
        if not merchant_public_address:
            logger.warning("⚠ Merchant public_address not provided - using wallet file address")
            merchant_public_address = merchant_wallet_address
        # Verify merchant SDK has payments enabled
        logger.info("DEBUG: Verifying merchant SDK has x402 payment methods...")
        if not hasattr(merchant_sdk, 'create_x402_payment_request'):
            error_msg = "Merchant SDK does not have create_x402_payment_request method. Ensure enable_payments=True when initializing SDK."
            logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        logger.info("✓ Merchant SDK has create_x402_payment_request method")
        
        # Verify client SDK has payments enabled  
        logger.info("DEBUG: Verifying client SDK has x402 payment methods...")
        if not hasattr(client_sdk, 'execute_x402_crypto_payment'):
            error_msg = "Client SDK does not have execute_x402_crypto_payment method. Ensure enable_payments=True when initializing SDK."
            logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        logger.info("✓ Client SDK has execute_x402_crypto_payment method")
        
        # Generate cart_id if not provided
        if not cart_id:
            cart_id = f"cart_{negotiation_id}" if negotiation_id else f"cart_{uuid.uuid4()}"
        
        logger.info(
            f"Creating x402 payment request: "
            f"Product={product_name}, Amount=${final_price}, Cart={cart_id}"
        )
        
        # Merchant creates payment request
        # CRITICAL: The merchant SDK should use its wallet_file address as settlement_address
        logger.info("DEBUG: Calling merchant_sdk.create_x402_payment_request...")
        logger.info(f"DEBUG: Merchant SDK agent_name: {merchant_sdk.agent_name if hasattr(merchant_sdk, 'agent_name') else 'N/A'}")
        logger.info(f"DEBUG: Merchant wallet address (from wallet file): {merchant_wallet_address}")
        logger.info(f"DEBUG: Merchant public_address (from DB): {merchant_public_address}")
        logger.info(f"DEBUG: Expected settlement_address (merchant's address): {merchant_public_address or merchant_wallet_address}")
        
        # Verify merchant SDK is using the correct wallet
        if hasattr(merchant_sdk, '_temp_wallet_file') and merchant_wallet_address:
            logger.info(f"DEBUG: Merchant SDK wallet file: {merchant_sdk._temp_wallet_file}")
            logger.info(f"DEBUG: Merchant SDK should use wallet address: {merchant_wallet_address} as settlement_address")
        
        try:
            # CRITICAL: Merchant SDK creates payment request - this embeds merchant as receiver
            # The settlement_address will be automatically set to merchant SDK's wallet address
            payment_request = merchant_sdk.create_x402_payment_request(
                cart_id=cart_id,
                total_amount=final_price,
                currency="USDC",
                items=[{
                    "name": product_name,
                    "price": final_price
                }]
            )
            logger.info("DEBUG: Payment request created successfully")
            logger.info(f"DEBUG: Payment request ID: {payment_request.id if hasattr(payment_request, 'id') else 'N/A'}")
            logger.info(f"DEBUG: Payment request settlement_address: {payment_request.settlement_address}")
            logger.info(f"DEBUG: Payment request should have merchant address: {merchant_public_address or merchant_wallet_address}")
            
            # CRITICAL: Verify payment request has correct merchant settlement_address
            if payment_request.settlement_address.lower() != (merchant_public_address or merchant_wallet_address or "").lower():
                raise ValueError(
                    f"Payment request settlement_address ({payment_request.settlement_address}) "
                    f"doesn't match merchant address ({merchant_public_address or merchant_wallet_address})! "
                    f"The merchant SDK should have set this automatically from its wallet."
                )
            
            # Store payment request details for verification
            payment_request_id = payment_request.id if hasattr(payment_request, 'id') else None
            payment_request_settlement = payment_request.settlement_address
            logger.info(f"✓ Payment request verified: ID={payment_request_id}, Settlement={payment_request_settlement}")
            
            # Verify payment request payee address
            if hasattr(payment_request, 'payee_address'):
                payee_addr = payment_request.payee_address
                logger.info(f"DEBUG: Payment request payee_address: {payee_addr}")
                if merchant_public_address and payee_addr.lower() != merchant_public_address.lower():
                    logger.warning(f"⚠ Payment request payee ({payee_addr}) doesn't match merchant address ({merchant_public_address})")
            elif hasattr(payment_request, 'merchant_address'):
                payee_addr = payment_request.merchant_address
                logger.info(f"DEBUG: Payment request merchant_address: {payee_addr}")
                if merchant_public_address and payee_addr.lower() != merchant_public_address.lower():
                    logger.warning(f"⚠ Payment request merchant ({payee_addr}) doesn't match merchant address ({merchant_public_address})")
            elif hasattr(payment_request, 'settlement_address'):
                payee_addr = payment_request.settlement_address
                logger.info(f"DEBUG: Payment request settlement_address: {payee_addr}")
            else:
                logger.warning("⚠ Could not find payee address in payment request")
        except Exception as e:
            logger.error(f"DEBUG: Error creating payment request: {str(e)}")
            logger.error(f"DEBUG: Error type: {type(e).__name__}")
            # Check if it's the "extension not enabled" error
            if "extension not enabled" in str(e).lower() or "x402" in str(e).lower():
                logger.error("DEBUG: x402 extension is not enabled. Check SDK initialization.")
                logger.error("DEBUG: Ensure enable_payments=True when creating the SDK instance.")
            raise
        
        # Log payment request details safely
        logger.info("DEBUG: Payment request created successfully")
        logger.info(f"DEBUG: Payment request type: {type(payment_request)}")
        logger.info(f"DEBUG: Payment request attributes: {[attr for attr in dir(payment_request) if not attr.startswith('_')]}")
        
        # Try to get request ID or cart ID - check what's available
        payment_request_id = None
        if hasattr(payment_request, 'request_id'):
            payment_request_id = payment_request.request_id
            logger.info(f"Payment request created: {payment_request_id}")
        elif hasattr(payment_request, 'cart_id'):
            payment_request_id = payment_request.cart_id
            logger.info(f"Payment request created with cart_id: {payment_request_id}")
        elif hasattr(payment_request, 'id'):
            payment_request_id = payment_request.id
            logger.info(f"Payment request created with id: {payment_request_id}")
        else:
            # Try to get it from __dict__ or string representation
            if hasattr(payment_request, '__dict__'):
                payment_request_id = payment_request.__dict__.get('request_id') or payment_request.__dict__.get('cart_id') or payment_request.__dict__.get('id')
            if not payment_request_id:
                payment_request_id = str(payment_request)
            logger.info(f"Payment request created: {payment_request}")
        
        # Client executes payment
        # Use provided client_name or try to get from SDK, fallback to default
        if not client_name:
            client_name = "ClientAgent"
            if hasattr(client_sdk, 'agent_name'):
                client_name = client_sdk.agent_name
            elif hasattr(client_sdk, '_agent_name'):
                client_name = client_sdk._agent_name
        
        logger.info(f"Executing payment from {client_name}...")
        logger.info(f"DEBUG: Client wallet address (from wallet file): {client_wallet_address}")
        logger.info(f"DEBUG: Client public_address (from DB): {client_public_address}")
        logger.info(f"DEBUG: Expected payer address: {client_public_address or client_wallet_address}")
        logger.info(f"DEBUG: Payment request settlement_address: {payment_request.settlement_address}")
        logger.info(f"DEBUG: Expected payee (merchant) address: {merchant_public_address or merchant_wallet_address}")
        
        # CRITICAL: Verify payment request settlement_address matches merchant address
        expected_merchant_addr = (merchant_public_address or merchant_wallet_address or "").lower()
        if payment_request.settlement_address.lower() != expected_merchant_addr:
            raise ValueError(
                f"Payment request settlement_address ({payment_request.settlement_address}) "
                f"doesn't match merchant address ({merchant_public_address or merchant_wallet_address})! "
                f"Payment cannot proceed."
            )
        
        # Get merchant name from merchant SDK - CRITICAL for payment execution
        merchant_name = None
        if hasattr(merchant_sdk, 'agent_name'):
            merchant_name = merchant_sdk.agent_name
        elif hasattr(merchant_sdk, '_agent_name'):
            merchant_name = merchant_sdk._agent_name
        
        if not merchant_name:
            raise ValueError("Cannot determine merchant agent name from merchant SDK")
        
        # CRITICAL: Verify payment request object before passing to SDK
        # The SDK should use THIS payment request, not create a new one
        payment_request_id = payment_request.id if hasattr(payment_request, 'id') else None
        payment_request_settlement = payment_request.settlement_address
        
        logger.info("="*80)
        logger.info("🔍 PAYMENT REQUEST VERIFICATION BEFORE EXECUTION")
        logger.info("="*80)
        logger.info(f"Payment Request ID: {payment_request_id}")
        logger.info(f"Payment Request Settlement Address: {payment_request_settlement}")
        logger.info(f"Expected Merchant Address: {merchant_public_address or merchant_wallet_address}")
        logger.info(f"Payment Request Type: {type(payment_request)}")
        logger.info(f"Payment Request Object ID (memory): {id(payment_request)}")
        logger.info("="*80)
        
        # Verify payment request hasn't been modified
        if payment_request_settlement.lower() != (merchant_public_address or merchant_wallet_address or "").lower():
            raise ValueError(
                f"Payment request settlement_address ({payment_request_settlement}) "
                f"doesn't match merchant address ({merchant_public_address or merchant_wallet_address})! "
                f"Cannot proceed with payment."
            )
        
        logger.info("DEBUG: Calling client_sdk.execute_x402_crypto_payment...")
        logger.info(f"DEBUG: Passing payment_request object (ID: {payment_request_id}, Settlement: {payment_request_settlement})")
        logger.info(f"DEBUG: Client name: {client_name}")
        logger.info(f"DEBUG: Merchant name: {merchant_name}")
        logger.info(f"DEBUG: Service description: Purchase: {product_name}")
        logger.info(f"DEBUG: ⚠ CRITICAL - SDK MUST use payment_request.settlement_address ({payment_request_settlement}) for recipient")
        logger.info(f"DEBUG: ⚠ CRITICAL - SDK MUST use client wallet_file ({client_wallet_address or client_public_address}) for sender")
        
        try:
            # Store original payment request details for verification
            original_settlement = payment_request.settlement_address
            original_id = payment_request.id if hasattr(payment_request, 'id') else None
            
            logger.info(f"DEBUG: Original payment request - ID: {original_id}, Settlement: {original_settlement}")
            logger.info(f"DEBUG: Payment request object ID (memory): {id(payment_request)}")
            logger.info(f"DEBUG: This payment request was created by MERCHANT SDK and should be used as-is")
            
            # Execute x402 payment from client to merchant
            # - Client SDK uses its own wallet as sender (payer)
            # - Payment request has merchant's address as settlement_address (recipient/payee)
            # - No payer_agent parameter needed - SDK should infer from its wallet and payment_request
            logger.info("="*80)
            logger.info("💰 EXECUTING PAYMENT: CLIENT → MERCHANT")
            logger.info("="*80)
            logger.info(f"FROM (Client/Payer): {client_name} ({client_wallet_address or client_public_address})")
            logger.info(f"TO (Merchant/Payee): {merchant_name} ({merchant_public_address or merchant_wallet_address})")
            logger.info(f"Amount: ${final_price} USDC")
            logger.info(f"Payment Request Settlement Address: {original_settlement}")
            logger.info("="*80)
            logger.info("DEBUG: Using merchant-created payment request (has correct merchant settlement_address)")
            logger.info("DEBUG: Client SDK will use its own wallet as sender")
            logger.info("DEBUG: Passing merchant_name as payer_agent - SDK will look up merchant in registry")
            logger.info(f"DEBUG: Expected flow: Client wallet → Merchant address ({merchant_public_address})")
            
            # Execute payment: client SDK uses its own wallet as sender
            # CRITICAL: Pass merchant_name as payer_agent so SDK looks up merchant in registry
            # The SDK will use the merchant's registered address as the recipient
            payment_result = client_sdk.execute_x402_crypto_payment(
                payment_request=payment_request,  # Merchant-created payment request with correct settlement_address
                payer_agent=merchant_name,  # Merchant name - SDK will look up merchant's address in registry
                service_description=f"Purchase: {product_name}"
            )
            
            # Verify payment_request object wasn't modified
            if payment_request.settlement_address != original_settlement:
                logger.warning(
                    f"⚠ Payment request settlement_address was modified! "
                    f"Original: {original_settlement}, After: {payment_request.settlement_address}"
                )
            
            logger.info("DEBUG: Payment execution completed successfully")
        except Exception as e:
            logger.error(f"DEBUG: Error executing payment: {str(e)}")
            logger.error(f"DEBUG: Error type: {type(e).__name__}")
            if "extension not enabled" in str(e).lower() or "x402" in str(e).lower():
                logger.error("DEBUG: x402 extension is not enabled for client SDK. Check SDK initialization.")
                logger.error("DEBUG: Ensure enable_payments=True when creating the client SDK instance.")
            raise
        
        # Safely extract attributes from payment_result FIRST (before using them)
        amount_paid = getattr(payment_result, 'amount_paid', None) or getattr(payment_result, 'total_amount', None) or final_price
        protocol_fee = getattr(payment_result, 'protocol_fee', None) or 0
        transaction_hash = getattr(payment_result, 'transaction_hash', None)
        settlement_address = getattr(payment_result, 'settlement_address', None) or payment_request.settlement_address
        
        logger.info(
            f"Payment executed successfully: "
            f"TX Hash={transaction_hash}, "
            f"Amount=${amount_paid}, "
            f"Settlement Address={settlement_address}"
        )
        
        # CRITICAL: Verify the ACTUAL transaction on-chain to catch SDK bugs
        # The SDK might report wrong settlement_address, so we check the actual blockchain transaction
        actual_recipient_address = None
        if transaction_hash:
            try:
                from web3 import Web3
                
                # Get RPC URL from environment (os is already imported at module level)
                rpc_url = os.getenv("BASE_SEPOLIA_RPC_URL") or "https://sepolia.base.org"
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Get the actual transaction from blockchain
                tx = w3.eth.get_transaction(transaction_hash)
                tx_receipt = w3.eth.get_transaction_receipt(transaction_hash)
                
                # For USDC transfers, check the Transfer event logs
                # USDC contract address on Base Sepolia: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
                usdc_contract_address = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
                
                # Look for Transfer events in the transaction receipt
                transfer_event_signature = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Transfer(address,address,uint256)
                
                for log in tx_receipt.get('logs', []):
                    if log.get('address', '').lower() == usdc_contract_address.lower():
                        # Decode Transfer event: Transfer(address indexed from, address indexed to, uint256 value)
                        try:
                            # Extract 'to' address from log topics (topic[2] for Transfer event)
                            if len(log.get('topics', [])) >= 3:
                                to_address_hex = log['topics'][2].hex()
                                # Remove '0x' and pad to 40 chars (20 bytes = 40 hex chars)
                                to_address = '0x' + to_address_hex[-40:].lower()
                                actual_recipient_address = Web3.to_checksum_address(to_address)
                                logger.info(f"DEBUG: Found USDC Transfer event - recipient: {actual_recipient_address}")
                                break
                        except Exception as e:
                            logger.warning(f"Could not decode Transfer event: {str(e)}")
                
                # Fallback: check transaction 'to' field if no Transfer event found
                if not actual_recipient_address:
                    actual_recipient_address = tx.get('to')
                    logger.info(f"DEBUG: Using transaction 'to' field as recipient: {actual_recipient_address}")
                
            except Exception as e:
                logger.warning(f"Could not verify transaction on-chain: {str(e)}")
                # Continue with settlement_address from payment_result as fallback
        
        # Use actual recipient from blockchain if available, otherwise use settlement_address from result
        verified_recipient = actual_recipient_address or settlement_address
        
        # CRITICAL: Verify recipient matches merchant address
        expected_merchant_address = merchant_public_address or merchant_wallet_address
        if verified_recipient and expected_merchant_address:
            if verified_recipient.lower() != expected_merchant_address.lower():
                error_msg = (
                    f"CRITICAL ERROR: Payment was sent to WRONG address!\n"
                    f"Expected merchant address: {expected_merchant_address}\n"
                    f"Actual recipient (from blockchain): {verified_recipient}\n"
                    f"SDK reported settlement_address: {settlement_address}\n"
                    f"Payment request had settlement_address: {payment_request.settlement_address}\n"
                    f"Transaction Hash: {transaction_hash}\n\n"
                    f"The payment request was created with merchant settlement_address "
                    f"({payment_request.settlement_address}), but the actual on-chain transaction "
                    f"sent funds to a different address ({verified_recipient}).\n\n"
                    f"Please verify the SDK payment execution logic."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                logger.info(f"✓ Recipient verified on-chain: {verified_recipient} (matches merchant)")
        
        # Also verify it's not the client's address
        expected_client_address = client_public_address or client_wallet_address
        if verified_recipient and expected_client_address:
            if verified_recipient.lower() == expected_client_address.lower():
                error_msg = (
                    f"CRITICAL ERROR: Payment was sent to CLIENT's own address instead of merchant!\n"
                    f"Client address: {expected_client_address}\n"
                    f"Actual recipient (from blockchain): {verified_recipient}\n"
                    f"Expected merchant address: {expected_merchant_address}\n"
                    f"Transaction Hash: {transaction_hash}\n\n"
                    f"The payment request was created with merchant settlement_address "
                    f"({payment_request.settlement_address}), but the actual on-chain transaction "
                    f"sent funds to the client's own address.\n\n"
                    f"Please verify the SDK payment execution logic."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Update settlement_address to verified recipient if we got it from blockchain
        if actual_recipient_address:
            settlement_address = actual_recipient_address
            logger.info(f"✓ Using verified recipient from blockchain: {settlement_address}")
        
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
        logger.info(f"Evidence stored on IPFS: {evidence_cid}")
        
        return {
            "status": "success",
            "transaction_hash": transaction_hash,
            "settlement_address": settlement_address,
            "amount_paid": amount_paid,
            "protocol_fee": protocol_fee,
            "evidence_cid": evidence_cid,
            "cart_id": cart_id,
            "payment_request_id": payment_request_id  # Use the variable we determined above
        }
        
    except Exception as e:
        logger.error(f"Error executing x402 payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

