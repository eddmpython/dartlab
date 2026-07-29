"""credential lifecycle 저장 상태와 만료 판정 회귀 테스트."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from dartlab.core.credentialLifecycle import (
    CredentialLifecycleCorruptError,
    CredentialLifecycleReadError,
    checkLifecycle,
)

pytestmark = pytest.mark.unit


def test_checkLifecycle_missingFileIsEmpty(tmp_path) -> None:
    """아직 생성되지 않은 lifecycle 파일은 등록 항목 0건을 뜻한다."""
    assert checkLifecycle(path=tmp_path / "missing.json") == []


def test_checkLifecycle_corruptJsonRaises(tmp_path) -> None:
    """존재하는 손상 파일을 자격증명 없음으로 축약하지 않는다."""
    path = tmp_path / "lifecycle.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(CredentialLifecycleCorruptError, match="lifecycle.json"):
        checkLifecycle(path=path)


def test_checkLifecycle_invalidUtf8RaisesTyped(tmp_path) -> None:
    """UTF-8이 아닌 기존 파일도 raw decoder 오류로 새지 않는다."""
    path = tmp_path / "lifecycle.json"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(CredentialLifecycleCorruptError, match="UTF-8"):
        checkLifecycle(path=path)


def test_checkLifecycle_readFailureRaisesTyped(tmp_path, monkeypatch) -> None:
    """존재 상태와 무관한 운영체제 읽기 실패도 등록 0건으로 축약하지 않는다."""
    path = tmp_path / "lifecycle.json"

    def failRead(self, *args, **kwargs):
        assert self == path
        raise PermissionError("simulated read failure")

    monkeypatch.setattr(Path, "read_text", failRead)

    with pytest.raises(CredentialLifecycleReadError, match="lifecycle.json"):
        checkLifecycle(path=path)


def test_checkLifecycle_invalidEntryRaisesWithKey(tmp_path) -> None:
    """만료 필드가 손상된 항목을 건너뛰지 않고 해당 key를 드러낸다."""
    path = tmp_path / "lifecycle.json"
    path.write_text(json.dumps({"BROKEN_KEY": {"issuedAt": "2026-01-01T00:00:00+00:00"}}), encoding="utf-8")

    with pytest.raises(CredentialLifecycleCorruptError, match="BROKEN_KEY"):
        checkLifecycle(path=path)


@pytest.mark.parametrize(
    "issuedAt",
    [None, "", "garbage", "2026-01-01T00:00:00"],
)
def test_checkLifecycle_invalidIssuedAtRaisesWithKey(tmp_path, issuedAt) -> None:
    """공개 alert의 발급 시점은 비어 있지 않은 timezone-aware ISO 값이어야 한다."""
    path = tmp_path / "lifecycle.json"
    entry = {
        "expiresAt": "2030-01-01T00:00:00+00:00",
    }
    if issuedAt is not None:
        entry["issuedAt"] = issuedAt
    path.write_text(json.dumps({"BROKEN_KEY": entry}), encoding="utf-8")

    with pytest.raises(CredentialLifecycleCorruptError, match="BROKEN_KEY"):
        checkLifecycle(path=path)


def test_checkLifecycle_recentlyExpiredIsExpired(tmp_path) -> None:
    """하루 미만 전에 만료된 key도 정수 절삭 때문에 critical로 낮아지지 않는다."""
    now = dt.datetime.now(dt.UTC)
    path = tmp_path / "lifecycle.json"
    path.write_text(
        json.dumps(
            {
                "EXPIRED_KEY": {
                    "issuedAt": (now - dt.timedelta(days=90)).isoformat(),
                    "expiresAt": (now - dt.timedelta(minutes=1)).isoformat(),
                }
            }
        ),
        encoding="utf-8",
    )

    alerts = checkLifecycle(path=path)

    assert len(alerts) == 1
    assert alerts[0].severity == "expired"
    assert alerts[0].daysRemaining == -1


def test_checkLifecycle_rejectsInvalidThreshold(tmp_path) -> None:
    """음수와 bool 임계값은 의미 없는 안전 판정을 만들 수 없다."""
    with pytest.raises(ValueError, match="thresholdDays"):
        checkLifecycle(thresholdDays=-1, path=tmp_path / "missing.json")
    with pytest.raises(TypeError, match="thresholdDays"):
        checkLifecycle(thresholdDays=True, path=tmp_path / "missing.json")
