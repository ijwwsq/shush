import re
import os
import tempfile
from datetime import datetime, timedelta, timezone

from core.logs import log_event, parse_time_expr
from core.config import LOG_PATH


def test_log_event_writes_line(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "activity.log")
        
        # правильно: заменяем переменную прямо в модуле core.logs
        monkeypatch.setattr("core.logs.LOG_PATH", path)

        log_event("add", key="mykey", status="success", note="test")

        assert os.path.exists(path)

        with open(path, "r") as f:
            line = f.read().strip()
            assert "add" in line
            assert "status=success" in line
            assert "note=test" in line

def test_parse_time_expr_relative():
    now = datetime.now(timezone.utc)

    assert parse_time_expr("2h") <= now - timedelta(hours=1, minutes=59)
    assert parse_time_expr("1d") <= now - timedelta(hours=23)

def test_parse_time_expr_today():
    result = parse_time_expr("today")
    assert result.hour == 0
    assert result.tzinfo is not None

def test_parse_time_expr_iso():
    dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    expr = dt.isoformat()
    parsed = parse_time_expr(expr)
    assert parsed == dt
