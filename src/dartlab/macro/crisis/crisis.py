"""매크로 위기 감지 — Credit-to-GDP Gap + GHS 위기예측 + 침체 대시보드.

투자전략 32: 신용스프레드는 곧 설비투자조정압력이다
투자전략 33: 공급과잉은 대부분 도산을 수반한다
투자전략 35: 국내 신용위험은 소비자물가상승률과 상관관계가 높다
투자전략 38: 금융시장 위험이 커지면 달러화는 상승한다
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

from dartlab.macro.crisis._crisisDetectors import (
    _crisisCapexPressure,
    _crisisCreditCycle,
    _crisisCreditGap,
    _crisisDalio48Match,
    _crisisDalioCaseMatch,
    _crisisDalioDebtCycle,
    _crisisDollarSafeHaven,
    _crisisExcessBondPremium,
    _crisisFisherDeflation,
    _crisisGhsScore,
    _crisisHistoricalContext,
    _crisisKooBsr,
    _crisisKrCreditRisk,
    _crisisKrHousingStress,
    _crisisMinsky,
    _crisisRRTypes,
    _frozenToDict,
)
from dartlab.macro.crisis.detectors import recessionDashboard
from dartlab.macro.seriesFetch import getGather


def _fetchCrisisData(market: str, asOf: str | None = None) -> dict[str, float | list | None]:
    """gather에서 위기 감지 지표 수집.

    Parameters
    ----------
    market : str
        시장 코드 ("US" | "KR").
    as_of : str | None
        기준일 (YYYY-MM-DD). None이면 최신.

    Returns
    -------
    dict[str, float | list | None]
        credit_gdp_series : list[float] — Credit/GDP 비율 시계열 (%)
        sp500_3y_return : float — S&P500 3년 수익률 (%)
        vix : float — VIX 지수 (pt)
        dxy_current : float — 달러인덱스 현재값
        dxy_3m_ago : float — 달러인덱스 3개월 전 값
        hy_series : list[float] — HY 스프레드 시계열 (bps)
        hy_current : float — HY 스프레드 현재값 (bps)
        cpi_yoy : float — CPI YoY 변화율 (%, KR 전용)
        apt_yoy : float — 아파트 가격 YoY 변화율 (%, KR 전용)
        private_saving : float — 민간 저축 (US, 십억달러)
        private_investment : float — 민간 투자 (US, 십억달러)
        gdp_level : float — GDP 수준 (US, 십억달러)
        fed_funds : float — 연방기금금리 (US, %)
        dsr : float — 부채서비스비율 (US, %)
        npl : float — 부실채권비율 (US, %)
        us_cpi_yoy : float — 미국 CPI YoY (%)
        public_debt_to_gdp : float — 공공부채/GDP (%)
        gdp_growth : float — 실질GDP 성장률 (%)
        real_rate : float — 10Y TIPS 실질금리 (%)
        debt_service_yoy : float — 부채서비스율 전년 대비 변화 (%p)
        total_debt_to_gdp : float — 총부채/GDP (%)
    """
    from dartlab.macro.seriesFetch import fetchLatest, fetchSeriesList, fetchYoy

    g = getGather(asOf)
    data: dict[str, float | list | None] = {}

    if market.upper() == "US":
        # HY 시계열 (bps 변환)
        hy_list = fetchSeriesList(g, "BAMLH0A0HYM2")
        if hy_list:
            data["hy_series"] = [v * 100 for v in hy_list]
            data["hy_current"] = hy_list[-1] * 100

        # S&P500 3년 수익률
        sp_list = fetchSeriesList(g, "SP500")
        if sp_list and len(sp_list) > 750:
            if sp_list[-750] > 0:
                data["sp500_3y_return"] = ((sp_list[-1] / sp_list[-750]) - 1) * 100

        data["vix"] = fetchLatest(g, "VIXCLS")

        # 달러인덱스
        dxy_list = fetchSeriesList(g, "DTWEXBGS")
        if dxy_list and len(dxy_list) > 60:
            data["dxy_current"] = dxy_list[-1]
            data["dxy_3m_ago"] = dxy_list[-60]

        # Credit-to-GDP
        credit_list = fetchSeriesList(g, "TCMDO")
        gdp_list = fetchSeriesList(g, "GDP")
        if credit_list and gdp_list:
            min_len = min(len(credit_list), len(gdp_list))
            ratios = [credit_list[i] / gdp_list[i] * 100 for i in range(min_len) if gdp_list[i] > 0]
            if ratios:
                data["credit_gdp_series"] = ratios

    elif market.upper() == "KR":
        credit_list = fetchSeriesList(g, "CREDIT_TOTAL")
        gdp_list = fetchSeriesList(g, "GDP")
        if credit_list and gdp_list:
            min_len = min(len(credit_list), len(gdp_list))
            ratios = [credit_list[i] / gdp_list[i] * 100 for i in range(min_len) if gdp_list[i] > 0]
            if ratios:
                data["credit_gdp_series"] = ratios

        data["cpi_yoy"] = fetchYoy(g, "CPI")
        data["apt_yoy"] = fetchYoy(g, "APT_PRICE")

    # Koo BSR (US)
    if market.upper() == "US":
        for label, sid in [
            ("private_saving", "W987RC1Q027SBEA"),
            ("private_investment", "GPDI"),
            ("gdp_level", "GDP"),
            ("fed_funds", "FEDFUNDS"),
            ("dsr", "TDSP"),
            ("npl", "DRSFRMACBS"),
        ]:
            data[label] = fetchLatest(g, sid)
        data["us_cpi_yoy"] = fetchYoy(g, "CPIAUCSL")

        # Dalio 부채사이클 기반지표 (Big Debt Crises Part 1)
        # 공공부채/GDP, 실질GDP 성장률, 10Y TIPS (실질금리)
        data["public_debt_to_gdp"] = fetchLatest(g, "GFDEGDQ188S")
        data["gdp_growth"] = fetchLatest(g, "A191RL1Q225SBEA")
        data["real_rate"] = fetchLatest(g, "DFII10")

        # 부채서비스율 YoY 변화 — TDSP 시계열에서 4분기 diff
        tdsp_list = fetchSeriesList(g, "TDSP")
        if tdsp_list and len(tdsp_list) >= 5:
            data["debt_service_yoy"] = tdsp_list[-1] - tdsp_list[-5]

        # 총부채/GDP (TCMDO / GDP) — credit_gdp_series 의 최신값 재사용
        if data.get("credit_gdp_series"):
            data["total_debt_to_gdp"] = data["credit_gdp_series"][-1]

    return {k: v for k, v in data.items() if v is not None}


def analyzeCrisis(*, market: str = "US", asOf: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """위기 감지 종합 분석 — Credit Gap + GHS + Minsky + 침체 대시보드.

    Capabilities:
        매크로 위기 신호 4 종 통합 — Credit-to-GDP Gap (BIS 기준), GHS 위기 점수
        (신용+자산 가격 동시 급등), Minsky 위기 단계 (대형 자산 거품 4 phase),
        침체 대시보드 (probit + LEI + ISM + 신용갭 + HY 스프레드 종합). 추가로
        설비투자 압력, 부채-deflation 신호.

    Args:
        market: 시장 코드. ``"US"`` (기본) 또는 ``"KR"``.
        asOf: 기준일 ``YYYY-MM-DD``. ``None`` 이면 최신.
        overrides: AI 가정 교체. 키: ``vix``/``hySpread``/``unrate`` 등.
        **kwargs: ``probitProb``/``leiSignal``/``ismLevel``/``realRate`` —
            summary 호출 시 자동 전달.

    Returns
    -------
    dict
        market : str — 시장 코드
        creditGap : dict | None — Credit-to-GDP Gap 분석
            gap : float — 갭 (%p)
            trend : float — 추세선 (%)
            actual : float — 실제 비율 (%)
            zone : str — 위험 구간 ("normal" | "warning" | "danger")
            zoneLabel : str — 위험 구간 한글 레이블
            ccybBuffer : float — 경기대응 완충자본 (%)
            description : str — 해설
        ghsScore : dict | None — GHS 위기예측 점수
            score : float — 위기 점수 (점, 0~1)
            zone : str — 위험 구간
            zoneLabel : str — 위험 구간 한글 레이블
            components : dict — 구성요소별 기여
            crisisProb : float — 위기 확률 (%)
            description : str — 해설
            regime : str — 레짐 코드
            regimeLabel : str — 레짐 한글 레이블
        capexPressure : dict | None — 설비투자 조정 압력
            pressure : str — 압력 코드
            pressureLabel : str — 압력 한글 레이블
            spreadLevel : float — HY 스프레드 수준 (bps)
            spreadChange : float — HY 스프레드 변화 (bps)
            description : str — 해설
        dollarSafeHaven : dict | None — 달러 안전자산 효과
            status : str — 상태 ("active" | "mild" | "inactive")
            statusLabel : str — 한글 레이블
            vix : float — VIX (pt)
            dxyChange3m : float — 달러인덱스 3개월 변화율 (%)
            description : str — 해설
        historicalContext : dict | None — 역사적 맥락 (US 전용)
        recessionDashboard : dict — 침체 대시보드
            composite : float — 종합 점수 (점, 0~1)
            zone : str — 위험 구간
            zoneLabel : str — 한글 레이블
            components : dict — 구성 지표
            historicalMatch : str | None — 역사적 유사 사례
            historicalFacts : dict | None — 역사적 맥락
            description : str — 해설
        minskyPhase : dict | None — Minsky 5단계 분류
            phase : int — 단계 (1~5)
            phaseLabel : str — 단계 한글명
            confidence : float — 신뢰도 (0~1)
            signals : list[str] — 근거 시그널
            description : str — 해설
        debtCyclePhase : dict | None — Dalio 부채사이클 단계 (US 전용)
        policyLeverStatus : dict | None — Dalio 정책 4 레버 소진도 (US 전용)
        dalioCaseMatch : list[dict] | None — Dalio Part 2 상세 사례 매칭
        dalio48Match : list[dict] | None — Dalio Part 3 48 사례 매칭
        crisisType : dict | None — R&R 위기 유형 분류
        rrMatch : list[dict] | None — R&R 역사적 매칭
        kooRecession : dict | None — Koo 재무상태표 불황 (US 전용)
        fisherDeflation : dict | None — Fisher 부채디플레이션 (US 전용)
        krHousingStress : dict | None — 한국 부동산-금융 스트레스 (KR 전용)
        krCreditRisk : dict | None — 한국 신용위험 ↔ CPI (KR 전용)
        excessBondPremium : dict | None — 초과채권프리미엄 (Gilchrist-Zakrajsek)
        creditCycle : dict | None — Verdad 신용사이클 4단계
        timeseries : dict — 주요 시계열 (hy_spread, vix, dxy)

    Example:
        >>> from dartlab.macro.crisis.crisis import analyzeCrisis
        >>> r = analyzeCrisis(market="US")
        >>> r["creditGap"]["zone"], r["minskyPhase"]["phaseLabel"]
        ('normal', '확장 (확실)')

    Guide:
        4 위기 모델 (BIS Credit Gap, GHS, Minsky, R&R) 을 동시 매칭. 단일 신호
        의존 금지 — composite + 다중 매칭으로 판정. KR 은 부동산 + 신용 사이클
        특화 모델 (krHousingStress, krCreditRisk) 추가.

    SeeAlso:
        - ``analyzeCycle``: 사이클 4 국면 (사이클·위기 동시 활용)
        - ``analyzeForecast``: 침체확률 (probit) — recessionDashboard 입력
        - ``creditToGDPGap``/``ghsCrisisScore``/``minskyPhase``: 개별 detector
        - ``synth.dalio48Match`` / ``synth.dalioCaseMatch``: 역사적 매칭 SSOT

    When:
        ``macro("crisis")`` 단일 진입점. AI 가 위기 종합 답변 (지금이 2008 같은가? 등) 시.

    How:
        ``_fetchCrisisData`` (FRED/ECOS) → overrides 적용 → 각 detector 호출 → 22+ 키 dict 합성
        → timeseries 첨부.

    Raises:
        없음 — 개별 detector 실패는 None 키로 폴백.

    Requires:
        FRED (US: hy_spread, vix, dxy, gdp 등) 또는 ECOS (KR). API key 불필요.

    AIContext:
        "지금 금융위기 신호 있나" · "2008 같은 거품 시작인가" · "한국 부동산
        위험" 등 위기 질문에 호출. composite 점수 + 다중 모델 합산을 보고
        zone 만 인용하지 말 것.

    LLM Specifications:
        AntiPatterns:
            - 단일 detector 결과만 인용 (creditGap 만 보고 위기 단정 등)
            - composite < 0.3 인데 alarmist 톤 — zoneLabel 우선 인용
            - KR 시장에 US 전용 키 (kooRecession/fisherDeflation/dalio*) 기대
        OutputSchema:
            상기 22+ 키 dict. market 별 일부 키 None 가능.
        Prerequisites:
            seriesFetch 의 FRED/ECOS cache (httpx) 워밍업.
        Freshness:
            FRED 일/주, ECOS 월 (계열별).
        Dataflow:
            _fetchCrisisData (FRED/ECOS) → overrides 적용 → 각 detector
            (creditToGDPGap, ghsCrisisScore, minskyPhase, recessionDashboard
            등) → dict 합치기.
        TargetMarkets: US (FRED), KR (ECOS + KR 특화 모델).
    """
    data = _fetchCrisisData(market, asOf=asOf)
    if overrides:
        from dartlab.macro.seriesFetch import applyOverrides

        data = applyOverrides(data, overrides)
    result: dict = {"market": market.upper()}

    result["creditGap"], creditGapVal = _crisisCreditGap(data)
    result["ghsScore"] = _crisisGhsScore(data, creditGapVal, kwargs.get("realRate"))
    result["capexPressure"] = _crisisCapexPressure(data)
    result["dollarSafeHaven"] = _crisisDollarSafeHaven(data)

    hyCurrent = data.get("hy_current")
    vix = data.get("vix")
    dxyCurrent = data.get("dxy_current")

    result["historicalContext"] = _crisisHistoricalContext(market, asOf)

    # 침체 대시보드 (다른 축 결과 필요 — 독립 실행 시 가용 데이터만 사용)
    probit_prob = kwargs.get("probitProb")
    lei_signal = kwargs.get("leiSignal")
    ism_level = kwargs.get("ismLevel")

    dashboard = recessionDashboard(
        probitProb=probit_prob,
        leiSignal=lei_signal,
        ismLevel=ism_level,
        creditGap=creditGapVal,
        hySpread=hyCurrent,
    )
    result["recessionDashboard"] = {
        "composite": dashboard.composite,
        "zone": dashboard.zone,
        "zoneLabel": dashboard.zoneLabel,
        "components": dashboard.components,
        "historicalMatch": dashboard.historicalMatch,
        "historicalFacts": result.get("historicalContext"),
        "description": dashboard.description,
        "status": dashboard.status,
        "observedInputs": dashboard.observedInputs,
        "totalInputs": dashboard.totalInputs,
    }

    result["minskyPhase"] = _crisisMinsky(data, creditGapVal, hyCurrent, vix, dxyCurrent)
    result["dalioCaseMatch"] = _crisisDalioCaseMatch(data, creditGapVal)
    result["dalio48Match"] = _crisisDalio48Match(data, creditGapVal)
    ct_res, rr_res = _crisisRRTypes(data, hyCurrent, market, kwargs)
    result["crisisType"] = ct_res
    result["rrMatch"] = rr_res
    dp_res, pl_res = _crisisDalioDebtCycle(data, creditGapVal, kwargs)
    result["debtCyclePhase"] = dp_res
    result["policyLeverStatus"] = pl_res
    result["kooRecession"] = _crisisKooBsr(data) if market.upper() == "US" else None
    result["fisherDeflation"] = _crisisFisherDeflation(data) if market.upper() == "US" else None
    if market.upper() == "KR":
        result["krHousingStress"] = _crisisKrHousingStress(data)
        kr_credit = _crisisKrCreditRisk(data)
        if kr_credit:
            result["krCreditRisk"] = kr_credit
    result["excessBondPremium"] = _crisisExcessBondPremium(asOf)
    result["creditCycle"] = _crisisCreditCycle(asOf)

    from dartlab.macro.seriesFetch import collectTimeseries

    g_ts = getGather(asOf)
    result["timeseries"] = collectTimeseries(g_ts, {"hy_spread": "BAMLH0A0HYM2", "vix": "VIXCLS", "dxy": "DTWEXBGS"})

    return result


# ── 사이클 위치 기반 행동 추천 ──

_CYCLE_ACTIONS: dict[str, list[dict]] = {
    "recovery": [
        {
            "priority": 1,
            "action": "성장 투자 확대",
            "reason": "경기 회복기 — 수요 증가 시 시장 선점 기회",
            "urgency": "high",
        },
        {
            "priority": 2,
            "action": "레버리지 활용 검토",
            "reason": "저금리 + 경기 호전 → 차입 비용 대비 투자 수익률 우위",
            "urgency": "medium",
        },
    ],
    "expansion": [
        {
            "priority": 1,
            "action": "수익성 극대화",
            "reason": "수요 호조 → 가격 인상 여력, 판관비 효율화 적기",
            "urgency": "medium",
        },
        {
            "priority": 2,
            "action": "현금 축적 시작",
            "reason": "사이클 정점 접근 → 하강기 대비 유보금 확보",
            "urgency": "medium",
        },
    ],
    "late_expansion": [
        {
            "priority": 1,
            "action": "부채 감축 가속화",
            "reason": "금리 상승 + 경기 둔화 시 이자부담 급증",
            "urgency": "high",
        },
        {
            "priority": 2,
            "action": "현금 보유 확대",
            "reason": "경기 하강기 인수 기회 또는 방어 자금",
            "urgency": "high",
        },
        {"priority": 3, "action": "CAPEX 집행 속도 조절", "reason": "투자 수익률 하락 구간 진입", "urgency": "medium"},
    ],
    "slowdown": [
        {
            "priority": 1,
            "action": "비용 구조 긴축",
            "reason": "매출 둔화 시 고정비 부담 급등 → 선제적 구조조정",
            "urgency": "high",
        },
        {
            "priority": 2,
            "action": "운전자본 최적화",
            "reason": "재고 축소, 매출채권 회수 가속화 → 현금 방어",
            "urgency": "high",
        },
    ],
    "contraction": [
        {
            "priority": 1,
            "action": "생존 모드 — 현금 보전",
            "reason": "경기 침체 → 매출 급감, 유동성이 생존 결정",
            "urgency": "critical",
        },
        {
            "priority": 2,
            "action": "저점 인수 기회 탐색",
            "reason": "경쟁사 부실 → 저가 인수 가능, 현금 여력이 전제",
            "urgency": "medium",
        },
    ],
}


def calcCyclicalAction(*, market: str = "KR", asOf: str | None = None, overrides: dict | None = None) -> dict | None:
    """사이클 위치 기반 행동 추천. overrides로 AI 사이클 국면 조율.

    Capabilities:
        ``analyzeCrisis`` 결과의 cycle phase 또는 ``overrides["cyclePhase"]`` 를 받아 5 국면별
        2~3 개 우선순위 행동 추천 dict 반환. AI 가 시나리오 조율 시 cyclePhase 강제 가능.

    Returns
    -------
    dict | None
        cyclePhase : str
        phaseLabel : str
        actions : list[dict]
        historicalPrecedent : str | None

    Raises:
        없음 — analyzeCrisis 실패 또는 cycle 부재 시 None.

    Example:
        >>> from dartlab.macro.crisis.crisis import calcCyclicalAction
        >>> r = calcCyclicalAction(market="KR")
        >>> r["actions"][0]["action"]

    Guide:
        actions 의 urgency = critical/high/medium 우선순위. AI 답변에서 priority 1 만 인용 권장.

    When:
        AI 가 회사 / 기관 향 "지금 무엇을 해야 하나" 행동 권고 답변 시. overrides 로 시나리오 분기.

    How:
        overrides.cyclePhase 직접 매핑 OR ``analyzeCrisis`` 호출 → cycle phase → ``_CYCLE_ACTIONS``
        룩업 → dict 반환.

    Requires:
        - FRED/ECOS 캐시 (analyzeCrisis 호출)

    See Also:
        - ``dartlab.macro.crisis.crisis.analyzeCrisis`` : cycle 산출
        - ``dartlab.macro.cycles.cycle.analyzeCycle`` : 사이클 4 국면

    AIContext:
        AI 가 행동 권고 답변 시 본 함수 결과 1~2 개 priority 만 인용. 5 개 동시 권고는 노이즈.
    """
    # override: cyclePhase 직접 지정
    if overrides and overrides.get("cyclePhase"):
        phase_key = overrides["cyclePhase"]
        actions = _CYCLE_ACTIONS.get(phase_key, _CYCLE_ACTIONS["expansion"])
        return {
            "cyclePhase": phase_key,
            "phaseLabel": f"{phase_key} (AI override)",
            "actions": actions,
            "historicalPrecedent": None,
        }

    try:
        crisis = analyzeCrisis(market=market, asOf=asOf)
    except (ValueError, TypeError, KeyError):
        return None

    cycle = crisis.get("cycle", {})
    if not cycle:
        return None

    phase = cycle.get("phase", "")
    label = cycle.get("label", "")

    # phase 매핑
    phase_key = "expansion"
    if "회복" in label or "recovery" in phase.lower():
        phase_key = "recovery"
    elif "확장" in label or "expansion" in phase.lower():
        if "후반" in label or "late" in phase.lower():
            phase_key = "late_expansion"
        else:
            phase_key = "expansion"
    elif "둔화" in label or "slowdown" in phase.lower():
        phase_key = "slowdown"
    elif "침체" in label or "contraction" in phase.lower():
        phase_key = "contraction"

    actions = _CYCLE_ACTIONS.get(phase_key, _CYCLE_ACTIONS["expansion"])

    # 역사적 선례 (historicalContext 활용)
    hc = crisis.get("historicalContext", {})
    events = hc.get("historicalEvents", []) if hc else []
    precedent = None
    if events and isinstance(events[0], dict):
        e = events[0]
        precedent = f"{e.get('eventName', '')} ({e.get('eventDate', '')}) — {e.get('outcome', '')}"

    return {
        "cyclePhase": phase_key,
        "phaseLabel": label or phase_key,
        "actions": actions,
        "historicalPrecedent": precedent,
    }
