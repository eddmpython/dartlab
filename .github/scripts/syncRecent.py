"""경량 일일 동기화 — 새 정기보고서가 올라온 종목만 증분 수집.

흐름:
  1. DART list.json으로 최근 N일 정기공시 조회 (API 1회)
  2. 사업보고서/반기보고서/분기보고서 필터링
  3. 기존 docs parquet의 rcept_no와 비교 → 새 보고서가 있는 종목만 추출
  4. 해당 종목만 증분 수집 + 변경 파일 기록

환경변수:
  DART_API_KEYS: DART OpenAPI 키 (쉼표 구분)
  SYNC_LOOKBACK_DAYS: 조회 기간 (기본: 7일)
  SYNC_CATEGORIES: 수집 카테고리 (기본: finance,report,docs)
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

import asyncio
import hashlib
import io
import os
import re
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path


def _fileHash(path: Path) -> str:
    """파일 SHA-256 해시 (첫 64KB + 파일크기)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(65536))
        h.update(str(path.stat().st_size).encode())
    return h.hexdigest()


def _snapshotHashes(directory: Path, targets: set[str]) -> dict[str, str]:
    """특정 종목코드 파일만 해시 스냅샷."""
    result = {}
    for sc in targets:
        p = directory / f"{sc}.parquet"
        if p.exists():
            result[p.name] = _fileHash(p)
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


def _existingRceptNos(docsDir: Path, stockCode: str) -> set[str]:
    """기존 docs parquet에서 rcept_no 집합 추출."""
    import polars as pl

    path = docsDir / f"{stockCode}.parquet"
    if not path.exists():
        return set()
    try:
        df = pl.scan_parquet(path).select("rcept_no").collect()
        return set(df["rcept_no"].unique().to_list())
    except (pl.exceptions.ComputeError, OSError):
        return set()


def _discoverNewFilings(
    keys: str, lookbackDays: int, dataDir: str
) -> tuple[set[str], dict[str, list[dict]]]:
    """최근 N일 정기공시에서 새 보고서 있는 종목 + rcept_no 매핑 반환.

    Returns:
        (targetCodes, codeToFilings)
        codeToFilings: {stockCode: [{rcept_no, rcept_dt, report_nm, corp_code, corp_name}, ...]}
    """
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.disclosure import listFilings
    from dartlab.core.dataConfig import DATA_RELEASES

    import polars as pl

    end = datetime.now()
    start = end - timedelta(days=lookbackDays)

    client = DartClient(apiKey=keys.split(",")[0].strip())

    filings = listFilings(
        client,
        corp=None,
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
        filingType="A",
        fetchAll=True,
    )

    if filings.height == 0:
        print("[syncRecent] 최근 정기공시 없음")
        return set(), {}

    reportFilter = r"^(사업보고서|반기보고서|분기보고서|\[기재정정\]|\[첨부정정\]|\[첨부추가\])"
    filtered = filings.filter(
        pl.col("report_nm").str.contains(reportFilter)
        & pl.col("stock_code").is_not_null()
        & (pl.col("stock_code") != "")
        & (pl.col("stock_code") != " ")
    )

    if filtered.height == 0:
        print("[syncRecent] 대상 보고서 없음")
        return set(), {}

    allCandidateCodes = set(filtered["stock_code"].unique().to_list())

    # docs parquet만 먼저 확보 (비교용)
    _cloneCategory("docs", dataDir, allCandidateCodes)

    # 종목별 filing 매핑
    codeToFilings: dict[str, list[dict]] = {}
    for row in filtered.iter_rows(named=True):
        sc = row["stock_code"]
        codeToFilings.setdefault(sc, []).append(row)

    # 기존 docs와 비교 → 새 rcept_no가 있는 종목만
    docsDir = Path(dataDir) / DATA_RELEASES["docs"]["dir"]
    targetCodes: set[str] = set()
    targetFilings: dict[str, list[dict]] = {}

    for sc, rows in codeToFilings.items():
        existing = _existingRceptNos(docsDir, sc)
        newRows = [r for r in rows if r["rcept_no"] not in existing]
        if newRows:
            targetCodes.add(sc)
            targetFilings[sc] = newRows

    skipped = len(allCandidateCodes) - len(targetCodes)
    reportNames = filtered["report_nm"].unique().to_list()
    print(f"[syncRecent] 최근 {lookbackDays}일 정기공시: {filtered.height}건, {len(allCandidateCodes)}개 종목")
    print(f"[syncRecent] 보고서 유형: {reportNames}")
    print(f"[syncRecent] 새 보고서 있는 종목: {len(targetCodes)}개 (이미 최신: {skipped}개 스킵)")

    return targetCodes, targetFilings


