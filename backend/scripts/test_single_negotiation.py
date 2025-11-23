#!/usr/bin/env python3
"""
Test script for single negotiation between specific client and merchant with x402 payment.

This script tests direct negotiation between two specific agents:
1. Get client and merchant agents
2. Get product from merchant
3. Run 5-round negotiation
4. Execute x402 payment if deal is successful

Usage:
    # Test with specific agents and product
    python scripts/test_single_negotiation.py \
        --client-agent-id <uuid> \
        --merchant-agent-id <uuid> \
        --product-id <uuid> \
        --budget 0.5

    # Test without payment execution (dry run)
    python scripts/test_single_negotiation.py \
        --client-agent-id <uuid> \
        --merchant-agent-id <uuid> \
        --product-id <uuid> \
        --budget 0.5 \
        --dry-run

    # Auto-select first available agents and products
    python scripts/test_single_negotiation.py --budget 0.5

Requirements:
    - Set environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, USER_SECRET_KEY
    - Have at least one client agent and one merchant agent in database
    - Have products in the products table
    - Agents must have encrypted private keys
    - Client agent wallet must have USDC for payments
    - Both agents must have ETH for gas fees
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional
from uuid import UUID
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase.client import get_supabase_client
from database.supabase.operations import AgentsOperations
from services.shopping_service import ShoppingService
from utils.wallet import decrypt_pk
from utils.chaoschain import get_agent_sdk, execute_x402_payment
from chaoschain_sdk import AgentRole

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_first_client_agent(supabase_client) -> Optional[Dict[str, Any]]:
    """Get first available client agent."""
    try:
        response = supabase_client.table("agents")\
            .select("*")\
            .eq("agent_type", "client")\
            .limit(1)\
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching client agent: {str(e)}")
        return None


def get_first_merchant_with_products(supabase_client) -> tuple:
    """Get first merchant that has products."""
    try:
        # Get products with merchant info
        response = supabase_client.table("products")\
            .select("*, agents(*)")\
            .not_.is_("agent_id", "null")\
            .limit(10)\
            .execute()
        
        products = response.data or []
        
        for product in products:
            if product.get("agents") and product["agents"].get("agent_type") == "merchant":
                return product["agents"], product
        
        return None, None
    except Exception as e:
        logger.error(f"Error fetching merchant: {str(e)}")
        return None, None


async def execute_payment_for_deal(
    client_agent: Dict[str, Any],
    merchant_agent: Dict[str, Any],
    product_name: str,
    final_price: float,
    negotiation_id: Optional[UUID] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Execute x402 payment for finalized deal."""
    if dry_run:
        logger.info("DRY RUN: Skipping payment execution")
        return {
            "status": "dry_run",
            "message": "Payment execution skipped (dry run mode)",
            "would_pay": final_price
        }
    
    try:
        client_agent_id = UUID(client_agent["id"])
        merchant_agent_id = UUID(merchant_agent["id"])
        
        # Decrypt private keys
        logger.info("Decrypting agent private keys...")
        client_private_key = decrypt_pk(client_agent["private_key"])
        merchant_private_key = decrypt_pk(merchant_agent["private_key"])
        
        # Get agent metadata
        client_metadata = client_agent.get("metadata", {})
        merchant_metadata = merchant_agent.get("metadata", {})
        
        client_name = client_metadata.get("name", f"Client_{str(client_agent_id)[:8]}")
        merchant_name = merchant_metadata.get("name", f"Merchant_{str(merchant_agent_id)[:8]}")
        
        client_domain = client_metadata.get("domain", f"{client_name.lower()}.example.com")
        merchant_domain = merchant_metadata.get("domain", f"{merchant_name.lower()}.example.com")
        
        # Get agent roles
        client_role_str = client_metadata.get("chaoschain_config", {}).get("agent_role", "CLIENT")
        merchant_role_str = merchant_metadata.get("chaoschain_config", {}).get("agent_role", "SERVER")
        
        client_role = getattr(AgentRole, client_role_str.upper(), AgentRole.CLIENT)
        merchant_role = getattr(AgentRole, merchant_role_str.upper(), AgentRole.SERVER)
        
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
        
        return payment_result
        
    except Exception as e:
        logger.error(f"Error executing payment: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def test_single_negotiation(
    client_agent_id: UUID,
    merchant_agent_id: UUID,
    product_id: UUID,
    budget: float,
    rounds: int = 5,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Test single negotiation between specific agents."""
    supabase_client = get_supabase_client()
    agents_ops = AgentsOperations()
    
    # Get agents
    client_agent = agents_ops.get_agent_by_id(client_agent_id)
    merchant_agent = agents_ops.get_agent_by_id(merchant_agent_id)
    
    if not client_agent:
        return {"status": "error", "message": f"Client agent {client_agent_id} not found"}
    if not merchant_agent:
        return {"status": "error", "message": f"Merchant agent {merchant_agent_id} not found"}
    
    # Get product
    response = supabase_client.table("products")\
        .select("*, agents(*)")\
        .eq("id", str(product_id))\
        .execute()
    
    products = response.data or []
    if not products:
        return {"status": "error", "message": f"Product {product_id} not found"}
    
    product = products[0]
    
    # Verify product belongs to merchant
    if str(product.get("agent_id")) != str(merchant_agent_id):
        return {
            "status": "error",
            "message": f"Product {product_id} does not belong to merchant {merchant_agent_id}"
        }
    
    print("\n" + "="*80)
    print("SINGLE NEGOTIATION TEST")
    print("="*80)
    print(f"Client: {client_agent.get('metadata', {}).get('name', str(client_agent_id)[:8])}")
    print(f"Merchant: {merchant_agent.get('metadata', {}).get('name', str(merchant_agent_id)[:8])}")
    print(f"Product: {product.get('name')}")
    print(f"Initial Price: ${product.get('price', 0):.2f}")
    print(f"Budget: ${budget:.2f}")
    print(f"Rounds: {rounds}")
    if dry_run:
        print("Mode: DRY RUN")
    print("="*80 + "\n")
    
    # Run negotiation
    shopping_service = ShoppingService()
    
    try:
        result = await shopping_service.start_shopping(
            client_agent_id=client_agent_id,
            product_query=product.get("name", ""),
            budget=budget,
            products=[product],
            max_rounds=rounds
        )
        
        best_offer = result.get("best_offer")
        
        print("\n" + "="*80)
        print("NEGOTIATION RESULT")
        print("="*80)
        
        if best_offer:
            print(f"Final Price: ${best_offer.get('negotiated_price', 0):.2f}")
            discount = product.get('price', 0) - best_offer.get('negotiated_price', 0)
            discount_pct = (discount / product.get('price', 1)) * 100 if product.get('price', 0) > 0 else 0
            print(f"Discount: ${discount:.2f} ({discount_pct:.1f}%)")
            print(f"Agreed: {'YES ✓' if best_offer.get('agreed') else 'NO ✗'}")
            print(f"Within Budget: {'YES ✓' if best_offer.get('negotiated_price', float('inf')) <= budget else 'NO ✗'}")
            
            # Execute payment if successful
            payment_result = None
            if best_offer.get("agreed") and best_offer.get("negotiated_price", float('inf')) <= budget:
                print(f"\n{'='*80}")
                print("EXECUTING PAYMENT")
                print("="*80 + "\n")
                
                negotiation_id = UUID(best_offer.get("negotiation_id")) if best_offer.get("negotiation_id") else None
                
                payment_result = await execute_payment_for_deal(
                    client_agent=client_agent,
                    merchant_agent=merchant_agent,
                    product_name=product.get("name"),
                    final_price=best_offer.get("negotiated_price"),
                    negotiation_id=negotiation_id,
                    dry_run=dry_run
                )
                
                print("\n" + "="*80)
                print("PAYMENT RESULT")
                print("="*80)
                
                if payment_result.get("status") == "success":
                    print("✅ Payment Successful!")
                    print(f"   Transaction: {payment_result.get('transaction_hash')}")
                    print(f"   Amount: ${payment_result.get('amount_paid', 0):.2f} USDC")
                    print(f"   Settlement: {payment_result.get('settlement_address')}")
                elif payment_result.get("status") == "dry_run":
                    print("🔄 DRY RUN - Payment not executed")
                else:
                    print(f"❌ Payment Failed: {payment_result.get('error')}")
                
                print("="*80 + "\n")
            
            return {
                "status": "completed",
                "negotiation_result": result,
                "best_offer": best_offer,
                "payment_result": payment_result
            }
        else:
            print("No offer received")
            print("="*80 + "\n")
            return {
                "status": "no_offer",
                "negotiation_result": result
            }
    
    except Exception as e:
        logger.error(f"Error in negotiation: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test single negotiation between specific client and merchant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--client-agent-id",
        type=str,
        help="Client agent UUID (auto-selects first if not provided)"
    )
    parser.add_argument(
        "--merchant-agent-id",
        type=str,
        help="Merchant agent UUID (auto-selects first with products if not provided)"
    )
    parser.add_argument(
        "--product-id",
        type=str,
        help="Product UUID (auto-selects from merchant if not provided)"
    )
    parser.add_argument(
        "--budget",
        type=float,
        required=True,
        help="Client budget limit"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=5,
        help="Number of negotiation rounds (default: 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip actual payment execution"
    )
    
    args = parser.parse_args()
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENAI_API_KEY", "USER_SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    supabase_client = get_supabase_client()
    
    # Auto-select agents if not provided
    client_agent_id = None
    merchant_agent_id = None
    product_id = None
    
    if args.client_agent_id:
        client_agent_id = UUID(args.client_agent_id)
    else:
        client_agent = get_first_client_agent(supabase_client)
        if not client_agent:
            print("❌ ERROR: No client agents found in database")
            sys.exit(1)
        client_agent_id = UUID(client_agent["id"])
        print(f"📝 Auto-selected client: {client_agent.get('metadata', {}).get('name', str(client_agent_id)[:8])}")
    
    if args.merchant_agent_id and args.product_id:
        merchant_agent_id = UUID(args.merchant_agent_id)
        product_id = UUID(args.product_id)
    else:
        merchant_agent, product = get_first_merchant_with_products(supabase_client)
        if not merchant_agent or not product:
            print("❌ ERROR: No merchant agents with products found")
            sys.exit(1)
        merchant_agent_id = UUID(merchant_agent["id"])
        product_id = UUID(product["id"])
        print(f"📝 Auto-selected merchant: {merchant_agent.get('metadata', {}).get('name', str(merchant_agent_id)[:8])}")
        print(f"📝 Auto-selected product: {product.get('name')}")
    
    # Run test
    try:
        result = await test_single_negotiation(
            client_agent_id=client_agent_id,
            merchant_agent_id=merchant_agent_id,
            product_id=product_id,
            budget=args.budget,
            rounds=args.rounds,
            dry_run=args.dry_run
        )
        
        if result.get("status") == "error":
            print(f"❌ ERROR: {result.get('message')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

