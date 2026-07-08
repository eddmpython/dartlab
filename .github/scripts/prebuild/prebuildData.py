"""CI용 scan 프리빌드 + HF 업로드.

수집 완료 후 실행되어 scan 프리빌드 데이터를 생성하고 HuggingFace에 업로드.

일일 흐름 (증분 — 기본):
  1. base seed: finance/report 는 Actions cache 우선, scan 은 알려진 산출물 직접 seed
  2. panel listing 1 회(다운로드 0) → 직전 ledger 대비 변경/삭제 종목 가림
  3. 변경 종목 panel parquet 만 다운로드 (전 92K seed 금지 = OOM/디스크 고갈 회피)
  4. buildScan(incremental=True): changes/sharesOutstanding 는 변경분만 재계산 후 기존 parquet 에
     종목 단위 머지. finance/report 는 입력이 full 캐시이므로 full 빌드.
  5. docsIndex 증분 머지 + 삭제 종목 prune + _scanBuildState 갱신
  6. HF upload_folder → dart/scan/

주간 흐름 (full — PREBUILD_FULL=1, 디스크 확보된 별도 job):
  전 종목 panel seed → buildScan(incremental=False) full 재생성 (빌더 변경/backfill drift 교정 안전망)

환경변수:
  DARTLAB_DATA_DIR: 데이터 경로 (기본: ./data)
  HF_TOKEN: HuggingFace write 토큰
  PREBUILD_TARGETS: scan (기본, 쉼표 구분 확장 가능)
  PREBUILD_FULL: "1"/"true" 면 전 종목 full 재생성 (주간 cron)
"""

import os
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))
from _hfRetry import retryHfCall  # noqa: E402
from planning.prebuildManifest import categoryFileCount, scanArtifactRelPaths  # noqa: E402
from planning.prebuildPlan import DEFAULT_INCREMENTAL_DOWNLOAD_CAP, planBaseSeed, planPanelDelta  # noqa: E402

# scan 프리빌드가 읽는 입력 카테고리 SSOT — buildScan 하위 빌더의 원천.
#   finance/report → 재무·보고서 빌더, panel → changes/sharesOutstanding/docsIndex 빌더.
INPUT_CATEGORIES: tuple[str, ...] = ("finance", "report", "panel")
# 증분 사이클 base seed: finance/report(full 빌드 입력) + scan(직전 산출물 + ledger).
# panel 은 전량 seed 하지 않고 변경분만 받는다 (전 92K seed = prebuild OOM/디스크 고갈 근본원인).
BASE_SEED_CATEGORIES: tuple[str, ...] = ("finance", "report", "scan")

SCAN_OUTPUT_KEYS = (
    ("changes.parquet", "stockCode"),
    ("sharesOutstanding.parquet", "stock_code"),
    ("docsIndex.parquet", "stockCode"),
)

# 일일 증분 변경분 다운로드 상한 — 초과분은 다음 사이클로 drain (대량 변경 시 디스크/시간 폭주
# 방지, OOM 근본원인 재발 차단). 정상 일일 변경은 수십~수백이라 거의 닿지 않는다.
INCREMENTAL_DOWNLOAD_CAP = DEFAULT_INCREMENTAL_DOWNLOAD_CAP


def _isFullMode() -> bool:
    return os.environ.get("PREBUILD_FULL", "").strip().lower() in ("1", "true", "yes")


def _categoryFileCount(dataDir: str, category: str) -> int:
    """Return local file count for a data category."""
    from dartlab.core.dataConfig import DATA_RELEASES

    return categoryFileCount(dataDir, category, DATA_RELEASES)


