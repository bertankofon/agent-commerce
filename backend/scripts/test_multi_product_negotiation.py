#!/usr/bin/env python3
"""
Enhanced Multi-Product Negotiation Test Script

This script tests negotiations with multiple products and agents, with configurable
parameters for negotiation rounds and product selection.

Usage:
    # Test with single product, 5 rounds, default budget
    python scripts/test_multi_product_negotiation.py --product-query "Playstation 5"

    # Test with multiple products, 3 rounds, custom budget
    python scripts/test_multi_product_negotiation.py --product-query "Playstation 5" --product-query "Xbox" --rounds 3 --budget 1000

    # Test with specific client agent
    python scripts/test_multi_product_negotiation.py --product-query "Playstation 5" --client-agent-id <uuid>

Requirements:
    - Set environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY
    - Have at least one client agent and merchant agents in the agents table
    - Have products in the products table
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
from services.shopping_service import ShoppingService

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


def list_available_products(supabase_client) -> None:
    """List all available products in the database."""
    try:
        response = supabase_client.table("products")\
            .select("id, name, price, agent_id")\
            .limit(100)\
            .execute()
        
        products = response.data or []
        
        if not products:
            print("No products found in database.")
            return
        
        print("\n" + "="*80)
        print("AVAILABLE PRODUCTS")
        print("="*80)
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.get('name', 'Unknown')} - ${product.get('price', 0):.2f} (ID: {product.get('id')})")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        print(f"Error listing products: {str(e)}")


def list_available_agents(supabase_client) -> None:
    """List all available agents in the database."""
    try:
        response = supabase_client.table("agents")\
            .select("id, agent_type, metadata")\
            .limit(100)\
            .execute()
        
        agents = response.data or []
        
        if not agents:
            print("No agents found in database.")
            return
        
        clients = [a for a in agents if a.get("agent_type") == "client"]
        merchants = [a for a in agents if a.get("agent_type") == "merchant"]
        
        print("\n" + "="*80)
        print("AVAILABLE AGENTS")
        print("="*80)
        print(f"\nClient Agents ({len(clients)}):")
        for i, agent in enumerate(clients, 1):
            name = agent.get("metadata", {}).get("name", f"Client_{str(agent.get('id'))[:8]}")
            print(f"  {i}. {name} (ID: {agent.get('id')})")
        
        print(f"\nMerchant Agents ({len(merchants)}):")
        for i, agent in enumerate(merchants, 1):
            name = agent.get("metadata", {}).get("name", f"Merchant_{str(agent.get('id'))[:8]}")
            print(f"  {i}. {name} (ID: {agent.get('id')})")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        print(f"Error listing agents: {str(e)}")


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


def print_statistics(results: Dict[str, Any]) -> None:
    """Print statistics about the negotiations."""
    offers = results.get('offers', [])
    if not offers:
        return
    
    agreed_offers = [o for o in offers if o.get('agreed')]
    total_offers = len(offers)
    success_rate = (len(agreed_offers) / total_offers * 100) if total_offers > 0 else 0
    
    if agreed_offers:
        avg_discount = sum(
            (o.get('initial_price', 0) - o.get('negotiated_price', 0)) / o.get('initial_price', 1) * 100
            for o in agreed_offers
            if o.get('initial_price', 0) > 0
        ) / len(agreed_offers)
        
        avg_price = sum(o.get('negotiated_price', 0) for o in agreed_offers) / len(agreed_offers)
    else:
        avg_discount = 0
        avg_price = 0
    
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    print(f"Total Negotiations: {total_offers}")
    print(f"Successful Negotiations: {len(agreed_offers)}")
    print(f"Success Rate: {success_rate:.1f}%")
    if agreed_offers:
        print(f"Average Discount: {avg_discount:.1f}%")
        print(f"Average Final Price: ${avg_price:.2f}")
    print("="*80 + "\n")


async def test_multi_product_negotiation(
    product_queries: List[str],
    rounds: int = 5,
    budget: Optional[float] = None,
    client_agent_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Test negotiations with multiple products and agents.
    
    Args:
        product_queries: List of product search queries or product IDs
        rounds: Number of negotiation rounds per merchant (default: 5)
        budget: Client budget limit (default: 870.0)
        client_agent_id: Specific client agent ID (optional)
    
    Returns:
        Dictionary with test results
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
            print_statistics(result)
            
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
    
    if overall_best:
        print(f"\nOVERALL BEST DEAL:")
        print(f"  Product: {overall_best.get('product_name')} (from query: {overall_best.get('source_query')})")
        print(f"  Merchant: {overall_best.get('merchant_name')}")
        print(f"  Price: ${overall_best.get('negotiated_price', 0):.2f}")
        print(f"  Discount: ${(overall_best.get('initial_price', 0) - overall_best.get('negotiated_price', 0)):.2f}")
        print(f"  Within Budget: {'YES ✓' if budget is None or overall_best.get('negotiated_price', 0) <= budget else 'NO ✗'}")
        print(f"  Agreed: {'YES ✓' if overall_best.get('agreed') else 'NO ✗'}")
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
        "total_negotiations": len(all_offers)
    }


async def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(
        description="Test multi-product negotiations with configurable parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with single product, 5 rounds, default budget
  python scripts/test_multi_product_negotiation.py --product-query "Playstation 5"

  # Test with multiple products, 3 rounds, custom budget
  python scripts/test_multi_product_negotiation.py --product-query "Playstation 5" --product-query "Xbox" --rounds 3 --budget 1000

  # Test with specific client agent
  python scripts/test_multi_product_negotiation.py --product-query "Playstation 5" --client-agent-id <uuid>

  # List available products and agents
  python scripts/test_multi_product_negotiation.py --list-products
  python scripts/test_multi_product_negotiation.py --list-agents
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
        "--list-products",
        action="store_true",
        help="List all available products and exit"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agents and exit"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export results to JSON file (optional)"
    )
    
    args = parser.parse_args()
    
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
    try:
        supabase_client = get_supabase_client()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Supabase: {str(e)}")
        sys.exit(1)
    
    # Handle list commands
    if args.list_products:
        list_available_products(supabase_client)
        sys.exit(0)
    
    if args.list_agents:
        list_available_agents(supabase_client)
        sys.exit(0)
    
    # Validate product queries
    if not args.product_queries:
        print("❌ ERROR: At least one --product-query is required")
        print("Use --list-products to see available products")
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
    print("MULTI-PRODUCT NEGOTIATION TEST")
    print("="*80)
    print(f"Product Queries: {', '.join(args.product_queries)}")
    print(f"Negotiation Rounds: {args.rounds}")
    print(f"Budget: ${args.budget:.2f}")
    if client_agent_id:
        print(f"Client Agent ID: {client_agent_id}")
    print("="*80 + "\n")
    
    try:
        results = await test_multi_product_negotiation(
            product_queries=args.product_queries,
            rounds=args.rounds,
            budget=args.budget,
            client_agent_id=client_agent_id
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

