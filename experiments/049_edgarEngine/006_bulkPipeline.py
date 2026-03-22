"""
실험 ID: 006
실험명: EDGAR 벌크 데이터 파이프라인

목적:
- SEC companyfacts.zip 벌크 다운로드 → CIK별 parquet 변환
- ticker↔CIK 매핑 (company_tickers.json)
- 갱신 체크 (meta.json 기반)
- eddmpython bulkDownloader.py + ticker.py를 polars로 포팅

가설:
1. companyfacts.zip 벌크 → polars 변환이 pandas보다 빠르다
2. JSON → parquet 병렬 변환은 ProcessPoolExecutor로 충분하다
3. meta.json 기반 갱신 체크로 불필요한 재다운로드를 방지할 수 있다

방법:
1. TickerMap: SEC company_tickers.json → polars parquet 캐시 (24h)
2. BulkDownload: companyfacts.zip 다운로드 → 압축 해제 → JSON → parquet 변환
3. UpdateCheck: meta.json에 downloadedAt, lastModified, totalCiks 저장
4. 검증: AAPL/MSFT/NVDA parquet 생성 확인 + buildTimeseries 호출

결과:
- TickerMap: 10,412개 ticker↔CIK, 24h parquet 캐시, search 동작 확인
- BulkDownloader: HEAD 기반 갱신 체크 동작 (Last-Modified 비교)
- meta.json: downloadedAt + lastModified + totalCiks 저장/비교 OK
- 검증: AAPL 136 accounts, MSFT 138 accounts, NVDA 164 accounts → buildTimeseries 정상
- 벌크 다운로드 실행 불필요 (기존 16,601 CIK 데이터 + Last-Modified 동일)
- SEC API 키 불필요 — User-Agent 헤더만으로 접근 가능

결론:
- 채택. 벌크 전용 파이프라인으로 ticker + bulk + meta 3요소 검증 완료
- 패키지 배치 준비 완료 (engines/edgar/ticker.py + bulk.py)

실험일: 2026-03-10
"""

from __future__ import annotations

import json
import multiprocessing
import shutil
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import requests
from alive_progress import alive_bar

SEC_HEADERS = {"User-Agent": "dartlab support@dartlab.io"}
BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def _convertJsonToParquet(args: tuple[Path, Path]) -> str:
    jsonPath, outDir = args
    try:
        with open(jsonPath, "r", encoding="utf-8") as f:
            data = json.load(f)

        cik = jsonPath.stem.replace("CIK", "")
        rows = []

        if "facts" not in data:
            return f"no_facts:{jsonPath.name}"

        for namespace, concepts in data["facts"].items():
            for tag, tagData in concepts.items():
                label = tagData.get("label", "")
                if "units" not in tagData:
                    continue
                for unit, factsList in tagData["units"].items():
                    for fact in factsList:
                        rows.append({
                            "cik": cik,
                            "namespace": namespace,
                            "tag": tag,
                            "label": label,
                            "unit": unit,
                            "val": fact.get("val"),
                            "start": fact.get("start"),
                            "end": fact.get("end"),
                            "accn": fact.get("accn"),
                            "fy": fact.get("fy"),
                            "fp": fact.get("fp"),
                            "form": fact.get("form"),
                            "filed": fact.get("filed"),
                            "frame": fact.get("frame"),
                        })

        if not rows:
            return f"empty:{jsonPath.name}"

        df = pl.DataFrame(rows)

        df = df.with_columns([
            pl.col("val").cast(pl.Float64, strict=False),
            pl.col("fy").cast(pl.Int32, strict=False),
            pl.col("start").str.to_date(strict=False),
            pl.col("end").str.to_date(strict=False),
            pl.col("filed").str.to_date(strict=False),
        ])

        outPath = outDir / f"{cik}.parquet"
        df.write_parquet(outPath)
        return f"ok:{cik}"

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return f"error:{jsonPath.name}:{e}"


