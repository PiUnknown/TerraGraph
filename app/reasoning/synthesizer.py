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
            message="I couldn't match your input to any known relationship in the knowledge base. "
                    "This usually means the values are outside the ranges I have evidence for, "
                    "or a required field is missing.",
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