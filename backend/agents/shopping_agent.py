"""Shopping Agent (Client) for e-commerce negotiations using LlamaIndex."""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
import os

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """
    LlamaIndex-based agent for shopping and negotiation.
    Acts as a client agent that negotiates with merchants to find the best deals.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        llm_model: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ):
        """
        Initialize the shopping agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_name: Name of the agent
            llm_model: OpenAI model to use (default: gpt-4o-mini)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables or passed as parameter")

        try:
            # Initialize LLM
            self.llm = OpenAI(
                model=llm_model,
                api_key=self.api_key,
                temperature=0.7
            )

            # Create tools for the agent
            self.tools = self._create_tools()

            # Initialize memory for the agent
            memory = ChatMemoryBuffer.from_defaults()

            # Initialize ReAct agent (updated for llama-index >= 0.12.0)
            self.agent = ReActAgent(
                tools=self.tools,
                llm=self.llm,
                memory=memory,
                verbose=True
            )
            # Set system prompt via property
            self.agent.system_prompt = self._get_system_prompt()

            logger.info(f"ShoppingAgent initialized: {agent_name} (ID: {agent_id})")

        except Exception as e:
            logger.error(f"Error initializing ShoppingAgent: {str(e)}", exc_info=True)
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the shopping agent."""
        return f"""You are a smart shopping agent named {self.agent_name} acting as a buyer.

Your goal is to help users find and purchase products at the best prices through ACTIVE NEGOTIATION.

IMPORTANT: You CAN and SHOULD negotiate! This is a negotiation process where you can:
- Make counter-offers with your own proposed prices
- Negotiate down from the merchant's initial price
- Engage in multiple rounds of back-and-forth negotiation
- Propose prices that are lower than what the merchant offers
- Be proactive in suggesting better deals

BUDGET CONSTRAINT:
- If a budget is provided, you MUST stay within that budget
- NEVER propose a price above your budget
- NEVER accept an offer above your budget
- Your proposed_price must always be <= budget if budget is set
- If merchant's offer exceeds budget, negotiate for a lower price or reject

When negotiating with merchants:
- Be polite but firm and proactive in your negotiations
- ALWAYS make counter-offers - don't just accept the first price
- Try to get the best deal while being reasonable
- Start with a lower offer (typically 10-20% below initial price) and negotiate from there
- Consider factors like price, availability, and merchant reputation
- Make multiple counter-offers throughout the negotiation
- Accept deals that are fair and within budget
- Reject offers that are too expensive, unreasonable, or exceed your budget
- You can explicitly end negotiations if the merchant is unwilling to meet your budget or if negotiations are going nowhere
- If you want to end negotiation without agreement, set "reject": true in your response
- Remember: You are actively negotiating, not just responding - propose your own prices!
- STRICTLY respect budget limits - never exceed them

