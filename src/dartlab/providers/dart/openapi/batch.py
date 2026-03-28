"""배치 수집 — 병렬 + 증분.

eddmpython v2 DartBase 패턴을 dartlab에 흡수.
키 N개 → asyncio 워커 N개 → Queue 기반 종목 분배.

개별: Dart()("005930").saveFinance(2016)  # 기존 그대로
배치: batchCollect(["005930", "000660"], categories=["finance", "report", "docs"])
전체: batchCollectAll(categories=["finance"])  # 전체 상장종목
"""

from __future__ import annotations

import asyncio
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import polars as pl

from dartlab.providers.dart.openapi.dartKey import resolveDartKeys

BASE_URL = "https://opendart.fss.or.kr/api"

# ── 상수 ──

from dartlab.providers.dart.openapi.constants import (
    CODE_TO_QUARTER as _CODE_TO_QUARTER,
)
from dartlab.providers.dart.openapi.constants import (
    CODE_TO_QUARTER_KR as _CODE_TO_QUARTER_KR,
)
from dartlab.providers.dart.openapi.constants import KR_TO_API_TYPE as _KR_TO_ENG_API_TYPE
from dartlab.providers.dart.openapi.constants import (
    QUARTER_TO_CODE as _QUARTER_TO_CODE,
)

_PERIODIC_REPORT_CATEGORIES: list[str] = [
    "배당",
    "직원",
    "임원",
    "최대주주",
    "최대주주변동",
    "소액주주",
    "자기주식",
    "증자감자",
    "이사회임원전체보수",
    "이사회임원개인보수",
    "개인별보수",
    "타법인출자",
    "주식총수",
    "회계감사인",
    "감사용역체결",
    "감사비감사계약",
    "사외이사변동",
    "미등기임원보수",
    "회사채미상환",
    "단기사채미상환",
    "공모자금용도",
    "공모자금사용",
    "대주주지분변동",
    "기업어음미상환",
    "채무증권발행실적",
    "조건부자본증권미상환",
    "신종자본증권미상환",
    "이사감사보수총회인정",
    "이사감사보수지급형태",
]

_REPORT_ENDPOINTS: dict[str, str] = {
    "증자감자": "irdsSttus",
    "배당": "alotMatter",
    "자기주식": "tesstkAcqsDspsSttus",
    "최대주주": "hyslrSttus",
    "최대주주변동": "hyslrChgSttus",
    "소액주주": "mrhlSttus",
    "임원": "exctvSttus",
    "직원": "empSttus",
    "이사회임원개인보수": "hmvAuditIndvdlBySttus",
    "이사회임원전체보수": "hmvAuditAllSttus",
    "개인별보수": "indvdlByPay",
    "타법인출자": "otrCprInvstmntSttus",
    "대주주지분변동": "eleStockIstySttus",
    "미등기임원보수": "unrstExctvMendngSttus",
    "주식총수": "stockTotqySttus",
    "회계감사인": "accnutAdtorNmNdAdtOpinion",
    "감사용역체결": "adtServcCnclsSttus",
    "감사비감사계약": "accnutAdtorNonAdtServcCnclsSttus",
    "사외이사변동": "outcmpnyDrctrNdChangeSttus",
    "회사채미상환": "cprndNrdmpBlce",
    "단기사채미상환": "srtpdPsndbtNrdmpBlce",
    "기업어음미상환": "entrprsBilScritsNrdmpBlce",
    "채무증권발행실적": "detScritsIsuAcmslt",
    "조건부자본증권미상환": "cndlCaplScrtsNrdmpBlce",
    "신종자본증권미상환": "newCaplScrtsNrdmpBlce",
    "공모자금용도": "prvsrpCptalUseDtls",
    "공모자금사용": "pssrpCptalUseDtls",
    "이사감사보수총회인정": "drctrAdtAllMendngSttusGmtsckConfmAmount",
    "이사감사보수지급형태": "drctrAdtAllMendngSttusMendngPymntamtTyCl",
}

START_YEAR = 2016


# ── AsyncDartClient ──


