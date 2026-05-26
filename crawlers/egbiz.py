"""이지비즈 크롤러."""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LIST_URL = "https://www.egbiz.or.kr/bbs/selectBbsList.do?bbsSn=1"
_DESIGN_KEYWORDS = ["디자인", "design", "UX", "UI", "그래픽", "브랜드", "영상", "콘텐츠", "시각"]


class EgbizCrawler(BaseCrawler):
    site_id = "egbiz"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                page.goto(_LIST_URL, timeout=30000)
                page.wait_for_selector("table, .board-list, .list-wrap", timeout=15000)

                rows = (
                    page.query_selector_all("table tbody tr")
                    or page.query_selector_all(".board-list li")
                    or page.query_selector_all(".list-wrap .item")
                )
                for row in rows:
                    title_el = row.query_selector("td a, .tit a, a")
                    if not title_el:
                        continue
                    title = title_el.inner_text().strip()
                    if not title or not self._is_design_related(title):
                        continue

                    href = title_el.get_attribute("href") or ""
                    full_url = (
                        href if href.startswith("http")
                        else f"https://www.egbiz.or.kr{href}"
                    )
                    cells = row.query_selector_all("td")
                    deadline = cells[-1].inner_text().strip() if len(cells) > 1 else None

                    postings.append(Posting(
                        source_id=self.site_id,
                        post_id=self._extract_post_id(href) or self._hash(title),
                        title=title,
                        url=full_url,
                        deadline=deadline,
                    ))
        except Exception as e:
            print(f"[egbiz] 크롤링 오류: {e}")

        return postings

    def _is_design_related(self, title: str) -> bool:
        lower = title.lower()
        return any(kw.lower() in lower for kw in _DESIGN_KEYWORDS)

    def _extract_post_id(self, href: str) -> str:
        for sep in ["bbsIdx=", "seq=", "idx=", "no=", "nttId="]:
            if sep in href:
                return href.split(sep)[-1].split("&")[0]
        return ""

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]