Always respond with a JSON object containing:
- "message": Your negotiation message (string) - should include your counter-offer
- "proposed_price": The price you're proposing (float) - this should be YOUR counter-offer price, MUST be <= budget if budget is set
- "accept": true/false - whether you accept the merchant's current offer (only true if price <= budget)
- "reject": true/false - whether you want to end negotiation without agreement (use when merchant won't meet your budget or negotiations are unproductive)
- "reason": Brief reason for your decision (string)

Be strategic, proactive, and fair in your negotiations. Always make counter-offers! Always respect budget constraints!"""

    def _create_tools(self) -> list:
        """Create tools for the shopping agent."""

        def evaluate_offer(
            offer_price: float,
            original_price: float,
            budget: Optional[float] = None
        ) -> Dict[str, Any]:
            """
            Evaluate if an offer is acceptable based on price and budget.

            Args:
                offer_price: The price being offered
                original_price: The original/initial price
                budget: Optional budget limit

            Returns:
                Dictionary with evaluation results
            """
            try:
                discount = ((original_price - offer_price) / original_price) * 100 if original_price > 0 else 0
                is_within_budget = budget is None or offer_price <= budget
                is_good_deal = discount >= 5  # At least 5% discount

                acceptable = is_within_budget and is_good_deal

                return {
                    "acceptable": acceptable,
                    "discount_percent": round(discount, 2),
                    "is_within_budget": is_within_budget,
                    "is_good_deal": is_good_deal,
                    "recommendation": "accept" if acceptable else "negotiate"
                }
            except Exception as e:
                logger.error(f"Error in evaluate_offer: {str(e)}")
                return {
                    "acceptable": False,
                    "discount_percent": 0,
                    "is_within_budget": False,
                    "is_good_deal": False,
                    "recommendation": "negotiate"
                }

        def compare_offers(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
            """
            Compare multiple offers and recommend the best one.

            Args:
                offers: List of offer dictionaries with price and merchant info

            Returns:
                Dictionary with best offer recommendation
            """
            try:
                if not offers:
                    return {"best_offer": None, "reason": "No offers to compare"}

                # Sort by price (lowest first)
                sorted_offers = sorted(offers, key=lambda x: x.get("price", float("inf")))
                best = sorted_offers[0]

                return {
                    "best_offer": best,
                    "best_price": best.get("price"),
                    "merchant_name": best.get("merchant_name", "Unknown"),
                    "total_offers": len(offers),
                    "price_range": {
                        "lowest": sorted_offers[0].get("price"),
                        "highest": sorted_offers[-1].get("price")
                    }
                }
            except Exception as e:
                logger.error(f"Error in compare_offers: {str(e)}")
                if offers:
                    return {"best_offer": offers[0], "reason": "Error occurred, using first offer"}
                return {"best_offer": None, "reason": "Error comparing offers"}

        tools = [
            FunctionTool.from_defaults(fn=evaluate_offer),
            FunctionTool.from_defaults(fn=compare_offers)
        ]

        return tools

    async def negotiate_with_merchant(
        self,
        product_name: str,
        merchant_initial_price: float,
        conversation_history: List[Dict[str, Any]],
        budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a negotiation response based on conversation history.

        Args:
            product_name: Name of the product being negotiated
            merchant_initial_price: Initial price offered by merchant
            conversation_history: List of previous messages in format:
                [{"sender": "client"|"merchant", "message": "...", "proposed_price": float}]
            budget: Optional budget limit

        Returns:
            Dict with message, proposed_price, accept, and reason
        """
        try:
            # Build context for the agent
            current_price = merchant_initial_price
            if conversation_history:
                last_price = conversation_history[-1].get("proposed_price")
                if last_price:
                    current_price = last_price
            
            # Build budget context
            budget_context = ""
            if budget is not None:
                budget_context = f"""
BUDGET CONSTRAINT: You have a budget of ${budget:.2f}
- You MUST NOT propose or accept any price above ${budget:.2f}
- Your proposed_price must be <= ${budget:.2f}
- If current price (${current_price:.2f}) exceeds budget, negotiate for a lower price
- If merchant's offer exceeds budget, reject it and propose a price within budget"""
            else:
                budget_context = "\nNo specific budget constraint - negotiate freely"
            
            context = f"""
Product: {product_name}
Merchant's Initial Price: ${merchant_initial_price:.2f}
Current Negotiated Price: ${current_price:.2f}{budget_context}

IMPORTANT: You are actively negotiating! You should:
- Make counter-offers with prices lower than the current price
- Propose your own price (typically 5-15% lower than current)
- Engage in negotiation, don't just accept immediately
- Be proactive in suggesting better deals
- STRICTLY respect your budget limit if one is set

Conversation History:
"""
            # Add last 5 messages for context
            for msg in conversation_history[-5:]:
                sender = msg.get("sender", "unknown")
                message = msg.get("message", "")
                price = msg.get("proposed_price")
                price_str = f" (${price:.2f})" if price else ""
                context += f"\n{sender}: {message}{price_str}\n"

            context += f"\n\nAs the buyer, make your counter-offer! Provide ONLY a JSON object with message (include your proposed price), proposed_price (your counter-offer), accept (true if accepting), reject (true if ending negotiation without agreement), and reason. Do not use any tools, just return the JSON directly."

            # Use LLM directly instead of ReActAgent for negotiation (more reliable for JSON responses)
            try:
                from llama_index.core.llms import ChatMessage
                messages = [
                    ChatMessage(role="system", content=self._get_system_prompt()),
                    ChatMessage(role="user", content=context)
                ]
                response = await self.llm.achat(messages)
                # Extract text from response (handle different response types)
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    response_text = response.message.content
                elif hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
            except Exception as e:
                logger.warning(f"Error with direct LLM call, trying ReActAgent: {str(e)}")
                # Fallback to ReActAgent but extract final response
                response = await self.agent.achat(context)
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    response_text = response.message.content
                elif hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)

            # Parse response (the agent should return JSON)
            # Try to extract JSON from response (handle both direct JSON and wrapped responses)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if not json_match:
                # Try to find JSON in code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    json_match = json_match.group(1)
                else:
                    json_match = None

            if json_match:
                try:
                    # Handle both Match object and string
                    json_str = json_match.group() if hasattr(json_match, 'group') else json_match
                    result = json.loads(json_str)
                    
                    # Ensure all required fields
                    result.setdefault("message", response_text)
                    proposed_price = result.get("proposed_price", merchant_initial_price * 0.9)
                    
                    # STRICT BUDGET ENFORCEMENT - Never allow prices above budget
                    if budget is not None:
                        # Check proposed price
                        if proposed_price > budget:
                            logger.warning(f"Proposed price ${proposed_price:.2f} exceeds budget ${budget:.2f}, capping to budget")
                            proposed_price = budget
                            result["message"] = f"I can offer up to ${budget:.2f} (my budget limit). Can we work with this price?"
                            result["accept"] = False
                            result["reason"] = "Budget constraint - cannot exceed budget"
                        
                        # Check if accepting - NEVER accept if price exceeds budget
                        if result.get("accept", False):
                            # Check both current_price and proposed_price
                            if current_price > budget or proposed_price > budget:
                                result["accept"] = False
                                result["reason"] = "Cannot accept - exceeds budget"
                                max_price = min(current_price, proposed_price, budget)
                                result["proposed_price"] = max_price
                                result["message"] = f"I cannot accept any price above ${budget:.2f} (my budget limit). The best I can offer is ${max_price:.2f}. Can you work with this?"
                                logger.warning(f"Rejected acceptance - price ${current_price:.2f} or ${proposed_price:.2f} exceeds budget ${budget:.2f}")
                        
                        # Check if merchant is repeatedly refusing to meet budget - allow explicit rejection
                        if conversation_history and len(conversation_history) >= 4:
                            # After multiple rounds, if merchant still won't meet budget, allow rejection
                            recent_merchant_prices = [
                                msg.get("proposed_price", float('inf'))
                                for msg in conversation_history[-4:]
                                if msg.get("sender") == "merchant"
                            ]
                            if recent_merchant_prices and all(price > budget for price in recent_merchant_prices):
                                # Merchant has been consistently above budget - allow rejection
                                if current_price > budget * 1.1:  # More than 10% above budget
                                    result["reject"] = True
                                    result["accept"] = False
                                    result["message"] = f"I'm sorry, but I cannot proceed. Your prices consistently exceed my budget of ${budget:.2f}. I cannot accept any offer above this limit."
                                    result["reason"] = f"Merchant prices consistently exceed budget ${budget:.2f}"
                                    logger.info(f"Client explicitly rejecting - merchant won't meet budget after multiple rounds")
                        
                        # If merchant has accepted a price within budget, client should accept too
                        # Check conversation history for merchant acceptance
                        if conversation_history:
                            last_msg = conversation_history[-1]
                            if last_msg.get("sender") == "merchant" and current_price <= budget:
                                # Merchant accepted and price is within budget - client should accept
                                if proposed_price <= budget:
                                    result["accept"] = True
                                    result["reject"] = False
                                    result["proposed_price"] = current_price
                                    result["message"] = f"I accept your offer of ${current_price:.2f}. This is within my budget of ${budget:.2f}. Let's proceed!"
                                    result["reason"] = "Merchant accepted and price is within budget"
                                    logger.info(f"Client accepting merchant's offer ${current_price:.2f} (within budget)")
                    
                    result["proposed_price"] = proposed_price
                    result.setdefault("accept", False)
                    result.setdefault("reject", False)  # Explicit rejection flag
                    result.setdefault("reason", "Negotiating")
                    
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {str(e)}")
                    logger.debug(f"Response text: {response_text[:500]}")
            else:
                logger.warning(f"No JSON found in response: {response_text}")

            # Fallback response with budget enforcement
            fallback_price = merchant_initial_price * 0.9
            if budget is not None:
                fallback_price = min(fallback_price, budget)
            
            return {
                "message": f"I'm interested in {product_name} at ${merchant_initial_price:.2f}. Can we negotiate a better price?{' I have a budget of $' + str(budget) + '.' if budget else ''}",
                "proposed_price": fallback_price,
                "accept": False,
                "reject": False,
                "reason": "Initial negotiation attempt"
            }

        except Exception as e:
            logger.error(f"Error in negotiation: {str(e)}", exc_info=True)
            # Fallback response
            return {
                "message": f"I need to consider this offer for {product_name}. Can we discuss the terms?",
                "proposed_price": merchant_initial_price,
                "accept": False,
                "reject": False,
                "reason": "Error occurred during negotiation"
            }

    async def select_best_offer(
        self,
        offers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select the best offer from multiple merchants.

        Args:
            offers: List of offer dictionaries with:
                - merchant_name
                - price
                - product_name
                - agreed (bool)
                - final_message (optional)

        Returns:
            Dict with selected_offer and reason
        """
        try:
            if not offers:
                return {"selected_offer": None, "reason": "No offers available"}

            context = f"""
You have received {len(offers)} offers for the product. Compare them and select the best one.

Offers:
"""
            for i, offer in enumerate(offers, 1):
                merchant_name = offer.get("merchant_name", "Unknown")
                price = offer.get("price", offer.get("negotiated_price", 0))
                product_name = offer.get("product_name", "Product")
                agreed = offer.get("agreed", False)
                final_message = offer.get("final_message", "")
                status = "AGREED" if agreed else "NOT AGREED"

                context += f"""
{i}. Merchant: {merchant_name}
   Price: ${price:.2f}
   Product: {product_name}
   Status: {status}
   Final Message: {final_message}
"""

            context += "\n\nWhich offer should we accept? Provide a JSON object with selected_offer_index (1-based) and reason."

            response = await self.agent.achat(context)

            # Parse response
            response_text = str(response)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)

            if json_match:
                try:
                    result = json.loads(json_match.group())
                    selected_index = result.get("selected_offer_index", 1) - 1
                    if 0 <= selected_index < len(offers):
                        return {
                            "selected_offer": offers[selected_index],
                            "reason": result.get("reason", "Best price")
                        }
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.warning(f"Failed to parse selection: {str(e)}")

            # Fallback: select lowest price among agreed offers
            agreed_offers = [o for o in offers if o.get("agreed", False)]
            if agreed_offers:
                best = min(agreed_offers, key=lambda x: x.get("price", x.get("negotiated_price", float("inf"))))
                return {"selected_offer": best, "reason": "Lowest price among agreed offers"}
            else:
                # If no agreed offers, select lowest price overall
                best = min(offers, key=lambda x: x.get("price", x.get("negotiated_price", float("inf"))))
                return {"selected_offer": best, "reason": "Lowest price available"}

        except Exception as e:
            logger.error(f"Error selecting best offer: {str(e)}", exc_info=True)
            # Fallback: lowest price
            if offers:
                best = min(offers, key=lambda x: x.get("price", x.get("negotiated_price", float("inf"))))
                return {"selected_offer": best, "reason": "Lowest price (fallback)"}
            return {"selected_offer": None, "reason": "Error occurred"}

