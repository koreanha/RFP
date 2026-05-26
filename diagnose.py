"""각 사이트의 실제 페이지 구조를 확인하는 진단 스크립트.

실행:
    python diagnose.py

결과:
    - 각 사이트 스크린샷 → diagnose_*.png
    - 페이지 구조 정보 → 터미널 출력
"""
import sys
from pathlib import Path
from utils.browser import new_page

SITES = [
    {
        "id": "bizinfo",
        "url": "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do?pageIndex=1&searchCnd=0&searchWrd=디자인",
    },
    {
        "id": "seouldesign",
        "url": "https://seouldesign.or.kr/?menuno=150",
    },
    {
        "id": "egbiz",
        "url": "https://www.egbiz.or.kr/index.do",
    },
    {
        "id": "g2b",
        "url": "https://www.g2b.go.kr/",
    },
]


def diagnose(site_id: str, url: str):
    print(f"\n{'='*60}")
    print(f"[{site_id}] {url}")
    print('='*60)

    try:
        with new_page(headless=True) as page:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # 페이지 제목
            print(f"제목: {page.title()}")

            # iframe 개수 및 URL
            frames = page.frames
            print(f"iframe 수: {len(frames)}")
            for i, f in enumerate(frames):
                print(f"  frame[{i}]: {f.url[:100]}")

            # 테이블 개수 및 구조
            tables = page.query_selector_all("table")
            print(f"table 수: {len(tables)}")
            for i, tbl in enumerate(tables[:3]):
                ths = [th.inner_text().strip() for th in tbl.query_selector_all("th")]
                trs = tbl.query_selector_all("tbody tr")
                print(f"  table[{i}] 헤더: {ths[:6]}  /  tbody 행 수: {len(trs)}")
                if trs:
                    first_row_text = trs[0].inner_text().strip().replace('\n', ' ')[:80]
                    print(f"  table[{i}] 첫 행: {first_row_text}")

            # 목록 관련 class 이름 탐색
            for selector in [".board-list", ".list-wrap", ".bbs-list", ".notice-list",
                              "#boardList", ".boardList", ".contents-list", "ul.list",
                              ".board_list", ".list_wrap", ".sub-content"]:
                el = page.query_selector(selector)
                if el:
                    print(f"발견된 셀렉터: {selector}")

            # a 태그 중 공고/사업 관련 링크 샘플
            links = page.eval_on_selector_all(
                "a",
                "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))"
                ".filter(l => l.text.length > 4 && l.text.length < 60)"
            )
            keywords = ["공고", "지원", "사업", "디자인", "공모"]
            matched = [l for l in links if any(k in l["text"] for k in keywords)]
            print(f"관련 링크 ({len(matched)}개 중 최대 8개):")
            for l in matched[:8]:
                print(f"  {l['text'][:45]:45s}  {l['href'][:70]}")

            # 스크린샷 저장
            shot_path = Path(f"diagnose_{site_id}.png")
            page.screenshot(path=str(shot_path), full_page=False)
            print(f"스크린샷 저장: {shot_path.resolve()}")

    except Exception as e:
        print(f"오류: {e}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else [s["id"] for s in SITES]
    for site in SITES:
        if site["id"] in targets:
            diagnose(site["id"], site["url"])

    print("\n\n진단 완료. 스크린샷 파일을 확인하세요.")
