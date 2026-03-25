"""Unit tests for cli.format_bullets."""

import pytest

from consume.cli import format_bullets


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
