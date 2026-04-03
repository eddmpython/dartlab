"""매크로 종합 분석 — 전체 축 종합 매트릭스."""

from __future__ import annotations


def analyze_summary(*, market: str = "US", **kwargs) -> dict:
    """매크로 전체 종합 판정.

    각 축을 독립 호출하여 종합. 다른 축 모듈을 직접 import하지 않고
    각 축의 analyze_* 함수를 개별 호출한다.

    Returns:
        dict: cycle, rates, assets, sentiment, liquidity + overall 판정
    """
    from dartlab.macro.assets import analyze_assets
    from dartlab.macro.cycle import analyze_cycle
    from dartlab.macro.liquidity import analyze_liquidity
    from dartlab.macro.rates import analyze_rates
    from dartlab.macro.sentiment import analyze_sentiment

    cycle = analyze_cycle(market=market)
    rates = analyze_rates(market=market)
    assets = analyze_assets(market=market)
    sentiment = analyze_sentiment(market=market)
    liquidity = analyze_liquidity(market=market)

    # 종합 판정 스코어 (-3 ~ +3, 양수=우호적)
    score = 0.0
    reasons: list[str] = []

    # 사이클
    phase = cycle.get("phase", "")
    if phase in ("recovery", "expansion"):
        score += 1.0
        reasons.append(f"사이클 {cycle.get('phaseLabel', '')} — 우호적")
    elif phase == "contraction":
        score -= 1.5
        reasons.append(f"사이클 {cycle.get('phaseLabel', '')} — 비우호적")
    elif phase == "slowdown":
        score -= 0.5
        reasons.append(f"사이클 {cycle.get('phaseLabel', '')} — 주의")

    # 금리 방향
    outlook = rates.get("outlook", {})
    direction = outlook.get("direction", "")
    if direction == "cut":
        score += 0.5
        reasons.append("금리 인하 기대 — 유동성 우호적")
    elif direction == "hike":
        score -= 0.5
        reasons.append("금리 인상 가능 — 유동성 비우호적")

    # 심리
    fg = sentiment.get("fearGreed")
    if fg is not None:
        fg_score = fg.get("score", 50)
        if fg_score < 25:
            score -= 0.5
            reasons.append(f"시장 심리 극단공포 ({fg_score:.0f})")
        elif fg_score > 75:
            score -= 0.3  # 과열 경계
            reasons.append(f"시장 심리 극단탐욕 ({fg_score:.0f}) — 과열 경계")
        elif fg_score > 55:
            score += 0.3
            reasons.append(f"시장 심리 탐욕 ({fg_score:.0f})")

    # 유동성
    liq_regime = liquidity.get("regime", "")
    if liq_regime == "abundant":
        score += 0.5
        reasons.append("유동성 풍부")
    elif liq_regime == "tight":
        score -= 0.5
        reasons.append("유동성 긴축")

    # 종합 판정
    if score >= 1.0:
        overall = "favorable"
        overallLabel = "우호적"
    elif score <= -1.0:
        overall = "unfavorable"
        overallLabel = "비우호적"
    else:
        overall = "neutral"
        overallLabel = "중립"

    return {
        "market": market.upper(),
        "overall": overall,
        "overallLabel": overallLabel,
        "score": round(score, 1),
        "reasons": reasons,
        "cycle": cycle,
        "rates": rates,
        "assets": assets,
        "sentiment": sentiment,
        "liquidity": liquidity,
    }
