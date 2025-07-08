from pathlib import Path
import gnupg

SHUSH_HOME = Path.home() / ".shush"
GPG_HOME = SHUSH_HOME / "gpg"
MASTER_KEY_PATH = SHUSH_HOME / "master.key.gpg"
DB_PATH = SHUSH_HOME / "secrets.db"
LOG_PATH = SHUSH_HOME / "activity.log"

GPG = gnupg.GPG(gnupghome=str(GPG_HOME))