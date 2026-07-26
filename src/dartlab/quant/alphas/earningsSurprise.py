"""PEAD (Post-Earnings Announcement Drift) 횡단면 quant factor.

학술: Bernard & Thomas (1989, Journal of Accounting and Economics) - 실적 발표 후
     긍정 서프라이즈 종목이 60~90일 drift 상승, 음의 서프라이즈가 drift 하락.
     Ball & Brown (1968) 최초 관측, Bernard-Thomas 가 정식 PEAD 팩터화.

dartlab 단순화 (forecast 없을 때 SUE = Standardized Unexpected Earnings):
    SUE = (NI_t − NI_{t-1}) / σ(NI)_rolling
    (t는 분기/연도)

단년도 annual data 면:
    growth = (NI_{y} − NI_{y-1}) / |NI_{y-1}|
    SUE = growth 의 시장 횡단면 z-score

Top 10 positive SUE = PEAD long 후보 (60~90일 홀드).
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.scanBridge import isEdgarSchema

log = logging.getLogger(__name__)

_MIN_UNIVERSE = 50
_DART_NET_INCOME_PATTERN = r"당기순이익|당기순손익|연결당기순이익|지배기업.*(?:귀속|소유주).*순이익"


def _annualFinanceLazy(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, str, bool]:
    """연간 연결 재무만 lazy 상태에서 남겨 parquet predicate pushdown을 보존한다."""
    columns = set(lf.collect_schema().names())
    edgar = isEdgarSchema(lf)
    if edgar:
        return lf, "fy", True

    annual = lf
    if "fs_div" in columns:
        annual = annual.filter(pl.col("fs_div") == "CFS")
    elif "fs_nm" in columns:
        annual = annual.filter(pl.col("fs_nm") == "연결재무제표")

    if "reprt_code" in columns:
        annual = annual.filter(pl.col("reprt_code") == "11011")
    elif "reprt_nm" in columns:
        annual = annual.filter(pl.col("reprt_nm") == "4분기")
    return annual, "bsns_year", False


def _latestEligibleYear(lf: pl.LazyFrame, yearCol: str) -> str | None:
    """최소 횡단면을 충족하는 최신 연도를 작은 집계 결과만 collect해 고른다."""
    counts = (
        lf.select(yearCol, "stockCode")
        .drop_nulls()
        .group_by(yearCol)
        .agg(pl.col("stockCode").n_unique().alias("universe"))
        .filter(pl.col("universe") >= _MIN_UNIVERSE)
        .sort(yearCol, descending=True)
        .limit(1)
        .collect(engine="streaming")
    )
    if counts.is_empty():
        return None
    value = counts[yearCol][0]
    return str(value) if value is not None else None


def _collectEarningsWindow(
    lf: pl.LazyFrame,
    *,
    yearCol: str,
    year: str,
    prevYear: str,
    edgar: bool,
) -> pl.DataFrame:
    """현재·전년 순이익 계정만 collect해 전 시장 원본 적재를 피한다."""
    columns = set(lf.collect_schema().names())
    yearValues: list[str | int]
    if edgar:
        yearValues = [int(year), int(prevYear)]
        valueColumn = "net_profit" if "net_profit" in columns else "net_income"
        required = ["stockCode", yearCol, valueColumn]
        if valueColumn not in columns:
            return pl.DataFrame()
        focused = lf.filter(pl.col(yearCol).is_in(yearValues)).select(required)
    else:
        yearValues = [year, prevYear]
        required = ["stockCode", yearCol, "sj_div", "account_nm", "thstrm_amount"]
        if not set(required).issubset(columns):
            return pl.DataFrame()
        focused = (
            lf.filter(pl.col(yearCol).is_in(yearValues))
            .filter(pl.col("sj_div").is_in(["IS", "CIS"]))
            .filter(pl.col("account_nm").str.contains(_DART_NET_INCOME_PATTERN))
            .select(required)
        )
    return focused.collect(engine="streaming")


def calcEarningsSurprise(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Earnings Surprise (SUE) - 한국 시장 PEAD drift 후보 랭킹.

    Capabilities:
        - 전종목 YoY 순이익 성장률 + 횡단면 z-score
        - Top 10 positive SUE (post-earnings drift long 후보)
        - Top 10 negative SUE (drift short 후보)
        - Bernard-Thomas 1989 PEAD

    AIContext:
        - Sprint 2 재무 알파 - 펀더멘털 서프라이즈 momentum
        - story `earningsSurpriseBlock` 시장분석 자동 호출

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict - market / year / prevYear / universe / scores / topPos / topNeg / interpretation

    Guide:
        Bernard-Thomas 1989 PEAD - 발표 후 60~90 일 drift. Top 10 positive 는
        long candidate, top negative 는 short.

    When:
        Quant 펀더멘털 모멘텀 + AI 어닝 서프라이즈 답변.

    How:
        scan finance.parquet 2 기 → YoY 순이익 성장률 → 횡단면 z-score → top
        10 양/음.

    Requires:
        scan finance.parquet (2 기 + universe ≥ 50).

    Raises:
        없음 - 실패는 None.

    Example:
        >>> r = calcEarningsSurprise()
        >>> r["topPos"][0]

    See Also:
        - calcEarnings : 단일 종목 SUE
        - calcPiotroskiFactor : 재무 건강
    """
    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        annual, yearCol, edgar = _annualFinanceLazy(lf)
        year = _latestEligibleYear(annual, yearCol)
        if year is None:
            return None
        prevYear = str(int(year) - 1)
        snap = _collectEarningsWindow(
            annual,
            yearCol=yearCol,
            year=year,
            prevYear=prevYear,
            edgar=edgar,
        )
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        log.warning("calcEarningsSurprise year 실패: %s", type(exc).__name__)
        return None

    year_val = int(year) if edgar else year
    prev_year_val = int(prevYear) if edgar else prevYear
    cur = snap.filter(pl.col(yearCol) == year_val)
    prev = snap.filter(pl.col(yearCol) == prev_year_val)
    if cur.is_empty() or prev.is_empty():
        return None

    growths: dict[str, float] = {}
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
        ni = extractAccount(s_cur, "net_income")
        ni_p = extractAccount(s_prev, "net_income")
        if ni is None or ni_p is None or abs(ni_p) < 1:
            continue
        growth = (ni - ni_p) / abs(ni_p)
        # 극단 outlier 클램핑 (±500%)
        growth = max(-5.0, min(5.0, growth))
        growths[code] = growth

    if len(growths) < 50:
        return None

    vals = np.asarray(list(growths.values()))
    mean = float(vals.mean())
    std = float(vals.std(ddof=1))
    scores = {c: (g - mean) / std if std > 0 else 0.0 for c, g in growths.items()}

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topPos = [(c, round(s, 2), round(growths[c], 2)) for c, s in sorted_items[:10]]
    topNeg = [(c, round(s, 2), round(growths[c], 2)) for c, s in sorted_items[-10:]]

    total = len(scores)
    # 단일 종목 분기 (Step 6)
    if stockCode:
        z = scores.get(stockCode)
        if z is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함, 전년 NI 필요)",
            }
        g = growths.get(stockCode, 0)
        verdict = (
            "positive SUE (PEAD long 후보)"
            if z > 0.5
            else ("negative SUE (drift short 후보)" if z < -0.5 else "neutral")
        )
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "prevYear": str(prev_year_val),
            "score": round(z, 2),
            "growth": round(g, 3),
            "category": verdict,
            "universe": total,
            "interpretation": (
                f"{stockCode} SUE z={round(z, 2)} (YoY NI {g:+.0%}) - {verdict}. Bernard-Thomas 1989 PEAD."
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "prevYear": str(prev_year_val),
        "universe": total,
        "scores": {c: round(s, 2) for c, s in scores.items()},
        "growths": {c: round(g, 3) for c, g in growths.items()},
        "topPos": topPos,
        "topNeg": topNeg,
        "interpretation": (
            f"{market} {year}년 SUE (YoY NI growth z-score, {total}종목) - "
            "positive SUE 상위가 Bernard-Thomas PEAD drift long 후보."
        ),
    }
