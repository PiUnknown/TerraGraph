import json
import re
from app.models.schemas import EnvironmentalInput
from app.knowledge.vector_store import VectorStore

RELATIONSHIPS_PATH = "app/knowledge/relationships.json"

NUMERIC_METRICS = {"soil_organic_carbon_pct", "soil_ph", "temperature_c"}

# Boolean input fields. Previously unhandled by match_relationships —
# deforestation_present and pollution_present were collected in the
# schema and asked about in the assignment's "human impact" knowledge
# category, but no matching branch ever checked them, so any
# relationship keyed on them could never fire. This set + the new
# elif branch below fixes that.
BOOLEAN_METRICS = {"deforestation_present", "pollution_present"}

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


def _word_matches(keyword: str, token: str) -> bool:
    """
    True if keyword and token are the same word or clear variants of
    each other (intensive/intensively, degraded/degrade, managed/
    management, converted/conversion). Uses a shared-prefix check
    rather than exact equality, since real-world phrasing varies in
    tense/form and exact matching missed genuine matches.

    Only applies the fuzzy prefix check for words 5+ characters long,
    specifically to avoid resurrecting the earlier substring bug
    (e.g. "land" must NOT fuzzy-match "landscape" or "grassland" —
    both keyword and token need real shared stems, not a short
    coincidental prefix).
    """
    if keyword == token:
        return True
    if len(keyword) >= 5 and len(token) >= 5:
        return keyword[:5] == token[:5]
    return False


def _matches_categorical(value: str, condition: str, match_mode: str = "any") -> bool:
    if not value:
        return False

    value_words = set(re.findall(r"[a-z0-9]+", value.lower()))

    condition_clean = re.sub(r"[^\w\s]", " ", condition.lower())
    keywords = [w for w in condition_clean.split() if w and w not in STOPWORDS]

    if not keywords:
        return False

    def keyword_hit(keyword: str) -> bool:
        return any(_word_matches(keyword, token) for token in value_words)

    if match_mode == "all":
        return all(keyword_hit(k) for k in keywords)
    return any(keyword_hit(k) for k in keywords)


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
        elif trigger_metric in BOOLEAN_METRICS:
            if isinstance(input_value, bool) and str(input_value).lower() == trigger_condition.lower():
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