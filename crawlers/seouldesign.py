"""서울디자인재단 크롤러.

URL: https://seouldesign.or.kr/?menuno=150
공지/공고 목록 페이지.
"""
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LIST_URL = "https://seouldesign.or.kr/?menuno=150"


class SeoulDesignCrawler(BaseCrawler):
    site_id = "seouldesign"

    def fetch(self) -> List[Posting]:
        page, browser = new_page()
        postings = []
        try:
            page.goto(_LIST_URL, timeout=30000)
            page.wait_for_selector(".board-list, table, .list-wrap", timeout=15000)

            # 서울디자인재단 특성상 다양한 셀렉터 시도
            rows = (
                page.query_selector_all(".board-list li")
                or page.query_selector_all("table tbody tr")
                or page.query_selector_all(".list-wrap .item")
            )

            for row in rows:
                title_el = row.query_selector("a")
                if not title_el:
                    continue
                title = title_el.inner_text().strip()
                if not title:
                    continue

                href = title_el.get_attribute("href") or ""
                full_url = href if href.startswith("http") else f"https://seouldesign.or.kr{href}"
                post_id = self._extract_post_id(href) or self._hash(title)

                # 날짜 추출 시도
                date_el = row.query_selector(".date, .period, td:last-child")
                deadline = date_el.inner_text().strip() if date_el else None

                postings.append(Posting(
                    source_id=self.site_id,
                    post_id=post_id,
                    title=title,
                    url=full_url,
                    deadline=deadline,
                ))
        except Exception as e:
            print(f"[seouldesign] 크롤링 오류: {e}")
        finally:
            browser.close()

        return postings

    def _extract_post_id(self, href: str) -> str:
        for sep in ["bbsIdx=", "seq=", "idx=", "no=", "idx="]:
            if sep in href:
                return href.split(sep)[-1].split("&")[0]
        return ""

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:12]