class AsyncDartClient:
    """비동기 DART API 클라이언트 (배치 수집 전용)."""

    def __init__(self, apiKey: str, *, requestsPerMinute: int = 580):
        self._key = apiKey
        self._client = httpx.AsyncClient(timeout=30)
        self._minInterval = 60.0 / requestsPerMinute
        self._lastRequest = 0.0
        self.exhausted = False

    async def _throttle(self) -> None:
        """키당 rate limit."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._lastRequest
        if elapsed < self._minInterval:
            await asyncio.sleep(self._minInterval - elapsed)
        self._lastRequest = asyncio.get_event_loop().time()

    async def getJson(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        emptyOn013: bool = False,
    ) -> dict[str, Any] | None:
        """비동기 JSON 요청. 한도 초과 시 None + exhausted=True."""
        await self._throttle()
        merged = {"crtfc_key": self._key}
        if params:
            merged.update(params)
        resp = await self._client.get(f"{BASE_URL}/{endpoint}", params=merged)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "000")
        if status == "000":
            return data
        if status == "013" and emptyOn013:
            return {}
        if status == "020":
            self.exhausted = True
            return None
        return {} if emptyOn013 else None

    async def getDf(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        listKey: str = "list",
    ) -> pl.DataFrame | None:
        """비동기 JSON → DataFrame. 한도 초과 시 None."""
        data = await self.getJson(endpoint, params, emptyOn013=True)
        if data is None:
            return None
        rows = data.get(listKey, [])
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    async def getBytes(self, endpoint: str, params: dict[str, Any] | None = None) -> bytes | None:
        """비동기 바이너리 요청. 한도 초과 시 None."""
        await self._throttle()
        merged = {"crtfc_key": self._key}
        if params:
            merged.update(params)
        resp = await self._client.get(
            f"{BASE_URL}/{endpoint}",
            params=merged,
            timeout=60,
        )
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct or "text/json" in ct:
            data = resp.json()
            if data.get("status") == "020":
                self.exhausted = True
                return None
        return resp.content

    async def close(self) -> None:
        """HTTP 클라이언트 연결을 닫는다."""
        await self._client.aclose()


# ── 증분 유틸 ──


def _buildAllPeriods(startYear: int = START_YEAR) -> list[tuple[str, str]]:
    """(bsnsYear, reprtCode) 전체 기간 리스트."""
    endYear = datetime.now().year
    periods = []
    for y in range(startYear, endYear + 1):
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            periods.append((str(y), _QUARTER_TO_CODE[q]))
    return periods


def _existingFinancePeriods(path: Path) -> set[tuple[str, str]]:
    """기존 finance parquet에서 수집된 (bsns_year, reprt_code) 세트."""
    if not path.exists():
        return set()
    try:
        schema = pl.read_parquet_schema(path)
        if "bsns_year" not in schema or "reprt_code" not in schema:
            return set()
        df = (
            pl.scan_parquet(path)
            .select("bsns_year", "reprt_code")
            .filter(pl.col("bsns_year").is_not_null() & pl.col("reprt_code").is_not_null())
            .unique()
            .collect()
        )
        return set(zip(df["bsns_year"].cast(pl.Utf8).to_list(), df["reprt_code"].cast(pl.Utf8).to_list()))
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return set()


def _existingReportPeriods(path: Path) -> set[tuple[str, str, str]]:
    """기존 report parquet에서 수집된 (year, quarter, apiType) 세트."""
    if not path.exists():
        return set()
    try:
        schema = pl.read_parquet_schema(path)
        required = {"year", "quarter", "apiType"}
        if not required.issubset(schema):
            return set()
        df = (
            pl.scan_parquet(path)
            .select("year", "quarter", "apiType")
            .filter(pl.col("year").is_not_null() & pl.col("quarter").is_not_null() & pl.col("apiType").is_not_null())
            .unique()
            .collect()
        )
        return set(
            zip(
                df["year"].cast(pl.Utf8).to_list(),
                df["quarter"].cast(pl.Utf8).to_list(),
                df["apiType"].cast(pl.Utf8).to_list(),
            )
        )
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError, pl.exceptions.ColumnNotFoundError):
        return set()


def _dataPath(category: str, stockCode: str) -> Path:
    """parquet 저장 경로."""
    from dartlab import config as _cfg
    from dartlab.core.dataConfig import DATA_RELEASES

    subDir = DATA_RELEASES.get(category, {}).get("dir", f"dart/{category}")
    dest = Path(_cfg.dataDir) / subDir / f"{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


# ── 단일 종목 수집 (비동기) ──


async def _collectFinance(
    stockCode: str,
    corpCode: str,
    corpName: str,
    client: AsyncDartClient,
    *,
    incremental: bool = True,
    onPeriod=None,
) -> int:
    """finance 수집 (CFS+OFS). 반환: 저장된 행 수."""
    from dartlab.providers.dart.openapi.saver import enrichFinance, save

    path = _dataPath("finance", stockCode)
    allPeriods = _buildAllPeriods()

    if incremental:
        existing = _existingFinancePeriods(path)
        periods = [(y, c) for y, c in allPeriods if (y, c) not in existing]
    else:
        periods = allPeriods

    if not periods:
        return 0

    frames: list[pl.DataFrame] = []
    totalPeriods = len(periods)
    for pIdx, (bsnsYear, reprtCode) in enumerate(periods):
        if client.exhausted:
            break
        quarter = _CODE_TO_QUARTER.get(reprtCode, "Q4")
        if onPeriod:
            onPeriod(f"finance {pIdx + 1}/{totalPeriods} {bsnsYear}{quarter}")
        # CFS (연결) + OFS (별도) 양쪽 수집
        for fsDiv in ("CFS", "OFS"):
            if client.exhausted:
                break
            df = await client.getDf(
                "fnlttSinglAcntAll.json",
                {
                    "corp_code": corpCode,
                    "bsns_year": bsnsYear,
                    "reprt_code": reprtCode,
                    "fs_div": fsDiv,
                },
            )
            if df is None:
                break
            if df.height > 0:
                # API 응답에 fs_div가 없으므로 요청한 값을 직접 부여
                if "fs_div" not in df.columns:
                    df = df.with_columns(pl.lit(fsDiv).alias("fs_div"))
                frames.append(df)

    if not frames:
        return 0

    combined = pl.concat(frames, how="diagonal_relaxed")
    enriched = enrichFinance(combined, stockCode, corpName)
    save(enriched, path)
    return enriched.height


async def _collectReport(
    stockCode: str,
    corpCode: str,
    corpName: str,
    client: AsyncDartClient,
    *,
    incremental: bool = True,
    onPeriod=None,
) -> int:
    """report 수집. 반환: 저장된 행 수."""
    from dartlab.providers.dart.openapi.saver import enrichReport, save

    path = _dataPath("report", stockCode)
    allPeriods = _buildAllPeriods()

    if incremental:
        existing = _existingReportPeriods(path)
    else:
        existing = set()

    frames: list[pl.DataFrame] = []
    totalCats = len(_PERIODIC_REPORT_CATEGORIES)
    for catIdx, cat in enumerate(_PERIODIC_REPORT_CATEGORIES):
        endpoint = _REPORT_ENDPOINTS.get(cat)
        if not endpoint:
            continue
        if onPeriod:
            onPeriod(f"report {catIdx + 1}/{totalCats} {cat}")
        for bsnsYear, reprtCode in allPeriods:
            if client.exhausted:
                break
            quarterKr = _CODE_TO_QUARTER_KR.get(reprtCode, "4분기")
            engApiType = _KR_TO_ENG_API_TYPE.get(cat, cat)
            # 증분: parquet 실제 포맷(year, "N분기", engApiType)으로 비교
            if incremental and (bsnsYear, quarterKr, engApiType) in existing:
                continue

            df = await client.getDf(
                f"{endpoint}.json",
                {"corp_code": corpCode, "bsns_year": bsnsYear, "reprt_code": reprtCode},
            )
            if df is None:
                break
            if df.height > 0:
                enriched = enrichReport(df, stockCode, corpCode, cat, endpoint)
                frames.append(enriched)
        if client.exhausted:
            break

    if not frames:
        return 0

    combined = pl.concat(frames, how="diagonal_relaxed")
    save(combined, path)
    return combined.height


_processPool = None


def _getProcessPool():
    """XML 파싱용 프로세스 풀 (모듈 레벨 싱글톤)."""
    global _processPool
    if _processPool is None:
        import concurrent.futures
        import os

        _processPool = concurrent.futures.ProcessPoolExecutor(
            max_workers=min(4, (os.cpu_count() or 4)),
        )
    return _processPool


async def _collectDocs(
    stockCode: str,
    corpCode: str,
    corpName: str,
    client: AsyncDartClient,
    *,
    onPeriod=None,
) -> int:
    """docs 수집 (완전 비동기 ZIP 기반)."""
    from dartlab.providers.dart.openapi.zipCollector import (
        _docsDataDir,
        _parseSections,
    )

    if onPeriod:
        onPeriod("docs 목록 조회 중...")

    # 1. 공시 목록 조회 (비동기 페이지네이션)
    allRows: list[dict] = []
    page = 1
    while True:
        if client.exhausted:
            break
        data = await client.getJson(
            "list.json",
            {
                "corp_code": corpCode,
                "bgn_de": "20160101",
                "pblntf_ty": "A",
                "page_count": "100",
                "page_no": str(page),
                "sort": "date",
                "sort_mth": "desc",
            },
            emptyOn013=True,
        )
        if data is None:
            break
        rows = data.get("list", [])
        if not rows:
            break
        allRows.extend(rows)
        totalPage = int(data.get("total_page", 1))
        if page >= totalPage:
            break
        page += 1

    if not allRows:
        return 0

    filings = pl.DataFrame(allRows)
    reportFilter = r"사업보고서|반기보고서|분기보고서"
    filings = filings.filter(pl.col("report_nm").str.contains(reportFilter))
    filings = filings.sort("rcept_dt", descending=True)

    # 기존 수집된 것 제외
    dataDir = _docsDataDir()
    parquetPath = dataDir / f"{stockCode}.parquet"
    existingReports: set[str] = set()
    if parquetPath.exists():
        try:
            df = pl.scan_parquet(parquetPath).select("rcept_no").collect()
            existingReports = set(df["rcept_no"].unique().to_list())
        except (pl.exceptions.ComputeError, OSError):
            pass

    newFilings = filings.filter(~pl.col("rcept_no").is_in(list(existingReports)))
    if newFilings.height == 0:
        return 0

    # 2. ZIP 수집 (비동기 파이프라인: 다운로드 + 파싱 동시)
    total = newFilings.height
    allSections: list[dict] = []
    failCount = 0
    doneCount = [0]

    async def _fetchOne(rowIdx: int, row: dict) -> None:
        nonlocal failCount
        if client.exhausted:
            return
        rceptNo = row["rcept_no"]
        rceptDt = row["rcept_dt"]
        reportNm = row["report_nm"]

        ym = re.search(r"\((\d{4})\.\d{2}\)", reportNm)
        year = ym.group(1) if ym else rceptDt[:4]

        try:
            raw = await client.getBytes("document.xml", {"rcept_no": rceptNo})
        except (httpx.HTTPError, OSError):
            failCount += 1
            doneCount[0] += 1
            if onPeriod:
                onPeriod(f"docs {doneCount[0]}/{total}")
            return

        if raw is None:
            failCount += 1
            doneCount[0] += 1
            if onPeriod:
                onPeriod(f"docs {doneCount[0]}/{total}")
            return

        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            failCount += 1
            doneCount[0] += 1
            if onPeriod:
                onPeriod(f"docs {doneCount[0]}/{total}")
            return

        names = zf.namelist()
        if not names:
            failCount += 1
            doneCount[0] += 1
            if onPeriod:
                onPeriod(f"docs {doneCount[0]}/{total}")
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
        sections = await loop.run_in_executor(_getProcessPool(), _parseSections, xmlContent)

        for s in sections:
            allSections.append(
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
        if onPeriod:
            onPeriod(f"docs {doneCount[0]}/{total} {reportNm}")

    # 세마포어로 동시 4개씩 다운로드+파싱
    sem = asyncio.Semaphore(4)

    async def _guarded(rowIdx: int, row: dict) -> None:
        async with sem:
            await _fetchOne(rowIdx, row)

    filingRows = list(enumerate(newFilings.iter_rows(named=True)))
    await asyncio.gather(*[_guarded(idx, row) for idx, row in filingRows])

    if not allSections:
        return 0

    # 3. parquet 저장
    newDf = pl.DataFrame(allSections)
    if parquetPath.exists():
        existingDf = pl.read_parquet(parquetPath)
        combinedDf = pl.concat([existingDf, newDf], how="diagonal_relaxed")
    else:
        combinedDf = newDf

    tmpPath = parquetPath.with_suffix(".parquet.tmp")
    combinedDf.write_parquet(tmpPath)
    if parquetPath.exists():
        parquetPath.unlink()
    tmpPath.rename(parquetPath)

    return len(allSections)


# ── async 실행 헬퍼 ──


def _runAsync(coro):
    """이벤트 루프 유무에 따라 코루틴 실행. Marimo/Jupyter 호환."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # 루프 없음 — 일반 Python (KeyboardInterrupt는 호출자가 처리)
        return asyncio.run(coro)
    # 이미 루프가 돌고 있음 (Marimo/Jupyter) → 별도 스레드에서 실행
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


