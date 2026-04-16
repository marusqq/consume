"""X session cookie management for consume."""

import json
from pathlib import Path

_COOKIES_PATH = Path.home() / ".consume" / "x_cookies.json"

X_LOGIN_URL = "https://x.com/login"
X_HOME_URL = "https://x.com/home"


def cookies_path() -> Path:
    return _COOKIES_PATH


def load_cookies() -> list[dict]:
    """Return saved X cookies, or an empty list if none exist."""
    if not _COOKIES_PATH.exists():
        return []
    try:
        return json.loads(_COOKIES_PATH.read_text())
    except Exception:
        return []


def save_cookies(cookies: list[dict]) -> None:
    _COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _COOKIES_PATH.write_text(json.dumps(cookies, indent=2))


def has_cookies() -> bool:
    return bool(load_cookies())


def login_interactive() -> bool:
    """Open a visible Chrome window, wait for the user to log in to X, then save cookies.

    Uses undetected-chromedriver so X does not block the browser as a bot.
    Returns True on success, False if the user did not complete the login.
    """
    try:
        import undetected_chromedriver as uc
    except ImportError as e:
        raise RuntimeError(
            "undetected-chromedriver is required for login. "
            "Install it with: pip install undetected-chromedriver"
        ) from e

    options = uc.ChromeOptions()
    try:
        driver = uc.Chrome(options=options, headless=False)
    except Exception as e:
        raise RuntimeError(f"Could not launch Chrome: {e}") from e

    try:
        driver.get(X_LOGIN_URL)
        print("Log in to X in the browser window, then press Enter here to continue...")
        input()

        cookies = driver.get_cookies()
        auth_cookie_names = {"auth_token", "ct0"}
        logged_in = any(c.get("name") in auth_cookie_names for c in cookies)
        if not logged_in:
            return False

        save_cookies(cookies)
        return True
    finally:
        driver.quit()
