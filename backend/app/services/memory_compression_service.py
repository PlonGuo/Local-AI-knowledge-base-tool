"""Memory compression service — summarize conversation history for layered memory."""
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import AppConfig
from app.services.llm_factory import create_chat_model

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM_PROMPT = (
    "You are a conversation summarizer. Given a sequence of chat messages, "
    "produce a concise summary that captures the key topics discussed, "
    "questions asked, and answers provided. Focus on information that would "
    "be useful context for future questions. Write in third person."
)

SUMMARIZE_USER_PROMPT = "Summarize the following conversation:\n\n{conversation}"


def _format_messages(messages: list[dict[str, str]]) -> str:
    """Format message dicts into a readable conversation transcript."""
    lines = []
    for msg in messages:
        role = msg["role"].capitalize()
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


async def summarize_messages(
    messages: list[dict[str, str]], config: AppConfig
) -> str:
    """Summarize a list of chat messages using the LLM.

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        config: App configuration for LLM access.

    Returns:
        A concise summary string. Falls back to empty string on error.
    """
    if not messages:
        return ""

    try:
        model = create_chat_model(config)
        conversation = _format_messages(messages)
        lc_messages = [
            SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT),
            HumanMessage(content=SUMMARIZE_USER_PROMPT.format(conversation=conversation)),
        ]
        response = await model.ainvoke(lc_messages)
        content = response.content
        if not content or not content.strip():
            return ""
        return content.strip()
    except Exception:
        logger.warning("Message summarization failed, returning empty summary", exc_info=True)
        return ""
