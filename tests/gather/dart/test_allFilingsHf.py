"""allFilingsHf: HF 폴백 타입·재동기화 게이트 단위 테스트 (DI fake, 네트워크 0)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_error_taxonomy_preserves_period_and_hierarchy() -> None:
    """오류 계층과 period 보존 계약."""
    from dartlab.gather.dart import allFilingsHf as mod

    err = mod.AllFilingsHfDownloadError("boom", period="20260527")
    assert isinstance(err, mod.AllFilingsHfError)
    assert err.period == "20260527"

    up = mod.AllFilingsHfUploadError("partial", uploadedFiles=3, totalFiles=5)
    assert up.uploadedFiles == 3 and up.totalFiles == 5 and up.period is None

    assert mod.HfFallbackStatus.LOCAL.value == "local"


def test_maybe_resync_marker_ttl_and_memo(monkeypatch, tmp_path) -> None:
    """마커 부재 시 1회 재동기화 + 마커 생성. 신선한 마커는 재호출을 차단한다."""
    from dartlab.gather.dart import allFilingsHf as mod

    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)
    monkeypatch.setattr(mod, "_resyncCheckedAt", {}, raising=False)

    calls: list[str | None] = []

    def fakeEnsure(period=None, *, refresh=False):
        assert refresh is True
        calls.append(period)

    mod._maybeResyncFromHf("20260527", ensureFromHf=fakeEnsure, allFilingsDir=lambda: tmp_path)
    assert calls == ["20260527"]
    assert (tmp_path / ".hfSynced_20260527").exists()

    # memo 를 비워도 신선한 마커 TTL 이 막는다
    monkeypatch.setattr(mod, "_resyncCheckedAt", {}, raising=False)
    mod._maybeResyncFromHf("20260527", ensureFromHf=fakeEnsure, allFilingsDir=lambda: tmp_path)
    assert calls == ["20260527"]


def test_maybe_resync_failure_keeps_marker_absent(monkeypatch, tmp_path) -> None:
    """재동기화 실패는 예외 없이 로컬 유지 + 마커 미생성 (다음 TTL 재시도)."""
    from dartlab.gather.dart import allFilingsHf as mod

    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)
    monkeypatch.setattr(mod, "_resyncCheckedAt", {}, raising=False)

    def failEnsure(period=None, *, refresh=False):
        raise OSError("network down")

    mod._maybeResyncFromHf(None, ensureFromHf=failEnsure, allFilingsDir=lambda: tmp_path)
    assert not (tmp_path / ".hfSynced__ALL_").exists()


def test_maybe_resync_env_switches_disable(monkeypatch, tmp_path) -> None:
    """DARTLAB_NO_HF_DOWNLOAD·DARTLAB_NO_REFRESH 는 재동기화를 차단한다."""
    from dartlab.gather.dart import allFilingsHf as mod

    def trap(*_a, **_k):
        raise AssertionError("resync must be disabled by env")

    monkeypatch.setattr(mod, "_resyncCheckedAt", {}, raising=False)
    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    mod._maybeResyncFromHf(None, ensureFromHf=trap, allFilingsDir=lambda: tmp_path)

    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.setenv("DARTLAB_NO_REFRESH", "1")
    monkeypatch.setattr(mod, "_resyncCheckedAt", {}, raising=False)
    mod._maybeResyncFromHf(None, ensureFromHf=trap, allFilingsDir=lambda: tmp_path)
