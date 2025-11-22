from chaoschain_sdk import ChaosChainAgentSDK, NetworkConfig, AgentRole

def create_chaos_agent(agent_name, agent_domain, role):
    sdk = ChaosChainAgentSDK(
        agent_name=agent_name,
        agent_domain=agent_domain,
        agent_role=role,
        network=NetworkConfig.BASE_SEPOLIA,
        enable_ap2=True,
        enable_process_integrity=True,
        enable_payments=True
    )

    agent_id, tx_hash = sdk.register_identity()
    return sdk, agent_id
