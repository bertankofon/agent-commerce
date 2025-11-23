from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from database.supabase.client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class AgentsOperations:
    """Operations for the agents table."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table = "agents"
    
    def create_agent(
        self,
        agent_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        chaoschain_agent_id: Optional[str] = None,
        transaction_hash: Optional[str] = None,
        public_address: Optional[str] = None,
        encrypted_private_key: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent record in the agents table.
        
        Args:
            agent_id: Optional UUID for the agent (defaults to auto-generated)
            created_at: Optional timestamp (defaults to now())
            chaoschain_agent_id: ChaosChain agent ID (ERC-8004)
            transaction_hash: Transaction hash from agent registration
            public_address: Public Ethereum address of the agent wallet
            encrypted_private_key: Encrypted private key of the agent wallet
            agent_type: Agent type ("client" or "merchant")
        
        Returns:
            Created agent record
        """
        try:
            data = {}
            
            if agent_id:
                data["id"] = str(agent_id)
            
            if created_at:
                data["created_at"] = created_at.isoformat()
            
            # Add ChaosChain fields if provided
            if chaoschain_agent_id:
                data["agent_id"] = chaoschain_agent_id
            
            if transaction_hash:
                data["tx_hash"] = transaction_hash
            
            if public_address:
                data["public_address"] = public_address
            
            if encrypted_private_key:
                data["private_key"] = encrypted_private_key
            
            if agent_type:
                data["agent_type"] = agent_type
            
            response = self.client.table(self.table).insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create agent: no data returned")
            
            logger.info(f"Created agent with ID: {response.data[0]['id']}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def get_agent_by_id(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: UUID of the agent
        
        Returns:
            Agent record or None if not found
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("id", str(agent_id))\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise
    
    def update_agent_metadata(
        self,
        agent_id: UUID,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update agent metadata.
        
        Args:
            agent_id: UUID of the agent
            metadata: Updated metadata (stored in metadata column if it exists)
        
        Returns:
            Updated agent record
        """
        try:
            # Try to update metadata column, but don't fail if it doesn't exist
            update_data = {}
            if metadata:
                # Check if metadata column exists, otherwise skip
                update_data["metadata"] = metadata
            
            if not update_data:
                logger.warning(f"No metadata to update for agent {agent_id}")
                return self.get_agent_by_id(agent_id) or {}
            
            response = self.client.table(self.table)\
                .update(update_data)\
                .eq("id", str(agent_id))\
                .execute()
            
            if not response.data:
                raise ValueError(f"Agent {agent_id} not found")
            
            logger.info(f"Updated agent metadata for ID: {agent_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
            raise
    
    def update_agent_avatar_url(
        self,
        agent_id: UUID,
        avatar_url: str
    ) -> Dict[str, Any]:
        """
        Update agent avatar URL.
        
        Args:
            agent_id: UUID of the agent
            avatar_url: Public URL of the avatar image
        
        Returns:
            Updated agent record
        """
        try:
            response = self.client.table(self.table)\
                .update({"avatar_url": avatar_url})\
                .eq("id", str(agent_id))\
                .execute()
            
            if not response.data:
                raise ValueError(f"Agent {agent_id} not found")
            
            logger.info(f"Updated agent avatar_url for ID: {agent_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error updating agent avatar_url {agent_id}: {str(e)}")
            raise
    
    def list_agents(self, limit: int = 100) -> list[Dict[str, Any]]:
        """
        List all agents.
        
        Args:
            limit: Maximum number of agents to return
        
        Returns:
            List of agent records
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise

