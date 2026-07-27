"""Piotroski F-Score 횡단면 quant factor.

학술: Piotroski (2000) Journal of Accounting Research — 9개 이진 신호 합산 (0~9점).

수익성 (4):
    F1 ROA > 0
    F2 CFO > 0
    F3 ΔROA > 0 (개선)
    F4 CFO > NI (accrual quality)

건전성/자본 (3):
    F5 Δ(TL/TA) < 0 (부채비율 감소)
    F6 ΔCurrent Ratio > 0 (유동성 개선)
    F7 신주 미발행 (equity/asset 희석 X)

효율성 (2):
    F8 ΔGross Margin > 0
    F9 ΔAsset Turnover > 0

해석: ≥7 strong / 4~6 moderate / ≤3 weak

dartlab 데이터: DART finance.parquet (BS/IS/CF 모두). 전년도 비교 필요.
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant.factor.build import _latestYear
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.rowAccess import safeDiv
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _scoreOne(cur: pl.DataFrame, prev: pl.DataFrame | None) -> dict | None:
    """단일 종목의 9 신호 평가 → dict(components, total)."""
    ta = extractAccount(cur, "total_assets")
    if not ta or ta <= 0:
        return None
    ni = extractAccount(cur, "net_income")
    ocf = extractAccount(cur, "operating_cf")
    tl = extractAccount(cur, "total_liabilities")
    ca = extractAccount(cur, "current_assets")
    cl = extractAccount(cur, "current_liabilities")
    gp = extractAccount(cur, "gross_profit")
    sales = extractAccount(cur, "sales")
    eq = extractAccount(cur, "total_equity")

    components: dict[str, bool] = {}
    roa = safeDiv(ni, ta)
    components["roaPositive"] = bool(roa is not None and roa > 0)
    components["ocfPositive"] = bool(ocf is not None and ocf > 0)
    components["cfGtNi"] = bool(ocf is not None and ni is not None and ocf > ni)

    ta_prev = None
    ni_prev = None
    ocf_prev = None
    tl_prev = None
    ca_prev = None
    cl_prev = None
    gp_prev = None
    sales_prev = None
    eq_prev = None
    if prev is not None and not prev.is_empty():
        ta_prev = extractAccount(prev, "total_assets")
        ni_prev = extractAccount(prev, "net_income")
        ocf_prev = extractAccount(prev, "operating_cf")
        tl_prev = extractAccount(prev, "total_liabilities")
        ca_prev = extractAccount(prev, "current_assets")
        cl_prev = extractAccount(prev, "current_liabilities")
        gp_prev = extractAccount(prev, "gross_profit")
        sales_prev = extractAccount(prev, "sales")
        eq_prev = extractAccount(prev, "total_equity")

    roa_prev = safeDiv(ni_prev, ta_prev)
    components["roaIncreasing"] = bool(roa is not None and roa_prev is not None and roa > roa_prev)

    # leverage = TL / TA (decreasing is good)
    lev_cur = safeDiv(tl, ta)
    lev_prev = safeDiv(tl_prev, ta_prev)
    components["debtDecreasing"] = bool(lev_cur is not None and lev_prev is not None and lev_cur < lev_prev)

    # current ratio
    cr_cur = safeDiv(ca, cl)
    cr_prev = safeDiv(ca_prev, cl_prev)
    components["currentRatioUp"] = bool(cr_cur is not None and cr_prev is not None and cr_cur > cr_prev)

    # no new shares: 자본 대비 자산 비율 지속 (equity dilution proxy)
    # 실제 issued_shares 없음 → equity가 자산 대비 떨어지지 않으면 pass (보수적)
    e2a_cur = safeDiv(eq, ta)
    e2a_prev = safeDiv(eq_prev, ta_prev)
    if e2a_cur is not None and e2a_prev is not None:
        components["noNewShares"] = bool(e2a_cur >= e2a_prev * 0.95)
    else:
        components["noNewShares"] = True  # 데이터 없으면 보수적 pass

    # gross margin
    gm_cur = safeDiv(gp, sales)
    gm_prev = safeDiv(gp_prev, sales_prev)
    components["grossMarginUp"] = bool(gm_cur is not None and gm_prev is not None and gm_cur > gm_prev)

    # asset turnover
    at_cur = safeDiv(sales, ta)
    at_prev = safeDiv(sales_prev, ta_prev)
    components["assetTurnoverUp"] = bool(at_cur is not None and at_prev is not None and at_cur > at_prev)

    total = sum(1 for v in components.values() if v)
    return {"total": total, "components": components}


def calcPiotroskiFactor(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Piotroski F-Score 횡단면 quant factor — 한국 전종목 재무 건강 9점 랭킹.

    Capabilities:
        - 전종목 F-Score (0~9점) 횡단면 분포
        - strong (≥7) / moderate (4~6) / weak (≤3) 3 그룹 비중
        - Top (9점) 종목 리스트 + Bottom 리스트
        - 9 신호별 통과율 (시장 평균 개선 방향 진단)

    AIContext:
        - Sprint 2 재무 알파 핵심 — 가치 + 품질 통합 스크리닝
        - story `piotroskiFactorBlock` 시장분석 자동 호출
        - F ≥ 7 종목 = fundamental momentum 후보 / F ≤ 3 = 회피 후보

    Guide:
        - 전종목 스냅샷 : calcPiotroskiFactor()
        - 단일종목 : analysis.financial.scorecard.calcPiotroskiDetail(company)

    See Also:
        - analysis.financial.research.scoring.calcPiotroski : 단일 종목 9 신호
        - calcAltmanFactor : 부실 확률 (보완 축)
        - calcBeneishFactor : 이익 조작 감지 (보완 축)

    When:
        Quant 재무 건강 축 + AI 가치 + 품질 통합 스크리닝 진입점.

    How:
        scan finance.parquet 2 기 → 9 신호 매핑 (수익성 4 + 레버리지 3 + 효율
        2) → F-Score (0~9) → strong/moderate/weak 분류.

    Requires:
        scan finance.parquet (2 기).

    Raises:
        없음 — 실패는 None.

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict
            market : str
            year : str — 현재 연도
            prevYear : str — 전년도 비교 기준
            universe : int
            scores : dict[str, int] — {stockCode: F (0~9)}
            components : dict[str, dict] — 종목별 9 신호 상세
            grades : dict — {strong: {count, pct}, moderate: {...}, weak: {...}}
            topStrong : list[tuple[str, int]] — Top 10 (F 내림차순)
            topWeak : list[tuple[str, int]] — Bottom 10
            signalAvg : dict[str, float] — 신호별 시장 평균 통과율 (%)
            interpretation : str

    Examples:
        >>> from dartlab.quant.alphas.piotroski import calcPiotroskiFactor
        >>> r = calcPiotroskiFactor()
        >>> print(r["grades"]["strong"]["pct"], "% 강건")
        18.3 % 강건

    Notes:
        - F7 (noNewShares): DART 에 issued_shares 원장 없어 equity/asset 유지로 근사.
        - 전년도 데이터 없는 종목은 F3/F5/F6/F7/F8/F9 자동 실패 (보수적).
        - 2년 연속 동일 F ≥ 8 stream = hedge fund 장기 롱 후보.
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
        log.warning("calcPiotroskiFactor year 추출 실패: %s", type(exc).__name__)
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
    if cur.is_empty():
        return None

    scores: dict[str, int] = {}
    components: dict[str, dict] = {}
    # 성능 fix (G5): partition_by 한 번 호출 → O(n) lookup
    cur_parts = cur.partition_by("stockCode", as_dict=True)
    prev_parts = prev.partition_by("stockCode", as_dict=True)
    for code_key, s_cur in cur_parts.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str):
            continue
        s_prev = prev_parts.get(code_key)
        res = _scoreOne(s_cur, s_prev if s_prev is not None and not s_prev.is_empty() else None)
        if res is None:
            continue
        scores[code] = res["total"]
        components[code] = res["components"]

    if not scores:
        return None

    grades_count = {"strong": 0, "moderate": 0, "weak": 0}
    for f in scores.values():
        if f >= 7:
            grades_count["strong"] += 1
        elif f >= 4:
            grades_count["moderate"] += 1
        else:
            grades_count["weak"] += 1

    total = len(scores)
    grades = {k: {"count": v, "pct": round(100 * v / total, 1)} for k, v in grades_count.items()}

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topStrong = sorted_items[:10]
    topWeak = sorted_items[-10:]

    # 신호별 통과율
    signal_keys = [
        "roaPositive",
        "ocfPositive",
        "roaIncreasing",
        "cfGtNi",
        "debtDecreasing",
        "currentRatioUp",
        "noNewShares",
        "grossMarginUp",
        "assetTurnoverUp",
    ]
    signalAvg = {}
    for k in signal_keys:
        passed = sum(1 for c in components.values() if c.get(k))
        signalAvg[k] = round(100 * passed / total, 1)

    # 단일 종목 분기 (Step 6)
    if stockCode:
        f = scores.get(stockCode)
        if f is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함)",
            }
        grade = "strong" if f >= 7 else ("moderate" if f >= 4 else "weak")
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "prevYear": str(prev_year_val),
            "score": f,
            "grade": grade,
            "components": components.get(stockCode, {}),
            "universe": total,
            "interpretation": (
                f"{stockCode} Piotroski F={f}/9 ({grade}) — "
                + ("재무 건강 강함." if grade == "strong" else "보통." if grade == "moderate" else "재무 신호 약함.")
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "prevYear": str(prev_year_val),
        "universe": total,
        "scores": scores,
        "components": components,
        "grades": grades,
        "topStrong": topStrong,
        "topWeak": topWeak,
        "signalAvg": signalAvg,
        "interpretation": (
            f"{market} 시장 {year}년 {total}개 종목 Piotroski 분포: "
            f"strong {grades['strong']['pct']}% ({grades['strong']['count']}사), "
            f"moderate {grades['moderate']['pct']}%, "
            f"weak {grades['weak']['pct']}%."
        ),
    }


def calcPiotroskiSeries(*, market: str = "KR") -> pl.DataFrame | None:
    """Piotroski F-Score 시계열 — (stockCode, bsns_year, piotroski) 전종목·전연도.

    Sig:
        calcPiotroskiSeries(*, market="KR") -> pl.DataFrame | None

    펀더게이트(terminal-strategy-lab W2) PIT 시계열 빌더용. calcPiotroskiFactor 는 *최신 1기*만
    내므로 백테스트 진입 게이트의 과거 시계열을 못 만든다. 본 함수는 전 연도를 루프하며 동일
    ``_scoreOne`` (단일 SSOT) 으로 채점한다. rcept_dt(공시일) PIT 앵커 join 은 호출부(buildFundamentalGate).

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        pl.DataFrame[stockCode(str), bsns_year(str), piotroski(int 0~9)] · 데이터 없으면 None.

    Example:
        >>> df = calcPiotroskiSeries(market="KR")
        >>> df.filter(pl.col("stockCode") == "005930").sort("bsns_year")
    """
    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        log.warning("calcPiotroskiSeries 로드 실패: %s", type(exc).__name__)
        return None

    yearCol = "fy" if isEdgarSchema(snap) else "bsns_year"
    byYear: dict[str, pl.DataFrame] = {}
    for k, g in snap.partition_by(yearCol, as_dict=True).items():
        key = k[0] if isinstance(k, tuple) else k
        byYear[str(key)] = g

    out: list[dict] = []
    for yStr in sorted(byYear):
        cur = byYear[yStr]
        try:
            prev = byYear.get(str(int(yStr) - 1))
        except ValueError:
            prev = None
        curParts = cur.partition_by("stockCode", as_dict=True)
        prevParts = prev.partition_by("stockCode", as_dict=True) if prev is not None else {}
        for ck, sCur in curParts.items():
            code = ck[0] if isinstance(ck, tuple) else ck
            if not isinstance(code, str):
                continue
            sPrev = prevParts.get(ck)
            res = _scoreOne(sCur, sPrev if sPrev is not None and not sPrev.is_empty() else None)
            if res is None:
                continue
            out.append({"stockCode": code, "bsns_year": yStr, "piotroski": int(res["total"])})
    if not out:
        return None
    return pl.DataFrame(out)
