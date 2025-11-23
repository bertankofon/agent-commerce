import os
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from uuid import UUID

from .models import (
    NegotiateAndPayRequest,
    NegotiateAndPayResponse,
    SingleNegotiationRequest,
    SingleNegotiationResponse
)
from database.supabase.operations import AgentsOperations
from database.supabase.client import get_supabase_client
from utils.wallet import decrypt_pk
from utils.chaoschain import get_agent_sdk, execute_x402_payment
from chaoschain_sdk import AgentRole
from services.shopping_service import ShoppingService

router = APIRouter(prefix="/negotiation", tags=["negotiation"])
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions for Negotiate and Pay
# ============================================================================
#
# PAYMENT IMPLEMENTATION NOTES:
# -----------------------------
# The ChaosChain SDK's A2A-x402 extension has a design issue where calling
# `execute_x402_crypto_payment` on an SDK instance uses that instance's
# agent_name as the recipient (to_agent).
#
# Our solution (implemented in utils/chaoschain.py):
# 1. Merchant SDK creates the x402 payment request (has correct settlement_address)
# 2. Client SDK's wallet_manager is monkey-patched to recognize merchant's address
# 3. Client SDK's PaymentManager is called directly (bypassing A2A extension)
# 4. This ensures: from_agent=client, to_agent=merchant (correct flow!)
#
# See execute_x402_payment() in utils/chaoschain.py for full implementation.
# ============================================================================

def validate_agent_id(agent_id: str) -> UUID:
    """Validate and convert agent_id string to UUID."""
    try:
        return UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_id format: {agent_id}"
        )


def validate_client_agent(agent_id: UUID, agents_ops: AgentsOperations) -> Dict[str, Any]:
    """Validate that agent exists and is a client agent."""
    client_agent = agents_ops.get_agent_by_id(agent_id)
    if not client_agent:
        raise HTTPException(
            status_code=404,
            detail=f"Client agent {agent_id} not found"
        )
    
    if client_agent.get("agent_type") != "client":
        raise HTTPException(
            status_code=400,
            detail=f"Agent {agent_id} is not a client agent"
        )
    
    return client_agent


def search_products_by_query(supabase_client, product_query: str) -> List[Dict[str, Any]]:
    """Search for products by query (name/description or UUID)."""
    products = []
    
    try:
        # Search by name/description
        response = supabase_client.table("products")\
            .select("*, agents(*)")\
            .or_(f"name.ilike.%{product_query}%,description.ilike.%{product_query}%")\
            .limit(50)\
            .execute()
        
        products = response.data or []
        
        # If no results, try treating query as UUID
        if not products:
            try:
                product_uuid = UUID(product_query)
                response = supabase_client.table("products")\
                    .select("*, agents(*)")\
                    .eq("id", str(product_uuid))\
                    .execute()
                products = response.data or []
            except ValueError:
                pass  # Not a valid UUID
    
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching products: {str(e)}"
        )
    
    return products


