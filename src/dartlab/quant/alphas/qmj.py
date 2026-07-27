"""Asness-Frazzini-Pedersen QMJ 횡단면 quant factor.

학술: Asness, Frazzini, Pedersen (2019, Review of Accounting Studies) — Quality minus Junk.
     Q = (Profitability + Growth + Safety + Payout) / 4

dartlab 단순화 (단년도 data 기준):
    Profitability : (ROE_rank + ROA_rank + CFOA_rank) / 3
        ROE  = NI / Equity
        ROA  = NI / TA
        CFOA = OCF / TA
    Safety        : (1 − debtRatio_rank) = 저레버리지 선호
        debtRatio = TL / TA
    (Growth/Payout 생략 — 5y 시계열 / 배당 데이터 별도)

Q = 0.7 · Profitability + 0.3 · Safety

KR 2025 검증 완료 : RMW Sharpe +3.74 (factorBuild)
QMJ composite 는 profitability 핵심 축에 safety 10% 편입한 보수 안정판.
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


def calcQMJ(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Asness-Frazzini-Pedersen QMJ composite — 한국 시장 품질주 랭킹.

    Capabilities:
        - 전종목 Q-score (profitability + safety 합성)
        - Top 10 Quality / Bottom 10 Junk
        - RMW 단독 (+3.74) 위에 safety 편입한 저위험 quality 축

    AIContext:
        - Sprint 2 재무 알파 — FF5 RMW 의 robust 확장
        - story `qmjBlock` 시장분석 자동 호출

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict — market / year / universe / scores / components / topQuality / topJunk / interpretation

    Guide:
        Asness-Frazzini-Pedersen QMJ — profitability + safety + (payout 제외)
        합성. Q ≥ 0.95 = strong quality, Junk (≤ 0.05) = 회피.

    When:
        Quant 재무 알파 + AI quality 종목 답변.

    How:
        scan finance.parquet → profitability (ROE/GP/AssetTurnover) +
        safety (저변동/저레버리지) rank → 합성 Q-score.

    Requires:
        scan finance.parquet (수익성 + 레버리지 매핑).

    Raises:
        없음 — 실패는 None.

    Example:
        >>> calcQMJ()["topQuality"][0]

    See Also:
        - calcQuality : 단일 종목 QMJ
        - calcQFactor : Hou-Xue-Zhang q
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
        log.warning("calcQMJ year 실패: %s", type(exc).__name__)
        return None

    edgar = isEdgarSchema(snap)
    yearCol = "fy" if edgar else "bsns_year"
    year_val = int(year) if edgar else year
    cur = snap.filter(pl.col(yearCol) == year_val)
    if cur.is_empty():
        return None

    rows = []
    # 성능 fix (G5): partition_by 한 번 호출 → O(n) lookup
    partitions = cur.partition_by("stockCode", as_dict=True)
    for code_key, stock in partitions.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str) or stock.is_empty():
            continue
        ni = extractAccount(stock, "net_income")
        eq = extractAccount(stock, "total_equity")
        ta = extractAccount(stock, "total_assets")
        tl = extractAccount(stock, "total_liabilities")
        ocf = extractAccount(stock, "operating_cf")
        if not ta or ta <= 0 or not eq or eq <= 0 or tl is None:
            continue
        roe = ni / eq if ni is not None else None
        roa = ni / ta if ni is not None else None
        cfoa = ocf / ta if ocf is not None else None
        debt_ratio = tl / ta
        if roe is None or roa is None or cfoa is None:
            continue
        rows.append(
            {
                "code": code,
                "roe": roe,
                "roa": roa,
                "cfoa": cfoa,
                "debtRatio": debt_ratio,
            }
        )

    if len(rows) < 50:
        return None

    roe_r = _rank([r["roe"] for r in rows])
    roa_r = _rank([r["roa"] for r in rows])
    cfoa_r = _rank([r["cfoa"] for r in rows])
    safety_r = _rank([-r["debtRatio"] for r in rows])  # 낮을수록 좋음

    scores = {}
    components = {}
    for i, r in enumerate(rows):
        prof = (roe_r[i] + roa_r[i] + cfoa_r[i]) / 3
        q = 0.7 * prof + 0.3 * safety_r[i]
        scores[r["code"]] = q
        components[r["code"]] = {
            "roe": round(r["roe"], 4),
            "roa": round(r["roa"], 4),
            "cfoa": round(r["cfoa"], 4),
            "debtRatio": round(r["debtRatio"], 4),
            "profScore": round(prof, 3),
            "safetyScore": round(safety_r[i], 3),
        }

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topQuality = [(c, round(s, 3)) for c, s in sorted_items[:10]]
    topJunk = [(c, round(s, 3)) for c, s in sorted_items[-10:]]

    total = len(scores)
    # 단일 종목 분기 (Step 6)
    if stockCode:
        s = scores.get(stockCode)
        if s is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함)",
            }
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "score": round(s, 3),
            "percentile": round(100 * s, 1),
            "components": components.get(stockCode, {}),
            "universe": total,
            "interpretation": (
                f"{stockCode} QMJ={round(s, 3)} (백분위 {round(100 * s, 0):.0f}) — Asness Profitability + Safety 합성."
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "universe": total,
        "scores": {c: round(s, 3) for c, s in scores.items()},
        "components": components,
        "topQuality": topQuality,
        "topJunk": topJunk,
        "interpretation": (
            f"{market} {year}년 QMJ composite ({total}종목) — "
            "고 ROE/ROA/CFOA + 저 leverage 조합이 Asness QMJ premium 후보."
        ),
    }
