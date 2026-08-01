"""매크로 사이클 분석 — 4국면 판별 + 전환 시퀀스."""

from __future__ import annotations

from dartlab.macro.cycles.macroCycle import classifyCycle, detectTransitionSequence
from dartlab.macro.seriesFetch import (
    applyOverrides,
    collectTimeseries,
    fetchChangePct,
    fetchLatest,
    fetchYoy,
    getGather,
    recentTimeseries,
)


def _fetchIndicators(market: str, asOf: str | None = None) -> dict[str, float | None]:
    """gather에서 사이클 판별에 필요한 지표 수집.

    Parameters
    ----------
    market : str
        ``"US"`` | ``"KR"``.
    as_of : str | None
        기준일 (``"2024-06-30"``). ``None`` 이면 최신.

    Returns
    -------
    dict[str, float]
        None 값은 제거된 채 반환. 가능한 키:

        - hy_spread : float — HY 스프레드 (bp)
        - hy_spread_3m_change : float — HY 스프레드 3개월 변화율 (%)
        - term_spread : float — 10Y-2Y 금리차 (%p)
        - vix : float — VIX 지수 (pt)
        - gold_yoy : float — 금 가격 전년비 변화율 (%)
        - bei_10y : float — 10년 BEI 기대인플레 (%)
        - cpi_yoy : float — CPI 전년비 (%)
        - cli_mom : float — OECD CLI 전월차 (pt, KR 전용)
    """
    g = getGather(asOf)
    indicators: dict[str, float | None] = {}

    if market.upper() == "US":
        hy = fetchLatest(g, "BAMLH0A0HYM2")
        if hy is not None:
            indicators["hy_spread"] = hy * 100
        hy_chg = fetchChangePct(g, "BAMLH0A0HYM2", 63)
        if hy_chg is not None:
            indicators["hy_spread_3m_change"] = hy_chg

        indicators["term_spread"] = fetchLatest(g, "T10Y2Y")
        indicators["vix"] = fetchLatest(g, "VIXCLS")
        indicators["gold_yoy"] = fetchYoy(g, "IR14270")
        indicators["bei_10y"] = fetchLatest(g, "T10YIE")
        indicators["cpi_yoy"] = fetchYoy(g, "CPIAUCSL")

    elif market.upper() == "KR":
        from dartlab.macro.seriesFetch import fetchLatestWithPrev

        cli, cli_prev = fetchLatestWithPrev(g, "CLI")
        if cli is not None and cli_prev is not None:
            indicators["cli_mom"] = cli - cli_prev

    # None 값 제거 (classifyCycle은 키 존재 여부로 판단)
    return {k: v for k, v in indicators.items() if v is not None}


def _buildSignalHistory(market: str, asOf: str | None = None) -> dict[str, list[tuple[str, float]]] | None:
    """전환 시퀀스 순서 검증을 위한 시계열 이력 구축.

    최근 12개월 데이터를 ``[(날짜, 값)]`` 형태로 반환.

    Parameters
    ----------
    market : str
        ``"US"`` 만 지원. 그 외 시장은 ``None`` 반환.
    as_of : str | None
        기준일. ``None`` 이면 최신.

    Returns
    -------
    dict[str, list[tuple[str, float]]] | None
        신호별 최근 12개월 시계열. ``None`` = US 외 시장이거나 데이터 부재. 키:

        - hy_spread_3m_change — HY 스프레드 3개월 변화
        - gold_yoy — 금 전년비
        - long_rate_change — 10Y 국채금리 변화
        - vix — VIX 지수
        - term_spread — 10Y-2Y 금리차
        - bei_10y — 10년 BEI
    """
    if market.upper() != "US":
        return None
    g = getGather(asOf)
    history: dict[str, list[tuple[str, float]]] = {}

    # 신호 → FRED 시리즈 매핑
    seriesMap = {
        "hy_spread_3m_change": "BAMLH0A0HYM2",
        "gold_yoy": "IR14270",
        "long_rate_change": "DGS10",
        "vix": "VIXCLS",
        "term_spread": "T10Y2Y",
        "bei_10y": "T10YIE",
    }
    for key, sid in seriesMap.items():
        ts = recentTimeseries(g.macro(sid), months=12)
        if ts:
            history[key] = [(entry["date"], entry["value"]) for entry in ts if entry["value"] is not None]

    return history if history else None


