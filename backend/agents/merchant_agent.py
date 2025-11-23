"""Merchant Agent (Seller) for e-commerce negotiations using LlamaIndex."""

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


class MerchantAgent:
    """
    LlamaIndex-based merchant agent that negotiates with buyers.
    Acts as a seller agent that tries to maximize profit while remaining competitive.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        llm_model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        negotiation_percentage: Optional[float] = None
    ):
        """
        Initialize the merchant agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_name: Name of the agent
            llm_model: OpenAI model to use (default: gpt-4o-mini)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            negotiation_percentage: Maximum percentage below initial price the merchant can go
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.negotiation_percentage = negotiation_percentage
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

            # Create tools
            self.tools = self._create_tools()

            # Initialize memory for the agent
            memory = ChatMemoryBuffer.from_defaults()

            # Initialize ReAct agent (direct instantiation for llama-index 0.14+)
            # Note: system_prompt is not a valid parameter for ReActAgent.__init__()
            # The system prompt is handled in direct LLM calls during negotiation
            self.agent = ReActAgent(
                tools=self.tools,
                llm=self.llm,
                memory=memory,
                verbose=True
            )

            logger.info(
                f"MerchantAgent initialized: {agent_name} (ID: {agent_id})"
                f"{f' - Max discount: {negotiation_percentage}%' if negotiation_percentage else ''}"
            )

        except Exception as e:
            logger.error(f"Error initializing MerchantAgent: {str(e)}", exc_info=True)
            raise

    def _get_system_prompt(self, negotiation_percentage: Optional[float] = None) -> str:
        """
        Get the system prompt for the merchant agent.
        
        Args:
            negotiation_percentage: Maximum percentage below initial price the merchant can go
        """
        base_prompt = f"""You are a merchant agent named {self.agent_name} selling products.

Your goal is to negotiate with buyers to make sales while maximizing profit.

When negotiating:
- Be professional and helpful
- Try to maximize price while remaining competitive
- Consider market value and your costs
- Make reasonable counter-offers
- Accept deals that are profitable
- You can explicitly end negotiations if the buyer's offers are too low or unreasonable
- If you want to end negotiation without agreement, set "reject": true in your response"""

        if negotiation_percentage is not None:
            base_prompt += f"""
- IMPORTANT: You can go up to {negotiation_percentage}% below the initial price
- Your minimum acceptable price is {100 - negotiation_percentage}% of the initial price
- Do NOT accept offers below this minimum price
- You can offer discounts up to {negotiation_percentage}% to close sales"""
        else:
            base_prompt += """
- Be willing to offer discounts to close sales (up to 15-20% discount is acceptable)
- Don't go below your cost price"""

        base_prompt += """

Always respond with a JSON object containing:
- "message": Your negotiation message (string)
- "proposed_price": The price you're proposing (float)
- "accept": true/false - whether you accept the buyer's offer
- "reject": true/false - whether you want to end negotiation without agreement (use when buyer won't meet your minimum price or negotiations are unproductive)
- "reason": Brief reason for your decision (string)

Be competitive but protect your profit margins."""

        return base_prompt

    def _create_tools(self) -> list:
        """Create tools for the merchant agent."""

        def calculate_profit_margin(
            selling_price: float,
            cost_price: float
        ) -> Dict[str, Any]:
            """
            Calculate profit margin for a sale.

            Args:
                selling_price: The price at which you're selling
                cost_price: Your cost price for the product

            Returns:
                Dictionary with profit calculations
            """
            try:
                profit = selling_price - cost_price
                margin = (profit / selling_price) * 100 if selling_price > 0 else 0

                return {
                    "profit": round(profit, 2),
                    "margin_percent": round(margin, 2),
                    "is_profitable": profit > 0,
                    "recommendation": "accept" if profit > 0 and margin >= 10 else "negotiate"
                }
            except Exception as e:
                logger.error(f"Error in calculate_profit_margin: {str(e)}")
                return {
                    "profit": 0,
                    "margin_percent": 0,
                    "is_profitable": False,
                    "recommendation": "negotiate"
                }

        tools = [
            FunctionTool.from_defaults(fn=calculate_profit_margin)
        ]

        return tools

    async def negotiate_with_buyer(
        self,
        product_name: str,
        initial_price: float,
        buyer_offer: float,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Respond to buyer's negotiation offer.

        Args:
            product_name: Name of the product
            initial_price: Your initial asking price
            buyer_offer: The price the buyer is offering
            conversation_history: List of previous messages in format:
                [{"sender": "client"|"merchant", "message": "...", "proposed_price": float}]

        Returns:
            Dict with message, proposed_price, accept, and reason
        """
        try:
            # Calculate discount percentage
            discount = ((initial_price - buyer_offer) / initial_price) * 100 if initial_price > 0 else 0
            
            # Calculate minimum acceptable price based on negotiation_percentage
            min_price = None
            if self.negotiation_percentage is not None:
                min_price = initial_price * (1 - self.negotiation_percentage / 100)
                min_price = round(min_price, 2)

            context = f"""
Product: {product_name}
Your Initial Price: ${initial_price:.2f}
Buyer's Offer: ${buyer_offer:.2f}
Discount Requested: {discount:.1f}%"""
            
            if min_price is not None:
                context += f"""
Minimum Acceptable Price: ${min_price:.2f} (You can go up to {self.negotiation_percentage}% below initial price)
Buyer's Offer is {'ABOVE' if buyer_offer >= min_price else 'BELOW'} your minimum price"""
            
            context += """

Conversation History:
"""
            # Add last 5 messages for context
            for msg in conversation_history[-5:]:
                sender = msg.get("sender", "unknown")
                message = msg.get("message", "")
                price = msg.get("proposed_price")
                price_str = f" (${price:.2f})" if price else ""
                context += f"\n{sender}: {message}{price_str}\n"

            context += "\n\nWhat is your response? Provide ONLY a JSON object with message, proposed_price, accept (true if accepting), reject (true if ending negotiation without agreement), and reason. Do not use any tools, just return the JSON directly."

            # Use LLM directly instead of ReActAgent for negotiation (more reliable for JSON responses)
            try:
                from llama_index.core.llms import ChatMessage
                messages = [
                    ChatMessage(role="system", content=self._get_system_prompt(self.negotiation_percentage)),
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

            # Parse response - try multiple patterns
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
                    result.setdefault("proposed_price", buyer_offer)
                    result.setdefault("accept", False)
                    result.setdefault("reject", False)  # Explicit rejection flag
                    result.setdefault("reason", "Negotiating")
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {str(e)}")
                    logger.debug(f"Response text: {response_text[:500]}")
            else:
                logger.warning(f"No JSON found in response: {response_text}")

            # Fallback logic with negotiation_percentage constraint
            if self.negotiation_percentage is not None:
                min_price = initial_price * (1 - self.negotiation_percentage / 100)
                min_price = round(min_price, 2)
                
                # Check if buyer offer is above minimum
                if buyer_offer >= min_price:
                    # Accept if reasonable discount, otherwise counter
                    if discount <= self.negotiation_percentage * 0.7:  # Accept if within 70% of max discount
                        return {
                            "message": f"I accept your offer of ${buyer_offer:.2f}. Let's proceed!",
                            "proposed_price": buyer_offer,
                            "accept": True,
                            "reject": False,
                            "reason": f"Offer is above minimum price (${min_price:.2f}) and within acceptable discount"
                        }
                    else:
                        # Counter-offer closer to minimum but still reasonable
                        counter_price = max(min_price, (initial_price + buyer_offer) / 2)
                        counter_price = round(counter_price, 2)
                        return {
                            "message": f"I can offer ${counter_price:.2f} as my best price. This is my minimum acceptable price.",
                            "proposed_price": counter_price,
                            "accept": False,
                            "reject": False,
                            "reason": f"Counter-offer at minimum price (${min_price:.2f})"
                        }
                else:
                    # Buyer offer is below minimum - can reject if too far below
                    if buyer_offer < min_price * 0.8:  # More than 20% below minimum
                        return {
                            "message": f"I'm sorry, but ${buyer_offer:.2f} is too far below my minimum price of ${min_price:.2f}. I cannot proceed with this negotiation.",
                            "proposed_price": min_price,
                            "accept": False,
                            "reject": True,  # Explicit rejection
                            "reason": f"Buyer offer too far below minimum price (${min_price:.2f})"
                        }
                    else:
                        return {
                            "message": f"I'm sorry, but ${buyer_offer:.2f} is below my minimum price of ${min_price:.2f}. I can go as low as ${min_price:.2f}.",
                            "proposed_price": min_price,
                            "accept": False,
                            "reject": False,
                            "reason": f"Buyer offer below minimum price (${min_price:.2f})"
                        }
            else:
                # No negotiation_percentage constraint - use original logic
                if discount <= 15:
                    return {
                        "message": f"I accept your offer of ${buyer_offer:.2f}. Let's proceed!",
                        "proposed_price": buyer_offer,
                        "accept": True,
                        "reject": False,
                        "reason": "Reasonable discount within acceptable margin"
                    }
                else:
                    # Counter-offer: split the difference
                    counter_price = (initial_price + buyer_offer) / 2
                    return {
                        "message": f"I can offer ${counter_price:.2f} as my best price. This is a {((initial_price - counter_price) / initial_price) * 100:.1f}% discount.",
                        "proposed_price": counter_price,
                        "accept": False,
                        "reject": False,
                        "reason": "Counter-offer to meet in the middle"
                    }

        except Exception as e:
            logger.error(f"Error in merchant negotiation: {str(e)}", exc_info=True)
            # Fallback response with negotiation_percentage constraint
            discount = ((initial_price - buyer_offer) / initial_price) * 100 if initial_price > 0 else 0
            
            if self.negotiation_percentage is not None:
                min_price = initial_price * (1 - self.negotiation_percentage / 100)
                min_price = round(min_price, 2)
                
                if buyer_offer >= min_price:
                    return {
                        "message": f"I can accept ${buyer_offer:.2f} for {product_name}.",
                        "proposed_price": buyer_offer,
                        "accept": True,
                        "reject": False,
                        "reason": f"Acceptable offer above minimum (${min_price:.2f})"
                    }
                else:
                    return {
                        "message": f"I can offer ${min_price:.2f} as my best price for {product_name} (minimum acceptable).",
                        "proposed_price": min_price,
                        "accept": False,
                        "reject": False,
                        "reason": f"Minimum price constraint (${min_price:.2f})"
                    }
            else:
                # Original fallback logic
                if discount <= 15:
                    return {
                        "message": f"I can accept ${buyer_offer:.2f} for {product_name}.",
                        "proposed_price": buyer_offer,
                        "accept": True,
                        "reject": False,
                        "reason": "Acceptable discount (fallback)"
                    }
                else:
                    return {
                        "message": f"I can offer ${initial_price * 0.9:.2f} as my best price for {product_name}.",
                        "proposed_price": initial_price * 0.9,
                        "accept": False,
                        "reject": False,
                        "reason": "Error occurred, using fallback counter-offer"
                    }

