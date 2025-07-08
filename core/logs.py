import re
import hashlib

from datetime import datetime, timedelta, timezone

from .config import LOG_PATH


def parse_time_expr(expr: str) -> datetime:
    now = datetime.now(timezone.utc)

    if expr == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif expr == "yesterday":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        match = re.match(r"(\d+)([smhd])", expr)
        if not match:
            return datetime.fromisoformat(expr).astimezone(timezone.utc)
        value, unit = int(match[1]), match[2]
        delta = {
            "s": timedelta(seconds=value),
            "m": timedelta(minutes=value),
            "h": timedelta(hours=value),
            "d": timedelta(days=value),
        }[unit]
        return now - delta

def log_event(action: str, key: str = None, status: str = "success", note: str = ""):
    timestamp = datetime.now().astimezone().isoformat()
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:8] + "..." if key else ""
    line = f"[{timestamp}] {action:<12} {key_hash:<12} status={status}"

    if note:
        line += f" note={note}"

    with open(LOG_PATH, "a") as f:
        f.write(line.strip() + "\n")
