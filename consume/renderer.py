"""Markdown and PDF rendering for consume summaries."""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def _bullets_to_list(summary: str) -> list[str]:
    """Return a list of plain bullet strings (without the leading • marker)."""
    bullets = []
    for line in summary.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading bullet markers
        if line.startswith("• "):
            bullets.append(line[2:])
        elif line[:2] in ("- ", "* "):
            bullets.append(line[2:])
        else:
            bullets.append(line)
    return bullets


def _url_to_slug(url: str) -> str:
    """Turn a URL into a safe filename stem, e.g. x.com_nick_status_123."""
    parsed = urlparse(url)
    parts = [parsed.netloc] + [p for p in parsed.path.split("/") if p]
    slug = "_".join(parts)
    slug = re.sub(r"[^\w\-]", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:80]


def default_output_path(url: str, ext: str) -> Path:
    """Return a sensible default output path for a given URL and file extension."""
    return Path(_url_to_slug(url) + "." + ext.lstrip("."))


def to_markdown(url: str, summary: str) -> str:
    """Format a summary as a Markdown document."""
    bullets = _bullets_to_list(summary)
    lines = [f"# {url}", ""]
    for b in bullets:
        lines.append(f"- {b}")
    lines.append("")
    return "\n".join(lines)


def write_markdown(path: Path, url: str, summary: str) -> None:
    path.write_text(to_markdown(url, summary), encoding="utf-8")


_UNICODE_FONT_CANDIDATES = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",   # Linux
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def _find_unicode_font() -> str | None:
    for p in _UNICODE_FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def write_pdf(path: Path, url: str, summary: str) -> None:
    """Write a PDF file containing the summary using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError as e:
        raise RuntimeError(
            "fpdf2 is required for PDF output. Install it with: pip install fpdf2"
        ) from e

    bullets = _bullets_to_list(summary)
    font_path = _find_unicode_font()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if font_path:
        pdf.add_font("Unicode", fname=font_path)
        pdf.add_font("Unicode", style="B", fname=font_path)
        body_font = "Unicode"
    else:
        # Latin-1 fallback: bullet points and non-Latin characters will be corrupted.
        print(
            "Warning: no Unicode font found; PDF output may contain garbled characters.\n"
            "  Install Arial Unicode or DejaVu Sans to fix this.",
            file=sys.stderr,
        )
        body_font = "Helvetica"

    def safe(text: str) -> str:
        if body_font == "Helvetica":
            return text.encode("latin-1", errors="replace").decode("latin-1")
        return text

    # Title
    pdf.set_font(body_font, style="B", size=12)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 8, safe(url), align="L")
    pdf.ln(3)

    # Divider
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.3)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.epw, pdf.get_y())
    pdf.ln(4)

    # Bullets
    pdf.set_text_color(50, 50, 50)
    for bullet in bullets:
        pdf.set_font(body_font, style="B", size=11)
        pdf.cell(6, 7, "\u2022", ln=False)
        pdf.set_font(body_font, size=11)
        pdf.multi_cell(0, 7, safe(bullet), align="L")
        pdf.ln(1)

    pdf.output(str(path))


DEFAULT_VOICE = "en-US-AriaNeural"


def _bullets_to_speech(summary: str) -> str:
    """Convert bullet list to natural-sounding spoken text."""
    bullets = _bullets_to_list(summary)
    if not bullets:
        return summary
    return ". ".join(bullets).rstrip(".") + "."


def write_audio(path: Path, summary: str, voice: str | None = None) -> None:
    """Write an MP3 file using Microsoft Edge's neural TTS (via edge-tts).

    Voice can be overridden with the CONSUME_VOICE env var or the voice parameter.
    Run ``edge-tts --list-voices`` to see all available voices.
    """
    import asyncio
    import os

    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError(
            "edge-tts is required for audio output. Install it with: pip install edge-tts"
        ) from e

    selected_voice = voice or os.environ.get("CONSUME_VOICE", DEFAULT_VOICE)
    text = _bullets_to_speech(summary)

    async def _save() -> None:
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(str(path))

    asyncio.run(_save())
