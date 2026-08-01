"""매크로 종합 분석 — 전체 축 종합 매트릭스."""

from __future__ import annotations

import gc
import logging

log = logging.getLogger(__name__)


def _gcAfterAxis() -> None:
    """11 axis sequential 호출 사이의 메모리 압박 완화.

    각 axis (analyze_cycle/rates/assets/...) 가 fetch_multi · regime model · OLS 등
    polars 큰 transient 를 만든다. Python ref 는 axis 함수 return 후 풀리지만
    polars Rust 힙은 즉시 회수 안 됨. ``gc.collect()`` 와 폴라스의 string cache
    회수를 명시 호출해 다음 axis 진입 전 RSS 정리.

    R5 매크로 종합 호출 7632 MB peak 의 직접 fix (5 질문 batch v2 측정).
    """
    gc.collect()
    try:
        import polars as pl

        pl.disable_string_cache()
    except (ImportError, AttributeError):
        pass


def _scoreCycle(cycle: dict) -> tuple[float, list[str]]:
    if cycle.get("status") != "observed":
        return 0.0, []
    phase = cycle.get("phase", "")
    label = cycle.get("phaseLabel", "")
    if phase in ("recovery", "expansion"):
        return 1.0, [f"사이클 {label} — 우호적"]
    if phase == "contraction":
        return -1.5, [f"사이클 {label} — 비우호적"]
    if phase == "slowdown":
        return -0.5, [f"사이클 {label} — 주의"]
    return 0.0, []


def _scoreRates(rates: dict) -> tuple[float, list[str]]:
    outlook = rates.get("outlook", {})
    if outlook.get("status") != "observed":
        return 0.0, []
    direction = outlook.get("direction", "")
    if direction == "cut":
        return 0.5, ["금리 인하 기대 — 유동성 우호적"]
    if direction == "hike":
        return -0.5, ["금리 인상 가능 — 유동성 비우호적"]
    return 0.0, []


def _scoreSentiment(sentiment: dict) -> tuple[float, list[str]]:
    fg = sentiment.get("fearGreed")
    if fg is None:
        return 0.0, []
    fg_score = fg.get("score")
    if fg_score is None:
        return 0.0, []
    if fg_score < 25:
        return -0.5, [f"시장 심리 극단공포 ({fg_score:.0f})"]
    if fg_score > 75:
        return -0.3, [f"시장 심리 극단탐욕 ({fg_score:.0f}) — 과열 경계"]
    if fg_score > 55:
        return 0.3, [f"시장 심리 탐욕 ({fg_score:.0f})"]
    return 0.0, []


def _scoreNarrative(narrative: dict | None) -> tuple[float, list[str]]:
    """narrative 축 점수 — Phase C, news headline pulse 기반 (-0.7~+0.4 contrib).

    score ≤ -2 → -0.7 (극단공포 narrative — 방어 신호)
    score ≤ -1 → -0.4 (비관)
    score ≥ +2 → -0.2 (극단탐욕 — 과열 경계, 역방향 감점)
    score ≥ +1 → +0.4 (낙관)
    else → 0.0.
    """
    if not narrative or not isinstance(narrative, dict):
        return 0.0, []
    raw_score = narrative.get("score")
    if raw_score is None:
        return 0.0, []
    s = float(raw_score)
    label = narrative.get("label", "중립")
    if s <= -2:
        return -0.7, [f"narrative 극단 비관 ({label})"]
    if s <= -1:
        return -0.4, ["narrative 비관"]
    if s >= 2:
        return -0.2, [f"narrative 극단 낙관 ({label}) — 과열 경계"]
    if s >= 1:
        return 0.4, ["narrative 낙관"]
    return 0.0, []


def _scoreLiquidity(liquidity: dict) -> tuple[float, list[str]]:
    if liquidity.get("status") != "observed":
        return 0.0, []
    regime = liquidity.get("regime", "")
    if regime == "abundant":
        return 0.5, ["유동성 풍부"]
    if regime == "tight":
        return -0.5, ["유동성 긴축"]
    return 0.0, []


def _coreCoverage(
    cycle: dict,
    rates: dict,
    assets: dict,
    sentiment: dict,
    liquidity: dict,
) -> tuple[dict[str, bool], list[str]]:
    """종합 결론에 필요한 5개 독립 축의 실제 관측 여부를 계산한다."""
    coverage = {
        "cycle": cycle.get("status") == "observed" and cycle.get("phase") is not None,
        "rates": rates.get("outlook", {}).get("status") == "observed"
        and rates.get("outlook", {}).get("direction") is not None,
        "assets": bool(assets.get("assets")),
        "sentiment": any(sentiment.get(key) is not None for key in ("fearGreed", "vixRegime", "macroUncertainty")),
        "liquidity": liquidity.get("status") == "observed" and liquidity.get("regime") is not None,
    }
    gaps = [axis for axis, observed in coverage.items() if not observed]
    return coverage, gaps


