from app.models.schemas import EnvironmentalInput

_sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "accumulated_input": EnvironmentalInput(),
            "history": [],
            "awaiting_clarification": False,
        }
    return _sessions[session_id]


def update_accumulated_input(session_id: str, new_input: EnvironmentalInput) -> EnvironmentalInput:
    session = get_session(session_id)
    session["accumulated_input"] = new_input
    return new_input


def append_turn(session_id: str, role: str, content: str) -> None:
    session = get_session(session_id)
    session["history"].append({"role": role, "content": content})


def set_awaiting_clarification(session_id: str, value: bool) -> None:
    """
    Tracks whether the assistant's LAST turn was specifically a
    clarifying question — distinct from "was there any prior assistant
    turn at all." Only when this is True should a terse, keyword-free
    reply ("moderate", "0.3") be routed through extraction instead of
    general chat.
    """
    session = get_session(session_id)
    session["awaiting_clarification"] = value