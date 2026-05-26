"""나라장터 크롤러.

진단 결과:
- iframe 6개이지만 frames[2-5]는 about:blank
- frames[1]은 WebSquare 유틸리티 (검색 form 없음)
- 메인 페이지에 검색 input 존재 (name='', placeholder='검색어를 입력해 주세요.')
- 모든 링크가 javascript:void(null) → WebSquare JS 프레임워크
- 전략: 입찰공고목록 직접 URL로 이동 후 검색 input 사용
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page
from filter import is_relevant

_HOME = "https://www.g2b.go.kr/"
_BID_LIST_URL = "https://www.g2b.go.kr:8101/ep/tbid/tbidFwd.do?taskClCd=5"
_SEARCH_KEYWORDS = ["디자인", "그래픽", "UX", "브랜드", "영상제작"]
_MAX_PAGES = 3


class G2BCrawler(BaseCrawler):
    site_id = "g2b"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                for kw in _SEARCH_KEYWORDS:
                    try:
                        results = self._search_keyword(page, kw)
                        postings.extend(results)
                        print(f"  [g2b] '{kw}' → {len(results)}건")
                    except Exception as e:
                        print(f"  [g2b] '{kw}' 오류: {e}")

        except Exception as e:
            print(f"[g2b] 크롤링 오류: {e}")

        return self._deduplicate(postings)

    def _search_keyword(self, page, keyword: str) -> List[Posting]:
        # 입찰공고 목록 직접 접근 시도
        page.goto(_BID_LIST_URL, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 검색 input 탐색 (메인 + iframe 모두)
        ctx, inp = self._find_search_input(page)
        if ctx is None or inp is None:
            # 홈에서 입찰공고목록 메뉴 클릭 시도
            ctx, inp = self._try_from_home(page)
            if ctx is None or inp is None:
                frames_info = [(i, f.url[:60]) for i, f in enumerate(page.frames)]
                print(f"  [g2b] 검색창 없음. frames: {frames_info}")
                return []

        ph = inp.get_attribute("placeholder") or inp.get_attribute("name") or "?"
        print(f"  [g2b] 검색창 발견: '{ph}' (frame: {ctx.url[:60] if hasattr(ctx, 'url') else 'main'})")

        inp.triple_click()
        inp.fill(keyword)

        btn = ctx.query_selector(
            "button[type='submit'], input[type='submit'], "
            "a.btn-search, button.btn-search, .search-btn"
        )
        if btn:
            btn.click()
        else:
            inp.press("Enter")

        page.wait_for_timeout(3000)

        postings = []
        for page_no in range(1, _MAX_PAGES + 1):
            rows_found = self._parse_all_contexts(page, postings)
            if not rows_found:
                break
            nxt = self._find_next_button(page, page_no)
            if not nxt:
                break
            nxt.click()
            page.wait_for_timeout(2000)

        return postings

    def _find_search_input(self, page):
        """메인 페이지 + 각 iframe에서 공고명 검색 input 탐색."""
        selectors = [
            "input[name='bidNtceNm']",
            "input[placeholder*='공고명']",
            "input[placeholder*='검색어']",
            "input[name='searchNm']",
        ]
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                for sel in selectors:
                    el = ctx.query_selector(sel)
                    if el:
                        return ctx, el
            except Exception:
                continue
        return None, None

    def _try_from_home(self, page):
        """홈에서 입찰공고 메뉴 클릭 후 재탐색."""
        try:
            page.goto(_HOME, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            bid_link = page.query_selector(
                "a:has-text('입찰공고목록'), a:has-text('입찰공고')"
            )
            if bid_link:
                bid_link.click()
                page.wait_for_timeout(3000)
                return self._find_search_input(page)
        except Exception:
            pass
        return None, None

    def _parse_all_contexts(self, page, postings: List[Posting]) -> int:
        """모든 context(메인+iframe)에서 행 파싱. 파싱된 건수 반환."""
        count = 0
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                rows = ctx.query_selector_all("table tbody tr")
                if rows:
                    print(f"  [g2b] 테이블 행={len(rows)}개 (frame: {ctx.url[:50]})")
                for row in rows:
                    p = self._parse_row(row)
                    if p:
                        postings.append(p)
                        count += 1
                if count:
                    break
            except Exception:
                continue
        return count

    def _find_next_button(self, page, current_page: int):
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                nxt = ctx.query_selector(
                    f"a:has-text('{current_page + 1}'), "
                    "a.next, a[title='다음페이지'], a[title='다음']"
                )
                if nxt:
                    return nxt
            except Exception:
                continue
        return None

    def _parse_row(self, row):
        title_el = row.query_selector("td a")
        if not title_el:
            return None
        title = title_el.inner_text().strip()
        if not title or title in ("이전", "다음", "처음", "마지막"):
            return None

        result = is_relevant(title)
        if not result.matched or result.stage == "excluded":
            return None

        href = title_el.get_attribute("href") or ""
        full_url = href if href.startswith("http") else f"https://www.g2b.go.kr{href}"
        cells = row.query_selector_all("td")
        deadline = self._find_deadline(cells)
        org = cells[1].inner_text().strip() if len(cells) > 1 else None

        return Posting(
            source_id=self.site_id,
            post_id=self._extract_post_id(href) or self._hash(title),
            title=title,
            url=full_url,
            deadline=deadline,
            organization=org,
            relevance_score=result.score,
            matched_keywords=result.matched_keywords,
        )

    def _find_deadline(self, cells) -> str:
        for cell in reversed(cells):
            text = cell.inner_text().strip()
            if len(text) >= 8 and any(c.isdigit() for c in text):
                return text
        return ""

    def _extract_post_id(self, href: str) -> str:
        for sep in ["bidNtceNo=", "seq=", "idx=", "no="]:
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
