from fastapi import APIRouter
from pydantic import BaseModel

from app.models.schemas import ChatResponse, EnvironmentalInput
from app.reasoning.metric_extractor import extract_metrics, merge_inputs
from app.conversation.session_manager import get_session, update_accumulated_input, append_turn
from app.conversation.clarifier import build_clarifying_question
from app.conversation.small_talk import detect_small_talk
from app.reasoning.synthesizer import generate_recommendations

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class StructuredChatRequest(BaseModel):
    session_id: str
    input_data: EnvironmentalInput


def _last_assistant_question(session: dict) -> str | None:
    """
    Finds the most recent assistant turn, if any, so extraction can
    interpret a terse reply ("Moderate") as answering that specific
    question rather than guessing blind from the word alone.
    """
    for turn in reversed(session["history"]):
        if turn["role"] == "assistant":
            return turn["content"]
    return None


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session = get_session(request.session_id)

    # Pure small talk (greeting/thanks/farewell) never needs the LLM —
    # deterministic, instant, zero token cost. Checked first and
    # regardless of session state, so "thanks" after recommendations
    # already exist still works correctly.
    small_talk_response = detect_small_talk(request.message)
    if small_talk_response:
        append_turn(request.session_id, "user", request.message)
        append_turn(request.session_id, "assistant", small_talk_response)
        return ChatResponse(message=small_talk_response)

    context = _last_assistant_question(session)
    append_turn(request.session_id, "user", request.message)

    newly_extracted = extract_metrics(request.message, context=context)
    merged_input = merge_inputs(session["accumulated_input"], newly_extracted)
    update_accumulated_input(request.session_id, merged_input)

    clarifying_question = build_clarifying_question(merged_input)

    if clarifying_question:
        response = ChatResponse(message=clarifying_question, clarifying_question=clarifying_question)
        append_turn(request.session_id, "assistant", clarifying_question)
        return response

    result = generate_recommendations(merged_input)
    append_turn(request.session_id, "assistant", result.message)
    return result


@router.post("/chat/structured", response_model=ChatResponse)
def chat_structured(request: StructuredChatRequest) -> ChatResponse:
    session = get_session(request.session_id)
    merged_input = merge_inputs(session["accumulated_input"], request.input_data)
    update_accumulated_input(request.session_id, merged_input)

    clarifying_question = build_clarifying_question(merged_input)
    if clarifying_question:
        return ChatResponse(message=clarifying_question, clarifying_question=clarifying_question)

    return generate_recommendations(merged_input)