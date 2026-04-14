"""
Módulo de persistência: histórico de downloads via SQLite.
DECISÃO ARQUITETURAL [2026-04-13]: SQLite síncrono via sqlite3 padrão.
Motivo: volume baixo (uso familiar), sem necessidade de ORM ou async driver.
Revisitar se houver necessidade de concorrência alta.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "/app/data/downloads.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria tabelas se não existirem."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id              TEXT PRIMARY KEY,
            url             TEXT NOT NULL,
            title           TEXT,
            format_label    TEXT,
            filename        TEXT,
            filesize        INTEGER,
            status          TEXT NOT NULL DEFAULT 'pending',
            error_msg       TEXT,
            is_playlist     INTEGER DEFAULT 0,
            playlist_total  INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            completed_at    TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_download(id: str, url: str, format_label: str) -> None:
    conn = _get_conn()
    conn.execute(
        """INSERT INTO downloads (id, url, format_label, status, created_at)
           VALUES (?, ?, ?, 'pending', ?)""",
        (id, url, format_label, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def update_download(id: str, **kwargs) -> None:
    """Atualiza campos arbitrários de um download pelo ID."""
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [id]
    conn = _get_conn()
    conn.execute(f"UPDATE downloads SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_history(limit: int = 100) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_download_record(id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM downloads WHERE id = ?", (id,))
    conn.commit()
    conn.close()
