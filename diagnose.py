"""사이트 HTML 구조 상세 진단 스크립트.

실행:
    python diagnose.py              # 전체 사이트
    python diagnose.py bizinfo      # 특정 사이트만
    python diagnose.py g2b seouldesign
"""
import sys
from pathlib import Path
from utils.browser import new_page

SITES = [
    {"id": "bizinfo",     "url": "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"},
    {"id": "seouldesign", "url": "https://seouldesign.or.kr/?menuno=18&siteno=1&boardno=19&cates=132"},
    {"id": "egbiz",       "url": "https://www.egbiz.or.kr/sp/supportPrjCatList.do"},
    {"id": "g2b",         "url": "https://www.g2b.go.kr/"},
]


def diagnose(site_id: str, url: str):
    print(f"\n{'='*65}")
    print(f"[{site_id}]  {url}")
    print('='*65)

    try:
        with new_page(headless=True) as page:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            print(f"페이지 제목: {page.title()}")

            # ── iframe 목록 (URL 포함) ──────────────────────────────
            frames = page.frames
            print(f"\n[iframe] 총 {len(frames)}개")
            for i, f in enumerate(frames):
                print(f"  [{i}] {f.url[:110]}")

            # ── 각 frame 별 링크·테이블 분석 ──────────────────────
            for fi, ctx in enumerate(frames):
                try:
                    frame_label = f"frame[{fi}]" if fi > 0 else "메인"

                    # 테이블
                    tables = ctx.query_selector_all("table")
                    if tables:
                        print(f"\n[{frame_label}] table {len(tables)}개")
                        for ti, tbl in enumerate(tables[:2]):
                            ths = [th.inner_text().strip()
                                   for th in tbl.query_selector_all("th")]
                            trs = tbl.query_selector_all("tbody tr")
                            print(f"  table[{ti}] 헤더: {ths[:7]}")
                            print(f"  table[{ti}] tbody 행 수: {len(trs)}")
                            if trs:
                                sample = trs[0].inner_text().strip().replace('\n', ' ')[:100]
                                print(f"  table[{ti}] 첫 행: {sample}")

                    # 리스트/카드 형 컨테이너
                    for sel in [".board-list", ".list-wrap", ".card-list",
                                 "#boardList", ".boardList", ".support-list",
                                 ".prj-list", ".contents-list", "ul.list",
                                 ".result-wrap", ".board_list"]:
                        el = ctx.query_selector(sel)
                        if el:
                            children = el.query_selector_all(":scope > *")
                            print(f"\n[{frame_label}] 발견: {sel}  ({len(children)}개 자식)")
                            break

                    # 검색 input
                    for sel in ["input[placeholder*='검색']", "input[type='search']",
                                 "input[name='searchNm']", "input[name='bidNtceNm']"]:
                        el = ctx.query_selector(sel)
                        if el:
                            ph = el.get_attribute("placeholder") or ""
                            nm = el.get_attribute("name") or ""
                            print(f"[{frame_label}] 검색 input: placeholder='{ph}'  name='{nm}'")
                            break

                    # 링크 샘플 (공고·지원 관련)
                    all_links = ctx.eval_on_selector_all(
                        "a",
                        "els => els.map(e => ({text: e.innerText.trim().slice(0,60), href: e.href}))"
                        ".filter(l => l.text.length > 5)"
                    )
                    kw_links = [l for l in all_links
                                if any(k in l["text"] for k in
                                       ["공고", "지원", "사업", "디자인", "공모", "입찰"])]
                    if kw_links:
                        print(f"[{frame_label}] 관련 링크 ({len(kw_links)}개, 최대 6개 출력):")
                        for l in kw_links[:6]:
                            print(f"  '{l['text'][:50]}'\n    → {l['href'][:100]}")

                except Exception as e:
                    print(f"[frame[{fi}]] 분석 오류: {e}")

            # ── 스크린샷 ──────────────────────────────────────────
            shot = Path(f"diagnose_{site_id}.png")
            page.screenshot(path=str(shot), full_page=False)
            print(f"\n스크린샷: {shot.resolve()}")

    except Exception as e:
        print(f"오류: {e}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else [s["id"] for s in SITES]
    for site in SITES:
        if site["id"] in targets:
            diagnose(site["id"], site["url"])
    print("\n진단 완료.")
