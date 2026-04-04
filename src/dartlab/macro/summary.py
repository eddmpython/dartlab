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

    # 신규 축 (실패해도 종합 판정은 계속)
    forecast_result = None
    crisis_result = None
    inventory_result = None
    trade_result = None

    try:
        from dartlab.macro.forecast import analyze_forecast

        forecast_result = analyze_forecast(market=market)
    except Exception:
        pass

    try:
        from dartlab.macro.crisis import analyze_crisis

        # 다른 축 결과를 crisis에 전달
        crisis_kwargs: dict = {}
        if forecast_result:
            rp = forecast_result.get("recessionProb")
            if rp:
                crisis_kwargs["probitProb"] = rp.get("probability")
            lei = forecast_result.get("lei")
            if lei and isinstance(lei, dict) and "signal" in lei:
                crisis_kwargs["leiSignal"] = lei.get("signal")
        crisis_result = analyze_crisis(market=market, **crisis_kwargs)
    except Exception:
        pass

    try:
        from dartlab.macro.inventory import analyze_inventory

        inventory_result = analyze_inventory(market=market)
    except Exception:
        pass

    try:
        from dartlab.macro.trade import analyze_trade

        trade_result = analyze_trade(market=market)
    except Exception:
        pass

    corporate_result = None
    try:
        from dartlab.macro.corporate import analyze_corporate

        corporate_result = analyze_corporate(market=market)
    except Exception:
        pass

    # 종합 판정 스코어 (-4 ~ +4, 양수=우호적)
    score = 0.0
    reasons: list[str] = []

    # ── 기존 5축 ──

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

    # ── 신규 4축 ──

    # 예측 (LEI + 침체확률)
    if forecast_result:
        rp = forecast_result.get("recessionProb")
        if rp and rp.get("probability") is not None:
            prob = rp["probability"]
            if prob > 0.4:
                score -= 0.5
                reasons.append(f"침체확률 {prob*100:.0f}% — 경계")
            elif prob < 0.15:
                score += 0.3
                reasons.append(f"침체확률 {prob*100:.0f}% — 낮음")

        lei = forecast_result.get("lei")
        if lei and isinstance(lei, dict):
            lei_signal = lei.get("signal")
            if lei_signal == "recession_warning":
                score -= 0.5
                reasons.append("LEI 침체 경고")
            elif lei_signal == "expansion":
                score += 0.3
                reasons.append("LEI 확장 지속")

    # 위기
    if crisis_result:
        cg = crisis_result.get("creditGap")
        if cg and cg.get("zone") in ("warning", "danger"):
            score -= 0.5
            reasons.append(f"Credit-to-GDP gap {cg.get('zoneLabel', '')}")

    # 재고
    if inventory_result:
        ip = inventory_result.get("inventoryPhase")
        if ip:
            eq = ip.get("equityImplication")
            if eq == "bullish":
                score += 0.3
                reasons.append(f"재고순환 {ip.get('phaseLabel', '')} — 긍정")
            elif eq == "bearish":
                score -= 0.3
                reasons.append(f"재고순환 {ip.get('phaseLabel', '')} — 부정")

    # 교역 (KR만)
    if trade_result and market.upper() == "KR":
        tot = trade_result.get("termsOfTrade")
        if tot:
            tot_dir = tot.get("direction")
            if tot_dir == "improving":
                score += 0.3
                reasons.append("교역조건 개선 — 수출 우호적")
            elif tot_dir == "deteriorating":
                score -= 0.3
                reasons.append("교역조건 악화 — 수출 부정적")

    # 기업집계
    if corporate_result:
        ec = corporate_result.get("earningsCycle")
        if ec and ec.get("currentDirection") == "contracting":
            score -= 0.3
            reasons.append(f"기업이익 수축 ({ec.get('currentLabel', '')})")
        elif ec and ec.get("currentDirection") == "expanding":
            score += 0.3
            reasons.append(f"기업이익 확장 ({ec.get('currentLabel', '')})")

        pr = corporate_result.get("ponziRatio")
        if pr and pr.get("currentRatio", 0) > 0.3:
            score -= 0.3
            reasons.append(f"Ponzi 비율 {pr.get('currentRatio', 0):.1%} — 금융 취약")

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

    # ── 40개 투자전략 대시보드 ──
    strategies_result = None
    try:
        from dartlab.core.finance.strategyRules import evaluateStrategies

        macro_data = {
            "cycle": cycle,
            "rates": rates,
            "assets": assets,
            "sentiment": sentiment,
            "liquidity": liquidity,
            "forecast": forecast_result,
            "crisis": crisis_result,
            "inventory": inventory_result,
            "trade": trade_result,
            "corporate": corporate_result,
        }
        signals = evaluateStrategies(macro_data)
        active_count = sum(1 for s in signals if s.active is True)
        bullish_count = sum(1 for s in signals if s.active and s.direction == "bullish")
        bearish_count = sum(1 for s in signals if s.active and s.direction == "bearish")
        strategies_result = {
            "total": len(signals),
            "active": active_count,
            "bullish": bullish_count,
            "bearish": bearish_count,
            "signals": [
                {
                    "id": s.id,
                    "name": s.name,
                    "active": s.active,
                    "direction": s.direction,
                    "description": s.description,
                }
                for s in signals
            ],
        }
    except Exception:
        pass

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
        "forecast": forecast_result,
        "crisis": crisis_result,
        "inventory": inventory_result,
        "trade": trade_result,
        "corporate": corporate_result,
        "strategies": strategies_result,
    }
