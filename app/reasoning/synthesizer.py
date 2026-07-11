import json
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.models.schemas import EnvironmentalInput, ChatResponse, Recommendation
from app.knowledge.relationship_graph import match_relationships, attach_evidence
from app.knowledge.vector_store import VectorStore
from app.utils.prompts import build_synthesis_prompt

_groq_client = Groq(api_key=GROQ_API_KEY)
_vector_store = VectorStore()


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

    enriched = attach_evidence(matched, _vector_store, k=2)
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