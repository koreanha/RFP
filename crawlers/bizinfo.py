"""기업마당 크롤러 — playwright 브라우저 직접 탐색 방식."""
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
        url = f"{_SEARCH_BASE}?pageIndex=1&searchCnd=0&searchWrd={keyword}"
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        postings = []
        for page_no in range(1, _MAX_PAGES + 1):
            rows = self._parse_rows(page)
            postings.extend(rows)
            if not rows or not self._go_next_page(page, page_no):
                break
        return postings

    def _parse_rows(self, page) -> List[Posting]:
        postings = []
        rows = (
            page.query_selector_all("#boardList tbody tr")
            or page.query_selector_all("table.tblList tbody tr")
            or page.query_selector_all("table tbody tr")
            or page.query_selector_all(".boardList li")
        )
        for row in rows:
            title_el = row.query_selector("td.subject a, td.tit a, td a")
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
            cells = row.query_selector_all("td")
            deadline = self._find_deadline_cell(cells)

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
                relevance_score=title_result.score,
                matched_keywords=title_result.matched_keywords,
            ))
        return postings

    def enrich_with_content(self, postings: List[Posting]) -> List[Posting]:
        """상세 페이지 본문으로 2단계 필터링 (--deep 옵션 시 호출)."""
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

    def _find_deadline_cell(self, cells) -> str:
        for cell in cells:
            text = cell.inner_text().strip()
            if len(text) >= 10 and (text.count("-") >= 1 or text.count(".") >= 1):
                if any(c.isdigit() for c in text[:4]):
                    return text
        return ""

    def _go_next_page(self, page, current_page: int) -> bool:
        nxt = page.query_selector(
            f".pagination a:has-text('{current_page + 1}'), "
            f"#pagination a:has-text('{current_page + 1}'), "
            f"a.next, a[title='다음페이지']"
        )
        if nxt:
            nxt.click()
            page.wait_for_load_state("networkidle", timeout=8000)
            page.wait_for_timeout(1000)
            return True
        return False

    def _extract_post_id(self, href: str) -> str:
        for sep in ["pblancId=", "bbsIdx=", "seq=", "idx=", "nttId="]:
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
