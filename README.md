# consume

Turn any article URL into a concise bullet-point summary.

```
consume https://example.com/some-article
• Author argues that X leads to Y under conditions Z.
• Study found a 40% improvement in outcome A.
• Three caveats apply: B, C, and D.
```

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/yourname/consume.git
cd consume
pip install -e .
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | API key for the Claude LLM used to summarize content. Get one at [console.anthropic.com](https://console.anthropic.com). |
| `CONSUME_MODEL` | No | Override the default Claude model (e.g. `claude-haiku-4-5-20251001`). |

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# then edit .env and replace the placeholder with your real key
```

Or export it directly in your shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```
consume <url> [--mode short|default|long]
```

**Arguments**

| Argument | Default | Description |
|---|---|---|
| `url` | — | The article URL to summarize (must start with `http://` or `https://`). |
| `--mode` | `short` | Summary length: `short` (3 bullets), `default` (5 bullets), or `long` (8–10 bullets). |

## Examples

Short summary (default):

```bash
consume https://example.com/article
```

Long summary:

```bash
consume https://example.com/article --mode long
```

## Modes

| Mode | Bullets | Use when |
|---|---|---|
| `short` | 3 | Quick scan — you want the gist fast. |
| `default` | 5 | Balanced summary — more context than short, still concise. |
| `long` | 8–10 | Deeper read — you want more detail without reading the full article. |

## Error Handling

`consume` exits with a non-zero status and prints a clear message for:

- Invalid or non-HTTP URL
- Network timeout or connection failure
- Page with no extractable content
- LLM API authentication failure (`ANTHROPIC_API_KEY` missing or invalid)
- LLM API rate limit or timeout

## Running Tests

```bash
# Unit tests only (no network or API key required)
pytest -m "not integration"

# All tests including integration smoke test (requires network + ANTHROPIC_API_KEY)
pytest
```
