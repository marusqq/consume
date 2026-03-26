from pathlib import Path

import pytest

from consume.extractor import MIN_CONTENT_LENGTH, extract_content

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestExtractContent:
    def test_normal_page_returns_text(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        assert "Baking bread" in result

    def test_normal_page_strips_tags(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        assert "<" not in result
        assert ">" not in result

    def test_normal_page_unescapes_entities(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        # &deg; → °, &ndash; → –
        assert "°" in result or "–" in result

    def test_normal_page_no_leading_trailing_whitespace(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        assert result == result.strip()

    def test_normal_page_no_consecutive_whitespace(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        assert "  " not in result

    def test_minimal_page_returns_text(self):
        html = load_fixture("minimal_page.html")
        result = extract_content(html)
        assert "Hello world" in result

    def test_minimal_page_strips_tags(self):
        html = load_fixture("minimal_page.html")
        result = extract_content(html)
        assert "<" not in result
        assert ">" not in result

    def test_fallback_to_raw_text_when_readability_returns_empty(self):
        # readability returns empty summary for very sparse pages; fallback strips raw HTML
        filler = " This fallback page has enough text to meet the minimum content length." * 2
        sparse = f"<html><body><p>Just this.{filler}</p></body></html>"
        result = extract_content(sparse)
        assert "Just this." in result
        assert "<" not in result

    def test_empty_html_raises(self):
        with pytest.raises(ValueError, match="No readable content"):
            extract_content("<html><body></body></html>")

    def test_whitespace_only_body_raises(self):
        with pytest.raises(ValueError, match="No readable content"):
            extract_content("<html><body>   \n\t  </body></html>")

    def test_returns_string(self):
        html = load_fixture("normal_page.html")
        result = extract_content(html)
        assert isinstance(result, str)

    def test_too_short_content_raises(self):
        # Build a page with content just under the minimum length
        short_text = "x" * (MIN_CONTENT_LENGTH - 1)
        raw_html = f"<html><body><article>{short_text}</article></body></html>"
        with pytest.raises(ValueError, match="too short"):
            extract_content(raw_html)

    def test_content_at_minimum_length_does_not_raise(self):
        exact_text = "x" * MIN_CONTENT_LENGTH
        raw_html = f"<html><body><article>{exact_text}</article></body></html>"
        result = extract_content(raw_html)
        assert len(result) >= MIN_CONTENT_LENGTH

    def test_too_short_error_includes_char_count(self):
        short_text = "Hi"
        raw_html = f"<html><body><article>{short_text}</article></body></html>"
        with pytest.raises(ValueError, match=r"\d+ chars"):
            extract_content(raw_html)
