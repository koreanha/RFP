"""이지비즈(경기기업비서) 크롤러.

진단 결과:
- 사이트명: 경기기업비서 (egbiz.or.kr)
- 목록 URL: /sp/supportPrjCatList.do (분야별 지원사업)
- 카드형 레이아웃 (table 없음)
- 검색창 placeholder: '지원사업명으로 조회'
"""
import hashlib
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page
from filter import is_relevant

_LIST_URL = "https://www.egbiz.or.kr/sp/supportPrjCatList.do"
_BASE = "https://www.egbiz.or.kr"
_SEARCH_TERMS = ["디자인", "제품디자인", "디자인컨설팅"]

# 카드형 아이템 셀렉터 우선순위 목록 (진단 화면에서 확인)
_CARD_SELECTORS = [
    ".support-item", ".card-item", ".list-item",
    ".prj-item", ".item", "li.card", "li.item",
    ".contents-list li", ".result-list li",
    ".board-list li", "ul.list li",
]


class EgbizCrawler(BaseCrawler):
    site_id = "egbiz"

    def fetch(self) -> List[Posting]:
        postings = []
        try:
            with new_page() as page:
                for keyword in _SEARCH_TERMS:
                    try:
                        results = self._fetch_keyword(page, keyword)
                        postings.extend(results)
                        print(f"  [egbiz] '{keyword}' → {len(results)}건 관련")
                    except Exception as e:
                        print(f"  [egbiz] '{keyword}' 오류: {e}")
        except Exception as e:
            print(f"[egbiz] 크롤링 오류: {e}")
        return self._deduplicate(postings)

    def _fetch_keyword(self, page, keyword: str) -> List[Posting]:
        page.goto(_LIST_URL, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 검색창 입력 (placeholder 확인됨: '지원사업명으로 조회')
        inp = (
            page.query_selector("input[placeholder='지원사업명으로 조회']")
            or page.query_selector("input[placeholder*='조회']")
            or page.query_selector("input[placeholder*='검색']")
            or page.query_selector("input[type='search']")
            or page.query_selector("input[name='searchNm']")
        )
        if inp:
            inp.triple_click()
            inp.fill(keyword)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)  # SPA 렌더링 대기
        else:
            print(f"  [egbiz] 검색창 없음 — 전체 목록 파싱")

        return self._parse_all_contexts(page)

    def _parse_all_contexts(self, page) -> List[Posting]:
        postings = []
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                found = self._parse_context(ctx)
                postings.extend(found)
            except Exception:
                pass
        return postings

    def _parse_context(self, ctx) -> List[Posting]:
        # 카드/리스트형 아이템 탐색
        items = []
        for sel in _CARD_SELECTORS:
            items = ctx.query_selector_all(sel)
            if items:
                break

        # 카드도 없으면 테이블 tr로 폴백
        if not items:
            items = ctx.query_selector_all("table tbody tr")

        postings = []
        for item in items:
            title_el = (
                item.query_selector(".tit, .title, .subject")
                or item.query_selector("a strong, a span, a")
                or item.query_selector("h3, h4, h5")
            )
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title or len(title) < 4:
                continue

            result = is_relevant(title)
            if not result.matched or result.stage == "excluded":
                continue

            # href 탐색: title_el 자체 or 가장 가까운 a
            href = title_el.get_attribute("href") or ""
            if not href:
                parent_a = item.query_selector("a")
                href = parent_a.get_attribute("href") if parent_a else ""

            full_url = href if href.startswith("http") else f"{_BASE}{href}"

            date_el = item.query_selector(
                ".date, .period, .deadline, .end-date, "
                ".apply-date, td:last-child, span.date"
            )
            deadline = date_el.inner_text().strip() if date_el else None

            org_el = item.query_selector(".org, .agency, .inst, .institution")
            org = org_el.inner_text().strip() if org_el else None

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
                organization=org,
                relevance_score=result.score,
                matched_keywords=result.matched_keywords,
            ))
        return postings

    def _extract_post_id(self, href: str) -> str:
        for sep in ["prjId=", "pblancId=", "seq=", "idx=", "no="]:
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
