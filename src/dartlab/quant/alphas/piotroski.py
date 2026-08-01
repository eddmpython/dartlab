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
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet, loadSharesOutstanding
from dartlab.synth.rowAccess import safeDiv
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _scoreOne(
    cur: pl.DataFrame,
    prev: pl.DataFrame | None,
    *,
    sharesCur: float | None = None,
    sharesPrev: float | None = None,
) -> dict | None:
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

    components: dict[str, bool | None] = {}
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
    if prev is not None and not prev.is_empty():
        ta_prev = extractAccount(prev, "total_assets")
        ni_prev = extractAccount(prev, "net_income")
        ocf_prev = extractAccount(prev, "operating_cf")
        tl_prev = extractAccount(prev, "total_liabilities")
        ca_prev = extractAccount(prev, "current_assets")
        cl_prev = extractAccount(prev, "current_liabilities")
        gp_prev = extractAccount(prev, "gross_profit")
        sales_prev = extractAccount(prev, "sales")

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

    # F7: 발행주식수의 전년 대비 증가 여부. 자본/자산 비율은 발행 여부가 아니므로 사용하지 않는다.
    if sharesCur is not None and sharesPrev is not None and sharesCur > 0 and sharesPrev > 0:
        components["noNewShares"] = bool(sharesCur <= sharesPrev * 1.001)
    else:
        components["noNewShares"] = None

    # gross margin
    gm_cur = safeDiv(gp, sales)
    gm_prev = safeDiv(gp_prev, sales_prev)
    components["grossMarginUp"] = bool(gm_cur is not None and gm_prev is not None and gm_cur > gm_prev)

    # asset turnover
    at_cur = safeDiv(sales, ta)
    at_prev = safeDiv(sales_prev, ta_prev)
    components["assetTurnoverUp"] = bool(at_cur is not None and at_prev is not None and at_cur > at_prev)

    observed = sum(value is not None for value in components.values())
    partialTotal = sum(1 for value in components.values() if value is True)
    return {
        "total": partialTotal if observed == 9 else None,
        "partialTotal": partialTotal,
        "components": components,
        "coverage": {"observed": observed, "expected": 9, "scoreEligible": observed == 9},
    }


