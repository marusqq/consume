from unittest.mock import MagicMock, patch

import anthropic
import pytest

from consume.summarizer import (
    DEFAULT_BULLETS,
    DEFAULT_MODEL,
    LONG_BULLETS_MAX,
    LONG_BULLETS_MIN,
    SHORT_BULLETS,
    summarize,
)


def _make_client(response_text: str) -> MagicMock:
    message = MagicMock()
    message.content = [MagicMock(text=response_text)]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


class TestSummarizeDefaultMode:
    def test_default_mode_calls_api(self):
        client = _make_client("• fact one\n• fact two\n• fact three\n• fact four\n• fact five")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            result = summarize("some article text")
        client.messages.create.assert_called_once()
        assert result != ""

    def test_default_mode_prompt_contains_bullet_count(self):
        client = _make_client("• a\n• b\n• c\n• d\n• e")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("article")
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        assert str(DEFAULT_BULLETS) in user_content

    def test_default_mode_uses_default_model(self):
        client = _make_client("• bullet")
        import os
        os.environ.pop("CONSUME_MODEL", None)
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("text")
        call_kwargs = client.messages.create.call_args
        assert call_kwargs[1]["model"] == DEFAULT_MODEL


class TestSummarizeShortMode:
    def test_short_mode_prompt_contains_short_bullet_count(self):
        client = _make_client("• a\n• b\n• c")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("article", mode="short")
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        assert str(SHORT_BULLETS) in user_content

    def test_short_mode_returns_stripped_text(self):
        client = _make_client("  • bullet one  \n")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            result = summarize("article", mode="short")
        assert result == "• bullet one"


class TestSummarizeLongMode:
    def test_long_mode_prompt_contains_min_bullet_count(self):
        client = _make_client("• a\n• b\n• c\n• d\n• e\n• f\n• g\n• h")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("article", mode="long")
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        assert str(LONG_BULLETS_MIN) in user_content

    def test_long_mode_prompt_contains_max_bullet_count(self):
        client = _make_client("• a\n• b\n• c\n• d\n• e\n• f\n• g\n• h\n• i\n• j")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("article", mode="long")
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        assert str(LONG_BULLETS_MAX) in user_content


class TestSummarizeUnknownMode:
    def test_unknown_mode_falls_back_to_default_bullet_count(self):
        client = _make_client("• a\n• b\n• c\n• d\n• e")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize("article", mode="fancy")
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        assert str(DEFAULT_BULLETS) in user_content


class TestSummarizeErrorPaths:
    def test_authentication_error_raises_runtime_error(self):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.AuthenticationError(
            message="bad key", response=MagicMock(status_code=401), body={}
        )
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            with pytest.raises(RuntimeError, match="authentication"):
                summarize("text")

    def test_rate_limit_error_raises_runtime_error(self):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.RateLimitError(
            message="rate limit", response=MagicMock(status_code=429), body={}
        )
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            with pytest.raises(RuntimeError, match="rate limit"):
                summarize("text")

    def test_timeout_error_raises_runtime_error(self):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            with pytest.raises(RuntimeError, match="timed out"):
                summarize("text")

    def test_generic_api_error_raises_runtime_error(self):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.APIStatusError(
            message="server error", response=MagicMock(status_code=500), body={}
        )
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            with pytest.raises(RuntimeError, match="LLM API error"):
                summarize("text")


class TestSummarizeEnvModel:
    def test_custom_model_from_env(self):
        client = _make_client("• bullet")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client), patch.dict(
            "os.environ", {"CONSUME_MODEL": "claude-opus-4-6"}
        ):
            summarize("text")
        call_kwargs = client.messages.create.call_args
        assert call_kwargs[1]["model"] == "claude-opus-4-6"


class TestSummarizeTruncation:
    def test_very_long_text_is_truncated_before_api_call(self):
        long_text = "word " * 100_000
        client = _make_client("• bullet")
        with patch("consume.summarizer.anthropic.Anthropic", return_value=client):
            summarize(long_text)
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs[1]["messages"][0]["content"]
        # The full long_text would be ~500,000 chars; prompt must be much shorter
        assert len(user_content) < 200_000
