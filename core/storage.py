import sqlite3
from cryptography.fernet import Fernet
from pathlib import Path
from .config import DB_PATH


def initialize_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_secret(key: str, fernet: Fernet) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM secrets WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise KeyError(f"No secret found for key: {key}")

    encrypted_value = row[0]
    decrypted_value = fernet.decrypt(encrypted_value.encode()).decode()
    return decrypted_value

def save_secret(key: str, value: str, fernet: Fernet):
    encrypted = fernet.encrypt(value.encode()).decode()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("REPLACE INTO secrets (key, value) VALUES (?, ?)", (key, encrypted))
    conn.commit()
    conn.close()

def delete_secret(key: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM secrets WHERE key = ?", (key,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def list_keys() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM secrets ORDER BY key")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
