from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Posting:
    source_id: str           # 사이트 id (g2b, bizinfo, ...)
    post_id: str             # 해당 사이트 내 고유 ID
    title: str
    url: str
    deadline: Optional[str] = None
    organization: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    crawled_at: datetime = field(default_factory=datetime.now)

    @property
    def uid(self) -> str:
        """중복 방지용 전역 고유키"""
        return f"{self.source_id}::{self.post_id}"
