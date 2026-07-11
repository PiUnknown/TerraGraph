import json
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.models.schemas import EnvironmentalInput, ChatResponse, Recommendation
from app.knowledge.relationship_graph import match_relationships, attach_evidence
from app.knowledge.vector_store import VectorStore
from app.utils.prompts import build_synthesis_prompt

_groq_client = Groq(api_key=GROQ_API_KEY)

# Lazily constructed on first real use, not at import time. Loading
# the embedding model eagerly at module-import time means it
# initializes during FastAPI's own startup, stacking peak memory
# usage right when the process is most memory-constrained — a real
# problem on Render's 512MB free tier. Deferring construction to the
# first actual request spreads that cost out instead of front-loading it.
_vector_store = None


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def generate_recommendations(user_input: EnvironmentalInput) -> ChatResponse:
    matched = match_relationships(user_input)

    if not matched:
        return ChatResponse(
            message=(
                "I don't have evidence-backed relationships covering this exact combination "
                f"(land use: '{user_input.land_use_type}', rainfall: '{user_input.rainfall}', "
                f"region: '{user_input.region_type}') in my current knowledge base. "
                "My knowledge base currently focuses on cropland practices — monoculture, cover "
                "cropping, crop rotation, and agroforestry — grounded in FAO, IPBES, and peer-reviewed "
                "sources. If your land is grazing pasture, forest, or another system, I may not have "
                "grounded evidence for it yet. Try describing a cropland scenario, or tell me if soil "
                "organic carbon is low (under 0.5%) or land use involves monoculture — those trigger "
                "the most relationships I currently have."
            ),
            recommendations=[],
        )

    enriched = attach_evidence(matched, _get_vector_store(), k=2)
    messages = build_synthesis_prompt(user_input, enriched)

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content

    try:
        parsed = json.loads(raw_content)
        recommendations = [Recommendation(**r) for r in parsed["recommendations"]]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"LLM returned malformed output: {e}\nRaw content: {raw_content}")

    return ChatResponse(
        message=f"Based on your input, I found {len(recommendations)} evidence-backed recommendation(s).",
        recommendations=recommendations,
    )