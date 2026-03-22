"""
실험 ID: 001
실험명: SEC EDGAR 벌크 데이터 덤프 + polars 변환

목적:
- companyfacts.zip 벌크 다운로드 → CIK별 JSON → polars parquet 변환
- 데이터 경로를 dartlab의 config.dataDir / edgarData/ 에 저장
- eddmpython bulkDownloader.py 로직을 polars only로 재현
- 변환된 데이터 구조 분석 (AAPL/MSFT/NVDA 샘플)

가설:
1. companyfacts.zip에서 전체 CIK JSON을 받아 parquet으로 변환할 수 있다
2. polars만으로 JSON→DataFrame→parquet 변환이 가능하다 (pandas 없이)
3. 변환된 parquet에서 주요 재무 태그가 정상적으로 존재한다

방법:
1. companyfacts.zip 다운로드 (~2GB compressed, 해제 후 ~30GB)
2. CIK별 JSON → polars DataFrame → parquet 변환 (multiprocessing)
3. config.dataDir / edgarData/ 에 저장
4. AAPL/MSFT/NVDA 샘플로 구조 분석

결과 (실험 후 작성):
- 다운로드: companyfacts.zip 1.36GB, 19,293개 CIK JSON 추출
- 변환: 16,601개 parquet 성공, 2,692개 데이터 없음, 에러 0건
- 전체 크기: 665 MB (0.6 GB)
- 변환 속도: 8코어 병렬, ~2분 22초 (평균 135 it/s)
- AAPL: 24,579 rows, 503 us-gaap tags, fy 2009~2026, 핵심 태그 7/7
- MSFT: 31,574 rows, 543 us-gaap tags, fy 2010~2026, 핵심 태그 7/7
- NVDA: 26,571 rows, 625 us-gaap tags, fy 2009~2026, 핵심 태그 7/7
- fp 분포: FY > Q3 > Q2 > Q1 (분기별 데이터 존재)
- 주의: start 컬럼이 전부 null인 CIK 존재 → dtype 체크 필수

결론:
- 가설 1 채택: companyfacts.zip → CIK별 parquet 변환 성공
- 가설 2 채택: polars only로 JSON→DataFrame→parquet 전 과정 처리 가능
- 가설 3 채택: 핵심 재무 태그 (Revenue, NetIncome, Assets 등) 7/7 모두 존재
- SEC User-Agent 형식: "{name} {email}" 필수 (403 방지)
- 캐시 로직: 24시간 + UTC 08:10 업데이트 시간 기준으로 재다운로드 판단

실험일: 2026-03-10
"""

import datetime
import json
import multiprocessing
import shutil
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timezone
from pathlib import Path

import polars as pl
import requests
from tqdm import tqdm

SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar"
SEC_FILES_BASE = "https://www.sec.gov/files"
BULK_FINANCE_URL = f"{SEC_ARCHIVES_BASE}/daily-index/xbrl/companyfacts.zip"
TICKERS_URL = f"{SEC_FILES_BASE}/company_tickers.json"
SEC_HEADERS = {"User-Agent": "dartlab o12486vs2@gmail.com"}

UPDATE_TIME_UTC = {"hour": 8, "minute": 10}


def _getEdgarDir() -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from dartlab import config
    edgarDir = Path(config.dataDir) / "edgarData"
    edgarDir.mkdir(parents=True, exist_ok=True)
    return edgarDir


def processJsonFile(args: tuple[Path, Path]) -> str:
    jsonFilePath, parquetDir = args

    cik = jsonFilePath.stem.replace("CIK", "")
    rows = []

    with open(jsonFilePath, "r") as f:
        data = json.load(f)

    if "facts" not in data:
        return f"no facts: {jsonFilePath.name}"

    entityName = data.get("entityName", "")

    for namespace, concepts in data["facts"].items():
        for tag, tagData in concepts.items():
            label = tagData.get("label", "")

            if "units" not in tagData:
                continue

            for unit, factsList in tagData["units"].items():
                for fact in factsList:
                    rows.append({
                        "cik": cik,
                        "entityName": entityName,
                        "namespace": namespace,
                        "tag": tag,
                        "label": label,
                        "unit": unit,
                        "val": fact.get("val"),
                        "fy": fact.get("fy"),
                        "fp": fact.get("fp"),
                        "form": fact.get("form"),
                        "filed": fact.get("filed"),
                        "frame": fact.get("frame"),
                        "start": fact.get("start"),
                        "end": fact.get("end"),
                        "accn": fact.get("accn"),
                    })

    if not rows:
        return f"no data: {jsonFilePath.name}"

    df = pl.DataFrame(rows, infer_schema_length=None)

    df = df.with_columns([
        pl.col("val").cast(pl.Float64, strict=False),
        pl.col("fy").cast(pl.Int32, strict=False),
    ])

    for dateCol in ["filed", "start", "end"]:
        if dateCol in df.columns and df[dateCol].dtype == pl.Utf8:
            df = df.with_columns(
                pl.col(dateCol).str.to_date(format="%Y-%m-%d", strict=False)
            )

    parquetFile = parquetDir / f"{cik}.parquet"
    df.write_parquet(parquetFile)
    return f"completed: {parquetFile.name} ({len(rows)} rows)"


