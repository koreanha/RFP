"""나라장터 크롤러 — playwright 브라우저 직접 탐색 방식.

나라장터는 iframe 중첩 + JS 렌더링 구조라 API 없이는 playwright 필수.
전략:
  1. 홈에서 '입찰공고' 메뉴 진입
  2. 용역 탭(디자인 공고가 주로 여기) 선택
  3. 키워드 검색 반복 (디자인, 그래픽, UX/UI 등)
  4. 결과 파싱 + 페이지네이션

실행 환경: 반드시 로컬에서 실행 (클라우드 환경 네트워크 차단됨).
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_HOME = "https://www.g2b.go.kr/"
_SEARCH_KEYWORDS = ["디자인", "그래픽", "UX", "UI", "브랜드", "시각", "영상제작", "홍보물"]
_MAX_PAGES = 3  # 키워드당 최대 페이지 수


class G2BCrawler(BaseCrawler):
    site_id = "g2b"

    def fetch(self) -> List[Posting]:
        page, browser = new_page()
        postings = []
        try:
            page.goto(_HOME, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # 입찰공고 메뉴 클릭 시도
            bid_menu = self._find_bid_menu(page)
            if bid_menu:
                bid_menu.click()
                page.wait_for_timeout(2000)

            # 각 키워드 검색
            for kw in _SEARCH_KEYWORDS:
                try:
                    results = self._search_keyword(page, kw)
                    postings.extend(results)
                except Exception as e:
                    print(f"  [g2b] 키워드 '{kw}' 오류: {e}")

        except Exception as e:
            print(f"[g2b] 크롤링 오류: {e}")
        finally:
            browser.close()

        return self._deduplicate(postings)

    def _find_bid_menu(self, page):
        """입찰공고 메뉴 링크 탐색 — 사이트 구조 변경에 대비해 다중 셀렉터 시도."""
        candidates = [
            "a:has-text('입찰공고')",
            "a:has-text('입찰정보')",
            "#gnb a:has-text('입찰')",
            ".nav a:has-text('입찰')",
        ]
        for sel in candidates:
            el = page.query_selector(sel)
            if el:
                return el
        return None

    def _search_keyword(self, page, keyword: str) -> List[Posting]:
        """검색창에 키워드 입력 후 결과 파싱."""
        postings = []

        # 검색 input 찾기
        search_input = page.query_selector(
            "input[name='bidNtceNm'], input[placeholder*='공고'], input[name='searchNm'], input[type='search']"
        )
        if not search_input:
            # iframe 안에 있는 경우
            for frame in page.frames[1:]:
                search_input = frame.query_selector(
                    "input[name='bidNtceNm'], input[placeholder*='공고']"
                )
                if search_input:
                    page = frame  # frame을 page처럼 사용
                    break

        if not search_input:
            return []

        search_input.fill(keyword)
        search_input.press("Enter")
        page.wait_for_load_state("networkidle", timeout=10000)

        for page_no in range(1, _MAX_PAGES + 1):
            rows = self._parse_rows(page)
            postings.extend(rows)
            if not self._go_next_page(page, page_no):
                break

        return postings

    def _parse_rows(self, ctx) -> List[Posting]:
        """테이블 행에서 공고 정보 추출."""
        postings = []
        rows = ctx.query_selector_all("table tbody tr")
        for row in rows:
            title_el = row.query_selector("td a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title or title in ("이전", "다음", "처음", "마지막"):
                continue
            href = title_el.get_attribute("href") or ""
            full_url = href if href.startswith("http") else f"https://www.g2b.go.kr{href}"

            cells = row.query_selector_all("td")
            deadline = self._find_deadline(cells)
            org = cells[1].inner_text().strip() if len(cells) > 1 else None

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
                organization=org,
            ))
        return postings

    def _find_deadline(self, cells) -> str:
        """마감일이 담긴 셀을 역방향으로 탐색."""
        for cell in reversed(cells):
            text = cell.inner_text().strip()
            if len(text) >= 8 and any(c.isdigit() for c in text):
                return text
        return ""

    def _go_next_page(self, ctx, current_page: int) -> bool:
        """다음 페이지 버튼 클릭. 없으면 False 반환."""
        nxt = ctx.query_selector(f"a:has-text('{current_page + 1}'), .paging a.next, a[title='다음']")
        if nxt:
            nxt.click()
            ctx.wait_for_load_state("networkidle", timeout=8000)
            return True
        return False

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