def _scoreForecast(forecastResult: dict | None) -> tuple[float, list[str]]:
    if not forecastResult:
        return 0.0, []
    contrib = 0.0
    reasons: list[str] = []
    rp = forecastResult.get("recessionProb")
    if rp and rp.get("probability") is not None:
        prob = rp["probability"]
        if prob > 0.4:
            contrib -= 0.5
            reasons.append(f"침체확률 {prob * 100:.0f}% — 경계")
        elif prob < 0.15:
            contrib += 0.3
            reasons.append(f"침체확률 {prob * 100:.0f}% — 낮음")
    lei = forecastResult.get("lei")
    if lei and isinstance(lei, dict):
        lei_signal = lei.get("signal")
        if lei_signal == "recession_warning":
            contrib -= 0.5
            reasons.append("LEI 침체 경고")
        elif lei_signal == "expansion":
            contrib += 0.3
            reasons.append("LEI 확장 지속")
    return contrib, reasons


def _scoreCrisis(crisisResult: dict | None) -> tuple[float, list[str]]:
    if not crisisResult:
        return 0.0, []
    cg = crisisResult.get("creditGap")
    if cg and cg.get("zone") in ("warning", "danger"):
        return -0.5, [f"Credit-to-GDP gap {cg.get('zoneLabel', '')}"]
    return 0.0, []


def _scoreInventory(inventoryResult: dict | None) -> tuple[float, list[str]]:
    if not inventoryResult:
        return 0.0, []
    ip = inventoryResult.get("inventoryPhase")
    if not ip:
        return 0.0, []
    eq = ip.get("equityImplication")
    label = ip.get("phaseLabel", "")
    if eq == "bullish":
        return 0.3, [f"재고순환 {label} — 긍정"]
    if eq == "bearish":
        return -0.3, [f"재고순환 {label} — 부정"]
    return 0.0, []


def _scoreTrade(tradeResult: dict | None, market: str) -> tuple[float, list[str]]:
    if not tradeResult or market.upper() != "KR":
        return 0.0, []
    tot = tradeResult.get("termsOfTrade")
    if not tot:
        return 0.0, []
    direction = tot.get("direction")
    if direction == "improving":
        return 0.3, ["교역조건 개선 — 수출 우호적"]
    if direction == "deteriorating":
        return -0.3, ["교역조건 악화 — 수출 부정적"]
    return 0.0, []


def _scoreCorporate(corporateResult: dict | None) -> tuple[float, list[str]]:
    if not corporateResult:
        return 0.0, []
    contrib = 0.0
    reasons: list[str] = []
    ec = corporateResult.get("earningsCycle")
    if ec and ec.get("currentDirection") == "contracting":
        contrib -= 0.3
        reasons.append(f"기업이익 수축 ({ec.get('currentLabel', '')})")
    elif ec and ec.get("currentDirection") == "expanding":
        contrib += 0.3
        reasons.append(f"기업이익 확장 ({ec.get('currentLabel', '')})")
    pr = corporateResult.get("ponziRatio")
    if pr and pr.get("currentRatio", 0) > 0.3:
        contrib -= 0.3
        reasons.append(f"Ponzi 비율 {pr.get('currentRatio', 0):.1%} — 금융 취약")
    return contrib, reasons


