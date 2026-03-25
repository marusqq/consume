from pathlib import Path

import pytest

from consume.extractor import extract_text

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestExtractText:
    def test_normal_page_returns_text(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        assert "Baking bread" in result

    def test_normal_page_strips_tags(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        assert "<" not in result
        assert ">" not in result

    def test_normal_page_unescapes_entities(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        # &deg; → °, &ndash; → –
        assert "°" in result or "–" in result

    def test_normal_page_no_leading_trailing_whitespace(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        assert result == result.strip()

    def test_normal_page_no_consecutive_whitespace(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        assert "  " not in result

    def test_minimal_page_returns_text(self):
        html = load_fixture("minimal_page.html")
        result = extract_text(html)
        assert "Hello world" in result

    def test_minimal_page_strips_tags(self):
        html = load_fixture("minimal_page.html")
        result = extract_text(html)
        assert "<" not in result
        assert ">" not in result

    def test_fallback_to_raw_text_when_readability_returns_empty(self):
        # readability returns empty summary for very sparse pages; fallback strips raw HTML
        sparse = "<html><body><p>Just this.</p></body></html>"
        result = extract_text(sparse)
        assert "Just this." in result
        assert "<" not in result

    def test_empty_html_raises(self):
        with pytest.raises(ValueError, match="No content"):
            extract_text("<html><body></body></html>")

    def test_whitespace_only_body_raises(self):
        with pytest.raises(ValueError, match="No content"):
            extract_text("<html><body>   \n\t  </body></html>")

    def test_returns_string(self):
        html = load_fixture("normal_page.html")
        result = extract_text(html)
        assert isinstance(result, str)
