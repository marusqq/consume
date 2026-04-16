import re

# Approximate characters per token for Claude models
_CHARS_PER_TOKEN = 4

# Default max tokens to send to the LLM (leaves room for prompt overhead and response)
DEFAULT_MAX_INPUT_TOKENS = 8000


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace (spaces, tabs, newlines) into a single space."""
    return re.sub(r"\s+", " ", text).strip()


def truncate_text(text: str, max_tokens: int = DEFAULT_MAX_INPUT_TOKENS) -> str:
    """Truncate text so it fits within approximately max_tokens LLM input tokens.

    Uses a character-based heuristic (~4 chars per token) to avoid a hard
    tokenizer dependency.  The result is stripped of trailing partial words.
    """
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Avoid cutting in the middle of a word
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated.strip()
