"""Unit tests for cli.format_bullets, cli.parse_args, and cli.main."""

from unittest.mock import patch

import pytest

from consume.cli import format_bullets, main, parse_args


@pytest.fixture(autouse=True)
def _tmp_project_dir(tmp_path, monkeypatch):
    """Redirect all library writes to a temp directory so tests don't pollute CWD."""
    monkeypatch.chdir(tmp_path)


class TestParseArgs:
    def test_url_is_required(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_single_url_stored(self):
        args = parse_args(["https://example.com"])
        assert args.urls == ["https://example.com"]

    def test_multiple_urls_stored(self):
        args = parse_args(["https://example.com", "https://example.org"])
        assert args.urls == ["https://example.com", "https://example.org"]

    def test_default_mode_is_short(self):
        args = parse_args(["https://example.com"])
        assert args.mode == "short"

    def test_mode_long(self):
        args = parse_args(["https://example.com", "--mode", "long"])
        assert args.mode == "long"

    def test_mode_short_explicit(self):
        args = parse_args(["https://example.com", "--mode", "short"])
        assert args.mode == "short"

    def test_mode_default_explicit(self):
        args = parse_args(["https://example.com", "--mode", "default"])
        assert args.mode == "default"

    def test_invalid_mode_exits(self):
        with pytest.raises(SystemExit):
            parse_args(["https://example.com", "--mode", "invalid"])


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
                "consume.cli.extract_content",
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
                "consume.cli.extract_content",
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
                "consume.cli.extract_content",
                side_effect=ValueError("No readable content could be extracted from this page."),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1


class TestMainFetchErrors:
    def test_invalid_url_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", side_effect=ValueError("Invalid URL: 'bad'")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid URL" in captured.err

    def test_timeout_error_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", side_effect=TimeoutError("Request timed out after 10s")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "timed out" in captured.err

    def test_connection_error_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", side_effect=ConnectionError("Could not connect")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "connect" in captured.err

    def test_unexpected_fetch_error_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", side_effect=RuntimeError("unexpected")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestMainSummarizeErrors:
    def test_runtime_error_from_summarize_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html><body>content</body></html>"),
            patch("consume.cli.extract_content", return_value="Some readable content here."),
            patch("consume.cli.summarize", side_effect=RuntimeError("API key missing")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "API key missing" in captured.err

    def test_unexpected_summarize_error_exits_with_code_1(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html><body>content</body></html>"),
            patch("consume.cli.extract_content", return_value="Some readable content here."),
            patch("consume.cli.summarize", side_effect=Exception("network failure")),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestMainMultipleUrls:
    def test_multiple_urls_prints_header_for_each(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html><body>content</body></html>"),
            patch("consume.cli.extract_content", return_value="Some readable content here."),
            patch("consume.cli.summarize", return_value="• A bullet point"),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main(["https://example.com", "https://example.org"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "=== https://example.com ===" in captured.out
        assert "=== https://example.org ===" in captured.out

    def test_multiple_urls_partial_failure_exits_with_code_1(self, capsys):
        def fake_fetch(url):
            if "bad" in url:
                raise ValueError("Invalid URL: 'bad'")
            return "<html><body>content</body></html>"

        with (
            patch("consume.cli.fetch_html", side_effect=fake_fetch),
            patch("consume.cli.extract_content", return_value="Some readable content here."),
            patch("consume.cli.summarize", return_value="• A bullet point"),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main(["https://example.com", "bad://url"])

        assert exc_info.value.code == 1

    def test_single_url_no_header_printed(self, capsys):
        with (
            patch("consume.cli.fetch_html", return_value="<html><body>content</body></html>"),
            patch("consume.cli.extract_content", return_value="Some readable content here."),
            patch("consume.cli.summarize", return_value="• A bullet point"),
            pytest.raises(SystemExit) as exc_info,
        ):
            _run_main(["https://example.com"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "===" not in captured.out


def _run_main(args=None):
    """Helper to invoke main() with patched sys.argv."""
    import sys

    argv = ["consume"] + (args if args is not None else ["https://example.com"])
    with patch.object(sys, "argv", argv):
        main()
