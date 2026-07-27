"""Fundamental Momentum 횡단면 quant factor.

학술: Chordia & Shivakumar (2006, Journal of Financial Economics) — 펀더멘털 모멘텀
     (earnings momentum) 과 가격 모멘텀 교차가 price momentum 만 쓰는 것보다 우위.

구성:
    earnings growth = (NI_t − NI_{t-1}) / |NI_{t-1}|
    price momentum  = 12-1 month return (Jegadeesh-Titman 1993 표준)
    composite = 0.5 · earnings_rank + 0.5 · price_momentum_rank

Top 10 = earnings 증가 + 가격 상승 종목 = 가장 확신 있는 롱 후보.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.quant.alphas.crossSection import percentileRank
from dartlab.quant.factor.build import _latestYear
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _rank(values: list[float]) -> list[float]:
    """값 목록을 0~1 백분위 순위로 바꾼다. 규칙은 `crossSection.percentileRank` 가 갖는다.

    예전에는 이 다섯 줄이 알파 세 파일에 글자까지 똑같이 복사돼 있었다. 한 곳만 tie
    처리를 바꾸면 같은 유니버스에서 팩터마다 다른 줄 세우기가 된다.
    """
    return percentileRank(values)


def calcFundamentalMomentum(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Chordia-Shivakumar 펀더멘털×가격 composite 모멘텀 — 한국 시장 전종목 랭킹.

    Capabilities:
        - earnings growth (YoY NI) + 12-1 price momentum composite
        - Top 10 double-momentum (가장 확신 있는 롱 후보)
        - Bottom 10 (long/short 혹은 회피)

    AIContext:
        - Sprint 2 재무 알파 — 단일 price momentum 보다 실증 우위
        - story `fundMomentumBlock` 시장분석 자동 호출

    Args:
        market: ``"KR"`` 만 지원 (KRX _hfBulk 필요).

    Returns:
        dict — market / year / universe / scores / components / topDouble / bottomDouble

    Guide:
        Chordia-Shivakumar (2006) — earnings + price double momentum 이 single
        momentum 보다 강건. Top 10 double = 가장 확신 long.

    When:
        Quant 재무 알파 + AI double momentum 답변.

    How:
        earnings growth (YoY NI rank) + 12-1 price momentum rank → composite
        score → top/bottom 10.

    Requires:
        scan finance.parquet + KRX OHLCV (12 개월).

    Raises:
        없음 — 실패는 None.

    Example:
        >>> calcFundamentalMomentum()["topDouble"][0]

    See Also:
        - calcMomentum : price momentum 단독
        - calcEarningsSurprise : earnings SUE
    """
    if market != "KR":
        return None

    # ── earnings growth ──
    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
        year = _latestYear(snap)
        if year is None:
            return None
    except (OSError, ValueError, KeyError, AttributeError):
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
        g = (ni - ni_p) / abs(ni_p)
        growths[code] = max(-5.0, min(5.0, g))

    if len(growths) < 50:
        return None

    # ── 12-1 price momentum (KRX _hfBulk) ──
    try:
        from dartlab.gather.bulkData.hfBulk import loadFiltered

        long_df = loadFiltered(adjustment="raw")
    except Exception as exc:  # noqa: BLE001
        log.warning("fundMomentum price fetch 실패: %s", type(exc).__name__)
        return None
    if long_df is None or long_df.is_empty():
        return None

    # 종목별 12-1 momentum = log(close[t-22]/close[t-252])
    dates = long_df.get_column("BAS_DD").unique().sort(descending=True).to_list()
    if len(dates) < 260:
        return None
    target_codes = list(growths.keys())
    sub = long_df.filter(pl.col("ISU_CD").is_in(target_codes)).select(["BAS_DD", "ISU_CD", "TDD_CLSPRC"])

    momentums: dict[str, float] = {}
    for code in target_codes:
        stock = sub.filter(pl.col("ISU_CD") == code).sort("BAS_DD")
        close = stock.get_column("TDD_CLSPRC").to_numpy().astype(np.float64)
        if len(close) < 260:
            continue
        # skip last month (22 일), measure 12m ago = index -252
        try:
            ret = float(np.log(close[-22] / close[-252]))
        except (ValueError, IndexError):
            continue
        if not np.isfinite(ret):
            continue
        momentums[code] = ret

    common = sorted(set(growths.keys()) & set(momentums.keys()))
    if len(common) < 50:
        return None

    g_vals = [growths[c] for c in common]
    m_vals = [momentums[c] for c in common]
    g_r = _rank(g_vals)
    m_r = _rank(m_vals)

    scores = {common[i]: 0.5 * g_r[i] + 0.5 * m_r[i] for i in range(len(common))}
    components = {
        common[i]: {
            "earningsGrowth": round(g_vals[i], 3),
            "priceMom12_1": round(m_vals[i], 4),
            "earningsRank": round(g_r[i], 3),
            "priceRank": round(m_r[i], 3),
        }
        for i in range(len(common))
    }

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topDouble = [(c, round(s, 3)) for c, s in sorted_items[:10]]
    bottomDouble = [(c, round(s, 3)) for c, s in sorted_items[-10:]]

    total = len(scores)
    # 단일 종목 분기 (Step 6)
    if stockCode:
        s = scores.get(stockCode)
        if s is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함, 가격+재무 모두 필요)",
            }
        comp = components.get(stockCode, {})
        verdict = "double-momentum (long 후보)" if s > 0.7 else ("약한 모멘텀" if s > 0.3 else "역모멘텀 (회피)")
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "score": round(s, 3),
            "percentile": round(100 * s, 1),
            "components": comp,
            "category": verdict,
            "universe": total,
            "interpretation": (
                f"{stockCode} fund-momentum={round(s, 3)} (백분위 {round(100 * s, 0):.0f}) "
                f"— earnings {comp.get('earningsGrowth', 0):+.0%} + price12-1 {comp.get('priceMom12_1', 0):+.0%}. {verdict}."
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "universe": total,
        "scores": {c: round(s, 3) for c, s in scores.items()},
        "components": components,
        "topDouble": topDouble,
        "bottomDouble": bottomDouble,
        "interpretation": (
            f"{market} {year}년 Chordia-Shivakumar 펀더멘털×가격 composite "
            f"({total}종목) — top 10 이 가장 확신 있는 롱 후보."
        ),
    }
