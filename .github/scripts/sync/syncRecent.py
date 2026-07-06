"""경량 일일 동기화 — 새 정기보고서가 올라온 종목만 증분 수집.

흐름:
  1. DART list.json으로 최근 N일 정기공시 조회 (API 1회)
  2. 사업보고서/반기보고서/분기보고서 필터링
  3. 기존 finance/report parquet의 rcept_no와 비교 → 새 보고서가 있는 종목만 추출
  4. 해당 종목만 증분 수집 + 변경 파일 기록

환경변수:
  DART_API_KEYS: DART OpenAPI 키 (쉼표 구분)
  SYNC_LOOKBACK_DAYS: 조회 기간 (기본: 7일)
  SYNC_CATEGORIES: 수집 카테고리 (기본: finance,report)
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


def _snapshotHashes(directory: Path, targets: set[str]) -> dict[str, str]:
    """특정 종목코드 파일만 해시 스냅샷 (pipeline.hashing.partialFileHash SSOT)."""
    from dartlab.pipeline.hashing import partialFileHash

    result = {}
    for sc in targets:
        p = directory / f"{sc}.parquet"
        if p.exists():
            result[p.name] = partialFileHash(p)
    return result


def _cloneCategory(category: str, dataDir: str, targetCodes: set[str]) -> int:
    """HF에서 대상 종목 parquet만 개별 다운로드."""
    from dartlab.core.dataConfig import DATA_RELEASES, hfBaseUrl

    dirPath = DATA_RELEASES[category]["dir"]
    localDir = Path(dataDir) / dirPath
    localDir.mkdir(parents=True, exist_ok=True)

    baseUrl = hfBaseUrl(category)
    downloaded = 0

    for sc in targetCodes:
        dest = localDir / f"{sc}.parquet"
        if dest.exists():
            continue
        url = f"{baseUrl}/{sc}.parquet"
        try:
            import urllib.request

            urllib.request.urlretrieve(url, str(dest))
            downloaded += 1
        except Exception:
            pass  # HF에 없는 신규 종목은 무시

    existing = len(list(localDir.glob("*.parquet")))
    if downloaded:
        print(f"[syncRecent] {category}: HF에서 {downloaded}개 다운로드, 총 {existing}개")
    return existing


def _stateDir(dataDir: str) -> Path:
    """카테고리별 collect state 경로.

    병렬/재실행 간 pending.txt/failures.json
    동시 쓰기 경쟁 회피 — env ``SYNC_STATE_SCOPE`` 로 subdir 분리.

    - fr: `data/dart/_collect_state/fr/` (finance+report)
    - scope 없으면 기존 단일 경로 (로컬 실행 호환)
    """
    base = Path(dataDir) / "dart" / "_collect_state"
    scope = os.environ.get("SYNC_STATE_SCOPE", "").strip()
    return base / scope if scope else base


def _existingRceptNos(directory: Path, stockCode: str) -> set[str]:
    """parquet 파일에서 rcept_no 집합 추출 (finance/report 공통).

    두 카테고리 모두 `rcept_no` 컬럼을 가지므로 단일 함수로 통일.
    파일이 없거나 컬럼이 없거나 손상된 경우 빈 set.
    """
    import polars as pl

    path = directory / f"{stockCode}.parquet"
    if not path.exists():
        return set()
    try:
        cols = pl.scan_parquet(path).collect_schema().names()
        if "rcept_no" not in cols:
            return set()
        df = (
            pl.scan_parquet(path)
            .select("rcept_no")
            .filter(pl.col("rcept_no").is_not_null() & (pl.col("rcept_no") != ""))
            .unique()
            .collect()
        )
        return set(df["rcept_no"].to_list())
    except (pl.exceptions.ComputeError, pl.exceptions.ColumnNotFoundError, OSError):
        return set()


# report도 finance와 동일 — rcept_no 존재 여부만 본다.
# (이전엔 apiType≥5 partial 임계를 두었으나, 정상 종목까지 재수집 대상으로
#  분류하는 부작용이 있어 폐기. partial은 batchCollect 단계에서 처리한다.)


def _reportNmToFinanceKey(reportNm: str) -> tuple[str, str] | None:
    """보고서명 → (bsns_year, reprt_code) 매핑.

    예: "사업보고서 (2025.12)" → ("2025", "11011")
    """
    import re

    normalized = re.sub(r"^(?:\[(?:기재정정|첨부정정|첨부추가)\]\s*)+", "", reportNm).strip()
    if "사업보고서제출기한연장신고서" in normalized:
        return None

    yearMatch = re.search(r"\((\d{4})\.(\d{2})\)", normalized)
    if not yearMatch:
        return None
    year = yearMatch.group(1)

    if normalized.startswith("사업보고서"):
        return (year, "11011")
    if normalized.startswith("반기보고서"):
        return (year, "11012")
    if normalized.startswith("분기보고서"):
        # 분기는 (2025.03) → Q1, (2025.09) → Q3
        month = yearMatch.group(2)
        if month == "03":
            return (year, "11013")
        if month == "09":
            return (year, "11014")
    return None


def _discoverNewFilings(keys: str, lookbackDays: int, dataDir: str) -> tuple[set[str], dict[str, list[dict]]]:
    """최근 N일 정기공시에서 새 보고서 있는 종목 + rcept_no 매핑 반환.

    Returns:
        (targetCodes, codeToFilings)
        codeToFilings: {stockCode: [{rcept_no, rcept_dt, report_nm, corp_code, corp_name}, ...]}
    """
    import polars as pl

    from dartlab.core.dartClient import DartApiError, DartClient
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.gather.dart.disclosure import listFilings

    end = datetime.now()
    start = end - timedelta(days=lookbackDays)

    # 키 로테이션: 여러 키가 있으면 순서대로 시도
    keyList = [k.strip() for k in keys.split(",") if k.strip()]
    filings = None

    for apiKey in keyList:
        try:
            client = DartClient(apiKey=apiKey)
            filings = listFilings(
                client,
                corp=None,
                start=start.strftime("%Y%m%d"),
                end=end.strftime("%Y%m%d"),
                filingType="A",
                fetchAll=True,
            )
            break  # 성공
        except DartApiError as e:
            if "020" in str(e):
                print(f"[syncRecent] API 한도 초과 (키 {apiKey[:8]}...), 다음 키 시도")
                continue
            raise

    if filings is None:
        print("[syncRecent] 모든 API 키 한도 초과 → 수집 불가, 다음 실행까지 대기")
        return set(), {}

    if filings.height == 0:
        print("[syncRecent] 최근 정기공시 없음")
        return set(), {}

    reportFilter = r"^(?:\[(?:기재정정|첨부정정|첨부추가)\]\s*)*(사업보고서|반기보고서|분기보고서)"
    filtered = filings.filter(
        pl.col("report_nm").str.contains(reportFilter)
        & ~pl.col("report_nm").str.contains("사업보고서제출기한연장신고서")
        & pl.col("stock_code").is_not_null()
        & (pl.col("stock_code") != "")
        & (pl.col("stock_code") != " ")
    )

    if filtered.height == 0:
        print("[syncRecent] 대상 보고서 없음")
        return set(), {}

    allCandidateCodes = set(filtered["stock_code"].unique().to_list())

    # finance + report parquet 확보 (비교용)
    _cloneCategory("finance", dataDir, allCandidateCodes)
    _cloneCategory("report", dataDir, allCandidateCodes)

    # 종목별 filing 매핑
    codeToFilings: dict[str, list[dict]] = {}
    for row in filtered.iter_rows(named=True):
        sc = row["stock_code"]
        codeToFilings.setdefault(sc, []).append(row)

    # 근본 원칙 (2026-04-08): rcept_no를 단일 키로 카테고리별 독립 누락 검사.
    #
    # 정기보고서 list.json의 각 행 = (stockCode, rcept_no) 단위.
    # 이 rcept_no가 finance/report 각 parquet에 들어있는지 독립 검사.
    # - finance: rcept_no 컬럼 직접 비교 (정정 보고서도 감지)
    # - report: rcept_no 컬럼 직접 비교 (apiType 임계 폐기 — 정상 종목 오탐 부작용)
    #
    # 종목 단위 targetCodes는 합집합이지만, 카테고리별로 정확히 누락된 (rcept_no/period)만
    # 수집하도록 missingByCat에 분리 저장한다.
    financeDir = Path(dataDir) / DATA_RELEASES["finance"]["dir"]
    reportDir = Path(dataDir) / DATA_RELEASES["report"]["dir"]

    targetCodes: set[str] = set()
    targetFilings: dict[str, list[dict]] = {}
    missingFinanceCount = 0
    missingReportCount = 0

    for sc, rows in codeToFilings.items():
        existingFinance = _existingRceptNos(financeDir, sc)
        existingReport = _existingRceptNos(reportDir, sc)

        missingFinance = [r for r in rows if r["rcept_no"] not in existingFinance]
        missingReport = [r for r in rows if r["rcept_no"] not in existingReport]

        if missingFinance:
            missingFinanceCount += 1
        if missingReport:
            missingReportCount += 1

        if missingFinance or missingReport:
            targetCodes.add(sc)
            # finance/report 수집은 batchCollect가 (year, reprt_code) 기반이므로
            # main()에서 missing rows를 합쳐 targetPeriodsByCode를 구성한다.
            targetFilings[sc] = {
                "finance": missingFinance,
                "report": missingReport,
            }

    skipped = len(allCandidateCodes) - len(targetCodes)
    reportNames = filtered["report_nm"].unique().to_list()
    print(f"[syncRecent] 최근 {lookbackDays}일 정기공시: {filtered.height}건, {len(allCandidateCodes)}개 종목")
    print(f"[syncRecent] 보고서 유형: {reportNames}")
    print(
        f"[syncRecent] 수집 대상: {len(targetCodes)}개 "
        f"(finance 누락={missingFinanceCount}, report 누락={missingReportCount}, 스킵={skipped})"
    )

    return targetCodes, targetFilings


def _verifyCollectedRcepts(
    targetFilings: dict[str, dict[str, list[dict]]],
    dataDir: str,
    categories: list[str],
) -> list[dict[str, str]]:
    """수집 대상 rcept_no가 실제 parquet에 들어갔는지 확인한다.

    실패 시 업로드 전에 workflow를 실패시켜 HF 기존 데이터를 보호한다.
    """
    from dartlab.core.dataConfig import DATA_RELEASES

    failures: list[dict[str, str]] = []

    for cat in categories:
        if cat not in DATA_RELEASES:
            continue
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        for stockCode, perCat in targetFilings.items():
            rows = perCat.get(cat, [])
            if not rows:
                continue

            expected: list[dict] = []
            for row in rows:
                rceptNo = str(row.get("rcept_no", "") or "")
                if not rceptNo:
                    continue
                if cat in ("finance", "report") and _reportNmToFinanceKey(str(row.get("report_nm", ""))) is None:
                    continue
                expected.append(row)

            if not expected:
                continue

            existing = _existingRceptNos(localDir, stockCode)
            for row in expected:
                rceptNo = str(row.get("rcept_no", "") or "")
                if rceptNo in existing:
                    continue
                failures.append(
                    {
                        "category": cat,
                        "stockCode": stockCode,
                        "rceptNo": rceptNo,
                        "reportNm": str(row.get("report_nm", "")),
                        "rceptDt": str(row.get("rcept_dt", "")),
                    }
                )

    return failures


def _syncMaxWorkers(default: int = 4) -> int | None:
    """최근 동기화에서 DART report API 동시성을 제한한다."""
    raw = os.environ.get("SYNC_MAX_WORKERS", "").strip()
    if not raw:
        return default
    if raw.lower() in {"0", "none", "all"}:
        return None
    try:
        workers = int(raw)
    except ValueError:
        return default
    return workers if workers > 0 else default


def _syncCheckpointEvery(default: int = 100) -> int:
    """batchCollect 의 checkpoint upload 단위 (종목 수). 0 이면 비활성."""
    raw = os.environ.get("SYNC_CHECKPOINT_EVERY", "").strip()
    if not raw:
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    return max(0, v)


def _makeCheckpointUploader(cat: str) -> "callable":
    """cat 단위 checkpoint upload 콜백 — 종목 N 개마다 HF 에 incremental upload.

    cancel/timeout 안전망: drain 된 종목까지는 HF 에 안전 반영. 나머지는 다음 sync 의
    rcept_no 비교로 자연 retry. 90 분 timeout 사고 (2026-05-16) 의 root cause fix —
    이전엔 main() 끝까지 가야 yml 의 Upload step 진입했고 cancel 시 0 건 반영됐다.
    """
    import subprocess

    scriptDir = Path(__file__).resolve().parent
    distDir = Path("dist")
    uploadScript = scriptDir / "uploadData.py"

    def _upload(stockCodes: list[str]) -> None:
        if not stockCodes:
            return
        distDir.mkdir(exist_ok=True)
        files = [f"{code}.parquet" for code in stockCodes]

        # 누적 changed_<cat>.txt: hash 감지 단계의 final 결과와 합쳐서 yml Upload step 이
        # 마지막 잔여분도 잡을 수 있게 한다.
        catPath = distDir / f"changed_{cat}.txt"
        existing = set(catPath.read_text(encoding="utf-8").splitlines()) if catPath.exists() else set()
        catPath.write_text("\n".join(sorted(existing | set(files))) + "\n", encoding="utf-8")

        # checkpoint batch 만 changed.txt → uploadData 가 그것만 HF push.
        (distDir / "changed.txt").write_text("\n".join(files) + "\n", encoding="utf-8")

        env = os.environ.copy()
        env["SYNC_CATEGORY"] = cat
        rc = subprocess.run(
            [sys.executable, "-X", "utf8", "-u", str(uploadScript), "--target", "hf"],
            env=env,
            check=False,
        ).returncode
        if rc != 0:
            print(f"[checkpoint] {cat}: upload rc={rc} (batch_size={len(files)})", flush=True)
        else:
            print(f"[checkpoint] {cat}: {len(files)}개 HF upload OK", flush=True)

    return _upload


def main():
    keys = os.environ.get("DART_API_KEYS", "")
    if not keys:
        print("DART_API_KEYS 환경변수가 필요합니다.")
        sys.exit(1)

    # 2개월 기본 — list.json에 있는데 finance/report에 없는 것만 수집한다.
    # 짧으면 정정 보고서 + 늦은 제출을 놓친다. rcept_no 누락 검사가 정확하므로
    # 길어도 비용은 사실상 list.json 페이징뿐.
    lookbackDays = int(os.environ.get("SYNC_LOOKBACK_DAYS", "60"))
    categories = [c.strip() for c in os.environ.get("SYNC_CATEGORIES", "finance,report").split(",") if c.strip()]
    invalid = [cat for cat in categories if cat not in {"finance", "report"}]
    if invalid:
        raise SystemExit(f"[syncRecent] retired categories are not supported: {invalid}")

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")
    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    print(f"[syncRecent] lookback={lookbackDays}일, categories={categories}, dataDir={dataDir}")

    # 0단계: 이전 실행에서 잘린/실패 종목 우선 회수
    # pending.txt: API 한도 초과로 큐에 남은 종목
    # failures.json: 네트워크·파싱 등 에러로 실패한 종목 (자동 재시도)
    stateDir = _stateDir(dataDir)
    pendingPath = stateDir / "pending.txt"
    failuresPath = stateDir / "failures.json"

    pendingCodes: set[str] = set()
    if pendingPath.exists():
        pendingCodes = set(
            line.strip() for line in pendingPath.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        if pendingCodes:
            print(f"[syncRecent] 이전 실행 pending: {len(pendingCodes)}개 종목 우선 처리")

    if failuresPath.exists():
        try:
            import json as _json

            prevFailures = _json.loads(failuresPath.read_text(encoding="utf-8"))
            if isinstance(prevFailures, dict):
                retryCodes = set(prevFailures.keys())
                newToRetry = retryCodes - pendingCodes
                if newToRetry:
                    pendingCodes |= newToRetry
                    print(f"[syncRecent] 이전 실행 failures: {len(newToRetry)}개 종목 재시도 추가")
        except (OSError, ValueError):
            pass

    # 1단계: 새 보고서가 있는 종목 발견
    targetCodes, targetFilings = _discoverNewFilings(keys, lookbackDays, dataDir)

    # pending과 합침 (우선)
    targetCodes = targetCodes | pendingCodes

    if not targetCodes:
        print("[syncRecent] 수집 대상 없음 → 종료")
        distDir = Path("dist")
        distDir.mkdir(exist_ok=True)
        for cat in categories:
            (distDir / f"changed_{cat}.txt").write_text("", encoding="utf-8")
        (distDir / "changed.txt").write_text("", encoding="utf-8")
        return

    # 2단계: 기존 데이터 확보 (HF에서 다운로드)
    from dartlab.core.dataConfig import DATA_RELEASES

    for cat in categories:
        _cloneCategory(cat, dataDir, targetCodes)

    # 3단계: 수집 전 해시 스냅샷
    allBeforeHashes: dict[str, dict[str, str]] = {}
    for cat in categories:
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        allBeforeHashes[cat] = _snapshotHashes(localDir, targetCodes)

    # 4단계: 카테고리별 수집
    startTime = time.time()

    # 카테고리별 정확히 누락된 종목 + (year, reprt_code) 만 수집한다.
    # finance/report는 batchCollect.
    def _periodsFor(cat: str) -> tuple[list[str], dict[str, list[tuple[str, str]]]]:
        """cat에서 누락이 있는 종목 + 그 종목의 누락 (year, reprt_code) list."""
        codes: list[str] = []
        periods: dict[str, list[tuple[str, str]]] = {}
        for sc, perCat in targetFilings.items():
            rows = perCat.get(cat, [])
            if not rows:
                continue
            ks: set[tuple[str, str]] = set()
            for r in rows:
                k = _reportNmToFinanceKey(r["report_nm"])
                if k is not None:
                    ks.add(k)
            if ks:
                codes.append(sc)
                periods[sc] = sorted(ks)
        return codes, periods

    nonDocsCats = categories
    if nonDocsCats:
        from dartlab.gather.dart.batch import batchCollect

        maxWorkers = _syncMaxWorkers()
        checkpointEvery = _syncCheckpointEvery()

        # finance/report 각각 독립적으로 누락 종목만 수집.
        # 한 카테고리만 누락이면 다른 카테고리는 건드리지 않는다.
        for cat in nonDocsCats:
            codes, periods = _periodsFor(cat)
            if not codes:
                print(f"[syncRecent] {cat}: 누락 없음 → 스킵")
                continue
            print(
                f"[syncRecent] {cat}: {len(codes)}개 종목 수집 시작 (checkpoint={checkpointEvery or 'off'})",
                flush=True,
            )
            batchCollect(
                codes,
                categories=[cat],
                incremental=True,
                showProgress=False,
                targetPeriodsByCode=periods,
                maxWorkers=maxWorkers,
                onCheckpoint=_makeCheckpointUploader(cat) if checkpointEvery > 0 else None,
                checkpointEvery=checkpointEvery,
            )

    verifyFailures = _verifyCollectedRcepts(targetFilings, dataDir, categories)
    if verifyFailures:
        import json

        distDir = Path("dist")
        distDir.mkdir(exist_ok=True)
        failPath = distDir / "sync_verification_failed.json"
        failPath.write_text(json.dumps(verifyFailures, ensure_ascii=False, indent=2), encoding="utf-8")
        # checkpoint upload (df6dbd37a) 도입 이후 verify 는 fail-safe 가 아닌 추적용.
        # 수집된 종목은 이미 incremental 로 HF push 완료, 잔여 missing 은 다음 sync 의
        # rcept_no 비교에서 자연 retry. 옛 동작 (sys.exit(1)) 은 정상 push 후에도
        # workflow fail 처리해 monitor 알림 다발 + cron 깨짐.
        print(f"[syncRecent] 수집 후 검증 잔여 누락: {len(verifyFailures)}건 — 다음 sync 자연 회복")
        for item in verifyFailures[:20]:
            print(f"[syncRecent] pending {item['category']} {item['stockCode']} {item['rceptNo']} {item['reportNm']}")
        if len(verifyFailures) > 20:
            print(f"[syncRecent] ... 외 {len(verifyFailures) - 20}건")

    elapsed = time.time() - startTime

    # pending.txt 비움 — collector가 새로 exhausted되면 batchCollect가 새 pending.txt를 작성
    if pendingPath.exists():
        try:
            pendingPath.unlink()
        except OSError:
            pass

    # 5단계: 변경 파일 감지
    allChanged: dict[str, list[str]] = {}
    allNew: dict[str, list[str]] = {}

    for cat in categories:
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        afterHashes = _snapshotHashes(localDir, targetCodes)
        beforeHashes = allBeforeHashes[cat]

        newFiles = [f for f in afterHashes if f not in beforeHashes]
        updatedFiles = [f for f in afterHashes if f in beforeHashes and afterHashes[f] != beforeHashes[f]]
        allNew[cat] = newFiles
        allChanged[cat] = newFiles + updatedFiles

    # 카테고리별 changed.txt 기록
    distDir = Path("dist")
    distDir.mkdir(exist_ok=True)

    totalChanged = 0
    for cat in categories:
        changedPath = distDir / f"changed_{cat}.txt"
        changedPath.write_text("\n".join(allChanged[cat]), encoding="utf-8")
        totalChanged += len(allChanged[cat])

    # 통합 changed.txt (uploadData.py 호환)
    allChangedFlat = []
    for cat in categories:
        allChangedFlat.extend(allChanged[cat])
    (distDir / "changed.txt").write_text("\n".join(allChangedFlat), encoding="utf-8")

    print(f"[syncRecent] 완료: {len(targetCodes)}개 종목, {elapsed:.0f}초")
    for cat in categories:
        print(f"[syncRecent] {cat}: 신규 {len(allNew[cat])}개 + 업데이트 {len(allChanged[cat]) - len(allNew[cat])}개")

    # GitHub Actions summary
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as f:
            f.write(f"## Daily Sync (최근 {lookbackDays}일 공시)\n\n")
            f.write("| 항목 | 값 |\n|------|----|\n")
            f.write(f"| 카테고리 | {', '.join(categories)} |\n")
            f.write(f"| 수집 대상 | {len(targetCodes)}개 |\n")
            f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")
            for cat in categories:
                changed = len(allChanged[cat])
                f.write(f"| {cat} 변경 | {changed}개 |\n")
            f.write(f"| 총 변경 파일 | {totalChanged}개 |\n")


if __name__ == "__main__":
    main()
