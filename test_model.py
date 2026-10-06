import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.litellm import LiteLLMModel

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

model = LiteLLMModel(
    client_args={
        "api_key": api_key,
        "api_base": "https://openrouter.ai/api/v1"
    },
    model_id="openrouter/openai/gpt-3.5-turbo",
    params={"max_tokens": 256}
)

agent = Agent(
    model=model,
    tools=[]
)

result = agent("Say hello and tell me what model you are in one sentence.")
print(result)
