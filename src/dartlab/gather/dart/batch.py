"""배치 수집 — 병렬 + 증분.

eddmpython v2 DartBase 패턴을 dartlab에 흡수.
키 N개 → asyncio 워커 N개 → Queue 기반 종목 분배.

개별: Dart()("005930").saveFinance(2016)  # 기존 그대로
배치: batchCollect(["005930", "000660"], categories=["finance", "report"])
전체: batchCollectAll(categories=["finance"])  # 전체 상장종목
"""

from __future__ import annotations

import asyncio
import io
import re
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import httpx
import polars as pl

from dartlab.core.dartClient import resolveDartKeys
from dartlab.core.requestPacing import awaitMinInterval
from dartlab.gather.batchProgress import buildWorkerTable

BASE_URL = "https://opendart.fss.or.kr/api"
_CLIENT_TIMEOUT = httpx.Timeout(60.0, connect=10.0, read=60.0, write=30.0, pool=10.0)
_CLIENT_LIMITS = httpx.Limits(max_connections=4, max_keepalive_connections=2)
_TRANSIENT_HTTP_ERRORS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
)
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# ── 상수 ──

from dartlab.core.dartConstants import (
    CODE_TO_QUARTER as _CODE_TO_QUARTER,
)
from dartlab.core.dartConstants import (
    CODE_TO_QUARTER_KR as _CODE_TO_QUARTER_KR,
)
from dartlab.core.dartConstants import KR_TO_API_TYPE as _KR_TO_ENG_API_TYPE
from dartlab.core.dartConstants import (
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

    def __init__(
        self,
        apiKey: str,
        *,
        requestsPerMinute: int = 580,
        maxRetries: int = 3,
        retryBaseDelay: float = 0.5,
    ):
        self._key = apiKey
        self._client = httpx.AsyncClient(timeout=_CLIENT_TIMEOUT, limits=_CLIENT_LIMITS)
        self._minInterval = 60.0 / requestsPerMinute
        self._lastRequest = 0.0
        self._maxRetries = max(0, maxRetries)
        self._retryBaseDelay = max(0.0, retryBaseDelay)
        self.exhausted = False

    async def _throttle(self) -> None:
        """키당 rate limit."""
        self._lastRequest = await awaitMinInterval(self._lastRequest, self._minInterval)

    async def _getWithRetry(
        self,
        endpoint: str,
        params: dict[str, Any],
        *,
        timeout: float | httpx.Timeout | None = None,
    ) -> httpx.Response:
        """DART 전송 계층 오류를 같은 요청 단위로 재시도한다."""
        lastError: BaseException | None = None
        for attempt in range(self._maxRetries + 1):
            await self._throttle()
            try:
                kwargs: dict[str, Any] = {"params": params}
                if timeout is not None:
                    kwargs["timeout"] = timeout
                resp = await self._client.get(f"{BASE_URL}/{endpoint}", **kwargs)
                if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < self._maxRetries:
                    await resp.aclose()
                    await asyncio.sleep(self._retryBaseDelay * (2**attempt))
                    continue
                return resp
            except _TRANSIENT_HTTP_ERRORS as exc:
                lastError = exc
                if attempt >= self._maxRetries:
                    raise
                await asyncio.sleep(self._retryBaseDelay * (2**attempt))

        raise RuntimeError("unreachable DART retry loop") from lastError

    async def getJson(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        emptyOn013: bool = False,
    ) -> dict[str, Any] | None:
        """비동기 JSON 요청. 한도 초과 시 None + exhausted=True.

        Args:
            endpoint: 인자.
            params: 인자.
            emptyOn013: 인자.

        Raises:
            없음.

        Example:
            >>> getJson(...)

        Returns:
            dict[str, Any] 또는 None — 결과 dict.

        """
        await self._throttle()
        merged = {"crtfc_key": self._key}
        if params:
            merged.update(params)
        resp = await self._getWithRetry(endpoint, merged)
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
        """비동기 JSON → DataFrame. 한도 초과 시 None.

        Args:
            endpoint: 인자.
            params: 인자.
            listKey: 인자.

        Raises:
            없음.

        Example:
            >>> getDf(...)

        Returns:
            pl.DataFrame 또는 None — 결과.

        """
        data = await self.getJson(endpoint, params, emptyOn013=True)
        if data is None:
            return None
        rows = data.get(listKey, [])
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    async def getBytes(self, endpoint: str, params: dict[str, Any] | None = None) -> bytes | None:
        """비동기 바이너리 요청. 한도 초과 시 None.

        Args:
            endpoint: 인자.
            params: 인자.

        Raises:
            없음.

        Example:
            >>> getBytes(...)

        Returns:
            bytes 또는 None — 응답 본문.

        """
        await self._throttle()
        merged = {"crtfc_key": self._key}
        if params:
            merged.update(params)
        resp = await self._getWithRetry(endpoint, merged, timeout=60)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct or "text/json" in ct:
            data = resp.json()
            if data.get("status") == "020":
                self.exhausted = True
                return None
        return resp.content

    async def close(self) -> None:
        """HTTP 클라이언트 연결을 닫는다.

        Raises:
            없음.

        Example:
            >>> close(...)
        """
        await self._client.aclose()


# ── 증분 유틸 ──


def _buildAllPeriods(startYear: int = START_YEAR) -> list[tuple[str, str]]:
    """(bsnsYear, reprtCode) 전체 기간 리스트.

    순서: **최신 분기부터 과거 순**.
    이유: DART API 일일 한도(20,000회) ÷ 종목당 ~32회 ≈ ~600 종목/일.
    전체 2,500+ 종목을 매일 처리할 수 없으므로 한도 도달 시 잘리는 종목이 발생한다.
    오래된 분기부터 처리하면 매번 동일한 종목의 **최신 분기**가 잘려서 신규 데이터가
    영구 누락되는 사례가 발생 (2026-04-06 두산에너빌리티 25Q4 누락 388개 사례).
    최신부터 처리하면 한도 잘림이 발생해도 옛날 분기만 잘리고, 신규 분기는 항상 우선
    처리된다.
    """
    endYear = datetime.now().year
    periods = []
    # 역순: 최신 연도 → 과거 연도, 각 연도 안에서도 Q4 → Q1
    for y in range(endYear, startYear - 1, -1):
        for q in ["Q4", "Q3", "Q2", "Q1"]:
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
            .collect(engine="streaming")
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
            .collect(engine="streaming")
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
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    subDir = DATA_RELEASES.get(category, {}).get("dir", f"dart/{category}")
    dest = _getDataRoot() / subDir / f"{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


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


def _resolveCorpMap(stockCodes: list[str]) -> dict[str, tuple[str, str]]:
    """종목코드 목록 → {stockCode: (corpCode, corpName)} 맵."""
    from dartlab.core.dartClient import DartClient
    from dartlab.gather.dart.corpCode import loadCorpCodes

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


def _activeDartCategories(categories: list[str] | None) -> list[str]:
    """DART 수집 카테고리 정규화.

    정기보고서 본문은 panel builder가 생산하므로 batch 수집기는 finance/report만 실행한다.
    """
    cats = list(categories or ["finance", "report"])
    invalid = [c for c in cats if c not in {"finance", "report"}]
    if invalid:
        raise ValueError(f"DART batch 수집 카테고리는 finance/report만 지원합니다: {invalid}")
    return cats


def batchCollect(
    stockCodes: list[str],
    *,
    categories: list[str] | None = None,
    maxWorkers: int | None = None,
    incremental: bool = True,
    showProgress: bool = True,
    targetPeriodsByCode: dict[str, list[tuple[str, str]]] | None = None,
    onCheckpoint: Callable[[list[str]], None] | None = None,
    checkpointEvery: int = 0,
) -> dict[str, dict[str, int]]:
    """병렬 배치 수집. 키 N개 → 워커 N개 → 종목 분배.

    Returns: {"005930": {"finance": 120, "report": 450}, ...}

    Args:
        targetPeriodsByCode: list.json에서 발견한 종목별 정확한 (year, reprt_code).
            지정하면 _collectFinance/_collectReport가 88분기 차집합 우회.

    Raises:
        없음.

    Example:
        >>> batchCollect(...)
    """
    cats = _activeDartCategories(categories)
    if not cats:
        return {sc: {} for sc in stockCodes}
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
        failures: dict[str, dict[str, str]] = {}

        # checkpoint: 모든 worker 공유 buffer + lock. N 종목 도달 시 외부 콜백.
        checkpointBuffer: list[str] | None = [] if onCheckpoint is not None and checkpointEvery > 0 else None
        checkpointLock: asyncio.Lock | None = asyncio.Lock() if checkpointBuffer is not None else None

        try:
            workers = [
                asyncio.create_task(
                    _workerLoop(
                        i,
                        c,
                        queue,
                        cats,
                        results,
                        corpMap,
                        incremental,
                        completeFn,
                        statusFn,
                        periodFn,
                        failures,
                        targetPeriodsByCode,
                        checkpointBuffer,
                        checkpointLock,
                        checkpointEvery,
                        onCheckpoint,
                    )
                )
                for i, c in enumerate(clients)
            ]
            await asyncio.gather(*workers)
        finally:
            for c in clients:
                await c.close()

            # final flush: cancel/exhausted/완료 어떤 경로든 buffer 의 잔여 종목 외부에 넘긴다.
            if onCheckpoint is not None and checkpointBuffer is not None and checkpointBuffer:
                drain = checkpointBuffer[:]
                checkpointBuffer.clear()
                import logging as _logging

                try:
                    onCheckpoint(drain)
                except Exception as e:  # noqa: BLE001 — user callback 임의 예외 흡수
                    _logging.getLogger("dartlab.collector").warning(
                        "checkpoint.final_flush.fail batch_size=%d err=%s", len(drain), repr(e)[:200]
                    )

        # P0 수정 (2026-04-06):
        # 1) 큐에 남은 종목 = exhausted로 잘린 종목 → pending 파일 저장
        # 2) 실패한 종목 = 에러 발생 종목 → failures 파일 저장
        # 다음 실행에서 이 두 파일을 읽고 우선 재시도해야 누락 회복 가능.
        from dartlab.core.messaging import emit

        pending: list[str] = []
        while not queue.empty():
            try:
                pending.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        if pending or failures:
            import os

            from dartlab.core.dataLoader import _getDataRoot

            # 병렬 Job 간 동시 쓰기 경쟁 회피 — env SYNC_STATE_SCOPE 로 하위 디렉토리 분리.
            baseDir = _getDataRoot() / "dart" / "_collect_state"
            scope = os.environ.get("SYNC_STATE_SCOPE", "").strip()
            stateDir = baseDir / scope if scope else baseDir
            stateDir.mkdir(parents=True, exist_ok=True)
            if pending:
                (stateDir / "pending.txt").write_text("\n".join(pending), encoding="utf-8")
                emit("collect:exhausted")
            if failures:
                import json

                (stateDir / "failures.json").write_text(
                    json.dumps(failures, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

        return results

    if not showProgress:
        try:
            return _runAsync(_run(None, None, None))
        except KeyboardInterrupt:
            _log.info("\n[배치] 사용자 중단.")
            return {}

    # ── progress 모드: rich Live 기반 워커별 실시간 표시 ──
    import threading

    from rich.live import Live
    from rich.table import Table

    numWorkers = len(keys)
    workerLines = ["⏳ 대기 중..."] * numWorkers
    completedCount = [0]
    lock = threading.Lock()
    result: dict[str, dict[str, int]] = {}
    runError: list[BaseException] = []

    ", ".join(cats)

    def _buildDisplay() -> Table:
        """워커 상태 + 전체 진행 bar를 rich Table로 구성."""
        return buildWorkerTable(numWorkers, workerLines, completedCount[0], total)

    def completeFn(corpName: str, catSummary: str) -> None:
        """worker callback — corp 처리 완료 시 workerLines 의 해당 행을 ``✓ {corp} ({summary})`` 로 갱신.

        Args:
            corpName: 완료된 corp 이름.
            catSummary: 카테고리별 수집 통계 (``""`` 가능).

        Raises:
            없음.

        Example:
            >>> completeFn("삼성전자", "f:5,r:3")
        """
        with lock:
            completedCount[0] += 1
            for wIdx in range(numWorkers):
                if corpName in workerLines[wIdx] and "✓" not in workerLines[wIdx]:
                    summary = f" ({catSummary})" if catSummary else ""
                    workerLines[wIdx] = f"✓ {corpName}{summary}"
                    break

    def statusFn(workerIdx: int, stockCode: str, corpName: str) -> None:
        """worker callback — 처리 시작 시 workerLines 에 ``{corp} ({code})`` 표시.

        Args:
            workerIdx: 워커 슬롯 index.
            stockCode: 종목코드.
            corpName: corp 이름.

        Raises:
            없음.

        Example:
            >>> statusFn(0, "005930", "삼성전자")
        """
        with lock:
            workerLines[workerIdx] = f"{corpName} ({stockCode})"

    def periodFn(workerIdx: int, corpName: str, detail: str) -> None:
        """worker callback — period 진행 상황 표시 (``{corp} | {detail}``).

        Args:
            workerIdx: 워커 슬롯 index.
            corpName: corp 이름.
            detail: 진행 상세 (예: ``"2024Q1 fetching"``).

        Raises:
            없음.

        Example:
            >>> periodFn(0, "삼성전자", "2024Q3 fetching")
        """
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

    from dartlab.core.logger import getConsole

    try:
        with Live(_buildDisplay(), refresh_per_second=8, console=getConsole()) as live:
            while t.is_alive():
                with lock:
                    live.update(_buildDisplay())
                t.join(timeout=0.12)
            # 최종 갱신
            with lock:
                live.update(_buildDisplay())
    except KeyboardInterrupt:
        _log.info("\n[배치] 사용자 중단.")

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

    Capabilities:
        - 상장 universe(코넥스 제외) 전 종목을 카테고리별로 순회 수집한다. mode="new" 는 파일
          없는 종목만, "all" 은 전체. incremental 은 종목별 부분 진행 재개를 허용한다.

    Args:
        categories: 수집 카테고리 list (None=기본 전체).
        mode: "new"(파일 없는 종목만) 또는 "all"(전체).
        maxWorkers: 동시 워커 수 (None=기본).
        incremental: 종목별 증분 재개 여부.
        showProgress: 진행 로그 출력.

    Returns:
        dict[str, dict[str, int]] — 종목 × 카테고리 별 수집 통계.

    Raises:
        없음 — 개별 종목 실패는 통계로 흡수.

    Example:
        >>> batchCollectAll(mode="new")  # doctest: +SKIP

    Guide:
        - 전 종목은 무겁다 — categories/mode 로 범위 조절. incremental=True 로 중단 후 재개.

    SeeAlso:
        - ``batchCollect`` — 단일 종목 배치.
        - ``core.listingResolver.getListingResolver`` — universe 해소.

    Requires:
        - 인터넷 + DART API 키 + 쓰기 가능 ``data/``.

    When:
        - 운영자가 전 상장 universe 원본을 수집/백필할 때.

    How:
        - listingResolver universe(코넥스 제외) → 종목별 batchCollect → 통계 집계.

    AIContext:
        - 배치 수집 — 운영자/CLI 전용(무겁다). 분석 파이프라인에서 호출 금지.
    """
    from dartlab.core.listingResolver import getListingResolver

    resolver = getListingResolver()
    if resolver is None:
        return {}
    kindDf = resolver.kindList()
    # 코넥스 제외 (공시 제한적, 사용자 관심 대상 아님)
    kindDf = kindDf.filter(pl.col("시장구분") != "코넥스")
    allCodes = kindDf["종목코드"].to_list()

    if mode == "new":
        cats = _activeDartCategories(categories)
        if not cats:
            return {}
        newCodes = []
        for sc in allCodes:
            missing = any(not _dataPath(cat, sc).exists() for cat in cats)
            if missing:
                newCodes.append(sc)
        targetCodes = newCodes
    else:
        targetCodes = allCodes

    if not targetCodes:
        _log.info("[배치] 수집할 종목이 없습니다.")
        return {}

    _log.info(f"[배치] {mode} 모드: {len(targetCodes)}개 종목")
    return batchCollect(
        targetCodes,
        categories=categories,
        maxWorkers=maxWorkers,
        incremental=incremental,
        showProgress=showProgress,
    )


# ── 재내보내기 (분리: batchCollectors.py · batchWorker.py) ──────
from dartlab.gather.dart.batchCollectors import (  # noqa: E402  re-export
    _collectFinance,
    _collectReport,
    _getProcessPool,
)
from dartlab.gather.dart.batchWorker import (  # noqa: E402  re-export
    _resolveCorpCode,
    _workerLoop,
)
