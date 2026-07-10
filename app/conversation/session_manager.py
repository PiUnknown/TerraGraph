from app.models.schemas import EnvironmentalInput

_sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "accumulated_input": EnvironmentalInput(),
            "history": [],
        }
    return _sessions[session_id]


def update_accumulated_input(session_id: str, new_input: EnvironmentalInput) -> EnvironmentalInput:
    session = get_session(session_id)
    session["accumulated_input"] = new_input
    return new_input


def append_turn(session_id: str, role: str, content: str) -> None:
    session = get_session(session_id)
    session["history"].append({"role": role, "content": content})