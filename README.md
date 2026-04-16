# consume

Turn any URL into a concise summary — output to terminal, markdown, PDF, or MP3.

```
consume https://example.com/some-article
• Author argues that X leads to Y under conditions Z.
• Study found a 40% improvement in outcome A.
• Three caveats apply: B, C, and D.
```

Works with regular articles, X/Twitter posts, and X Articles (long-form Notes).

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/marusqq/consume.git
cd consume
pip install -e .
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | API key for Claude. Get one at [console.anthropic.com](https://console.anthropic.com). |
| `CONSUME_MODEL` | No | Override the default Claude model (default: `claude-haiku-4-5-20251001`). |
| `CONSUME_VOICE` | No | Override the default Edge TTS voice for audio output (default: `en-US-AriaNeural`). |

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

## Usage

```
consume [--mode MODE] [--format FORMAT] [--out PATH] [--voice VOICE] <url> [url ...]
consume login
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `url` | — | One or more URLs to summarize. |
| `--mode` | `short` | Summary depth (see [Modes](#modes)). |
| `--format` | `text` | Output format (see [Formats](#formats)). |
| `--out PATH` | auto | Output file path for `markdown`, `pdf`, or `audio`. Defaults to a filename derived from the URL. |
| `--voice VOICE` | `en-US-AriaNeural` | Edge TTS voice for `--format audio`. Run `edge-tts --list-voices` to list options. |

### Commands

| Command | Description |
|---|---|
| `consume login` | Log in to X in a browser window and save session cookies. Required for X Articles. |

## Modes

| Mode | Bullets | Use when |
|---|---|---|
| `short` | 3 | Quick scan — you want the gist fast. |
| `default` | 5 | Balanced — more context, still concise. |
| `long` | 8–10 | Deeper read — more detail without reading the full article. |
| `auto` | Claude decides | Nothing important is left out. Claude picks the right depth for the content. |

## Formats

| Format | Output | Description |
|---|---|---|
| `text` | Terminal | Bullet points printed to stdout (default). |
| `markdown` | `markdown/{slug}.md` | Markdown file with bullet list. |
| `pdf` | `pdf/{slug}.pdf` | PDF document. |
| `audio` | `audio/{slug}.mp3` | MP3 narration via Microsoft Edge neural TTS (free, no API key). |

## Library

Every consumed URL is saved to a local library so it is never re-fetched or re-summarized:

```
library/
  .index.json          ← registry of all consumed URLs and their outputs
  {slug}.md            ← markdown summary, written once per URL

audio/{slug}.mp3
pdf/{slug}.pdf
markdown/{slug}.md
```

- Re-consuming the same URL **with the same format** shows the existing file path immediately.
- Re-consuming the same URL **with a different format** reads the cached summary and generates the new output — no network request needed.
- The library markdown is only written once and never overwritten.

## Examples

```bash
# Terminal summary (3 bullets, default)
consume https://example.com/article

# Let Claude decide how many bullets — captures everything
consume --mode auto https://x.com/user/status/123

# Save as PDF
consume --mode auto --format pdf https://x.com/user/status/123

# Save as MP3 with a specific voice
consume --mode auto --format audio --voice en-US-BrianNeural https://example.com/article

# Save as markdown to a custom path
consume --mode auto --format markdown --out ~/notes/summary.md https://example.com

# Summarize multiple URLs at once
consume https://url1.com https://url2.com https://url3.com

# Log in to X for article support
consume login
```

## X / Twitter Support

Regular posts and X Articles (long-form Notes) are both supported.

- **Regular posts** are fetched via the oEmbed API — no login required.
- **X Articles** require a logged-in session. Run `consume login` once to save your cookies:

```bash
consume login
# A Chrome window opens — log in to X, then press Enter in the terminal.
# Cookies are saved to ~/.consume/x_cookies.json and reused automatically.
```

Tracking parameters (e.g. `?s=20`) are stripped automatically before fetching.

## Error Handling

`consume` exits with a non-zero status and prints a clear message for:

- Invalid or non-HTTP URL
- Network timeout or connection failure
- Page with no extractable content (JavaScript-only, login wall, images only)
- LLM API authentication failure (`ANTHROPIC_API_KEY` missing or invalid)
- LLM API rate limit or timeout

## Running Tests

```bash
# Unit tests only (no network or API key required)
pytest -m "not integration"

# All tests including integration smoke test (requires network + ANTHROPIC_API_KEY)
pytest
```
