"""판독 성적표 : 버킷 중립 채점 + Fama-MacBeth 주단위 t + factor-zoo 허들 (L2.5 simulate).

판독을 정직 규율로 채점해 표면을 도태시킨다 (06 §4). ① 채점 타깃 = forward 5거래일 시장 내
초과를 사이즈(시총) 5분위 버킷 평균으로 다시 중립화 (스타일 편승 차단). ② 원자 = 주(週):
표면별 주간 횡단면 스프레드 시계열 → t (Fama-MacBeth·calendar-time, 이벤트 표본수 부풀림
구조 해결). ③ 연속 표면 = Q5-Q1 분위, 이산 방향 표면 = 상/하 집단. ④ factor-zoo t>3 미달은
"동물원 구분불가", 표본 주 수 미달은 "미검증" 라벨 (성과 숫자 렌더 금지).

이벤트 방향화 bootstrap(deriveEventDirections)도 여기서: train 구간 버킷중립 초과의 타입별
중앙값 게이트(n>=100 & |med|>=1%)로 방향 사전을 낸다 (손 사전 금지, 데이터가 방향을 정함).

Layer: L2.5 simulate. reading·numpy·polars 만 의존 (SPA/부트스트랩 numpy 자급).
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate.reading import (
    CONTINUOUS_DISTINCT_MIN,
    DIRECTION_MIN_ABS_MEDIAN,
    DIRECTION_MIN_N,
    FACTOR_ZOO_T,
    SCORECARD_MIN_WEEKS,
)


def weeklyLabels(weekEnd: pl.DataFrame, dailyPrices: pl.DataFrame) -> pl.DataFrame:
    """주간 채점 라벨: forward 5거래일 시장 내 초과 + 사이즈 버킷 중립 잔차 + 절단 관측 보존.

    절단(censored) 관측: 지평 내 종목이 소멸(상폐·장기정지)했는데 시장 달력은 계속되는 경우,
    마지막 관측가까지의 절단 수익으로 채점에 남긴다 (2026-07-07 레드팀 실증: 기존 scorable 필터가
    회피 표면이 가장 크게 맞춘 관측을 침묵 제거 + uniMean 생존자 편향. 15 §4-2). 절단 수익은
    관측 가능한 마지막 가격까지만 = 소멸 후 미관측 손실 미포함(보수적 하한, 날조 금지). 지평
    미도래(데이터 끝)는 절단이 아니라 pending 유지.

    Args:
        weekEnd: (week, date=그 주 마지막 거래일).
        dailyPrices: (date, code, close, shares, mktcap) 일별.

    Returns:
        (code, week, exRaw, exNeutral, scorable, censored). corpAction(주식수 급변·일수익 40%+)
        제외 (절단 행은 면제: 죽음 자체가 채점 대상).
    """
    df = dailyPrices.filter(pl.col("close") > 0).sort(["code", "date"])
    cal = df.select("date").unique().sort("date").with_row_index("di")
    marketMaxDi = int(cal["di"].max()) if cal.height else 0
    df = df.join(cal, on="date", how="left")
    c = pl.col("close")
    df = df.with_columns(
        fwdClose=c.shift(-5).over("code"),
        fwdShares=pl.col("shares").shift(-5).over("code"),
        fwdMaxAbs=(c / c.shift(1).over("code") - 1).abs().shift(-1).rolling_max(5).over("code").shift(-4),
        lastDi=pl.col("di").max().over("code"),
        lastClose=c.last().over("code"),
    ).with_columns(
        fwdRet=(pl.col("fwdClose") / c - 1),
        corpAction=(
            ((pl.col("fwdShares") / pl.col("shares") - 1).abs() > 0.10) | (pl.col("fwdMaxAbs") > 0.40)
        ).fill_null(True),
    )
    snap = df.join(weekEnd, on="date", how="inner")
    # 절단 = 지평 창이 시장 달력 안(미도래 아님)인데 종목 행이 창 끝 전에 소멸
    censored = pl.col("fwdClose").is_null() & (pl.col("di") + 5 <= marketMaxDi) & (pl.col("lastDi") < pl.col("di") + 5)
    snap = snap.with_columns(
        censored=censored,
        fwdRet=pl.when(censored).then(pl.col("lastClose") / c - 1).otherwise(pl.col("fwdRet")),
    )
    scorable = (pl.col("fwdRet").is_not_null() & ~pl.col("corpAction")) | pl.col("censored")
    snap = snap.with_columns(
        uniMean=pl.col("fwdRet").filter(scorable).mean().over("week"), scorable=scorable
    ).with_columns(exRaw=pl.col("fwdRet") - pl.col("uniMean"))
    snap = (
        snap.filter(pl.col("scorable"))
        .with_columns(sizeBucket=(pl.col("mktcap").rank() / pl.len()).over("week").mul(5).ceil().clip(1, 5))
        .with_columns(exNeutral=pl.col("exRaw") - pl.col("exRaw").mean().over(["week", "sizeBucket"]))
    )
    return snap.select("code", "week", "exRaw", "exNeutral", pl.lit(True).alias("scorable"), "censored")


def deriveEventDirections(
    eventMatrix: pl.DataFrame, labels: pl.DataFrame, *, trainWeekMax: int | None = None
) -> dict[str, int]:
    """이벤트 방향화 bootstrap: train 구간 버킷중립 초과 중앙값 게이트로 타입별 방향 사전.

    Args:
        eventMatrix: (code, week, reportType).
        labels: weeklyLabels 산출.
        trainWeekMax: 이 주 이하만 방향 도출 (OOS 분리). None = 전 구간.

    Returns:
        {reportType: +1|-1} 게이트(n>=DIRECTION_MIN_N & |median|>=DIRECTION_MIN_ABS_MEDIAN) 통과분.
    """
    j = eventMatrix.join(labels.select("code", "week", "exNeutral"), on=["code", "week"], how="inner")
    if trainWeekMax is not None:
        j = j.filter(pl.col("week") <= trainWeekMax)
    dirTable = (
        j.group_by("reportType")
        .agg(n=pl.len(), med=pl.col("exNeutral").median())
        .filter((pl.col("n") >= DIRECTION_MIN_N) & (pl.col("med").abs() >= DIRECTION_MIN_ABS_MEDIAN))
        .with_columns(direction=pl.col("med").sign().cast(pl.Int64))
    )
    return {r["reportType"]: r["direction"] for r in dirTable.iter_rows(named=True)}


def _weeklyT(diff: pl.Series) -> float:
    if diff.len() < 2 or diff.std() in (None, 0):
        return 0.0
    return float(diff.mean() / (diff.std() / (diff.len() ** 0.5)))


def _surfaceSpreadByWeek(d: pl.DataFrame) -> tuple[pl.DataFrame | None, str]:
    """단일 표면 조인 df → (주별 스프레드 (week, spread), kind). 채점 불가면 (None, kind).

    연속 표면(고유 score > CONTINUOUS_DISTINCT_MIN)은 주별 Q5-Q1 분위 스프레드, 이산 방향 표면은
    상/하 집단 스프레드. 주별 1값 (Fama-MacBeth 원자) 시계열을 낸다. 기권행(score null) 제외.
    """
    d = d.filter(pl.col("score").is_not_null())  # 기권행은 스프레드에서 제외 (기권률은 별도 채점)
    if d.height == 0:
        return None, "미채점"
    if d["score"].n_unique() > CONTINUOUS_DISTINCT_MIN:
        dq = d.with_columns(q=(pl.col("score").rank() / pl.len()).over("week").mul(5).ceil().clip(1, 5).cast(pl.Int32))
        wk = dq.group_by(["week", "q"]).agg(ex=pl.col("exNeutral").mean())
        sp = wk.pivot(values="ex", index="week", on="q").drop_nulls()
        kind, hi, lo = "분위", "5", "1"
    else:
        wk = (
            d.with_columns(
                side=pl.when(pl.col("score") > 0.5).then(1).when(pl.col("score") < 0.5).then(0).otherwise(None)
            )
            .drop_nulls("side")
            .group_by(["week", "side"])
            .agg(ex=pl.col("exNeutral").mean())
        )
        sp = wk.pivot(values="ex", index="week", on="side").drop_nulls()
        kind, hi, lo = "방향", "1", "0"
    if hi not in sp.columns or lo not in sp.columns:
        return None, kind
    return sp.select("week", spread=(pl.col(hi) - pl.col(lo))).sort("week"), kind


def surfaceWeeklySpreads(readings: pl.DataFrame, labels: pl.DataFrame, *, valueCol: str = "exNeutral") -> pl.DataFrame:
    """표면별 주단위 스프레드 시계열 → long (surface, week, spread). certify 부트스트랩 입력.

    Args:
        readings: (code, week, surface, direction, score) 판독.
        labels: weeklyLabels 산출.
        valueCol: 채점 값 컬럼 ("exNeutral" gross 버킷중립 | "netExNeutral" net-of-cost).

    Returns:
        (surface, week, spread) long. 표면별 주 1값 (Fama-MacBeth 원자). 다중검정 인증(certify)이
        이 시계열들로 정상성 부트스트랩해 타입 간 상관을 보존한다.
    """
    j = readings.join(
        labels.select("code", "week", pl.col(valueCol).alias("exNeutral")), on=["code", "week"], how="inner"
    )
    out = []
    for surf in j["surface"].unique().sort():
        series, _ = _surfaceSpreadByWeek(j.filter(pl.col("surface") == surf))
        if series is not None:
            out.append(series.with_columns(surface=pl.lit(surf)).select("surface", "week", "spread"))
    if not out:
        return pl.DataFrame(schema={"surface": pl.Utf8, "week": pl.Int64, "spread": pl.Float64})
    return pl.concat(out)


def _abstainRateBySurface(readings: pl.DataFrame) -> dict[str, float]:
    """표면별 기권률 = score null 비율 (기권도 채점 대상, 06 §2). score 컬럼 없으면 빈 dict."""
    if "score" not in readings.columns:
        return {}
    ar = readings.group_by("surface").agg(abstainRate=pl.col("score").is_null().mean())
    return {r["surface"]: float(r["abstainRate"] or 0.0) for r in ar.iter_rows(named=True)}


def traitConditionalScorecard(
    readings: pl.DataFrame, labels: pl.DataFrame, traitByCode: pl.DataFrame, *, traitName: str = "trait"
) -> pl.DataFrame:
    """형질 조건부 성적표 (11 §5): 표면 x 형질 버킷 셀 → 어떤 형질이 어떤 표면을 가르는지 측정.

    형질(예 CB 발행 이력 0 vs 1+)이 표면의 예측력을 조건화하는지 셀 단위로 채점한다. 셀 신설은
    자동(전수)이되 주장 승격은 06 §4 깔때기 그대로 (주단위 t → 표본 게이트 미달 "미검증"). 형질
    수백 x 표면 수백 = 셀 폭발 주의: 여기서는 셀 성적만 내고, 승격 판정은 certify 로 위임한다.

    Args:
        readings: (code, week, surface, direction, score).
        labels: weeklyLabels 산출.
        traitByCode: (code, traitBucket) 형질 버킷 (예 profile 자금조달 이력 0/1+). 결정론.
        traitName: 형질 축 이름 (라벨).

    Returns:
        (surface, traitBucket, traitName, kind, spread, t, weeks, n, verdict). 같은 표면의 버킷 간
        t 차이가 형질의 조건화 실측(예 유상증자 x CB 이력 = 드리프트 1.5배).
    """
    j = (
        readings.join(labels.select("code", "week", "exNeutral"), on=["code", "week"], how="inner")
        .join(traitByCode.select("code", "traitBucket"), on="code", how="inner")
        .filter(pl.col("score").is_not_null())
    )
    rows = []
    for surf in j["surface"].unique().sort():
        for bucket in j.filter(pl.col("surface") == surf)["traitBucket"].unique().sort():
            d = j.filter((pl.col("surface") == surf) & (pl.col("traitBucket") == bucket))
            series, kind = _surfaceSpreadByWeek(d)
            if series is None:
                continue
            diff = series["spread"]
            t = _weeklyT(diff)
            weeks = series.height
            verdict = (
                "미검증" if weeks < SCORECARD_MIN_WEEKS else ("통과" if abs(t) >= FACTOR_ZOO_T else "동물원구분불가")
            )
            rows.append(
                {
                    "surface": surf,
                    "traitBucket": str(bucket),
                    "traitName": traitName,
                    "kind": kind,
                    "spread": float(diff.mean()),
                    "t": t,
                    "weeks": weeks,
                    "n": d.height,
                    "verdict": verdict,
                }
            )
    schema = {
        "surface": pl.Utf8,
        "traitBucket": pl.Utf8,
        "traitName": pl.Utf8,
        "kind": pl.Utf8,
        "spread": pl.Float64,
        "t": pl.Float64,
        "weeks": pl.Int64,
        "n": pl.Int64,
        "verdict": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema).sort(["surface", "traitBucket"]) if rows else pl.DataFrame(schema=schema)


def scorecard(readings: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    """표면별 버킷 중립 스프레드 + 주단위 t + 기권률. → (surface, kind, spread, t, weeks, n, abstainRate, verdict).

    연속 표면(고유 score > CONTINUOUS_DISTINCT_MIN)은 주별 Q5-Q1 분위, 이산 방향 표면은 상/하
    집단. verdict = "통과"(|t|>=FACTOR_ZOO_T) | "동물원구분불가" | "미검증"(주<SCORECARD_MIN_WEEKS).
    기권행(score null)은 스프레드에서 제외하되 기권률로 별도 채점 (silent 누락 0).
    """
    abstainMap = _abstainRateBySurface(readings)
    j = readings.join(labels.select("code", "week", "exNeutral"), on=["code", "week"], how="inner")
    rows = []
    for surf in j["surface"].unique().sort():
        d = j.filter(pl.col("surface") == surf)
        series, kind = _surfaceSpreadByWeek(d)
        if series is None:
            continue
        diff = series["spread"]
        t = _weeklyT(diff)
        weeks = series.height
        verdict = "미검증" if weeks < SCORECARD_MIN_WEEKS else ("통과" if abs(t) >= FACTOR_ZOO_T else "동물원구분불가")
        rows.append(
            {
                "surface": surf,
                "kind": kind,
                "spread": float(diff.mean()),
                "t": t,
                "weeks": weeks,
                "n": d.height,
                "abstainRate": abstainMap.get(surf, 0.0),
                "verdict": verdict,
            }
        )
    return (
        pl.DataFrame(rows).sort("t", descending=True)
        if rows
        else pl.DataFrame(
            schema={
                "surface": pl.Utf8,
                "kind": pl.Utf8,
                "spread": pl.Float64,
                "t": pl.Float64,
                "weeks": pl.Int64,
                "n": pl.Int64,
                "abstainRate": pl.Float64,
                "verdict": pl.Utf8,
            }
        )
    )