def _buildAllocation(
    overall: str, cycle: dict, sentiment: dict, liquidity: dict, crisisResult: dict | None
) -> dict | None:
    """포트폴리오 매핑 — regimeToAllocation → equity/bond/gold/cash 비중 dict."""
    try:
        from dartlab.synth.portfolioMapping import regimeToAllocation

        alloc = regimeToAllocation(
            {
                "overall": overall,
                "cycle": cycle,
                "sentiment": sentiment,
                "liquidity": liquidity
                if isinstance(liquidity, dict)
                else {"regime": liquidity.get("regime") if isinstance(liquidity, dict) else ""},
                "crisis": crisisResult,
            }
        )
        return {
            "equity": alloc.equity,
            "bond": alloc.bond,
            "gold": alloc.gold,
            "cash": alloc.cash,
            "regime": alloc.regime,
            "rationale": alloc.rationale,
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _buildStrategiesDashboard(
    cycle,
    rates,
    assets,
    sentiment,
    liquidity,
    forecastResult,
    crisisResult,
    inventoryResult,
    tradeResult,
    corporateResult,
) -> dict | None:
    """40개 투자전략 대시보드 — evaluateStrategies → signals list."""
    try:
        from dartlab.synth.strategyRules import evaluateStrategies

        signals = evaluateStrategies(
            {
                "cycle": cycle,
                "rates": rates,
                "assets": assets,
                "sentiment": sentiment,
                "liquidity": liquidity,
                "forecast": forecastResult,
                "crisis": crisisResult,
                "inventory": inventoryResult,
                "trade": tradeResult,
                "corporate": corporateResult,
            }
        )
        return {
            "total": len(signals),
            "active": sum(1 for s in signals if s.active is True),
            "bullish": sum(1 for s in signals if s.active and s.direction == "bullish"),
            "bearish": sum(1 for s in signals if s.active and s.direction == "bearish"),
            "signals": [
                {
                    "id": s.id,
                    "name": s.name,
                    "active": s.active,
                    "direction": s.direction,
                    "strength": s.strength,
                    "confidence": s.confidence,
                    "description": s.description,
                }
                for s in signals
            ],
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _addGrowthAtRisk(forecastResult: dict | None, liquidity: dict, asOf: str | None) -> None:
    """Adrian-Boyarchenko-Giannone (2019) FCI → GDP 분위회귀. forecast_result 에 in-place 추가."""
    if forecastResult is None:
        return
    try:
        from dartlab.macro.crisis.growthAtRisk import growthAtRisk as _gar
        from dartlab.macro.seriesFetch import fetchSeriesList, getGather

        fci_data = liquidity.get("fci") if isinstance(liquidity, dict) else None
        fci_series = fci_data.get("history") if isinstance(fci_data, dict) else None

        _g = getGather(asOf)
        gdp_series = fetchSeriesList(_g, "GDP")
        if not (gdp_series and len(gdp_series) >= 20):
            return
        gdp_growth = [
            ((gdp_series[i] / gdp_series[i - 4]) - 1) * 100
            for i in range(4, len(gdp_series))
            if gdp_series[i - 4] and gdp_series[i - 4] > 0
        ]

        if not fci_series:
            nfci_series = fetchSeriesList(_g, "NFCI")
            if nfci_series and len(nfci_series) >= 20:
                fci_series = nfci_series

        if fci_series and gdp_growth:
            gar = _gar(fci_series, gdp_growth, horizon=4)
            if gar:
                forecastResult["growthAtRisk"] = gar
    except (KeyError, ValueError, TypeError, AttributeError, ImportError):
        return


def analyzeSummary(*, market: str = "US", asOf: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """매크로 전체 종합 판정 — 종목 분석 시 macro 호출은 이 함수 1회로 끝낸다.

    Capabilities:
        11 축 (cycle/rates/assets/sentiment/liquidity/forecast/crisis/
        inventory/trade/corporate/scenario) 을 순차 호출 → 가중 스코어
        합산 → overall (favorable/neutral/unfavorable) + 자산배분 +
        40 투자전략 대시보드를 단일 dict 로 반환. 각 축 사이 ``_gcAfterAxis``
        로 polars Rust 힙 회수 (R5 호출 7632MB peak 의 직접 fix).

    Args:
        market: 시장 코드 ``"US"`` 또는 ``"KR"``. 기본 ``"US"``. 종목의
            currency 와 맞춰야 cycle/sentiment/trade 결과가 의미 있음.
        asOf: 기준일 (YYYY-MM-DD). ``None`` 이면 최신 호출.
        overrides: AI 가정 교체 dict. 전체 축에 전파.
        **kwargs: BC 흡수 (현재 미사용).

    Returns:
        dict with keys:
            - ``market`` (str): 입력 echo
            - ``overall`` (str): ``"favorable"``/``"neutral"``/``"unfavorable"``
            - ``overallLabel`` (str): 한국어
            - ``score`` (float): -4 ~ +4 가중 합
            - ``contributions`` (dict[str, float]): 축별 기여도 (0 제외)
            - ``reasons`` (list[str]): 판정 근거
            - ``cycle``/``rates``/``assets``/``sentiment``/``liquidity``
              (dict): 5 핵심 축 결과
            - ``forecast``/``crisis``/``inventory``/``trade``/``corporate``
              (dict|None): 5 보조 축 (실패해도 종합 판정은 계속)
            - ``allocation`` (dict|None): 자산배분 ``{equity, bond, gold,
              cash, regime, rationale}``
            - ``strategies`` (dict|None): 40 전략 대시보드
              ``{total, active, bullish, bearish, signals}``

    Raises:
        없음. 보조 축 실패는 흡수한다. 핵심 5축 중 하나라도 근거가 없으면
        status="blocked"로 반환하고 overall/score/allocation/strategies를 발행하지 않는다.

    Example:
        >>> from dartlab.macro import Macro
        >>> r = Macro()(market="KR")
        >>> r["overall"], r["allocation"]["equity"]
        ('favorable', 60)

    Guide:
        종목 분석 컨텍스트에서는 이 함수 1 회 호출로 끝낸다. 개별 축
        (analyzeCycle, analyzeRates 등) 11 번 반복 호출 금지 — 같은 데이터
        2 회 fetch + polars 힙 추가 압박. 단일 축은 사용자가 "금리만
        자세히" 같이 명시했을 때만.

    See Also:
        - ``dartlab.macro.cycles.cycle.analyzeCycle``
        - ``dartlab.macro.rates.rates.analyzeRates``
        - ``dartlab.synth.portfolioMapping.regimeToAllocation``
        - ``dartlab.synth.strategyRules.evaluateStrategies``

    When:
        ``Macro().__call__`` 단일 진입점. 종목 분석 시 macro 호출 1 회로 종결.

    How:
        5 핵심 축 (cycle/rates/assets/sentiment/liquidity) 순차 → _gcAfterAxis →
        5 보조 축 (forecast/crisis/inventory/trade/corporate) try/except → score
        가중 합산 → regimeToAllocation → evaluateStrategies → dict 합성.

    Requires:
        DART/EDGAR provider + Yahoo Finance + FRED/KOSIS. 인터넷 필요.

    AIContext:
        결과 dict 의 ``contributions`` 가 overall 의 직접 근거이므로
        해석 시 가장 큰 기여 축 1~2 개를 인용. allocation 은 정성
        권고이지 trade rule 이 아니다. strategies 의 high-confidence active
        만 필터링해 사용 권장.

    LLM Specifications:
        AntiPatterns:
            - 종목별로 매번 analyzeSummary 호출 금지. 한 세션 내 최신
              결과 재사용 (caching 책임은 호출자).
            - market="US" 로 호출한 결과를 KR 종목 분석에 사용 금지 (금리/
              유동성 축이 달라짐).
            - 개별 축 dict 의 score 합산을 직접 재계산하지 말 것 — 가중치는
              내부 비공개.
        OutputSchema:
            ``{market, overall, overallLabel, score, contributions, reasons,
            cycle, rates, assets, sentiment, liquidity, forecast, crisis,
            inventory, trade, corporate, allocation, strategies}``.
        Prerequisites:
            네트워크 + macro provider 활성. analyzeCycle/Rates/Assets/
            Sentiment/Liquidity 5 핵심 축 모두 성공해야 점수 신뢰 가능.
        Freshness:
            cycle/rates 일 단위, sentiment/liquidity 주 단위. asOf=None 이면
            real-time fetch.
        Dataflow:
            analyzeCycle → analyzeRates → analyzeAssets → calcSentiment →
            calcLiquidity (각 _gcAfterAxis) → 보조 5 축 → score 합산 →
            regimeToAllocation → evaluateStrategies → dict 조립.
        TargetMarkets: US, KR (market 인자로 분기). JP/EM 미지원.
    """
    from dartlab.macro.corporate.assets import analyzeAssets
    from dartlab.macro.cycles.cycle import analyzeCycle
    from dartlab.macro.cycles.liquidity import calcLiquidity
    from dartlab.macro.cycles.sentiment import calcSentiment
    from dartlab.macro.rates.rates import analyzeRates

    # 기준일과 내부 시나리오 지표 치환을 전체 축에 동일하게 전파한다.
    _ax = {"market": market, "asOf": asOf, "overrides": overrides}

    cycle = analyzeCycle(**_ax)
    _gcAfterAxis()
    rates = analyzeRates(**_ax)
    _gcAfterAxis()
    assets = analyzeAssets(**_ax)
    _gcAfterAxis()
    sentiment = calcSentiment(**_ax)
    _gcAfterAxis()
    liquidity = calcLiquidity(**_ax)
    _gcAfterAxis()

    # 신규 축 (실패해도 종합 판정은 계속)
    forecastResult = None
    crisisResult = None
    inventoryResult = None
    tradeResult = None

    try:
        from dartlab.macro.forecast.forecast import analyzeForecast

        forecastResult = analyzeForecast(**_ax)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    try:
        from dartlab.macro.crisis.crisis import analyzeCrisis

        # 다른 축 결과를 crisis에 전달
        crisis_kwargs: dict = {}
        if forecastResult:
            rp = forecastResult.get("recessionProb")
            if rp:
                crisis_kwargs["probitProb"] = rp.get("probability")
            lei = forecastResult.get("lei")
            if lei and isinstance(lei, dict) and "signal" in lei:
                crisis_kwargs["leiSignal"] = lei.get("signal")
        crisisResult = analyzeCrisis(**_ax, **crisis_kwargs)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    try:
        from dartlab.macro.cycles.inventory import analyzeInventory

        inventoryResult = analyzeInventory(**_ax)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    try:
        from dartlab.macro.trade.trade import analyzeTrade

        tradeResult = analyzeTrade(**_ax)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    corporateResult = None
    try:
        from dartlab.macro.corporate.corporate import analyzeCorporate

        corporateResult = analyzeCorporate(**_ax)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    narrativeResult: dict | None = None
    try:
        from dartlab.macro.narrative.narrative import analyzeNarrative

        narrativeResult = analyzeNarrative(market=market, asOf=asOf)
        _gcAfterAxis()
    except (KeyError, ValueError, TypeError, AttributeError, ImportError):
        narrativeResult = None

    core_coverage, core_gaps = _coreCoverage(cycle, rates, assets, sentiment, liquidity)
    conclusion_eligible = not core_gaps

    score = 0.0
    reasons: list[str] = []
    contributions: dict[str, float] = {}

    # 10 축 scoring 을 sub 에 위임 — 각 sub 는 (contrib, reason_list) 리턴.
    for axisName, contrib, axReasons in (
        ("cycle", *_scoreCycle(cycle)),
        ("rates", *_scoreRates(rates)),
        ("sentiment", *_scoreSentiment(sentiment)),
        ("liquidity", *_scoreLiquidity(liquidity)),
        ("forecast", *_scoreForecast(forecastResult)),
        ("crisis", *_scoreCrisis(crisisResult)),
        ("inventory", *_scoreInventory(inventoryResult)),
        ("trade", *_scoreTrade(tradeResult, market)),
        ("corporate", *_scoreCorporate(corporateResult)),
        ("narrative", *_scoreNarrative(narrativeResult)),
    ):
        if conclusion_eligible:
            score += contrib
            contributions[axisName] = contrib
            reasons.extend(axReasons)

    # 종합 판정
    if not conclusion_eligible:
        overall = None
        overallLabel = "판정불가"
    elif score >= 1.0:
        overall = "favorable"
        overallLabel = "우호적"
    elif score <= -1.0:
        overall = "unfavorable"
        overallLabel = "비우호적"
    else:
        overall = "neutral"
        overallLabel = "중립"

    allocation_result = None
    strategies_result = None
    if conclusion_eligible:
        allocation_result = _buildAllocation(overall, cycle, sentiment, liquidity, crisisResult)
        strategies_result = _buildStrategiesDashboard(
            cycle,
            rates,
            assets,
            sentiment,
            liquidity,
            forecastResult,
            crisisResult,
            inventoryResult,
            tradeResult,
            corporateResult,
        )
    _addGrowthAtRisk(forecastResult, liquidity, asOf)

    return {
        "market": market.upper(),
        "status": "usable" if conclusion_eligible else "blocked",
        "blockedReason": (None if conclusion_eligible else f"핵심 매크로 근거 부족: {', '.join(core_gaps)}"),
        "coverage": {
            "observed": sum(core_coverage.values()),
            "required": len(core_coverage),
            "axes": core_coverage,
            "gaps": core_gaps,
        },
        "overall": overall,
        "overallLabel": overallLabel,
        "score": round(score, 1) if conclusion_eligible else None,
        "contributions": {k: round(v, 2) for k, v in contributions.items() if v != 0},
        "reasons": reasons,
        "cycle": cycle,
        "rates": rates,
        "assets": assets,
        "sentiment": sentiment,
        "liquidity": liquidity,
        "forecast": forecastResult,
        "crisis": crisisResult,
        "inventory": inventoryResult,
        "trade": tradeResult,
        "corporate": corporateResult,
        "narrative": narrativeResult,
        "allocation": allocation_result,
        "strategies": strategies_result,
    }
