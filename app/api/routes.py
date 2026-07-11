from fastapi import APIRouter
from pydantic import BaseModel

from app.models.schemas import ChatResponse, EnvironmentalInput
from app.reasoning.metric_extractor import extract_metrics, merge_inputs
from app.reasoning.general_chat import general_chat_reply
from app.conversation.session_manager import (
    get_session, update_accumulated_input, append_turn, set_awaiting_clarification,
)
from app.conversation.clarifier import build_clarifying_question
from app.conversation.small_talk import detect_small_talk
from app.conversation.intent import is_on_topic, is_terse_clarification_answer
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
    # deterministic, instant, zero token cost.
    small_talk_response = detect_small_talk(request.message)
    if small_talk_response:
        append_turn(request.session_id, "user", request.message)
        append_turn(request.session_id, "assistant", small_talk_response)
        set_awaiting_clarification(request.session_id, False)
        return ChatResponse(message=small_talk_response)

    context = _last_assistant_question(session)
    awaiting = session.get("awaiting_clarification", False)

    # Off-topic gate: route to general chat only when the message is
    # NEITHER on-topic itself NOR a terse answer to a clarifying
    # question that is actually currently pending. Checking
    # "awaiting_clarification" specifically (not just "was there any
    # prior assistant turn") is what fixes repeated off-topic messages
    # incorrectly being forced through extraction after any assistant
    # reply, including a previous general-chat answer.
    if not is_on_topic(request.message) and not (awaiting and is_terse_clarification_answer(request.message)):
        append_turn(request.session_id, "user", request.message)
        reply = general_chat_reply(request.message)
        append_turn(request.session_id, "assistant", reply)
        set_awaiting_clarification(request.session_id, False)
        return ChatResponse(message=reply)

    append_turn(request.session_id, "user", request.message)

    newly_extracted = extract_metrics(request.message, context=context)
    merged_input = merge_inputs(session["accumulated_input"], newly_extracted)
    update_accumulated_input(request.session_id, merged_input)

    clarifying_question = build_clarifying_question(merged_input)

    if clarifying_question:
        response = ChatResponse(message=clarifying_question, clarifying_question=clarifying_question)
        append_turn(request.session_id, "assistant", clarifying_question)
        set_awaiting_clarification(request.session_id, True)
        return response

    result = generate_recommendations(merged_input)
    append_turn(request.session_id, "assistant", result.message)
    set_awaiting_clarification(request.session_id, False)
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