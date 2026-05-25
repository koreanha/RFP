"""playwright 브라우저 공통 설정.
봇 차단 우회를 위해 실제 브라우저처럼 보이게 설정.
"""
from playwright.sync_api import sync_playwright, Page, Browser

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def new_page(headless: bool = True) -> tuple[Page, Browser]:
    """(page, browser) 반환 — 호출 측에서 browser.close() 책임"""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    ctx = browser.new_context(
        user_agent=_DEFAULT_UA,
        locale="ko-KR",
        viewport={"width": 1280, "height": 800},
    )
    page = ctx.new_page()
    return page, browser
