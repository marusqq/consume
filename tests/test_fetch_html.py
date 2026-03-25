import pytest
import requests

from consume.extractor import fetch_html, TIMEOUT, USER_AGENT


class TestFetchHtml:
    def test_returns_html_on_success(self, requests_mock):
        requests_mock.get("https://example.com", text="<html><body>Hello</body></html>")
        result = fetch_html("https://example.com")
        assert "<html>" in result
        assert "Hello" in result

    def test_sends_user_agent_header(self, requests_mock):
        requests_mock.get("https://example.com", text="<html></html>")
        fetch_html("https://example.com")
        assert requests_mock.last_request.headers["User-Agent"] == USER_AGENT

    def test_raises_value_error_for_invalid_url(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            fetch_html("not-a-url")

    def test_raises_timeout_error_on_timeout(self, requests_mock):
        requests_mock.get("https://example.com", exc=requests.exceptions.Timeout)
        with pytest.raises(TimeoutError, match=str(TIMEOUT)):
            fetch_html("https://example.com")

    def test_raises_connection_error_on_connection_failure(self, requests_mock):
        requests_mock.get("https://example.com", exc=requests.exceptions.ConnectionError)
        with pytest.raises(ConnectionError, match="example.com"):
            fetch_html("https://example.com")

    def test_raises_for_http_error_status(self, requests_mock):
        requests_mock.get("https://example.com", status_code=404)
        with pytest.raises(requests.exceptions.HTTPError):
            fetch_html("https://example.com")

    def test_uses_10_second_timeout(self, requests_mock):
        requests_mock.get("https://example.com", text="<html></html>")
        fetch_html("https://example.com")
        assert requests_mock.last_request is not None
        assert TIMEOUT == 10