def checkNeedUpdate(cacheFile: Path) -> bool:
    if not cacheFile.exists():
        return True

    with open(cacheFile, "r") as f:
        cachedTimeStr = f.read().strip()

    fileModifiedTime = datetime.datetime.fromisoformat(cachedTimeStr)
    currentUtc = datetime.datetime.now(timezone.utc)

    if (currentUtc - fileModifiedTime).total_seconds() < 24 * 60 * 60:
        return False

    todayUpdateTime = currentUtc.replace(
        hour=UPDATE_TIME_UTC["hour"],
        minute=UPDATE_TIME_UTC["minute"],
        second=0,
        microsecond=0,
    )

    if fileModifiedTime < todayUpdateTime and currentUtc >= todayUpdateTime:
        return True

    return False


def downloadBulk(edgarDir: Path, force: bool = False) -> Path:
    financeDir = edgarDir / "finance"
    tempDir = edgarDir / "temp" / "finance"
    cacheFile = edgarDir / "bulkCacheFinance.txt"

    financeDir.mkdir(parents=True, exist_ok=True)

    parquetFiles = list(financeDir.glob("*.parquet"))
    hasData = len(parquetFiles) > 0

    pendingJsonFiles = list(tempDir.glob("CIK*.json")) if tempDir.exists() else []
    hasPendingConversion = len(pendingJsonFiles) > 0

    if hasPendingConversion:
        existingCiks = {p.stem.lstrip("0") or "0" for p in parquetFiles}
        pendingJsonFiles = [
            j for j in pendingJsonFiles
            if (j.stem.replace("CIK", "").lstrip("0") or "0") not in existingCiks
        ]
        print(f"[EDGAR] 미변환 JSON 발견: {len(pendingJsonFiles)}개 (기변환: {len(parquetFiles)}개)")
    elif not force and hasData and not checkNeedUpdate(cacheFile):
        print(f"[EDGAR] 캐시 유효 — {len(parquetFiles)}개 parquet 이미 존재")
        return financeDir
    else:
        tempDir.mkdir(parents=True, exist_ok=True)
        zipFilePath = tempDir / "companyfacts.zip"

        if not hasData:
            print("[EDGAR] Bulk 초기 다운로드 시작...")
        else:
            print("[EDGAR] Bulk 업데이트 다운로드...")

        response = requests.get(BULK_FINANCE_URL, headers=SEC_HEADERS, stream=True)
        response.raise_for_status()

        totalSize = int(response.headers.get("content-length", 0))

        with open(zipFilePath, "wb") as f:
            with tqdm(total=totalSize, unit="B", unit_scale=True, desc="Download") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print("Extracting...")
        with zipfile.ZipFile(zipFilePath, "r") as zipRef:
            fileList = zipRef.namelist()
            print(f"  archive 내 파일: {len(fileList)}")

            for fileName in tqdm(fileList, desc="Extracting"):
                zipRef.extract(fileName, tempDir)

        print("zip 파일 삭제...")
        zipFilePath.unlink()

        currentUtc = datetime.datetime.now(timezone.utc)
        with open(cacheFile, "w") as f:
            f.write(currentUtc.isoformat())

        pendingJsonFiles = list(tempDir.glob("CIK*.json"))

    print("polars parquet 변환...")
    jsonFiles = pendingJsonFiles
    print(f"  JSON 파일: {len(jsonFiles)}")

    numProcesses = min(multiprocessing.cpu_count(), 8)
    print(f"  병렬 프로세스: {numProcesses}")

    args = [(jsonFile, financeDir) for jsonFile in jsonFiles]

    with ProcessPoolExecutor(max_workers=numProcesses) as executor:
        futures = {executor.submit(processJsonFile, arg): arg for arg in args}

        results = []
        for future in tqdm(as_completed(futures), total=len(futures), desc="Converting"):
            try:
                result = future.result()
            except Exception as e:
                result = f"error: {e}"
            results.append(result)

    completed = [r for r in results if r.startswith("completed:")]
    errors = [r for r in results if r.startswith("error")]
    noData = [r for r in results if r.startswith("no")]

    print(f"\n변환 완료!")
    print(f"  성공: {len(completed)}")
    print(f"  데이터 없음: {len(noData)}")
    print(f"  에러: {len(errors)}")
    if errors:
        for e in errors[:5]:
            print(f"    {e}")

    if len(errors) == 0:
        print("temp 정리...")
        shutil.rmtree(tempDir)
    else:
        print(f"  에러 {len(errors)}건 — temp 보존 (재실행으로 미변환분 처리 가능)")

    finalCount = len(list(financeDir.glob("*.parquet")))
    print(f"\n[EDGAR] Bulk 완료 — {finalCount}개 parquet")

    return financeDir


