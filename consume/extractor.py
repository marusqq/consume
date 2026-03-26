import html
import re
from urllib.parse import urlparse

import requests
from readability import Document

from .utils import normalize_whitespace

TIMEOUT = 10
USER_AGENT = "consume/1.0 (content reader)"
MIN_CONTENT_LENGTH = 50

_X_DOMAINS = {"x.com", "twitter.com", "www.x.com", "www.twitter.com"}
_X_OEMBED_URL = "https://publish.twitter.com/oembed"


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: '{url}'. Expected a URL starting with http:// or https://")


def _is_x_url(url: str) -> bool:
    return urlparse(url).netloc in _X_DOMAINS


def _fetch_x_html(url: str) -> str:
    try:
        response = requests.get(
            _X_OEMBED_URL,
            params={"url": url},
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request timed out after {TIMEOUT}s: '{url}'")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to '{url}'. Check your network connection.")
    data = response.json()
    author = data.get("author_name", "")
    tweet_html = data.get("html", "")
    return f"<html><body><h1>{author}</h1>{tweet_html}</body></html>"


def fetch_html(url: str) -> str:
    _validate_url(url)
    if _is_x_url(url):
        return _fetch_x_html(url)
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
    return normalize_whitespace(text)


def extract_content(html: str) -> str:
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
