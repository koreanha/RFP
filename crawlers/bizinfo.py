"""기업마당 크롤러.

검색창에 키워드를 직접 입력하는 방식 사용.
URL 파라미터 검색은 기업마당에서 무시됨.
테이블 컬럼 구조: 번호 | 지원분야 | 지원사업명(링크) | 신청기간 | 소관부처 | 수행기관 | 등록일 | 조회수
"""
import hashlib
from typing import List, Optional
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page
from filter import is_relevant

_SEARCH_BASE = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
_MAX_PAGES = 5
_SEARCH_TERMS = [
    "제품디자인", "산업디자인", "디자인컨설팅",
    "디자인R&D", "디자인바우처", "디자인 고도화",
]


class BizinfoCrawler(BaseCrawler):
    site_id = "bizinfo"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                for keyword in _SEARCH_TERMS:
                    try:
                        results = self._fetch_keyword(page, keyword)
                        postings.extend(results)
                        print(f"  [bizinfo] '{keyword}' → {len(results)}건 관련")
                    except Exception as e:
                        print(f"  [bizinfo] '{keyword}' 오류: {e}")
        except Exception as e:
            print(f"[bizinfo] 크롤링 오류: {e}")
        return self._deduplicate(postings)

    def _fetch_keyword(self, page, keyword: str) -> List[Posting]:
        # 검색 목록 페이지로 이동
        page.goto(_SEARCH_BASE, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        # 검색창에 키워드 직접 입력 후 Enter
        inp = page.query_selector("input[placeholder='검색어를 입력해 주세요.']")
        if not inp:
            print(f"  [bizinfo] 검색창을 찾지 못함")
            return []
        inp.triple_click()
        inp.fill(keyword)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle", timeout=12000)
        page.wait_for_timeout(1000)

        postings = []
        for page_no in range(1, _MAX_PAGES + 1):
            rows = self._parse_rows(page)
            postings.extend(rows)
            if not rows or not self._go_next_page(page, page_no):
                break
        return postings

    def _parse_rows(self, page) -> List[Posting]:
        """
        테이블 컬럼 순서:
          [0] 번호  [1] 지원분야  [2] 지원사업명(링크)
          [3] 신청기간  [4] 소관부처·지자체  [5] 사업수행기관
        """
        postings = []
        rows = page.query_selector_all("table tbody tr")
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) < 3:
                continue
            # 3번째 셀(index 2): 지원사업명
            title_el = cells[2].query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title or "등록된" in title:
                continue

            title_result = is_relevant(title)
            if title_result.stage == "excluded" or not title_result.matched:
                continue

            href = title_el.get_attribute("href") or ""
            full_url = (
                href if href.startswith("http")
                else f"https://www.bizinfo.go.kr{href}"
            )
            deadline = cells[3].inner_text().strip() if len(cells) > 3 else None
            org = cells[4].inner_text().strip() if len(cells) > 4 else None

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
                organization=org,
                relevance_score=title_result.score,
                matched_keywords=title_result.matched_keywords,
            ))
        return postings

    def enrich_with_content(self, postings: List[Posting]) -> List[Posting]:
        enriched = []
        try:
            with new_page() as page:
                for p in postings:
                    content = self._fetch_detail(page, p)
                    if not content:
                        enriched.append(p)
                        continue
                    result = is_relevant(p.title, content)
                    if result.matched:
                        p.description = content[:500]
                        p.relevance_score = result.score
                        p.matched_keywords = result.matched_keywords
                        enriched.append(p)
        except Exception as e:
            print(f"[bizinfo] enrich 오류: {e}")
        return enriched

    def _fetch_detail(self, page, posting: Posting) -> Optional[str]:
        try:
            page.goto(posting.url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            content_el = (
                page.query_selector(".view-content, .bbs-view, #viewContent, .cont-area")
                or page.query_selector("table.tblView, .detail-wrap")
            )
            return content_el.inner_text() if content_el else page.inner_text("body")
        except Exception:
            return None

    def _go_next_page(self, page, current_page: int) -> bool:
        nxt = page.query_selector(
            f"a:has-text('{current_page + 1}'), "
            f"a.next, a[title='다음페이지'], a[title='다음']"
        )
        if nxt:
            nxt.click()
            page.wait_for_load_state("networkidle", timeout=8000)
            page.wait_for_timeout(1000)
            return True
        return False

    def _extract_post_id(self, href: str) -> str:
        for sep in ["pblancId=", "bbsIdx=", "hashCode=", "seq=", "idx=", "nttId="]:
            if sep in href:
                val = href.split(sep)[-1].split("&")[0]
                if val:
                    return val
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
