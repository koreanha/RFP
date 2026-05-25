from abc import ABC, abstractmethod
from typing import List
from models.posting import Posting


class BaseCrawler(ABC):
    """모든 사이트 크롤러가 상속하는 인터페이스.

    새 사이트 추가 방법:
      1. 이 클래스를 상속한 파일을 crawlers/<site_id>.py 로 생성
      2. site_id 와 fetch() 를 구현
      3. config/sites.yaml 에 항목 추가
      4. crawlers/registry.py 의 _CRAWLERS 에 등록
    """

    site_id: str  # config/sites.yaml 의 id 와 일치

    @abstractmethod
    def fetch(self) -> List[Posting]:
        """공고 목록을 가져와 Posting 리스트로 반환"""
        ...
