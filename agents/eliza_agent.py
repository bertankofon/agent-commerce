from eliza.agent import Agent

def create_eliza_agent(personality_prompt: str):
    return Agent(
        instructions=personality_prompt,
        memory=True,
        llm_model="gpt-4.1-mini"
    )