# ── 워커 + 배치 ──


def _resolveCorpCode(stockCode: str) -> tuple[str, str]:
    """종목코드 → (corpCode, corpName)."""
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.corpCode import findCorpCode, loadCorpCodes

    client = DartClient()
    codes = loadCorpCodes(client)
    match = codes.filter(pl.col("stock_code") == stockCode)
    if match.height > 0:
        return match["corp_code"][0], match["corp_name"][0]
    code = findCorpCode(client, stockCode)
    return (code or "", stockCode)


async def _workerLoop(
    workerIndex: int,
    client: AsyncDartClient,
    queue: asyncio.Queue,
    categories: list[str],
    results: dict,
    corpMap: dict[str, tuple[str, str]],
    incremental: bool,
    onComplete,
    onStatus,
    onPeriod,
) -> None:
    """워커: 큐에서 종목 꺼내서 수집. 키 소진 시 종료."""
    while not client.exhausted:
        try:
            stockCode = queue.get_nowait()
        except asyncio.QueueEmpty:
            if onPeriod:
                onPeriod(workerIndex, "", "완료")
            return

        corpCode, corpName = corpMap.get(stockCode, ("", stockCode))
        result: dict[str, int] = {}

        if onStatus:
            onStatus(workerIndex, stockCode, corpName)

        def _periodCb(msg):
            if onPeriod:
                onPeriod(workerIndex, corpName, msg)

        for cat in categories:
            if client.exhausted:
                await queue.put(stockCode)
                return
            try:
                if cat == "finance":
                    count = await _collectFinance(
                        stockCode,
                        corpCode,
                        corpName,
                        client,
                        incremental=incremental,
                        onPeriod=_periodCb,
                    )
                elif cat == "report":
                    count = await _collectReport(
                        stockCode,
                        corpCode,
                        corpName,
                        client,
                        incremental=incremental,
                        onPeriod=_periodCb,
                    )
                elif cat == "docs":
                    count = await _collectDocs(
                        stockCode,
                        corpCode,
                        corpName,
                        client,
                        onPeriod=_periodCb,
                    )
                else:
                    count = 0
                result[cat] = count
            except asyncio.CancelledError:
                return
            except (httpx.HTTPError, OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile):
                result[cat] = 0

        if not client.exhausted:
            results[stockCode] = result
            if onComplete:
                catSummary = " ".join(f"{k}:{v}" for k, v in result.items() if v > 0)
                onComplete(corpName, catSummary)

        queue.task_done()


