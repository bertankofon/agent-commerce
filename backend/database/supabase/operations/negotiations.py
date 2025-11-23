"""Operations for negotiations table."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from database.supabase.client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class NegotiationsOperations:
    """Operations for the negotiations table."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table = "negotiations"
    
    def create_negotiation(
        self,
        session_id: str,
        client_agent_id: UUID,
        merchant_agent_id: UUID,
        product_id: UUID,
        initial_price: float,
        negotiation_percentage: Optional[float] = None,
        budget: Optional[float] = None,
        status: str = "in_progress",
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a new negotiation record.
        
        Args:
            session_id: Shopping session ID
            client_agent_id: UUID of client agent
            merchant_agent_id: UUID of merchant agent
            product_id: UUID of product
            initial_price: Initial product price
            negotiation_percentage: Max discount percentage for merchant
            budget: Client's budget limit
            status: Negotiation status (in_progress, agreed, rejected, failed)
            user_id: UUID of the user who owns the client agent
        
        Returns:
            Created negotiation record
        """
        try:
            data = {
                "session_id": session_id,
                "client_agent_id": str(client_agent_id),
                "merchant_agent_id": str(merchant_agent_id),
                "product_id": str(product_id),
                "initial_price": initial_price,
                "status": status
            }
            
            if negotiation_percentage is not None:
                data["negotiation_percentage"] = negotiation_percentage
            
            if budget is not None:
                data["budget"] = budget
            
            if user_id is not None:
                data["user_id"] = str(user_id)
            
            response = self.client.table(self.table).insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create negotiation: no data returned")
            
            logger.info(f"Created negotiation with ID: {response.data[0]['id']}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating negotiation: {str(e)}")
            raise
    
    def update_negotiation(
        self,
        negotiation_id: UUID,
        final_price: Optional[float] = None,
        agreed: Optional[bool] = None,
        status: Optional[str] = None,
        txh_hash: Optional[str] = None,
        payment_successful: Optional[bool] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Update a negotiation record with final results.
        
        Args:
            negotiation_id: UUID of the negotiation
            final_price: Final negotiated price
            agreed: Whether agreement was reached
            status: Final status (agreed, rejected, failed)
            txh_hash: Transaction hash from successful x402 payment
            payment_successful: Whether the x402 payment was successfully executed
            user_id: UUID of the user who owns the client agent
        
        Returns:
            Updated negotiation record
        """
        try:
            update_data = {}
            
            if final_price is not None:
                update_data["final_price"] = final_price
            
            if agreed is not None:
                update_data["agreed"] = agreed
            
            if status:
                update_data["status"] = status
            
            if txh_hash is not None:
                update_data["txh_hash"] = txh_hash
            
            if payment_successful is not None:
                update_data["payment_successful"] = payment_successful
            
            if user_id is not None:
                update_data["user_id"] = str(user_id)
            
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            if not update_data:
                logger.warning(f"No data to update for negotiation {negotiation_id}")
                return self.get_negotiation_by_id(negotiation_id) or {}
            
            response = self.client.table(self.table)\
                .update(update_data)\
                .eq("id", str(negotiation_id))\
                .execute()
            
            if not response.data:
                raise ValueError(f"Negotiation {negotiation_id} not found")
            
            logger.info(f"Updated negotiation {negotiation_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error updating negotiation {negotiation_id}: {str(e)}")
            raise
    
    def get_negotiation_by_id(self, negotiation_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a negotiation by ID.
        
        Args:
            negotiation_id: UUID of the negotiation
        
        Returns:
            Negotiation record or None if not found
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("id", str(negotiation_id))\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error getting negotiation {negotiation_id}: {str(e)}")
            raise
    
    def get_negotiations_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all negotiations for a shopping session.
        
        Args:
            session_id: Shopping session ID
        
        Returns:
            List of negotiation records
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting negotiations for session {session_id}: {str(e)}")
            raise
    
    def list_negotiations(
        self,
        client_agent_id: Optional[UUID] = None,
        merchant_agent_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List negotiations with optional filters.
        
        Args:
            client_agent_id: Filter by client agent
            merchant_agent_id: Filter by merchant agent
            limit: Maximum number of records
        
        Returns:
            List of negotiation records
        """
        try:
            query = self.client.table(self.table).select("*")
            
            if client_agent_id:
                query = query.eq("client_agent_id", str(client_agent_id))
            
            if merchant_agent_id:
                query = query.eq("merchant_agent_id", str(merchant_agent_id))
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error listing negotiations: {str(e)}")
            raise

