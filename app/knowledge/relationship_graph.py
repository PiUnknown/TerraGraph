import json
import re
from app.models.schemas import EnvironmentalInput
from app.knowledge.vector_store import VectorStore

RELATIONSHIPS_PATH = "app/knowledge/relationships.json"

NUMERIC_METRICS = {"soil_organic_carbon_pct", "soil_ph", "temperature_c"}

STOPWORDS = {"and", "or", "the", "a", "to", "of", "from", "with", "without", "in", "on", "at"}


def _load_relationships(path: str = RELATIONSHIPS_PATH) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("relationships", [])

    if not isinstance(data, list) or (data and not isinstance(data[0], dict)):
        raise ValueError(
            f"{path} did not parse into a list of relationship objects. "
            f"Got type: {type(data)}. Check the file's top-level structure."
        )

    return data


def _matches_numeric(value: float, condition: str) -> bool:
    match = re.match(r"\s*(<=|>=|<|>|==)\s*([\d.]+)", condition)
    if not match:
        return False

    op, threshold_str = match.group(1), match.group(2)
    threshold = float(threshold_str)

    if op == "<":
        return value < threshold
    if op == ">":
        return value > threshold
    if op == "<=":
        return value <= threshold
    if op == ">=":
        return value >= threshold
    if op == "==":
        return value == threshold
    return False


def _matches_categorical(value: str, condition: str, match_mode: str = "any") -> bool:
    if not value:
        return False

    value_lower = value.lower()
    condition_clean = re.sub(r"[^\w\s]", " ", condition.lower())
    keywords = [w for w in condition_clean.split() if w and w not in STOPWORDS]

    if not keywords:
        return False

    if match_mode == "all":
        return all(keyword in value_lower for keyword in keywords)
    return any(keyword in value_lower for keyword in keywords)


def match_relationships(user_input: EnvironmentalInput, relationships: list[dict] = None) -> list[dict]:
    if relationships is None:
        relationships = _load_relationships()

    input_dict = user_input.model_dump()
    matched = []

    for rel in relationships:
        trigger_metric = rel["trigger"]["metric"]
        trigger_condition = rel["trigger"]["condition"]

        input_value = input_dict.get(trigger_metric)
        if input_value is None:
            continue

        if trigger_metric in NUMERIC_METRICS:
            if isinstance(input_value, (int, float)) and _matches_numeric(input_value, trigger_condition):
                matched.append(rel)
        else:
            match_mode = rel["trigger"].get("match_mode", "any")
            if isinstance(input_value, str) and _matches_categorical(input_value, trigger_condition, match_mode):
                matched.append(rel)

    return matched


def attach_evidence(matched_relationships: list[dict], vector_store: VectorStore, k: int = 2) -> list[dict]:
    enriched = []
    for rel in matched_relationships:
        query = f"{rel['affects_metric']} {rel['mechanism']}"
        evidence = vector_store.retrieve(query, k=k)
        enriched.append({**rel, "evidence": evidence})
    return enriched