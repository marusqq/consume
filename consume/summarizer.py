import os

import anthropic

SHORT_BULLETS = 5
LONG_BULLETS = 9

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are a factual summarizer. "
    "Rules you must never break:\n"
    "1. Output ONLY bullet points — no headings, no preamble, no trailing commentary.\n"
    "2. Every bullet starts with the '•' character followed by a single space.\n"
    "3. Each bullet is ≤15 words and states a verifiable fact from the source text.\n"
    "4. Do not infer, editorialize, or add information not present in the source.\n"
    "5. Output exactly the number of bullets requested — no more, no fewer."
)


def summarize(text: str, mode: str = "short") -> str:
    n = SHORT_BULLETS if mode == "short" else LONG_BULLETS
    user_prompt = f"Summarize the following article in exactly {n} bullet points:\n\n{text}"

    model = os.environ.get("CONSUME_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()
    try:
        message = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": user_prompt}],
            system=SYSTEM_PROMPT,
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
