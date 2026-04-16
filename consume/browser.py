"""Headless-browser fetcher used for JavaScript-rendered pages (e.g. X articles)."""

import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# How long to wait for content to appear in the DOM
BROWSER_TIMEOUT = 15

# Selectors tried in order for regular tweets
_TWEET_TEXT_SELECTOR = '[data-testid="tweetText"]'

# Selectors tried in order; first match with text wins
_SELECTORS = [
    '[data-testid="tweetText"]',               # regular tweets / thread posts
    '[data-testid="twitterArticleRichTextView"]',  # X Articles (rich text body)
    '[data-testid="twitterArticleReadView"]',   # X Articles (read view container)
    '[data-testid="longformRichTextComponent"]',# X Articles (paragraph blocks)
]

# Login gate path
_LOGIN_PATH = "/i/flow/login"


def _make_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)


def _load_cookies(driver: webdriver.Chrome) -> None:
    """Inject saved X session cookies into the driver."""
    from .auth import load_cookies
    cookies = load_cookies()
    if not cookies:
        return
    driver.get("https://x.com")
    for cookie in cookies:
        allowed = {"name", "value", "domain", "path", "expiry", "secure", "httpOnly"}
        clean = {k: v for k, v in cookie.items() if k in allowed}
        try:
            driver.add_cookie(clean)
        except Exception:
            pass


def _dismiss_consent(driver: webdriver.Chrome) -> None:
    """Click the 'Accept all cookies' consent banner if present."""
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in btns:
            try:
                text = btn.text.lower()
            except StaleElementReferenceException:
                continue
            if "accept" in text and "cookie" in text:
                btn.click()
                time.sleep(2)  # let the page re-render after consent
                return
    except Exception:
        pass


def _collect_text(driver: webdriver.Chrome, selector: str) -> str:
    """Return joined text of all elements matching selector, ignoring stale ones."""
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    texts = []
    for el in elements:
        try:
            t = el.text.strip()
            if t:
                texts.append(t)
        except StaleElementReferenceException:
            continue
    return "\n\n".join(texts)


def fetch_x_text(url: str) -> str:
    """Render an X URL with a headless browser and return the post/article text.

    Loads saved X session cookies so that login-gated content (X Articles) is
    accessible. Returns an empty string on any failure.
    """
    driver = None
    try:
        driver = _make_driver()
        _load_cookies(driver)
        driver.get(url)

        if _LOGIN_PATH in driver.current_url:
            return ""

        _dismiss_consent(driver)

        wait = WebDriverWait(driver, BROWSER_TIMEOUT)

        for selector in _SELECTORS:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                text = _collect_text(driver, selector)
                if text:
                    return text
            except TimeoutException:
                continue

        return ""

    except WebDriverException:
        return ""
    finally:
        if driver is not None:
            driver.quit()
