"""mappingLedger ENV gate, 검증 선행 append, path override 단위 테스트.

본 ledger 는 prod 동작 0 영향이 핵심. ENV OFF 가 기본이며 어떤 호출도
file IO 를 일으키면 안 된다. 본 모듈은 옵트인 안전장치.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from dartlab.core.accounts import mappingLedger

pytestmark = pytest.mark.unit


@pytest.fixture
def _clearEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """ENV gate 와 path override 를 매 테스트마다 제거."""
    monkeypatch.delenv("DARTLAB_MAPPING_LEDGER", raising=False)
    monkeypatch.delenv("DARTLAB_MAPPING_LEDGER_PATH", raising=False)


class TestIsEnabled:
    def test_default_off(self, _clearEnv) -> None:
        assert mappingLedger.isEnabled() is False

    @pytest.mark.parametrize("flag", ["1", "true", "True", "YES", "on", "ON"])
    def test_truthy_values_enable(self, _clearEnv, monkeypatch, flag) -> None:
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", flag)
        assert mappingLedger.isEnabled() is True

    @pytest.mark.parametrize("flag", ["0", "false", "no", "off", "", "random"])
    def test_falsy_values_disable(self, _clearEnv, monkeypatch, flag) -> None:
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", flag)
        assert mappingLedger.isEnabled() is False


class TestLedgerPath:
    def test_default_path(self, _clearEnv) -> None:
        path = mappingLedger.ledgerPath()
        assert path.name == "mapping_candidates_raw.ndjson"
        assert path.parent.name == "data"

    def test_env_override(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        custom = tmp_path / "custom.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(custom))
        assert mappingLedger.ledgerPath() == custom


class TestAppend:
    def test_env_off_returns_zero_and_no_file(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        target = tmp_path / "off.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))
        # ENV flag 미설정 = OFF
        n = mappingLedger.append(
            [{"accountId": "x", "accountNm": "y", "sjDiv": "BS", "occurrenceCount": 1}],
            stockCode="005930",
        )
        assert n == 0
        assert not target.exists()

    def test_env_on_writes_ndjson_line(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        target = tmp_path / "on.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

        n = mappingLedger.append(
            [
                {
                    "accountId": "-표준계정코드 미사용-",
                    "accountNm": "기타의금융자산",
                    "sjDiv": "BS",
                    "occurrenceCount": 14,
                }
            ],
            stockCode="005930",
        )
        assert n == 1
        assert target.exists()

        lines = target.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["accountNm"] == "기타의금융자산"
        assert record["stockCode"] == "005930"
        assert record["sjDiv"] == "BS"
        assert record["occurrenceCount"] == 14
        assert "observedAt" in record

    def test_multiple_records_append_multiple_lines(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        target = tmp_path / "multi.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

        records = [
            {"accountId": "a", "accountNm": "기타의금융자산", "sjDiv": "BS", "occurrenceCount": 14},
            {"accountId": "b", "accountNm": "출자금의 중간분배", "sjDiv": "CF", "occurrenceCount": 6},
        ]
        n = mappingLedger.append(records, stockCode="000660")
        assert n == 2

        lines = target.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_append_creates_parent_directory(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "tree" / "ledger.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(nested))

        n = mappingLedger.append([{"accountId": "", "accountNm": "test", "sjDiv": "IS", "occurrenceCount": 1}])
        assert n == 1
        assert nested.exists()

    def test_append_preserves_extra_keys(self, _clearEnv, monkeypatch, tmp_path: Path) -> None:
        target = tmp_path / "extras.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

        records = [
            {
                "accountId": "x",
                "accountNm": "y",
                "sjDiv": "BS",
                "occurrenceCount": 3,
                "extraKey": "extraValue",
            }
        ]
        mappingLedger.append(records)

        record = json.loads(target.read_text(encoding="utf-8").strip())
        assert record["extraKey"] == "extraValue"

    def test_invalid_later_record_doesNotPartiallyCommit(
        self,
        _clearEnv,
        monkeypatch,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "invalid.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))
        records = [
            {"accountId": "ok", "accountNm": "정상", "sjDiv": "BS", "occurrenceCount": 1},
            {"accountId": "bad", "accountNm": "오류", "sjDiv": "BS", "occurrenceCount": "bad"},
        ]

        with pytest.raises(TypeError, match=r"records\[1\]\.occurrenceCount"):
            mappingLedger.append(records)

        assert not target.exists()

    def test_invalid_schema_doesNotCreateFile(
        self,
        _clearEnv,
        monkeypatch,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "invalid-schema.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

        with pytest.raises(ValueError, match="accountNm must not be empty"):
            mappingLedger.append([{"accountId": "", "accountNm": "", "sjDiv": "BS", "occurrenceCount": 1}])

        assert not target.exists()

    def test_append_flushes_to_disk_before_return(
        self,
        _clearEnv,
        monkeypatch,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "durable.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

        with patch.object(mappingLedger.os, "fsync") as fsyncMock:
            mappingLedger.append([{"accountId": "", "accountNm": "정상", "sjDiv": "BS", "occurrenceCount": 1}])

        fsyncMock.assert_called_once()

    def test_lock_timeout_is_typed_and_writes_nothing(
        self,
        _clearEnv,
        monkeypatch,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "contended.ndjson"
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
        monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))
        monkeypatch.setattr(mappingLedger, "_LOCK_TIMEOUT_SECONDS", 0.01)

        with mappingLedger.locked(target, timeoutSeconds=0):
            with pytest.raises(mappingLedger.MappingLedgerLockError, match="lock timeout"):
                mappingLedger.append([{"accountId": "", "accountNm": "정상", "sjDiv": "BS", "occurrenceCount": 1}])

        assert not target.exists()
