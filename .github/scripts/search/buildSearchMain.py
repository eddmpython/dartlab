"""Search content index 월간 main + 일간 누적 delta 빌드와 HF 업로드.

일·월 단일 워크플로(`searchIndexBuild`)에서 호출한다. 월간에는 main을 압축하고, 일간에는
그 main catalog와 현재 catalog의 누적 차이만 단일 delta로 교체한다. delta fan-out은 항상 1이다.

흐름:
1. previous(이전 current) + current catalog 변화가 0이면 manifest pointer만 갱신한다.
2. 월간 또는 main 기준 snapshot 부재면 source catalog 전체를 main으로 압축한다.
3. 그 외에는 main 기준 누적 changed-set과 tombstone만 delta로 만든다.
3. per-source 하한 가드(allFilings/panel/edgar/news) + 총량 가드 → partial HF pull 회귀 차단.
4. clean publish — `indexPublishNames`(npz·delta 제외=sidecar SSOT), `previousManifestPath` seed 안 함
   → 새 fileSources 에 delta 키 자연 부재(HF pointer main-only flip).
5. lite tier(최근 N개월) 동반 빌드/업로드.

환경:
- HF_TOKEN: HuggingFace 업로드용
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# per-source 하한(runtime source 명) — 2026-06 풀셋 실측(allFilings 165k·panel 98k·edgar 56k·news 103k)의
# ~80%. 총량 350k 만으로는 한 소스(예: news → 319k)가 통째로 누락돼도 통과(silent partial-pull)하므로,
# 소스별 하한으로 partial HF pull 회귀를 개별 차단한다. env(JSON dict)로 재정의 가능.
_DEFAULT_MIN_DOCS_BY_SOURCE: dict[str, int] = {
    "allFilings": 130000,
    "panel": 70000,
    "edgar-panel": 40000,
    "news": 70000,
}


def _catalogInputsFromEnv() -> tuple[str | None, str | None, list[str], list[str]]:
    manifestPaths = [p for p in os.environ.get("DARTLAB_SEARCH_SOURCE_MANIFESTS", "").split(os.pathsep) if p]
    expectedSources = [p.strip() for p in os.environ.get("DARTLAB_SEARCH_EXPECTED_SOURCES", "").split(",") if p.strip()]
    return (
        os.environ.get("DARTLAB_SEARCH_PREVIOUS_CATALOG") or None,
        os.environ.get("DARTLAB_SEARCH_CURRENT_CATALOG") or None,
        manifestPaths,
        expectedSources,
    )


def _isNoChange(previousCatalog: str | None, currentCatalog: str | None) -> bool:
    """previous와 current catalog의 changed-set이 비어 있으면 True."""
    if not (currentCatalog and previousCatalog and Path(previousCatalog).exists()):
        return False
    from dartlab.providers.dart.search.pipeline import _loadCatalog, exportDeltaRowsForContentIndex

    rows = exportDeltaRowsForContentIndex(_loadCatalog(previousCatalog), _loadCatalog(currentCatalog))
    return rows.height == 0


def _publishNoChangeManifest(hfToken: str) -> None:
    """main 재빌드 없이 manifest pointer 만 re-point(이전 fileSources 보존). 빌드 0·fast."""
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir, clearCache
    from dartlab.providers.dart.search.fieldIndexRebuild import writeIndexManifest
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    outDir = _contentIndexDir()
    writeIndexManifest(outDir, tier="full", buildCommand="buildSearchMain.noChange")
    clearCache()
    if not hfToken:
        print("[build] HF_TOKEN 없음 — no-change manifest 로컬 재작성만 수행")
        return
    summary = publishContentIndexFiles(
        token=hfToken,
        indexDir=outDir,
        files=["manifest.json"],
        tier="full",
        previousManifestPath=outDir / "previous_manifest.json",
        promoteCurrent=_promoteCurrent(),
    )
    _writeCandidateEnv(summary)
    print(
        f"  [no-change-manifest] {summary.get('candidateManifestPath', '')} "
        f"-> {summary['currentPrefix']} {summary['publishMode']}"
    )


def _perSourceGuard(nDocsBySource: dict) -> str | None:
    """소스별 하한 검사 — 미달/누락 소스가 있으면 사람용 에러 문자열, 없으면 None.

    한 소스 통째 누락(silent partial-pull)은 총량 가드를 통과할 수 있어 소스별로 개별 차단한다.
    env ``DARTLAB_SEARCH_MIN_DOCS_BY_SOURCE`` (JSON dict, runtime source 명) 로 재정의 가능.
    """
    minimums = dict(_DEFAULT_MIN_DOCS_BY_SOURCE)
    raw = os.environ.get("DARTLAB_SEARCH_MIN_DOCS_BY_SOURCE", "").strip()
    if raw:
        # env 제공 시 *대체*(merge 아님) — 빈 {} 면 per-source 가드 비활성(테스트/특수 운영).
        try:
            override = json.loads(raw)
            if isinstance(override, dict):
                minimums = {str(k): int(v) for k, v in override.items()}
        except (json.JSONDecodeError, ValueError, TypeError):
            print(f"[main] ⚠ DARTLAB_SEARCH_MIN_DOCS_BY_SOURCE 파싱 실패(기본값 사용): {raw!r}")
    counts = {str(k): int(v or 0) for k, v in (nDocsBySource or {}).items()}
    failures = [
        f"{source}={counts.get(source, 0):,}(< {minimum:,})"
        for source, minimum in minimums.items()
        if counts.get(source, 0) < minimum
    ]
    return "소스별 하한 미달: " + ", ".join(failures) if failures else None


def _buildRouterArtifact(tier: str = "full") -> int:
    """events.json 시드 → 결정론 라우터 router.json 을 인덱스 디렉터리에 도출 (scope=auto 확장축).

    빌드는 코퍼스 무관(시드만 입력)·수 ms·bounded(~수 KB). 반환 = 이벤트 수 (0 = 퇴행).
    """
    import json

    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir
    from dartlab.providers.dart.search.router import buildRouterModel

    eventsPath = Path(__file__).resolve().parent / "questionSet" / "events.json"
    events = json.loads(eventsPath.read_text(encoding="utf-8"))["events"]
    model = buildRouterModel(events)
    outDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    (outDir / "router.json").write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
    return len(model["events"])


def main() -> int:
    hfToken = os.environ.get("HF_TOKEN", "")
    mainMode = os.environ.get("DARTLAB_SEARCH_MAIN_MODE", "auto").strip().lower() or "auto"
    mainOnly = os.environ.get("DARTLAB_SEARCH_MAIN_ONLY", "").strip().lower()
    if mainMode not in {"auto", "catalog", "legacy"}:
        print(f"[main] invalid DARTLAB_SEARCH_MAIN_MODE={mainMode!r}")
        return 2
    if mainOnly and mainOnly not in {"lite"}:
        print(f"[main] invalid DARTLAB_SEARCH_MAIN_ONLY={mainOnly!r}")
        return 2
    if mainOnly == "lite":
        _buildAndUploadLite(hfToken)
        print("[lite] 단독 완료")
        return 0

    # ── no-change 단락 — previous+current catalog 변화 0 + 이전 manifest clean 이면 pointer 만 re-point ──
    previousCatalog, currentCatalog, manifestPaths, expectedSources = _catalogInputsFromEnv()
    if mainMode != "legacy" and _isNoChange(previousCatalog, currentCatalog):
        print("[build] catalog 변화 0 + 이전 manifest clean — main 재빌드 없이 manifest pointer 만 re-point")
        _publishNoChangeManifest(hfToken)
        print("[build] no-change 완료")
        return 0

    nDocs = _buildMainFromCatalog(mainMode)
    if nDocs is None:
        print("[main] content 인덱스 풀리빌드 시작 (allFilings + DART panel + EDGAR panel + 뉴스)")
        from dartlab.providers.dart.search import rebuildContent

        t0 = time.perf_counter()
        nDocs = rebuildContent(includePanel=True, includeEdgarPanel=True, includeNews=True, showProgress=True)
        elapsed = time.perf_counter() - t0
        print(f"[main] {nDocs:,} 문서, {elapsed / 60:.1f}분")
    elif nDocs < 0:
        return abs(nDocs)

    # 통합검색(R*) artifact — 결정론 라우터 (질의→이벤트 canon 확장. 큐레이션 동의어는 코드 내장)
    nEvents = _buildRouterArtifact()
    print(f"[main] router.json {nEvents} 이벤트")

    from dartlab.providers.dart.search.entityGraphCatalog import prepareEntityGraphCatalogArtifact
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir
    from dartlab.providers.dart.search.fieldIndexRebuild import writeIndexManifest

    outDir = _contentIndexDir()
    _printEntityGraphSummary(prepareEntityGraphCatalogArtifact(outDir, sourceCatalogPath=currentCatalog))
    manifest = writeIndexManifest(outDir, tier="full", buildCommand="buildSearchMain")

    if nDocs == 0:
        print("[main] 빌드된 문서 없음")
        return 1

    # 퇴행 가드 — HF pull 이 429 등으로 조용히 빈 데이터를 반환하면 nDocs/router/소스별 행수가 빈다.
    # 이 상태로 업로드하면 프로덕션 인덱스를 빈 산출물로 *덮어쓰는 퇴행*. 업로드 중단.
    # ① 총량(350k) ② 소스별 하한(allFilings/panel/edgar/news) — 한 소스 통째 누락(silent partial-pull)
    # 은 총량만으로는 통과할 수 있어(예: news → 319k) 소스별로 개별 차단한다(2026-06 풀셋 ~80%).
    minDocs = int(os.environ.get("DARTLAB_SEARCH_MIN_DOCS", "350000"))
    if nEvents == 0 or nDocs < minDocs:
        print(
            f"[main] ✗ 퇴행 가드 발동 — router {nEvents} 이벤트 / {nDocs:,} 문서(< {minDocs:,}). "
            f"allFilings/panel pull 누락 의심 → 업로드 중단(프로덕션 보호)."
        )
        return 1
    sourceGuardError = _perSourceGuard(manifest.get("nDocsBySource") or {})
    if sourceGuardError:
        print(f"[main] ✗ per-source 가드 발동 — {sourceGuardError} → 업로드 중단(partial pull 회귀 차단).")
        return 1

    if not hfToken:
        print("[main] HF_TOKEN 없음 — 업로드 스킵")
        return 0

    print("[main] 변경 artifact만 staging 업로드 후 current manifest pointer publish")
    from dartlab.providers.dart.search.fieldIndexRebuild import indexPublishNames
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    previousManifestPath = outDir / "previous_manifest.json"
    summary = publishContentIndexFiles(
        token=hfToken,
        indexDir=outDir,
        files=_changedPublishNames(outDir, previousManifestPath, indexPublishNames(outDir)),
        tier="full",
        previousManifestPath=previousManifestPath,
        promoteCurrent=_promoteCurrent(),
    )
    _printPublishSummary(summary)
    _writeCandidateEnv(summary)

    # ── lite tier — pip 사용자 기본 경량 배포(최근 N개월). full(flat)과 별 디렉터리라 공존. ──
    # full 업로드를 막지 않는 best-effort: lite 빌드/업로드 실패해도 full 은 이미 배포됨.
    _buildAndUploadLite(hfToken)

    print("[main] 완료")
    return 0


def _buildMainFromCatalog(mainMode: str) -> int | None:
    if mainMode == "legacy":
        return None
    _, currentCatalog, manifestPaths, expectedSources = _catalogInputsFromEnv()
    if not currentCatalog:
        if mainMode == "catalog":
            print("[main] catalog mode requires DARTLAB_SEARCH_CURRENT_CATALOG")
            return -2
        print("[main] catalog inputs 없음 — legacy raw main rebuild path 사용")
        return None
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir
    from dartlab.providers.dart.search.fieldIndexRebuild import (
        clearDeltaSegment,
        rebuildDeltaFromCatalog,
        rebuildMainFromCatalog,
    )
    from dartlab.providers.dart.search.pipeline import (
        _loadCatalog,
        exportDeltaRowsForContentIndex,
        runCatalogDeltaDryRun,
    )

    result = runCatalogDeltaDryRun(
        previousCatalogPath=None,
        currentCatalogPath=currentCatalog,
        sourceManifestPaths=manifestPaths,
        expectedSources=expectedSources,
    )
    if not result.get("valid"):
        print(f"[main] catalog main input invalid: {result.get('errors')}")
        return -1
    t0 = time.perf_counter()
    catalog = _loadCatalog(currentCatalog)
    outDir = _contentIndexDir()
    import shutil

    mainCatalogPath = outDir / "main_catalog_snapshot.parquet"
    forceFull = _envFlag("FORCE_FULL") or not mainCatalogPath.exists() or not (outDir / "main.postings.bin").exists()
    if forceFull:
        nDocs = rebuildMainFromCatalog(catalog, tier="full", showProgress=True)
        clearDeltaSegment(tier="full")
        shutil.copyfile(currentCatalog, mainCatalogPath)
        buildKind = "mainCompaction"
    else:
        mainCatalog = _loadCatalog(mainCatalogPath)
        deltaRows = exportDeltaRowsForContentIndex(mainCatalog, catalog)
        deltaDocs = rebuildDeltaFromCatalog(deltaRows, tier="full")
        nDocs = _activeCatalogRows(catalog)
        buildKind = f"cumulativeDelta:{deltaDocs}"
    shutil.copyfile(currentCatalog, outDir / "catalog_snapshot.parquet")
    _copySourceManifestSet(outDir)
    elapsed = time.perf_counter() - t0
    print(f"[main] catalog {buildKind} {nDocs:,} active 문서, {elapsed / 60:.1f}분")
    return nDocs


def _activeCatalogRows(catalog) -> int:
    if catalog.is_empty():
        return 0
    if "deleted" not in catalog.columns:
        return catalog.height
    import polars as pl

    return int(catalog.filter(~pl.col("deleted").fill_null(False)).height)


def _envFlag(name: str) -> bool:
    raw = os.environ.get(name, "")
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _buildAndUploadLite(hfToken: str) -> None:
    """lite tier 빌드(최근 N개월 sinceDate 축소) + HF dart/contentIndex/lite/ 업로드.

    환경 ``DARTLAB_LITE_MONTHS`` (기본 18) 만큼 최근 공시만 색인 → 사용자 첫 다운로드 경량.
    퇴행 가드 — lite nDocs 가 너무 적으면(< DARTLAB_LITE_MIN_DOCS) 업로드 skip. full 배포엔 무영향.
    """
    from datetime import datetime, timedelta

    months = int(os.environ.get("DARTLAB_LITE_MONTHS", "18"))
    sinceDate = (datetime.now() - timedelta(days=int(months * 30.5))).strftime("%Y%m%d")
    print(f"[lite] tier 빌드 시작 — sinceDate={sinceDate} (최근 {months}개월)")

    from dartlab.providers.dart.search.fieldIndex import clearCache
    from dartlab.providers.dart.search.fieldIndexRebuild import clearDeltaSegment, rebuildMain, writeIndexManifest

    clearCache()
    _, currentCatalog, _, _ = _catalogInputsFromEnv()
    if currentCatalog:
        nLite = _buildLiteFromCatalog(currentCatalog, sinceDate)
    else:
        nLite = rebuildMain(
            includePanel=True,
            includeEdgarPanel=True,
            includeNews=True,
            tier="lite",
            sinceDate=sinceDate,
            showProgress=True,
        )
        clearDeltaSegment(tier="lite")
    _buildRouterArtifact(tier="lite")  # 라우터는 코퍼스 무관 — lite 디렉터리에 동거

    # 산출물 실측 크기 — '사용자 첫 다운로드 경량' 가치제안을 숫자로 검증(가정 금지).
    from dartlab.providers.dart.search.entityGraphCatalog import prepareEntityGraphCatalogArtifact
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir

    liteDir = _contentIndexDir("lite")
    _copySourceManifestSet(liteDir)
    _printEntityGraphSummary(prepareEntityGraphCatalogArtifact(liteDir, sourceCatalogPath=currentCatalog))
    liteBytes = sum(p.stat().st_size for p in liteDir.glob("*") if p.is_file())
    liteMb = liteBytes / 1024 / 1024
    print(f"[lite] 산출물 {liteMb:.1f} MB ({nLite:,} 문서)")
    maxMb = float(os.environ.get("DARTLAB_LITE_MAX_MB", "300"))
    if liteMb > maxMb:
        print(
            f"[lite] ⚠ 크기 경고 — {liteMb:.0f} MB > {maxMb:.0f} MB. lite 의 '경량' 가치가 약화 — "
            f"DARTLAB_LITE_MONTHS 축소 또는 종목 whitelist(시총 상위) 도입 검토."
        )

    minLite = int(os.environ.get("DARTLAB_LITE_MIN_DOCS", "50000"))
    if nLite < minLite:
        print(f"[lite] ✗ nDocs {nLite:,} < {minLite:,} — lite 업로드 skip (full 은 이미 배포됨)")
        return
    writeIndexManifest(liteDir, tier="lite", buildCommand="buildSearchMain.lite")
    if not hfToken:
        print("[lite] HF_TOKEN 없음 — 업로드 스킵")
        return
    print(f"[lite] {nLite:,} 문서 / {liteMb:.1f} MB → HF dart/contentIndex/lite/ 업로드")
    from dartlab.providers.dart.search.fieldIndexRebuild import indexPublishNames
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    previousManifestPath = liteDir / "previous_manifest.json"
    summary = publishContentIndexFiles(
        token=hfToken,
        indexDir=liteDir,
        files=_changedPublishNames(liteDir, previousManifestPath, indexPublishNames(liteDir)),
        tier="lite",
        previousManifestPath=previousManifestPath,
        promoteCurrent=_promoteCurrent(),
    )
    _printPublishSummary(summary)
    _writeCandidateEnv(summary)
    print("[lite] 완료")


def _buildLiteFromCatalog(currentCatalog: str, sinceDate: str) -> int:
    import polars as pl

    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir
    from dartlab.providers.dart.search.fieldIndexRebuild import (
        clearDeltaSegment,
        rebuildDeltaFromCatalog,
        rebuildMainFromCatalog,
    )
    from dartlab.providers.dart.search.pipeline import _loadCatalog, exportDeltaRowsForContentIndex

    catalog = _loadCatalog(currentCatalog)
    liteCatalog = _filterLiteCatalogRows(catalog, sinceDate)
    print(f"[lite] catalog mode — {catalog.height:,} rows -> {liteCatalog.height:,} rows")
    liteDir = _contentIndexDir("lite")
    mainCatalogPath = liteDir / "main_catalog_snapshot.parquet"
    forceFull = _envFlag("FORCE_FULL") or not mainCatalogPath.exists() or not (liteDir / "main.postings.bin").exists()
    if forceFull:
        nLite = rebuildMainFromCatalog(liteCatalog, tier="lite", showProgress=True)
        clearDeltaSegment(tier="lite")
        liteCatalog.write_parquet(mainCatalogPath)
        buildKind = "mainCompaction"
    else:
        mainCatalog = _loadCatalog(mainCatalogPath)
        deltaRows = exportDeltaRowsForContentIndex(mainCatalog, liteCatalog)
        deltaDocs = rebuildDeltaFromCatalog(deltaRows, tier="lite")
        nLite = _activeCatalogRows(liteCatalog)
        buildKind = f"cumulativeDelta:{deltaDocs}"
    if isinstance(liteCatalog, pl.DataFrame):
        liteCatalog.write_parquet(liteDir / "catalog_snapshot.parquet")
    print(f"[lite] catalog {buildKind}, {nLite:,} active 문서")
    return nLite


def _filterLiteCatalogRows(catalogRows, sinceDate: str):
    import polars as pl

    if catalogRows.is_empty() or "date" not in catalogRows.columns:
        return catalogRows
    return (
        catalogRows.with_columns(
            pl.col("date").cast(pl.Utf8).str.replace_all("-", "").fill_null("").alias("__liteDate")
        )
        .filter(pl.col("__liteDate") >= sinceDate)
        .drop("__liteDate")
    )


def _copySourceManifestSet(outDir: Path) -> None:
    src = os.environ.get("DARTLAB_SEARCH_SOURCE_MANIFEST_SET", "").strip()
    if not src:
        return
    path = Path(src)
    if path.exists():
        import shutil

        shutil.copyfile(path, outDir / "source_manifest_set.json")


def _printEntityGraphSummary(summary: dict) -> None:
    mode = str(summary.get("mode") or "")
    if mode not in {"copied", "built", "missing"}:
        return
    print(f"[graph] entityGraphCatalog {mode}: {summary}")


def _promoteCurrent() -> bool:
    raw = os.environ.get("DARTLAB_SEARCH_PROMOTE_CURRENT", "1")
    return raw.strip().lower() not in {"0", "false", "no", "n"}


def _changedPublishNames(outDir: Path, previousManifestPath: Path, names: list[str]) -> list[str]:
    """이전 pointer와 hash가 같은 artifact는 재업로드하지 않고 fileSources를 재사용한다."""
    try:
        current = json.loads((outDir / "manifest.json").read_text(encoding="utf-8"))
        previous = json.loads(previousManifestPath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return names
    currentHashes = current.get("fileHashes") if isinstance(current.get("fileHashes"), dict) else {}
    previousHashes = previous.get("fileHashes") if isinstance(previous.get("fileHashes"), dict) else {}
    previousSources = previous.get("fileSources") if isinstance(previous.get("fileSources"), dict) else {}
    changed = [
        name
        for name in names
        if name == "manifest.json" or currentHashes.get(name) != previousHashes.get(name) or name not in previousSources
    ]
    skipped = len(names) - len(changed)
    if skipped:
        print(f"[publish] unchanged artifact {skipped}개 재사용, upload {len(changed) - 1}개")
    return changed


def _printPublishSummary(summary: dict) -> None:
    action = "promote" if summary.get("promoted", True) else "stage"
    print(
        f"  [{action}] {summary.get('candidateManifestPath', '')} "
        f"-> {summary['currentPrefix']} {summary['publishMode']} ({len(summary['uploaded'])} uploads)"
    )


def _writeCandidateEnv(summary: dict) -> None:
    envFile = os.environ.get("GITHUB_ENV", "").strip()
    candidate = str(summary.get("candidateManifestPath") or "").strip()
    tier = str(summary.get("tier") or "full").strip().upper()
    if not envFile or not candidate:
        return
    key = f"DARTLAB_SEARCH_{tier}_CANDIDATE_MANIFEST"
    with Path(envFile).open("a", encoding="utf-8") as f:
        f.write(f"{key}={candidate}\n")


if __name__ == "__main__":
    sys.exit(main())
