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

from dartlab.simulate import costs as _costs
from dartlab.simulate import opine as _opine
from dartlab.simulate import readingLedger as _ledger
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import surfaces as _surfaces
from dartlab.simulate import table as _table


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def marketTable(market: str):
    """시장 → 입력 상(床) 모듈 (KR=table, US=tableUs). 미지원 시장은 table(KR) 폴백."""
    from dartlab.simulate import markets as _markets

    return _markets.tableModule(market) or _table


def _buildMatrices(dataDir: Path | None, market: str = "KR"):
    tbl = marketTable(market)
    weekMap, weekEnd = tbl.weekCalendar(dataDir)
    caps = tbl.marketCap(dataDir)
    priceM = tbl.priceWeekly(weekMap, dataDir)
    fundM = tbl.fundWeekly(weekEnd, caps, dataDir)
    eventM = tbl.eventWeekly(weekMap, dataDir)
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
    weekMap, weekEnd, priceM, fundM, eventM = matrices or _buildMatrices(dataDir, market)
    if directionByType is None:
        lab = labels if labels is not None else _sc.weeklyLabels(weekEnd, marketTable(market).dailyPrices(dataDir))
        directionByType = _sc.deriveEventDirections(eventM, lab)
    readings = _opine.opine(priceM, fundM, eventM, directionByType=directionByType)
    if readings.height == 0:
        return 0
    if week is None:
        # 최신 완전주 = 가격 커버(거래 유니버스) 최신 주. 미래 투영 레버(락업만기 = 공시+26주 등)가
        # readings.max 를 미래로 끌어올려 가격 없는 near-empty 주를 발행하는 것을 차단.
        week = int(priceM["week"].max()) if "week" in priceM.columns and priceM.height else int(readings["week"].max())
    readings = readings.filter(pl.col("week") == week)
    if readings.height == 0:
        return 0
    readings = _fillAbstain(readings, priceM, week, directionByType)  # 완전성 강제 (silent 누락 0)
    asOf = weekEnd.filter(pl.col("week") == week)["date"]
    asOfStr = asOf[0] if asOf.len() else str(week)
    # 표면 provenance → refs (근거 참조 자연 기록, 재계산 계약).
    provBySurface = {s.surface: " ".join(s.provenance) for s in _surfaces.enumerateSurfaces(directionByType)}
    sealed = readings.with_columns(
        market=pl.lit(market),
        asOf=pl.lit(asOfStr),
        horizon=pl.lit(horizon, dtype=pl.Int64),
        refs=pl.col("surface").replace_strict(provBySurface, default=""),
    )
    _ledger.appendReadingsFrame(sealed, issuedAt=_nowUtc(), issuedLive=live, baseDir=baseDir)
    return sealed.height


def _fillAbstain(
    readings: pl.DataFrame, priceM: pl.DataFrame, week: int, directionByType: dict[str, int] | None
) -> pl.DataFrame:
    """연속 표면(price·fund)에서 거래 유니버스 중 판독 없는 종목을 기권행으로 발행 (완전성 강제).

    opine 이 결손 code-week 를 드롭한 것을 기권(abstainReason="noData")으로 되살린다: 모든 회사가
    매주 표면마다 판독/중립/기권 셋 중 하나로 기록된다 (silent 누락 0, 0 대체 금지). 이벤트 표면은
    희소성 설계라 부재=중립(미발화)이므로 기권 대상 아님. 기권행 = direction 0 + score null.
    """
    # 거래 유니버스 = 그 주 가격 데이터 종목. 가격 유니버스가 없으면 완전성 강제 대상 미정 → 무발행.
    if not (priceM.height and "week" in priceM.columns):
        return readings
    universe = priceM.filter(pl.col("week") == week).select("code").unique()
    if universe.height == 0:
        return readings
    contSurfaces = [
        s.surface for s in _surfaces.enumerateSurfaces(directionByType) if s.surface.startswith(("price.", "fund."))
    ]
    parts = [readings]
    for surf in contSurfaces:
        have = readings.filter(pl.col("surface") == surf).select("code").unique()
        miss = universe.join(have, on="code", how="anti")
        if miss.height:
            parts.append(
                miss.select(
                    "code",
                    week=pl.lit(week, dtype=pl.Int64),
                    surface=pl.lit(surf),
                    direction=pl.lit(0, dtype=pl.Int64),
                    score=pl.lit(None, dtype=pl.Float64),
                    abstainReason=pl.lit("noData"),
                ).select(readings.columns)
            )
    return pl.concat(parts, how="vertical") if len(parts) > 1 else readings


def scoreReadingsDue(
    *,
    market: str = "KR",
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    labels: pl.DataFrame | None = None,
    costFloorByWeekCode: pl.DataFrame | None = None,
) -> int:
    """지평 경과·라벨 확보된 판독을 버킷 중립 초과로 채점. 반환 = 채점 행 수.

    Args:
        market: 시장 ("KR"|"US"). 라이브 런 라벨·비용 바닥을 이 시장 상(床)에서 계산.
        baseDir: 원장(출력) 루트 override.
        dataDir: 데이터(읽기전용 SSOT) 루트 override.
        labels: 채점 라벨 (None 이면 table 에서 계산). 라벨 없는(지평 미도래) 주는 pending.
        costFloorByWeekCode: (week, code, costFloor) net 게이트용. None + 라이브 런(labels None)이면
            costs 로 직접 생산. 라벨 주입(테스트·백테스트)이면 자동 실데이터 스캔 안 함 (주입만).
    """
    due = _ledger.unscoredReadings(baseDir=baseDir)
    if due is None or due.height == 0:
        return 0
    if "abstainReason" in due.columns:
        due = due.filter(pl.col("abstainReason").is_null())  # 기권행은 채점 대상 아님 (포지션 없음)
    if due.height == 0:
        return 0
    tbl = marketTable(market)
    liveRun = labels is None  # 라벨 미주입 = 실데이터 라이브 런 (자동 스캔 허용)
    weekEnd = None
    if labels is None:
        _, weekEnd = tbl.weekCalendar(dataDir)
        labels = _sc.weeklyLabels(weekEnd, tbl.dailyPrices(dataDir))
    lab = labels.select("week", pl.col("code").alias("stockCode"), "exRaw", "exNeutral")
    joined = due.join(lab, on=["week", "stockCode"], how="inner")
    if joined.height == 0:
        return 0
    # 비용 바닥: 외부 주입 우선. 미주입 + 라이브 런이면 costs 로 직접 생산 (net 상시 유효).
    # 라벨 주입 경로(테스트)는 자동 실데이터 스캔을 하지 않는다 (주입 격리 + OOM 회피).
    if costFloorByWeekCode is None and liveRun:
        if weekEnd is None:
            _, weekEnd = tbl.weekCalendar(dataDir)
        costFloorByWeekCode = _costs.costFloorWeekly(weekEnd, tbl.dailyHighLow(dataDir), market=market)
    if costFloorByWeekCode is None:
        joined = joined.with_columns(costFloor=pl.lit(None, dtype=pl.Float64))
    else:
        cf = (
            costFloorByWeekCode.rename({"code": "stockCode"})
            if "code" in costFloorByWeekCode.columns
            else costFloorByWeekCode
        ).select("week", "stockCode", "costFloor")
        joined = joined.join(cf, on=["week", "stockCode"], how="left")
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
