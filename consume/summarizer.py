import anthropic

SHORT_BULLETS = 3
LONG_BULLETS = 9

SYSTEM_PROMPT = (
    "You are a concise summarizer. Output only bullet points, one per line, "
    "each starting with '•'. No preamble, no commentary, no trailing text. "
    "Each bullet must be factual, ≤15 words."
)


def summarize(text: str, mode: str = "short") -> str:
    n = SHORT_BULLETS if mode == "short" else LONG_BULLETS
    user_prompt = f"Summarize the following article in exactly {n} bullet points:\n\n{text}"

    client = anthropic.Anthropic()
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
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
