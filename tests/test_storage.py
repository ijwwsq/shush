import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3

import pytest
from cryptography.fernet import Fernet

from core import storage


@pytest.fixture
def temp_db(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "secrets.db"

    monkeypatch.setattr(storage, "DB_PATH", db_path)
    yield db_path
    shutil.rmtree(temp_dir)

@pytest.fixture
def fernet():
    return Fernet(Fernet.generate_key())

def test_initialize_db_creates_tables(temp_db):
    storage.initialize_db()
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "secrets" in tables
    assert "meta" in tables

def test_save_and_get_secret(temp_db, fernet):
    storage.initialize_db()
    key = "my_key"
    value = "my_secret"

    storage.save_secret(key, value, fernet)
    retrieved = storage.get_secret(key, fernet)
    assert retrieved == value

def test_delete_secret(temp_db, fernet):
    storage.initialize_db()
    key = "to_delete"
    value = "value"
    storage.save_secret(key, value, fernet)

    deleted = storage.delete_secret(key)
    assert deleted

    with pytest.raises(KeyError):
        storage.get_secret(key, fernet)

def test_get_status(temp_db, fernet):
    storage.initialize_db()
    storage.save_secret("k1", "v1", fernet)
    status = storage.get_status()

    assert "keys_count" in status
    assert "last_access" in status
    assert "last_modified" in status
    assert "db_size_bytes" in status
    assert status["keys_count"] == 1
