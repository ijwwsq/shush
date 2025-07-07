import pytest
import tempfile
from pathlib import Path
from core import crypto


@pytest.fixture
def temp_env(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    gpg_home = temp_dir / "gpg"
    master_path = temp_dir / "master.key.gpg"

    gpg_home.mkdir(parents=True)  # важно: создать gpg каталог

    monkeypatch.setattr(crypto, "SHUSH_HOME", temp_dir)
    monkeypatch.setattr(crypto, "GPG_HOME", gpg_home)
    monkeypatch.setattr(crypto, "MASTER_KEY_PATH", master_path)
    monkeypatch.setattr(crypto, "GPG", crypto.gnupg.GPG(gnupghome=str(gpg_home)))

    return temp_dir

def test_encrypt_decrypt_master_key(temp_env):
    master_password = "testpassword"

    crypto.encrypt_master_key(master_password)
    assert crypto.MASTER_KEY_PATH.exists()

    decrypted = crypto.decrypt_master_key(master_password)
    assert decrypted == master_password

def test_fernet_key_derivation():
    password = "anothersecret"
    fernet = crypto.derive_fernet_key(password)
    encrypted = fernet.encrypt(b"data")
    decrypted = fernet.decrypt(encrypted)
    assert decrypted == b"data"
