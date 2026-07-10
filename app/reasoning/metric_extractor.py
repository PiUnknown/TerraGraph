import json
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.models.schemas import EnvironmentalInput

_groq_client = Groq(api_key=GROQ_API_KEY)

EXTRACTION_SYSTEM_PROMPT = """You extract structured environmental data from a user's message.

Return ONLY a JSON object with these keys (use null for anything not mentioned or not inferable with confidence):
- soil_organic_carbon_pct (float, percentage)
- soil_ph (float)
- soil_moisture (string: "low"/"moderate"/"high")
- rainfall (string: "low"/"moderate"/"high")
- land_use_type (string, e.g. "monoculture wheat")
- region_type (string, e.g. "semi-arid")
- temperature_c (float)
- species_richness (string)
- deforestation_present (boolean)
- pollution_present (boolean)
- latitude (float)
- longitude (float)

Rules:
- Do NOT invent a value the user didn't state or clearly imply
- "pretty dry" -> rainfall: "low" is a fair inference; a specific number the user never gave is not
- Output ONLY the JSON object, no prose
"""


def extract_metrics(message: str) -> EnvironmentalInput:
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return EnvironmentalInput()

    return EnvironmentalInput(**{k: v for k, v in parsed.items() if v is not None})


def merge_inputs(existing: EnvironmentalInput, new: EnvironmentalInput) -> EnvironmentalInput:
    existing_dict = existing.model_dump()
    new_dict = new.model_dump()

    merged = {
        field: (new_dict[field] if new_dict[field] is not None else existing_dict[field])
        for field in existing_dict
    }
    return EnvironmentalInput(**merged)