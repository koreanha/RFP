"""나라장터 크롤러 — playwright 브라우저 직접 탐색 방식.

메뉴 클릭 대신 검색 URL로 직접 이동해서 안정성 확보.
키워드별로 용역 입찰공고 검색 → 결과 파싱 + 페이지네이션.
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

# 나라장터 용역 입찰공고 검색 URL (GET 방식)
_SEARCH_URL = (
    "https://www.g2b.go.kr/pt/menu/selectSubFrame.do"
    "?framesrc=/pt/menu/frameTgong.do"
    "?bidNtceMenu=Y&bidNtceSn=&bidClseNm=&inqryDiv=1"
    "&bidNtceNm={keyword}&currentPageNo={page}"
)
_HOME = "https://www.g2b.go.kr/"
_SEARCH_KEYWORDS = ["디자인", "그래픽", "UX", "UI", "브랜드", "시각", "영상제작", "홍보물"]
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
                    except Exception as e:
                        print(f"  [g2b] 키워드 '{kw}' 오류: {e}")
        except Exception as e:
            print(f"[g2b] 크롤링 오류: {e}")

        return self._deduplicate(postings)

    def _search_keyword(self, page, keyword: str) -> List[Posting]:
        postings = []
        for page_no in range(1, _MAX_PAGES + 1):
            url = _SEARCH_URL.format(keyword=keyword, page=page_no)
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # iframe 내부 탐색
            rows = self._get_rows(page)
            if not rows:
                break

            postings.extend(self._parse_rows(rows))
        return postings

    def _get_rows(self, page):
        """메인 페이지 또는 iframe에서 테이블 행 탐색."""
        rows = page.query_selector_all("table tbody tr")
        if rows:
            return rows
        for frame in page.frames[1:]:
            try:
                rows = frame.query_selector_all("table tbody tr")
                if rows:
                    return rows
            except Exception:
                continue
        return []

    def _parse_rows(self, rows) -> List[Posting]:
        postings = []
        for row in rows:
            title_el = row.query_selector("td a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title or title in ("이전", "다음", "처음", "마지막"):
                continue

            href = title_el.get_attribute("href") or ""
            full_url = (
                href if href.startswith("http")
                else f"https://www.g2b.go.kr{href}"
            )
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
