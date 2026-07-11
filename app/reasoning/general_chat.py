from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL

_groq_client = Groq(api_key=GROQ_API_KEY)

GENERAL_CHAT_SYSTEM_PROMPT = """You are a friendly assistant embedded in the
Darukaa.Earth Biodiversity Intelligence Chatbot. For questions unrelated to
soil, land, biodiversity, or agriculture, answer normally and helpfully like
any general-purpose assistant would. Keep it brief. Don't force a mention of
biodiversity/land topics into every reply — only bring it up if it's
genuinely relevant to what was asked."""


def general_chat_reply(message: str) -> str:
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": GENERAL_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content