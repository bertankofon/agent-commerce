from pydantic import BaseModel
from typing import Dict, Optional, List


class NegotiateAndPayRequest(BaseModel):
    agent_id: str
    product_query: str
    budget: Optional[float] = None
    rounds: Optional[int] = 5
    dry_run: Optional[bool] = False


class NegotiateAndPayResponse(BaseModel):
    status: str
    client_agent_id: str
    product_query: str
    session_id: Optional[str] = None
    total_products_found: int
    total_negotiations: int
    best_offer: Optional[Dict] = None
    payment_result: Optional[Dict] = None
    results_by_product: Optional[List[Dict]] = None
    error: Optional[str] = None


class SingleNegotiationRequest(BaseModel):
    """Request for single negotiation between specific client and merchant."""
    client_agent_id: str
    merchant_agent_id: str
    product_id: str
    budget: float
    rounds: Optional[int] = 5
    dry_run: Optional[bool] = False


class SingleNegotiationResponse(BaseModel):
    """Response for single negotiation with payment."""
    status: str
    client_agent_id: str
    merchant_agent_id: str
    product_id: str
    product_name: Optional[str] = None
    initial_price: Optional[float] = None
    final_price: Optional[float] = None
    agreed: bool = False
    negotiation_rounds: int = 0
    negotiation_history: Optional[List[Dict]] = None
    payment_result: Optional[Dict] = None
    error: Optional[str] = None

