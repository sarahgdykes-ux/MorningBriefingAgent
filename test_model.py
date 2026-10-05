import os
from dotenv import load_dotenv
from strands_agents import Agent, LiteLLM

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

model = LiteLLM(
    base_url="https://openrouter.ai/api/v1",
    model_id="openrouter/openrouter/free",
    api_key=api_key,
    params={"max_tokens": 256}
)

agent = Agent(
    model=model,
    tools=[]
)

result = agent.run("Say hello and tell me what model you are in one sentence.")
print(result)
