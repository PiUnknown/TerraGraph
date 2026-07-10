from app.models.schemas import EnvironmentalInput

FIELD_PROMPTS = {
    "soil_organic_carbon_pct": "your soil organic carbon percentage (or a rough estimate, e.g. 'low'/'moderate')",
    "rainfall": "the rainfall pattern in your area (low, moderate, or high)",
    "land_use_type": "what's currently growing there (e.g. monoculture wheat, mixed cropping, grassland)",
    "region_type": "the general region/climate type (e.g. semi-arid, tropical, temperate)",
}


def build_clarifying_question(user_input: EnvironmentalInput) -> str | None:
    missing = user_input.missing_required_fields()
    if not missing:
        return None

    asks = [FIELD_PROMPTS[field] for field in missing if field in FIELD_PROMPTS]

    if len(asks) == 1:
        return f"Could you tell me {asks[0]}?"

    joined = "; ".join(asks[:-1]) + f"; and {asks[-1]}"
    return f"To give you a grounded recommendation, could you share: {joined}?"