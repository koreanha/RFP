"""서울디자인재단 크롤러.

진단 결과: menuno=150은 메인 홈페이지.
공고 목록 실제 URL: menuno=18 (입찰공고 게시판, boardno=19)
공고 링크 패턴: ?menuno=18&...&bbsno=XXXX&act=view
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LIST_URL = "https://seouldesign.or.kr/?menuno=18&siteno=1&boardno=19&cates=132"
_BASE = "https://seouldesign.or.kr"


class SeoulDesignCrawler(BaseCrawler):
    site_id = "seouldesign"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                page.goto(_LIST_URL, timeout=30000, wait_until="networkidle")
                page.wait_for_timeout(3000)

                # 메인 페이지 + 모든 iframe 에서 공고 링크 수집
                contexts = [page] + [f for f in page.frames if f != page.main_frame]
                for ctx in contexts:
                    try:
                        postings.extend(self._extract_links(ctx))
                    except Exception:
                        pass

        except Exception as e:
            print(f"[seouldesign] 크롤링 오류: {e}")

        return self._deduplicate(postings)

    def _extract_links(self, ctx) -> List[Posting]:
        """공고 상세 링크(bbsno= 포함)를 찾아 Posting 생성."""
        postings = []
        try:
            links = ctx.query_selector_all("a[href*='bbsno=']")
            for link in links:
                href = link.get_attribute("href") or ""
                if "act=view" not in href:
                    continue
                title = link.inner_text().strip()
                # 날짜/숫자만 있는 링크 제거
                if not title or len(title) < 6 or title.isdigit():
                    continue

                full_url = href if href.startswith("http") else f"{_BASE}{href}"
                post_id = self._extract_post_id(href) or self._hash(title)

                # 날짜 요소 탐색 (형제 요소에서)
                try:
                    parent = link.evaluate("el => el.closest('li, tr, .item, .board-item')")
                    date_el = ctx.query_selector(
                        f"[data-bbsno='{post_id}'] .date, .period"
                    ) if parent else None
                    deadline = date_el.inner_text().strip() if date_el else None
                except Exception:
                    deadline = None

                postings.append(Posting(
                    source_id=self.site_id,
                    post_id=post_id,
                    title=title,
                    url=full_url,
                    deadline=deadline,
                ))
        except Exception:
            pass
        return postings

    def _extract_post_id(self, href: str) -> str:
        for sep in ["bbsno=", "bbsIdx=", "seq=", "idx=", "no="]:
            if sep in href:
                return href.split(sep)[-1].split("&")[0]
        return ""

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def _deduplicate(self, postings: List[Posting]) -> List[Posting]:
        seen, unique = set(), []
        for p in postings:
            if p.uid not in seen:
                seen.add(p.uid)
                unique.append(p)
        return unique
