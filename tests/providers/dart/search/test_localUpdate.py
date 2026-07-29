"""providers/dart/search/localUpdate.py mirror tests."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.dart.search.localUpdate as mod

    assert mod is not None


# compact-only(P2): postings SSOT = sidecar. loadShardedSegment 가 읽는 engine-load 파일 집합.
_REQUIRED = [
    "main.postings.bin",
    "main.terms.bin",
    "main.docLengths.bin",
    "main_stems.json",
    "main_meta.parquet",
    "main_info.json",
]


def _writeRealSegment(outDir):
    import polars as pl

    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar

    rows = [
        {
            "section_content": "유상증자 자금조달",
            "rcept_no": "20260615000001",
            "section_order": 0,
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "rcept_dt": "20260615",
            "report_nm": "주요사항보고서",
            "section_title": "",
            "source": "allFilings",
        }
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    assert isinstance(meta, pl.DataFrame)
    saveSegmentWithSidecar(idx, meta, "main", outDir)


def _writeManifest(outDir):
    from dartlab.providers.dart.search.fieldIndex import INDEX_SCHEMA_VERSION

    (outDir / "manifest.json").write_text(
        json.dumps(
            {
                "artifactVersion": 1,
                "schemaVersion": INDEX_SCHEMA_VERSION,
                "builtAt": "2026-06-15T00:00:00",
                "sourceDataAsOf": {"allFilings": "20260615"},
                "nDocsBySource": {"allFilings": 1},
                "requiredFiles": _REQUIRED,
            }
        ),
        encoding="utf-8",
    )


def _writeManifestWithCanary(outDir, queries):
    from dartlab.providers.dart.search.fieldIndex import INDEX_SCHEMA_VERSION

    (outDir / "manifest.json").write_text(
        json.dumps(
            {
                "artifactVersion": 1,
                "schemaVersion": INDEX_SCHEMA_VERSION,
                "builtAt": "2026-06-15T00:00:00",
                "sourceDataAsOf": {"allFilings": "20260615"},
                "nDocsBySource": {"allFilings": 1},
                "requiredFiles": _REQUIRED,
                "canaryQueries": queries,
            }
        ),
        encoding="utf-8",
    )


def _writeManifestWithSourceCanary(outDir, rows):
    from dartlab.providers.dart.search.fieldIndex import INDEX_SCHEMA_VERSION

    (outDir / "manifest.json").write_text(
        json.dumps(
            {
                "artifactVersion": 1,
                "schemaVersion": INDEX_SCHEMA_VERSION,
                "builtAt": "2026-06-15T00:00:00",
                "sourceDataAsOf": {"allFilings": "20260615"},
                "nDocsBySource": {"allFilings": 1},
                "requiredFiles": _REQUIRED,
                "sourceCanaryPack": rows,
            }
        ),
        encoding="utf-8",
    )


def test_activate_staged_index_writes_active_pointer(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)
    _writeManifest(staged)

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is True
    assert resolveActiveIndexDir(base) == staged


def test_activate_staged_index_rejects_missing_manifest(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is False
    assert "missing:manifest" in result["errors"]
    assert resolveActiveIndexDir(base) is None


def test_download_and_activate_content_index_uses_staging(tmp_path):
    from dartlab.providers.dart.search.localUpdate import downloadAndActivateContentIndex, resolveActiveIndexDir

    remote = tmp_path / "remote"
    remoteIndex = remote / "dart" / "contentIndex" / "lite"
    remoteIndex.mkdir(parents=True)
    _writeRealSegment(remoteIndex)
    _writeManifest(remoteIndex)

    def fakeDownload(repoPath, downloadRoot):
        src = remote / repoPath
        assert src.exists()
        return src

    base = tmp_path / "contentIndex"
    result = downloadAndActivateContentIndex(tier="lite", baseDir=base, downloadFile=fakeDownload)
    assert result["activated"] is True
    active = resolveActiveIndexDir(base)
    assert active is not None
    assert active.parent.name == "_staging"
    assert active.name.startswith("lite-")


def test_download_and_activate_uses_manifest_file_sources(tmp_path):
    from dartlab.providers.dart.search.localUpdate import downloadAndActivateContentIndex, resolveActiveIndexDir

    remote = tmp_path / "remote"
    current = remote / "dart" / "contentIndex" / "lite"
    stagedRemote = current / "_staging" / "run1"
    stagedRemote.mkdir(parents=True)
    _writeRealSegment(stagedRemote)
    _writeManifest(stagedRemote)
    manifest = json.loads((stagedRemote / "manifest.json").read_text(encoding="utf-8"))
    manifest["fileSources"] = {name: f"dart/contentIndex/lite/_staging/run1/{name}" for name in _REQUIRED}
    (current / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def fakeDownload(repoPath, downloadRoot):
        src = remote / repoPath
        assert src.exists()
        return src

    base = tmp_path / "contentIndex"
    result = downloadAndActivateContentIndex(tier="lite", baseDir=base, downloadFile=fakeDownload)
    assert result["activated"] is True
    active = resolveActiveIndexDir(base)
    assert active is not None
    assert (active / "main.postings.bin").exists()


def test_activate_staged_index_runs_manifest_canary_queries(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)
    _writeManifestWithCanary(staged, ["유상증자"])

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is True


def test_activate_staged_index_rejects_failed_canary_query(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)
    _writeManifestWithCanary(staged, ["없는단어"])

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is False
    assert "canaryMiss:없는단어" in result["errors"]
    assert resolveActiveIndexDir(base) is None


def test_activate_staged_index_runs_source_canary_pack(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)
    _writeManifestWithSourceCanary(
        staged,
        [
            {
                "query": "유상증자",
                "target": "filing",
                "expectedSource": "allFilings",
                "expectedSourceRef": "20260615000001",
            },
            {"query": "없는단어", "target": "noAnswer", "expectedAnswerable": False},
        ],
    )

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is True


def test_activate_staged_index_rejects_source_canary_pack_miss(tmp_path):
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeRealSegment(staged)
    _writeManifestWithSourceCanary(
        staged,
        [
            {
                "query": "유상증자",
                "target": "news",
                "expectedSource": "news",
                "expectedSourceRef": "news:missing",
            }
        ],
    )

    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is False
    assert "sourceCanary:유상증자:sourceMiss" in result["errors"]
    assert "sourceCanary:유상증자:sourceRefMiss" in result["errors"]
    assert resolveActiveIndexDir(base) is None


def _writeTwoDocSegment(outDir):
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar

    rows = [
        {
            "section_content": "유상증자 자금조달",
            "rcept_no": "AAA00000001",
            "section_order": 0,
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "rcept_dt": "20260615",
            "report_nm": "주요사항보고서",
            "section_title": "",
            "source": "allFilings",
        },
        {
            "section_content": "현금배당 결정",
            "rcept_no": "BBB00000002",
            "section_order": 0,
            "corp_code": "00164742",
            "corp_name": "현대차",
            "stock_code": "005380",
            "rcept_dt": "20260616",
            "report_nm": "현금ㆍ현물배당결정",
            "section_title": "",
            "source": "allFilings",
        },
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    saveSegmentWithSidecar(idx, meta, "main", outDir)


def test_source_canary_ref_is_deterministic_not_ranking(tmp_path):
    # 인용 무결성은 BM25 랭킹이 아니라 meta 직독 라운드트립(존재+docLengths>0)으로 본다.
    # 질의 '유상증자' 는 doc0(AAA)만 매치 → source-lane(allFilings) 충족하나, 기대 ref 는 doc1(BBB):
    # 옛 랭킹 멤버십이면 BBB 가 top-K 에 없어 sourceRefMiss(거짓 RED)였다. 결정론 검증은 BBB 가 meta 에
    # 존재+색인이므로 PASS — bigram 토크나이저서 보일러플레이트 self-retrieval 불가가 게이트를 막지 않음.
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeTwoDocSegment(staged)
    _writeManifestWithSourceCanary(
        staged,
        [
            {
                "query": "유상증자",
                "target": "filing",
                "expectedSource": "allFilings",
                "expectedSourceRef": "BBB00000002",
                "topK": 1,
            }
        ],
    )
    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is True
    assert resolveActiveIndexDir(base) == staged


def test_source_canary_ref_absent_still_rejected(tmp_path):
    # 결정론 검증이 무결성을 hollow 하게 만들지 않음 — ref 가 meta 에 아예 없으면(드리프트·doc 누락) RED.
    from dartlab.providers.dart.search.localUpdate import activateStagedIndex, resolveActiveIndexDir

    base = tmp_path / "contentIndex"
    staged = base / "_staging" / "run1"
    staged.mkdir(parents=True)
    _writeTwoDocSegment(staged)
    _writeManifestWithSourceCanary(
        staged,
        [
            {
                "query": "유상증자",
                "target": "filing",
                "expectedSource": "allFilings",
                "expectedSourceRef": "ZZZ00000099",
                "topK": 1,
            }
        ],
    )
    result = activateStagedIndex(staged, baseDir=base)
    assert result["activated"] is False
    assert "sourceCanary:유상증자:sourceRefMiss" in result["errors"]
    assert resolveActiveIndexDir(base) is None


def test_download_and_activate_preserves_active_on_missing_file(tmp_path):
    from dartlab.providers.dart.search.localUpdate import (
        activateStagedIndex,
        downloadAndActivateContentIndex,
        resolveActiveIndexDir,
    )

    base = tmp_path / "contentIndex"
    existing = base / "_staging" / "old"
    existing.mkdir(parents=True)
    _writeRealSegment(existing)
    _writeManifest(existing)
    assert activateStagedIndex(existing, baseDir=base)["activated"] is True

    remote = tmp_path / "remote"
    remoteIndex = remote / "dart" / "contentIndex" / "lite"
    remoteIndex.mkdir(parents=True)
    _writeRealSegment(remoteIndex)
    _writeManifest(remoteIndex)
    (remoteIndex / "main_stems.json").unlink()

    def fakeDownload(repoPath, downloadRoot):
        src = remote / repoPath
        if not src.exists():
            raise FileNotFoundError(repoPath)
        return src

    result = downloadAndActivateContentIndex(tier="lite", baseDir=base, downloadFile=fakeDownload)
    assert result["activated"] is False
    assert result["activeDir"] == str(existing)
    assert resolveActiveIndexDir(base) == existing


def test_download_and_activate_skips_same_or_older_manifest(tmp_path):
    from dartlab.providers.dart.search.localUpdate import (
        activateStagedIndex,
        downloadAndActivateContentIndex,
        resolveActiveIndexDir,
    )

    base = tmp_path / "contentIndex"
    existing = base / "_staging" / "old"
    existing.mkdir(parents=True)
    _writeRealSegment(existing)
    _writeManifest(existing)
    assert activateStagedIndex(existing, baseDir=base)["activated"] is True

    remote = tmp_path / "remote"
    remoteIndex = remote / "dart" / "contentIndex" / "lite"
    remoteIndex.mkdir(parents=True)
    _writeRealSegment(remoteIndex)
    _writeManifest(remoteIndex)

    def fakeDownload(repoPath, downloadRoot):
        src = remote / repoPath
        assert src.exists()
        return src

    result = downloadAndActivateContentIndex(tier="lite", baseDir=base, downloadFile=fakeDownload)
    assert result["activated"] is False
    assert result["skipped"] == "notNewer"
    assert resolveActiveIndexDir(base) == existing


def test_rollback_active_index_restores_previous_pointer(tmp_path):
    from dartlab.providers.dart.search.localUpdate import (
        activateStagedIndex,
        resolveActiveIndexDir,
        rollbackActiveIndex,
    )

    base = tmp_path / "contentIndex"
    old = base / "_staging" / "old"
    new = base / "_staging" / "new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    _writeRealSegment(old)
    _writeManifest(old)
    _writeRealSegment(new)
    _writeManifest(new)

    assert activateStagedIndex(old, baseDir=base)["activated"] is True
    second = activateStagedIndex(new, baseDir=base)
    assert second["activated"] is True
    assert second["previousActiveDir"] == "_staging/old"
    assert resolveActiveIndexDir(base) == new

    rollback = rollbackActiveIndex(baseDir=base)

    assert rollback["rolledBack"] is True
    assert resolveActiveIndexDir(base) == old


def test_rollback_active_index_preserves_current_when_previous_is_invalid(tmp_path):
    import json

    from dartlab.providers.dart.search.localUpdate import (
        activateStagedIndex,
        resolveActiveIndexDir,
        rollbackActiveIndex,
    )

    base = tmp_path / "contentIndex"
    current = base / "_staging" / "current"
    current.mkdir(parents=True)
    _writeRealSegment(current)
    _writeManifest(current)
    assert activateStagedIndex(current, baseDir=base)["activated"] is True
    (base / "active.json").write_text(
        json.dumps({"activeDir": "_staging/current", "previousActiveDir": "_staging/missing"}),
        encoding="utf-8",
    )

    rollback = rollbackActiveIndex(baseDir=base)

    assert rollback["rolledBack"] is False
    assert "missing:manifest" in rollback["errors"]
    assert resolveActiveIndexDir(base) == current


def test_should_activate_remote_manifest_compares_identity() -> None:
    from dartlab.providers.dart.search.localUpdate import shouldActivateRemoteManifest

    local = {"artifactVersion": 1, "builtAt": "2026-06-15T00:00:00", "fileHashes": {"a": "1"}}
    same = {"artifactVersion": 1, "builtAt": "2026-06-15T00:00:00", "fileHashes": {"a": "1"}}
    newer = {"artifactVersion": 1, "builtAt": "2026-06-16T00:00:00", "fileHashes": {"a": "2"}}
    older = {"artifactVersion": 1, "builtAt": "2026-06-14T00:00:00", "fileHashes": {"a": "2"}}
    assert shouldActivateRemoteManifest(same, local) is False
    assert shouldActivateRemoteManifest(newer, local) is True
    assert shouldActivateRemoteManifest(older, local) is False


def test_ensure_content_index_activates_manifest_download(tmp_path, monkeypatch):
    import dartlab.config as cfg
    from dartlab.providers.dart.search import fieldIndexRebuild

    calls = []
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(fieldIndexRebuild, "_HF_CONTENTINDEX_ATTEMPTED", False, raising=False)

    def fakeDownloadAndActivate(*, tier=None, baseDir=None, **kwargs):
        calls.append((tier, baseDir))
        return {"activated": True, "errors": [], "activeDir": str(baseDir)}

    monkeypatch.setattr(
        "dartlab.providers.dart.search.localUpdate.downloadAndActivateContentIndex",
        fakeDownloadAndActivate,
    )

    assert fieldIndexRebuild.ensureContentIndex(tier="lite") is True
    assert calls


def test_ensure_content_index_failure_is_typed_and_retryable(tmp_path, monkeypatch):
    """원격 실패를 정상 index 부재로 삼키거나 영구 캐시하지 않는다."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.core import hfRetry
    from dartlab.providers.dart.search import fieldIndexRebuild

    calls = 0

    def failSnapshot(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise OSError("network down")

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.setattr(fieldIndexRebuild, "_HF_CONTENTINDEX_ATTEMPTED", False)
    monkeypatch.setattr(
        "dartlab.providers.dart.search.localUpdate.downloadAndActivateContentIndex",
        lambda **_kwargs: {"activated": False, "errors": ["download:missing"]},
    )
    monkeypatch.setattr(huggingface_hub, "snapshot_download", failSnapshot)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    for _ in range(2):
        with pytest.raises(fieldIndexRebuild.ContentIndexFetchError, match="network down") as excInfo:
            fieldIndexRebuild.ensureContentIndex(tier="lite")
        assert isinstance(excInfo.value.__cause__, OSError)

    assert calls == 2
    assert fieldIndexRebuild._HF_CONTENTINDEX_ATTEMPTED is False
