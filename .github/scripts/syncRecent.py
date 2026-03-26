"""경량 일일 동기화 — 최근 공시가 있던 종목만 증분 수집.

흐름:
  1. DART list.json으로 최근 N일 정기공시 조회 (API 1회)
  2. 사업보고서/반기보고서/분기보고서 필터링
  3. 해당 종목코드만 추출 → 증분 수집
  4. 변경 파일만 changed.txt에 기록

환경변수:
  DART_API_KEYS: DART OpenAPI 키 (쉼표 구분)
  SYNC_LOOKBACK_DAYS: 조회 기간 (기본: 7일)
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time
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


def _findRecentFilings(keys: str, lookbackDays: int) -> set[str]:
    """최근 N일 정기공시에서 대상 종목코드 추출."""
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.disclosure import listFilings

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
        return set()

    # 사업보고서 / 반기보고서 / 분기보고서만
    reportFilter = r"사업보고서|반기보고서|분기보고서"
    filings = filings.filter(
        pl.col("report_nm").str.contains(reportFilter)
    )

    if filings.height == 0:
        print("[syncRecent] 대상 보고서 없음")
        return set()

    # stock_code가 있는 행만 (상장사)
    filings = filings.filter(
        pl.col("stock_code").is_not_null()
        & (pl.col("stock_code") != "")
        & (pl.col("stock_code") != " ")
    )

    codes = set(filings["stock_code"].unique().to_list())
    reportNames = filings["report_nm"].unique().to_list()

    print(f"[syncRecent] 최근 {lookbackDays}일 정기공시: {filings.height}건, {len(codes)}개 종목")
    print(f"[syncRecent] 보고서 유형: {reportNames}")

    return codes


def main():
    keys = os.environ.get("DART_API_KEYS", "")
    if not keys:
        print("DART_API_KEYS 환경변수가 필요합니다.")
        sys.exit(1)

    lookbackDays = int(os.environ.get("SYNC_LOOKBACK_DAYS", "7"))

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")
    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    print(f"[syncRecent] lookback={lookbackDays}일, dataDir={dataDir}")

    # 1단계: 최근 공시 조회 (API 1회)
    targetCodes = _findRecentFilings(keys, lookbackDays)

    if not targetCodes:
        print("[syncRecent] 수집 대상 없음 → 종료")
        # 빈 changed.txt
        distDir = Path("dist")
        distDir.mkdir(exist_ok=True)
        (distDir / "changed.txt").write_text("", encoding="utf-8")
        return

    print(f"[syncRecent] 수집 대상: {len(targetCodes)}개 종목")

    # 2단계: 대상 종목 기존 데이터 확보 (캐시 없으면 HF에서 개별 다운로드)
    categories = ["finance", "report", "docs"]
    for cat in categories:
        _cloneCategory(cat, dataDir, targetCodes)

    # 3단계: 수집 전 해시 스냅샷
    from dartlab.core.dataConfig import DATA_RELEASES
    allBeforeHashes: dict[str, dict[str, str]] = {}
    for cat in categories:
        localDir = Path(dataDir) / DATA_RELEASES[cat]["dir"]
        allBeforeHashes[cat] = _snapshotHashes(localDir, targetCodes)

    # 4단계: 대상 종목만 증분 수집
    start = time.time()

    from dartlab.providers.dart.openapi.batch import batchCollect

    results = batchCollect(
        list(targetCodes),
        categories=categories,
        incremental=True,
        showProgress=False,
    )

    elapsed = time.time() - start

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

    totalRows = sum(
        sum(r.get(cat, 0) for cat in categories)
        for r in results.values()
    )
    print(f"[syncRecent] 완료: {len(results)}개 종목, {totalRows}행, {elapsed:.0f}초")
    for cat in categories:
        print(f"[syncRecent] {cat}: 신규 {len(allNew[cat])}개 + 업데이트 {len(allChanged[cat]) - len(allNew[cat])}개")

    # GitHub Actions summary
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as f:
            f.write(f"## Daily Sync (최근 {lookbackDays}일 공시)\n\n")
            f.write(f"| 항목 | 값 |\n|------|----|\n")
            f.write(f"| 대상 종목 | {len(targetCodes)}개 |\n")
            f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")
            for cat in categories:
                changed = len(allChanged[cat])
                f.write(f"| {cat} 변경 | {changed}개 |\n")
            f.write(f"| 총 변경 파일 | {totalChanged}개 |\n")


if __name__ == "__main__":
    main()
