from pydantic import BaseModel
from typing import Optional


class UserLoginRequest(BaseModel):
    privy_user_id: str
    wallet_address: str
    email: Optional[str] = None
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    privy_user_id: str
    wallet_address: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: str

