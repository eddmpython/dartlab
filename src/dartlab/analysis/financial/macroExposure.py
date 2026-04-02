"""6부 매크로 분석 — 경제 사이클, 매크로 민감도, 자산 신호, 밸류에이션 밴드.

탑다운(매크로→섹터→종목)과 바텀업(기업→매크로 민감도) 양방향 연결.
gather(L1)에서 수집한 매크로 데이터를 core/macroCycle(L0) 해석 함수로 판별하고,
Company의 업종 특성과 연결한다.
"""

from __future__ import annotations

import logging

from dartlab.analysis.financial._memoize import memoized_calc

log = logging.getLogger(__name__)


def _loadMacroIndicator(g, seriesId: str, source: str = "ecos", start: str = "2014-01-01"):
    """gather에서 단일 매크로 지표 로드."""
    try:
        if source == "ecos":
            return g.macro("KR", seriesId, start=start)
        return g.macro(seriesId, start=start)
    except Exception:
        return None


def _getGather():
    """gather 싱글톤 로드 (lazy)."""
    try:
        from dartlab.gather import getDefaultGather

        return getDefaultGather()
    except ImportError:
        return None


def _getLatestValue(df, col: str = "value"):
    """DataFrame의 최신 값."""
    if df is None or len(df) == 0:
        return None
    try:
        sorted_df = df.sort("date", descending=True)
        val = sorted_df[col][0]
        return float(val) if val is not None else None
    except Exception:
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
    except Exception:
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
    except Exception:
        pass
    return None


# ══════════════════════════════════════
# 축 1: 매크로환경
# ══════════════════════════════════════


@memoized_calc
def calcMacroEnvironment(company, *, basePeriod: str | None = None) -> dict | None:
    """현재 경제 사이클 판별 + 이 기업의 포지션.

    gather.macro()로 핵심 신호 수집 → classifyCycle()로 4국면 판별 →
    company 업종의 cyclicality와 매칭하여 현재 사이클에서의 위치를 판정.
    """
    from dartlab.core.finance.macroCycle import classifyCycle
    from dartlab.core.finance.scenario import getElasticity

    g = _getGather()
    if g is None:
        return None

    # 핵심 신호 지표 수집
    hy_df = _loadMacroIndicator(g, "BAMLH0A0HYM2", "fred")
    ts_df = _loadMacroIndicator(g, "T10Y2Y", "fred")
    vix_df = _loadMacroIndicator(g, "VIXCLS", "fred")
    cli_df = _loadMacroIndicator(g, "CLI", "ecos")

    hy_spread = _getLatestValue(hy_df)
    if hy_spread is not None:
        hy_spread *= 100  # % → bp

    indicators = {
        "hy_spread": hy_spread,
        "hy_spread_3m_change": _getMonthlyChange(hy_df, 3),
        "term_spread": _getLatestValue(ts_df),
        "vix": _getLatestValue(vix_df),
        "cli_mom": _getMonthlyChange(cli_df, 1),
    }

    # HY 3m change도 bp 변환
    if indicators["hy_spread_3m_change"] is not None:
        indicators["hy_spread_3m_change"] *= 100

    cycle = classifyCycle(indicators)

    # 기업 업종 → SectorElasticity → cyclicality
    sectorKey = None
    try:
        sector = getattr(company, "sector", None)
        if sector is not None:
            sectorKey = getattr(sector, "sectorKey", None) or getattr(sector, "name", None)
    except AttributeError:
        pass

    elasticity = getElasticity(sectorKey)
    position = cycle.sectorStrategy.get(elasticity.cyclicality, "neutral")

    position_labels = {
        "overweight": "비중확대",
        "neutral": "중립",
        "underweight": "비중축소",
    }

    return {
        "phase": cycle.phase,
        "phaseLabel": cycle.label,
        "confidence": cycle.confidence,
        "signals": list(cycle.signals),
        "sectorKey": sectorKey,
        "cyclicality": elasticity.cyclicality,
        "position": position,
        "positionLabel": position_labels.get(position, position),
        "implication": (f"{cycle.label}기 — {elasticity.cyclicality} 업종 → {position_labels.get(position, position)}"),
        "sectorStrategy": cycle.sectorStrategy,
    }


# ══════════════════════════════════════
# 축 2: 매크로민감도
# ══════════════════════════════════════


