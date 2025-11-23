#!/usr/bin/env python3
"""
Test script for agent-to-agent negotiation.

This script directly tests the negotiation flow between ShoppingAgent (client) 
and MerchantAgent (seller) using real data from Supabase.

Usage:
    python scripts/test_negotiation.py

Requirements:
    - Set environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY
    - Have at least one client agent and one merchant agent in the agents table
    - Have at least one product in the products table
"""

import os
import sys
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from uuid import UUID
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase.client import get_supabase_client
from database.supabase.operations import NegotiationsOperations, AgentChatHistoryOperations
from agents.shopping_agent import ShoppingAgent
from agents.merchant_agent import MerchantAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_client_agents(supabase_client) -> List[Dict[str, Any]]:
    """Get client agents from Supabase."""
    try:
        response = supabase_client.table("agents")\
            .select("*")\
            .eq("agent_type", "client")\
            .limit(10)\
            .execute()
        
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching client agents: {str(e)}")
        return []


def get_merchant_agents(supabase_client) -> List[Dict[str, Any]]:
    """Get merchant agents from Supabase."""
    try:
        response = supabase_client.table("agents")\
            .select("*")\
            .eq("agent_type", "merchant")\
            .limit(10)\
            .execute()
        
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching merchant agents: {str(e)}")
        return []


