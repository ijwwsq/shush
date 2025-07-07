import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

from .config import DB_PATH


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def initialize_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    conn.close()

def update_activity():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO meta (key, value) VALUES (?, ?)", ("last_activity", str(datetime.now())))
    conn.commit()
    conn.close()

def get_status() -> dict:
    if not os.path.exists(DB_PATH):
        raise RuntimeError("database not found")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM secrets")
    count = cursor.fetchone()[0]

    cursor.execute("SELECT value FROM meta WHERE key = 'last_activity'")
    activity_row = cursor.fetchone()
    last_activity = activity_row[0] if activity_row else "unknown"

    conn.close()

    stat = os.stat(DB_PATH)

    return {
        "keys_count": count,
        "db_size_bytes": stat.st_size,
        "last_access": last_activity,
        "last_modified": datetime.fromtimestamp(stat.st_mtime),
    }

def get_secret(key: str, fernet: Fernet) -> str:
    key_hash = _hash_key(key)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM secrets WHERE key = ?", (key_hash,))
    row = cursor.fetchone()
    conn.close()
    update_activity()

    if row is None:
        raise KeyError(f"No secret found for key: {key}")

    encrypted_value = row[0]
    decrypted_value = fernet.decrypt(encrypted_value.encode()).decode()
    return decrypted_value

def save_secret(key: str, value: str, fernet: Fernet):
    key_hash = _hash_key(key)
    encrypted = fernet.encrypt(value.encode()).decode()
    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)

    cursor.execute("REPLACE INTO secrets (key, value, created_at) VALUES (?, ?, ?)", (key_hash, encrypted, created_at))
    conn.commit()
    update_activity()
    conn.close()

def delete_secret(key: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM secrets WHERE key = ?", (key,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    update_activity()
    return affected > 0
