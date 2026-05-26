"""나라장터 크롤러.

진단 결과: iframe 6개 구조, 링크가 javascript:void(null) → JS 기반 내비게이션.
전략: 메인 페이지 로드 후 각 iframe을 순회하며 검색 form을 찾아 키워드 검색.
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_HOME = "https://www.g2b.go.kr/"
_SEARCH_KEYWORDS = ["디자인", "그래픽", "UX", "브랜드", "영상제작"]
_MAX_PAGES = 3


class G2BCrawler(BaseCrawler):
    site_id = "g2b"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                page.goto(_HOME, timeout=30000, wait_until="networkidle")
                page.wait_for_timeout(3000)

                # iframe 중 검색 form이 있는 frame 찾기
                search_frame = self._find_search_frame(page)

                if search_frame is None:
                    print("  [g2b] 검색 frame을 찾지 못했습니다. diagnose.py --frames 실행 권장")
                    return []

                for kw in _SEARCH_KEYWORDS:
                    try:
                        results = self._search_in_frame(search_frame, kw)
                        postings.extend(results)
                    except Exception as e:
                        print(f"  [g2b] '{kw}' 오류: {e}")

        except Exception as e:
            print(f"[g2b] 크롤링 오류: {e}")

        return self._deduplicate(postings)

    def _find_search_frame(self, page):
        """입찰공고 검색창이 있는 iframe 탐색."""
        # 메인 페이지 자체에서 먼저 시도
        if page.query_selector("input[name='bidNtceNm'], input[placeholder*='공고명']"):
            return page

        # 각 iframe 순회
        for frame in page.frames[1:]:
            try:
                if frame.query_selector(
                    "input[name='bidNtceNm'], input[placeholder*='공고명'], "
                    "input[name='searchNm'], form[name*='bid']"
                ):
                    return frame
            except Exception:
                continue

        # 못 찾은 경우: 입찰공고목록 링크 클릭 후 재탐색
        try:
            bid_link = page.query_selector("a:has-text('입찰공고목록'), a:has-text('입찰공고')")
            if bid_link:
                bid_link.click()
                page.wait_for_timeout(2000)
                for frame in page.frames[1:]:
                    try:
                        if frame.query_selector("input[name='bidNtceNm']"):
                            return frame
                    except Exception:
                        continue
        except Exception:
            pass

        return None

    def _search_in_frame(self, ctx, keyword: str) -> List[Posting]:
        postings = []

        inp = ctx.query_selector("input[name='bidNtceNm'], input[placeholder*='공고명'], input[name='searchNm']")
        if not inp:
            return []

        inp.triple_click()
        inp.fill(keyword)

        # 검색 버튼 또는 Enter
        btn = ctx.query_selector("button[type='submit'], input[type='submit'], a.btn-search")
        if btn:
            btn.click()
        else:
            inp.press("Enter")

        ctx.wait_for_timeout(2000)

        for page_no in range(1, _MAX_PAGES + 1):
            rows = ctx.query_selector_all("table tbody tr")
            if not rows:
                break
            for row in rows:
                p = self._parse_row(row)
                if p:
                    postings.append(p)
            # 다음 페이지
            nxt = ctx.query_selector(f"a:has-text('{page_no + 1}'), a.next, a[title='다음']")
            if not nxt:
                break
            nxt.click()
            ctx.wait_for_timeout(1500)

        return postings

    def _parse_row(self, row):
        title_el = row.query_selector("td a")
        if not title_el:
            return None
        title = title_el.inner_text().strip()
        if not title or title in ("이전", "다음", "처음", "마지막"):
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
