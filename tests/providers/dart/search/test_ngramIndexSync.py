"""mirror smoke — dart/search/ngramIndexSync.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.dart.search.ngramIndexSync as mod

    assert mod is not None


# ---------------------------------------------------------------------------
# freshness 재동기화 (TTL + 마커) — HF 재빌드 catch-up 배선
# ---------------------------------------------------------------------------


def test_stem_refresh_due_gates(monkeypatch, tmp_path):
    """env off 스위치·신선한 마커는 재동기화를 차단하고, 마커 부재는 due 다."""
    from dartlab.providers.dart.search import ngramIndexSync as mod

    monkeypatch.setattr(mod, "_stemResyncCheckedAt", {}, raising=False)
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)

    # 마커 없음 → due
    assert mod._stemRefreshDue(tmp_path) is True

    # 신선한 마커 → due 아님 (memo 리셋 후에도)
    monkeypatch.setattr(mod, "_stemResyncCheckedAt", {}, raising=False)
    mod._touchStemSyncMarker(tmp_path)
    assert mod._stemRefreshDue(tmp_path) is False

    # env off 스위치 → 마커 없어도 차단
    monkeypatch.setattr(mod, "_stemResyncCheckedAt", {}, raising=False)
    (tmp_path / ".hfSyncedAt").unlink()
    monkeypatch.setenv("DARTLAB_NO_REFRESH", "1")
    assert mod._stemRefreshDue(tmp_path) is False


def test_pull_stem_index_refresh_failure_keeps_local(monkeypatch, tmp_path):
    """로컬 인덱스 존재 + TTL 만료 + 원격 실패면 로컬을 유지하고 예외를 내지 않는다."""
    import huggingface_hub

    from dartlab.core import hfRetry
    from dartlab.providers.dart.search import ngramIndex as ngmod
    from dartlab.providers.dart.search import ngramIndexSync as mod

    outDir = tmp_path / "dart" / "stemIndex"
    outDir.mkdir(parents=True)
    (outDir / "stemIndex.npz").write_bytes(b"\x00")

    monkeypatch.setattr(mod, "_stemIndexDir", lambda: outDir)
    monkeypatch.setattr(mod, "_stemResyncCheckedAt", {}, raising=False)
    monkeypatch.setattr(ngmod, "ngramStats", lambda: {"documents": 10, "sizeMb": 1})
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)

    def failSnapshot(*_a, **_k):
        raise OSError("network down")

    monkeypatch.setattr(huggingface_hub, "snapshot_download", failSnapshot)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    assert mod.pullStemIndex() == outDir  # 예외 없이 로컬 유지
    assert not (outDir / ".hfSyncedAt").exists()  # 실패는 마커 미갱신


def test_pull_stem_index_fresh_marker_skips_network(monkeypatch, tmp_path):
    """신선한 마커면 원격 접근 0회 로컬 반환."""
    import huggingface_hub

    from dartlab.providers.dart.search import ngramIndex as ngmod
    from dartlab.providers.dart.search import ngramIndexSync as mod

    outDir = tmp_path / "dart" / "stemIndex"
    outDir.mkdir(parents=True)
    (outDir / "stemIndex.npz").write_bytes(b"\x00")
    mod._touchStemSyncMarker(outDir)

    monkeypatch.setattr(mod, "_stemIndexDir", lambda: outDir)
    monkeypatch.setattr(mod, "_stemResyncCheckedAt", {}, raising=False)
    monkeypatch.setattr(ngmod, "ngramStats", lambda: {"documents": 10, "sizeMb": 1})
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)

    def trap(*_a, **_k):
        raise AssertionError("snapshot_download must not be called within TTL")

    monkeypatch.setattr(huggingface_hub, "snapshot_download", trap)

    assert mod.pullStemIndex() == outDir
