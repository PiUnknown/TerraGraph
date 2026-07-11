import re

_GREETING_PATTERN = re.compile(
    r"^\s*(hi+|hello+|hey+|hiya|yo|hlo|good\s?(morning|afternoon|evening))\s*[!.]*\s*$",
    re.IGNORECASE,
)

_THANKS_PATTERN = re.compile(
    r"^\s*(thanks|thank you|thankyou|thx|ty|appreciate it|cheers)\s*[!.]*\s*$",
    re.IGNORECASE,
)

_FAREWELL_PATTERN = re.compile(
    r"^\s*(bye|goodbye|see ya|see you|take care|later|farewell)\s*[!.]*\s*$",
    re.IGNORECASE,
)

GREETING_RESPONSE = (
    "Hi! I can help you find evidence-backed ways to improve biodiversity on your land. "
    "Tell me a bit about your soil, rainfall, and what's currently growing there, "
    "and I'll look for grounded recommendations."
)

THANKS_RESPONSE = "You're welcome! Let me know if you'd like recommendations for another scenario."

FAREWELL_RESPONSE = "Take care! Come back anytime you want more biodiversity recommendations."


def detect_small_talk(message: str) -> str | None:
    """
    Returns a canned response for pure greetings/thanks/farewells, or
    None if the message contains anything beyond small talk. Patterns
    anchor to the WHOLE message (^...$), not just a keyword's
    presence — "Hi, my soil is dry" must NOT match, since it carries
    real information the extraction pipeline needs to see. Only a
    message that is entirely small talk skips the LLM.
    """
    if _GREETING_PATTERN.match(message):
        return GREETING_RESPONSE
    if _THANKS_PATTERN.match(message):
        return THANKS_RESPONSE
    if _FAREWELL_PATTERN.match(message):
        return FAREWELL_RESPONSE
    return None