def get_products(supabase_client, product_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get products from Supabase, optionally filtered by query."""
    try:
        query = supabase_client.table("products").select("*, agents(*)")
        
        if product_query:
            # Search in name and description
            query = query.or_(f"name.ilike.%{product_query}%,description.ilike.%{product_query}%")
        
        response = query.limit(10).execute()
        
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return []


async def run_negotiation(
    client_agent_data: Dict[str, Any],
    merchant_agent_data: Dict[str, Any],
    product_data: Dict[str, Any],
    budget: Optional[float] = None,
    session_id: Optional[str] = None,
    negotiations_ops: Optional[NegotiationsOperations] = None,
    chat_history_ops: Optional[AgentChatHistoryOperations] = None
) -> Dict[str, Any]:
    """
    Run a negotiation between client and merchant agents.
    
    Args:
        client_agent_data: Client agent data from database
        merchant_agent_data: Merchant agent data from database
        product_data: Product data from database
        budget: Optional budget limit
    
    Returns:
        Dictionary with negotiation results
    """
    try:
        # Extract agent info
        client_id = client_agent_data["id"]
        client_metadata = client_agent_data.get("metadata", {})
        client_name = client_metadata.get("name", f"Client_{client_id[:8]}")
        
        merchant_id = merchant_agent_data["id"]
        merchant_metadata = merchant_agent_data.get("metadata", {})
        merchant_name = merchant_metadata.get("name", f"Merchant_{merchant_id[:8]}")
        
        product_name = product_data.get("name", "Unknown Product")
        initial_price = float(product_data.get("price", 0))
        
        print("\n" + "="*80)
        print(f"NEGOTIATION TEST")
        print("="*80)
        print(f"Client Agent: {client_name} (ID: {client_id})")
        print(f"Merchant Agent: {merchant_name} (ID: {merchant_id})")
        print(f"Product: {product_name}")
        print(f"Initial Price: ${initial_price:.2f}")
        if budget:
            print(f"Budget: ${budget:.2f}")
        print("="*80 + "\n")
        
        # Get negotiation_percentage from product
        negotiation_percentage = product_data.get("negotiation_percentage")
        if negotiation_percentage is not None:
            negotiation_percentage = float(negotiation_percentage)
        
        # Create negotiation record in database
        negotiation_id = None
        if session_id and negotiations_ops:
            try:
                negotiation_record = negotiations_ops.create_negotiation(
                    session_id=session_id,
                    client_agent_id=UUID(client_id),
                    merchant_agent_id=UUID(merchant_id),
                    product_id=UUID(product_data.get("id")),
                    initial_price=initial_price,
                    negotiation_percentage=negotiation_percentage,
                    budget=budget,
                    status="in_progress"
                )
                negotiation_id = UUID(negotiation_record["id"])
                print(f"✓ Created negotiation record (ID: {negotiation_id})")
            except Exception as e:
                logger.error(f"Failed to create negotiation record: {str(e)}")
                print(f"⚠ Warning: Could not create negotiation record: {str(e)}")
        
        # Initialize agents
        print("Initializing agents...")
        shopping_agent = ShoppingAgent(
            agent_id=client_id,
            agent_name=client_name
        )
        
        merchant_agent = MerchantAgent(
            agent_id=merchant_id,
            agent_name=merchant_name,
            negotiation_percentage=negotiation_percentage
        )
        print("✓ Agents initialized")
        if negotiation_percentage:
            print(f"  Merchant max discount: {negotiation_percentage}%\n")
        else:
            print()
        
        # Negotiation loop
        conversation = []
        current_price = initial_price
        agreed = False
        
        print("Starting negotiation...\n")
        print("-" * 80)
        
        for round_num in range(5):
            print(f"\n--- ROUND {round_num + 1} ---\n")
            
            # Client makes offer
            print(f"[CLIENT] Negotiating...")
            try:
                client_response = await shopping_agent.negotiate_with_merchant(
                    product_name=product_name,
                    merchant_initial_price=initial_price,
                    conversation_history=conversation,
                    budget=budget
                )
            except Exception as e:
                logger.error(f"Error in client negotiation: {str(e)}", exc_info=True)
                break
            
            client_message = client_response.get("message", "")
            client_price = client_response.get("proposed_price", current_price)
            
            conversation.append({
                "sender": "client",
                "message": client_message,
                "proposed_price": client_price,
                "accept": client_response.get("accept", False),
                "reject": client_response.get("reject", False)
            })
            
            # Save chat message to database
            if negotiation_id and chat_history_ops:
                try:
                    chat_history_ops.create_chat_message(
                        negotiation_id=negotiation_id,
                        round_number=round_num + 1,
                        sender_agent_id=UUID(client_id),
                        receiver_agent_id=UUID(merchant_id),
                        message=client_message,
                        proposed_price=client_price,
                        accept=client_response.get("accept", False),
                        reason=client_response.get("reason")
                    )
                except Exception as e:
                    logger.warning(f"Failed to save client chat message: {str(e)}")
            
            print(f"[CLIENT] {client_message}")
            print(f"         Proposed Price: ${client_price:.2f}")
            print(f"         Accept: {client_response.get('accept', False)}")
            print(f"         Reject: {client_response.get('reject', False)}")
            print(f"         Reason: {client_response.get('reason', 'N/A')}\n")
            
            # Check for explicit rejection
            if client_response.get("reject", False):
                print("✗ CLIENT REJECTED - Ending negotiation without agreement")
                agreed = False
                final_message = client_message
                break
            
            if client_response.get("accept", False):
                # Verify price is within budget before accepting
                if budget is not None and current_price > budget:
                    print(f"⚠ CLIENT TRIED TO ACCEPT ${current_price:.2f} BUT IT EXCEEDS BUDGET ${budget:.2f}")
                    print("   Rejecting acceptance - negotiation continues")
                    agreed = False
                else:
                    agreed = True
                    current_price = client_price
                    print("✓ CLIENT ACCEPTED THE OFFER!")
                    break
            
            # Merchant responds
            print(f"[MERCHANT] Responding...")
            try:
                merchant_response = await merchant_agent.negotiate_with_buyer(
                    product_name=product_name,
                    initial_price=initial_price,
                    buyer_offer=client_price,
                    conversation_history=conversation
                )
            except Exception as e:
                logger.error(f"Error in merchant negotiation: {str(e)}", exc_info=True)
                break
            
            merchant_message = merchant_response.get("message", "")
            merchant_price = merchant_response.get("proposed_price", current_price)
            
            conversation.append({
                "sender": "merchant",
                "message": merchant_message,
                "proposed_price": merchant_price,
                "accept": merchant_response.get("accept", False),
                "reject": merchant_response.get("reject", False)
            })
            
            # Save chat message to database
            if negotiation_id and chat_history_ops:
                try:
                    chat_history_ops.create_chat_message(
                        negotiation_id=negotiation_id,
                        round_number=round_num + 1,
                        sender_agent_id=UUID(merchant_id),
                        receiver_agent_id=UUID(client_id),
                        message=merchant_message,
                        proposed_price=merchant_price,
                        accept=merchant_response.get("accept", False),
                        reason=merchant_response.get("reason")
                    )
                except Exception as e:
                    logger.warning(f"Failed to save merchant chat message: {str(e)}")
            
            print(f"[MERCHANT] {merchant_message}")
            print(f"          Proposed Price: ${merchant_price:.2f}")
            print(f"          Accept: {merchant_response.get('accept', False)}")
            print(f"          Reject: {merchant_response.get('reject', False)}")
            print(f"          Reason: {merchant_response.get('reason', 'N/A')}\n")
            
            # Check for explicit rejection
            if merchant_response.get("reject", False):
                print("✗ MERCHANT REJECTED - Ending negotiation without agreement")
                agreed = False
                final_message = merchant_message
                break
            
            if merchant_response.get("accept", False):
                # Check if merchant's accepted price is within client's budget
                if budget is not None and merchant_price > budget:
                    print(f"⚠ MERCHANT ACCEPTED ${merchant_price:.2f} BUT IT EXCEEDS CLIENT BUDGET ${budget:.2f}")
                    print("   Client must reject - negotiation continues")
                    agreed = False
                    current_price = merchant_price
                    # Don't break - let client respond in next iteration
                else:
                    # Merchant accepted and price is within budget
                    agreed = True
                    current_price = merchant_price
                    print(f"✓ MERCHANT ACCEPTED THE OFFER AT ${current_price:.2f} (within budget)")
                    # If last round, check if client also accepts
                    if round_num == 4:  # Last round
                        if budget is None or current_price <= budget:
                            break
                        else:
                            agreed = False
                    else:
                        # Continue to let client confirm
                        pass
            
            current_price = merchant_price
        
        # Final check: Negotiation is only successful if price is within budget
        if agreed and budget is not None and current_price > budget:
            print(f"\n⚠ FINAL CHECK: Price ${current_price:.2f} exceeds budget ${budget:.2f}")
            print("   Marking negotiation as NOT successful")
            agreed = False
        
        # Update negotiation record with final results
        if negotiation_id and negotiations_ops:
            try:
                # Determine final status
                if agreed and (budget is None or current_price <= budget):
                    final_status = "agreed"
                else:
                    # Check if negotiation ended due to explicit rejection
                    # (We'll check the last message in conversation)
                    final_status = "rejected" if any(
                        msg.get("reject", False) for msg in conversation[-2:] if isinstance(msg, dict)
                    ) else "failed"
                
                negotiations_ops.update_negotiation(
                    negotiation_id=negotiation_id,
                    final_price=current_price,
                    agreed=agreed and (budget is None or current_price <= budget),
                    status=final_status
                )
                print(f"✓ Updated negotiation record with final results (Status: {final_status})")
            except Exception as e:
                logger.error(f"Failed to update negotiation record: {str(e)}")
                print(f"⚠ Warning: Could not update negotiation record: {str(e)}")
        
        print("-" * 80)
        
        # Final results
        print("\n" + "="*80)
        print("NEGOTIATION RESULTS")
        print("="*80)
        print(f"Product: {product_name}")
        print(f"Initial Price: ${initial_price:.2f}")
        print(f"Final Negotiated Price: ${current_price:.2f}")
        print(f"Budget: ${budget:.2f}" if budget else "Budget: No limit")
        print(f"Discount: ${(initial_price - current_price):.2f} ({(initial_price - current_price) / initial_price * 100:.1f}%)")
        if budget is not None:
            within_budget = current_price <= budget
            print(f"Within Budget: {'YES ✓' if within_budget else 'NO ✗'}")
        print(f"Agreement Reached: {'YES ✓' if agreed and (budget is None or current_price <= budget) else 'NO ✗'}")
        if budget is not None and current_price > budget:
            print(f"⚠ REASON: Final price ${current_price:.2f} exceeds budget ${budget:.2f}")
        print(f"Total Rounds: {len(conversation) // 2}")
        print("="*80)
        
        return {
            "product_name": product_name,
            "initial_price": initial_price,
            "final_price": current_price,
            "agreed": agreed,
            "conversation": conversation,
            "discount": initial_price - current_price,
            "discount_percent": ((initial_price - current_price) / initial_price * 100) if initial_price > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error in negotiation: {str(e)}", exc_info=True)
        raise


async def main():
    """Main function to run the test."""
    print("\n" + "="*80)
    print("AGENT-TO-AGENT NEGOTIATION TEST SCRIPT")
    print("="*80 + "\n")
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file or environment:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)
    
    # Connect to Supabase
    print("Connecting to Supabase...")
    try:
        supabase_client = get_supabase_client()
        print("✓ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Supabase: {str(e)}")
        sys.exit(1)
    
    # Get agents
    print("Fetching agents from database...")
    client_agents = get_client_agents(supabase_client)
    merchant_agents = get_merchant_agents(supabase_client)
    
    if not client_agents:
        print("❌ ERROR: No client agents found in database.")
        print("   Please create at least one agent with agent_type='client'")
        sys.exit(1)
    
    if not merchant_agents:
        print("❌ ERROR: No merchant agents found in database.")
        print("   Please create at least one agent with agent_type='merchant'")
        sys.exit(1)
    
    print(f"✓ Found {len(client_agents)} client agent(s)")
    print(f"✓ Found {len(merchant_agents)} merchant agent(s)\n")
    
    # Get products - search for a specific product (e.g., "Playstation 5")
    print("Fetching products from database...")
    product_query = "Playstation 5"  # You can change this
    products = get_products(supabase_client, product_query=product_query)
    
    if not products:
        print(f"❌ ERROR: No products found for '{product_query}' in database.")
        print("   Please create at least one product in the products table")
        sys.exit(1)
    
    print(f"✓ Found {len(products)} product(s) matching '{product_query}'\n")
    
    # Select first client agent
    client_agent = client_agents[0]
    client_metadata = client_agent.get("metadata", {})
    client_name = client_metadata.get("name", f"Client_{client_agent['id'][:8]}")
    
    # Budget
    budget = 870.0
    
    # Generate session ID for this shopping session
    session_id = str(uuid.uuid4())
    
    # Initialize database operations
    negotiations_ops = NegotiationsOperations()
    chat_history_ops = AgentChatHistoryOperations()
    
    print("="*80)
    print("MULTI-MERCHANT NEGOTIATION TEST")
    print("="*80)
    print(f"Session ID: {session_id}")
    print(f"Client Agent: {client_name} (ID: {client_agent['id']})")
    print(f"Product Query: {product_query}")
    print(f"Budget: ${budget:.2f}")
    print(f"Found {len(products)} merchant(s) selling this product")
    print("="*80 + "\n")
    
    # Initialize shopping agent
    print("Initializing shopping agent...")
    from agents.shopping_agent import ShoppingAgent
    shopping_agent = ShoppingAgent(
        agent_id=client_agent["id"],
        agent_name=client_name
    )
    print("✓ Shopping agent initialized\n")
    
    # Negotiate with each merchant (5 rounds each)
    all_offers = []
    
    for idx, product in enumerate(products, 1):
        merchant_agent_id = product.get("agent_id")
        if not merchant_agent_id:
            print(f"⚠ Product {idx} has no agent_id, skipping")
            continue
        
        # Find merchant agent
        merchant_agent = None
        for m in merchant_agents:
            if str(m["id"]) == str(merchant_agent_id):
                merchant_agent = m
                break
        
        if not merchant_agent:
            print(f"⚠ Merchant agent {merchant_agent_id} not found for product {idx}, skipping")
            continue
        
        merchant_metadata = merchant_agent.get("metadata", {})
        merchant_name = merchant_metadata.get("name", f"Merchant_{merchant_agent_id[:8]}")
        
        print(f"\n{'='*80}")
        print(f"NEGOTIATING WITH MERCHANT {idx}/{len(products)}: {merchant_name}")
        print(f"{'='*80}\n")
        
        # Run negotiation with this merchant
        try:
            result = await run_negotiation(
                client_agent_data=client_agent,
                merchant_agent_data=merchant_agent,
                product_data=product,
                budget=budget,
                session_id=session_id,
                negotiations_ops=negotiations_ops,
                chat_history_ops=chat_history_ops
            )
            
            # Store offer
            offer = {
                "merchant_agent_id": str(merchant_agent_id),
                "merchant_name": merchant_name,
                "product_id": product.get("id"),
                "product_name": result["product_name"],
                "initial_price": result["initial_price"],
                "negotiated_price": result["final_price"],
                "agreed": result["agreed"] and (budget is None or result["final_price"] <= budget),
                "conversation": result["conversation"],
                "final_message": result.get("final_message", "")
            }
            
            all_offers.append(offer)
            
            print(f"\n✓ Negotiation with {merchant_name} completed:")
            print(f"  Final Price: ${result['final_price']:.2f}")
            print(f"  Agreed: {'YES ✓' if offer['agreed'] else 'NO ✗'}")
            if budget and result['final_price'] > budget:
                print(f"  ⚠ Price exceeds budget ${budget:.2f}")
            
        except Exception as e:
            print(f"❌ Error negotiating with {merchant_name}: {str(e)}")
            logger.exception("Negotiation failed")
            continue
    
    # Select best offer
    print("\n" + "="*80)
    print("SELECTING BEST OFFER")
    print("="*80 + "\n")
    
    if not all_offers:
        print("❌ No offers collected. Negotiation failed.")
        sys.exit(1)
    
    # Filter to agreed offers within budget
    valid_offers = [o for o in all_offers if o["agreed"] and (budget is None or o["negotiated_price"] <= budget)]
    
    if not valid_offers:
        print("⚠ No offers within budget. Showing all offers:")
        valid_offers = all_offers
    
    # Use shopping agent to select best offer
    try:
        best_selection = await shopping_agent.select_best_offer(valid_offers)
        best_offer = best_selection["selected_offer"]
        selection_reason = best_selection.get("reason", "Best price")
    except Exception as e:
        logger.error(f"Error selecting best offer: {str(e)}", exc_info=True)
        # Fallback: lowest price
        best_offer = min(valid_offers, key=lambda x: x["negotiated_price"])
        selection_reason = "Lowest price (fallback)"
    
    # Display results
    print("\n" + "="*80)
    print("NEGOTIATION RESULTS SUMMARY")
    print("="*80)
    print(f"\nTotal Merchants Contacted: {len(products)}")
    print(f"Successful Negotiations: {len([o for o in all_offers if o['agreed']])}")
    print(f"Offers Within Budget: {len([o for o in all_offers if o['agreed'] and (budget is None or o['negotiated_price'] <= budget)])}")
    
    print(f"\n{'='*80}")
    print("ALL OFFERS:")
    print("="*80)
    for i, offer in enumerate(all_offers, 1):
        status = "✓ AGREED" if offer["agreed"] else "✗ NOT AGREED"
        budget_status = ""
        if budget:
            if offer["negotiated_price"] <= budget:
                budget_status = " (within budget)"
            else:
                budget_status = f" ⚠ EXCEEDS BUDGET ${budget:.2f}"
        
        print(f"\n{i}. {offer['merchant_name']}")
        print(f"   Product: {offer['product_name']}")
        print(f"   Initial Price: ${offer['initial_price']:.2f}")
        print(f"   Final Price: ${offer['negotiated_price']:.2f}")
        print(f"   Status: {status}{budget_status}")
        print(f"   Discount: ${(offer['initial_price'] - offer['negotiated_price']):.2f} ({(offer['initial_price'] - offer['negotiated_price']) / offer['initial_price'] * 100:.1f}%)")
    
    print(f"\n{'='*80}")
    print("BEST OFFER SELECTED:")
    print("="*80)
    print(f"Merchant: {best_offer['merchant_name']}")
    print(f"Product: {best_offer['product_name']}")
    print(f"Initial Price: ${best_offer['initial_price']:.2f}")
    print(f"Final Price: ${best_offer['negotiated_price']:.2f}")
    print(f"Discount: ${(best_offer['initial_price'] - best_offer['negotiated_price']):.2f} ({(best_offer['initial_price'] - best_offer['negotiated_price']) / best_offer['initial_price'] * 100:.1f}%)")
    print(f"Within Budget: {'YES ✓' if budget is None or best_offer['negotiated_price'] <= budget else 'NO ✗'}")
    print(f"Agreed: {'YES ✓' if best_offer['agreed'] else 'NO ✗'}")
    print(f"Selection Reason: {selection_reason}")
    
    if best_offer['agreed'] and (budget is None or best_offer['negotiated_price'] <= budget):
        print(f"\n✓ DEAL SUCCESSFUL! Ready to proceed with purchase.")
    else:
        print(f"\n✗ DEAL NOT SUCCESSFUL: Price exceeds budget or not agreed.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

