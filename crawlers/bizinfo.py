"""기업마당 크롤러 — playwright 브라우저 직접 탐색 방식.

URL: https://www.bizinfo.go.kr/
지원사업 공고 목록 → 디자인 관련 키워드 필터링.

전략:
  1. 지원사업 목록 페이지 직접 접근
  2. 검색창에 키워드 입력
  3. 결과 파싱 + 페이지네이션

실행 환경: 반드시 로컬에서 실행 (클라우드 환경 네트워크 차단됨).
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

# 기업마당 지원사업 통합검색 URL
_SEARCH_BASE = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
_HOME = "https://www.bizinfo.go.kr/"
_DESIGN_KEYWORDS = ["디자인", "UX", "UI", "그래픽", "브랜드", "시각", "영상", "콘텐츠"]
_MAX_PAGES = 5


class BizinfoCrawler(BaseCrawler):
    site_id = "bizinfo"

    def fetch(self) -> List[Posting]:
        page, browser = new_page()
        postings = []
        try:
            for keyword in _DESIGN_KEYWORDS:
                try:
                    results = self._fetch_keyword(page, keyword)
                    postings.extend(results)
                    print(f"  [bizinfo] '{keyword}' → {len(results)}건")
                except Exception as e:
                    print(f"  [bizinfo] '{keyword}' 오류: {e}")
        except Exception as e:
            print(f"[bizinfo] 크롤링 오류: {e}")
        finally:
            browser.close()

        return self._deduplicate(postings)

    def _fetch_keyword(self, page, keyword: str) -> List[Posting]:
        # 검색 파라미터를 URL에 포함해서 직접 이동
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

        # 다양한 셀렉터 시도 (사이트 구조 변경 대비)
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
            if not title or "등록된" in title:  # "등록된 글이 없습니다" 등 빈 결과 문구 제거
                continue

            href = title_el.get_attribute("href") or ""
            full_url = href if href.startswith("http") else f"https://www.bizinfo.go.kr{href}"

            cells = row.query_selector_all("td")
            # 기업마당은 보통 마지막 컬럼이 접수기간
            deadline = self._find_deadline_cell(cells)

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
            ))
        return postings

    def _find_deadline_cell(self, cells) -> str:
        """'접수기간', '마감' 헤더에 해당하는 셀 값을 찾아 반환."""
        for cell in cells:
            text = cell.inner_text().strip()
            # 날짜 형식 패턴 (YYYY-MM-DD 또는 YYYY.MM.DD)
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
