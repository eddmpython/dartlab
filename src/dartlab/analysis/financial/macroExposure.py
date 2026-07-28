"""6부 매크로 분석 — 기업-매크로 연결 (매크로 민감도, 밸류에이션 밴드).

기업 매출과 외생변수의 관계, 기업 멀티플 밴드 등 Company가 필수인 분석.
시장 자체 매크로 분석(사이클, 자산해석 등)은 독립 엔진 dartlab.macro()가 담당.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

from dartlab.core.memory import memoizedCalc

log = logging.getLogger(__name__)

MACRO_EXPOSURE_MODEL_VERSION = "macroExposure.v1"
MACRO_EXPOSURE_METHOD = "annual_revenue_yoy_macro_yoy_ols"
MACRO_EXPOSURE_TARGET_METRIC = "annualRevenueYoY"
MACRO_EXPOSURE_MIN_OBS = 5


def _modelSpec() -> dict:
    return {
        "method": MACRO_EXPOSURE_METHOD,
        "modelVersion": MACRO_EXPOSURE_MODEL_VERSION,
        "targetMetric": MACRO_EXPOSURE_TARGET_METRIC,
        "minObs": MACRO_EXPOSURE_MIN_OBS,
    }


def _loadMacroIndicator(g, seriesId: str, source: str = "ecos", start: str = "2014-01-01"):
    """gather에서 단일 매크로 지표 로드 — source로 KR/US 자동 분기."""
    try:
        if source == "ecos":
            return g.macro("KR", seriesId, start=start)
        return g.macro("US", seriesId, start=start)
    except (KeyError, ValueError, TypeError, AttributeError, ImportError):
        return None


def _getGather():
    """gather 싱글톤 로드 — MacroDataProvider 위임 (정공법 B+C)."""
    try:
        from dartlab.core.di import getMacroProvider

        return getMacroProvider().getDefaultGather()
    except (ImportError, AttributeError, RuntimeError):
        return None


def _getLatestValue(df, col: str = "value"):
    """DataFrame의 최신 값."""
    if df is None or len(df) == 0:
        return None
    try:
        sorted_df = df.sort("date", descending=True)
        val = sorted_df[col][0]
        return float(val) if val is not None else None
    except (KeyError, ValueError, TypeError, AttributeError, ImportError):
        return None


def _getMonthlyChange(df, months: int = 3, col: str = "value"):
    """N개월 전 대비 변화."""
    if df is None or len(df) < months + 1:
        return None
    try:
        sorted_df = df.sort("date", descending=True)
        latest = sorted_df[col][0]
        past = sorted_df[col][months]
        if latest is not None and past is not None and past != 0:
            return float(latest - past)
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return None


def _getYoYChange(df, col: str = "value"):
    """YoY 변화율 (%)."""
    if df is None or len(df) < 13:
        return None
    try:
        import polars as pl

        monthly = df.sort("date").group_by_dynamic("date", every="1mo").agg(pl.col(col).last())
        if len(monthly) < 13:
            return None
        latest = monthly[col][-1]
        year_ago = monthly[col][-13]
        if latest is not None and year_ago is not None and year_ago != 0:
            return float((latest / year_ago - 1) * 100)
    except (KeyError, IndexError, ValueError, TypeError, ImportError):
        pass
    return None


def _qualityFromSelected(selected: list[dict], *, stockCode: str) -> dict:
    """Macro Lens가 소비하는 회사 단위 매크로 노출 품질 블록."""
    if not selected:
        return {
            **_modelSpec(),
            "status": "blocked",
            "reason": "회사 매출과 매크로 지표의 겹친 표본이 부족합니다.",
            "blockedReason": "selected macro regression absent",
            "missingEvidence": ["selected indicator", "nObs", "R²", "window", "sourceRef"],
            "sourceRef": f"analysis.macroExposure:{stockCode}",
            "nObs": None,
            "rSquared": None,
            "window": None,
            "frequency": "annual",
            "lagMonths": None,
            "coverage": "missing",
        }

    best = max(selected, key=lambda row: row.get("rSquared", 0) or 0)
    nObs = best.get("nObs")
    rSquared = best.get("rSquared")
    missingEvidence = []
    if not isinstance(nObs, int) or nObs < MACRO_EXPOSURE_MIN_OBS:
        missingEvidence.append(f"nObs>={MACRO_EXPOSURE_MIN_OBS}")
    if not isinstance(rSquared, int | float) or rSquared < 0.2:
        missingEvidence.append("R²>=0.20")
    if not best.get("sourceRef"):
        missingEvidence.append("sourceRef")

    return {
        **_modelSpec(),
        "status": "qualitativeOnly" if missingEvidence else "quantCandidate",
        "reason": "연간 매출 성장률과 매크로 지표 변화율의 공개 품질 계약입니다.",
        "blockedReason": " · ".join(missingEvidence) if missingEvidence else "",
        "missingEvidence": missingEvidence,
        "sourceRef": best.get("sourceRef") or f"analysis.macroExposure:{stockCode}",
        "nObs": nObs,
        "rSquared": rSquared,
        "window": best.get("window"),
        "frequency": "annual",
        "lagMonths": best.get("lagMonths"),
        "coverage": "company",
    }


def _revenueGrowthRows(years: Sequence[str | int], revenue: Sequence[float | int | None]) -> list[dict]:
    """연매출 배열을 회귀 입력용 성장률 row로 변환한다."""
    rows = []
    for year, value in zip(years, revenue):
        if value is None:
            continue
        try:
            y = int(str(year)[:4])
            v = float(value)
        except (TypeError, ValueError):
            continue
        rows.append({"year": y, "revenue": v})
    rows.sort(key=lambda row: row["year"])

    growthRows = []
    for prev, cur in zip(rows, rows[1:]):
        prevRev = prev["revenue"]
        if prevRev == 0:
            continue
        growthRows.append({"year": cur["year"], "growth": cur["revenue"] / abs(prevRev) - 1})
    return growthRows


def _regressAnnualIndicators(
    *,
    stockCode: str,
    growthRows: list[dict],
    indicators: Sequence,
    macroAnnual: Mapping[tuple[str, str], Mapping[int, float]],
) -> list[dict]:
    """연매출 성장률과 연평균 매크로 지표 변화율의 품질 row를 계산한다."""
    results = []
    years = [int(row["year"]) for row in growthRows]
    growth = [float(row["growth"]) for row in growthRows]
    if len(years) < 3:
        return results

    for ind in indicators:
        source = str(getattr(ind, "source", "")).lower()
        seriesId = str(getattr(ind, "seriesId", ""))
        annual = macroAnnual.get((source, seriesId))
        if not annual:
            continue

        values = [annual.get(y) for y in years]
        validPairs = [(i, gVal, v) for i, (gVal, v) in enumerate(zip(growth, values)) if v is not None]
        if len(validPairs) < 3:
            continue

        gVals = [float(p[1]) for p in validPairs]
        iVals = [float(p[2]) for p in validPairs]
        validYears = [years[p[0]] for p in validPairs]

        indicatorChanges = []
        for j in range(1, len(iVals)):
            prevVal = iVals[j - 1]
            if prevVal != 0:
                indicatorChanges.append((iVals[j] - prevVal) / abs(prevVal))
            else:
                indicatorChanges.append(0.0)

        gSubset = gVals[1:]
        if len(gSubset) < 2 or len(indicatorChanges) < 2:
            continue

        nObs = len(gSubset)
        gMean = sum(gSubset) / len(gSubset)
        iMean = sum(indicatorChanges) / len(indicatorChanges)
        sst = sum((v - gMean) ** 2 for v in gSubset)
        cov = sum((gSubset[k] - gMean) * (indicatorChanges[k] - iMean) for k in range(len(gSubset)))
        iVar = sum((v - iMean) ** 2 for v in indicatorChanges)
        r2 = (cov**2) / (sst * iVar) if sst > 0 and iVar > 0 else 0.0
        latestChange = indicatorChanges[-1] if indicatorChanges else 0.0
        betaSign = 1 if cov > 0 else -1
        impact = "상승" if latestChange * betaSign > 0 else "하락"

        results.append(
            {
                **_modelSpec(),
                "label": getattr(ind, "label", seriesId),
                "seriesId": seriesId,
                "axis": getattr(ind, "axis", ""),
                "rSquared": round(r2, 3),
                "nObs": nObs,
                "window": f"{validYears[1]}-{validYears[-1]} annual",
                "frequency": "annual",
                "lagMonths": 0,
                "coverage": "company",
                "sourceRef": f"analysis.macroExposure:{stockCode}:{seriesId}",
                "sourceRefs": [
                    "finance.parquet:annualRevenue",
                    f"macro/{source}/observations.parquet#{seriesId}",
                ],
                "latestChange": round(latestChange * 100, 1),
                "impact": impact,
            }
        )

    return results


def calcMacroExposureFromAnnualRevenue(
    *,
    stockCode: str,
    years: Sequence[str | int],
    revenue: Sequence[float | int | None],
    macroAnnual: Mapping[tuple[str, str], Mapping[int, float]],
    currency: str = "KRW",
    industry: str | None = None,
    product: str | None = None,
) -> dict:
    """회사 객체 없이 public prebuild가 소비하는 매크로 노출 품질 패킷.

    UI가 회귀를 다시 만들지 않도록, 기존 ``finance.json`` 생성 단계에서 회사별
    연매출과 macro observation 연평균만으로 최소 품질 상태를 계산한다.
    """
    from dartlab.gather.mapping.exogenousAxes import ExogenousIndicator, getExogenousIndicators

    growthRows = _revenueGrowthRows(years, revenue)
    if currency == "USD":
        optimal = []
        generic = [
            ExogenousIndicator("FEDFUNDS", "fred", "Federal Funds Rate", "financial"),
            ExogenousIndicator("DTWEXBGS", "fred", "USD Index", "fx"),
            ExogenousIndicator("INDPRO", "fred", "Industrial Production", "domestic"),
        ]
    else:
        optimal = getExogenousIndicators(industry=industry, product=product)
        generic = [
            ExogenousIndicator("BASE_RATE", "ecos", "기준금리", "financial"),
            ExogenousIndicator("USDKRW", "ecos", "원/달러", "fx"),
            ExogenousIndicator("IPI", "ecos", "산업생산", "domestic"),
        ]

    optimalResults = _regressAnnualIndicators(
        stockCode=stockCode,
        growthRows=growthRows,
        indicators=optimal,
        macroAnnual=macroAnnual,
    )
    genericResults = _regressAnnualIndicators(
        stockCode=stockCode,
        growthRows=growthRows,
        indicators=generic,
        macroAnnual=macroAnnual,
    )

    optBest = max((r["rSquared"] for r in optimalResults), default=0)
    genBest = max((r["rSquared"] for r in genericResults), default=0)
    if optBest >= genBest:
        selected = optimalResults
        selectedLabel = "업종최적"
    else:
        selected = genericResults
        selectedLabel = "범용"

    upCount = sum(1 for r in selected if r["impact"] == "상승")
    downCount = sum(1 for r in selected if r["impact"] == "하락")
    netDirection = "positive" if upCount > downCount else "negative" if downCount > upCount else "neutral"

    return {
        "stockCode": stockCode,
        "selected": selected[:3],
        "selectedSource": selectedLabel,
        "optimalBestR2": optBest,
        "genericBestR2": genBest,
        "exposureQuality": _qualityFromSelected(selected, stockCode=stockCode),
        "netDirection": netDirection,
        "netDirectionLabel": {"positive": "매출 상승 방향", "negative": "매출 하락 방향", "neutral": "중립"}.get(
            netDirection, "중립"
        ),
    }


# ══════════════════════════════════════
# 매크로민감도 — 기업 매출 vs 외생변수
# ══════════════════════════════════════


@memoizedCalc
def calcMacroSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """기업 매출 vs 외생변수 회귀 — 업종 최적 + 범용 병행.

    exogenousAxes에서 업종 최적 3지표를 가져오고, 범용 3지표(금리/환율/IPI)와 비교.
    R-squared가 높은 쪽을 채택. 현재 외생변수 상태 × beta로 매출 방향 추정.

    Capabilities:
        - 매출-매크로 회귀 (업종 최적 + 범용) + 종합 방향 라벨.

    Guide:
        R² 높은 쪽 채택 → 외생 변수 현재값 × beta = 방향.

    When:
        "거시 환경이 이 회사 매출에 어떻게?" 매크로 의도 진입 시.

    How:
        IS 매출 시계열 + exogenous indicators → 회귀 → R²/impact.

    Requires:
        gather 매크로 시계열 + IS 매출 ≥ 4 년.

    Raises:
        없음 (데이터 부재 시 None).

    Example:
        >>> calcMacroSensitivity(c)["netDirection"]
        "positive"

    See Also:
        - calcValuationBand : 매크로 시나리오별 밴드
        - exogenousAxes : 업종 최적 지표 룩업

    AIContext:
        AI 답변 "금리 인상시 이 회사 영향" 코너 핵심 evidence.

    Returns
    -------
    dict
        stockCode : str — 종목코드
        optimalIndicators : list[dict] — 업종 최적 지표별 회귀 결과 (label, rSquared, impact)
        genericIndicators : list[dict] — 범용 3지표 회귀 결과
        selected : list[dict] — 채택된 지표 그룹 (R2 높은 쪽)
        selectedSource : str — 채택 출처 ("업종최적" | "범용")
        optimalBestR2 : float — 업종 최적 최고 R-squared
        genericBestR2 : float — 범용 최고 R-squared
        netDirection : str — 종합 매출 방향 ("positive" | "negative" | "neutral")
        netDirectionLabel : str — 종합 방향 한글 라벨
        exposureQuality : dict — nObs/R²/window/lag/coverage/sourceRef 품질 계약
    """
    import polars as pl

    from dartlab.gather.mapping.exogenousAxes import ExogenousIndicator, getExogenousIndicators

    g = _getGather()
    if g is None:
        return None

    stockCode = getattr(company, "stockCode", None)
    if stockCode is None:
        return None

    # 매출 성장률 시계열 — flow 헬퍼 경유 (Q4 분기 단독값 함정 차단)
    from dartlab.core.utils.helpers import (
        annualColsFromPeriods,
        toDictBySnakeId,
    )

    rev_result = company.select("IS", ["매출액"])
    if rev_result is None:
        return None

    parsed = toDictBySnakeId(rev_result)
    if parsed is None:
        return None
    isData, isPeriods = parsed
    revRow = isData.get("매출액", {})
    yCols = annualColsFromPeriods(isPeriods)
    if len(yCols) < 4:
        return None
    # Phase 15 A1: Q4 함정 제거 — annualSumFlow 로 4분기 합산 (주석과 실제 이행 일치)
    from dartlab.core.utils.flow import annualSumFlow

    allIsPeriods = set(isPeriods)
    rev_data = []
    for col in sorted(yCols):
        val = annualSumFlow(revRow, col, allIsPeriods, withFallback=True)
        year_str = col.replace("Q4", "").replace("A", "")
        try:
            year = int(year_str)
        except ValueError:
            continue
        if val is not None:
            rev_data.append({"year": year, "revenue": float(val)})

    if len(rev_data) < 4:
        return None

    rev_df = pl.DataFrame(rev_data).sort("year")
    rev_df = rev_df.with_columns((pl.col("revenue") / pl.col("revenue").shift(1) - 1).alias("growth")).drop_nulls(
        "growth"
    )

    years = rev_df["year"].to_list()
    growth = rev_df["growth"].to_list()

    if len(years) < 3:
        return None

    # KR/US 자동 분기 — currency 우선, 없으면 KR 기본
    currency = getattr(company, "currency", "KRW")

    if currency == "USD":
        # US 종목: getExogenousIndicators는 KR 전용이므로 스킵, 범용 FRED 지표만 사용
        optimal = []
        generic = [
            ExogenousIndicator("FEDFUNDS", "fred", "Federal Funds Rate", "financial"),
            ExogenousIndicator("DTWEXBGS", "fred", "USD Index", "fx"),
            ExogenousIndicator("INDPRO", "fred", "Industrial Production", "domestic"),
        ]
    else:
        # KR 종목: 업종 최적 3지표 + 범용 ECOS 3지표
        optimal = getExogenousIndicators(stockCode=stockCode)
        generic = [
            ExogenousIndicator("BASE_RATE", "ecos", "기준금리", "financial"),
            ExogenousIndicator("USDKRW", "ecos", "원/달러", "fx"),
            ExogenousIndicator("IPI", "ecos", "산업생산", "domestic"),
        ]

    def _regress(indicators: list[ExogenousIndicator]):
        """각 지표와 매출 성장률의 R-squared 계산."""
        results = []
        for ind in indicators:
            ind_df = _loadMacroIndicator(g, ind.seriesId, ind.source)
            if ind_df is None or len(ind_df) == 0:
                continue

            # 연간 평균
            annual = (
                ind_df.with_columns(pl.col("date").dt.year().alias("year"))
                .group_by("year")
                .agg(pl.col("value").mean())
                .sort("year")
            )

            # years와 매칭
            ind_values = []
            for y in years:
                row = annual.filter(pl.col("year") == y)
                if len(row) > 0:
                    ind_values.append(float(row["value"][0]))
                else:
                    ind_values.append(None)

            # None 필터링 + 변화율
            valid_pairs = [(i, g_val, v) for i, (g_val, v) in enumerate(zip(growth, ind_values)) if v is not None]
            if len(valid_pairs) < 3:
                continue

            g_vals = [p[1] for p in valid_pairs]
            i_vals = [p[2] for p in valid_pairs]
            valid_years = [years[p[0]] for p in valid_pairs]

            # 지표 변화율
            i_changes = []
            for j in range(1, len(i_vals)):
                if i_vals[j - 1] != 0:
                    i_changes.append((i_vals[j] - i_vals[j - 1]) / abs(i_vals[j - 1]))
                else:
                    i_changes.append(0)

            g_subset = g_vals[1:]
            if len(g_subset) < 2 or len(i_changes) < 2:
                continue
            nObs = len(g_subset)
            window = f"{valid_years[1]}-{valid_years[-1]} annual" if len(valid_years) >= 2 else "annual"

            # R-squared
            g_mean = sum(g_subset) / len(g_subset)
            i_mean = sum(i_changes) / len(i_changes)
            sst = sum((v - g_mean) ** 2 for v in g_subset)
            cov = sum((g_subset[k] - g_mean) * (i_changes[k] - i_mean) for k in range(len(g_subset)))
            i_var = sum((v - i_mean) ** 2 for v in i_changes)

            r2 = (cov**2) / (sst * i_var) if sst > 0 and i_var > 0 else 0

            # 현재 지표 변화와 최근 매출 방향
            latest_i_change = i_changes[-1] if i_changes else 0
            beta_sign = 1 if cov > 0 else -1
            impact = "상승" if latest_i_change * beta_sign > 0 else "하락"

            results.append(
                {
                    **_modelSpec(),
                    "label": ind.label,
                    "seriesId": ind.seriesId,
                    "axis": ind.axis,
                    "rSquared": round(r2, 3),
                    "nObs": nObs,
                    "window": window,
                    "frequency": "annual",
                    "lagMonths": 0,
                    "coverage": "company",
                    "sourceRef": f"analysis.macroExposure:{stockCode}:{ind.seriesId}",
                    "sourceRefs": [
                        "Company.select:IS:매출액",
                        f"macro/{ind.source}/observations.parquet#{ind.seriesId}",
                    ],
                    "latestChange": round(latest_i_change * 100, 1),
                    "impact": impact,
                }
            )

        return results

    optimal_results = _regress(optimal)
    generic_results = _regress(generic)

    # 최고 R-squared 비교
    opt_best = max((r["rSquared"] for r in optimal_results), default=0)
    gen_best = max((r["rSquared"] for r in generic_results), default=0)

    # 더 나은 쪽 선택
    if opt_best >= gen_best:
        selected = optimal_results
        selectedLabel = "업종최적"
    else:
        selected = generic_results
        selectedLabel = "범용"

    # 종합 방향
    up_count = sum(1 for r in selected if r["impact"] == "상승")
    down_count = sum(1 for r in selected if r["impact"] == "하락")
    net_direction = "positive" if up_count > down_count else "negative" if down_count > up_count else "neutral"

    return {
        "stockCode": stockCode,
        "optimalIndicators": optimal_results,
        "genericIndicators": generic_results,
        "selected": selected,
        "selectedSource": selectedLabel,
        "optimalBestR2": opt_best,
        "genericBestR2": gen_best,
        "exposureQuality": _qualityFromSelected(selected, stockCode=stockCode),
        "netDirection": net_direction,
        "netDirectionLabel": {"positive": "매출 상승 방향", "negative": "매출 하락 방향", "neutral": "중립"}.get(
            net_direction, "중립"
        ),
    }


# ══════════════════════════════════════
# 밸류에이션밴드 — 기업 PER/PBR 정규분포 밴드
# ══════════════════════════════════════


@memoizedCalc
def calcValuationBand(company, *, basePeriod: str | None = None) -> dict | None:
    """PER/PBR 정규분포 밴드에서 현재 위치.

    Capabilities:
        - PER/PBR 정규분포 밴드 + 현재 위치 zone 라벨.

    Guide:
        과거 분포 평균/표준편차 기준 z-score → 저평가/적정/고평가.

    When:
        "지금 비싼가 싼가?" 멀티플 평가 의도 진입 시.

    How:
        ratios show → PER/PBR 시계열 → calcMultipleBand → zone 합성.

    Requires:
        company.panel("ratios") 반환 + PER/PBR 시계열.

    Raises:
        없음 (예외 시 None).

    Example:
        >>> calcValuationBand(c)["overallZone"]
        "저평가"

    See Also:
        - calcMacroSensitivity : 매크로 영향
        - macro.cycles.macroCycle : 밴드 계산 원본

    AIContext:
        AI "현재 멀티플 위치" 카드 zone/percentile 표시에 사용.

    Returns
    -------
    dict
        bands : dict — PER/PBR별 밴드 정보 (metric, current, mean, std, percentile, zone, zoneLabel, dataPoints)
        overallZone : str — 종합 판정 ("저평가" | "고평가" | "부분 저평가" | "부분 고평가" | "적정")
    """
    import importlib

    calcMultipleBand = importlib.import_module("dartlab.macro.cycles.macroCycle").calcMultipleBand

    # ratioSeries에서 PER/PBR 과거 시계열 추출 (show 은퇴 → panel native ratios)
    try:
        ratios = company.panel("ratios")
        if ratios is None:
            return None
    except (AttributeError, TypeError):
        return None

    result = {}

    for metric, key in [("PER", "per"), ("PBR", "pbr")]:
        try:
            # ratios DataFrame에서 해당 행 추출
            if hasattr(ratios, "columns"):
                import polars as pl

                # snakeId 또는 항목으로 필터
                row = (
                    ratios.filter(pl.col("snakeId").str.to_lowercase() == key) if "snakeId" in ratios.columns else None
                )

                if row is None or len(row) == 0:
                    continue

                # 기간 컬럼에서 값 추출
                values = []
                for col in row.columns:
                    if col in ("snakeId", "항목", "account"):
                        continue
                    val = row[col][0]
                    if val is not None:
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            pass

                if len(values) < 5:
                    continue

                current = values[0]  # 가장 최근
                band = calcMultipleBand(values, current, metric)
                if band is not None:
                    result[key] = {
                        "metric": band.metric,
                        "current": band.current,
                        "mean": band.mean,
                        "std": band.std,
                        "percentile": band.percentile,
                        "zone": band.zone,
                        "zoneLabel": band.zLabel,
                        "dataPoints": len(values),
                    }
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            log.debug("밸류에이션밴드 %s 실패: %s", metric, e)
            continue

    if not result:
        return None

    # 종합 zone
    zones = [v["zone"] for v in result.values()]
    if all(z == "cheap" for z in zones):
        overall = "저평가"
    elif all(z == "expensive" for z in zones):
        overall = "고평가"
    elif any(z == "cheap" for z in zones):
        overall = "부분 저평가"
    elif any(z == "expensive" for z in zones):
        overall = "부분 고평가"
    else:
        overall = "적정"

    return {
        "bands": result,
        "overallZone": overall,
    }
