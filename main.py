"""크롤링 실행 진입점.

사용법:
  python main.py                        # 활성화된 모든 사이트 크롤링 (제목 필터)
  python main.py --sites g2b bizinfo    # 특정 사이트만
  python main.py --dry-run              # DB 저장 없이 결과 출력만
  python main.py --deep                 # 상세 페이지 본문까지 2단계 필터 적용
  python main.py --min-score 2          # 관련도 점수 2 이상만 저장
"""
import argparse
import yaml
from pathlib import Path
from storage.db import init_db, save_new
from crawlers.registry import get_crawler

CONFIG_PATH = Path(__file__).parent / "config" / "sites.yaml"


def load_enabled_sites(filter_ids: list = None) -> list:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    sites = [s for s in cfg["sites"] if s.get("enabled", True)]
    if filter_ids:
        sites = [s for s in sites if s["id"] in filter_ids]
    return sites


def run(site_ids: list = None, dry_run: bool = False, deep: bool = False, min_score: int = 1):
    init_db()
    sites = load_enabled_sites(site_ids)

    if not sites:
        print("실행할 사이트가 없습니다.")
        return

    total_new = 0
    for site in sites:
        sid = site["id"]
        print(f"\n[{sid}] {site['name']} 크롤링 시작...")
        try:
            crawler = get_crawler(sid)
            postings = crawler.fetch()

            # --deep 옵션: 상세 페이지 본문까지 2단계 필터 적용
            if deep and hasattr(crawler, "enrich_with_content"):
                print(f"  [{sid}] 상세 페이지 분석 중... ({len(postings)}건)")
                postings = crawler.enrich_with_content(postings)

            # 관련도 점수 필터
            postings = [p for p in postings if p.relevance_score >= min_score]
            print(f"[{sid}] 관련 공고 {len(postings)}건 (score ≥ {min_score})")

            if dry_run:
                for p in sorted(postings, key=lambda x: -x.relevance_score):
                    kw = ", ".join(p.matched_keywords[:3])
                    print(f"  [{p.relevance_score}점] {p.title[:55]}  마감:{p.deadline or '-'}")
                    print(f"        키워드: {kw}")
            else:
                saved = save_new(postings)
                print(f"[{sid}] 신규 {len(saved)}건 저장")
                total_new += len(saved)

        except Exception as e:
            print(f"[{sid}] 오류: {e}")

    if not dry_run:
        print(f"\n완료 — 총 신규 공고 {total_new}건 저장")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sites", nargs="+", help="크롤링할 사이트 id (미지정 시 전체)")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 결과 출력만")
    parser.add_argument("--deep", action="store_true", help="상세 페이지 본문까지 2단계 필터 적용")
    parser.add_argument("--min-score", type=int, default=1, help="최소 관련도 점수 (기본: 1)")
    args = parser.parse_args()
    run(site_ids=args.sites, dry_run=args.dry_run, deep=args.deep, min_score=args.min_score)
