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
            enable_process_integrity=enable_process_integrity,
            enable_ap2=enable_ap2,
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
    client_name: Optional[str] = None
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
    
    Returns:
        Dictionary with payment result including transaction_hash, evidence_cid, etc.
    """
    try:
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
        logger.info("DEBUG: Calling merchant_sdk.create_x402_payment_request...")
        try:
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
        except Exception as e:
            logger.error(f"DEBUG: Error creating payment request: {str(e)}")
            logger.error(f"DEBUG: Error type: {type(e).__name__}")
            # Check if it's the "extension not enabled" error
            if "extension not enabled" in str(e).lower() or "x402" in str(e).lower():
                logger.error("DEBUG: x402 extension is not enabled. Check SDK initialization.")
                logger.error("DEBUG: Ensure enable_payments=True when creating the SDK instance.")
            raise
        
        logger.info(f"Payment request created: {payment_request.request_id}")
        logger.info(f"DEBUG: Payment request type: {type(payment_request)}")
        logger.info(f"DEBUG: Payment request attributes: {dir(payment_request)[:10]}...")  # First 10 attributes
        
        # Client executes payment
        # Use provided client_name or try to get from SDK, fallback to default
        if not client_name:
            client_name = "ClientAgent"
            if hasattr(client_sdk, 'agent_name'):
                client_name = client_sdk.agent_name
            elif hasattr(client_sdk, '_agent_name'):
                client_name = client_sdk._agent_name
        
        logger.info(f"Executing payment from {client_name}...")
        logger.info("DEBUG: Calling client_sdk.execute_x402_crypto_payment...")
        logger.info(f"DEBUG: Payment request: {payment_request}")
        logger.info(f"DEBUG: Payer agent: {client_name}")
        logger.info(f"DEBUG: Service description: Purchase: {product_name}")
        
        try:
            payment_result = client_sdk.execute_x402_crypto_payment(
                payment_request=payment_request,
                payer_agent=client_name,
                service_description=f"Purchase: {product_name}"
            )
            logger.info("DEBUG: Payment execution completed successfully")
        except Exception as e:
            logger.error(f"DEBUG: Error executing payment: {str(e)}")
            logger.error(f"DEBUG: Error type: {type(e).__name__}")
            if "extension not enabled" in str(e).lower() or "x402" in str(e).lower():
                logger.error("DEBUG: x402 extension is not enabled for client SDK. Check SDK initialization.")
                logger.error("DEBUG: Ensure enable_payments=True when creating the client SDK instance.")
            raise
        
        logger.info(
            f"Payment executed successfully: "
            f"TX Hash={payment_result.transaction_hash}, "
            f"Amount=${payment_result.amount_paid}"
        )
        
        # Store evidence on IPFS
        evidence = {
            "negotiation_id": str(negotiation_id) if negotiation_id else None,
            "cart_id": cart_id,
            "product_name": product_name,
            "final_price": final_price,
            "payment_request": payment_request.__dict__ if hasattr(payment_request, '__dict__') else str(payment_request),
            "payment_result": payment_result.__dict__ if hasattr(payment_result, '__dict__') else str(payment_result),
            "timestamp": str(uuid.uuid1().time)
        }
        
        evidence_cid = merchant_sdk.store_evidence(evidence)
        logger.info(f"Evidence stored on IPFS: {evidence_cid}")
        
        return {
            "status": "success",
            "transaction_hash": payment_result.transaction_hash,
            "settlement_address": payment_result.settlement_address,
            "amount_paid": payment_result.amount_paid,
            "protocol_fee": payment_result.protocol_fee,
            "evidence_cid": evidence_cid,
            "cart_id": cart_id,
            "payment_request_id": payment_request.request_id if hasattr(payment_request, 'request_id') else None
        }
        
    except Exception as e:
        logger.error(f"Error executing x402 payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

