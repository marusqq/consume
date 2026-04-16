"""Unit tests for consume.browser — all WebDriver interactions are mocked."""

from unittest.mock import MagicMock, patch, PropertyMock

from selenium.common.exceptions import TimeoutException, WebDriverException

from consume.browser import fetch_x_text, _LOGIN_PATH


def _make_driver_mock(current_url="https://x.com/user/status/1", elements=None):
    """Return a mock Chrome driver pre-configured with sensible defaults."""
    driver = MagicMock()
    type(driver).current_url = PropertyMock(return_value=current_url)
    if elements is None:
        el = MagicMock()
        el.text = "Hello from a tweet"
        elements = [el]
    driver.find_elements.return_value = elements
    return driver


class TestFetchXText:
    _URL = "https://x.com/user/status/1"

    def test_returns_tweet_text_on_success(self):
        driver = _make_driver_mock()
        with patch("consume.browser._make_driver", return_value=driver):
            result = fetch_x_text(self._URL)
        assert result == "Hello from a tweet"

    def test_joins_multiple_elements_with_blank_line(self):
        el1, el2 = MagicMock(), MagicMock()
        el1.text, el2.text = "First part", "Second part"
        driver = _make_driver_mock(elements=[el1, el2])
        with patch("consume.browser._make_driver", return_value=driver):
            result = fetch_x_text(self._URL)
        assert result == "First part\n\nSecond part"

    def test_skips_blank_elements(self):
        el1, el2 = MagicMock(), MagicMock()
        el1.text, el2.text = "Real content", "   "
        driver = _make_driver_mock(elements=[el1, el2])
        with patch("consume.browser._make_driver", return_value=driver):
            result = fetch_x_text(self._URL)
        assert result == "Real content"

    def test_returns_empty_string_on_login_wall(self):
        driver = _make_driver_mock(current_url=f"https://x.com{_LOGIN_PATH}")
        with patch("consume.browser._make_driver", return_value=driver):
            result = fetch_x_text(self._URL)
        assert result == ""

    def test_returns_empty_string_on_timeout(self):
        driver = _make_driver_mock()
        # Make WebDriverWait(...).until(...) raise TimeoutException
        with patch("consume.browser._make_driver", return_value=driver), \
             patch("consume.browser.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException()
            result = fetch_x_text(self._URL)
        assert result == ""

    def test_returns_empty_string_on_webdriver_exception(self):
        with patch("consume.browser._make_driver", side_effect=WebDriverException("no chrome")):
            result = fetch_x_text(self._URL)
        assert result == ""

    def test_driver_is_always_quit(self):
        driver = _make_driver_mock()
        with patch("consume.browser._make_driver", return_value=driver):
            fetch_x_text(self._URL)
        driver.quit.assert_called_once()

    def test_driver_quit_even_on_webdriver_error_after_get(self):
        driver = _make_driver_mock()
        driver.get.side_effect = WebDriverException("crashed")
        with patch("consume.browser._make_driver", return_value=driver):
            result = fetch_x_text(self._URL)
        assert result == ""
        driver.quit.assert_called_once()
