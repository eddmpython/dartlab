"""Search publish script contract tests (월간 main + 일간 누적 delta).

단일 빌드 스크립트 ``buildSearchMain.py`` + 단일 워크플로 ``searchIndexBuild.yml`` 계약을 박제한다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_search_main_publish_includes_manifest() -> None:
    text = Path(".github/scripts/search/buildSearchMain.py").read_text(encoding="utf-8")
    assert "writeIndexManifest(outDir" in text
    assert '"manifest.json"' in text
    assert "source_manifest_set.json" in text
    assert "DARTLAB_SEARCH_SOURCE_MANIFEST_SET" in text
    assert "publishContentIndexFiles" in text
    # sidecar SSOT + hash 기반 변경 artifact 업로드.
    assert "indexPublishNames(outDir)" in text
    assert "_changedPublishNames" in text
    assert "obsoleteCurrentFiles" not in text
    assert "DARTLAB_SEARCH_MAIN_MODE" in text
    assert "DARTLAB_SEARCH_MAIN_ONLY" in text
    assert 'mainOnly == "lite"' in text
    assert "prepareEntityGraphCatalogArtifact" in text
    assert "rebuildMainFromCatalog" in text
    assert "[lite] HF_TOKEN 없음" in text


def test_search_main_publish_uses_no_change_short_circuit_and_per_source_guard() -> None:
    text = Path(".github/scripts/search/buildSearchMain.py").read_text(encoding="utf-8")
    assert "_isNoChange" in text
    assert "_publishNoChangeManifest" in text
    assert "rebuildDeltaFromCatalog" in text
    assert "main_catalog_snapshot.parquet" in text
    assert "_perSourceGuard" in text
    assert "previous_manifest.json" in text
    assert "buildSearchMain.noChange" in text
    assert "DARTLAB_SEARCH_PREVIOUS_CATALOG" in text


def test_push_content_index_uses_publish_names_ssot() -> None:
    text = Path("src/dartlab/providers/dart/search/fieldIndexRebuild.py").read_text(encoding="utf-8")
    # publish 파일 SSOT = indexPublishNames(_segmentFiles + _INDEX_COMMON_FILES). catalog_snapshot 동반 publish.
    assert "names = indexPublishNames(outDir)" in text
    assert '"catalog_snapshot.parquet"' in text


def test_search_main_lite_catalog_filter_uses_date() -> None:
    import importlib.util

    import polars as pl

    path = Path(".github/scripts/search/buildSearchMain.py")
    spec = importlib.util.spec_from_file_location("buildSearchMainForTest", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    catalog = pl.DataFrame(
        [
            {"docKey": "old", "date": "20240101"},
            {"docKey": "recent", "date": "20250101"},
            {"docKey": "dash", "date": "2025-03-01"},
        ]
    )
    filtered = module._filterLiteCatalogRows(catalog, "20250101")

    assert filtered["docKey"].to_list() == ["recent", "dash"]


def test_per_source_guard_blocks_partial_pull() -> None:
    import importlib.util

    path = Path(".github/scripts/search/buildSearchMain.py")
    spec = importlib.util.spec_from_file_location("buildSearchMainGuardTest", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 한 소스(news) 통째 누락 → 총량은 통과해도 per-source 가드가 잡는다.
    healthy = {"allFilings": 165000, "panel": 98000, "edgar-panel": 56000, "news": 103000}
    assert module._perSourceGuard(healthy) is None
    missingNews = {"allFilings": 165000, "panel": 98000, "edgar-panel": 56000}
    err = module._perSourceGuard(missingNews)
    assert err is not None and "news" in err


def test_search_publish_helper_uses_staging_and_manifest_pointer() -> None:
    text = Path("src/dartlab/providers/dart/search/publishIndex.py").read_text(encoding="utf-8")
    assert "_staging" in text
    assert "MANIFEST_NAME" in text
    assert "orderedPublishFiles" in text
    assert "currentPrefix" in text
    assert "manifestPointer" in text
    assert "fileSources" in text
    assert "preflightContentIndexPublish" in text
    assert "contentIndex publish selfcheck failed" in text
    assert "create_commit" in text
    assert "CommitOperationAdd" in text


def test_remote_evidence_asserts_delta_manifest_consistency() -> None:
    text = Path(".github/scripts/search/checkSearchRemoteEvidence.py").read_text(encoding="utf-8")
    assert "deltaFileSources" in text
    assert "missingDeltaFiles" in text
    assert "staleDeltaFileSource" in text
    assert "contentIndexDeltaInconsistent" in text


def test_pull_search_current_index_script_exists() -> None:
    text = Path(".github/scripts/search/pullSearchCurrentIndex.py").read_text(encoding="utf-8")
    assert "fileSources" in text
    assert "previous_manifest.json" in text
    assert "requiredFiles" in text


def test_promote_search_candidate_script_exists() -> None:
    text = Path(".github/scripts/search/promoteSearchCandidate.py").read_text(encoding="utf-8")
    assert "promoteCandidateManifest" in text
    assert "--candidate-manifest-path" in text
    assert "--fail-on-error" in text


def test_search_proof_bundle_script_exists() -> None:
    text = Path(".github/scripts/search/buildSearchProofBundle.py").read_text(encoding="utf-8")
    assert "searchProofBundle.json" in text
    assert "evaluateSearchProductizationStatus.py" in text
    assert "missingEvidence" in text


def test_search_replacement_evidence_script_exists() -> None:
    text = Path(".github/scripts/search/buildSearchReplacementEvidence.py").read_text(encoding="utf-8")
    assert "buildReplacementEvidence" in text
    assert "defaultBuildMode" in text
    assert "scheduledBuildMode" in text
    assert "legacyFallbackOperatorOnly" in text
    assert "failClosedPublish" in text
    assert "activeManifestId" in text
    assert "previousManifestId" in text
    # compact-only — 단일 searchIndexBuild 워크플로 기준(옛 main/delta 2 파일 분기 제거).
    assert "searchIndexBuild.yml" in text


def test_buildsearchdelta_script_is_retired() -> None:
    """delta 세그먼트 폐기 — buildSearchDelta.py 는 삭제됐다."""
    assert not Path(".github/scripts/search/buildSearchDelta.py").exists()


def test_search_index_delta_workflow_is_retired() -> None:
    """delta·main 2 워크플로 fold — searchIndexDelta.yml / searchIndexMain.yml 삭제, build 단일."""
    assert not Path(".github/workflows/searchIndexDelta.yml").exists()
    assert not Path(".github/workflows/searchIndexMain.yml").exists()
    assert Path(".github/workflows/searchIndexBuild.yml").exists()


def test_search_main_script_catalog_build_subprocess(tmp_path) -> None:
    import polars as pl

    curr = tmp_path / "curr.parquet"
    manifest = tmp_path / "source.json"
    dataDir = tmp_path / "data"
    pl.DataFrame([{"source": "allFilings", "rcept_no": "A", "text": "main 유상증자"}]).write_parquet(curr)
    manifest.write_text(
        json.dumps(
            {
                "source": "allFilings",
                "sourceVersion": "v1",
                "schemaVersion": "2026-06",
                "snapshotScope": "full",
                "dataAsOf": "20260615",
                "builtAt": "2026-06-15T00:00:00",
                "files": [{"path": "x.parquet", "rowCount": 1}],
                "totalRows": 1,
                "changedRows": 1,
                "deletedRows": 0,
                "producer": "test",
            }
        ),
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "HF_TOKEN": "",
        "DARTLAB_DATA_DIR": str(dataDir),
        "DARTLAB_SEARCH_MAIN_MODE": "catalog",
        "DARTLAB_SEARCH_CURRENT_CATALOG": str(curr),
        "DARTLAB_SEARCH_SOURCE_MANIFESTS": str(manifest),
        "DARTLAB_SEARCH_EXPECTED_SOURCES": "allFilings",
        "DARTLAB_SEARCH_MIN_DOCS": "1",
        "DARTLAB_SEARCH_MIN_DOCS_BY_SOURCE": "{}",  # per-source 가드 비활성(합성 1 doc)
    }
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", ".github/scripts/search/buildSearchMain.py"],
        cwd=Path.cwd(),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    outDir = dataDir / "dart" / "contentIndex"
    assert (outDir / "main.postings.bin").exists()  # sidecar = SSOT
    assert (outDir / "manifest.json").exists()
    assert (outDir / "catalog_snapshot.parquet").exists()
    manifestData = json.loads((outDir / "manifest.json").read_text(encoding="utf-8"))
    assert "catalog_snapshot.parquet" in manifestData["requiredFiles"]
    assert "catalog_snapshot.parquet" in manifestData["fileHashes"]
    assert manifestData["hasDelta"] is False
    assert not any(str(n).startswith("delta") for n in manifestData["requiredFiles"])


def test_search_main_script_no_change_repoints_manifest(tmp_path) -> None:
    """previous==current catalog + 이전 manifest clean → 재빌드 없이 manifest pointer 만 re-point."""
    import polars as pl

    catalog = tmp_path / "catalog.parquet"
    manifest = tmp_path / "source.json"
    dataDir = tmp_path / "data"
    row = {"source": "allFilings", "rcept_no": "A", "text": "투자설명서 케이티스카이라이프"}
    pl.DataFrame([row]).write_parquet(catalog)
    manifest.write_text(
        json.dumps(
            {
                "source": "allFilings",
                "sourceVersion": "v1",
                "schemaVersion": "2026-06",
                "snapshotScope": "full",
                "dataAsOf": "20260617",
                "builtAt": "2026-06-17T00:00:00",
                "files": [{"path": "x.parquet", "rowCount": 1}],
                "totalRows": 1,
                "changedRows": 0,
                "deletedRows": 0,
                "producer": "test",
            }
        ),
        encoding="utf-8",
    )
    base = {
        **os.environ,
        "HF_TOKEN": "",
        "DARTLAB_DATA_DIR": str(dataDir),
        "DARTLAB_SEARCH_MAIN_MODE": "catalog",
        "DARTLAB_SEARCH_SOURCE_MANIFESTS": str(manifest),
        "DARTLAB_SEARCH_EXPECTED_SOURCES": "allFilings",
        "DARTLAB_SEARCH_MIN_DOCS": "1",
        "DARTLAB_SEARCH_MIN_DOCS_BY_SOURCE": "{}",
    }
    # 1차 — 풀 빌드(previous 없음).
    subprocess.run(
        [sys.executable, "-X", "utf8", ".github/scripts/search/buildSearchMain.py"],
        cwd=Path.cwd(),
        env={**base, "DARTLAB_SEARCH_CURRENT_CATALOG": str(catalog)},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=True,
    )
    outDir = dataDir / "dart" / "contentIndex"
    # pull current index 가 previous_manifest 를 내려놓는 것을 모사(clean — delta 키 0).
    shutil.copyfile(outDir / "manifest.json", outDir / "previous_manifest.json")

    # 2차 — previous==current → 변화 0 + clean manifest → no-change re-point.
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", ".github/scripts/search/buildSearchMain.py"],
        cwd=Path.cwd(),
        env={
            **base,
            "DARTLAB_SEARCH_PREVIOUS_CATALOG": str(catalog),
            "DARTLAB_SEARCH_CURRENT_CATALOG": str(catalog),
        },
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    manifestData = json.loads((outDir / "manifest.json").read_text(encoding="utf-8"))
    assert manifestData["buildCommand"] == "buildSearchMain.noChange"


def test_search_catalog_script_exists() -> None:
    text = Path(".github/scripts/search/buildSearchCatalog.py").read_text(encoding="utf-8")
    assert "writeSourceCatalogArtifacts" in text
    assert "--snapshot-scope" in text
    assert "--min-files" in text
    assert "--min-rows" in text
    assert "--min-catalog-rows" in text
    assert "--compare-remote-manifest" in text
    assert "--require-previous-manifest" in text
    assert "create_commit" in text
    assert "CommitOperationAdd" in text


def test_source_workflows_build_search_catalog_artifacts() -> None:
    original = Path(".github/workflows/originalSync.yml").read_text(encoding="utf-8")
    backfill = Path(".github/workflows/allFilingsBackfill.yml").read_text(encoding="utf-8")
    news = Path(".github/workflows/newsArchiveSync.yml").read_text(encoding="utf-8")
    edgar = Path(".github/workflows/edgarSync.yml").read_text(encoding="utf-8")
    combined = "\n".join([original, backfill, news, edgar])
    for source in ("dartPanel", "allFilings", "edgarPanel", "newsPublic"):
        assert f"--source {source}" in combined
        assert f"search-catalog-{source}" in combined
        assert f"data/dart/searchCatalog/{source}/**" in combined
    assert "--upload" in combined
    assert "--compare-remote-manifest" in combined
    assert "--require-previous-manifest" in combined
    assert "search_catalog_bootstrap" in combined
    assert "SEARCH_CATALOG_BOOTSTRAP" in combined
    assert "extra+=(--require-previous-manifest)" in combined
    assert "--min-files 300" in combined
    assert "--min-rows 150000" in combined
    assert "--min-catalog-rows 150000" in combined
    assert "--min-files 2400" in combined
    assert "--min-rows 90000" in combined
    assert "--min-catalog-rows 90000" in combined
    assert "--min-files 2000" in combined
    assert "--min-rows 50000" in combined
    assert "--min-catalog-rows 50000" in combined
    assert "--min-rows 100" in combined
    assert "actions/upload-artifact" in combined
    assert "if-no-files-found: ignore" in combined


def test_allfilings_backfill_is_decoupled_from_daily_original_sync() -> None:
    original = Path(".github/workflows/originalSync.yml").read_text(encoding="utf-8")
    backfill = Path(".github/workflows/allFilingsBackfill.yml").read_text(encoding="utf-8")
    assert "name: AllFilings Backfill" in backfill
    assert "cron: '30 5 * * *'" in backfill
    assert "timeout-minutes: 120" in backfill
    assert "timeout-minutes: 65" in backfill
    assert "비정기공시 코드 버킷 증분 갱신" in backfill
    assert "DARTLAB_HF_RETRY_ATTEMPTS: '3'" in original
    assert "DARTLAB_HF_RETRY_ATTEMPTS: '3'" in backfill
    assert "DARTLAB_HF_RETRY_MAX_SINGLE_WAIT_SECONDS: '120'" in original
    assert "DARTLAB_HF_RETRY_MAX_SINGLE_WAIT_SECONDS: '120'" in backfill
    assert "--producer allFilingsBackfill.allfilings-backfill" in backfill
    assert "name: search-catalog-allFilings-backfill-${{ github.run_id }}" in backfill
    assert "github.event.inputs.jobs == 'allfilings-backfill'" in original


def test_search_index_build_workflow_is_single_folded_pipeline() -> None:
    """단일 searchIndexBuild - 일간 누적 delta + 월간 main + workflow_run."""
    text = Path(".github/workflows/searchIndexBuild.yml").read_text(encoding="utf-8")
    # 트리거 fold — 일간 cron + 월간 cron + 4 source workflow_run.
    assert "name: Search Index Build" in text
    assert "cron: '0 19 * * *'" in text
    assert "cron: '0 20 1 * *'" in text
    assert "workflow_run" in text
    assert "Original SSOT Sync" in text
    assert "AllFilings Backfill" in text
    assert "News Archive Sync" in text
    assert "EDGAR Data Sync (Bulk)" in text
    assert "github.event.workflow_run.conclusion == 'success'" in text
    # build_mode catalog/legacy + force_full + 증분 diff(previous catalog).
    assert "build_mode" in text
    assert "default: catalog" in text
    assert "options:\n          - catalog\n          - legacy" in text
    assert "${{ inputs.build_mode || 'catalog' }}" in text
    assert "FORCE_FULL" in text
    assert "PRODUCTIZATION_GATE" in text
    assert "pullSearchCurrentIndex.py" in text
    assert "prepareSearchDeltaInputs.py" in text
    assert "data/dart/contentIndex/catalog_snapshot.parquet" in text
    assert "main_catalog_snapshot.parquet" in text
    assert "Pull existing lite content index from HF" in text
    # 단일 build 스크립트 + clean publish 게이트 + per-source 가드 동반.
    assert "buildSearchMain.py" in text
    assert "buildSearchDelta.py" not in text
    assert 'DARTLAB_SEARCH_PROMOTE_CURRENT: "0"' in text
    assert "verifySearchHfRoundTrip.py" in text
    assert '--manifest-repo-path "$DARTLAB_SEARCH_FULL_CANDIDATE_MANIFEST"' in text
    assert '--manifest-repo-path "$DARTLAB_SEARCH_LITE_CANDIDATE_MANIFEST"' in text
    assert "promoteSearchCandidate.py" in text
    assert "evaluateSearchResultContract.py" in text
    assert "evaluateSearchCanary.py" in text
    assert "runSearchQualityDrill.py" in text
    assert "checkSearchRemoteEvidence.py" in text
    assert "--fail-on-missing" in text
    assert "evaluateSearchGold.py" in text
    assert "evaluateSearchProductizationStatus.py" in text
    assert "buildSearchProofBundle.py" in text
    assert "buildSearchReplacementEvidence.py" in text
    assert "evaluateSearchCutover.py" in text
    assert "--replacement-evidence" in text
    assert "--workflow .github/workflows/searchIndexBuild.yml" in text
    assert "--fail-on-incomplete" in text
    assert "--fail-on-default-not-ready" in text
    assert "--fail-on-ops-not-ready" in text
    assert "--fail-on-release-not-ready" in text
    assert 'blockers":["missingProofBundle"]' in text
    assert "actions/upload-artifact" in text
    assert "buildSearchDelta.py" not in text


def test_search_index_build_workflow_keeps_legacy_bootstrap_operator_only() -> None:
    """build_mode=legacy 일 때만 raw HF 풀 + canonical catalog 부트스트랩(disaster recovery)."""
    text = Path(".github/workflows/searchIndexBuild.yml").read_text(encoding="utf-8")
    assert "inputs.build_mode == 'legacy'" in text
    assert "for attempt in $(seq 1 12)" in text
    assert "sleep 310" in text
    assert "searchIndexBuild.full-pull" in text
    for source in ("allFilings", "dartPanel", "edgarPanel", "newsPublic"):
        assert f"--source {source}" in text
    assert "dart/allFilings/*" in text
    assert "dart/panel/**" in text
    assert "edgar/panel/**" in text
    assert "news/public/rss_enriched/**" in text
