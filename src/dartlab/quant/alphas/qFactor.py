"""Hou-Xue-Zhang q-factor 횡단면 quant factor.

학술: Hou, Xue, Zhang (2015, Review of Financial Studies) — q-theory 기반 4-factor.
     Q-Factor(i) = w_I · (−I/A) + w_ROE · ROE

     (−I/A) = "conservative investment" premium (Asset growth 낮으면 우위)
     ROE = profitability premium

FF5 의 RMW + CMA 를 하나의 q-axis 로 재구성. H-X-Z 연구에서 FF5 를 능가한다고 주장.

dartlab 에선 FF5 의 RMW/CMA 가 이미 있으므로 q-factor 는 **복합 composite score**.
    q = 0.5 · roe_rank + 0.5 · (−assetGrowth)_rank

동점일 때 우위: 수익성 + 보수적 투자 합성.
"""

from __future__ import annotations

import logging

import numpy as np

from dartlab.quant.alphas.crossSection import percentileRank
from dartlab.quant.factor.build import _buildUniverseMetrics, _latestYear
from dartlab.quant.screen.dataAccess import loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated

log = logging.getLogger(__name__)


def _percentileRank(values: list[float]) -> list[float]:
    """값 목록을 0~1 백분위 순위로 바꾼다. 규칙은 `crossSection.percentileRank` 가 갖는다.

    예전에는 이 다섯 줄이 알파 세 파일에 글자까지 똑같이 복사돼 있었다. 한 곳만 tie
    처리를 바꾸면 같은 유니버스에서 팩터마다 다른 줄 세우기가 된다.
    """
    return percentileRank(values)


def calcQFactor(
    *,
    market: str = "KR",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Hou-Xue-Zhang q-factor composite — 한국 시장 수익성+보수투자 복합 랭킹.

    Capabilities:
        - 전종목 q-score = 0.5·ROE_rank + 0.5·(−AssetGrowth)_rank
        - Top 10 (높은 수익성 + 낮은 투자 = q-factor 강한 alpha)
        - 팩터 분해 (Hou-Xue-Zhang 2015)

    AIContext:
        - Sprint 2 재무 알파 — FF5 RMW + CMA 를 composite 로 재조립
        - story `qFactorBlock` 시장분석 자동 호출

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict
            market : str
            year : str
            universe : int
            scores : dict[str, float] — {stockCode: q-score (0~1 percentile)}
            components : dict[str, dict] — {stockCode: {roe, assetGrowth}}
            topQ : list[tuple[str, float]] — Top 10 (0.99 이상)
            bottomQ : list[tuple[str, float]] — Bottom 10
            interpretation : str

    Guide:
        Hou-Xue-Zhang (2015) q-factor — FF5 RMW + CMA 재조립. q ≥ 0.95 = 강한
        alpha 후보.

    When:
        Quant 재무 알파 + AI q-factor 답변.

    How:
        scan finance.parquet 2 기 → ROE rank + -AssetGrowth rank → 0.5×0.5
        가중 합 → q-score percentile.

    Requires:
        scan finance.parquet (2 기 + AssetGrowth 매핑).

    Raises:
        없음 — 실패는 None.

    Example:
        >>> r = calcQFactor()
        >>> r["topQ"][0]

    See Also:
        - calcQMJ : Asness QMJ
        - calcPiotroskiFactor : 9 신호 합성
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
        log.warning("calcQFactor year 실패: %s", type(exc).__name__)
        return None

    metrics = _buildUniverseMetrics(market, str(year))
    if not metrics:
        return None

    # ROE (클수록 좋음), AssetGrowth (작을수록 좋음 → negative rank)
    valid = {c: m for c, m in metrics.items() if m.get("roe") is not None and m.get("assetGrowth") is not None}
    if len(valid) < 50:
        return None

    codes = list(valid.keys())
    roe_vals = [valid[c]["roe"] for c in codes]
    ag_vals = [-valid[c]["assetGrowth"] for c in codes]  # reverse sign

    roe_ranks = _percentileRank(roe_vals)
    ag_ranks = _percentileRank(ag_vals)

    scores = {codes[i]: 0.5 * roe_ranks[i] + 0.5 * ag_ranks[i] for i in range(len(codes))}
    components = {
        codes[i]: {
            "roe": round(valid[codes[i]]["roe"], 4),
            "assetGrowth": round(valid[codes[i]]["assetGrowth"], 4),
            "roeRank": round(roe_ranks[i], 3),
            "conservInvRank": round(ag_ranks[i], 3),
        }
        for i in range(len(codes))
    }

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    topQ = [(c, round(s, 3)) for c, s in sorted_items[:10]]
    bottomQ = [(c, round(s, 3)) for c, s in sorted_items[-10:]]

    # 단일 종목 분기 (Step 6)
    total = len(scores)
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
                f"{stockCode} q-score={round(s, 3)} (백분위 {round(100 * s, 0):.0f}) — "
                "Hou-Xue-Zhang ROE + (−assetGrowth) composite."
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "universe": total,
        "scores": {c: round(s, 3) for c, s in scores.items()},
        "components": components,
        "topQ": topQ,
        "bottomQ": bottomQ,
        "interpretation": (
            f"{market} {year}년 q-factor composite ({total}종목) — "
            "고 ROE + 저 asset growth 조합이 Hou-Xue-Zhang q-premium 후보."
        ),
    }
