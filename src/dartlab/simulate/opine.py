"""의견화 : 입력 상(床)을 표면별 주간 판독으로 변환 (L2.5 simulate).

table 이 차린 3축 (code, week) 행렬을 표면별 판독 행렬로 바꾼다. 연속 표면(가격·재무 비율)은
주간 횡단면 랭크 → 강도(score)와 극단 방향(±1/중립 0), 이산 표면(이벤트)은 방향화 사전을
적용한다. 스케일이 주당 수백만 행이라 Reading dataclass 객체가 아니라 polars 행렬로 다룬다
(계약은 reading.py, 대량 경로는 여기).

방향 규칙 (06 §2): 연속 표면은 상위 극단 = +1, 하위 극단 = -1, 중간 = 중립 0 (판독 발행됨,
기권 아님). 데이터 결손(그 code-week 에 표면 값 없음) = 기권 (0 대체 금지, abstainReason 기록).

Layer: L2.5 simulate. table·surfaces·reading 만 의존 (하향).
"""

from __future__ import annotations

import polars as pl

# 연속 표면 극단 방향 임계 (상위 20% = 상방, 하위 20% = 하방, 중간 = 중립).
_UP_Q, _DOWN_Q = 0.8, 0.2
# 축별 {입력 컬럼: 표면 id}. table.priceWeekly·fundWeekly 컬럼 → 표면.
_PRICE_COLS = {"ret5": "price.ret5", "mom20x5": "price.mom20x5", "volShock": "price.volShock", "high52": "price.high52"}
_FUND_COLS = {"ep": "fund.ep", "bm": "fund.bm"}


def _continuousReadings(matrix: pl.DataFrame, colToSurface: dict[str, str]) -> pl.DataFrame:
    """연속 표면 판독: 주간 랭크 → score, 극단 방향. → (code, week, surface, direction, score)."""
    out = []
    for col, surface in colToSurface.items():
        if col not in matrix.columns:
            continue
        r = matrix.select("code", "week", pl.col(col).alias("raw")).filter(pl.col("raw").is_finite())
        r = r.with_columns(score=(pl.col("raw").rank() / pl.len()).over("week"))
        r = r.with_columns(
            direction=pl.when(pl.col("score") >= _UP_Q)
            .then(1)
            .when(pl.col("score") <= _DOWN_Q)
            .then(-1)
            .otherwise(0)
            .cast(pl.Int64),
            surface=pl.lit(surface),
            abstainReason=pl.lit(None, dtype=pl.Utf8),
        )
        out.append(r.select("code", "week", "surface", "direction", "score", "abstainReason"))
    return pl.concat(out) if out else _empty()


def _eventReadings(eventMatrix: pl.DataFrame, directionByType: dict[str, int]) -> pl.DataFrame:
    """이산 이벤트 표면 판독: 방향화 사전 적용, 접수 주에 방향 발행. → 동일 스키마."""
    if not directionByType or eventMatrix.height == 0:
        return _empty()
    dirDf = pl.DataFrame({"reportType": list(directionByType), "dir": list(directionByType.values())})
    scored = eventMatrix.join(dirDf, on="reportType", how="inner")
    r = scored.group_by(["code", "week"]).agg(direction=pl.col("dir").sum().sign().cast(pl.Int64))
    return r.with_columns(
        surface=pl.lit("event.dilutionGovernance"),
        score=(pl.col("direction") + 1) / 2,
        abstainReason=pl.lit(None, dtype=pl.Utf8),
    ).select("code", "week", "surface", "direction", "score", "abstainReason")


def _empty() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "surface": pl.Utf8,
            "direction": pl.Int64,
            "score": pl.Float64,
            "abstainReason": pl.Utf8,
        }
    )


def opine(
    priceMatrix: pl.DataFrame,
    fundMatrix: pl.DataFrame,
    eventMatrix: pl.DataFrame,
    *,
    directionByType: dict[str, int] | None = None,
) -> pl.DataFrame:
    """3축 입력 행렬 → 통합 판독 행렬 (code, week, surface, direction, score, abstainReason).

    Args:
        priceMatrix: table.priceWeekly 산출 (code, week, ret5, ...).
        fundMatrix: table.fundWeekly 산출 (code, week, ep, bm).
        eventMatrix: table.eventWeekly 산출 (code, week, reportType).
        directionByType: 이벤트 방향화 사전 (없으면 이벤트 표면 무발행 = bootstrap 전).

    Returns:
        통합 판독 행렬. 표면은 자동 등재분 전체, 방향은 06 §2 규칙.
    """
    parts = [
        _continuousReadings(priceMatrix, _PRICE_COLS),
        _continuousReadings(fundMatrix, _FUND_COLS),
        _eventReadings(eventMatrix, directionByType or {}),
    ]
    return pl.concat([p for p in parts if p.height]) if any(p.height for p in parts) else _empty()
