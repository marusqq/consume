import html
import re
from urllib.parse import urlparse

import requests
from readability import Document

TIMEOUT = 10
USER_AGENT = "consume/1.0 (content reader)"


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


def extract_text(raw_html: str) -> str:
    doc = Document(raw_html)
    content_html = doc.summary()
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", content_html)
    # Unescape HTML entities and collapse whitespace
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise ValueError("No content could be extracted from the page.")
    return text
