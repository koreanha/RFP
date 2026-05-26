from contextlib import contextmanager
from playwright.sync_api import sync_playwright

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@contextmanager
def new_page(headless: bool = True):
    """playwright 브라우저를 열고 page를 yield한 뒤 완전히 종료.

    사용법:
        with new_page() as page:
            page.goto(...)

    sync_playwright 인스턴스까지 with 블록 종료 시 자동 정리되므로
    asyncio 루프 충돌이 발생하지 않는다.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=_DEFAULT_UA,
            locale="ko-KR",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8"},
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = ctx.new_page()
        try:
            yield page
        finally:
            browser.close()
