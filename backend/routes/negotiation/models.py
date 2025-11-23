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