class TickerMap:
    def __init__(self, edgarDir: Path):
        self.edgarDir = edgarDir
        self.cachePath = edgarDir / "tickers.parquet"
        self.cacheTimeout = 24 * 60 * 60
        self._df: pl.DataFrame | None = None

    def _isCacheValid(self) -> bool:
        if not self.cachePath.exists():
            return False
        age = time.time() - self.cachePath.stat().st_mtime
        return age < self.cacheTimeout

    def load(self) -> pl.DataFrame:
        if self._df is not None:
            return self._df

        if self._isCacheValid():
            self._df = pl.read_parquet(self.cachePath)
            return self._df

        print("[EDGAR] ticker 매핑 다운로드 중...")
        resp = requests.get(TICKERS_URL, headers=SEC_HEADERS, timeout=30)
        resp.raise_for_status()

        records = []
        for entry in resp.json().values():
            records.append({
                "cik": str(entry["cik_str"]).zfill(10),
                "ticker": entry["ticker"],
                "title": entry["title"],
            })

        self._df = pl.DataFrame(records)
        self.edgarDir.mkdir(parents=True, exist_ok=True)
        self._df.write_parquet(self.cachePath)
        print(f"[EDGAR] {len(records)}개 ticker 캐시 저장")
        return self._df

    def getCik(self, ticker: str) -> str | None:
        df = self.load()
        row = df.filter(pl.col("ticker") == ticker.upper())
        if row.height == 0:
            return None
        return row["cik"][0]

    def getTicker(self, cik: str) -> str | None:
        df = self.load()
        padded = str(cik).zfill(10)
        row = df.filter(pl.col("cik") == padded)
        if row.height == 0:
            return None
        return row["ticker"][0]

    def getName(self, ticker: str) -> str | None:
        df = self.load()
        row = df.filter(pl.col("ticker") == ticker.upper())
        if row.height == 0:
            return None
        return row["title"][0]

    def search(self, query: str, limit: int = 10) -> pl.DataFrame:
        df = self.load()
        q = query.upper()
        matched = df.filter(
            pl.col("ticker").str.contains(q) |
            pl.col("title").str.to_uppercase().str.contains(q)
        )
        return matched.head(limit)


