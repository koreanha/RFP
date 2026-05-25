from typing import Dict, Type
from crawlers.base import BaseCrawler
from crawlers.g2b import G2BCrawler
from crawlers.bizinfo import BizinfoCrawler
from crawlers.ripc import RIPCCrawler
from crawlers.seouldesign import SeoulDesignCrawler

# 새 크롤러 추가 시 여기에 한 줄만 추가
_CRAWLERS: Dict[str, Type[BaseCrawler]] = {
    "g2b":         G2BCrawler,
    "bizinfo":     BizinfoCrawler,
    "ripc":        RIPCCrawler,
    "seouldesign": SeoulDesignCrawler,
}


def get_crawler(site_id: str) -> BaseCrawler:
    cls = _CRAWLERS.get(site_id)
    if cls is None:
        raise ValueError(f"등록되지 않은 사이트: {site_id}. registry.py 에 추가하세요.")
    return cls()


def list_crawlers() -> list:
    return list(_CRAWLERS.keys())
