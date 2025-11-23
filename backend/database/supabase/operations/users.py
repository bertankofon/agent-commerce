from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from database.supabase.client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class UsersOperations:
    """Operations for the users table."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table = "users"
    
    def create_or_update_user(
        self,
        privy_user_id: str,
        wallet_address: str,
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a user record in the users table.
        Uses privy_user_id as unique identifier to prevent duplicates.
        
        Args:
            privy_user_id: Privy user ID (unique identifier)
            wallet_address: User's wallet address from Privy
            email: User's email (from Privy login)
            name: User's name (from Google/other providers)
        
        Returns:
            Created or updated user record
        """
        try:
            # First, check if user exists by privy_user_id
            existing_user = self.get_user_by_privy_id(privy_user_id)
            
            if existing_user:
                # Update existing user
                logger.info(f"Updating existing user with Privy ID: {privy_user_id}")
                return self.update_user(
                    user_id=existing_user["id"],
                    wallet_address=wallet_address,
                    email=email,
                    name=name
                )
            
            # Create new user
            data = {
                "privy_user_id": privy_user_id,
                "wallet_address": wallet_address
            }
            
            if email:
                data["email"] = email
            
            if name:
                data["name"] = name
            
            response = self.client.table(self.table).insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create user: no data returned")
            
            logger.info(f"Created user with ID: {response.data[0]['id']}, Privy ID: {privy_user_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating/updating user: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a user by database ID.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            User record or None if not found
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("id", str(user_id))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            raise
    
    def get_user_by_privy_id(self, privy_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by Privy user ID.
        
        Args:
            privy_user_id: Privy user ID
        
        Returns:
            User record or None if not found
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("privy_user_id", privy_user_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by Privy ID {privy_user_id}: {str(e)}")
            raise
    
    def get_user_by_wallet(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by wallet address.
        
        Args:
            wallet_address: Wallet address
        
        Returns:
            User record or None if not found
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("wallet_address", wallet_address)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by wallet {wallet_address}: {str(e)}")
            raise
    
    def update_user(
        self,
        user_id: UUID,
        wallet_address: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user details.
        
        Args:
            user_id: UUID of the user
            wallet_address: Updated wallet address
            email: Updated email
            name: Updated name
        
        Returns:
            Updated user record
        """
        try:
            update_data = {}
            
            if wallet_address:
                update_data["wallet_address"] = wallet_address
            
            if email:
                update_data["email"] = email
            
            if name:
                update_data["name"] = name
            
            if not update_data:
                logger.warning(f"No data to update for user {user_id}")
                return self.get_user_by_id(user_id) or {}
            
            response = self.client.table(self.table)\
                .update(update_data)\
                .eq("id", str(user_id))\
                .execute()
            
            if not response.data:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"Updated user ID: {user_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    def list_users(self, limit: int = 100) -> list[Dict[str, Any]]:
        """
        List all users.
        
        Args:
            limit: Maximum number of users to return
        
        Returns:
            List of user records
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            raise

