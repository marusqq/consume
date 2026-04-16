import json
import os
import re

import anthropic

from .utils import truncate_text

SHORT_BULLETS = 3
DEFAULT_BULLETS = 5
LONG_BULLETS_MIN = 8
LONG_BULLETS_MAX = 10

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are a factual summarizer. "
    "Rules you must never break:\n"
    "1. Output ONLY bullet points — no headings, no preamble, no trailing commentary.\n"
    "2. Every bullet starts with the '•' character followed by a single space.\n"
    "3. Each bullet is ≤20 words and states a verifiable fact from the source text.\n"
    "4. Do not infer, editorialize, or add information not present in the source.\n"
    "5. Output the exact number of bullets requested — no more, no fewer.\n"
    "6. For short social media posts with fewer distinct facts than bullets requested, "
    "   output only as many bullets as there are distinct facts (minimum 1)."
)

AUTO_SYSTEM_PROMPT = (
    "You are a factual summarizer. "
    "Rules you must never break:\n"
    "1. Output ONLY bullet points — no headings, no preamble, no trailing commentary.\n"
    "2. Every bullet starts with the '•' character followed by a single space.\n"
    "3. Each bullet is ≤25 words and states one distinct fact or insight from the source.\n"
    "4. Do not infer, editorialize, or add information not present in the source.\n"
    "5. Use as many bullets as the content requires — enough to capture every important "
    "   fact, argument, and conclusion without padding or repetition."
)


def summarize(text: str, mode: str = "default") -> str:
    text = truncate_text(text)

    if mode == "auto":
        user_prompt = (
            "Extract all key facts, ideas, and conclusions from the following content "
            "as bullet points. Capture everything important — do not omit significant details:\n\n"
            + text
        )
        system = AUTO_SYSTEM_PROMPT
        max_tokens = 2048
    elif mode == "short":
        user_prompt = f"Summarize the following article in exactly {SHORT_BULLETS} bullet points:\n\n{text}"
        system = SYSTEM_PROMPT
        max_tokens = 512
    elif mode == "long":
        user_prompt = (
            f"Summarize the following article in between {LONG_BULLETS_MIN} and {LONG_BULLETS_MAX} bullet points:\n\n{text}"
        )
        system = SYSTEM_PROMPT
        max_tokens = 512
    else:
        user_prompt = f"Summarize the following article in exactly {DEFAULT_BULLETS} bullet points:\n\n{text}"
        system = SYSTEM_PROMPT
        max_tokens = 512

    model = os.environ.get("CONSUME_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_prompt}],
            system=system,
        )
    except anthropic.AuthenticationError:
        raise RuntimeError("LLM API authentication failed: check your ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise RuntimeError("LLM API rate limit exceeded: please wait before retrying.")
    except anthropic.APITimeoutError:
        raise RuntimeError("LLM API request timed out: please try again later.")
    except anthropic.APIError as e:
        raise RuntimeError(f"LLM API error: {e}") from e
    return message.content[0].text.strip()


def categorize_entries(entries: list[dict]) -> dict[str, str]:
    """Ask Claude to assign a category directory to each library entry.

    Each entry must have 'slug' and 'first_line' keys.
    Returns {slug: category} where category is a short snake_case directory name.
    Falls back to 'misc' for any entry Claude cannot categorize.
    """
    if not entries:
        return {}

    model = os.environ.get("CONSUME_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    lines = "\n".join(f"- {e['slug']}: {e['first_line']}" for e in entries)
    prompt = (
        "You are organizing a reading library. Assign each article slug below to a "
        "short, lowercase, snake_case directory name (2-3 words max, no numbers). "
        "Group related topics together. Common categories: ai, crypto, programming, "
        "business, science, health, politics, misc.\n\n"
        "Output ONLY valid JSON: an object mapping each slug to its category string. "
        "No explanation, no markdown fences.\n\n"
        f"Articles:\n{lines}"
    )

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```[^\n]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        result = json.loads(raw)
        if isinstance(result, dict):
            # Sanitize values: keep only alphanumeric and underscores
            return {
                slug: re.sub(r"[^\w]+", "_", str(cat)).strip("_").lower() or "misc"
                for slug, cat in result.items()
            }
    except Exception:
        pass

    return {e["slug"]: "misc" for e in entries}


def generate_filename(summary: str) -> str:
    """Ask Claude to generate a short descriptive snake_case filename for a summary.

    Returns a sanitized string like 'claude_ultraplan_parallel_agents'.
    Falls back to 'untitled' on any error.
    """
    model = os.environ.get("CONSUME_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    try:
        message = client.messages.create(
            model=model,
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": (
                    "Generate a filename (3–5 words, snake_case, no extension) that describes "
                    "the topic of this summary. Output ONLY the filename, nothing else.\n\n"
                    + summary[:600]
                ),
            }],
        )
        raw = message.content[0].text.strip().lower()
        # Keep only alphanumeric and underscores, collapse runs
        sanitized = re.sub(r"[^\w]+", "_", raw).strip("_")
        return sanitized[:80] if sanitized else "untitled"
    except Exception:
        return "untitled"
