import os
import json
import tempfile
import logging
from typing import Dict, Optional
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

