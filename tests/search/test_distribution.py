"""검색 인덱스 배포(lazy pull) 단위 테스트 — ensureContentIndex offline/local 가드 + indexInfo.

pip 사용자가 dartlab.search() 첫 호출 시 인덱스를 HF lazy pull 하는 배선 검증. 네트워크 미사용
(로컬 존재 / DARTLAB_NO_HF_DOWNLOAD 경로만 — 둘 다 snapshot_download 이전에 반환).
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def _patch(monkeypatch, tmp_path):
    from dartlab.providers.dart.search import fieldIndex, fieldIndexRebuild

    monkeypatch.setattr(fieldIndex, "_contentIndexDir", lambda: tmp_path)
    monkeypatch.setattr(fieldIndexRebuild, "_HF_CONTENTINDEX_ATTEMPTED", False, raising=False)
    return fieldIndexRebuild


def test_ensure_content_index_local_noop(tmp_path, monkeypatch):
    """로컬 main.postings.bin(sidecar SSOT) 존재 → 다운로드 시도 없이 즉시 반환(no-op)."""
    (tmp_path / "main.postings.bin").write_bytes(b"\x00")
    fir = _patch(monkeypatch, tmp_path)
    assert fir.ensureContentIndex() is True  # 예외 없이 즉시 반환(로컬 우선)


def test_ensure_content_index_offline_skip(tmp_path, monkeypatch):
    """DARTLAB_NO_HF_DOWNLOAD=1 → 빈 인덱스라도 다운로드 skip(graceful)."""
    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    fir = _patch(monkeypatch, tmp_path)
    assert fir.ensureContentIndex() is False  # 네트워크 미접근, 예외 없음
    assert not (tmp_path / "main.postings.bin").exists()


def test_index_info_absent(tmp_path, monkeypatch):
    """인덱스 부재 → available=False."""
    fir = _patch(monkeypatch, tmp_path)
    info = fir.indexInfo()
    assert info["available"] is False
    assert info["nDocs"] == 0


def test_index_info_present(tmp_path, monkeypatch):
    """main_info.json + router.json 존재 → available·dataAsOf·hasRouter."""
    fir = _patch(monkeypatch, tmp_path)
    (tmp_path / "main_info.json").write_text(
        json.dumps({"nDocs": 17438, "avgDocLength": 120.0, "builtAt": "2026-06-02T05:00:00"}), encoding="utf-8"
    )
    # 이벤트 비어있지 않은 router.json — hasRouter 는 *존재* 가 아니라 *비어있지 않음* 을 본다(degraded 거짓보고 차단).
    (tmp_path / "router.json").write_text(
        '{"v": 1, "events": {"dividend": {"route": {"배당": 1.0}, "canon": ["배당금"]}}}', encoding="utf-8"
    )
    info = fir.indexInfo()
    assert info["available"] is True
    assert info["dataAsOf"] == "2026-06-02T05:00:00"
    assert info["nDocs"] == 17438
    assert info["hasRouter"] is True
    assert info["hasDelta"] is False


def test_prefetch_indexInfo_exported():
    """prefetch·indexInfo 가 search 패키지 public."""
    from dartlab.providers.dart.search import indexInfo, prefetch

    assert callable(prefetch)
    assert callable(indexInfo)
