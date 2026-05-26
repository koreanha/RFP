"""이지비즈(경기기업비서) 크롤러.

진단 결과:
- 사이트명: 경기기업비서 (egbiz.or.kr)
- 올바른 목록 URL: /sp/supportPrjCatList.do (분야별 지원사업)
- SPA 구조 (iframe 3개, table 없음) → 검색창 입력 후 동적 로딩 대기
- 검색창 placeholder: '검색어를 입력해 주세요.'
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

        # 검색창 입력
        inp = page.query_selector(
            "input[placeholder='검색어를 입력해 주세요.'], "
            "input[type='search'], input[name='searchNm']"
        )
        if inp:
            inp.triple_click()
            inp.fill(keyword)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)  # SPA 렌더링 대기

        return self._parse_all_contexts(page)

    def _parse_all_contexts(self, page) -> List[Posting]:
        """메인 페이지 + iframe 모두에서 공고 파싱."""
        postings = []
        contexts = [page] + [f for f in page.frames if f != page.main_frame]
        for ctx in contexts:
            try:
                postings.extend(self._parse_context(ctx))
            except Exception:
                pass
        return postings

    def _parse_context(self, ctx) -> List[Posting]:
        postings = []

        # 카드형 또는 리스트형 아이템 탐색
        items = (
            ctx.query_selector_all(".card, .list-item, .support-item, .prj-item")
            or ctx.query_selector_all("li.item, ul.list li, .result-item")
            or ctx.query_selector_all("table tbody tr")
        )

        for item in items:
            title_el = item.query_selector("a, .tit, .title, h3, h4")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title or len(title) < 4:
                continue

            result = is_relevant(title)
            if not result.matched or result.stage == "excluded":
                continue

            href = title_el.get_attribute("href") or ""
            if not href:
                # 부모 a 태그 탐색
                parent_a = item.query_selector("a")
                href = parent_a.get_attribute("href") if parent_a else ""

            full_url = href if href.startswith("http") else f"{_BASE}{href}"

            date_el = item.query_selector(".date, .period, .deadline, td:last-child")
            deadline = date_el.inner_text().strip() if date_el else None

            postings.append(Posting(
                source_id=self.site_id,
                post_id=self._extract_post_id(href) or self._hash(title),
                title=title,
                url=full_url,
                deadline=deadline,
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