def getTickerMap() -> dict[str, str]:
    print("ticker↔CIK 매핑 다운로드...")
    resp = requests.get(TICKERS_URL, headers=SEC_HEADERS)
    resp.raise_for_status()

    tickerToCik = {}
    for entry in resp.json().values():
        ticker = entry["ticker"]
        cik = str(entry["cik_str"]).zfill(10)
        tickerToCik[ticker] = cik

    print(f"  {len(tickerToCik)}개 ticker 로드")
    return tickerToCik


def analyzeSample(financeDir: Path, tickerToCik: dict[str, str]):
    sampleTickers = ["AAPL", "MSFT", "NVDA"]

    for ticker in sampleTickers:
        cik = tickerToCik.get(ticker)
        if not cik:
            print(f"\n{ticker}: CIK 없음")
            continue

        parquetPath = financeDir / f"{cik}.parquet"

        if not parquetPath.exists():
            print(f"\n{ticker} (CIK={cik}): parquet 없음")
            continue

        df = pl.read_parquet(parquetPath)
        print(f"\n=== {ticker} (CIK={cik}) ===")
        print(f"  rows: {df.height}, columns: {df.width}")
        print(f"  entityName: {df.select('entityName').unique().to_series().to_list()}")

        usGaap = df.filter(pl.col("namespace") == "us-gaap")
        print(f"  us-gaap tags: {usGaap.select('tag').unique().height}")

        fyRange = df.filter(pl.col("fy").is_not_null())
        if fyRange.height > 0:
            print(f"  fy 범위: {fyRange['fy'].min()} ~ {fyRange['fy'].max()}")

        fpCounts = df.group_by("fp").len().sort("len", descending=True)
        print(f"  fp 분포:")
        for row in fpCounts.head(8).iter_rows(named=True):
            print(f"    {row['fp']}: {row['len']}")

        keyTags = [
            "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "NetIncomeLoss", "Assets", "StockholdersEquity",
            "OperatingIncomeLoss", "CashAndCashEquivalentsAtCarryingValue",
        ]
        existingTags = usGaap.select("tag").unique().to_series().to_list()
        print(f"  핵심 태그:")
        for tag in keyTags:
            mark = "O" if tag in existingTags else "X"
            count = usGaap.filter(pl.col("tag") == tag).height
            print(f"    [{mark}] {tag} ({count})")

        sizeMb = parquetPath.stat().st_size / 1024 / 1024
        print(f"  parquet 크기: {sizeMb:.1f} MB")


def main():
    edgarDir = _getEdgarDir()
    print(f"[EDGAR] 데이터 경로: {edgarDir}")

    financeDir = downloadBulk(edgarDir, force=False)

    tickerToCik = getTickerMap()
    analyzeSample(financeDir, tickerToCik)

    totalParquets = len(list(financeDir.glob("*.parquet")))
    totalSizeMb = sum(f.stat().st_size for f in financeDir.glob("*.parquet")) / 1024 / 1024
    print(f"\n=== 전체 요약 ===")
    print(f"  parquet 파일: {totalParquets}개")
    print(f"  전체 크기: {totalSizeMb:.0f} MB ({totalSizeMb/1024:.1f} GB)")


if __name__ == "__main__":
    main()
