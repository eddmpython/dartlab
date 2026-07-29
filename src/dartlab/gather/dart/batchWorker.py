"""dart/openapi batch 워커 + corp resolver — batch.py 분할 (규칙 3 LoC).

_resolveCorpCode / _workerLoop / _resolveCorpMap.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

import httpx
import polars as pl

from dartlab.core.dartClient import DartApiError

# batch ↔ batchWorker 양방향 import 회피 — AsyncDartClient 는 type annotation 만 사용
# (`from __future__ import annotations` 효과로 string lazy). runtime 사용 0.
if TYPE_CHECKING:
    from dartlab.gather.dart.batch import AsyncDartClient

from dartlab.gather.dart.batchCollectors import (
    _collectFinance,
    _collectReport,
)

# ── 워커 + 배치 ──


def _resolveCorpCode(stockCode: str) -> tuple[str, str]:
    """종목코드 → (corpCode, corpName)."""
    from dartlab.core.dartClient import DartClient
    from dartlab.gather.dart.corpCode import findCorpCode, loadCorpCodes

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
    failures: dict[str, dict[str, str]] | None = None,
    targetPeriodsByCode: dict[str, list[tuple[str, str]]] | None = None,
    checkpointBuffer: list[str] | None = None,
    checkpointLock: asyncio.Lock | None = None,
    checkpointEvery: int = 0,
    onCheckpoint: Callable[[list[str]], None] | None = None,
) -> None:
    """워커: 큐에서 종목 꺼내서 수집. 키 소진 시 종료.

    failures: {stockCode: {category: errorRepr}} 형태로 실패 추적.
    onCheckpoint: 종목 ``checkpointEvery`` 개 완료마다 그 batch 의 stockCode 리스트로 호출.
        cancel/timeout 안전망 — buffer drain 된 종목은 콜백이 이미 외부 보존 (예: HF upload) 처리.
    """
    import logging

    logger = logging.getLogger("dartlab.collector")
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

        # 이 종목의 list.json 기반 정확한 (year, reprt_code) — 있으면 88분기 우회
        targetPeriods = None
        if targetPeriodsByCode is not None:
            targetPeriods = targetPeriodsByCode.get(stockCode)

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
                        targetPeriods=targetPeriods,
                    )
                elif cat == "report":
                    count = await _collectReport(
                        stockCode,
                        corpCode,
                        corpName,
                        client,
                        incremental=incremental,
                        onPeriod=_periodCb,
                        targetPeriods=targetPeriods,
                    )
                else:
                    raise ValueError(f"unsupported DART batch category: {cat}")
                result[cat] = count
            except asyncio.CancelledError:
                return
            except (
                DartApiError,
                httpx.HTTPError,
                OSError,
                ValueError,
                KeyError,
                RuntimeError,
            ) as e:
                result[cat] = 0
                # P0 수정 (2026-04-06): 무성한 try/except → 로깅 + 실패 사전 기록.
                # 과거에는 388개 종목 누락 원인이 추적 불가였음.
                errMsg = f"{type(e).__name__}: {e!s}"[:200]
                logger.warning(
                    "collect.fail stockCode=%s category=%s err=%s",
                    stockCode,
                    cat,
                    errMsg,
                )
                if failures is not None:
                    failures.setdefault(stockCode, {})[cat] = errMsg
                if client.exhausted:
                    await queue.put(stockCode)
                    queue.task_done()
                    return

        if not client.exhausted:
            results[stockCode] = result
            if onComplete:
                catSummary = " ".join(f"{k}:{v}" for k, v in result.items() if v > 0)
                onComplete(corpName, catSummary)
            # checkpoint: N 종목마다 buffer drain + 외부 콜백 (HF incremental upload 등).
            # cancel/timeout 시 drain 된 종목까지는 외부에 안전 보존, 나머지는 다음 sync 의
            # rcept_no 비교로 자연 retry.
            if (
                onCheckpoint is not None
                and checkpointBuffer is not None
                and checkpointLock is not None
                and checkpointEvery > 0
            ):
                drain: list[str] | None = None
                async with checkpointLock:
                    checkpointBuffer.append(stockCode)
                    if len(checkpointBuffer) >= checkpointEvery:
                        drain = checkpointBuffer[:]
                        checkpointBuffer.clear()
                if drain:
                    loop = asyncio.get_running_loop()
                    try:
                        await loop.run_in_executor(None, onCheckpoint, drain)
                    except Exception as e:  # noqa: BLE001 — user callback 임의 예외 흡수
                        logger.warning("checkpoint.fail batch_size=%d err=%s", len(drain), repr(e)[:200])

        queue.task_done()