def filter_products_with_merchants(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter products that have associated merchant agents."""
    return [p for p in products if p.get("agent_id")]


def get_agent_metadata(agent: Dict[str, Any]) -> Dict[str, Any]:
    """Extract agent metadata with defaults."""
    metadata = agent.get("metadata", {})
    agent_id = agent.get("id")
    
    return {
        "name": metadata.get("name", f"Agent_{str(agent_id)[:8]}"),
        "domain": metadata.get("domain", f"agent_{str(agent_id)[:8]}.example.com"),
        "role_str": metadata.get("chaoschain_config", {}).get("agent_role", "CLIENT" if agent.get("agent_type") == "client" else "SERVER")
    }


def parse_agent_role(role_str: str, default_role: AgentRole) -> AgentRole:
    """Parse agent role string to AgentRole enum."""
    try:
        return getattr(AgentRole, role_str.upper(), default_role)
    except (AttributeError, TypeError):
        return default_role


def initialize_agent_sdks(
    client_agent: Dict[str, Any],
    merchant_agent: Dict[str, Any]
) -> tuple:
    """Initialize SDKs for client and merchant agents."""
    from eth_account import Account
    
    # Get encrypted private keys
    client_encrypted_pk = client_agent.get("private_key")
    merchant_encrypted_pk = merchant_agent.get("private_key")
    
    if not client_encrypted_pk or not merchant_encrypted_pk:
        raise ValueError("One or both agents missing encrypted private keys")
    
    # Decrypt private keys
    client_private_key = decrypt_pk(client_encrypted_pk)
    merchant_private_key = decrypt_pk(merchant_encrypted_pk)
    
    # Verify private keys match public addresses
    client_public_address = client_agent.get("public_address")
    merchant_public_address = merchant_agent.get("public_address")
    
    if client_public_address:
        client_derived_address = Account.from_key(client_private_key).address
        if client_derived_address.lower() != client_public_address.lower():
            raise ValueError(
                f"Client private key doesn't match public_address! "
                f"Expected: {client_public_address}, "
                f"Derived from key: {client_derived_address}"
            )
        logger.info(f"✓ Client private key verified: {client_derived_address}")
    
    if merchant_public_address:
        merchant_derived_address = Account.from_key(merchant_private_key).address
        if merchant_derived_address.lower() != merchant_public_address.lower():
            raise ValueError(
                f"Merchant private key doesn't match public_address! "
                f"Expected: {merchant_public_address}, "
                f"Derived from key: {merchant_derived_address}"
            )
        logger.info(f"✓ Merchant private key verified: {merchant_derived_address}")
    
    # Verify addresses are different
    if client_public_address and merchant_public_address:
        if client_public_address.lower() == merchant_public_address.lower():
            raise ValueError(
                f"CRITICAL: Client and Merchant have the SAME public_address! "
                f"Address: {client_public_address}. "
                f"This means they're the same agent - payment cannot proceed."
            )
        logger.info(f"✓ Client and Merchant addresses are different")
    
    # Get agent metadata
    client_meta = get_agent_metadata(client_agent)
    merchant_meta = get_agent_metadata(merchant_agent)
    
    # Parse agent roles
    client_role = parse_agent_role(client_meta["role_str"], AgentRole.CLIENT)
    merchant_role = parse_agent_role(merchant_meta["role_str"], AgentRole.SERVER)
    
    # Initialize SDKs
    logger.info(f"Initializing Client SDK: {client_meta['name']} ({client_public_address or 'N/A'})")
    client_sdk = get_agent_sdk(
        agent_name=client_meta["name"],
        agent_domain=client_meta["domain"],
        private_key=client_private_key,
        agent_role=client_role,
        enable_payments=True
    )
    
    logger.info(f"Initializing Merchant SDK: {merchant_meta['name']} ({merchant_public_address or 'N/A'})")
    merchant_sdk = get_agent_sdk(
        agent_name=merchant_meta["name"],
        agent_domain=merchant_meta["domain"],
        private_key=merchant_private_key,
        agent_role=merchant_role,
        enable_payments=True
    )
    
    return client_sdk, merchant_sdk


def cleanup_temp_wallet_files(*sdks) -> None:
    """Deprecated: SDK now manages wallets internally via external_private_key."""
    # No cleanup needed - SDK handles wallet management
    pass


async def execute_payment_for_deal(
    client_agent: Dict[str, Any],
    merchant_agent: Dict[str, Any],
    best_offer: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, Any]:
    """Execute x402 payment for a finalized deal."""
    if dry_run:
        return {
            "status": "dry_run",
            "message": "Payment execution skipped (dry run mode)",
            "would_pay": best_offer.get("negotiated_price")
        }
    
    try:
        # Initialize SDKs
        client_sdk, merchant_sdk = initialize_agent_sdks(client_agent, merchant_agent)
        
        try:
            # Get negotiation ID if available
            negotiation_id = None
            if best_offer.get("negotiation_id"):
                negotiation_id = UUID(best_offer.get("negotiation_id"))
            
            # Get client name and addresses for payment
            client_meta = get_agent_metadata(client_agent)
            client_public_address = client_agent.get("public_address")
            merchant_public_address = merchant_agent.get("public_address")
            
            if not merchant_public_address:
                raise ValueError("Merchant agent missing public_address field - required for payment")
            
            # Execute payment
            payment_result = execute_x402_payment(
                client_sdk=client_sdk,
                merchant_sdk=merchant_sdk,
                product_name=best_offer.get("product_name"),
                final_price=best_offer.get("negotiated_price"),
                negotiation_id=negotiation_id,
                client_name=client_meta["name"],
                client_public_address=client_public_address,
                merchant_public_address=merchant_public_address
            )
            
            return payment_result
        
        finally:
            # Always cleanup temp wallet files
            cleanup_temp_wallet_files(client_sdk, merchant_sdk)
    
    except Exception as e:
        logger.error(f"Error executing payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def run_negotiations(
    client_agent_id: UUID,
    product_query: str,
    products: List[Dict[str, Any]],
    budget: Optional[float],
    rounds: int
) -> Dict[str, Any]:
    """Run shopping negotiations for products."""
    shopping_service = ShoppingService()
    
    result = await shopping_service.start_shopping(
        client_agent_id=client_agent_id,
        product_query=product_query,
        budget=budget,
        products=products,
        max_rounds=rounds
    )
    
    return result


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/negotiate-and-pay", response_model=NegotiateAndPayResponse)
async def negotiate_and_pay(request: NegotiateAndPayRequest):
    """
    Negotiate for products matching a query and execute payment if successful.
    
    Flow:
    1. Validate client agent exists
    2. Search for products matching query
    3. Negotiate with all merchants selling those products
    4. Select best offer
    5. Execute x402 payment if deal is successful
    
    Args:
        request: NegotiateAndPayRequest with agent_id, product_query, etc.
    
    Returns:
        NegotiateAndPayResponse with negotiation and payment results
    """
    try:
        # Validate and get client agent
        client_agent_id = validate_agent_id(request.agent_id)
        agents_ops = AgentsOperations()
        client_agent = validate_client_agent(client_agent_id, agents_ops)
        
        # Search for products
        logger.info(f"Searching for products matching: {request.product_query}")
        supabase_client = get_supabase_client()
        products = search_products_by_query(supabase_client, request.product_query)
        
        if not products:
            return NegotiateAndPayResponse(
                status="no_products_found",
                client_agent_id=str(client_agent_id),
                product_query=request.product_query,
                total_products_found=0,
                total_negotiations=0,
                error=f"No products found for query: {request.product_query}"
            )
        
        # Filter products with merchants
        products_with_merchants = filter_products_with_merchants(products)
        
        if not products_with_merchants:
            return NegotiateAndPayResponse(
                status="no_merchants",
                client_agent_id=str(client_agent_id),
                product_query=request.product_query,
                total_products_found=len(products),
                total_negotiations=0,
                error="No products have associated merchant agents"
            )
        
        logger.info(f"Found {len(products_with_merchants)} products with merchants")
        
        # Run negotiations
        negotiation_result = await run_negotiations(
            client_agent_id=client_agent_id,
            product_query=request.product_query,
            products=products_with_merchants,
            budget=request.budget,
            rounds=request.rounds or 5
        )
        
        # Check if we have a successful deal and execute payment
        best_offer = negotiation_result.get("best_offer")
        payment_result = None
        
        if best_offer and best_offer.get("agreed") and negotiation_result.get("deal_successful"):
            logger.info(f"Executing payment for deal: ${best_offer.get('negotiated_price', 0):.2f}")
            
            # Get merchant agent
            merchant_agent_id = UUID(best_offer.get("merchant_agent_id"))
            merchant_agent = agents_ops.get_agent_by_id(merchant_agent_id)
            
            if not merchant_agent:
                payment_result = {
                    "status": "error",
                    "error": f"Merchant agent {merchant_agent_id} not found"
                }
            else:
                payment_result = await execute_payment_for_deal(
                    client_agent=client_agent,
                    merchant_agent=merchant_agent,
                    best_offer=best_offer,
                    dry_run=request.dry_run
                )
        
        # Prepare response
        return NegotiateAndPayResponse(
            status=negotiation_result.get("status", "completed"),
            client_agent_id=str(client_agent_id),
            product_query=request.product_query,
            session_id=negotiation_result.get("session_id"),
            total_products_found=len(products),
            total_negotiations=negotiation_result.get("total_merchants_contacted", 0),
            best_offer=best_offer,
            payment_result=payment_result,
            results_by_product=[negotiation_result]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in negotiate_and_pay endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/single-negotiation", response_model=SingleNegotiationResponse)
async def single_negotiation(request: SingleNegotiationRequest):
    """
    Direct negotiation between specific client and merchant agents.
    
    Flow:
    1. Validate both agents exist
    2. Get product details
    3. Run 5-round negotiation between the two agents
    4. Execute x402 payment if deal is successful
    
    Args:
        request: SingleNegotiationRequest with client_id, merchant_id, product_id, budget
    
    Returns:
        SingleNegotiationResponse with negotiation results and payment status
    """
    try:
        # Validate agent IDs
        client_agent_id = validate_agent_id(request.client_agent_id)
        merchant_agent_id = validate_agent_id(request.merchant_agent_id)
        
        agents_ops = AgentsOperations()
        
        # Get and validate client agent
        client_agent = validate_client_agent(client_agent_id, agents_ops)
        
        # Get merchant agent
        merchant_agent = agents_ops.get_agent_by_id(merchant_agent_id)
        if not merchant_agent:
            raise HTTPException(
                status_code=404,
                detail=f"Merchant agent {merchant_agent_id} not found"
            )
        
        if merchant_agent.get("agent_type") != "merchant":
            raise HTTPException(
                status_code=400,
                detail=f"Agent {merchant_agent_id} is not a merchant agent"
            )
        
        # Get product
        supabase_client = get_supabase_client()
        try:
            product_uuid = UUID(request.product_id)
            response = supabase_client.table("products")\
                .select("*, agents(*)")\
                .eq("id", str(product_uuid))\
                .execute()
            
            products = response.data or []
            if not products:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {request.product_id} not found"
                )
            
            product = products[0]
            
            # Verify product belongs to merchant
            if str(product.get("agent_id")) != str(merchant_agent_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {request.product_id} does not belong to merchant {merchant_agent_id}"
                )
                
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_id format: {request.product_id}"
            )
        
        logger.info(
            f"Starting single negotiation: Client {client_agent_id} ↔ "
            f"Merchant {merchant_agent_id} for product {product.get('name')}"
        )
        
        # Run negotiation using shopping service
        shopping_service = ShoppingService()
        
        negotiation_result = await shopping_service.start_shopping(
            client_agent_id=client_agent_id,
            product_query=product.get("name", ""),
            budget=request.budget,
            products=[product],
            max_rounds=request.rounds or 5
        )
        
        # Extract negotiation details
        best_offer = negotiation_result.get("best_offer")
        negotiation_history = negotiation_result.get("offers", [])
        
        # Prepare base response
        response_data = {
            "status": "completed",
            "client_agent_id": str(client_agent_id),
            "merchant_agent_id": str(merchant_agent_id),
            "product_id": request.product_id,
            "product_name": product.get("name"),
            "initial_price": product.get("price"),
            "final_price": best_offer.get("negotiated_price") if best_offer else None,
            "agreed": best_offer.get("agreed", False) if best_offer else False,
            "negotiation_rounds": negotiation_result.get("total_merchants_contacted", 0),
            "negotiation_history": negotiation_history,
            "payment_result": None,
            "error": None
        }
        
        # Execute payment if deal was successful and not dry run
        if best_offer and best_offer.get("agreed") and not request.dry_run:
            if best_offer.get("negotiated_price", float('inf')) <= request.budget:
                logger.info(f"Executing payment for negotiated price: ${best_offer.get('negotiated_price'):.2f}")
                
                payment_result = await execute_payment_for_deal(
                    client_agent=client_agent,
                    merchant_agent=merchant_agent,
                    best_offer=best_offer,
                    dry_run=request.dry_run
                )
                
                response_data["payment_result"] = payment_result
                
                if payment_result.get("status") == "success":
                    response_data["status"] = "completed_with_payment"
                else:
                    response_data["status"] = "negotiation_success_payment_failed"
            else:
                response_data["status"] = "negotiation_success_over_budget"
                response_data["error"] = f"Final price ${best_offer.get('negotiated_price'):.2f} exceeds budget ${request.budget:.2f}"
        elif request.dry_run and best_offer and best_offer.get("agreed"):
            response_data["status"] = "negotiation_success_dry_run"
            response_data["payment_result"] = {
                "status": "dry_run",
                "message": "Payment skipped (dry run mode)"
            }
        elif not best_offer or not best_offer.get("agreed"):
            response_data["status"] = "negotiation_failed"
            response_data["error"] = "No agreement reached"
        
        return SingleNegotiationResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in single_negotiation endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

