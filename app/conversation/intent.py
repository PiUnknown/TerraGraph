import re

# Broad on purpose — false positives here are low-risk (worst case,
# an off-topic message gets treated as on-topic, extraction finds
# nothing, and a clarifying question fires once; recoverable next
# turn). False negatives are worse (a real biodiversity question gets
# incorrectly routed to generic chat), so the list errs toward "catch
# more, not less."
_DOMAIN_STEMS = {
    "soil", "land", "farm", "crop", "agri", "forest", "biodivers",
    "ecosystem", "pollinat", "wildlife", "water", "rain", "climate",
    "sustain", "organic", "till", "pasture", "grassland", "wetland",
    "species", "habitat", "pollut", "deforest", "carbon", "moistur",
    "fertil", "erosion", "monocultur", "agroforest", "intercrop",
    "grazing", "irrigat", "drought", "region", "semi-arid", "tropical",
    "desert", "grow", "plant", "vegetat", "yield", "recommend",
}

_TERSE_ANSWER_PATTERN = re.compile(
    r"^\s*(low|moderate|high|\d+(\.\d+)?%?)\s*[.!]?\s*$",
    re.IGNORECASE,
)


def is_on_topic(message: str) -> bool:
    words = re.findall(r"[a-z]+", message.lower())
    return any(any(word.startswith(stem) for stem in _DOMAIN_STEMS) for word in words)


def is_terse_clarification_answer(message: str) -> bool:
    """
    True for short answers that plausibly answer a pending clarifying
    question but contain no domain keywords of their own — "moderate",
    "0.3", "low". Used together with the session's awaiting_clarification
    flag: only when a clarifying question is actually pending should a
    message like this skip the off-topic/general-chat path.
    """
    return bool(_TERSE_ANSWER_PATTERN.match(message)) or len(message.split()) <= 3