def _resolveCorpMap(stockCodes: list[str]) -> dict[str, tuple[str, str]]:
    """종목코드 목록 → {stockCode: (corpCode, corpName)} 맵."""
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.corpCode import loadCorpCodes

    client = DartClient()
    codes = loadCorpCodes(client)
    corpMap: dict[str, tuple[str, str]] = {}
    for sc in stockCodes:
        match = codes.filter(pl.col("stock_code") == sc)
        if match.height > 0:
            corpMap[sc] = (match["corp_code"][0], match["corp_name"][0])
        else:
            corpMap[sc] = ("", sc)
    return corpMap


def batchCollect(
    stockCodes: list[str],
    *,
    categories: list[str] | None = None,
    maxWorkers: int | None = None,
    incremental: bool = True,
    showProgress: bool = True,
) -> dict[str, dict[str, int]]:
    """병렬 배치 수집. 키 N개 → 워커 N개 → 종목 분배.

    Returns: {"005930": {"finance": 120, "report": 450, "docs": 1681}, ...}
    """
    cats = categories or ["finance", "report", "docs"]
    keys = resolveDartKeys()
    if not keys:
        raise ValueError("DART API 키가 필요합니다. DART_API_KEYS 환경변수를 설정하세요.")

    if maxWorkers is not None:
        keys = keys[:maxWorkers]

    # corpCode 맵 사전 로드
    corpMap = _resolveCorpMap(stockCodes)
    total = len(stockCodes)

    async def _run(completeFn, statusFn, periodFn) -> dict[str, dict[str, int]]:
        clients = [AsyncDartClient(k) for k in keys]
        queue: asyncio.Queue = asyncio.Queue()
        for sc in stockCodes:
            await queue.put(sc)

        results: dict[str, dict[str, int]] = {}

        try:
            workers = [
                asyncio.create_task(
                    _workerLoop(i, c, queue, cats, results, corpMap, incremental, completeFn, statusFn, periodFn)
                )
                for i, c in enumerate(clients)
            ]
            await asyncio.gather(*workers)
        finally:
            for c in clients:
                await c.close()

        remaining = queue.qsize()
        if remaining > 0:
            from dartlab.core.guidance import emit

            emit("collect:exhausted")

        return results

    if not showProgress:
        try:
            return _runAsync(_run(None, None, None))
        except KeyboardInterrupt:
            print("\n[배치] 사용자 중단.")
            return {}

    # ── progress 모드: rich Live 기반 워커별 실시간 표시 ──
    import threading

    from rich.live import Live
    from rich.table import Table
    from rich.text import Text

    numWorkers = len(keys)
    workerLines = ["⏳ 대기 중..."] * numWorkers
    completedCount = [0]
    lock = threading.Lock()
    result: dict[str, dict[str, int]] = {}
    runError: list[BaseException] = []

    catLabel = ", ".join(cats)

    def _buildDisplay() -> Table:
        """워커 상태 + 전체 진행 bar를 rich Table로 구성."""
        tbl = Table.grid(padding=(0, 1))
        tbl.add_column(style="bold cyan", width=4)
        tbl.add_column()

        for i in range(numWorkers):
            tbl.add_row(f"W{i}", workerLines[i])

        # progress bar
        pct = completedCount[0] / total * 100 if total else 0
        filled = int(pct / 2)
        barStr = "█" * filled + "░" * (50 - filled)
        barText = Text(f"[{barStr}] {completedCount[0]}/{total} ({pct:.0f}%)")
        tbl.add_row("", barText)
        return tbl

    def completeFn(corpName: str, catSummary: str) -> None:
        with lock:
            completedCount[0] += 1
            for wIdx in range(numWorkers):
                if corpName in workerLines[wIdx] and "✓" not in workerLines[wIdx]:
                    summary = f" ({catSummary})" if catSummary else ""
                    workerLines[wIdx] = f"✓ {corpName}{summary}"
                    break

    def statusFn(workerIdx: int, stockCode: str, corpName: str) -> None:
        with lock:
            workerLines[workerIdx] = f"{corpName} ({stockCode})"

    def periodFn(workerIdx: int, corpName: str, detail: str) -> None:
        with lock:
            workerLines[workerIdx] = f"{corpName} | {detail}"

    def _threadTarget():
        try:
            nonlocal result
            result = asyncio.run(_run(completeFn, statusFn, periodFn))
        except KeyboardInterrupt:
            pass
        except BaseException as exc:
            runError.append(exc)

    t = threading.Thread(target=_threadTarget, daemon=True)
    t.start()

    try:
        with Live(_buildDisplay(), refresh_per_second=8) as live:
            while t.is_alive():
                with lock:
                    live.update(_buildDisplay())
                t.join(timeout=0.12)
            # 최종 갱신
            with lock:
                live.update(_buildDisplay())
    except KeyboardInterrupt:
        print("\n[배치] 사용자 중단.")

    if runError and not isinstance(runError[0], KeyboardInterrupt):
        raise runError[0]

    return result


