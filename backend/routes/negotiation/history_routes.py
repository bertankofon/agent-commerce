"""
Negotiation History Routes

Endpoints to fetch negotiation history and chat messages.
"""

import logging
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
from uuid import UUID

from database.supabase.client import get_supabase_client

router = APIRouter(prefix="/negotiation", tags=["negotiation"])
logger = logging.getLogger(__name__)


def validate_agent_id(agent_id: str) -> UUID:
    """Validate and convert agent_id string to UUID."""
    try:
        return UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_id format: {agent_id}"
        )


@router.get("/history/agent/{agent_id}")
async def get_agent_negotiation_history(agent_id: str, limit: int = 50):
    """
    Get negotiation history for a specific agent (client or merchant).
    Returns negotiations with chat history.
    """
    try:
        supabase = get_supabase_client()
        agent_uuid = validate_agent_id(agent_id)
        
        # Get negotiations where agent is either client or merchant
        response = supabase.table("negotiations")\
            .select("""
                *,
                client_agent:client_agent_id(id, name, agent_type, category),
                merchant_agent:merchant_agent_id(id, name, agent_type, category),
                product:product_id(id, name, price, image_url)
            """)\
            .or_(f"client_agent_id.eq.{agent_uuid},merchant_agent_id.eq.{agent_uuid}")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        negotiations = response.data or []
        
        # For each negotiation, fetch chat history
        for negotiation in negotiations:
            chat_response = supabase.table("agent_chat_history")\
                .select("""
                    *,
                    sender:sender_agent_id(id, name),
                    receiver:receiver_agent_id(id, name)
                """)\
                .eq("negotiation_id", negotiation["id"])\
                .order("round_number", desc=False)\
                .execute()
            
            negotiation["chat_history"] = chat_response.data or []
        
        return {
            "success": True,
            "agent_id": agent_id,
            "negotiations": negotiations,
            "count": len(negotiations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching negotiation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch negotiation history: {str(e)}"
        )


@router.get("/history/product/{product_id}")
async def get_product_negotiation_history(product_id: str, limit: int = 50):
    """
    Get all negotiations for a specific product.
    """
    try:
        supabase = get_supabase_client()
        
        try:
            product_uuid = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_id format: {product_id}"
            )
        
        response = supabase.table("negotiations")\
            .select("""
                *,
                client_agent:client_agent_id(id, name, agent_type),
                merchant_agent:merchant_agent_id(id, name, agent_type),
                product:product_id(id, name, price)
            """)\
            .eq("product_id", str(product_uuid))\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        negotiations = response.data or []
        
        # Add chat history for each
        for negotiation in negotiations:
            chat_response = supabase.table("agent_chat_history")\
                .select("""
                    *,
                    sender:sender_agent_id(id, name),
                    receiver:receiver_agent_id(id, name)
                """)\
                .eq("negotiation_id", negotiation["id"])\
                .order("round_number", desc=False)\
                .execute()
            
            negotiation["chat_history"] = chat_response.data or []
        
        return {
            "success": True,
            "product_id": product_id,
            "negotiations": negotiations,
            "count": len(negotiations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product negotiation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch product negotiation history: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_negotiation_session(session_id: str):
    """
    Get all negotiations in a shopping session.
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("negotiations")\
            .select("""
                *,
                client_agent:client_agent_id(id, name, agent_type),
                merchant_agent:merchant_agent_id(id, name, agent_type),
                product:product_id(id, name, price, image_url)
            """)\
            .eq("session_id", session_id)\
            .order("created_at", desc=False)\
            .execute()
        
        negotiations = response.data or []
        
        # Add chat history
        for negotiation in negotiations:
            chat_response = supabase.table("agent_chat_history")\
                .select("""
                    *,
                    sender:sender_agent_id(id, name),
                    receiver:receiver_agent_id(id, name)
                """)\
                .eq("negotiation_id", negotiation["id"])\
                .order("round_number", desc=False)\
                .execute()
            
            negotiation["chat_history"] = chat_response.data or []
        
        return {
            "success": True,
            "session_id": session_id,
            "negotiations": negotiations,
            "count": len(negotiations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching session negotiations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch session negotiations: {str(e)}"
        )


@router.post("/list/user/negotiations")
async def get_user_negotiations(request: Dict[str, Any] = Body(...), limit: int = 50):
    """
    Get all negotiations for a specific user.
    Returns negotiations where the client_agent belongs to the user.
    """
    try:
        supabase = get_supabase_client()
        
        # Get user_id from request body
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required in request body"
            )
        
        # Validate user_id format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user_id format: {user_id}"
            )
        
        # First, get all client agents for this user
        agents_response = supabase.table("agents")\
            .select("id")\
            .eq("user_id", str(user_uuid))\
            .eq("agent_type", "client")\
            .execute()
        
        client_agent_ids = [agent["id"] for agent in (agents_response.data or [])]
        
        if not client_agent_ids:
            # No client agents for this user, return empty list
            return {
                "success": True,
                "user_id": user_id,
                "negotiations": [],
                "count": 0
            }
        
        # Get negotiations where client_agent_id is in the list
        # Build OR query for multiple agent IDs
        or_conditions = ",".join([f"client_agent_id.eq.{agent_id}" for agent_id in client_agent_ids])
        
        response = supabase.table("negotiations")\
            .select("""
                id,
                session_id,
                client_agent_id,
                merchant_agent_id,
                product_id,
                initial_price,
                final_price,
                negotiation_percentage,
                budget,
                agreed,
                status,
                payment_successful,
                txn_hash,
                created_at,
                updated_at,
                client_agent:client_agent_id(id, name, agent_type, category),
                merchant_agent:merchant_agent_id(id, name, agent_type, category)
            """)\
            .or_(or_conditions)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        negotiations = response.data or []
        
        # Add chat history for each negotiation
        for negotiation in negotiations:
            chat_response = supabase.table("agent_chat_history")\
                .select("""
                    *,
                    sender:sender_agent_id(id, name),
                    receiver:receiver_agent_id(id, name)
                """)\
                .eq("negotiation_id", negotiation["id"])\
                .order("round_number", desc=False)\
                .execute()
            
            negotiation["chat_history"] = chat_response.data or []
        
        return {
            "success": True,
            "user_id": user_id,
            "negotiations": negotiations,
            "count": len(negotiations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user negotiations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user negotiations: {str(e)}"
        )

