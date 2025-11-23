from pydantic import BaseModel
from typing import Dict, Optional


class AgentConfig(BaseModel):
    name: str
    domain: str


class AgentDeployRequest(BaseModel):
    agent_type: str
    config: AgentConfig


class AgentDeployResponse(BaseModel):
    agent_id: str
    status: str
    agent0_id: Optional[str] = None
    metadata: Optional[Dict] = None
    avatar_url: Optional[str] = None