@memoized_calc
def calcMacroSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """기업 매출 vs 외생변수 회귀 — 업종 최적 + 범용 병행.

    exogenousAxes에서 업종 최적 3지표를 가져오고, 범용 3지표(금리/환율/IPI)와 비교.
    R-squared가 높은 쪽을 채택. 현재 외생변수 상태 × beta로 매출 방향 추정.
    """
    import polars as pl

    from dartlab.core.finance.exogenousAxes import ExogenousIndicator, getExogenousIndicators

    g = _getGather()
    if g is None:
        return None

    stockCode = getattr(company, "stockCode", None) or getattr(company, "stock_code", None)
    if stockCode is None:
        return None

    # 매출 성장률 시계열
    rev_result = company.select("IS", ["매출액"])
    if rev_result is None:
        return None

    df = rev_result._df if hasattr(rev_result, "_df") else rev_result
    period_cols = [c for c in df.columns if c.endswith("Q4") or c.endswith("A")]
    if len(period_cols) < 4:
        return None

    rev_data = []
    for col in sorted(period_cols):
        val = df[col][0]
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

    # 업종 최적 3지표
    optimal = getExogenousIndicators(stockCode=stockCode)

    # 범용 3지표
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
                    "label": ind.label,
                    "seriesId": ind.seriesId,
                    "axis": ind.axis,
                    "rSquared": round(r2, 3),
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
        "netDirection": net_direction,
        "netDirectionLabel": {"positive": "매출 상승 방향", "negative": "매출 하락 방향", "neutral": "중립"}.get(
            net_direction, "중립"
        ),
    }


# ══════════════════════════════════════
# 축 3: 자산신호
# ══════════════════════════════════════


@memoized_calc
def calcAssetSignals(company, *, basePeriod: str | None = None) -> dict | None:
    """5대 자산 해석 + 기업 업종 연관성."""
    from dartlab.core.finance.macroCycle import interpretAssets
    from dartlab.core.finance.scenario import getElasticity

    g = _getGather()
    if g is None:
        return None

    # 지표 수집
    short_rate_df = _loadMacroIndicator(g, "DGS2", "fred")
    long_rate_df = _loadMacroIndicator(g, "DGS10", "fred")
    fx_df = _loadMacroIndicator(g, "USDKRW", "ecos")
    vix_df = _loadMacroIndicator(g, "VIXCLS", "fred")

    indicators = {
        "short_rate": _getLatestValue(short_rate_df),
        "short_rate_change": _getMonthlyChange(short_rate_df, 3),
        "long_rate": _getLatestValue(long_rate_df),
        "long_rate_change": _getMonthlyChange(long_rate_df, 3),
        "fx_usdkrw": _getLatestValue(fx_df),
        "fx_change_pct": _getYoYChange(fx_df) if fx_df is not None else None,
        "vix": _getLatestValue(vix_df),
        "vix_change": _getMonthlyChange(vix_df, 1),
    }

    assets = interpretAssets(indicators)

    # 기업 업종 연관성
    sectorKey = None
    try:
        sector = getattr(company, "sector", None)
        if sector is not None:
            sectorKey = getattr(sector, "sectorKey", None) or getattr(sector, "name", None)
    except AttributeError:
        pass

    elasticity = getElasticity(sectorKey)

    # 업종 특성에 따라 관련 자산 강조
    relevance = {}
    if elasticity.revenueToFx > 0.3:
        relevance["fx"] = f"수출 비중 높음 — 환율 민감도 {elasticity.revenueToFx:.1f}"
    if elasticity.nimToRate > 0:
        relevance["shortRate"] = f"금리 민감 — NIM 감응도 {elasticity.nimToRate}bp"
    if elasticity.cyclicality == "high":
        relevance["vix"] = "경기민감 업종 — VIX 상승 시 주가 하락 압력"

    return {
        "assets": [
            {
                "asset": a.asset,
                "label": a.label,
                "level": a.level,
                "change": a.change,
                "interpretation": a.interpretation,
                "implication": a.implication,
                "companyRelevance": relevance.get(a.asset),
            }
            for a in assets
        ],
        "sectorKey": sectorKey,
        "cyclicality": elasticity.cyclicality,
    }


# ══════════════════════════════════════
# 축 4: 밸류에이션밴드
# ══════════════════════════════════════


@memoized_calc
def calcValuationBand(company, *, basePeriod: str | None = None) -> dict | None:
    """PER/PBR 정규분포 밴드에서 현재 위치."""
    from dartlab.core.finance.macroCycle import calcMultipleBand

    # ratioSeries에서 PER/PBR 과거 시계열 추출
    try:
        ratios = company.ratios
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

                # snakeId 또는 계정명으로 필터
                row = (
                    ratios.filter(pl.col("snakeId").str.to_lowercase() == key) if "snakeId" in ratios.columns else None
                )

                if row is None or len(row) == 0:
                    continue

                # 기간 컬럼에서 값 추출
                values = []
                for col in row.columns:
                    if col in ("snakeId", "계정명", "account"):
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
        except Exception as e:
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