# ── docs 직접 수집 (listing API 재조회 없이 rcept_no로 직접 ZIP 다운로드) ──


async def _collectDocsDirect(
    targetFilings: dict[str, list[dict]],
    dataDir: str,
    keys: str,
) -> dict[str, int]:
    """이미 발견한 rcept_no들의 ZIP만 직접 다운로드 + 파싱.

    batchCollect._collectDocs와 달리 per-stock listing API를 호출하지 않는다.
    이것이 타임아웃의 근본 원인이었음.
    """
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.providers.dart.openapi.batch import AsyncDartClient
    from dartlab.providers.dart.openapi.zipCollector import _parseSections

    import polars as pl

    docsDir = Path(dataDir) / DATA_RELEASES["docs"]["dir"]
    docsDir.mkdir(parents=True, exist_ok=True)

    apiKey = keys.split(",")[0].strip()
    client = AsyncDartClient(apiKey)

    # 모든 filing을 flat list로 변환
    allJobs: list[tuple[str, dict]] = []
    for sc, rows in targetFilings.items():
        for row in rows:
            allJobs.append((sc, row))

    total = len(allJobs)
    doneCount = [0]
    failCount = [0]
    stockSections: dict[str, list[dict]] = {}  # stockCode → sections

    sem = asyncio.Semaphore(6)  # 동시 6개 다운로드

    async def _fetchOne(stockCode: str, row: dict) -> None:
        if client.exhausted:
            return

        rceptNo = row["rcept_no"]
        rceptDt = row.get("rcept_dt", "")
        reportNm = row.get("report_nm", "")
        corpCode = row.get("corp_code", "")
        corpName = row.get("corp_name", stockCode)

        ym = re.search(r"\((\d{4})\.\d{2}\)", reportNm)
        year = ym.group(1) if ym else rceptDt[:4]

        try:
            raw = await client.getBytes("document.xml", {"rcept_no": rceptNo})
        except Exception:
            failCount[0] += 1
            doneCount[0] += 1
            return

        if raw is None:
            failCount[0] += 1
            doneCount[0] += 1
            return

        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            failCount[0] += 1
            doneCount[0] += 1
            return

        names = zf.namelist()
        if not names:
            failCount[0] += 1
            doneCount[0] += 1
            return

        largest = max(names, key=lambda n: zf.getinfo(n).file_size)
        content = zf.read(largest)

        xmlContent = None
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                xmlContent = content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if xmlContent is None:
            xmlContent = content.decode("utf-8", errors="replace")

        loop = asyncio.get_event_loop()
        sections = await loop.run_in_executor(None, _parseSections, xmlContent)

        if stockCode not in stockSections:
            stockSections[stockCode] = []

        for s in sections:
            stockSections[stockCode].append(
                {
                    "corp_code": corpCode,
                    "corp_name": corpName,
                    "stock_code": stockCode,
                    "year": year,
                    "rcept_date": rceptDt,
                    "rcept_no": rceptNo,
                    "report_type": reportNm,
                    "section_order": s["order"],
                    "section_title": s["title"],
                    "section_url": "",
                    "section_content": s["content"],
                }
            )

        doneCount[0] += 1
        if doneCount[0] % 10 == 0 or doneCount[0] == total:
            print(f"[syncRecent] docs: {doneCount[0]}/{total} 완료 (실패: {failCount[0]})")

    async def _guarded(stockCode: str, row: dict) -> None:
        async with sem:
            try:
                await asyncio.wait_for(_fetchOne(stockCode, row), timeout=120)
            except asyncio.TimeoutError:
                failCount[0] += 1
                doneCount[0] += 1
                print(f"[syncRecent] docs 타임아웃: {stockCode} {row.get('rcept_no', '?')}")

    await asyncio.gather(*[_guarded(sc, row) for sc, row in allJobs])
    await client.close()

    # 종목별 parquet 저장
    results: dict[str, int] = {}
    for sc, sections in stockSections.items():
        if not sections:
            continue

        parquetPath = docsDir / f"{sc}.parquet"
        newDf = pl.DataFrame(sections)

        if parquetPath.exists():
            try:
                existingDf = pl.read_parquet(parquetPath)
                combinedDf = pl.concat([existingDf, newDf], how="diagonal_relaxed")
            except (pl.exceptions.ComputeError, OSError):
                combinedDf = newDf
        else:
            combinedDf = newDf

        tmpPath = parquetPath.with_suffix(".parquet.tmp")
        combinedDf.write_parquet(tmpPath)
        if parquetPath.exists():
            parquetPath.unlink()
        tmpPath.rename(parquetPath)

        results[sc] = len(sections)

    print(f"[syncRecent] docs 직접 수집 완료: {len(results)}개 종목, {sum(results.values())}개 섹션")
    return results


