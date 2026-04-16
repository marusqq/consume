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


def categorize_entries(entries: list[dict]) -> dict[str, dict[str, str]]:
    """Ask Claude to assign a two-level category to each library entry.

    Each entry must have 'slug' and 'first_line' keys.
    Returns {slug: {"category": "ai", "subcategory": "agents"}}.
    Falls back to {"category": "misc", "subcategory": "general"} on any error.
    """
    if not entries:
        return {}

    model = os.environ.get("CONSUME_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()

    lines = "\n".join(f"- {e['slug']}: {e['first_line']}" for e in entries)
    prompt = (
        "You are organizing a reading library into a two-level folder hierarchy.\n"
        "For each article slug assign:\n"
        "  - category: broad topic (e.g. ai, crypto, programming, business, science, politics, misc)\n"
        "  - subcategory: specific sub-topic within that category (e.g. agents, tools, trading, "
        "web_dev, economics, regulation)\n\n"
        "Rules:\n"
        "1. Both values must be lowercase snake_case, 1-3 words, no numbers.\n"
        "2. subcategory must make sense inside its category.\n"
        "3. Output ONLY valid JSON — an object where each key is a slug and each value is "
        "{\"category\": \"...\", \"subcategory\": \"...\"}. No explanation, no markdown fences.\n\n"
        f"Articles:\n{lines}"
    )

    def _sanitize(s: str) -> str:
        return re.sub(r"[^\w]+", "_", str(s)).strip("_").lower() or "misc"

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```[^\n]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw.rstrip())
        result = json.loads(raw)

        out: dict[str, dict[str, str]] = {}

        if isinstance(result, list):
            # Array format: [{"slug": "...", "category": "...", "subcategory": "..."}]
            for item in result:
                if isinstance(item, dict) and "slug" in item:
                    slug = str(item["slug"])
                    out[slug] = {
                        "category": _sanitize(item.get("category", "misc")),
                        "subcategory": _sanitize(item.get("subcategory", "general")),
                    }
        elif isinstance(result, dict):
            # Object format: {"slug": {"category": "...", "subcategory": "..."}}
            for slug, val in result.items():
                if isinstance(val, dict):
                    out[slug] = {
                        "category": _sanitize(val.get("category", "misc")),
                        "subcategory": _sanitize(val.get("subcategory", "general")),
                    }
                else:
                    out[slug] = {"category": _sanitize(val), "subcategory": "general"}

        if out:
            return out
    except Exception:
        pass

    return {e["slug"]: {"category": "misc", "subcategory": "general"} for e in entries}


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
