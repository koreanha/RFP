"""기업마당 크롤러.

URL: https://www.bizinfo.go.kr/web/index.do
지원사업 공고 목록 페이지를 playwright로 크롤링.
디자인 관련 키워드로 제목 필터링.
"""
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LIST_URL = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
_DESIGN_KEYWORDS = ["디자인", "design", "UX", "UI", "그래픽", "브랜드", "영상", "콘텐츠"]


class BizinfoCrawler(BaseCrawler):
    site_id = "bizinfo"

    def fetch(self) -> List[Posting]:
        page, browser = new_page()
        postings = []
        try:
            page.goto(_LIST_URL, timeout=30000)
            page.wait_for_selector("table", timeout=15000)

            rows = page.query_selector_all("table tbody tr")
            for row in rows:
                title_el = row.query_selector("td.tit a, td a")
                if not title_el:
                    continue

                title = title_el.inner_text().strip()
                if not self._is_design_related(title):
                    continue

                href = title_el.get_attribute("href") or ""
                full_url = href if href.startswith("http") else f"https://www.bizinfo.go.kr{href}"

                # 마감일 추출 시도
                cells = row.query_selector_all("td")
                deadline = cells[-1].inner_text().strip() if cells else None

                # post_id: URL에서 추출하거나 title 해시 사용
                post_id = self._extract_post_id(href) or self._hash(title)

                postings.append(Posting(
                    source_id=self.site_id,
                    post_id=post_id,
                    title=title,
                    url=full_url,
                    deadline=deadline,
                ))
        except Exception as e:
            print(f"[bizinfo] 크롤링 오류: {e}")
        finally:
            browser.close()

        return postings

    def _is_design_related(self, title: str) -> bool:
        lower = title.lower()
        return any(kw.lower() in lower for kw in _DESIGN_KEYWORDS)

    def _extract_post_id(self, href: str) -> str:
        # href 파라미터에서 ID 추출
        for sep in ["bbsId=", "nttId=", "seq=", "idx="]:
            if sep in href:
                return href.split(sep)[-1].split("&")[0]
        return ""

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:12]
