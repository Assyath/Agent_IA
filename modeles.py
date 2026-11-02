
import os
from dotenv import load_dotenv

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

# Configuration du fournisseur RodiumAI
provider = OpenAIProvider(
    base_url="https://api.rodiumai.io/v1",
    api_key=os.environ["RODIUMAI_API_KEY"],
)

# Modèle utilisé par les agents
gpt_model = OpenAIChatModel(
    "anthropic/claude-haiku-4-5-20251001",
    provider=provider,
)

# Modèle utilisé pour l'évaluation
haiku_model = OpenAIChatModel(
    "anthropic/claude-haiku-5-5",
    provider=provider,
)