def analyzeCycle(*, market: str = "US", asOf: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """매크로 사이클 — 4 국면 판정 + 전환 시퀀스 + Bridgewater 4 분면.

    Capabilities:
        HY spread · VIX · term spread 등 매크로 지표를 fetch 해 경기 4 국면 (확장/둔화/수축/회복)
        을 판정하고, 신호 시계열 이력에서 전환 시퀀스 (다음 국면으로의 진행률 + 순서 검증) 와
        Bridgewater 4 분면 (성장 × 인플레) 을 단일 dict 로 반환. US/KR 동일 진입점.

    Parameters
    ----------
    market : str, default "US"
        시장 코드 — "US" 또는 "KR".
    asOf : str | None, default None
        기준일 (YYYY-MM-DD). None 이면 최신 데이터.
    overrides : dict | None, default None
        지표 강제 치환 (예: ``{"vix": 35}``). 시나리오/스트레스 테스트용.
    **kwargs
        forward-compat 확장 슬롯.

    Returns
    -------
    dict
        market : str — 입력 그대로 (대문자)
        phase : str — "expansion" | "slowdown" | "contraction" | "recovery"
        phaseLabel : str — 한글 ("확장" | "둔화" | "수축" | "회복")
        confidence : str — "high" | "medium" | "low"
        signals : list[str] — 판정에 사용된 신호 목록
        sectorStrategy : str — 국면별 섹터 전략 가이드
        transition : dict | None — 전환 시퀀스 (from/to/progress/triggered/pending/sequenceOrder/orderValid)
        timeseries : dict — hy_spread/vix/term_spread 시계열
        quadrant : dict | None — Bridgewater 4 분면 (US 만 활성)

    Raises
    ------
    없음 (지표 fetch 실패 시 confidence="low" + signals 축약).

    Example
    -------
    >>> r = analyzeCycle(market="US")
    >>> r["phase"], r["phaseLabel"], r["confidence"]
    ('slowdown', '둔화', 'high')
    >>> analyzeCycle(market="US", overrides={"vix": 35})["phase"]
    'contraction'

    Guide
    -----
    L1 gather (FRED · BOK ECOS) 의 실시간 fetch 가 필요 — 오프라인 환경에서는 overrides 로
    대체. KR 시장은 BSI/CPI 기반 (US 와 지표 다름), quadrant 는 현재 US 만.

    SeeAlso
    -------
    - ``dartlab.synth.quadrant.classifyQuadrant`` : 성장 × 인플레 4 분면
    - ``dartlab.macro.cycles.macroCycle.calcMultipleBand`` : 사이클 기반 multiple band
    - See Also: 위와 동일

    When:
        ``macro("cycle")`` 단일 진입점. AI 매크로 환경 답변 1 차.

    How:
        ``_fetchIndicators`` (FRED/ECOS) → overrides → ``classifyCycle`` → transition + quadrant
        → dict 합성.

    Requires
    --------
    - L1 gather: FRED (US) 또는 BOK ECOS (KR) 접근
    - 신호 history baseline 1 년 이상 (전환 시퀀스 신뢰도)

    AIContext
    ---------
    매크로 환경 1 차 답변 진입점. phaseLabel + sectorStrategy 두 필드만 인용해도 한 단락 답변
    가능. transition.progress 가 70%+ 면 "다음 국면 임박" 메시지 추가.

    Args
    ----
    market: 시장 코드 ``"US"`` (기본) 또는 ``"KR"``. KR 은 BSI/CPI 기반.
    asOf: 기준일 ``YYYY-MM-DD``. None 이면 최신.
    overrides: 지표 강제 치환. 키: ``vix``/``hySpread``/``termSpread`` 등.
    **kwargs: forward-compat. 현재 미사용.

    LLM Specifications:
        AntiPatterns:
            - phase 만 인용 (confidence 무시) — low confidence 면 결과 약함
            - transition 누락 — progress < 30% 면 transition None 또는 미트리거
            - KR 시장에 quadrant 기대 — US 만 활성
        OutputSchema:
            ``{market: str, phase: str, phaseLabel: str, confidence: str,
            signals: list[str], sectorStrategy: str, transition: dict|None,
            timeseries: dict, quadrant: dict|None}``.
        Prerequisites:
            FRED (US) 또는 ECOS (KR) cache. 1 년+ history baseline.
        Freshness:
            FRED 일간 (hy_spread, vix, term_spread) — 호출 시점 캐시 갱신.
        Dataflow:
            _fetchIndicators → overrides → classifyCycle → detectTransition
            (전환 시퀀스) → classifyQuadrant (US 만) → dict.
        TargetMarkets: US (FRED 풀세트), KR (ECOS BSI/CPI 일부).
    """
    indicators = _fetchIndicators(market, asOf=asOf)
    if overrides:
        indicators = applyOverrides(indicators, overrides)

    cycle = classifyCycle(indicators)

    # 시계열 이력 구축 — 전환 시퀀스 순서 검증용
    history = _buildSignalHistory(market, asOf)
    transition = detectTransitionSequence(cycle.phase, indicators, history=history) if cycle.phase is not None else None

    result: dict = {
        "market": market.upper(),
        "phase": cycle.phase,
        "phaseLabel": cycle.label,
        "confidence": cycle.confidence,
        "status": cycle.status,
        "observedInputs": cycle.observedInputs,
        "totalInputs": cycle.totalInputs,
        "signals": list(cycle.signals),
        "sectorStrategy": cycle.sectorStrategy,
        "transition": None,
    }

    if transition is not None:
        t_dict: dict = {
            "from": transition.fromPhase,
            "to": transition.toPhase,
            "progress": transition.progress,
            "triggered": list(transition.triggered),
            "pending": list(transition.pending),
        }
        if transition.sequenceOrder:
            t_dict["sequenceOrder"] = [{"signal": sig, "firstTriggered": dt} for sig, dt in transition.sequenceOrder]
        if transition.orderValid is not None:
            t_dict["orderValid"] = transition.orderValid
        result["transition"] = t_dict

    g = getGather(asOf)
    result["timeseries"] = collectTimeseries(
        g,
        {
            "hy_spread": "BAMLH0A0HYM2",
            "vix": "VIXCLS",
            "term_spread": "T10Y2Y",
        },
    )

    # ── Bridgewater 4 Quadrant (Growth × Inflation) ──
    try:
        from dartlab.synth.quadrant import classifyQuadrant

        if market.upper() == "US":
            # ISM PMI - 50 (성장 신호)
            ism = fetchLatest(g, "AMTMNO")
            # CPI YoY 3개월 모멘텀 (인플레 신호)
            cpiYoy = indicators.get("cpi_yoy")
            cpi_yoy_prev = fetchChangePct(g, "CPIAUCSL", 63)  # 3M ago
            if ism is not None and cpiYoy is not None:
                growthSignal = ism - 50.0
                # 인플레 모멘텀: 현재 CPI YoY 방향 (양수=상승 추세)
                inflationSignal = cpi_yoy_prev if cpi_yoy_prev is not None else 0.0
                result["quadrant"] = classifyQuadrant(growthSignal, inflationSignal)
        elif market.upper() == "KR":
            # BSI 제조업 (성장 대용치)
            bsi = fetchLatest(g, "BSI")
            cpi_yoy_kr = fetchYoy(g, "CPI")
            cpi_change = fetchChangePct(g, "CPI", 3)
            if bsi is not None and cpi_yoy_kr is not None:
                growthSignal = bsi - 100.0  # BSI 100 기준
                inflationSignal = cpi_change if cpi_change is not None else 0.0
                result["quadrant"] = classifyQuadrant(growthSignal, inflationSignal)
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    result.setdefault("quadrant", None)

    return result
