import sys, json
from chaos_agent import create_chaos_agent
from eliza_agent import create_eliza_agent
from prompts import SELLER_PROMPT, BUYER_PROMPT
from tools import build_tools
from chaoschain_sdk import AgentRole

agent_type = sys.argv[1]
config = json.loads(sys.argv[2])

if agent_type == "seller":
    role = AgentRole.SERVER
    prompt = SELLER_PROMPT
else:
    role = AgentRole.CLIENT
    prompt = BUYER_PROMPT

sdk, agent_id = create_chaos_agent(config["name"], config["domain"], role)

eliza = create_eliza_agent(prompt)
eliza.tools = build_tools(sdk)

print(json.dumps({
    "agent_id": agent_id,
    "status": "deployed"
}))
