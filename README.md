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

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```
consume <url> [--mode short|long]
```

**Arguments**

| Argument | Default | Description |
|---|---|---|
| `url` | — | The article URL to summarize (must start with `http://` or `https://`). |
| `--mode` | `short` | Summary length: `short` (3 bullets) or `long` (9 bullets). |

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
| `long` | 9 | Deeper read — you want more detail without reading the full article. |

## Error Handling

`consume` exits with a non-zero status and prints a clear message for:

- Invalid or non-HTTP URL
- Network timeout or connection failure
- Page with no extractable content
- LLM API authentication failure (`ANTHROPIC_API_KEY` missing or invalid)
- LLM API rate limit or timeout
