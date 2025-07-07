import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from cryptography.fernet import Fernet

from .config import DB_PATH


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

@contextmanager
def get_db_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.close()

def initialize_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Проверка целостности базы
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != "ok":
            raise RuntimeError(f"database integrity check failed: {result[0]}")

        # Создание таблиц
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()


def update_activity():
    with get_db_conn() as conn:
        conn.execute(
            "REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("last_activity", datetime.now().isoformat())
        )
        conn.commit()

def get_status() -> dict:
    if not DB_PATH.exists():
        raise RuntimeError("database not found")

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM secrets")
        count = cursor.fetchone()[0]

        cursor.execute("SELECT value FROM meta WHERE key = 'last_activity'")
        row = cursor.fetchone()
        last_activity = row[0] if row else "unknown"

    stat = os.stat(DB_PATH)
    return {
        "keys_count": count,
        "db_size_bytes": stat.st_size,
        "last_access": last_activity,
        "last_modified": datetime.fromtimestamp(stat.st_mtime),
    }

def get_secret(key: str, fernet: Fernet) -> str:
    key_hash = _hash_key(key)

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM secrets WHERE key = ?", (key_hash,))
        row = cursor.fetchone()

    update_activity()

    if row is None:
        raise KeyError(f"No secret found for key: {key}")

    return fernet.decrypt(row[0].encode()).decode()

def save_secret(key: str, value: str, fernet: Fernet):
    key_hash = _hash_key(key)
    encrypted = fernet.encrypt(value.encode()).decode()
    created_at = datetime.now().isoformat()

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            REPLACE INTO secrets (key, value, created_at) VALUES (?, ?, ?)
        """, (key_hash, encrypted, created_at))
        conn.commit()

    update_activity()

def delete_secret(key: str) -> bool:
    key_hash = _hash_key(key)

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM secrets WHERE key = ?", (key_hash,))
        affected = cursor.rowcount
        conn.commit()

    update_activity()
    return affected > 0
