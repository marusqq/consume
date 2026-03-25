from unittest.mock import MagicMock, patch

import anthropic
import pytest

from consume.summarizer import SHORT_BULLETS, LONG_BULLETS, DEFAULT_MODEL, summarize


def make_message(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


SAMPLE_TEXT = "This is an article about baking bread at home with simple ingredients."
BULLET_RESPONSE = "• Bread can be baked at home.\n• Simple ingredients are needed.\n• The process is straightforward."


class TestSummarize:
    @patch("consume.summarizer.anthropic.Anthropic")
    def test_short_mode_returns_text(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.return_value = make_message(BULLET_RESPONSE)
        result = summarize(SAMPLE_TEXT, mode="short")
        assert result == BULLET_RESPONSE

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_long_mode_returns_text(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.return_value = make_message(BULLET_RESPONSE)
        result = summarize(SAMPLE_TEXT, mode="long")
        assert result == BULLET_RESPONSE

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_short_mode_requests_correct_bullet_count(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        summarize(SAMPLE_TEXT, mode="short")
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert f"exactly {SHORT_BULLETS} bullet points" in messages[0]["content"]

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_long_mode_requests_correct_bullet_count(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        summarize(SAMPLE_TEXT, mode="long")
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert f"exactly {LONG_BULLETS} bullet points" in messages[0]["content"]

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_strips_leading_trailing_whitespace(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.return_value = make_message("  • A bullet.  ")
        result = summarize(SAMPLE_TEXT)
        assert result == "• A bullet."

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_passes_text_to_api(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        summarize(SAMPLE_TEXT)
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert SAMPLE_TEXT in messages[0]["content"]

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_authentication_error_raises_runtime_error(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.side_effect = anthropic.AuthenticationError(
            message="Unauthorized", response=MagicMock(status_code=401), body={}
        )
        with pytest.raises(RuntimeError, match="authentication failed"):
            summarize(SAMPLE_TEXT)

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_rate_limit_error_raises_runtime_error(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limited", response=MagicMock(status_code=429), body={}
        )
        with pytest.raises(RuntimeError, match="rate limit"):
            summarize(SAMPLE_TEXT)

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_timeout_error_raises_runtime_error(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.side_effect = anthropic.APITimeoutError(
            request=MagicMock()
        )
        with pytest.raises(RuntimeError, match="timed out"):
            summarize(SAMPLE_TEXT)

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_generic_api_error_raises_runtime_error(self, mock_anthropic):
        mock_anthropic.return_value.messages.create.side_effect = anthropic.APIError(
            message="Internal error", request=MagicMock(), body={}
        )
        with pytest.raises(RuntimeError, match="LLM API error"):
            summarize(SAMPLE_TEXT)

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_default_mode_is_short(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        summarize(SAMPLE_TEXT)
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert f"exactly {SHORT_BULLETS} bullet points" in messages[0]["content"]

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_uses_default_model_when_env_not_set(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("CONSUME_MODEL", None)
            summarize(SAMPLE_TEXT)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == DEFAULT_MODEL

    @patch("consume.summarizer.anthropic.Anthropic")
    def test_uses_model_from_env_var(self, mock_anthropic):
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = make_message(BULLET_RESPONSE)
        with patch.dict("os.environ", {"CONSUME_MODEL": "claude-opus-4-6"}):
            summarize(SAMPLE_TEXT)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-opus-4-6"
