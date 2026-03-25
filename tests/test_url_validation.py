import pytest

from consume.extractor import _validate_url


class TestValidateUrl:
    def test_valid_http_url(self):
        _validate_url("http://example.com")

    def test_valid_https_url(self):
        _validate_url("https://example.com")

    def test_valid_https_url_with_path(self):
        _validate_url("https://example.com/some/path?q=1#anchor")

    def test_valid_https_url_with_subdomain(self):
        _validate_url("https://www.example.co.uk/page")

    def test_missing_scheme_raises(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            _validate_url("example.com")

    def test_ftp_scheme_raises(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            _validate_url("ftp://example.com")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            _validate_url("")

    def test_scheme_only_raises(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            _validate_url("https://")

    def test_no_netloc_raises(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            _validate_url("https:///path/only")

    def test_error_message_includes_url(self):
        bad_url = "not-a-url"
        with pytest.raises(ValueError, match=bad_url):
            _validate_url(bad_url)

    def test_error_message_includes_hint(self):
        with pytest.raises(ValueError, match="http"):
            _validate_url("not-a-url")
