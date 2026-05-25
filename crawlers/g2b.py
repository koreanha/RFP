"""나라장터 크롤러.

공공데이터포털 OpenAPI 사용:
  https://www.data.go.kr/data/15000474/openapi.do  (입찰공고정보서비스)

환경변수:
  G2B_API_KEY  — 공공데이터포털에서 발급받은 서비스 키 (URL 인코딩된 키)

API 없이 테스트하려면 G2B_API_KEY=test 로 실행하면 빈 리스트 반환.
"""
import os
import requests
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler

_API_BASE = "https://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoThng"

# 디자인 관련 업종 코드 (나라장터 업종분류 기준)
_DESIGN_KEYWORDS = ["디자인", "design", "UX", "UI", "그래픽", "영상", "브랜드"]


class G2BCrawler(BaseCrawler):
    site_id = "g2b"

    def fetch(self) -> List[Posting]:
        api_key = os.environ.get("G2B_API_KEY", "")
        if not api_key or api_key == "test":
            print("[g2b] G2B_API_KEY 미설정 — 건너뜀")
            return []

        postings = []
        for keyword in _DESIGN_KEYWORDS:
            postings.extend(self._fetch_keyword(api_key, keyword))

        # 중복 제거 (여러 키워드에서 같은 공고가 나올 수 있음)
        seen = set()
        unique = []
        for p in postings:
            if p.uid not in seen:
                seen.add(p.uid)
                unique.append(p)
        return unique

    def _fetch_keyword(self, api_key: str, keyword: str) -> List[Posting]:
        params = {
            "serviceKey": api_key,
            "pageNo": "1",
            "numOfRows": "50",
            "type": "json",
            "inqryDiv": "1",           # 입력일자 기준
            "bidNtceNm": keyword,       # 공고명 검색
        }
        try:
            resp = requests.get(_API_BASE, params=params, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("response", {}).get("body", {}).get("items", [])
            if isinstance(items, dict):
                items = [items]
        except Exception as e:
            print(f"[g2b] API 오류 ({keyword}): {e}")
            return []

        result = []
        for item in items:
            post_id = item.get("bidNtceNo", "")
            if not post_id:
                continue
            result.append(Posting(
                source_id=self.site_id,
                post_id=post_id,
                title=item.get("bidNtceNm", ""),
                url=item.get("ntceUrl", f"https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo={post_id}"),
                deadline=item.get("bidClseDt", ""),
                organization=item.get("ntceInsttNm", ""),
                category=item.get("bidMethdNm", ""),
            ))
        return result
