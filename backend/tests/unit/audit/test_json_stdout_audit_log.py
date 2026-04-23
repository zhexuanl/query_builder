"""Unit tests for JsonStdoutAuditLog."""
import json
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

import pytest

from adapters.audit.json_stdout_audit_log import JsonStdoutAuditLog
from domain.value_objects.audit_event import AuditEvent


@pytest.fixture()
def event() -> AuditEvent:
    return AuditEvent(
        caller_id="user-1",
        connection_id="conn-1",
        table_names=frozenset({"orders", "customers"}),
        dialect="postgres",
        outcome="success",
        row_count=5,
        duration_ms=42,
        timestamp=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )


def test_one_json_line_per_append(event, capsys):
    log = JsonStdoutAuditLog()
    log.append(event)
    log.append(event)
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 2


def test_all_fields_present(event, capsys):
    log = JsonStdoutAuditLog()
    log.append(event)
    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    assert record["caller_id"] == "user-1"
    assert record["connection_id"] == "conn-1"
    assert record["dialect"] == "postgres"
    assert record["outcome"] == "success"
    assert record["row_count"] == 5
    assert record["duration_ms"] == 42


def test_table_names_serialised_as_sorted_array(event, capsys):
    log = JsonStdoutAuditLog()
    log.append(event)
    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    assert record["table_names"] == ["customers", "orders"]


def test_timestamp_is_iso8601_string(event, capsys):
    log = JsonStdoutAuditLog()
    log.append(event)
    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    ts = record["timestamp"]
    assert isinstance(ts, str)
    datetime.fromisoformat(ts)  # must not raise


def test_broken_stdout_does_not_propagate(event):
    log = JsonStdoutAuditLog()
    broken = StringIO()
    broken.write = lambda s: (_ for _ in ()).throw(OSError("broken pipe"))  # type: ignore[assignment]
    with patch("adapters.audit.json_stdout_audit_log.sys.stdout", broken):
        log.append(event)  # must not raise
