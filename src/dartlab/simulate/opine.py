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


def _numericCols(matrix: pl.DataFrame) -> list[str]:
    """행렬의 수치 컬럼 전수 (code·week 제외) = 자동 표면 등재 축. 컬럼 추가 = 표면 추가 (수정 0)."""
    return [c for c, dt in matrix.schema.items() if c not in ("code", "week") and dt.is_numeric()]


def _continuousReadings(matrix: pl.DataFrame, axis: str) -> pl.DataFrame:
    """연속 표면 판독: 수치 컬럼 자동 전수 등재 (surface = "<axis>.<col>", 손 매핑 0, 06 §3).

    주간 랭크 → score, 극단 방향. → (code, week, surface, direction, score). 새 데이터 컬럼이
    table/피드에 추가되면 그대로 표면이 되고 도태는 성적표·인증 깔때기가 한다 (자동흡수).
    """
    out = []
    for col in _numericCols(matrix):
        surface = f"{axis}.{col}"
        r = matrix.select("code", "week", pl.col(col).cast(pl.Float64).alias("raw")).filter(pl.col("raw").is_finite())
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
    extraMatrices: dict[str, pl.DataFrame] | None = None,
) -> pl.DataFrame:
    """입력 행렬 전수 → 통합 판독 행렬 (code, week, surface, direction, score, abstainReason).

    Args:
        priceMatrix: table.priceWeekly 산출 (code, week, ret5, ...).
        fundMatrix: table.fundWeekly 산출 (code, week, ep, bm).
        eventMatrix: table.eventWeekly 산출 (code, week, reportType).
        directionByType: 이벤트 방향화 사전 (없으면 이벤트 표면 무발행 = bootstrap 전).
        extraMatrices: {axis: (code, week, 수치컬럼...)} 추가 피드 행렬 (feeds 레지스트리 산출).
            수치 컬럼마다 "<axis>.<col>" 표면 자동 등재 = 새 엔진 데이터 자동흡수.

    Returns:
        통합 판독 행렬. 표면은 컬럼 자동 전수 등재 (손 매핑 0), 방향은 06 §2 규칙, 도태는 성적표.
    """
    parts = [
        _continuousReadings(priceMatrix, "price"),
        _continuousReadings(fundMatrix, "fund"),
        _eventReadings(eventMatrix, directionByType or {}),
        _leverReadings(eventMatrix, directionByType or {}),
    ]
    for axis, m in (extraMatrices or {}).items():
        parts.append(_continuousReadings(m, axis))
    return pl.concat([p for p in parts if p.height]) if any(p.height for p in parts) else _empty()


def _leverReadings(eventMatrix: pl.DataFrame, directionByType: dict[str, int]) -> pl.DataFrame:
    """레버 원장(levers) + 정제 레버(leverRefine) 표면 판독. 각 레버가 인증 깔때기 대상 = 전수 등재."""
    from dartlab.simulate.leverRefine import refinedEventReadings
    from dartlab.simulate.levers import leverReadings

    if eventMatrix.height == 0:
        return _empty()
    parts = [leverReadings(eventMatrix, directionByType), refinedEventReadings(eventMatrix)]
    parts = [p for p in parts if p.height]
    if not parts:
        return _empty()
    r = pl.concat(parts)
    return r.with_columns(abstainReason=pl.lit(None, dtype=pl.Utf8)).select(
        "code", "week", "surface", "direction", "score", "abstainReason"
    )
