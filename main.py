"""크롤링 실행 진입점.

사용법:
  python main.py                         # 전체 사이트, 이메일 발송
  python main.py --sites g2b bizinfo     # 특정 사이트만
  python main.py --dry-run               # DB 저장·이메일 없이 결과만 출력
  python main.py --deep                  # 상세 페이지 본문까지 2단계 필터
  python main.py --min-score 2           # 관련도 점수 2 이상만
  python main.py --no-email              # 이메일 발송 건너뜀
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

from models.posting import Posting
from storage.db import init_db, save_new
from crawlers.registry import get_crawler
from notifier.email import send as send_email

CONFIG_PATH = Path(__file__).parent / "config" / "sites.yaml"
LOG_DIR     = Path(__file__).parent / "logs"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"crawl_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def load_enabled_sites(filter_ids: list = None) -> list:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    sites = [s for s in cfg["sites"] if s.get("enabled", True)]
    if filter_ids:
        sites = [s for s in sites if s["id"] in filter_ids]
    return sites


def run(
    site_ids: list = None,
    dry_run: bool = False,
    deep: bool = False,
    min_score: int = 1,
    no_email: bool = False,
) -> List[Posting]:
    setup_logging()
    init_db()
    sites = load_enabled_sites(site_ids)

    if not sites:
        logging.info("실행할 사이트가 없습니다.")
        return []

    all_new: List[Posting] = []

    for site in sites:
        sid = site["id"]
        logging.info(f"[{sid}] {site['name']} 크롤링 시작...")
        try:
            crawler  = get_crawler(sid)
            postings = crawler.fetch()

            if deep and hasattr(crawler, "enrich_with_content"):
                logging.info(f"  [{sid}] 상세 페이지 분석 중... ({len(postings)}건)")
                postings = crawler.enrich_with_content(postings)

            postings = [p for p in postings if p.relevance_score >= min_score]
            logging.info(f"[{sid}] 관련 공고 {len(postings)}건 (score ≥ {min_score})")

            if dry_run:
                for p in sorted(postings, key=lambda x: -x.relevance_score):
                    kw = ", ".join(p.matched_keywords[:3])
                    logging.info(f"  [{p.relevance_score}점] {p.title[:55]}")
                    logging.info(f"        키워드: {kw}  마감: {p.deadline or '-'}")
            else:
                saved = save_new(postings)
                logging.info(f"[{sid}] 신규 {len(saved)}건 저장")
                all_new.extend(saved)

        except Exception as e:
            logging.error(f"[{sid}] 오류: {e}")

    if not dry_run:
        logging.info(f"\n완료 — 총 신규 공고 {len(all_new)}건")

        # 이메일 발송 (새 공고가 없어도 보내서 정상 작동 확인 가능)
        if not no_email:
            send_email(all_new)

    return all_new


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sites",     nargs="+", help="크롤링할 사이트 id")
    parser.add_argument("--dry-run",   action="store_true", help="DB 저장·이메일 없이 출력만")
    parser.add_argument("--deep",      action="store_true", help="상세 페이지 본문 2단계 필터")
    parser.add_argument("--min-score", type=int, default=1, help="최소 관련도 점수 (기본: 1)")
    parser.add_argument("--no-email",  action="store_true", help="이메일 발송 건너뜀")
    args = parser.parse_args()
    run(
        site_ids=args.sites,
        dry_run=args.dry_run,
        deep=args.deep,
        min_score=args.min_score,
        no_email=args.no_email,
    )