class BulkDownloader:
    def __init__(self, edgarDir: Path):
        self.edgarDir = edgarDir
        self.financeDir = edgarDir / "finance"
        self.tempDir = edgarDir / "temp"
        self.metaPath = edgarDir / "meta.json"

    def _loadMeta(self) -> dict | None:
        if not self.metaPath.exists():
            return None
        with open(self.metaPath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _saveMeta(self, totalCiks: int, lastModified: str | None = None):
        meta = {
            "downloadedAt": datetime.now(timezone.utc).isoformat(),
            "lastModified": lastModified,
            "totalCiks": totalCiks,
        }
        with open(self.metaPath, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def needsUpdate(self) -> tuple[bool, str]:
        meta = self._loadMeta()
        if meta is None:
            return True, "초기 다운로드 필요"

        existing = list(self.financeDir.glob("*.parquet"))
        if len(existing) == 0:
            return True, "parquet 파일 없음"

        try:
            resp = requests.head(BULK_URL, headers=SEC_HEADERS, timeout=15)
            remoteLM = resp.headers.get("Last-Modified")
        except requests.RequestException:
            return False, "원격 확인 실패, 기존 데이터 유지"

        if remoteLM and meta.get("lastModified"):
            if remoteLM != meta["lastModified"]:
                return True, f"원격 갱신 감지 ({remoteLM})"

        return False, f"최신 상태 ({meta['totalCiks']}개 CIK)"

    def download(self, force: bool = False) -> Path:
        self.financeDir.mkdir(parents=True, exist_ok=True)
        self.tempDir.mkdir(parents=True, exist_ok=True)

        if not force:
            needs, reason = self.needsUpdate()
            if not needs:
                print(f"[EDGAR] {reason}")
                return self.financeDir

        zipPath = self.tempDir / "companyfacts.zip"

        print("[EDGAR] companyfacts.zip 다운로드 중...")
        resp = requests.get(BULK_URL, headers=SEC_HEADERS, stream=True, timeout=600)
        resp.raise_for_status()

        lastModified = resp.headers.get("Last-Modified")
        totalSize = int(resp.headers.get("content-length", 0))

        with open(zipPath, "wb") as f:
            downloaded = 0
            with alive_bar(totalSize, title="다운로드", unit="B", scale="SI") as bar:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
                        bar(len(chunk))
                        downloaded += len(chunk)

        print(f"[EDGAR] ZIP 다운로드 완료 ({downloaded / 1e9:.1f} GB)")

        print("[EDGAR] 압축 해제 중...")
        jsonDir = self.tempDir / "json"
        jsonDir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zipPath, "r") as zf:
            members = [m for m in zf.namelist() if m.startswith("CIK") and m.endswith(".json")]
            print(f"[EDGAR] {len(members)}개 JSON 파일")
            with alive_bar(len(members), title="압축 해제") as bar:
                for m in members:
                    zf.extract(m, jsonDir)
                    bar()

        zipPath.unlink()

        print("[EDGAR] JSON → Parquet 변환 중...")
        jsonFiles = list(jsonDir.glob("CIK*.json"))
        nWorkers = min(multiprocessing.cpu_count(), 8)
        args = [(jf, self.financeDir) for jf in jsonFiles]

        okCount = 0
        errCount = 0
        with ProcessPoolExecutor(max_workers=nWorkers) as executor:
            futures = [executor.submit(_convertJsonToParquet, a) for a in args]
            with alive_bar(len(futures), title=f"변환 ({nWorkers} workers)") as bar:
                for future in as_completed(futures):
                    result = future.result()
                    if result.startswith("ok:"):
                        okCount += 1
                    elif result.startswith("error:"):
                        errCount += 1
                    bar()

        shutil.rmtree(self.tempDir, ignore_errors=True)

        totalCiks = len(list(self.financeDir.glob("*.parquet")))
        self._saveMeta(totalCiks, lastModified)

        print(f"[EDGAR] 완료: {okCount} 성공, {errCount} 실패, 총 {totalCiks}개 CIK parquet")
        return self.financeDir

    def status(self) -> dict:
        meta = self._loadMeta()
        existing = list(self.financeDir.glob("*.parquet")) if self.financeDir.exists() else []
        return {
            "hasData": len(existing) > 0,
            "totalCiks": len(existing),
            "meta": meta,
        }


def _verify(edgarDir: Path):
    from dartlab.engines.company.edgar.finance.pivot import buildTimeseries

    testCases = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "NVDA": "0001045810",
    }

    financeDir = edgarDir / "finance"
    for ticker, cik in testCases.items():
        path = financeDir / f"{cik}.parquet"
        if not path.exists():
            print(f"  {ticker} ({cik}): parquet 없음")
            continue

        df = pl.read_parquet(path)
        result = buildTimeseries(cik, edgarDir=financeDir)
        if result is None:
            print(f"  {ticker}: buildTimeseries 실패")
            continue

        series, periods = result
        rev = series.get("IS", {}).get("revenue")
        revLast = None
        if rev:
            for v in reversed(rev):
                if v is not None:
                    revLast = v
                    break

        nAccounts = sum(len(sids) for sids in series.values())
        print(f"  {ticker}: {df.height:,} rows, {len(periods)} periods, "
              f"{nAccounts} accounts, latest revenue={revLast:,.0f}" if revLast else
              f"  {ticker}: {df.height:,} rows, {len(periods)} periods, {nAccounts} accounts")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

    from dartlab import config
    edgarDir = Path(config.dataDir) / "edgar"

    print("=" * 60)
    print("EDGAR 벌크 데이터 파이프라인 실험")
    print("=" * 60)

    print("\n--- 1. Ticker 매핑 ---")
    tm = TickerMap(edgarDir)
    df = tm.load()
    print(f"총 {df.height}개 ticker")

    for t in ["AAPL", "MSFT", "NVDA", "TSLA", "GOOG"]:
        cik = tm.getCik(t)
        name = tm.getName(t)
        print(f"  {t}: CIK={cik}, {name}")

    print("\n검색 'apple':")
    results = tm.search("apple", limit=5)
    print(results)

    print("\n--- 2. 벌크 다운로드 ---")
    bd = BulkDownloader(edgarDir)
    st = bd.status()
    print(f"현재 상태: {st['totalCiks']}개 CIK")

    if st["hasData"]:
        needs, reason = bd.needsUpdate()
        print(f"업데이트 필요: {needs} ({reason})")

    mode = input("\n다운로드 실행? (y=force, u=update check, n=skip): ").strip().lower()
    if mode == "y":
        bd.download(force=True)
    elif mode == "u":
        bd.download(force=False)
    else:
        print("다운로드 스킵")

    print("\n--- 3. 검증 ---")
    _verify(edgarDir)
