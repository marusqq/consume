import html
import re
from urllib.parse import urlparse, urlunparse

import requests
from readability import Document

from .browser import fetch_x_text
from .utils import normalize_whitespace

TIMEOUT = 10
USER_AGENT = "consume/1.0 (content reader)"
MIN_CONTENT_LENGTH = 20

_X_DOMAINS = {"x.com", "twitter.com", "www.x.com", "www.twitter.com"}
_X_OEMBED_URL = "https://publish.twitter.com/oembed"
# Bot UAs that X may serve pre-rendered HTML to (used as fallback for articles)
_X_BOT_USER_AGENTS = ["Twitterbot/1.0", "facebookexternalhit/1.1"]
# t.co is X's URL shortener; a tweet that contains only a t.co link is likely an article
_TCO_ONLY_RE = re.compile(r"^https://t\.co/\S+$")


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: '{url}'. Expected a URL starting with http:// or https://")


def _is_x_url(url: str) -> bool:
    return urlparse(url).netloc in _X_DOMAINS


def _strip_x_tracking_params(url: str) -> str:
    """Drop query-string tracking params (e.g. ?s=20) from X status URLs."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _extract_tweet_text(tweet_html: str) -> str:
    """Extract readable text from an oEmbed tweet blockquote."""
    # Drop <script> elements entirely
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", tweet_html, flags=re.DOTALL | re.IGNORECASE)
    # Pull just the <p> content (the tweet body, before the attribution line)
    p_match = re.search(r"<p\b[^>]*>(.*?)</p>", text, re.DOTALL | re.IGNORECASE)
    if p_match:
        inner = p_match.group(1)
        inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
        inner = re.sub(r"<[^>]+>", "", inner)
        return normalize_whitespace(html.unescape(inner))
    # Fallback: strip all tags
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(html.unescape(text))


def _try_fetch_x_article_text(url: str) -> str:
    """Try to get richer content from the X page via bot user-agents.

    X serves pre-rendered HTML including og:description to some crawlers.
    For articles/Notes this is often substantially longer than oEmbed returns.
    Returns empty string if nothing useful is found.
    """
    for ua in _X_BOT_USER_AGENTS:
        try:
            resp = requests.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": ua},
                allow_redirects=True,
            )
            resp.raise_for_status()
            page_html = resp.text
            # og:description is the most reliable source for tweet/article text
            for pattern in (
                r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
                r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:description["\']',
                r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            ):
                m = re.search(pattern, page_html, re.IGNORECASE)
                if m:
                    candidate = html.unescape(m.group(1))
                    if len(candidate) > 50:
                        return candidate
        except Exception:
            continue
    return ""


def _resolve_tco(tco_url: str) -> str:
    """Follow a t.co redirect and return the final URL, or the original on failure."""
    try:
        r = requests.head(tco_url, timeout=TIMEOUT, allow_redirects=True,
                          headers={"User-Agent": USER_AGENT})
        return r.url
    except Exception:
        return tco_url


def _fetch_x_html(url: str) -> str:
    """Fetch tweet or X article content and return clean HTML ready for extraction.

    Strategy:
    1. Headless browser on the status URL (works when logged in via ``consume login``)
    2. oEmbed API to get tweet text; if the text is just a bare t.co link, follow it
       and run the browser on the resolved article URL instead
    3. Bot-UA og:description fetch as a last resort
    """
    clean_url = _strip_x_tracking_params(url)

    # --- Primary: headless browser on the status URL ---
    browser_text = fetch_x_text(clean_url)

    # Only return early if the browser got a meaningfully long result; otherwise
    # keep trying fallbacks and pick the longest candidate at the end.
    if browser_text and len(browser_text) >= 100:
        title = html.escape("X Post")
        body = html.escape(browser_text)
        return f"<html><body><article><h1>{title}</h1><p>{body}</p></article></body></html>"

    # --- oEmbed to get author + tweet text ---
    author = ""
    oembed_text = ""
    try:
        response = requests.get(
            _X_OEMBED_URL,
            params={"url": clean_url},
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        data = response.json()
        author = data.get("author_name", "")
        oembed_text = _extract_tweet_text(data.get("html", ""))
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request timed out after {TIMEOUT}s: '{url}'")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to '{url}'. Check your network connection.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Could not fetch X content (HTTP {e.response.status_code}): '{url}'")
    except requests.exceptions.RequestException:
        pass  # other network hiccups: fall through to bot-UA fallback

    # If the tweet body is just a t.co link, it's likely an X Article — follow it
    # and try the browser on the resolved URL (e.g. x.com/i/article/...)
    if _TCO_ONLY_RE.match(oembed_text):
        article_url = _resolve_tco(oembed_text)
        article_browser_text = fetch_x_text(article_url)
        if article_browser_text:
            title = html.escape(f"Article by {author}" if author else "X Article")
            body = html.escape(article_browser_text)
            return f"<html><body><article><h1>{title}</h1><p>{body}</p></article></body></html>"

    # Last-resort: try bot-UA og:description fetch
    article_text = _try_fetch_x_article_text(clean_url)

    # Pick the longest candidate across all strategies
    candidates = [c for c in [browser_text, oembed_text, article_text] if c]
    content = max(candidates, key=len) if candidates else ""

    title = html.escape(f"Post by {author}" if author else "X Post")
    body = html.escape(content)
    return f"<html><body><article><h1>{title}</h1><p>{body}</p></article></body></html>"


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
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"HTTP {e.response.status_code} fetching '{url}'") from e
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Request failed for '{url}': {e}") from e
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
