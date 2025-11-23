"""Shopping Service - Orchestrates product search, negotiation, and purchase."""

import logging
import uuid
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from database.supabase.operations import (
    AgentsOperations,
    NegotiationsOperations,
    AgentChatHistoryOperations
)
from agents.shopping_agent import ShoppingAgent
from agents.merchant_agent import MerchantAgent

logger = logging.getLogger(__name__)


class ShoppingService:
    """
    Main service for orchestrating shopping: search, negotiate, purchase.
    Manages the negotiation flow between client and merchant agents.
    """

    def __init__(self):
        """Initialize the shopping service."""
        self.agents_ops = AgentsOperations()
        self.negotiations_ops = NegotiationsOperations()
        self.chat_history_ops = AgentChatHistoryOperations()
        # Note: ProductsOperations will be added when database layer is implemented
        # For now, we'll work with what we have

    async def start_shopping(
        self,
        client_agent_id: UUID,
        product_query: str,
        budget: Optional[float] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        max_rounds: int = 5
    ) -> Dict[str, Any]:
        """
        Start a shopping session: search for products and negotiate.

        Args:
            client_agent_id: UUID of the client agent
            product_query: Product search query
            budget: Optional budget limit
            products: Optional list of products (if None, will need ProductsOperations)
            max_rounds: Maximum number of negotiation rounds per merchant (default: 5)

        Returns:
            Dictionary with session_id, offers, best_offer, and status
        """
        try:
            # Get client agent
            client_agent = self.agents_ops.get_agent_by_id(client_agent_id)
            if not client_agent:
                raise ValueError(f"Client agent {client_agent_id} not found")

            client_metadata = client_agent.get("metadata", {})
            client_name = client_metadata.get("name", f"Client_{str(client_agent_id)[:8]}")
            
            # Get user_id from client agent
            user_id = None
            if client_agent.get("user_id"):
                try:
                    user_id = UUID(client_agent.get("user_id"))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid user_id format in client_agent: {client_agent.get('user_id')}")

            # Create shopping session ID
            session_id = str(uuid.uuid4())

            logger.info(
                f"Starting shopping session {session_id} for client {client_name} "
                f"searching for: {product_query}"
            )

            # If products not provided, we need ProductsOperations
            # For now, assume products are passed in or will be implemented later
            if products is None:
                logger.warning("No products provided and ProductsOperations not yet implemented")
                return {
                    "session_id": session_id,
                    "status": "error",
                    "message": "ProductsOperations not yet implemented. Please provide products list."
                }

            if not products:
                return {
                    "session_id": session_id,
                    "status": "no_products_found",
                    "message": f"No products found for '{product_query}'"
                }

            logger.info(f"Found {len(products)} products to negotiate with")

            # Initialize shopping agent
            try:
                shopping_agent = ShoppingAgent(
                    agent_id=str(client_agent_id),
                    agent_name=client_name
                )
            except Exception as e:
                logger.error(f"Failed to initialize ShoppingAgent: {str(e)}", exc_info=True)
                raise

            # Negotiate with each merchant (sequential)
            offers = []
            for product in products:
                try:
                    merchant_agent_id_str = product.get("agent_id")
                    if not merchant_agent_id_str:
                        logger.warning(f"Product {product.get('id')} has no agent_id, skipping")
                        continue

                    merchant_agent_id = UUID(merchant_agent_id_str)
                    merchant_agent = self.agents_ops.get_agent_by_id(merchant_agent_id)

                    if not merchant_agent:
                        logger.warning(f"Merchant agent {merchant_agent_id} not found, skipping")
                        continue

                    merchant_metadata = merchant_agent.get("metadata", {})
                    merchant_name = merchant_metadata.get("name", f"Merchant_{str(merchant_agent_id)[:8]}")

                    initial_price = float(product.get("price", 0))
                    product_name = product.get("name", "Unknown Product")
                    negotiation_percentage = product.get("negotiation_percentage")  # Can be None
                    if negotiation_percentage is not None:
                        negotiation_percentage = float(negotiation_percentage)

                    logger.info(
                        f"Negotiating with {merchant_name} for {product_name} "
                        f"at initial price ${initial_price:.2f}"
                        f"{f' (max discount: {negotiation_percentage}%)' if negotiation_percentage else ''}"
                    )

                    # Initialize merchant agent with negotiation_percentage
                    try:
                        merchant_agent_llm = MerchantAgent(
                            agent_id=str(merchant_agent_id),
                            agent_name=merchant_name,
                            negotiation_percentage=negotiation_percentage
                        )
                    except Exception as e:
                        logger.error(f"Failed to initialize MerchantAgent: {str(e)}", exc_info=True)
                        continue

                    # Create negotiation record in database
                    try:
                        negotiation_record = self.negotiations_ops.create_negotiation(
                            session_id=session_id,
                            client_agent_id=client_agent_id,
                            merchant_agent_id=merchant_agent_id,
                            product_id=UUID(product.get("id")),
                            initial_price=initial_price,
                            negotiation_percentage=negotiation_percentage,
                            budget=budget,
                            status="in_progress",
                            user_id=user_id
                        )
                        negotiation_id = UUID(negotiation_record["id"])
                        logger.info(f"Created negotiation record: {negotiation_id}")
                    except Exception as e:
                        logger.error(f"Failed to create negotiation record: {str(e)}", exc_info=True)
                        negotiation_id = None

                    # Negotiation loop (configurable max rounds)
                    conversation = []
                    current_price = initial_price
                    agreed = False
                    final_message = ""

                    for round_num in range(max_rounds):
                        logger.info(f"Round {round_num + 1} of negotiation with {merchant_name}")

                        # Client makes offer/response
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
                        if negotiation_id:
                            try:
                                self.chat_history_ops.create_chat_message(
                                    negotiation_id=negotiation_id,
                                    round_number=round_num + 1,
                                    sender_agent_id=client_agent_id,
                                    receiver_agent_id=merchant_agent_id,
                                    message=client_message,
                                    proposed_price=client_price,
                                    accept=client_response.get("accept", False),
                                    reason=client_response.get("reason")
                                )
                            except Exception as e:
                                logger.warning(f"Failed to save client chat message: {str(e)}")

                        logger.info(f"Client: {client_message} (${client_price:.2f})")

                        # Check for explicit rejection
                        if client_response.get("reject", False):
                            logger.info("Client explicitly rejected - ending negotiation without agreement")
                            agreed = False
                            final_message = client_message
                            break

                        if client_response.get("accept", False):
                            # Verify price is within budget before accepting
                            if budget is not None and current_price > budget:
                                logger.warning(
                                    f"Client tried to accept ${current_price:.2f} but it exceeds budget ${budget:.2f}. "
                                    f"Rejecting acceptance."
                                )
                                agreed = False
                                # Continue negotiation instead of breaking
                            else:
                                agreed = True
                                current_price = client_price
                                final_message = client_message
                                logger.info(f"Client accepted offer at ${current_price:.2f}")
                                break

                        # Merchant responds
                        try:
                            merchant_response = await merchant_agent_llm.negotiate_with_buyer(
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
                        if negotiation_id:
                            try:
                                self.chat_history_ops.create_chat_message(
                                    negotiation_id=negotiation_id,
                                    round_number=round_num + 1,
                                    sender_agent_id=merchant_agent_id,
                                    receiver_agent_id=client_agent_id,
                                    message=merchant_message,
                                    proposed_price=merchant_price,
                                    accept=merchant_response.get("accept", False),
                                    reason=merchant_response.get("reason")
                                )
                            except Exception as e:
                                logger.warning(f"Failed to save merchant chat message: {str(e)}")

                        logger.info(f"Merchant: {merchant_message} (${merchant_price:.2f})")

                        # Check for explicit rejection
                        if merchant_response.get("reject", False):
                            logger.info("Merchant explicitly rejected - ending negotiation without agreement")
                            agreed = False
                            final_message = merchant_message
                            break

                        if merchant_response.get("accept", False):
                            current_price = merchant_price
                            # Check if merchant's accepted price is within client's budget
                            if budget is not None and merchant_price > budget:
                                logger.warning(
                                    f"Merchant accepted ${merchant_price:.2f} but it exceeds client budget ${budget:.2f}. "
                                    f"Client must reject this - negotiation will continue or fail."
                                )
                                agreed = False
                                # If last round, negotiation fails
                                if round_num == max_rounds - 1:
                                    final_message = f"Negotiation failed: Merchant accepted ${merchant_price:.2f} but it exceeds budget ${budget:.2f}"
                                    break
                                # Otherwise continue to let client reject
                            else:
                                # Merchant accepted and price is within budget
                                final_message = merchant_message
                                logger.info(f"Merchant accepted offer at ${current_price:.2f} (within budget)")
                                # Client should accept this since it's within budget
                                # If last round, mark as agreed
                                if round_num == max_rounds - 1:
                                    if budget is None or current_price <= budget:
                                        agreed = True
                                        break
                                    else:
                                        agreed = False
                                        break
                                # If not last round, continue to get client confirmation
                                # Client should accept in next round since price is within budget

                        current_price = merchant_price
                    
                    # Final check: Negotiation is only successful if price is within budget
                    if agreed and budget is not None and current_price > budget:
                        logger.warning(
                            f"Negotiation marked as agreed but price ${current_price:.2f} exceeds budget ${budget:.2f}. "
                            f"Marking as NOT agreed."
                        )
                        agreed = False
                        final_message = f"Negotiation failed: Final price ${current_price:.2f} exceeds budget ${budget:.2f}"
                    
                    # Update negotiation record with final results
                    if negotiation_id:
                        try:
                            # Determine final status
                            if agreed and (budget is None or current_price <= budget):
                                final_status = "agreed"
                            else:
                                # Check if negotiation ended due to explicit rejection
                                final_status = "rejected" if any(
                                    msg.get("reject", False) for msg in conversation[-2:] if isinstance(msg, dict)
                                ) else "failed"
                            
                            self.negotiations_ops.update_negotiation(
                                negotiation_id=negotiation_id,
                                final_price=current_price,
                                agreed=agreed and (budget is None or current_price <= budget),
                                status=final_status
                            )
                            logger.info(f"Updated negotiation {negotiation_id} with final results")
                        except Exception as e:
                            logger.warning(f"Failed to update negotiation record: {str(e)}")

                    # Store offer
                    offer = {
                        "negotiation_id": str(negotiation_id) if negotiation_id else None,
                        "merchant_agent_id": str(merchant_agent_id),
                        "merchant_name": merchant_name,
                        "product_id": product.get("id"),
                        "product_name": product_name,
                        "initial_price": initial_price,
                        "negotiated_price": current_price,
                        "agreed": agreed and (budget is None or current_price <= budget),  # Only agreed if within budget
                        "conversation": conversation,
                        "final_message": final_message or (conversation[-1]["message"] if conversation else "")
                    }

                    offers.append(offer)
                    logger.info(
                        f"Negotiation with {merchant_name} completed: "
                        f"${current_price:.2f} (agreed: {agreed})"
                    )

                except Exception as e:
                    logger.error(f"Error negotiating with merchant: {str(e)}", exc_info=True)
                    continue

            # Select best offer
            if not offers:
                return {
                    "session_id": session_id,
                    "status": "no_offers",
                    "message": "No successful negotiations"
                }

            # Filter to agreed offers that are within budget
            valid_offers = [
                o for o in offers 
                if o["agreed"] and (budget is None or o["negotiated_price"] <= budget)
            ]
            
            if not valid_offers:
                # If no valid offers within budget, check if any offers exist
                logger.warning("No offers within budget. Checking all offers...")
                # Use all offers for selection, but mark as not successful
                valid_offers = sorted(offers, key=lambda x: x["negotiated_price"])

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
            
            # Final verification: Best offer must be within budget for successful deal
            deal_successful = (
                best_offer["agreed"] and 
                (budget is None or best_offer["negotiated_price"] <= budget)
            )
            
            status = "offer_selected" if deal_successful else "no_valid_offers"
            
            logger.info(
                f"Shopping session {session_id} completed. "
                f"Best offer: ${best_offer['negotiated_price']:.2f} from {best_offer['merchant_name']}. "
                f"Deal successful: {deal_successful}"
            )

            return {
                "session_id": session_id,
                "status": status,
                "product_query": product_query,
                "total_merchants_contacted": len(products),
                "successful_negotiations": len([o for o in offers if o["agreed"]]),
                "valid_offers_count": len([o for o in offers if o["agreed"] and (budget is None or o["negotiated_price"] <= budget)]),
                "offers": offers,
                "best_offer": best_offer,
                "selected_reason": selection_reason,
                "deal_successful": deal_successful,
                "final_price": best_offer["negotiated_price"],
                "within_budget": budget is None or best_offer["negotiated_price"] <= budget
            }

        except Exception as e:
            logger.error(f"Error in shopping service: {str(e)}", exc_info=True)
            raise

