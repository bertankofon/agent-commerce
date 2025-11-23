"""Operations for agent_chat_history table."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from database.supabase.client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class AgentChatHistoryOperations:
    """Operations for the agent_chat_history table."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table = "agent_chat_history"
    
    def create_chat_message(
        self,
        negotiation_id: UUID,
        round_number: int,
        sender_agent_id: UUID,
        receiver_agent_id: UUID,
        message: str,
        proposed_price: float,
        accept: bool = False,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat message record.
        
        Args:
            negotiation_id: UUID of the negotiation
            round_number: Round number in the negotiation (1-5)
            sender_agent_id: UUID of agent sending the message
            receiver_agent_id: UUID of agent receiving the message
            message: The message text
            proposed_price: Price proposed in this message
            accept: Whether this message accepts the offer
            reason: Reason for the decision (optional)
        
        Returns:
            Created chat message record
        """
        try:
            data = {
                "negotiation_id": str(negotiation_id),
                "round_number": round_number,
                "sender_agent_id": str(sender_agent_id),
                "receiver_agent_id": str(receiver_agent_id),
                "message": message,
                "proposed_price": proposed_price,
                "accept": accept
            }
            
            if reason:
                data["reason"] = reason
            
            response = self.client.table(self.table).insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create chat message: no data returned")
            
            logger.debug(f"Created chat message for negotiation {negotiation_id}, round {round_number}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating chat message: {str(e)}")
            raise
    
    def get_chat_history_by_negotiation(
        self,
        negotiation_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all chat messages for a negotiation, ordered by round and timestamp.
        
        Args:
            negotiation_id: UUID of the negotiation
        
        Returns:
            List of chat message records ordered by round_number and created_at
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("negotiation_id", str(negotiation_id))\
                .order("round_number", desc=False)\
                .order("created_at", desc=False)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting chat history for negotiation {negotiation_id}: {str(e)}")
            raise
    
    def get_chat_history_by_session(
        self,
        session_id: str,
        negotiations: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all chat messages for all negotiations in a session.
        
        Args:
            session_id: Shopping session ID
            negotiations: Optional pre-fetched negotiations list (to avoid circular import)
        
        Returns:
            List of chat message records
        """
        try:
            # Get negotiations if not provided
            if negotiations is None:
                from .negotiations import NegotiationsOperations
                negotiations_ops = NegotiationsOperations()
                negotiations = negotiations_ops.get_negotiations_by_session(session_id)
            
            if not negotiations:
                return []
            
            # Get chat history for all negotiations
            all_messages = []
            for negotiation in negotiations:
                messages = self.get_chat_history_by_negotiation(UUID(negotiation["id"]))
                all_messages.extend(messages)
            
            # Sort by negotiation created_at and round_number
            return sorted(
                all_messages,
                key=lambda x: (x.get("negotiation_id", ""), x.get("round_number", 0))
            )
            
        except Exception as e:
            logger.error(f"Error getting chat history for session {session_id}: {str(e)}")
            raise
    
    def list_chat_messages(
        self,
        agent_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List chat messages with optional filter by agent.
        
        Args:
            agent_id: Filter by sender or receiver agent
            limit: Maximum number of records
        
        Returns:
            List of chat message records
        """
        try:
            query = self.client.table(self.table).select("*")
            
            if agent_id:
                # Messages where agent is sender or receiver
                query = query.or_(f"sender_agent_id.eq.{agent_id},receiver_agent_id.eq.{agent_id}")
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error listing chat messages: {str(e)}")
            raise

