import os
import base64
import hashlib
import logging
from typing import Dict, Optional
from eth_account import Account
from web3 import Web3
from nacl import secret, utils

logger = logging.getLogger(__name__)


def create_wallet() -> Dict[str, str]:
    """
    Create a new Ethereum wallet.
    
    Returns:
        Dictionary with address and private_key (hex string)
    """
    try:
        acct = Account.create()
        # eth-account uses .key attribute (HexBytes), convert to hex string
        return {
            "address": acct.address,
            "private_key": acct.key.hex()
        }
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}")
        raise


def encrypt_pk(private_key: str, user_secret: str = None) -> str:
    """
    Encrypt a private key using NaCl secret box.
    
    Args:
        private_key: The private key to encrypt (hex string)
        user_secret: Secret key for encryption (defaults to env var)
    
    Returns:
        Base64-encoded encrypted private key
    """
    try:
        # Get user secret from parameter or environment variable
        if user_secret is None:
            user_secret = os.getenv("USER_SECRET_KEY")
            if not user_secret:
                raise ValueError(
                    "USER_SECRET_KEY must be set in environment variables or passed as parameter"
                )
        
        # Generate key from user secret using SHA256 hash
        # PyNaCl SecretBox needs a 32-byte key
        key = hashlib.sha256(user_secret.encode()).digest()
        
        # Ensure key is exactly 32 bytes (SecretBox.KEY_SIZE)
        if len(key) != secret.SecretBox.KEY_SIZE:
            key = key[:secret.SecretBox.KEY_SIZE]
        
        # Create secret box and encrypt
        box = secret.SecretBox(key)
        nonce = utils.random(secret.SecretBox.NONCE_SIZE)
        encrypted = box.encrypt(private_key.encode(), nonce)
        
        # Return base64-encoded encrypted data
        return base64.b64encode(encrypted).decode()
        
    except Exception as e:
        logger.error(f"Error encrypting private key: {str(e)}")
        raise


def decrypt_pk(encrypted_private_key: str, user_secret: str = None) -> str:
    """
    Decrypt a private key using NaCl secret box.
    Also handles plaintext private keys for backward compatibility.
    
    Args:
        encrypted_private_key: Base64-encoded encrypted private key OR plaintext hex string
        user_secret: Secret key for decryption (defaults to env var)
    
    Returns:
        Decrypted private key (hex string, without 0x prefix)
    """
    try:
        # DEBUG: Print what we received
        logger.info(f"DEBUG: Attempting to decrypt private key")
        logger.info(f"DEBUG: Key length: {len(encrypted_private_key) if encrypted_private_key else 0}")
        logger.info(f"DEBUG: Key preview (first 50 chars): {encrypted_private_key[:50] if encrypted_private_key else 'None'}...")
        logger.info(f"DEBUG: Key preview (last 50 chars): ...{encrypted_private_key[-50:] if encrypted_private_key and len(encrypted_private_key) > 50 else encrypted_private_key}")
        
        # First, check if it's already a plaintext private key
        # Private keys are 64 hex characters (32 bytes), optionally prefixed with 0x
        cleaned_key = encrypted_private_key.strip()
        if cleaned_key.startswith("0x"):
            cleaned_key = cleaned_key[2:]
        
        # Check if it looks like a plaintext hex private key (64 hex chars)
        if len(cleaned_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in cleaned_key):
            logger.info("DEBUG: Private key appears to be in plaintext format (64 hex chars), returning as-is")
            return cleaned_key.lower()  # Return lowercase hex without 0x prefix
        
        # If not plaintext, try to decrypt it
        # Get user secret from parameter or environment variable
        if user_secret is None:
            user_secret = os.getenv("USER_SECRET_KEY")
            if not user_secret:
                raise ValueError(
                    "USER_SECRET_KEY must be set in environment variables or passed as parameter"
                )
        
        logger.info(f"DEBUG: USER_SECRET_KEY length: {len(user_secret)}")
        logger.info(f"DEBUG: USER_SECRET_KEY preview: {user_secret[:10]}...")
        
        # Generate key from user secret using SHA256 hash
        key = hashlib.sha256(user_secret.encode()).digest()
        
        # Ensure key is exactly 32 bytes (SecretBox.KEY_SIZE)
        if len(key) != secret.SecretBox.KEY_SIZE:
            key = key[:secret.SecretBox.KEY_SIZE]
        
        # Decode base64-encoded encrypted data
        try:
            encrypted_data = base64.b64decode(encrypted_private_key.encode())
            logger.info(f"DEBUG: Successfully decoded base64, encrypted data length: {len(encrypted_data)}")
        except Exception as e:
            logger.error(f"DEBUG: Failed to base64 decode private key. Error: {str(e)}")
            # If base64 decode fails, check if it's a hex string
            if all(c in '0123456789abcdefABCDEF' for c in cleaned_key):
                logger.warning("DEBUG: Private key appears to be plaintext hex (not base64), returning as-is")
                return cleaned_key.lower()
            raise ValueError(f"Invalid encrypted private key format: {str(e)}")
        
        # Create secret box and decrypt
        box = secret.SecretBox(key)
        logger.info("DEBUG: Attempting decryption with SecretBox...")
        decrypted = box.decrypt(encrypted_data)
        logger.info(f"DEBUG: Decryption successful! Decrypted length: {len(decrypted)}")
        
        # Return decrypted private key as string (remove 0x if present)
        decrypted_str = decrypted.decode()
        if decrypted_str.startswith("0x"):
            decrypted_str = decrypted_str[2:]
        logger.info(f"DEBUG: Final decrypted key preview: {decrypted_str[:20]}...")
        return decrypted_str
        
    except Exception as e:
        logger.error(f"Error decrypting private key: {str(e)}")
        logger.error(f"DEBUG: Full error traceback:")
        import traceback
        logger.error(traceback.format_exc())
        raise