def _sharesByYear(market: str) -> dict[tuple[str, str], float]:
    """발행주식수 원장에서 (종목, 연도)별 최신 보통주+우선주 합계를 만든다."""
    try:
        sharesLf = loadSharesOutstanding(market)
        if sharesLf is None:
            return {}
        sharesDf = sharesLf.collect(engine="streaming")
    except (OSError, ValueError, KeyError, AttributeError):
        return {}

    result: dict[tuple[str, str], tuple[str, float]] = {}
    for row in sharesDf.to_dicts():
        code = str(row.get("stockCode") or "")
        if market.upper() == "KR" and code.isdigit():
            code = code.zfill(6)
        period = str(row.get("period_end") or "")[:10]
        if not code or len(period) < 4:
            continue
        values = [row.get("common"), row.get("preferred")]
        numeric = [float(value) for value in values if isinstance(value, int | float) and value >= 0]
        if not numeric:
            continue
        key = (code, period[:4])
        total = sum(numeric)
        if key not in result or period > result[key][0]:
            result[key] = (period, total)
    return {key: value for key, (_, value) in result.items()}


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
        - F7 (noNewShares): sharesOutstanding 원장의 전년 대비 주식수 변화 proxy.
          원장 결손이면 실패 0점이 아니라 None이며 9점 총점·등급을 발행하지 않는다.
        - 전년도 비교가 없는 신호는 None으로 coverage에서 제외한다.
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
    if stockCode:
        cur = cur.filter(pl.col("stockCode") == stockCode)
        prev = prev.filter(pl.col("stockCode") == stockCode)

    sharesByYear = _sharesByYear(market)

    scores: dict[str, int] = {}
    partialScores: dict[str, int] = {}
    components: dict[str, dict] = {}
    coverageByStock: dict[str, dict] = {}
    # 성능 fix (G5): partition_by 한 번 호출 → O(n) lookup
    cur_parts = cur.partition_by("stockCode", as_dict=True)
    prev_parts = prev.partition_by("stockCode", as_dict=True)
    for code_key, s_cur in cur_parts.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str):
            continue
        s_prev = prev_parts.get(code_key)
        res = _scoreOne(
            s_cur,
            s_prev if s_prev is not None and not s_prev.is_empty() else None,
            sharesCur=sharesByYear.get((code, str(year))),
            sharesPrev=sharesByYear.get((code, str(prev_year_val))),
        )
        if res is None:
            continue
        partialScores[code] = res["partialTotal"]
        if res["total"] is not None:
            scores[code] = res["total"]
        components[code] = res["components"]
        coverageByStock[code] = res["coverage"]

    if not scores:
        return {
            "status": "unavailable",
            "blockedReason": "F7 발행주식수 또는 다른 필수 신호가 없어 canonical 9점 F-Score를 발행할 수 없습니다.",
            "market": market,
            "year": str(year),
            "prevYear": str(prev_year_val),
            "universe": len(partialScores),
            "scores": {},
            "partialScores": partialScores,
            "components": components,
            "coverage": coverageByStock,
            "grades": None,
            "topStrong": [],
            "topWeak": [],
            "signalAvg": {},
        }

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
        eligibleComponents = [components[code] for code in scores if code in components]
        passed = sum(1 for component in eligibleComponents if component.get(k) is True)
        signalAvg[k] = round(100 * passed / total, 1)

    # 단일 종목 분기 (Step 6)
    if stockCode:
        f = scores.get(stockCode)
        if f is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "status": "unavailable",
                "blockedReason": "9개 신호 coverage가 불완전해 canonical F-Score를 발행할 수 없습니다.",
                "score": None,
                "grade": None,
                "partialScore": partialScores.get(stockCode),
                "components": components.get(stockCode, {}),
                "coverage": coverageByStock.get(stockCode),
            }
        grade = "strong" if f >= 7 else ("moderate" if f >= 4 else "weak")
        return {
            "status": "usable",
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "prevYear": str(prev_year_val),
            "score": f,
            "grade": grade,
            "components": components.get(stockCode, {}),
            "coverage": coverageByStock.get(stockCode),
            "universe": total,
            "interpretation": (
                f"{stockCode} Piotroski F={f}/9 ({grade}) — "
                + ("재무 건강 강함." if grade == "strong" else "보통." if grade == "moderate" else "재무 신호 약함.")
            ),
        }

    return {
        "status": "usable" if len(scores) == len(partialScores) else "partial",
        "market": market,
        "year": str(year),
        "prevYear": str(prev_year_val),
        "universe": total,
        "scores": scores,
        "partialScores": partialScores,
        "components": components,
        "coverage": coverageByStock,
        "excludedForCoverage": len(partialScores) - len(scores),
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
    sharesByYear = _sharesByYear(market)

    out: list[dict] = []
    for yStr in sorted(byYear):
        cur = byYear[yStr]
        try:
            prevYearStr = str(int(yStr) - 1)
            prev = byYear.get(prevYearStr)
        except ValueError:
            prevYearStr = ""
            prev = None
        curParts = cur.partition_by("stockCode", as_dict=True)
        prevParts = prev.partition_by("stockCode", as_dict=True) if prev is not None else {}
        for ck, sCur in curParts.items():
            code = ck[0] if isinstance(ck, tuple) else ck
            if not isinstance(code, str):
                continue
            sPrev = prevParts.get(ck)
            res = _scoreOne(
                sCur,
                sPrev if sPrev is not None and not sPrev.is_empty() else None,
                sharesCur=sharesByYear.get((code, yStr)),
                sharesPrev=sharesByYear.get((code, prevYearStr)),
            )
            if res is None or res["total"] is None:
                continue
            out.append({"stockCode": code, "bsns_year": yStr, "piotroski": int(res["total"])})
    if not out:
        return None
    return pl.DataFrame(out)
