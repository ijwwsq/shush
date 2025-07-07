import gnupg
import os
import base64
import hashlib
import gc
from pathlib import Path
from .config import GPG_HOME, MASTER_KEY_PATH, SHUSH_HOME
from cryptography.fernet import Fernet


GPG = gnupg.GPG(gnupghome=str(GPG_HOME))

def initialize_gpg():
    os.makedirs(SHUSH_HOME, exist_ok=True)
    os.makedirs(GPG_HOME, exist_ok=True)
    os.makedirs(MASTER_KEY_PATH.parent, exist_ok=True)

def encrypt_master_key(master_password: str) -> None:
    output = GPG.encrypt(
        master_password,
        recipients=None,
        symmetric=True,
        passphrase=master_password,
        armor=False,
        always_trust=True,
        output=str(MASTER_KEY_PATH),
    )
    if not output.ok:
        raise RuntimeError(f"gpg encryption failed: {output.status}")

def decrypt_master_key(gpg_passphrase: str) -> str:
    with open(MASTER_KEY_PATH, "rb") as f:
        decrypted = GPG.decrypt_file(f, passphrase=gpg_passphrase)
    if not decrypted.ok:
        raise RuntimeError(f"gpg decryption failed: {decrypted.status}")
    return str(decrypted)

def derive_fernet_key(password: str) -> Fernet:
    hash_digest = hashlib.sha256(password.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(hash_digest)
    return Fernet(fernet_key)

def clear_sensitive_data(*vars):
    for var in vars:
        if isinstance(var, str):
            var = None
    gc.collect()
