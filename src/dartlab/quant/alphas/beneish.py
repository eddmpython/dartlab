"""Beneish M-Score 횡단면 quant factor — 이익 조작 감지.

학술: Beneish (1999) Financial Analysts Journal — 8변수 probit 모형.

M = -4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI + 0.115·DEPI
    - 0.172·SGAI + 4.679·TATA - 0.327·LVGI

변수 (전년도 비교):
    DSRI : Days Sales Receivables Index = (AR_t/Sales_t) / (AR_{t-1}/Sales_{t-1})
    GMI  : Gross Margin Index = GM_{t-1} / GM_t   (마진 악화 시 > 1)
    AQI  : Asset Quality Index = (1 - CA_t/TA_t) / (1 - CA_{t-1}/TA_{t-1})
    SGI  : Sales Growth Index = Sales_t / Sales_{t-1}
    DEPI : Depreciation Index = DepRate_{t-1} / DepRate_t (감가상각 감소 시 > 1)
    SGAI : SG&A Index = (SGA_t/Sales_t) / (SGA_{t-1}/Sales_{t-1})
    TATA : Total Accruals to Total Assets = (NI - CFO) / TA
    LVGI : Leverage Index = (TL_t/TA_t) / (TL_{t-1}/TA_{t-1})

해석:
    M > -1.78 : 조작 가능 (red flag) — Beneish 원본 임계
    M ≤ -1.78 : 양호

dartlab 데이터: DART BS/IS/CF (AR, Sales, GM, Depreciation, SG&A, Accruals 모두 계산 가능).
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant.factor.build import _latestYear
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.rowAccess import safeDiv
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _computeM(cur: pl.DataFrame, prev: pl.DataFrame) -> float | None:
    """단일 종목의 Beneish M. prev 없으면 None (변수 대부분이 비율 변화 필요)."""
    # 현재
    ta = extractAccount(cur, "total_assets")
    ca = extractAccount(cur, "current_assets")
    tl = extractAccount(cur, "total_liabilities")
    ar = extractAccount(cur, "accounts_receivable")
    sales = extractAccount(cur, "sales")
    gp = extractAccount(cur, "gross_profit")
    dep = extractAccount(cur, "depreciation")
    sga = extractAccount(cur, "selling_admin")
    ni = extractAccount(cur, "net_income")
    ocf = extractAccount(cur, "operating_cf")
    # 전년
    taP = extractAccount(prev, "total_assets")
    caP = extractAccount(prev, "current_assets")
    tlP = extractAccount(prev, "total_liabilities")
    ar_p = extractAccount(prev, "accounts_receivable")
    sales_p = extractAccount(prev, "sales")
    gp_p = extractAccount(prev, "gross_profit")
    depP = extractAccount(prev, "depreciation")
    sgaP = extractAccount(prev, "selling_admin")

    if not ta or ta <= 0 or not sales or sales <= 0:
        return None
    if not taP or taP <= 0 or not sales_p or sales_p <= 0:
        return None

    # DSRI
    dsri_num = safeDiv(ar, sales)
    dsri_den = safeDiv(ar_p, sales_p)
    dsri = safeDiv(dsri_num, dsri_den) if (dsri_num and dsri_den) else 1.0

    # GMI — 전년 GM / 현재 GM (악화 시 > 1)
    gm = safeDiv(gp, sales)
    gm_p = safeDiv(gp_p, sales_p)
    gmi = safeDiv(gm_p, gm) if (gm and gm_p and gm > 0) else 1.0

    # AQI — (1 - CA/TA) / prev
    aqi_num = 1 - safeDiv(ca, ta) if ca is not None else None
    aqi_den = 1 - safeDiv(caP, taP) if caP is not None else None
    aqi = safeDiv(aqi_num, aqi_den) if (aqi_num and aqi_den and aqi_den > 0) else 1.0

    # SGI
    sgi = sales / sales_p if sales_p > 0 else 1.0

    # DEPI — 전년 감가율 / 현재 감가율 (감소 시 > 1)
    dep_rate = safeDiv(dep, ta) if dep else None
    dep_rate_p = safeDiv(depP, taP) if depP else None
    depi = safeDiv(dep_rate_p, dep_rate) if (dep_rate and dep_rate_p and dep_rate > 0) else 1.0

    # SGAI
    sgai_num = safeDiv(sga, sales)
    sgai_den = safeDiv(sgaP, sales_p)
    sgai = safeDiv(sgai_num, sgai_den) if (sgai_num and sgai_den) else 1.0

    # TATA
    tata = ((ni or 0) - (ocf or 0)) / ta if (ni is not None or ocf is not None) and ta > 0 else 0.0

    # LVGI
    lvgi_num = safeDiv(tl, ta) if tl is not None else None
    lvgi_den = safeDiv(tlP, taP) if tlP is not None else None
    lvgi = safeDiv(lvgi_num, lvgi_den) if (lvgi_num and lvgi_den and lvgi_den > 0) else 1.0

    m = (
        -4.84
        + 0.920 * (dsri or 1.0)
        + 0.528 * (gmi or 1.0)
        + 0.404 * (aqi or 1.0)
        + 0.892 * sgi
        + 0.115 * (depi or 1.0)
        - 0.172 * (sgai or 1.0)
        + 4.679 * tata
        - 0.327 * (lvgi or 1.0)
    )
    return m


def calcBeneishFactor(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Beneish M-Score 횡단면 quant factor — 한국 전종목 이익 조작 red flag.

    Capabilities:
        - 전종목 M-Score (8변수) 횡단면 분포
        - red flag (M > -1.78) 종목 비율 + Top 10
        - 이익 조작 의심 시장 지도 (회계 품질 관점)

    AIContext:
        - Sprint 2 재무 알파 — Piotroski (건강) + Altman (부실) + Beneish (조작) 3종 교차
        - red flag = quant 포트폴리오 자동 제외 후보
        - story `beneishFactorBlock` 시장분석 자동 호출

    Guide:
        - 시장 스냅샷 : calcBeneishFactor()

    See Also:
        - calcPiotroskiFactor : 재무 건강
        - calcAltmanFactor : 부실 확률
        - analysis.financial.earningsQuality : 단일 종목 이익 품질

    When:
        Quant 회계 품질 축 + AI 이익 조작 red flag 답변.

    How:
        scan finance.parquet 2 기 → 8 변수 M-Score 계산 → -1.78 임계로 red flag.

    Requires:
        scan finance.parquet (2 기 이상).

    Raises:
        없음 — 실패는 None.

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict
            market : str
            year : str
            prevYear : str
            universe : int
            scores : dict[str, float] — {stockCode: M}
            flags : dict — {redFlag: {count, pct}, clean: {count, pct}}
            topFlag : list[tuple[str, float]] — M 상위 10 (가장 의심)
            topClean : list[tuple[str, float]] — M 하위 10 (가장 투명)
            interpretation : str

    Examples:
        >>> from dartlab.quant.alphas.beneish import calcBeneishFactor
        >>> r = calcBeneishFactor()
        >>> print(r["flags"]["redFlag"]["pct"], "% red flag")
        17.2 % red flag

    Notes:
        - 임계 -1.78 은 Beneish 원본. 한국 시장엔 부분 조정 여지 있으나 일관성 위해 유지.
        - SGA (판관비) 데이터 없을 시 SGAI = 1 (뉴트럴).
        - 단일 연도 M 만 신호 아님 — 2~3년 연속 red flag 가 실제 risk.
    """
    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
        year = _latestYear(snap)
        if year is None:
            return None
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        log.warning("calcBeneishFactor year 추출 실패: %s", type(exc).__name__)
        return None

    edgar = isEdgarSchema(snap)
    yearCol = "fy" if edgar else "bsns_year"
    year_val = int(year) if edgar else year
    try:
        prev_year_val = int(year) - 1 if edgar else str(int(year) - 1)
    except ValueError:
        return None

    cur = snap.filter(pl.col(yearCol) == year_val)
    prev = snap.filter(pl.col(yearCol) == prev_year_val)
    if cur.is_empty() or prev.is_empty():
        return None

    scores: dict[str, float] = {}
    # 성능 fix (G5): partition_by 한 번 호출 → O(n) lookup
    cur_parts = cur.partition_by("stockCode", as_dict=True)
    prev_parts = prev.partition_by("stockCode", as_dict=True)
    for code_key, s_cur in cur_parts.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str):
            continue
        s_prev = prev_parts.get(code_key)
        if s_prev is None or s_prev.is_empty():
            continue
        m = _computeM(s_cur, s_prev)
        if m is None:
            continue
        scores[code] = m

    if not scores:
        return None

    red_flag = sum(1 for m in scores.values() if m > -1.78)
    clean = len(scores) - red_flag
    total = len(scores)
    flags = {
        "redFlag": {"count": red_flag, "pct": round(100 * red_flag / total, 1)},
        "clean": {"count": clean, "pct": round(100 * clean / total, 1)},
    }

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topFlag = [(c, round(m, 2)) for c, m in sorted_items[:10]]
    topClean = [(c, round(m, 2)) for c, m in sorted_items[-10:]]

    # 단일 종목 분기 (Step 6)
    if stockCode:
        m = scores.get(stockCode)
        if m is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함, 전년 비교 필요)",
            }
        flag = "redFlag" if m > -1.78 else "clean"
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "prevYear": str(prev_year_val),
            "score": round(m, 2),
            "flag": flag,
            "universe": total,
            "interpretation": (
                f"{stockCode} Beneish M={round(m, 2)} ({flag}) — "
                + ("이익 조작 의심 (M > -1.78)." if flag == "redFlag" else "회계 투명 (M ≤ -1.78).")
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "prevYear": str(prev_year_val),
        "universe": total,
        "scores": {c: round(m, 2) for c, m in scores.items()},
        "flags": flags,
        "topFlag": topFlag,
        "topClean": topClean,
        "interpretation": (
            f"{market} {year}년 {total}개 종목 중 red flag "
            f"{flags['redFlag']['pct']}% ({flags['redFlag']['count']}사). "
            "M > -1.78 = 이익 조작 의심."
        ),
    }
