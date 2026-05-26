"""서울디자인재단 크롤러.

진단 결과:
- URL: menuno=18 (입찰정보 게시판)
- 테이블 컬럼: [0]번호 [1]제목(링크) [2]첨부파일 [3]조회수 [4]등록일
- 링크는 tbody tr > td:nth-child(2) > a 에 위치
- 서울디자인재단 자체가 디자인 전문기관 → 별도 키워드 필터 없이 전체 수집
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LIST_URL = "https://seouldesign.or.kr/?menuno=18&siteno=1&boardno=19&cates=132"
_BASE = "https://seouldesign.or.kr"
_MAX_PAGES = 5


class SeoulDesignCrawler(BaseCrawler):
    site_id = "seouldesign"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                page.goto(_LIST_URL, timeout=30000, wait_until="networkidle")
                page.wait_for_timeout(3000)

                for page_no in range(1, _MAX_PAGES + 1):
                    rows = self._parse_rows(page)
                    postings.extend(rows)
                    if not rows or not self._go_next_page(page, page_no):
                        break

        except Exception as e:
            print(f"[seouldesign] 크롤링 오류: {e}")

        return self._deduplicate(postings)

    def _parse_rows(self, page) -> List[Posting]:
        """
        테이블 컬럼: [0]번호 [1]제목(링크) [2]첨부파일 [3]조회수 [4]등록일
        메인 페이지와 iframe 모두 시도.
        서울디자인재단은 전체 공고 수집 (키워드 필터 미적용).
        """
        postings = []
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                rows = ctx.query_selector_all("table tbody tr")
                print(f"  [seouldesign] 테이블 행 수: {len(rows)} (frame url: {ctx.url[:60]})")
                if not rows:
                    continue
                for row in rows:
                    cells = row.query_selector_all("td")
                    if len(cells) < 2:
                        continue
                    title_el = cells[1].query_selector("a")
                    if not title_el:
                        # cells[0]에 링크가 있을 수도 있음
                        title_el = cells[0].query_selector("a")
                    if not title_el:
                        continue
                    title = title_el.inner_text().strip()
                    if not title or len(title) < 4 or title.isdigit():
                        continue

                    href = title_el.get_attribute("href") or ""
                    full_url = href if href.startswith("http") else f"{_BASE}{href}"
                    post_id = self._extract_post_id(href) or self._hash(title)
                    deadline = cells[4].inner_text().strip() if len(cells) > 4 else None

                    postings.append(Posting(
                        source_id=self.site_id,
                        post_id=post_id,
                        title=title,
                        url=full_url,
                        deadline=deadline,
                        relevance_score=1,
                        matched_keywords=["seouldesign"],
                    ))
                if postings:
                    break  # 첫 번째 유효한 context 사용
            except Exception as e:
                print(f"  [seouldesign] frame 파싱 오류: {e}")
                continue
        return postings

    def _go_next_page(self, page, current_page: int) -> bool:
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                nxt = ctx.query_selector(
                    f"a:has-text('{current_page + 1}'), "
                    "a.next, a[title='다음페이지'], a[title='다음']"
                )
                if nxt:
                    nxt.click()
                    page.wait_for_load_state("networkidle", timeout=8000)
                    page.wait_for_timeout(1500)
                    return True
            except Exception:
                continue
        return False

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
