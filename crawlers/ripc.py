"""RIPC (한국산업기술진흥원 지역혁신센터) 크롤러.

URL: https://pms.ripc.org/
로그인 필요 — 환경변수로 크리덴셜 관리.

환경변수:
  RIPC_USERNAME
  RIPC_PASSWORD

크리덴셜이 없으면 건너뜀.
"""
import os
from typing import List
from models.posting import Posting
from crawlers.base import BaseCrawler
from utils.browser import new_page

_LOGIN_URL = "https://pms.ripc.org/loginMain.do"
_LIST_URL  = "https://pms.ripc.org/pms/anno/selectAnnoList.do"  # 실제 경로 확인 필요


class RIPCCrawler(BaseCrawler):
    site_id = "ripc"

    def fetch(self) -> List[Posting]:
        username = os.environ.get("RIPC_USERNAME", "")
        password = os.environ.get("RIPC_PASSWORD", "")
        if not username or not password:
            print("[ripc] RIPC_USERNAME / RIPC_PASSWORD 미설정 — 건너뜀")
            return []

        page, browser = new_page()
        postings = []
        try:
            # 로그인
            page.goto(_LOGIN_URL, timeout=30000)
            page.wait_for_selector("input[name='userId'], input[type='text']", timeout=10000)
            page.fill("input[name='userId']", username)
            page.fill("input[name='userPw']", password)
            page.click("button[type='submit'], input[type='submit']")
            page.wait_for_load_state("networkidle", timeout=15000)

            # 공고 목록으로 이동
            page.goto(_LIST_URL, timeout=30000)
            page.wait_for_selector("table, .list", timeout=15000)

            rows = page.query_selector_all("table tbody tr")
            for row in rows:
                title_el = row.query_selector("td a")
                if not title_el:
                    continue
                title = title_el.inner_text().strip()
                href = title_el.get_attribute("href") or ""
                full_url = href if href.startswith("http") else f"https://pms.ripc.org{href}"
                cells = row.query_selector_all("td")
                deadline = cells[-1].inner_text().strip() if len(cells) > 1 else None
                post_id = self._extract_post_id(href) or self._hash(title)

                postings.append(Posting(
                    source_id=self.site_id,
                    post_id=post_id,
                    title=title,
                    url=full_url,
                    deadline=deadline,
                ))
        except Exception as e:
            print(f"[ripc] 크롤링 오류: {e}")
        finally:
            browser.close()

        return postings

    def _extract_post_id(self, href: str) -> str:
        for sep in ["annoId=", "seq=", "idx=", "no="]:
            if sep in href:
                return href.split(sep)[-1].split("&")[0]
        return ""

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:12]
