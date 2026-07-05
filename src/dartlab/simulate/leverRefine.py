"""레버 정제 : awaitingMeasurement 레버를 보유 데이터로 실표면화 (L2.5 simulate).

레버 원장(levers)의 "정제 대기(awaitingMeasurement)" 항목 중 실은 보유 데이터로 도출 가능한
것들을 실표면화한다 (10 §1). 진짜 미보유(Form 4 P/S 거래코드·락업 만기 정밀 파싱)만 남기고,
빈도·군집·타이밍·시총 랭크로 도출되는 정제는 지금 낸다. ① 내부자 군집: 문헌 정제 핵심인
"복수내부자 군집·비정기"는 P/S 코드 없이도 공시 빈도로 도출 (실측: KR (code,week) 28%가 복수
공시). ② 락업 만료: 증권신고서 발행 주 + 표준 락업(26주) = 만료 주 회피. ③ 지수 편입: 시총 랭크가
편입 경계(KOSPI200/KOSDAQ150) 근방 = 편입 후보. 방향은 문헌 prior, 인증 깔때기가 도태.

- ``insiderClusterReadings`` : 내부자 공시 군집 강도 (빈도 가중, 정제).
- ``lockupExpiryReadings`` : 증권신고서 + 표준 락업 = 만료 주 회피.
- ``indexInclusionReadings`` : 시총 편입 경계 근방 후보.
- ``refinedEventReadings`` : 이벤트 파생 정제 (군집·락업) 합 (opine 배선).

Layer: L2.5 simulate. reading·polars 만 의존. 신규 데이터 수집 0 (allFilings·시총 재조합).
"""

from __future__ import annotations

import polars as pl

# 시장별 내부자·공모 이벤트 타입 (KR + US v2 정규화).
INSIDER_TYPES = ("임원ㆍ주요주주특정증권등소유상황보고서", "insiderTransaction")
OFFERING_TYPES = ("증권신고서", "securitiesOffering")
_LOCKUP_WEEKS = 26  # 표준 의무보유 락업 (약 6개월)
_CLUSTER_SCALE = 4  # 군집 강도 포화 (공시 5건 이상 = 최대 강도)


def insiderClusterReadings(eventMatrix: pl.DataFrame, *, insiderTypes: tuple[str, ...] = INSIDER_TYPES) -> pl.DataFrame:
    """내부자 공시 군집 강도 → (code, week, surface, direction, score). 정제 = 복수 공시 군집.

    문헌(Cohen-Malloy-Pomorski) 정제의 "복수내부자 군집·비정기"를 P/S 코드 없이 공시 빈도로
    도출한다: 한 주 복수 공시 = 강한 신호. score = 0.5 + 0.5*min((cnt-1)/scale, 1). 방향 long prior.
    """
    sub = eventMatrix.filter(pl.col("reportType").is_in(list(insiderTypes)))
    if sub.height == 0:
        return _empty()
    cw = sub.group_by(["code", "week"]).len().rename({"len": "cnt"})
    return cw.with_columns(
        surface=pl.lit("lever.insiderCluster"),
        direction=pl.lit(1, dtype=pl.Int64),
        score=0.5 + 0.5 * ((pl.col("cnt") - 1) / _CLUSTER_SCALE).clip(0, 1),
    ).select("code", "week", "surface", "direction", "score")


def lockupExpiryReadings(
    eventMatrix: pl.DataFrame, *, offeringTypes: tuple[str, ...] = OFFERING_TYPES, lockupWeeks: int = _LOCKUP_WEEKS
) -> pl.DataFrame:
    """증권신고서 발행 주 + 표준 락업 = 만료 주 회피 → (code, week, surface, direction, score).

    락업 만료 주에 의무보유 물량 출회 = 회피(-1). 만기 주 = 발행 주 + lockupWeeks (iso 주 근사,
    연 52주 기준). 정밀 만기(확약 파싱)는 미보유라 표준 기간 근사 (문헌 표준 180일 = 26주).
    """
    sub = eventMatrix.filter(pl.col("reportType").is_in(list(offeringTypes)))
    if sub.height == 0:
        return _empty()
    # week = isoYear*100 + isoWeek → 총주차 + lockupWeeks → 만료 week (연 52주 근사).
    total = (pl.col("week") // 100) * 52 + (pl.col("week") % 100) + lockupWeeks
    expiryWeek = (total // 52) * 100 + (total % 52).clip(1, 53)
    return (
        sub.with_columns(expiry=expiryWeek)
        .group_by(pl.col("code"), pl.col("expiry").alias("week"))
        .len()
        .with_columns(surface=pl.lit("lever.lockupExpiry"), direction=pl.lit(-1, dtype=pl.Int64), score=pl.lit(0.0))
        .select("code", "week", "surface", "direction", "score")
    )


def indexInclusionReadings(
    marketCap: pl.DataFrame, weekMap: pl.DataFrame, *, lowerPct: float = 0.90, upperPct: float = 0.97
) -> pl.DataFrame:
    """시총 편입 경계 근방 후보 → (code, week, surface, direction, score). 지수 편입 예측(long).

    주말 시총 백분위가 편입 경계 밴드(KOSPI200/KOSDAQ150 근방)에 든 종목 = 편입 후보. 정기
    재구성(6·12월) 규칙 공개라 사전 예측 가능. 방향 long prior (레짐 부패 전제, 인증이 검증).
    """
    if marketCap.height == 0 or weekMap.height == 0:
        return _empty()
    snap = marketCap.join(weekMap, on="date", how="inner")
    weekEndSnap = snap.sort("date").group_by(["code", "week"]).agg(mktcap=pl.col("mktcap").last())
    ranked = weekEndSnap.with_columns(pct=(pl.col("mktcap").rank() / pl.len()).over("week"))
    band = ranked.filter((pl.col("pct") >= lowerPct) & (pl.col("pct") <= upperPct))
    if band.height == 0:
        return _empty()
    return band.with_columns(
        surface=pl.lit("lever.indexInclusion"), direction=pl.lit(1, dtype=pl.Int64), score=pl.lit(0.75)
    ).select("code", "week", "surface", "direction", "score")


def refinedEventReadings(eventMatrix: pl.DataFrame) -> pl.DataFrame:
    """이벤트 파생 정제 레버 합 (내부자 군집 + 락업 만료). opine 배선용."""
    parts = [insiderClusterReadings(eventMatrix), lockupExpiryReadings(eventMatrix)]
    parts = [p for p in parts if p.height]
    return pl.concat(parts) if parts else _empty()


def _empty() -> pl.DataFrame:
    return pl.DataFrame(
        schema={"code": pl.Utf8, "week": pl.Int64, "surface": pl.Utf8, "direction": pl.Int64, "score": pl.Float64}
    )
