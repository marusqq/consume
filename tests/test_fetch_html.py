import json

import pytest
import requests

from consume.extractor import fetch_html, TIMEOUT, USER_AGENT, _X_OEMBED_URL


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


class TestFetchXHtml:
    _OEMBED_RESPONSE = {
        "author_name": "PolyDAO",
        "html": '<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Some tweet content here</p>&mdash; PolyDAO (@polydao) <a href="https://twitter.com/polydao/status/123">date</a></blockquote>',
    }

    def test_x_url_uses_oembed_api(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, json=self._OEMBED_RESPONSE)
        result = fetch_html("https://x.com/polydao/status/123")
        assert "PolyDAO" in result
        assert "Some tweet content here" in result

    def test_twitter_url_uses_oembed_api(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, json=self._OEMBED_RESPONSE)
        result = fetch_html("https://twitter.com/polydao/status/123")
        assert "PolyDAO" in result

    def test_oembed_url_passed_as_param(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, json=self._OEMBED_RESPONSE)
        tweet_url = "https://x.com/polydao/status/123"
        fetch_html(tweet_url)
        assert "url" in requests_mock.last_request.qs
        assert requests_mock.last_request.qs["url"][0] == tweet_url

    def test_x_url_timeout_raises_timeout_error(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, exc=requests.exceptions.Timeout)
        with pytest.raises(TimeoutError, match=str(TIMEOUT)):
            fetch_html("https://x.com/polydao/status/123")

    def test_x_url_connection_error_raises_connection_error(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, exc=requests.exceptions.ConnectionError)
        with pytest.raises(ConnectionError):
            fetch_html("https://x.com/polydao/status/123")

    def test_x_url_http_error_raises(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, status_code=404)
        with pytest.raises(requests.exceptions.HTTPError):
            fetch_html("https://x.com/polydao/status/123")

    def test_returns_html_string(self, requests_mock):
        requests_mock.get(_X_OEMBED_URL, json=self._OEMBED_RESPONSE)
        result = fetch_html("https://x.com/polydao/status/123")
        assert result.startswith("<html>")