def _knownScanRelPaths() -> list[str]:
    """Return fixed scan artifacts for direct seed without HF tree listing."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.scan.builders.kr.notes import SCAN_NOTE_CONCEPTS
    from dartlab.scan.builders.kr.report.build import SCAN_API_TYPES

    noteBares = [bare for bare, _, _ in SCAN_NOTE_CONCEPTS]
    return scanArtifactRelPaths(DATA_RELEASES["scan"]["dir"], SCAN_API_TYPES, noteBares)


def _seedKnownScanArtifacts(dataDir: str) -> tuple[int, int, float]:
    """Seed known scan outputs by direct resolve URLs, avoiding HF tree-list 429."""
    from dartlab.pipeline.seed import downloadCategoryFiles

    root = Path(dataDir)
    missing = [rel for rel in _knownScanRelPaths() if not (root / rel).exists()]
    if missing:
        downloaded, skipped404 = downloadCategoryFiles("scan", missing, dataDir=dataDir)
    else:
        downloaded, skipped404 = 0, 0

    downloadedBytes = sum((root / rel).stat().st_size for rel in missing if (root / rel).exists())
    total = _categoryFileCount(dataDir, "scan")
    skip = f", 404-skip {skipped404}" if skipped404 else ""
    print(
        f"[prebuild] base seed scan: 로컬 {total}개 (known 신규 {downloaded}{skip} / {downloadedBytes / 1024 / 1024:.1f}MB)"
    )
    return total, downloaded, downloadedBytes / 1024 / 1024


def _seedBaseInputs(dataDir: str) -> None:
    """finance/report full inputs cache-first + scan known artifacts direct seed."""
    from dartlab.pipeline.seed import seedCategoriesFromHf

    localCounts = {cat: _categoryFileCount(dataDir, cat) for cat in ("finance", "report")}
    seedPlan = planBaseSeed(localCounts)
    for cat in seedPlan.cachedCategories:
        print(f"[prebuild] base seed {cat}: 로컬 {localCounts[cat]}개 (Actions cache 사용, HF listing skip)")

    categories = list(seedPlan.missingCategories)
    summary = seedCategoriesFromHf(categories, dataDir=dataDir) if categories else {}
    for cat, (total, new, mb) in summary.items():
        print(f"[prebuild] base seed {cat}: 로컬 {total}개 (신규 {new} / {mb:.1f}MB)")
    _seedKnownScanArtifacts(dataDir)


def _seedKindAndCorpProfile(dataDir: str) -> None:
    """KIND/dartList/corpProfile 메타를 HF 에서 로컬 캐시 위치로 seed (retryHfCall SSOT 경유).

    buildScan 이 KIND HTTP 호출 시 OfflineViolation 이므로 kindlist.yml 이 HF push 한 결과를
    오프라인 가드 아래 다운로드해 둔다. 결산월 SSOT(corpProfile) 도 함께. best-effort —
    부재/일시실패는 다음 빌드 단계가 raw 추정으로 보강하므로 빌드를 막지 않는다.
    """
    from huggingface_hub import hf_hub_download

    from dartlab.core.dataConfig import HF_REPO

    root = Path(dataDir)
    seeds = [
        ("metadata/corpList.parquet", root / "kindList" / "corpList.parquet"),
        ("metadata/dartList.parquet", root / "dartList" / "dartList.parquet"),
        ("dart/scan/corpProfile.parquet", root / "dart" / "scan" / "corpProfile.parquet"),
    ]
    token = os.environ.get("HF_TOKEN") or None
    for src, dst in seeds:
        try:
            cached = retryHfCall(hf_hub_download, repo_id=HF_REPO, repo_type="dataset", filename=src, token=token)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(cached, dst)
            print(f"[prebuild] KIND seed: {src} -> {dst}")
        except Exception as exc:  # noqa: BLE001 — best-effort: 부재/일시실패는 빌드 단계가 보강
            print(f"[prebuild] KIND seed skip ({src}): {type(exc).__name__}: {exc}")


def _seedFullPanel(dataDir: str) -> dict[str, int]:
    """(full 모드) 전 종목 panel seed — 디스크 확보된 주간 job 전용. ledger 용 remote state 반환."""
    from dartlab.pipeline.seed import listRemoteFiles, seedCategoriesFromHf

    summary = seedCategoriesFromHf(["panel"], dataDir=dataDir)
    for cat, (total, new, mb) in summary.items():
        print(f"[prebuild] full panel seed {cat}: 로컬 {total}개 (신규 {new} / {mb:.1f}MB)")
    return listRemoteFiles("panel")


def _prepareIncrementalPanel(dataDir: str) -> tuple[list[str], list[str], dict[str, int]]:
    """panel listing(다운로드 0) → 직전 ledger 대비 변경/삭제 가림 → 변경분만 다운로드.

    부트스트랩(ledger 부재)은 변경분을 받지 않고 ledger 만 기록한다 — 전 92K seed(=OOM
    근본원인)를 일으키지 않기 위함. baseline 산출물은 주간 full cron 이 생성한다.
    대량 변경은 ``INCREMENTAL_DOWNLOAD_CAP`` 까지만 받고 나머지는 다음 사이클로 drain.

    Returns:
        (changedCodes, removedCodes, newState) — newState 는 다음 사이클 ledger(처리분만 반영).
    """
    from dartlab.pipeline.seed import downloadCategoryFiles, listRemoteFiles
    from dartlab.scan.builders.kr.common import loadScanBuildState

    prior = loadScanBuildState()
    try:
        remote = listRemoteFiles("panel")  # {dart/panel/CODE.parquet: size}
    except Exception as exc:  # noqa: BLE001 — HF tree 429 시 직전 ledger 로 no-change degrade
        if prior:
            print(f"[prebuild] ⚠ panel listing 실패 — no-change 사이클로 degrade: {type(exc).__name__}: {exc}")
            return [], [], dict(prior)
        raise
    print(f"[prebuild] panel listing: 원격 {len(remote)}개, 직전 ledger {len(prior)}개")

    panelPlan = planPanelDelta(prior, remote, cap=INCREMENTAL_DOWNLOAD_CAP)
    if panelPlan.bootstrap:
        # 부트스트랩: 전량 다운로드 금지. ledger 만 기록 → 다음 사이클부터 진짜 변경분만.
        print(
            "[prebuild] ⚠ ledger 부재(부트스트랩) — panel 다운로드 skip, ledger 만 기록. baseline 은 full cron 이 생성"
        )
        return [], [], dict(panelPlan.newState)

    processRel = list(panelPlan.processRel)
    if panelPlan.capped:
        totalChanged = len(panelPlan.processRel) + len(panelPlan.deferredRel)
        print(
            f"[prebuild] ⚠ 변경 {totalChanged}개 > 상한 {INCREMENTAL_DOWNLOAD_CAP} — "
            f"{len(processRel)}개만 처리, 나머지는 다음 사이클 drain"
        )

    if processRel:
        print(f"[prebuild] 변경 종목 {len(processRel)}개 panel 다운로드")
        downloaded, skipped404 = downloadCategoryFiles("panel", processRel, dataDir=dataDir)
        skip = f", 404-skip {skipped404}" if skipped404 else ""
        print(f"[prebuild] panel 다운로드 완료: {downloaded}개{skip}")
    else:
        print("[prebuild] 변경 종목 없음 — panel 다운로드 skip")

    return list(panelPlan.changedCodes), list(panelPlan.removedCodes), dict(panelPlan.newState)


def _checkDataReady(dataDir: str) -> dict[str, int]:
    """INPUT_CATEGORIES 입력 캐시 존재 여부 확인. 카테고리별 파일 수 반환.

    증분 모드에서 panel 수 = '변경 종목 수' (0 허용)이다.
    """
    from dartlab.core.dataConfig import DATA_RELEASES

    counts = {}
    for cat in INPUT_CATEGORIES:
        catDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        n = len(list(catDir.glob("*.parquet"))) if catDir.exists() else 0
        counts[cat] = n
    return counts


def _validateInputCoverage(counts: dict[str, int], *, incremental: bool) -> None:
    """prebuild 입력 coverage 검증.

    full 모드: panel 은 changes/sharesOutstanding/docsIndex 의 source 이자 회사 enum 이므로 필수.
    증분 모드: panel 로컬 수 = 변경 종목 수라 0 도 정상. finance/report 존재로 충분하며,
    finance 산출 검증은 빌드 후 _validateFinanceParquet 가 담당.
    """
    if all(v == 0 for v in counts.values()):
        print("[prebuild] ❌ 입력 데이터가 전부 0개 — base seed 실패 또는 빈 dataset")
        sys.exit(1)

    if incremental:
        return

    panelCount = counts.get("panel", 0)
    if panelCount <= 0:
        print("[prebuild] ❌ panel 입력 0개 — changes/sharesOutstanding/docsIndex 빌드 불가")
        sys.exit(1)

    sourceCount = max(counts.get("finance", 0), counts.get("report", 0))
    if sourceCount >= 100:
        minPanelCount = max(1, int(sourceCount * 0.5))
        if panelCount < minPanelCount:
            print(
                f"[prebuild] ❌ panel coverage 부족: panel={panelCount}, "
                f"finance/report 기준={sourceCount}, 최소={minPanelCount}"
            )
            sys.exit(1)


def _buildScan(dataDir: str, *, incremental: bool) -> dict[str, Path | list[Path] | None]:
    """scan 프리빌드 실행 (incremental=True 면 panel 빌더는 변경분만 재계산·머지)."""
    from dartlab.scan.builders.kr import buildScan

    return buildScan(sinceYear=2021, reportSinceYear=2016, verbose=True, incremental=incremental)


def _buildDocsIndex(dataDir: str, *, incremental: bool) -> Path | None:
    """docsIndex 슬림 인덱스 빌드 — panel 섹션 메타에서 생성 (실패는 silent → summary 표기).

    Args:
        dataDir: 데이터 디렉토리.
        incremental: True 면 변경 종목 행을 기존 docsIndex 에 머지.

    Returns:
        산출 parquet 경로 또는 None (실패 시).

    Raises:
        없음 (실패는 silent → summary 에 표기).

    Example:
        >>> _buildDocsIndex("./data", incremental=False)  # doctest: +SKIP
    """
    try:
        from dartlab.scan.builders.kr.docsIndex import buildDocsIndex

        return buildDocsIndex(sinceYear=2016, batchSize=100, verbose=True, incremental=incremental)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"[prebuild] docsIndex 빌드 실패 (스킵): {exc}")
        return None


def _pruneRemovedCodes(removedCodes: list[str]) -> None:
    """상장폐지 등으로 사라진 종목 행을 scan 산출물에서 제거 (다운로드 불요)."""
    if not removedCodes:
        return
    from dartlab.scan.builders.kr.common import pruneScanCodes, scanDir

    sd = scanDir()
    for fname, key in SCAN_OUTPUT_KEYS:
        removed = pruneScanCodes(sd / fname, removedCodes, key=key)
        if removed:
            print(f"[prebuild] prune {fname}: {removed}행 제거 ({len(removedCodes)}종목 삭제)")


def _uploadScan(dataDir: str) -> None:
    """scan 결과를 HuggingFace에 업로드 (_scanBuildState.json 포함)."""
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print("[prebuild] HF_TOKEN 없음 → 업로드 스킵")
        return

    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

    scanDir = Path(dataDir) / DATA_RELEASES["scan"]["dir"]
    if not scanDir.exists():
        print("[prebuild] scan 디렉토리 없음 → 업로드 스킵")
        return

    parquets = list(scanDir.rglob("*.parquet"))
    if not parquets:
        print("[prebuild] scan parquet 없음 → 업로드 스킵")
        return

    api = HfApi(token=token)
    dirPath = DATA_RELEASES["scan"]["dir"]

    print(f"[prebuild] HF 업로드: {len(parquets)}개 parquet (+ledger) → {HF_REPO}/{dirPath}/")
    retryHfCall(
        api.upload_folder,
        repo_id=HF_REPO,
        repo_type="dataset",
        folder_path=str(scanDir),
        path_in_repo=dirPath,
        commit_message=f"prebuild scan: {len(parquets)} files",
    )
    print("[prebuild] HF 업로드 완료")


def _validateFinanceParquet(dataDir: str, sourceFileCount: int) -> None:
    """프리빌드 finance.parquet 품질 검증.

    원본 finance 파일 수 대비 프리빌드 종목 수가 50% 미만이면 에러로 빌드 실패 처리.
    """
    from dartlab.core.dataConfig import DATA_RELEASES

    scanDir = Path(dataDir) / DATA_RELEASES["scan"]["dir"]
    fp = scanDir / "finance.parquet"
    if not fp.exists():
        # 원본 finance 가 있었는데 프리빌드 산출이 없으면 = seed/빌드 실패(부분 scan 을 HF 에 올릴 위험).
        if sourceFileCount > 0:
            print(
                f"[prebuild] ❌ 원본 finance {sourceFileCount}종목인데 프리빌드 finance.parquet 미생성 — seed/빌드 실패"
            )
            sys.exit(1)
        print("[prebuild] finance.parquet 없음 (원본도 0) → 검증 스킵")
        return

    import polars as pl

    df = pl.read_parquet(str(fp))
    scCol = "stockCode" if "stockCode" in df.columns else "stock_code"
    prebuildStocks = df.select(scCol).unique().height
    ratio = prebuildStocks / sourceFileCount if sourceFileCount > 0 else 0

    print(f"[prebuild] 품질: 원본 {sourceFileCount}종목, 프리빌드 {prebuildStocks}종목 ({ratio:.0%})")

    if ratio < 0.5:
        print(f"[prebuild] ❌ 커버리지 {ratio:.0%} < 50% — 캐시가 stale한 것으로 판단")
        sys.exit(1)


def main():
    # prebuild = offline only. 외부 API 호출은 sync 단계 책임 — 가드로 강제.
    # HF dataset 다운로드는 default allow.
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.offlineGuard import enforceOffline
    from dartlab.scan.builders.kr.common import saveScanBuildState

    enforceOffline()

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")
    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    targets = os.environ.get("PREBUILD_TARGETS", "scan").split(",")
    fullMode = _isFullMode()
    incremental = not fullMode
    print(f"[prebuild] targets={targets} dataDir={dataDir} mode={'full' if fullMode else 'incremental'}")

    # panel 로컬 dir 보장 (증분 0-change 사이클에서도 빌더 glob 이 FileNotFoundError 안 나게)
    (Path(dataDir) / DATA_RELEASES["panel"]["dir"]).mkdir(parents=True, exist_ok=True)

    # 1단계: base seed (finance/report full + scan 직전 산출물/ledger) + KIND/corpProfile 메타
    _seedBaseInputs(dataDir)
    _seedKindAndCorpProfile(dataDir)

    # 2단계: panel 변경 감지 (증분) 또는 전량 seed (full)
    if fullMode:
        remoteState = _seedFullPanel(dataDir)
        changedCodes, removedCodes = [], []
    else:
        changedCodes, removedCodes, remoteState = _prepareIncrementalPanel(dataDir)
        print(f"[prebuild] 증분: 변경 {len(changedCodes)}종목 · 삭제 {len(removedCodes)}종목")

    counts = _checkDataReady(dataDir)
    print("[prebuild] 캐시: " + " ".join(f"{k}={v}" for k, v in counts.items()))
    _validateInputCoverage(counts, incremental=incremental)

    # 3단계: scan 프리빌드 (외부 API 호출 0)
    if "scan" in targets:
        start = time.time()
        results = _buildScan(dataDir, incremental=incremental)
        elapsed = time.time() - start
        print(f"[prebuild] scan 빌드 완료: {elapsed:.0f}초")

        # 3.5단계: docsIndex (panel 섹션) — 증분이면 변경분 머지, full 이면 전체.
        #   증분 0-change 사이클은 panel 로컬 0 → buildDocsIndex 가 안전히 skip(직전 산출 보존).
        if fullMode or changedCodes:
            results["docsIndex"] = _buildDocsIndex(dataDir, incremental=incremental)

        # 3.6단계: 삭제 종목 prune (증분 전용)
        _pruneRemovedCodes(removedCodes)

        # 3.7단계: ledger 갱신 (다음 사이클 변경 감지 기준)
        saveScanBuildState(remoteState)
        print(f"[prebuild] ledger 갱신: panel {len(remoteState)}개")

        # 3.8단계: 데이터 품질 검증 (finance 는 full 빌드라 모드 무관)
        _validateFinanceParquet(dataDir, counts["finance"])

        # 4단계: HF 업로드
        _uploadScan(dataDir)
        _writeSummary(counts, results, elapsed)
    else:
        print("[prebuild] scan이 targets에 없음 → 스킵")
        _writeSummary(counts, None, 0)


def _writeSummary(
    counts: dict[str, int],
    results: dict | None,
    elapsed: float,
) -> None:
    """GitHub Actions step summary 작성."""
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summaryPath:
        return

    dataDir = os.environ.get("DARTLAB_DATA_DIR", "./data")

    with open(summaryPath, "a", encoding="utf-8") as f:
        f.write("## Scan Prebuild\n\n")
        f.write(f"| 모드 | {'full' if _isFullMode() else 'incremental'} |\n|------|----|\n")
        for cat, n in counts.items():
            label = f"{cat} 캐시" if cat != "panel" or _isFullMode() else "panel 변경분"
            f.write(f"| {label} | {n}개 |\n")
        f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")

        if results:
            from dartlab.core.dataConfig import DATA_RELEASES

            scanDir = Path(dataDir) / DATA_RELEASES["scan"]["dir"]
            if scanDir.exists():
                totalMb = sum(p.stat().st_size for p in scanDir.rglob("*.parquet")) / 1024 / 1024
                fileCount = len(list(scanDir.rglob("*.parquet")))
                f.write(f"| scan 파일 | {fileCount}개 |\n")
                f.write(f"| scan 크기 | {totalMb:.1f}MB |\n")


if __name__ == "__main__":
    main()