def main():
    keys = os.environ.get("DART_API_KEYS", "")
    if not keys:
        print("DART_API_KEYS 환경변수가 필요합니다.")
        sys.exit(1)

    lookbackDays = int(os.environ.get("SYNC_LOOKBACK_DAYS", "7"))
    categories = [
        c.strip()
        for c in os.environ.get("SYNC_CATEGORIES", "finance,report,docs").split(",")
        if c.strip()
    ]

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")
    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    print(f"[syncRecent] lookback={lookbackDays}일, categories={categories}, dataDir={dataDir}")

    # 1단계: 새 보고서가 있는 종목 발견
    targetCodes, targetFilings = _discoverNewFilings(keys, lookbackDays, dataDir)

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
        if cat != "docs":  # docs는 _discoverNewFilings에서 이미 확보
            _cloneCategory(cat, dataDir, targetCodes)

    # 3단계: 수집 전 해시 스냅샷
    allBeforeHashes: dict[str, dict[str, str]] = {}
    for cat in categories:
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        allBeforeHashes[cat] = _snapshotHashes(localDir, targetCodes)

    # 4단계: 카테고리별 수집
    startTime = time.time()

    if "docs" in categories and len(categories) == 1:
        # docs 전용 모드: 직접 ZIP 수집 (listing API 재조회 없음)
        asyncio.run(_collectDocsDirect(targetFilings, dataDir, keys))
    elif "docs" not in categories:
        # finance/report만: batchCollect 사용
        from dartlab.providers.dart.openapi.batch import batchCollect

        batchCollect(
            list(targetCodes),
            categories=categories,
            incremental=True,
            showProgress=False,
        )
    else:
        # 혼합 모드 (fallback): batchCollect로 전체 수집
        from dartlab.providers.dart.openapi.batch import batchCollect

        batchCollect(
            list(targetCodes),
            categories=categories,
            incremental=True,
            showProgress=False,
        )

    elapsed = time.time() - startTime

    # 5단계: 변경 파일 감지
    allChanged: dict[str, list[str]] = {}
    allNew: dict[str, list[str]] = {}

    for cat in categories:
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        afterHashes = _snapshotHashes(localDir, targetCodes)
        beforeHashes = allBeforeHashes[cat]

        newFiles = [f for f in afterHashes if f not in beforeHashes]
        updatedFiles = [
            f for f in afterHashes
            if f in beforeHashes and afterHashes[f] != beforeHashes[f]
        ]
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
            f.write(f"| 항목 | 값 |\n|------|----|\n")
            f.write(f"| 카테고리 | {', '.join(categories)} |\n")
            f.write(f"| 수집 대상 | {len(targetCodes)}개 |\n")
            f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")
            for cat in categories:
                changed = len(allChanged[cat])
                f.write(f"| {cat} 변경 | {changed}개 |\n")
            f.write(f"| 총 변경 파일 | {totalChanged}개 |\n")


if __name__ == "__main__":
    main()
