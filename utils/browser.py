"""playwright 브라우저 공통 설정.
봇 차단 우회: 실제 브라우저 UA, 한국어 locale, SSL 무시(정부 사이트용).
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
    browser = pw.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent=_DEFAULT_UA,
        locale="ko-KR",
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,   # 정부 사이트 자체 CA 인증서 허용
        extra_http_headers={
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        },
    )
    # navigator.webdriver 속성 숨기기 (봇 감지 우회)
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = ctx.new_page()
    return page, browser
