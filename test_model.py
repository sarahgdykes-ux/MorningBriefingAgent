import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.litellm import LiteLLMModel

load_dotenv()

# Prefer Anthropic if available, otherwise use OpenRouter
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")

if anthropic_key:
    # Use Anthropic
    model = LiteLLMModel(
        client_args={
            "api_key": anthropic_key
        },
        model_id="anthropic/claude-3-haiku-20240307",
        params={"max_tokens": 256}
    )
elif openrouter_key:
    # Use OpenRouter as fallback
    model = LiteLLMModel(
        client_args={
            "api_key": openrouter_key,
            "api_base": "https://openrouter.ai/api/v1"
        },
        model_id="openrouter/openai/gpt-3.5-turbo",
        params={"max_tokens": 256}
    )
else:
    raise ValueError("Neither ANTHROPIC_API_KEY nor OPENROUTER_API_KEY is set in .env")

agent = Agent(
    model=model,
    tools=[]
)

result = agent("Say hello and tell me what model you are in one sentence.")
print(result)
