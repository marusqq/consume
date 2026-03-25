"""Unit tests for cli.format_bullets and cli.main."""

from unittest.mock import patch

import pytest

from consume.cli import format_bullets, main


class TestFormatBullets:
    def test_basic_bullets_preserved(self):
        summary = "• First point\n• Second point\n• Third point"
        result = format_bullets(summary)
        lines = result.splitlines()
        assert all(line.startswith("•") for line in lines)
        assert len(lines) == 3

    def test_blank_lines_removed(self):
        summary = "• First\n\n• Second\n\n• Third"
        result = format_bullets(summary)
        assert "" not in result.splitlines()

    def test_dash_bullets_normalised_to_bullet(self):
        summary = "- First\n- Second"
        result = format_bullets(summary)
        lines = result.splitlines()
        assert all(line.startswith("•") for line in lines)

    def test_asterisk_bullets_normalised_to_bullet(self):
        summary = "* First\n* Second"
        result = format_bullets(summary)
        lines = result.splitlines()
        assert all(line.startswith("•") for line in lines)

    def test_long_bullet_wraps_with_indent(self):
        long_text = "• " + ("word " * 30).strip()
        result = format_bullets(long_text)
        lines = result.splitlines()
        assert len(lines) > 1
        # First line starts with bullet; continuation lines are indented
        assert lines[0].startswith("•")
        for cont in lines[1:]:
            assert cont.startswith("  "), f"Continuation line not indented: {repr(cont)}"

    def test_empty_string_returns_empty(self):
        assert format_bullets("") == ""

    def test_only_blank_lines_returns_empty(self):
        assert format_bullets("\n\n\n") == ""

    def test_non_bullet_line_passed_through(self):
        summary = "Some intro text\n• A bullet"
        result = format_bullets(summary)
        lines = result.splitlines()
        assert lines[0] == "Some intro text"
        assert lines[1].startswith("•")

    def test_strips_leading_trailing_whitespace_per_line(self):
        summary = "  • Indented bullet  \n  • Another  "
        result = format_bullets(summary)
        for line in result.splitlines():
            assert not line.endswith(" "), f"Trailing space: {repr(line)}"


class TestMainEmptyContent:
    def test_empty_content_prints_error_to_stderr(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html></html>"),
            patch(
                "consume.cli.extract_text",
                side_effect=ValueError(
                    "No readable content could be extracted from this page. "
                    "The page may require JavaScript, be behind a login, or contain only images."
                ),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No readable content" in captured.err

    def test_too_short_content_prints_error_to_stderr(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html><body>hi</body></html>"),
            patch(
                "consume.cli.extract_text",
                side_effect=ValueError("Extracted content is too short (2 chars, minimum 50)."),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "too short" in captured.err

    def test_empty_content_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html></html>"),
            patch(
                "consume.cli.extract_text",
                side_effect=ValueError("No readable content could be extracted from this page."),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1


def _run_main(args=None):
    """Helper to invoke main() with patched sys.argv."""
    import sys

    with patch.object(sys, "argv", ["consume", "https://example.com"]):
        main()
