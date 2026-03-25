import html
import re
from urllib.parse import urlparse

import requests
from readability import Document

TIMEOUT = 10
USER_AGENT = "consume/1.0 (content reader)"
MIN_CONTENT_LENGTH = 50


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: '{url}'. Expected a URL starting with http:// or https://")


def fetch_html(url: str) -> str:
    _validate_url(url)
    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request timed out after {TIMEOUT}s: '{url}'")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to '{url}'. Check your network connection.")
    return response.text


def _strip_tags(raw_html: str) -> str:
    """Strip all HTML tags, unescape entities, and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_text(html: str) -> str:
    """Use readability-lxml to strip boilerplate and return the main article text."""
    doc = Document(html)
    content_html = doc.summary()
    text = _strip_tags(content_html)
    if not text:
        # Fallback: strip all tags from the raw HTML directly
        text = _strip_tags(html)
    if not text:
        raise ValueError(
            "No readable content could be extracted from this page. "
            "The page may require JavaScript, be behind a login, or contain only images."
        )
    if len(text) < MIN_CONTENT_LENGTH:
        raise ValueError(
            f"Extracted content is too short ({len(text)} chars, minimum {MIN_CONTENT_LENGTH}). "
            "The page may not contain enough readable text to summarize."
        )
    return text