def batchCollectAll(
    *,
    categories: list[str] | None = None,
    mode: str = "new",
    maxWorkers: int | None = None,
    incremental: bool = True,
    showProgress: bool = True,
) -> dict[str, dict[str, int]]:
    """전체 상장종목 배치 수집.

    mode:
      "new" — 파일 없는 종목만
      "all" — 전체
    """
    from dartlab.gather.listing import getKindList

    kindDf = getKindList()
    # 코넥스 제외 (공시 제한적, 사용자 관심 대상 아님)
    kindDf = kindDf.filter(pl.col("시장구분") != "코넥스")
    allCodes = kindDf["종목코드"].to_list()

    if mode == "new":
        cats = categories or ["finance", "report", "docs"]
        newCodes = []
        for sc in allCodes:
            missing = any(not _dataPath(cat, sc).exists() for cat in cats)
            if missing:
                newCodes.append(sc)
        targetCodes = newCodes
    else:
        targetCodes = allCodes

    if not targetCodes:
        print("[배치] 수집할 종목이 없습니다.")
        return {}

    print(f"[배치] {mode} 모드: {len(targetCodes)}개 종목")
    return batchCollect(
        targetCodes,
        categories=categories,
        maxWorkers=maxWorkers,
        incremental=incremental,
        showProgress=showProgress,
    )
