#!/usr/bin/env python3
"""
Test script for negotiations with x402 payment execution.

This script tests the complete flow:
1. Search for products
2. Negotiate with merchants
3. Select best offer
4. Execute x402 payment from client to merchant

Usage:
    # Test with single product, execute payment
    python scripts/test_negotiation_with_payment.py --product-query "Playstation 5"

    # Test with multiple products, custom budget
    python scripts/test_negotiation_with_payment.py --product-query "Playstation 5" --product-query "Xbox" --budget 1000

    # Test without executing payment (dry run)
    python scripts/test_negotiation_with_payment.py --product-query "Playstation 5" --dry-run

Requirements:
    - Set environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, USER_SECRET_KEY
    - Have at least one client agent and merchant agents in the agents table
    - Have products in the products table
    - Agents must have encrypted private keys in database
    - Client agent wallet must have USDC for payments
    - Both agents must have ETH for gas fees
"""

import os
import sys
import asyncio
import logging
import argparse
import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase.client import get_supabase_client
from database.supabase.operations import AgentsOperations
from services.shopping_service import ShoppingService
from utils.wallet import decrypt_pk
from utils.chaoschain import get_agent_sdk, execute_x402_payment
from chaoschain_sdk import AgentRole, NetworkConfig

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


def get_products(supabase_client, product_queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get products from Supabase for multiple queries.
    
    Returns:
        Dictionary mapping product query to list of products
    """
    products_by_query = {}
    
    for query in product_queries:
        try:
            # Try to search by name/description first
            response = supabase_client.table("products")\
                .select("*, agents(*)")\
                .or_(f"name.ilike.%{query}%,description.ilike.%{query}%")\
                .limit(50)\
                .execute()
            
            products = response.data or []
            
            # If no results, try treating query as UUID
            if not products:
                try:
                    product_uuid = UUID(query)
                    response = supabase_client.table("products")\
                        .select("*, agents(*)")\
                        .eq("id", str(product_uuid))\
                        .execute()
                    products = response.data or []
                except ValueError:
                    pass  # Not a valid UUID, continue with empty list
            
            products_by_query[query] = products
            logger.info(f"Found {len(products)} product(s) for query: {query}")
            
        except Exception as e:
            logger.error(f"Error fetching products for query '{query}': {str(e)}")
            products_by_query[query] = []
    
    return products_by_query


def validate_test_setup(supabase_client, product_queries: List[str], client_agent_id: Optional[UUID] = None) -> tuple:
    """Validate that the test setup has required data."""
    # Check client agents
    client_agents = get_client_agents(supabase_client)
    if not client_agents:
        return False, "No client agents found in database. Please create at least one agent with agent_type='client'"
    
    # Check if specified client agent exists
    if client_agent_id:
        if not any(str(a["id"]) == str(client_agent_id) for a in client_agents):
            return False, f"Client agent {client_agent_id} not found in database"
    
    # Check products
    products_by_query = get_products(supabase_client, product_queries)
    total_products = sum(len(products) for products in products_by_query.values())
    
    if total_products == 0:
        return False, f"No products found for queries: {', '.join(product_queries)}"
    
    # Check if products have merchant agents
    products_with_merchants = 0
    for products in products_by_query.values():
        for product in products:
            if product.get("agent_id"):
                products_with_merchants += 1
    
    if products_with_merchants == 0:
        return False, "No products have associated merchant agents (agent_id)"
    
    return True, None


async def execute_payment_for_deal(
    client_agent_id: UUID,
    merchant_agent_id: UUID,
    product_name: str,
    final_price: float,
    negotiation_id: Optional[UUID] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute x402 payment for a finalized deal.
    
    Args:
        client_agent_id: UUID of client agent (payer)
        merchant_agent_id: UUID of merchant agent (payee)
        product_name: Name of product being purchased
        final_price: Final negotiated price
        negotiation_id: Optional negotiation ID
        dry_run: If True, skip actual payment execution
    
    Returns:
        Payment result dictionary
    """
    if dry_run:
        logger.info("DRY RUN: Skipping payment execution")
        return {
            "status": "dry_run",
            "message": "Payment execution skipped (dry run mode)",
            "would_pay": final_price
        }
    
    try:
        agents_ops = AgentsOperations()
        
        # Get agent records
        client_agent = agents_ops.get_agent_by_id(client_agent_id)
        merchant_agent = agents_ops.get_agent_by_id(merchant_agent_id)
        
        if not client_agent:
            raise ValueError(f"Client agent {client_agent_id} not found")
        if not merchant_agent:
            raise ValueError(f"Merchant agent {merchant_agent_id} not found")
        
        # Check for encrypted private keys
        client_encrypted_pk = client_agent.get("private_key")
        merchant_encrypted_pk = merchant_agent.get("private_key")
        
        if not client_encrypted_pk:
            raise ValueError(f"Client agent {client_agent_id} has no encrypted private key")
        if not merchant_encrypted_pk:
            raise ValueError(f"Merchant agent {merchant_agent_id} has no encrypted private key")
        
        # Decrypt private keys
        logger.info("Decrypting agent private keys...")
        logger.info(f"DEBUG: Client encrypted PK length: {len(client_encrypted_pk) if client_encrypted_pk else 0}")
        logger.info(f"DEBUG: Client encrypted PK preview: {client_encrypted_pk[:50] if client_encrypted_pk else 'None'}...")
        logger.info(f"DEBUG: Merchant encrypted PK length: {len(merchant_encrypted_pk) if merchant_encrypted_pk else 0}")
        logger.info(f"DEBUG: Merchant encrypted PK preview: {merchant_encrypted_pk[:50] if merchant_encrypted_pk else 'None'}...")
        
        try:
            logger.info("DEBUG: Attempting to decrypt CLIENT private key...")
            client_private_key = decrypt_pk(client_encrypted_pk)
            logger.info(f"DEBUG: Client private key decrypted successfully, length: {len(client_private_key)}")
            logger.info(f"DEBUG: Client private key preview: {client_private_key[:20]}...")
        except Exception as e:
            logger.error(f"DEBUG: Failed to decrypt client private key: {str(e)}")
            raise
        
        try:
            logger.info("DEBUG: Attempting to decrypt MERCHANT private key...")
            merchant_private_key = decrypt_pk(merchant_encrypted_pk)
            logger.info(f"DEBUG: Merchant private key decrypted successfully, length: {len(merchant_private_key)}")
            logger.info(f"DEBUG: Merchant private key preview: {merchant_private_key[:20]}...")
        except Exception as e:
            logger.error(f"DEBUG: Failed to decrypt merchant private key: {str(e)}")
            raise
        
        # Get agent metadata
        client_metadata = client_agent.get("metadata", {})
        merchant_metadata = merchant_agent.get("metadata", {})
        
        client_name = client_metadata.get("name", f"Client_{str(client_agent_id)[:8]}")
        merchant_name = merchant_metadata.get("name", f"Merchant_{str(merchant_agent_id)[:8]}")
        
        client_domain = client_metadata.get("domain", f"{client_name.lower()}.example.com")
        merchant_domain = merchant_metadata.get("domain", f"{merchant_name.lower()}.example.com")
        
        # Get agent roles from metadata or default
        client_role_str = client_metadata.get("chaoschain_config", {}).get("agent_role", "CLIENT")
        merchant_role_str = merchant_metadata.get("chaoschain_config", {}).get("agent_role", "SERVER")
        
        try:
            client_role = getattr(AgentRole, client_role_str.upper(), AgentRole.CLIENT)
        except:
            client_role = AgentRole.CLIENT
        
        try:
            # MERCHANT doesn't exist in AgentRole enum, use SERVER for merchants
            merchant_role = getattr(AgentRole, merchant_role_str.upper(), AgentRole.SERVER)
        except:
            merchant_role = AgentRole.SERVER
        
        # Initialize SDKs
        logger.info(f"Initializing SDK for client agent: {client_name}")
        client_sdk = get_agent_sdk(
            agent_name=client_name,
            agent_domain=client_domain,
            private_key=client_private_key,
            agent_role=client_role,
            enable_payments=True
        )
        
        logger.info(f"Initializing SDK for merchant agent: {merchant_name}")
        merchant_sdk = get_agent_sdk(
            agent_name=merchant_name,
            agent_domain=merchant_domain,
            private_key=merchant_private_key,
            agent_role=merchant_role,
            enable_payments=True
        )
        
        # Get public addresses
        client_public_address = client_agent.get("public_address")
        merchant_public_address = merchant_agent.get("public_address")
        
        if not merchant_public_address:
            raise ValueError("Merchant agent missing public_address field - required for payment")
        
        # Execute payment
        logger.info(f"Executing x402 payment: ${final_price} from {client_name} to {merchant_name}")
        logger.info(f"Client address: {client_public_address}")
        logger.info(f"Merchant address: {merchant_public_address}")
        payment_result = execute_x402_payment(
            client_sdk=client_sdk,
            merchant_sdk=merchant_sdk,
            product_name=product_name,
            final_price=final_price,
            negotiation_id=negotiation_id,
            client_name=client_name,
            client_public_address=client_public_address,
            merchant_public_address=merchant_public_address
        )
        
        # Cleanup temp wallet files
        try:
            if hasattr(client_sdk, '_temp_wallet_file') and os.path.exists(client_sdk._temp_wallet_file):
                os.remove(client_sdk._temp_wallet_file)
            if hasattr(merchant_sdk, '_temp_wallet_file') and os.path.exists(merchant_sdk._temp_wallet_file):
                os.remove(merchant_sdk._temp_wallet_file)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp wallet files: {str(e)}")
        
        return payment_result
        
    except Exception as e:
        logger.error(f"Error executing payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def print_negotiation_summary(results: Dict[str, Any]) -> None:
    """Print a comprehensive summary of all negotiations."""
    print("\n" + "="*80)
    print("NEGOTIATION SUMMARY")
    print("="*80)
    
    print(f"\nSession ID: {results.get('session_id')}")
    print(f"Product Query: {results.get('product_query', 'N/A')}")
    print(f"Total Merchants Contacted: {results.get('total_merchants_contacted', 0)}")
    print(f"Successful Negotiations: {results.get('successful_negotiations', 0)}")
    print(f"Valid Offers (within budget): {results.get('valid_offers_count', 0)}")
    print(f"Status: {results.get('status', 'unknown')}")
    
    offers = results.get('offers', [])
    if offers:
        print(f"\n{'='*80}")
        print("ALL OFFERS")
        print("="*80)
        
        for i, offer in enumerate(offers, 1):
            status = "✓ AGREED" if offer.get("agreed") else "✗ NOT AGREED"
            print(f"\n{i}. {offer.get('merchant_name', 'Unknown Merchant')}")
            print(f"   Product: {offer.get('product_name', 'Unknown')}")
            print(f"   Initial Price: ${offer.get('initial_price', 0):.2f}")
            print(f"   Final Price: ${offer.get('negotiated_price', 0):.2f}")
            discount = offer.get('initial_price', 0) - offer.get('negotiated_price', 0)
            discount_pct = (discount / offer.get('initial_price', 1)) * 100 if offer.get('initial_price', 0) > 0 else 0
            print(f"   Discount: ${discount:.2f} ({discount_pct:.1f}%)")
            print(f"   Status: {status}")
            if offer.get('negotiation_id'):
                print(f"   Negotiation ID: {offer.get('negotiation_id')}")
    
    best_offer = results.get('best_offer')
    if best_offer:
        print(f"\n{'='*80}")
        print("BEST OFFER SELECTED")
        print("="*80)
        print(f"Merchant: {best_offer.get('merchant_name', 'Unknown')}")
        print(f"Product: {best_offer.get('product_name', 'Unknown')}")
        print(f"Initial Price: ${best_offer.get('initial_price', 0):.2f}")
        print(f"Final Price: ${best_offer.get('negotiated_price', 0):.2f}")
        discount = best_offer.get('initial_price', 0) - best_offer.get('negotiated_price', 0)
        discount_pct = (discount / best_offer.get('initial_price', 1)) * 100 if best_offer.get('initial_price', 0) > 0 else 0
        print(f"Discount: ${discount:.2f} ({discount_pct:.1f}%)")
        print(f"Within Budget: {'YES ✓' if results.get('within_budget') else 'NO ✗'}")
        print(f"Agreed: {'YES ✓' if best_offer.get('agreed') else 'NO ✗'}")
        print(f"Selection Reason: {results.get('selected_reason', 'N/A')}")
        print(f"Deal Successful: {'YES ✓' if results.get('deal_successful') else 'NO ✗'}")
    
    print("="*80 + "\n")


def print_payment_summary(payment_result: Dict[str, Any]) -> None:
    """Print payment execution summary."""
    print("\n" + "="*80)
    print("PAYMENT EXECUTION SUMMARY")
    print("="*80)
    
    if payment_result.get("status") == "dry_run":
        print(f"\nDRY RUN MODE - Payment not executed")
        print(f"Would pay: ${payment_result.get('would_pay', 0):.2f}")
    elif payment_result.get("status") == "success":
        print(f"\n✓ Payment Executed Successfully")
        print(f"Transaction Hash: {payment_result.get('transaction_hash')}")
        print(f"Amount Paid: ${payment_result.get('amount_paid', 0):.2f} USDC")
        print(f"Protocol Fee: ${payment_result.get('protocol_fee', 0):.2f}")
        print(f"Settlement Address: {payment_result.get('settlement_address')}")
        print(f"Evidence CID: {payment_result.get('evidence_cid')}")
        print(f"Cart ID: {payment_result.get('cart_id')}")
    elif payment_result.get("status") == "error":
        print(f"\n✗ Payment Failed")
        print(f"Error: {payment_result.get('error', 'Unknown error')}")
    else:
        print(f"\n? Unknown payment status: {payment_result.get('status')}")
    
    print("="*80 + "\n")


async def test_negotiation_with_payment(
    product_queries: List[str],
    rounds: int = 5,
    budget: Optional[float] = None,
    client_agent_id: Optional[UUID] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Test negotiations with x402 payment execution.
    
    Args:
        product_queries: List of product search queries or product IDs
        rounds: Number of negotiation rounds per merchant (default: 5)
        budget: Client budget limit (default: 870.0)
        client_agent_id: Specific client agent ID (optional)
        dry_run: If True, skip actual payment execution
    
    Returns:
        Dictionary with test results including payment info
    """
    # Connect to Supabase
    supabase_client = get_supabase_client()
    
    # Validate setup
    is_valid, error_msg = validate_test_setup(supabase_client, product_queries, client_agent_id)
    if not is_valid:
        return {
            "status": "error",
            "message": error_msg
        }
    
    # Get or select client agent
    client_agents = get_client_agents(supabase_client)
    if client_agent_id:
        client_agent = next((a for a in client_agents if str(a["id"]) == str(client_agent_id)), None)
        if not client_agent:
            return {
                "status": "error",
                "message": f"Client agent {client_agent_id} not found"
            }
    else:
        client_agent = client_agents[0]
    
    client_agent_id = UUID(client_agent["id"])
    client_metadata = client_agent.get("metadata", {})
    client_name = client_metadata.get("name", f"Client_{str(client_agent_id)[:8]}")
    
    # Get products for all queries
    products_by_query = get_products(supabase_client, product_queries)
    
    # Initialize shopping service
    shopping_service = ShoppingService()
    
    # Run negotiations for each product query
    all_results = []
    for query, products in products_by_query.items():
        if not products:
            logger.warning(f"No products found for query: {query}")
            continue
        
        print("\n" + "="*80)
        print(f"NEGOTIATING FOR: {query}")
        print(f"Found {len(products)} merchant(s) selling this product")
        print("="*80)
        
        # Run shopping session
        try:
            result = await shopping_service.start_shopping(
                client_agent_id=client_agent_id,
                product_query=query,
                budget=budget,
                products=products,
                max_rounds=rounds
            )
            
            result["product_query"] = query
            all_results.append(result)
            
            # Print summary for this product
            print_negotiation_summary(result)
            
        except Exception as e:
            logger.error(f"Error in shopping session for '{query}': {str(e)}", exc_info=True)
            all_results.append({
                "status": "error",
                "product_query": query,
                "message": str(e)
            })
    
    # Find overall best deal across all products
    all_offers = []
    for result in all_results:
        if result.get("offers"):
            for offer in result["offers"]:
                offer["source_query"] = result.get("product_query")
                all_offers.append(offer)
    
    overall_best = None
    if all_offers:
        # Filter to agreed offers within budget
        valid_offers = [
            o for o in all_offers
            if o.get("agreed") and (budget is None or o.get("negotiated_price", float('inf')) <= budget)
        ]
        
        if valid_offers:
            overall_best = min(valid_offers, key=lambda x: x.get("negotiated_price", float('inf')))
        elif all_offers:
            # If no valid offers, use lowest price anyway
            overall_best = min(all_offers, key=lambda x: x.get("negotiated_price", float('inf')))
    
    # Print overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Products Tested: {len(all_results)}")
    print(f"Total Negotiations: {len(all_offers)}")
    
    payment_result = None
    if overall_best and overall_best.get("agreed"):
        print(f"\nOVERALL BEST DEAL:")
        print(f"  Product: {overall_best.get('product_name')} (from query: {overall_best.get('source_query')})")
        print(f"  Merchant: {overall_best.get('merchant_name')}")
        print(f"  Price: ${overall_best.get('negotiated_price', 0):.2f}")
        print(f"  Discount: ${(overall_best.get('initial_price', 0) - overall_best.get('negotiated_price', 0)):.2f}")
        print(f"  Within Budget: {'YES ✓' if budget is None or overall_best.get('negotiated_price', 0) <= budget else 'NO ✗'}")
        print(f"  Agreed: {'YES ✓' if overall_best.get('agreed') else 'NO ✗'}")
        
        # Execute payment if deal is successful
        if overall_best.get("agreed") and (budget is None or overall_best.get("negotiated_price", 0) <= budget):
            print(f"\n{'='*80}")
            print("EXECUTING PAYMENT")
            print("="*80)
            
            merchant_agent_id = UUID(overall_best.get("merchant_agent_id"))
            negotiation_id = UUID(overall_best.get("negotiation_id")) if overall_best.get("negotiation_id") else None
            
            payment_result = await execute_payment_for_deal(
                client_agent_id=client_agent_id,
                merchant_agent_id=merchant_agent_id,
                product_name=overall_best.get("product_name"),
                final_price=overall_best.get("negotiated_price"),
                negotiation_id=negotiation_id,
                dry_run=dry_run
            )
            
            print_payment_summary(payment_result)
    else:
        print("\nNo valid offers found across all products.")
    
    print("="*80 + "\n")
    
    return {
        "status": "completed",
        "client_agent_id": str(client_agent_id),
        "client_name": client_name,
        "rounds": rounds,
        "budget": budget,
        "product_queries": product_queries,
        "results_by_product": all_results,
        "overall_best_offer": overall_best,
        "total_negotiations": len(all_offers),
        "payment_result": payment_result
    }


async def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(
        description="Test negotiations with x402 payment execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with single product, execute payment
  python scripts/test_negotiation_with_payment.py --product-query "Playstation 5"

  # Test with multiple products, custom budget
  python scripts/test_negotiation_with_payment.py --product-query "Playstation 5" --product-query "Xbox" --budget 1000

  # Test without executing payment (dry run)
  python scripts/test_negotiation_with_payment.py --product-query "Playstation 5" --dry-run

  # Test with specific client agent
  python scripts/test_negotiation_with_payment.py --product-query "Playstation 5" --client-agent-id <uuid>
        """
    )
    
    parser.add_argument(
        "--product-query",
        action="append",
        dest="product_queries",
        help="Product search query or product ID (can be specified multiple times)"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=5,
        help="Number of negotiation rounds per merchant (default: 5)"
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=870.0,
        help="Client budget limit (default: 870.0)"
    )
    parser.add_argument(
        "--client-agent-id",
        type=str,
        help="Specific client agent ID (optional, uses first available if not specified)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip actual payment execution (dry run mode)"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export results to JSON file (optional)"
    )
    
    args = parser.parse_args()
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY", "USER_SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file or environment:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)
    
    # Connect to Supabase
    try:
        supabase_client = get_supabase_client()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Supabase: {str(e)}")
        sys.exit(1)
    
    # Validate product queries
    if not args.product_queries:
        print("❌ ERROR: At least one --product-query is required")
        sys.exit(1)
    
    # Parse client agent ID if provided
    client_agent_id = None
    if args.client_agent_id:
        try:
            client_agent_id = UUID(args.client_agent_id)
        except ValueError:
            print(f"❌ ERROR: Invalid client agent ID format: {args.client_agent_id}")
            sys.exit(1)
    
    # Run test
    print("\n" + "="*80)
    print("NEGOTIATION WITH PAYMENT TEST")
    print("="*80)
    print(f"Product Queries: {', '.join(args.product_queries)}")
    print(f"Negotiation Rounds: {args.rounds}")
    print(f"Budget: ${args.budget:.2f}")
    if client_agent_id:
        print(f"Client Agent ID: {client_agent_id}")
    if args.dry_run:
        print("Mode: DRY RUN (payment will not be executed)")
    print("="*80 + "\n")
    
    try:
        results = await test_negotiation_with_payment(
            product_queries=args.product_queries,
            rounds=args.rounds,
            budget=args.budget,
            client_agent_id=client_agent_id,
            dry_run=args.dry_run
        )
        
        # Export to JSON if requested
        if args.export_json:
            with open(args.export_json, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✓ Results exported to {args.export_json}")
        
        if results.get("status") == "error":
            print(f"❌ ERROR: {results.get('message')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running test: {str(e)}", exc_info=True)
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

