"""판독 사이클 : 주간 판독을 봉인하고 지평 도래 시 채점하는 유일 collector (L2.5 simulate).

issueMacro 동형의 판독판. table 이 차린 3축 입력을 opine 이 판독으로 바꾸면, 발행 시점에
전량 봉인한다 (선정 이전 봉인 = selection bias 구조 차단). 5거래일 지평 도래 시 실제 초과를
버킷 중립 채점해 append 한다. 유일 writer 이며 L2 엔진은 본 모듈을 import 하지 않는다.

- ``issueReadings`` : 대상 주의 전종목 x 전표면 판독 봉인 (idempotent: 같은 봉인 키 재발행 거부).
- ``scoreReadingsDue`` : 지평 경과·라벨 확보된 판독을 버킷 중립 초과로 채점.

Layer: L2.5 simulate. table·opine·readingScorecard·readingLedger 만 의존 (하향).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from dartlab.simulate import opine as _opine
from dartlab.simulate import readingLedger as _ledger
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import table as _table


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def _buildMatrices(dataDir: Path | None):
    weekMap, weekEnd = _table.weekCalendar(dataDir)
    caps = _table.marketCap(dataDir)
    priceM = _table.priceWeekly(weekMap, dataDir)
    fundM = _table.fundWeekly(weekEnd, caps, dataDir)
    eventM = _table.eventWeekly(weekMap, dataDir)
    return weekMap, weekEnd, priceM, fundM, eventM


def issueReadings(
    *,
    market: str = "KR",
    week: int | None = None,
    live: bool = True,
    horizon: int = 5,
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    matrices: tuple | None = None,
    directionByType: dict[str, int] | None = None,
    labels: pl.DataFrame | None = None,
) -> int:
    """대상 주의 전종목 x 전표면 판독을 봉인. 반환 = 봉인 행 수.

    Args:
        market: 시장 라벨 ("KR" v1).
        week: 대상 주 iso year*100+week (None = 사용 가능한 최신 주).
        live: False = backfill.
        horizon: 거래일 지평 (v0=5).
        baseDir: 원장(출력) 루트 override.
        dataDir: 데이터(읽기전용 SSOT) 루트 override. 원장과 다른 뿌리.
        matrices: 주입 (weekMap, weekEnd, priceM, fundM, eventM) (테스트용, table 스캔 skip).
        directionByType: 이벤트 방향화 사전 (None + labels 있으면 여기서 도출).
        labels: 방향화 도출용 라벨 (None 이면 table 에서 계산).
    """
    weekMap, weekEnd, priceM, fundM, eventM = matrices or _buildMatrices(dataDir)
    if directionByType is None:
        lab = labels if labels is not None else _sc.weeklyLabels(weekEnd, _table.dailyPrices(dataDir))
        directionByType = _sc.deriveEventDirections(eventM, lab)
    readings = _opine.opine(priceM, fundM, eventM, directionByType=directionByType)
    if readings.height == 0:
        return 0
    if week is None:
        week = int(readings["week"].max())
    readings = readings.filter(pl.col("week") == week)
    if readings.height == 0:
        return 0
    asOf = weekEnd.filter(pl.col("week") == week)["date"]
    asOfStr = asOf[0] if asOf.len() else str(week)
    sealed = readings.with_columns(market=pl.lit(market), asOf=pl.lit(asOfStr), horizon=pl.lit(horizon, dtype=pl.Int64))
    _ledger.appendReadingsFrame(sealed, issuedAt=_nowUtc(), issuedLive=live, baseDir=baseDir)
    return sealed.height


def scoreReadingsDue(
    *,
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    labels: pl.DataFrame | None = None,
    costFloorByWeekCode: pl.DataFrame | None = None,
) -> int:
    """지평 경과·라벨 확보된 판독을 버킷 중립 초과로 채점. 반환 = 채점 행 수.

    Args:
        baseDir: 원장(출력) 루트 override.
        dataDir: 데이터(읽기전용 SSOT) 루트 override.
        labels: 채점 라벨 (None 이면 table 에서 계산). 라벨 없는(지평 미도래) 주는 pending.
        costFloorByWeekCode: (week, code, costFloor) net 게이트용 (없으면 costFloor null).
    """
    due = _ledger.unscoredReadings(baseDir=baseDir)
    if due is None or due.height == 0:
        return 0
    if labels is None:
        weekMap, weekEnd = _table.weekCalendar(dataDir)
        labels = _sc.weeklyLabels(weekEnd, _table.dailyPrices(dataDir))
    lab = labels.select("week", pl.col("code").alias("stockCode"), "exRaw", "exNeutral")
    joined = due.join(lab, on=["week", "stockCode"], how="inner")
    if joined.height == 0:
        return 0
    if costFloorByWeekCode is not None:
        cf = (
            costFloorByWeekCode.rename({"code": "stockCode"})
            if "code" in costFloorByWeekCode.columns
            else costFloorByWeekCode
        )
        joined = joined.join(cf, on=["week", "stockCode"], how="left")
    else:
        joined = joined.with_columns(costFloor=pl.lit(None, dtype=pl.Float64))
    scoreRows = joined.select(
        "week",
        "stockCode",
        "surface",
        scoredAt=pl.lit(_nowUtc()),
        exRaw=pl.col("exRaw"),
        exNeutral=pl.col("exNeutral"),
        costFloor=pl.col("costFloor"),
        netExNeutral=pl.col("exNeutral") - pl.col("costFloor").fill_null(0.0),
        error=pl.lit(None, dtype=pl.Utf8),
    ).to_dicts()
    _ledger.appendReadingScores(scoreRows, baseDir=baseDir)
    return len(scoreRows)
