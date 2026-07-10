import json
from app.models.schemas import EnvironmentalInput

SYSTEM_PROMPT = """You are an environmental scientist assistant. You will be given:
1. A user's environmental/land data
2. A list of scientifically-grounded relationships that were matched to that data, each with a mechanism, a suggested intervention, and supporting evidence excerpts from real sources

Your job is to turn each matched relationship into ONE recommendation. Rules:

- Produce exactly ONE recommendation per matched relationship you were given. Do NOT merge two or more relationships into a single recommendation, even if their interventions sound similar — each relationship has its own specific evidence and source, and merging loses that specificity.
- The only exception: if two relationships have the EXACT same intervention text, you may combine them, but you must still preserve the most specific estimated_effect and impacted_metrics from BOTH — never replace a concrete number with a vague phrase like "qualitative directional relationship" when a concrete number was available in either source.
- Do NOT invent facts, numbers, or sources beyond what is given to you below
- Every recommendation's "mechanism" and "estimated_effect" must be traceable to the matched relationship it came from
- If a relationship's estimated_effect field contains a specific number or range, that exact number must appear in your output's estimated_effect. Only use directional/qualitative language when the source relationship itself has no number.
- Output ONLY a JSON object of the exact shape shown below — no prose before or after

Output shape:
{
  "recommendations": [
    {
      "action": "string - what to do, concretely",
      "mechanism": "string - why it works",
      "impacted_metrics": ["string", "..."],
      "estimated_effect": "string or null",
      "time_horizon": "short_term | medium_term | long_term",
      "confidence": "high | medium | low",
      "source": "string - citation"
    }
  ]
}
"""


def build_synthesis_prompt(user_input: EnvironmentalInput, matched_relationships: list[dict]) -> list[dict]:
    trimmed_relationships = []
    for rel in matched_relationships:
        trimmed_relationships.append({
            "affects_metric": rel["affects_metric"],
            "mechanism": rel["mechanism"],
            "intervention": rel["intervention"],
            "estimated_effect": rel["estimated_effect"],
            "source": rel["source"],
            "evidence_excerpts": [e["text"][:400] for e in rel.get("evidence", [])],
        })

    user_content = {
        "user_environmental_data": user_input.model_dump(exclude_none=True),
        "matched_relationships": trimmed_relationships,
    }

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_content, indent=2)},
    ]