def send_eth_to_wallet(
    recipient_address: str,
    amount_eth: str,
    admin_private_key: Optional[str] = None,
    rpc_url: Optional[str] = None
) -> Dict[str, str]:
    """
    Send ETH from admin wallet to recipient wallet on Base network.
    
    Args:
        recipient_address: Address of the wallet to receive ETH
        amount_eth: Amount of ETH to send (as string, e.g., "0.001")
        admin_private_key: Private key of admin wallet (defaults to ADMIN_PRIVATE_KEY env var)
        rpc_url: Base network RPC URL (defaults to BASE_RPC_URL env var or public RPC)
    
    Returns:
        Dictionary with transaction_hash and status
    """
    try:
        # Get admin wallet from environment if not provided
        if admin_private_key is None:
            admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
            if not admin_private_key:
                raise ValueError(
                    "ADMIN_PRIVATE_KEY must be set in environment variables or passed as parameter"
                )
        
        # Get RPC URL from environment or use default Base Sepolia public RPC
        if rpc_url is None:
            rpc_url = os.getenv("BASE_RPC_URL")
            if not rpc_url:
                # Default to Base Sepolia public RPC (try multiple endpoints)
                # Primary: Official Base Sepolia endpoint
                # Fallback options available if primary fails
                rpc_url = "https://sepolia.base.org/"
                logger.info("Using default Base Sepolia public RPC")
        
        # Initialize Web3 connection with timeout
        # Try primary RPC, with fallback options
        w3 = None
        rpc_endpoints = [rpc_url]
        
        # If using default, add fallback endpoints
        if rpc_url == "https://sepolia.base.org/" or not os.getenv("BASE_RPC_URL"):
            rpc_endpoints.extend([
                "https://base-sepolia.gateway.tatum.io",
                "https://base-testnet.rpc.grove.city/v1/01fdb492",
                "https://base-sepolia-rpc.publicnode.com"
            ])
        
        connection_error = None
        for endpoint in rpc_endpoints:
            try:
                logger.info(f"Attempting to connect to Base Sepolia RPC: {endpoint}")
                w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 30}))
                
                # Test connection by making an actual RPC call (more reliable than is_connected())
                try:
                    chain_id = w3.eth.chain_id
                    if chain_id == 84532:  # Base Sepolia chain ID
                        logger.info(f"✓ Successfully connected to Base Sepolia RPC: {endpoint} (Chain ID: {chain_id})")
                        break
                    else:
                        connection_error = f"Wrong chain ID {chain_id} for {endpoint} (expected 84532)"
                        logger.warning(connection_error)
                        w3 = None
                except Exception as chain_test_error:
                    # If chain_id check fails, try is_connected() as fallback
                    if w3.is_connected():
                        logger.info(f"✓ Successfully connected to Base Sepolia RPC: {endpoint}")
                        break
                    else:
                        connection_error = f"Connection test failed for {endpoint}: {str(chain_test_error)}"
                        logger.warning(connection_error)
                        w3 = None
            except Exception as e:
                connection_error = f"Error connecting to {endpoint}: {str(e)}"
                logger.warning(connection_error)
                w3 = None
                continue
        
        if w3 is None:
            raise ConnectionError(
                f"Failed to connect to any Base Sepolia RPC endpoint. "
                f"Tried: {', '.join(rpc_endpoints)}. "
                f"Last error: {connection_error}. "
                f"Please set BASE_RPC_URL in environment with a valid endpoint."
            )
        
        # Get admin account
        admin_account = Account.from_key(admin_private_key)
        admin_address = admin_account.address
        
        # Validate recipient address
        if not w3.is_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")
        
        # Convert amount to Wei
        amount_wei = w3.to_wei(float(amount_eth), 'ether')
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(admin_address)
        
        # Build transaction
        transaction = {
            'to': recipient_address,
            'value': amount_wei,
            'gas': 21000,  # Standard ETH transfer gas limit
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 84532  # Base Sepolia chain ID
        }
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, admin_private_key)
        
        # Send transaction
        logger.info(
            f"Sending {amount_eth} ETH from {admin_address} to {recipient_address} "
            f"on Base Sepolia (Chain ID: 84532)"
        )
        # Use raw_transaction (snake_case) for web3.py v6+
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for transaction receipt
        logger.info(f"Transaction sent, waiting for confirmation. Hash: {tx_hash.hex()}")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if tx_receipt.status == 1:
            logger.info(
                f"✓ Successfully sent {amount_eth} ETH to {recipient_address}. "
                f"Transaction: {tx_hash.hex()}"
            )
            return {
                "transaction_hash": tx_hash.hex(),
                "status": "success",
                "from": admin_address,
                "to": recipient_address,
                "amount_eth": amount_eth,
                "block_number": tx_receipt.blockNumber
            }
        else:
            raise Exception(f"Transaction failed with status: {tx_receipt.status}")
            
    except Exception as e:
        logger.error(f"Error sending ETH: {str(e)}", exc_info=True)
        raise

