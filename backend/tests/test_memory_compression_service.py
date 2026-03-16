"""Tests for memory compression service (Tasks 134-135)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import AppConfig
from app.services.memory_compression_service import (
    SUMMARIZE_SYSTEM_PROMPT,
    SUMMARIZE_USER_PROMPT,
    _format_messages,
    summarize_messages,
)


# ---------------------------------------------------------------------------
# _format_messages
# ---------------------------------------------------------------------------

class TestFormatMessages:
    def test_formats_user_and_assistant(self):
        messages = [
            {"role": "user", "content": "What is BFS?"},
            {"role": "assistant", "content": "BFS is breadth-first search."},
        ]
        result = _format_messages(messages)
        assert "User: What is BFS?" in result
        assert "Assistant: BFS is breadth-first search." in result

    def test_empty_list(self):
        assert _format_messages([]) == ""


# ---------------------------------------------------------------------------
# summarize_messages
# ---------------------------------------------------------------------------

class TestSummarizeMessages:
    @pytest.fixture
    def config(self):
        return AppConfig()

    @pytest.mark.asyncio
    async def test_returns_summary(self, config):
        mock_response = MagicMock()
        mock_response.content = "The user asked about BFS and received an explanation."
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(
                [{"role": "user", "content": "What is BFS?"}], config
            )
        assert result == "The user asked about BFS and received an explanation."

    @pytest.mark.asyncio
    async def test_empty_messages_returns_empty(self, config):
        result = await summarize_messages([], config)
        assert result == ""

    @pytest.mark.asyncio
    async def test_llm_called_with_correct_messages(self, config):
        mock_response = MagicMock()
        mock_response.content = "summary"
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            await summarize_messages(messages, config)

        call_args = mock_model.ainvoke.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0].content == SUMMARIZE_SYSTEM_PROMPT
        assert "User: Hello" in call_args[1].content

    @pytest.mark.asyncio
    async def test_strips_whitespace(self, config):
        mock_response = MagicMock()
        mock_response.content = "  summary with spaces  \n"
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(
                [{"role": "user", "content": "hi"}], config
            )
        assert result == "summary with spaces"

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty(self, config):
        mock_response = MagicMock()
        mock_response.content = ""
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(
                [{"role": "user", "content": "hi"}], config
            )
        assert result == ""

    @pytest.mark.asyncio
    async def test_none_response_returns_empty(self, config):
        mock_response = MagicMock()
        mock_response.content = None
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(
                [{"role": "user", "content": "hi"}], config
            )
        assert result == ""

    @pytest.mark.asyncio
    async def test_llm_error_returns_empty(self, config):
        mock_model = AsyncMock()
        mock_model.ainvoke.side_effect = RuntimeError("LLM down")

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(
                [{"role": "user", "content": "hi"}], config
            )
        assert result == ""

    @pytest.mark.asyncio
    async def test_create_chat_model_called_with_config(self, config):
        mock_response = MagicMock()
        mock_response.content = "summary"
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ) as mock_factory:
            await summarize_messages(
                [{"role": "user", "content": "hi"}], config
            )
        mock_factory.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_multi_message_conversation(self, config):
        mock_response = MagicMock()
        mock_response.content = "Multi-turn summary."
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        messages = [
            {"role": "user", "content": "What is DFS?"},
            {"role": "assistant", "content": "DFS is depth-first search."},
            {"role": "user", "content": "How does it differ from BFS?"},
            {"role": "assistant", "content": "BFS explores level by level."},
        ]
        with patch(
            "app.services.memory_compression_service.create_chat_model",
            return_value=mock_model,
        ):
            result = await summarize_messages(messages, config)

        assert result == "Multi-turn summary."
        call_args = mock_model.ainvoke.call_args[0][0]
        prompt_text = call_args[1].content
        assert "User: What is DFS?" in prompt_text
        assert "Assistant: DFS is depth-first search." in prompt_text
        assert "User: How does it differ from BFS?" in prompt_text
