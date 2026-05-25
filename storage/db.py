import sqlite3
from pathlib import Path
from typing import List
from models.posting import Posting

DB_PATH = Path(__file__).parent.parent / "data" / "postings.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                uid          TEXT PRIMARY KEY,
                source_id    TEXT NOT NULL,
                post_id      TEXT NOT NULL,
                title        TEXT NOT NULL,
                url          TEXT NOT NULL,
                deadline     TEXT,
                organization TEXT,
                category     TEXT,
                description  TEXT,
                crawled_at   TEXT NOT NULL
            )
        """)


def save_new(postings: List[Posting]) -> List[Posting]:
    """새 공고만 저장하고 실제 저장된 항목 반환"""
    saved = []
    with _connect() as conn:
        for p in postings:
            try:
                conn.execute(
                    """INSERT INTO postings
                       (uid, source_id, post_id, title, url, deadline,
                        organization, category, description, crawled_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (p.uid, p.source_id, p.post_id, p.title, p.url,
                     p.deadline, p.organization, p.category, p.description,
                     p.crawled_at.isoformat()),
                )
                saved.append(p)
            except sqlite3.IntegrityError:
                pass  # 이미 저장된 공고 — 스킵
    return saved


def already_seen(uid: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM postings WHERE uid=?", (uid,)).fetchone()
    return row is not None
