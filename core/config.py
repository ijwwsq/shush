from pathlib import Path
import gnupg

GPG_HOME = Path.home() / ".shush" / "gpg"
MASTER_KEY_PATH = Path.home() / ".shush" / "master.key.gpg"
GPG = gnupg.GPG(gnupghome=str(GPG_HOME))
DB_PATH = Path.home() / ".shush" / "secrets.db"