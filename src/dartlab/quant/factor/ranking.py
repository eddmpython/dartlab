"""멀티팩터 복합 순위 (횡단면).

학술 근거: Asness et al. (2013) — Value and Momentum Everywhere.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.quant.screen.dataAccess import loadScanParquet
from dartlab.quant.strategy.metrics import pearsonCorr, spearmanCorr
from dartlab.synth.scanBridge import (
    extractAnnualConsolidated,
    getAccountValue,
    isEdgarSchema,
)

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Grinold Ch.5-6 — 횡단면 IC
# ══════════════════════════════════════════════════════════════════════
#
# IC_t = corr(factorScore_{i,t}, forwardReturn_{i, t→t+h})  for all i
#
# 단일 종목 시계열 IR (factor.py) 과 구분. 이 모듈은 **한 시점에서 전종목 팩터
# 스코어가 종목을 잘 정렬하는가** 의 Grinold 정의 IC.


def calcCrossSectionIC(
    factorScores: dict[str, float],
    forwardReturns: dict[str, float],
) -> dict:
    """한 시점의 횡단면 IC (Pearson + Spearman + t-stat).

    Capabilities:
        - 종목별 factorScore vs forwardReturn → Pearson + Spearman + t-stat 단일 시점
        - n ≥ 10 필수 + perfect correlation 안전 처리 (1.0 시 t inf 회피)

    Args:
        factorScores: ``{stockCode: factorScore}``.
        forwardReturns: ``{stockCode: forward_return}``.

    Returns:
        dict — ic_pearson/ic_spearman/n_stocks/t_stat/is_significant.

    Guide:
        Grinold-Kahn Ch.5-6 정의. IC ≥ 0.05 = useful, ≥ 0.10 = strong. |t| > 2.0 = 5% 유의.

    When:
        팩터 단일 시점 효과 검증 + AI 횡단면 alpha 답변.

    How:
        공통 종목 → x/y array → NaN 제거 → pearson/spearman → t-stat.

    Requires:
        공통 종목 ≥ 10.

    Raises:
        없음.

    Example:
        >>> r = calcCrossSectionIC({'A': 1, 'B': 2}, {'A': 0.1, 'B': 0.2})
        >>> r["n_stocks"]
        2

    See Also:
        - icTimeSeries : 다시점 IC + ICIR
        - strategy.metrics.pearsonCorr / spearmanCorr : core stats

    AIContext:
        "팩터가 종목 잘 정렬" 답변 시 ic_spearman + is_significant 인용.
    """
    common = sorted(set(factorScores) & set(forwardReturns))
    if len(common) < 10:
        return {
            "ic_pearson": float("nan"),
            "ic_spearman": float("nan"),
            "n_stocks": len(common),
            "t_stat": None,
            "is_significant": False,
        }
    x = np.array([factorScores[k] for k in common], dtype=float)
    y = np.array([forwardReturns[k] for k in common], dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if x.size < 10:
        return {
            "ic_pearson": float("nan"),
            "ic_spearman": float("nan"),
            "n_stocks": int(x.size),
            "t_stat": None,
            "is_significant": False,
        }
    ic_p = pearsonCorr(x, y)
    ic_s = spearmanCorr(x, y)
    n = int(x.size)
    t_stat: float | None = None
    perfect = not np.isnan(ic_p) and abs(ic_p) >= 0.9999
    if not np.isnan(ic_p) and not perfect and n > 2:
        denom = np.sqrt(max(1.0 - ic_p * ic_p, 1e-12))
        t_stat = float(ic_p * np.sqrt(n - 2) / denom)
    return {
        "ic_pearson": float(ic_p),
        "ic_spearman": float(ic_s),
        "n_stocks": n,
        "t_stat": t_stat,
        "is_significant": perfect or (t_stat is not None and abs(t_stat) > 2.0),
    }


def icTimeSeries(
    factorScoresSeries: list[dict[str, float]],
    forwardReturnsSeries: list[dict[str, float]],
) -> dict:
    """IC 시계열 통계 — 여러 시점 IC 의 평균/표준편차/ICIR.

    Parameters
    ----------
    factorScoresSeries : list[dict[str, float]]
        시점별 {종목코드: 팩터 스코어} dict 리스트.
    forwardReturnsSeries : list[dict[str, float]]
        시점별 {종목코드: forward return} dict 리스트 (동일 길이).

    Returns
    -------
    dict
        mean_ic : float — 평균 Spearman IC (비율)
        std_ic : float — IC 표준편차 (비율)
        icir : float — ICIR = mean_ic / std_ic (배)
        n_periods : int — 유효 기간 수
        hit_rate : float — IC 부호 일치 비율 (0~1)

    Capabilities:
        - 시점별 calcCrossSectionIC 반복 → ic_spearman 누적 → 평균/표준편차/ICIR
        - hit_rate = 부호 일치 비율

    Guide:
        Grinold-Kahn ICIR ≥ 0.5 = useful, ≥ 0.75 = exceptional. Fundamental Law breadth N_periods.

    When:
        팩터 시계열 견고성 + AI ICIR 답변.

    How:
        for fs, fr → calcCrossSectionIC → ic_spearman 수집 → 통계.

    Requires:
        두 series 길이 일치 + 유효 IC ≥ 2.

    Raises:
        ValueError — 두 series 길이 불일치.

    Example:
        >>> icTimeSeries(fs_list, fr_list)["icir"]
        0.48

    See Also:
        - calcCrossSectionIC : 단일 시점
        - strategy.metrics.fundamentalLawIR : breadth 결합

    AIContext:
        "팩터 시간적 견고성" 답변 시 icir + hit_rate 인용.
    """
    if len(factorScoresSeries) != len(forwardReturnsSeries):
        raise ValueError("factorScoresSeries / forwardReturnsSeries 길이 불일치")
    ics: list[float] = []
    for fs, fr in zip(factorScoresSeries, forwardReturnsSeries):
        r = calcCrossSectionIC(fs, fr)
        ic = r.get("ic_spearman")
        if ic is not None and not (isinstance(ic, float) and np.isnan(ic)):
            ics.append(float(ic))
    if len(ics) < 2:
        return {
            "mean_ic": float("nan"),
            "std_ic": float("nan"),
            "icir": float("nan"),
            "n_periods": len(ics),
            "hit_rate": float("nan"),
        }
    arr = np.array(ics, dtype=float)
    mean_ic = float(arr.mean())
    std_ic = float(arr.std(ddof=1))
    icir = float(mean_ic / std_ic) if std_ic > 0 else 0.0
    hit_rate = float(np.mean(np.sign(arr) == np.sign(mean_ic)))
    return {
        "mean_ic": mean_ic,
        "std_ic": std_ic,
        "icir": icir,
        "n_periods": len(ics),
        "hit_rate": hit_rate,
    }


def _loadAccount(lf: pl.LazyFrame, sj: str, account: str, year: str) -> dict[str, float]:
    """특정 계정의 전종목 금액 추출 — scanBridge 경유 DART/EDGAR 통일."""
    try:
        full = lf.collect(engine="streaming")
    except (KeyError, ValueError, TypeError, AttributeError):
        return {}
    annual = extractAnnualConsolidated(full)
    if annual.is_empty():
        return {}
    return getAccountValue(annual, account, year=year)


def calcRanking(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    asof: str | None = None,
    **kwargs,
) -> dict:
    """전종목 멀티팩터 횡단면 순위 — 5 팩터 (KR) / 3 팩터 (US) 복합 score.

    Capabilities:
        scan finance.parquet 의 최신 연도 데이터로 영업이익률/ROA/부채비율 (3 팩터) + KR 한정
        시가총액/북수익률 (size/value 2 팩터 추가) 의 백분위 평균을 복합 점수로 산출하고
        상위 50 종목을 반환. stockCode 지정 시 해당 종목 순위 + 상위 10 인용 반환.

    Parameters
    ----------
    market : str, default "KR"
        시장 코드. KR 은 5 팩터, US 는 3 팩터 (size/value 미수집).
    stockCode : str | None, default None
        특정 종목 지정 시 해당 종목 순위 + 상위 10 인용.
    **kwargs
        forward-compat 슬롯.

    Returns
    -------
    dict
        market : str — 입력 echo
        year : str — 기준 연도 (데이터 풍부한 최신 연도 자동 선택)
        totalStocks : int — 순위 산출 종목 수
        factorsUsed : list[str] — 사용된 팩터 명 리스트
        rankings : list[dict] — 상위 50 종목 (stockCode/opMargin/ROA/debtRatio/marketCap/bookYield/compositeScore/rank)
        target : dict | None — stockCode 지정 시 (해당 종목 + 상위 10 인용)
        데이터 부재 시 {**result, "error": str}.

    Raises
    ------
    없음 (scan 결손 시 dict["error"]).

    Example
    -------
    >>> r = calcRanking(market="KR")
    >>> r["rankings"][0]["stockCode"], r["rankings"][0]["compositeScore"]
    ('005930', 0.94)
    >>> r2 = calcRanking(market="KR", stockCode="005930")
    >>> r2["target"]["rank"]
    7

    Guide
    -----
    학술 근거: Asness 2013 (Value/Momentum Everywhere) · FF 1992 (size + BM) · Piotroski 2000
    (Fundamentals). compositeScore 는 백분위 평균이므로 0~1 범위가 의미. 100 개 미만 연도는
    fallback 으로 다음 후보 연도 자동 선택.

    See Also:
        - ``dartlab.quant.factor.value.calcValue`` : 가치 단축
        - ``dartlab.quant.factor.quality.calcQuality`` : 퀄리티 단축
        - ``dartlab.scan.financial`` : finance.parquet SSOT

    When:
        Quant universe ranking 진입점 + AI 종목 순위 답변.

    How:
        scan finance.parquet → 최신 연도 → 5 팩터 (KR) 또는 3 팩터 (US) 백분위
        평균 → top-50 + stockCode 순위.

    Requires
    --------
    - L1.5 scan: finance.parquet (시장별 100 종목 이상)
    - KR 5 팩터: 시가총액 (KRX) 추가 필요

    AIContext
    ---------
    "퀄리티 + 가치 통합 상위 종목" 1 차 진입. stockCode 지정 호출은 해당 종목이 "전종목 중 어디"
    답변에 직결. factorsUsed 함께 인용해 KR/US 차이 명시 권장.
    """
    result: dict = {"market": market}

    lf = loadScanParquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}

    # 최신 연도 확인
    edgar = isEdgarSchema(lf)
    yearCol = "fy" if edgar else "bsns_year"
    try:
        years = lf.select(yearCol).unique().collect(engine="streaming").to_series().sort(descending=True).to_list()
        years = [str(y) for y in years]
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        return {**result, "error": str(e)}

    if not years:
        return {**result, "error": "연도 데이터 없음"}

    # 데이터가 풍부한 연도 선택 (최신 → fallback)
    year = None
    for y in years:
        assets_test = _loadAccount(lf, "BS", "자산총계", y)
        if len(assets_test) >= 100:
            year = y
            break
    if year is None:
        year = years[0]
    result["year"] = year

    # 계정별 전종목 추출 (LazyFrame 필터로 메모리 안전)
    sales = _loadAccount(lf, "IS", "매출액", year)
    op = _loadAccount(lf, "IS", "영업이익", year)
    ni = _loadAccount(lf, "IS", "당기순이익", year)
    assets = _loadAccount(lf, "BS", "자산총계", year)
    debt = _loadAccount(lf, "BS", "부채총계", year)
    equity = _loadAccount(lf, "BS", "자본총계", year)

    # 시총 (KR 만) — size + bookYield 팩터용
    market_caps: dict[str, float] = {}
    if market == "KR":
        try:
            from dartlab.gather.bulkData.hfBulk import loadFiltered

            mc_long = loadFiltered(start=f"{year}-12-25", end=f"{year}-12-31", adjustment="raw", asof=asof)
            if mc_long is not None and not mc_long.is_empty():
                latest = (
                    mc_long.sort("BAS_DD", descending=True)
                    .unique(subset=["ISU_CD"], keep="first")
                    .select(["ISU_CD", "MKTCAP"])
                )
                market_caps = {
                    row["ISU_CD"]: float(row["MKTCAP"])
                    for row in latest.iter_rows(named=True)
                    if row.get("MKTCAP") and row["MKTCAP"] > 0
                }
        except Exception as exc:
            log.warning("ranking: KR 시총 fetch 실패: %s", type(exc).__name__)

    # 공통 종목
    all_codes = set(sales) & set(assets)
    if not all_codes:
        return {**result, "error": "공통 종목 없음"}

    # 지표 계산
    has_size_value = market == "KR" and len(market_caps) >= 100
    ranked = []
    for code in all_codes:
        s = sales.get(code, 0)
        o = op.get(code)
        n = ni.get(code)
        a = assets.get(code, 0)
        d = debt.get(code, 0)
        eq = equity.get(code)

        margin = (o / s * 100) if s > 0 and o is not None else None
        roa = (n / a * 100) if a > 0 and n is not None else None
        dr = (d / a * 100) if a > 0 else None
        mc = market_caps.get(code) if has_size_value else None
        by = (eq / mc) if (has_size_value and mc and mc > 0 and eq is not None and eq > 0) else None

        if margin is not None or roa is not None:
            ranked.append(
                {
                    "stockCode": code,
                    "opMargin": round(margin, 2) if margin else None,
                    "ROA": round(roa, 2) if roa else None,
                    "debtRatio": round(dr, 2) if dr else None,
                    "marketCap": round(mc, 0) if mc else None,
                    "bookYield": round(by, 4) if by else None,
                }
            )

    if not ranked:
        return {**result, "error": "순위 산출 가능 종목 없음"}

    # 백분위 순위
    n = len(ranked)
    margins = np.array([r["opMargin"] or 0 for r in ranked])
    roas = np.array([r["ROA"] or 0 for r in ranked])
    debts = np.array([r["debtRatio"] or 100 for r in ranked])

    m_rank = np.argsort(np.argsort(-margins)) / max(n - 1, 1)
    r_rank = np.argsort(np.argsort(-roas)) / max(n - 1, 1)
    d_rank = np.argsort(np.argsort(debts)) / max(n - 1, 1)

    # 5-factor composite (KR 시총 있을 때) 또는 3-factor (fallback)
    if has_size_value:
        # size: 작을수록 top (small premium) — 근데 한국 2025 RMW 검증으로 size 역방향
        # 실용: 큰 시총 = 안정성 ↑ 가 더 적절. size_rank = 큰 시총 top (역발상 제거)
        mcaps = np.array([r["marketCap"] or 0 for r in ranked])
        yields_ = np.array([r["bookYield"] or 0 for r in ranked])
        # size_rank: 시총 큰 종목이 top (실용적 안정성)
        s_rank = np.argsort(np.argsort(-mcaps)) / max(n - 1, 1)
        # value_rank: bookYield 큰 종목 top (= 낮은 PBR = value)
        v_rank = np.argsort(np.argsort(-yields_)) / max(n - 1, 1)
        composites = (m_rank + r_rank + d_rank + s_rank + v_rank) / 5
        factors_used = ["margin", "ROA", "debt", "size", "value"]
    else:
        composites = (m_rank + r_rank + d_rank) / 3
        factors_used = ["margin", "ROA", "debt"]
    # composite 는 0 이 최고다. 각 factor 를 `argsort(argsort(-x))` 로 만들었기 때문에
    # 가장 좋은 종목이 0 순위를 받고 그 평균도 0 에 가깝다. 그런데 내림차순으로 정렬해
    # 왔기 때문에 가장 나쁜 종목이 1 위로 올라갔다. 마진 -5%, ROA -3%, 부채비율 400%
    # 짜리가 "상위 50 종목" 맨 앞에 서던 것이 그 결과다.
    order = np.argsort(composites)

    for i, idx in enumerate(order):
        # 점수도 사람이 읽는 방향으로 뒤집는다. 1 에 가까울수록 좋다.
        ranked[idx]["compositeScore"] = round(1.0 - float(composites[idx]), 4)
        ranked[idx]["rank"] = i + 1

    sorted_ranked = sorted(ranked, key=lambda x: x.get("rank", 9999))
    result["totalStocks"] = n
    result["factorsUsed"] = factors_used

    if stockCode:
        target = [r for r in sorted_ranked if r["stockCode"] == stockCode]
        result["target"] = target[0] if target else None
        result["rankings"] = sorted_ranked[:10]
    else:
        result["rankings"] = sorted_ranked[:50]

    return result
