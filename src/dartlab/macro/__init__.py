"""시장 레벨 매크로 분석 엔진 - 6막 인과 서사.

dartlab의 핵심 사상 4가지 비교 가능성 중 "시장 내/시장 간 비교"를 담당.
gather(L1)이 수집한 원시 데이터 위에 6막 인과 해석을 제공한다.

6막 구조 - "앞 막이 뒷 막의 원인"::

    1막: "경제는 어디에 있나"     (국면 진단)     cycle, inventory
     ↓
    2막: "왜 여기에 있나"         (실물 인과)     corporate, trade
     ↓
    3막: "정책은 뭘 하고 있나"    (중앙은행)      rates
     ↓
    4막: "금융 시스템은 괜찮나"   (신용/유동성)   liquidity, crisis
     ↓
    5막: "시장은 어떻게 반응하나"  (자산/심리)     assets, sentiment
     ↓
    6막: "앞으로 어떻게 되나"     (전망/시나리오)  forecast, scenario

사용법::

    import dartlab

    dartlab.macro()                                    # 가이드 (6막 구조)
    dartlab.macro("사이클")                             # 1막: 국면 진단
    dartlab.macro("기업집계")                           # 2막: 실물 인과
    dartlab.macro("금리")                               # 3막: 정책 대응
    dartlab.macro("위기")                               # 4막: 금융 건전성
    dartlab.macro("심리")                               # 5막: 시장 반응
    dartlab.macro("시나리오", "2008 금융위기")           # 6막: 시나리오
    dartlab.macro("종합")                               # 전체 종합 판정

학술 근거:
    - FOMC 성명서 구조 (고용/물가 → 정책 → 포워드 가이던스)
    - ECB 전파 메커니즘 (정책금리 → 금융상태 → 실물 → 물가)
    - Bernanke & Gertler (1995) - 신용 채널, 금융가속기
    - Ray Dalio - 단기/장기 부채 사이클
    - Goldman Sachs/IMF 매크로 보고서 구조
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any

import polars as pl

# ── 6막 정의 ────────────────────────────────────────

_ACT_LABELS: dict[int, str] = {
    1: "경제는 어디에 있나",
    2: "왜 여기에 있나",
    3: "정책은 뭘 하고 있나",
    4: "금융 시스템은 괜찮나",
    5: "시장은 어떻게 반응하나",
    6: "앞으로 어떻게 되나",
    0: "종합",
}

# Public surface - Macro callable + sub-axis 진입.
__all__ = ["Macro"]

# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """macro 축 메타데이터.

    Attributes
    ----------
    module : str
        축 구현 모듈의 정규화된 import 경로 (예: ``"dartlab.macro.cycles.cycle"``).
    fn : str
        모듈 내 진입 함수 이름 (예: ``"analyze_cycle"``).
    label : str
        사용자 노출용 한글 축 이름 (예: ``"사이클"``).
    description : str
        축이 수행하는 분석에 대한 한 줄 설명.
    example : str
        호출 예시 코드 문자열 (예: ``'macro("사이클")'``).
    act : int
        6막 인과 서사에서의 위치. 1~6=해당 막, 0=종합.
    """

    module: str
    fn: str
    label: str
    description: str
    example: str
    act: int


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    # ── 1막: 경제는 어디에 있나 (국면 진단) ──
    "cycle": _AxisEntry(
        module="dartlab.macro.cycles.cycle",
        fn="analyzeCycle",
        label="사이클",
        description="경제 사이클 4국면 식별 + 전환 시퀀스 감지",
        example='macro("사이클")',
        act=1,
    ),
    "inventory": _AxisEntry(
        module="dartlab.macro.cycles.inventory",
        fn="analyzeInventory",
        label="재고",
        description="ISM 재고순환 4국면 + 자산배분 바로미터",
        example='macro("재고")',
        act=1,
    ),
    # ── 2막: 왜 여기에 있나 (실물 인과) ──
    "corporate": _AxisEntry(
        module="dartlab.macro.corporate.corporate",
        fn="analyzeCorporate",
        label="기업집계",
        description="전종목 이익사이클 + Ponzi비율 + 레버리지",
        example='macro("산업집계")',
        act=2,
    ),
    "trade": _AxisEntry(
        module="dartlab.macro.trade.trade",
        fn="analyzeTrade",
        label="교역",
        description="교역조건 + 수출이익 선행 + 양국 선행지수",
        example='macro("교역", market="KR")',
        act=2,
    ),
    "transmission": _AxisEntry(
        module="dartlab.macro.transmission.transmission",
        fn="analyzeTransmission",
        label="전파",
        description="driver → sector → financial line → valuation lever 전파 edge와 source lineage",
        example='macro("전파", market="KR", sectorKey="semiconductor")',
        act=2,
    ),
    # ── 3막: 정부는 뭘 하고 있나 (중앙은행 대응) ──
    "rates": _AxisEntry(
        module="dartlab.macro.rates.rates",
        fn="analyzeRates",
        label="금리",
        description="금리 방향 + 고용/물가 + 수익률곡선 + 기간프리미엄",
        example='macro("금리")',
        act=3,
    ),
    # ── 4막: 금융 시스템은 괜찮나 (신용/유동성) ──
    "liquidity": _AxisEntry(
        module="dartlab.macro.cycles.liquidity",
        fn="calcLiquidity",
        label="유동성",
        description="M2 + 연준 B/S + NFCI + 자체 FCI",
        example='macro("유동성")',
        act=4,
    ),
    "crisis": _AxisEntry(
        module="dartlab.macro.crisis.crisis",
        fn="analyzeCrisis",
        label="위기",
        description="Credit-to-GDP gap + GHS + Minsky + 역사적 맥락",
        example='macro("위기")',
        act=4,
    ),
    # ── 5막: 시장은 어떻게 반응하나 (자산/심리) ──
    "assets": _AxisEntry(
        module="dartlab.macro.corporate.assets",
        fn="analyzeAssets",
        label="자산",
        description="5대 자산 심층 해석 + Cu/Au + BEI 4분면",
        example='macro("자산")',
        act=5,
    ),
    "sentiment": _AxisEntry(
        module="dartlab.macro.cycles.sentiment",
        fn="calcSentiment",
        label="심리",
        description="공포탐욕 근사 + VIX 구간 + JLN 실물 불확실성",
        example='macro("심리")',
        act=5,
    ),
    "narrative": _AxisEntry(
        module="dartlab.macro.narrative.narrative",
        fn="analyzeNarrative",
        label="내러티브",
        description="news headline 30 일 sentiment + topic pulse + regime shift (Phase A/B archive 입력)",
        example='macro("내러티브")',
        act=5,
    ),
    # ── 6막: 앞으로 어떻게 되나 (전망 + 시나리오) ──
    "forecast": _AxisEntry(
        module="dartlab.macro.forecast.forecast",
        fn="analyzeForecast",
        label="예측",
        description="LEI + Cleveland Fed 침체확률 + Sahm + Hamilton RS + GaR",
        example='macro("예측")',
        act=6,
    ),
    "scenario": _AxisEntry(
        module="dartlab.macro.scenarios",
        fn="analyzeScenario",
        label="시나리오",
        description="역사적 충격 재현 + 유형별 스트레스 (~146개 프리셋)",
        example='macro("시나리오", "2008 금융위기")',
        act=6,
    ),
    "simulate": _AxisEntry(
        module="dartlab.macro.simulate.simulate",
        fn="analyzeSimulation",
        label="전망시뮬",
        description="BVAR 변수 팬(분위 경로) + 충격반응 IRF + 국면 forward - 미래 확률 시뮬",
        example='macro("시뮬레이션", market="US")',
        act=6,
    ),
    # ── 종합 ──
    "summary": _AxisEntry(
        module="dartlab.macro.summary",
        fn="analyzeSummary",
        label="종합",
        description="6막 전체 종합 - 점수 + 자산배분 + 40개 투자전략",
        example='macro("종합")',
        act=0,
    ),
}

_ALIASES: dict[str, str] = {
    # 한글 → 영문
    "사이클": "cycle",
    "경제사이클": "cycle",
    "경기": "cycle",
    "금리": "rates",
    "금리전망": "rates",
    "자산": "assets",
    "자산신호": "assets",
    "심리": "sentiment",
    "시장심리": "sentiment",
    "공포탐욕": "sentiment",
    "내러티브": "narrative",
    "뉴스내러티브": "narrative",
    "뉴스심리": "narrative",
    "헤드라인": "narrative",
    "유동성": "liquidity",
    "유동성환경": "liquidity",
    "예측": "forecast",
    "GDP": "forecast",
    "경제전망": "forecast",
    "nowcast": "forecast",
    "시뮬레이션": "simulate",
    "전망시뮬": "simulate",
    "시뮬": "simulate",
    "팬차트": "simulate",
    "bvar": "simulate",
    "위기": "crisis",
    "위기감지": "crisis",
    "금융안정": "crisis",
    "재고": "inventory",
    "재고순환": "inventory",
    "ISM": "inventory",
    "기업집계": "corporate",
    "기업": "corporate",
    "바텀업": "corporate",
    "교역": "trade",
    "교역조건": "trade",
    "수출": "trade",
    "전파": "transmission",
    "매크로전파": "transmission",
    "트랜스미션": "transmission",
    "종합": "summary",
    "매크로종합": "summary",
    "시나리오": "scenario",
    "스트레스": "scenario",
    "스트레스테스트": "scenario",
}


def _resolve(axis: str) -> str:
    """한글/영문 alias → 정규 축 이름으로 변환.

    Parameters
    ----------
    axis : str
        축 이름. 정규 영문(``"cycle"``), 한글(``"사이클"``), 별칭(``"경기"``) 모두 허용.

    Returns
    -------
    str
        ``_AXIS_REGISTRY`` 의 정규 키 (예: ``"cycle"``, ``"rates"``).

    Raises
    ------
    KeyError
        매칭되는 축이 없을 때. 사용 가능한 축 목록을 메시지에 포함.
    """
    lower = axis.strip().lower()
    if lower in _AXIS_REGISTRY:
        return lower
    if axis in _ALIASES:
        return _ALIASES[axis]
    if lower in _ALIASES:
        return _ALIASES[lower]
    # fuzzy hint
    available = list(_AXIS_REGISTRY.keys()) + list(_ALIASES.keys())
    hint = ", ".join(sorted(set(available)))
    msg = f"'{axis}' 축을 찾을 수 없습니다. 사용 가능: {hint}"
    # market 코드 오용 가드 - 'KR'/'US' 류 ISO 시장 코드를 axis 자리에 넣은 경우
    # 친절한 호출 예 동봉. LLM agent 가 KeyError 메시지 안 hint 로 자가 교정.
    if axis.strip().upper() in {"KR", "US", "JP", "JPN", "EU", "CN", "UK", "DE", "FR"}:
        msg += (
            f". 힌트: '{axis}' 는 market 코드입니다. 첫 인자는 axis 이름 "
            f"(예: 'cycle'/'사이클'/'rates'/'금리'), 시장은 market='{axis.strip().upper()}' "
            f"keyword 로 넘기세요 - dartlab.macro('사이클', market='{axis.strip().upper()}')"
        )
    raise KeyError(msg)


# ── Macro 클래스 ────────────────────────────────────────


def _bindCompanyTransmissionContext(target: dict[str, Any], company: Any) -> None:
    """전파 축에만 Company 교차 렌즈 문맥을 지연 결합한다."""
    from dartlab.synth.macroCompanyContext import buildMacroCompanyContext

    context = buildMacroCompanyContext(company)
    target.setdefault("stockCode", str(getattr(company, "stockCode", "") or "unknown"))
    if context.get("sectorKey"):
        target.setdefault("sectorKey", context["sectorKey"])
    target.setdefault("companyEvidence", context["companyEvidence"])
    target.setdefault("contextGaps", context["contextGaps"])


class Macro:
    """시장 레벨 매크로 분석 - 6 막 인과 서사 엔진.

    Capabilities:
        FRED · ECOS 등 공개 매크로 데이터를 가져와 사이클 4 국면 (침체/회복/
        확장/둔화) · 위기 신호 (8 종 경고등) · 금리 전망 · 유동성 레짐 · 시장
        심리 · 시나리오 매칭 (역사적 재현) · 종합 투자 전략을 산출. ``Macro()``
        무인자 호출은 가이드 DataFrame, axis 지정은 dict 반환.

    Args:
        없음 (callable). 실제 인자는 ``__call__`` 시그니처:
        ``axis``/``target``/``market``/``overrides``/``**kwargs``.

    Returns:
        ``Macro`` 인스턴스. 호출 가능 객체.

    Example:
        >>> from dartlab import macro
        >>> macro()                            # 가이드 DataFrame
        >>> macro("사이클")                     # 경기 4 국면
        >>> macro("금리")                       # 금리 + 수익률곡선
        >>> macro("종합")                       # 매크로 종합 + 투자 전략
        >>> macro("시나리오", "2008 금융위기")    # 역사적 시나리오

    Guide:
        매크로 엔진은 6 막 인과의 최상위 - 사이클 → 업종 (scan) → 기업
        (analysis) 순서로 분석 흐름이 흘러간다. 종목 분석 전 매크로 환경부터
        파악할 때 사용. KR/US 시장 모두 지원, market 명시 필수.

    SeeAlso:
        - ``Quant``: 시장 심리·변동성 - macro 사이클과 교차 분석
        - ``analysis``: 개별 기업 재무 - macro 환경 하 기업 건전성
        - ``scan``: 전종목 횡단 - macro 사이클별 업종 영향 비교
        - ``synth.scenario``: 시나리오 카탈로그 SSOT

    Requires:
        FRED API (US, 공개), ECOS API (KR, 공개). API key 불필요.

    AIContext:
        "지금 경기 어떄?" · "금리 방향성 어디로 가나" · "2008 같은 위기 올
        수 있나" · "시장 심리 과열인가" 등 매크로 환경 질문에 매칭. AI 는
        axis 를 한국어 키 (사이클/위기/시나리오/유동성/심리/금리/종합) 로
        전달. company 분석 전 매크로 컨텍스트 확립용으로 우선 호출.

    LLM Specifications:
        AntiPatterns:
            - axis 영문 추측 (cycle/crisis) - 한국어 키만 매핑
            - market 미지정 시 default "US" - KR 의도면 명시 필수
            - overrides 키 임의 추가 - 유효 키 4 종 (cyclePhase/rateScenario/
              fxScenario/liquidityScenario) 외 ValueError
        OutputSchema:
            - axis=None: ``pl.DataFrame(columns=[axis, label, description, example, group])``
            - axis="사이클": ``{phase, label, confidence, indicators}``
            - axis="시나리오": ``{historical analogue, projection}``
            - axis="종합": ``{indicators, narrative, investmentStrategy}``
        Prerequisites:
            FRED 데이터 캐시 (httpx) + ECOS public endpoint (kr).
        Freshness:
            FRED 일/월/분기, ECOS 월/분기 (시리즈별).
        Dataflow:
            axis → _resolve(한글→key) → _AXIS_REGISTRY 룩업 → import_module →
            축 함수 호출 (market + overrides) → autoEnrich → dict.
        TargetMarkets:
            - US (FRED)
            - KR (ECOS)
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        *,
        market: str = "US",
        overrides: dict | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict:
        """매크로 분석 실행.

        Parameters
        ----------
        axis : str | None
            분석 축. ``None`` 이면 가이드 DataFrame 반환.
        target : str | None
            2번째 positional 인자 (시나리오 이름 등).
            ``macro("시나리오", "2008 금융위기")`` 형태.
        market : str
            ``"US"`` | ``"KR"``.
        overrides : dict | None
            AI/사용자가 매크로 시나리오 강제. 키: cyclePhase/rateScenario/
            fxScenario/liquidityScenario. 상세: ``core/overrides.py``.
        **kwargs
            축별 추가 파라미터.

        Returns
        -------
        pl.DataFrame | dict
            axis=None (가이드): DataFrame (axis/label/description/example/group 컬럼)
            axis 지정: dict - 축별 분석 결과.
                cycle: {phase, label, confidence, indicators[{name, value, signal}]}
                summary: {indicators[], narrative}
                rates/liquidity/trade/...: {지표별 dict, narrative}
            _summary (autoEnrich 자동) - 핵심 요약 + [엔진가정].

        Raises
        ------
        ValueError
            market 이 "US"/"KR" 이 아닌 경우.
            축 이름이 등록되지 않은 경우.

        Examples
        --------
        >>> dartlab.macro()                          # 가이드
        >>> dartlab.macro("사이클")                   # 경기 4국면 판별
        >>> dartlab.macro("금리")                     # 금리 + 수익률곡선
        >>> dartlab.macro("예측")                     # 침체확률 + GDP Nowcast
        >>> dartlab.macro("종합")                     # 매크로 종합 + 투자전략
        >>> dartlab.macro("시나리오", "2008 금융위기")  # 역사적 시나리오

        Notes
        -----
        FRED 데이터 기반. API 키 불필요 (공개 API).
        Hamilton EM, Kalman DFM, Nelson-Siegel, Cleveland Fed 프로빗 등 numpy 직접 구현.

        Guide
        -----
        AI 역할: AI는 macro를 시장 환경과 기업/섹터 해석을 연결하는 엔진으로 보고 asOf, 지표, 방향성 근거를 고정한다.
        When: 종목 분석 전 경제 환경을 먼저 파악할 때. Company 없이 사용 가능.
        How: 6막 인과의 최상위 - macro(사이클) → scan(업종) → analysis(기업) 순서.
            story macro/crisis 타입이 macro 종합 → analysis(안정성, 현금흐름) 순서로 조합.
        Verified:
            - macro("사이클") → CLI + 사분면 + 금리 + 유동성 + 심리 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
            - macro + analysis 조합 → 경제 고려한 논제 검증 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        See Also
        --------
        scan : 전종목 횡단 - macro 사이클에 따른 업종별 영향 비교.
        quant : 시장 심리·변동성 - macro 사이클과 교차 분석.
        analysis : 개별 기업 재무 - macro 환경 하에서 기업 건전성 판단.

        LLM Specifications:
            AntiPatterns:
                - axis 추측 (한글 - 사이클 / 위기 / 시나리오 / 유동성 / 심리 / 금리 / 종합 등)
                - market 미지정 시 default "US" - KR 분석 의도면 명시 필수
                - overrides 키 추측 (cyclePhase / rateScenario / fxScenario / liquidityScenario)
            OutputSchema:
                - axis="사이클": dict - phase / label / confidence / indicators
                - axis="시나리오": dict - historical analogue + projection
                - axis="종합": dict - indicators[] + narrative + 투자전략
                - axis 미지정: 가이드 DataFrame (axis/label/description/example/group)
            Prerequisites:
                - FRED 데이터 (US) - 공개 API, API 키 불필요
                - ECOS (KR) - public API
            Freshness:
                FRED / ECOS 갱신 주기 (월 / 분기).
            Dataflow:
                axis → _resolve → _AXIS_REGISTRY 룩업 → importlib.import_module
                → 축 함수 호출 (market + overrides + kwargs) → dict 결과
                → buildAssumptions 보강 → 반환.
            TargetMarkets:
                - US (FRED)
                - KR (ECOS)
        """
        from dartlab.synth.overrides import validateOverrides

        if axis is None:
            return self._guide()

        if market not in ("US", "KR"):
            raise ValueError(
                f"market 은 'US' 또는 'KR' 만 지원합니다. 받은 값: '{market}'\n"
                f"  사용법: dartlab.macro('{axis}', market='KR') 또는 market='US'"
            )

        clean = validateOverrides(overrides, engine="macro")
        merged: dict = {**clean, **kwargs}

        key = _resolve(axis)
        company = merged.pop("company", None)
        fallbackKwargs = dict(kwargs)
        fallbackKwargs.pop("company", None)
        if key == "transmission" and company is not None:
            _bindCompanyTransmissionContext(merged, company)
            _bindCompanyTransmissionContext(fallbackKwargs, company)
        entry = _AXIS_REGISTRY[key]
        mod = importlib.import_module(entry.module)
        fn = getattr(mod, entry.fn)

        # 2번째 positional: macro("시나리오", "2008 금융위기")
        # 시그니처 기반 분기 - target positional 받지 않는 축(cycle/rates/...)에는 drop
        sig = inspect.signature(fn)
        targetParameters = [
            p
            for p in sig.parameters.values()
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            and p.name != "market"
        ]
        effective_target = target if (target is not None and targetParameters) else None
        try:
            if effective_target is not None:
                result = fn(effective_target, market=market, **merged)
            else:
                result = fn(market=market, **merged)
        except TypeError:
            # 축 함수가 override 키 수용 전 - 키 제거 후 재시도
            if effective_target is not None:
                result = fn(effective_target, market=market, **fallbackKwargs)
            else:
                result = fn(market=market, **fallbackKwargs)

        # assumptions 투명화 - 4 엔진 공통 utility (phase → cyclePhase alias 자동)
        if isinstance(result, dict):
            from dartlab.synth.overrides import buildAssumptions

            assumptions = buildAssumptions(result, engine="macro", overrides=clean)
            if assumptions:
                result["assumptions"] = assumptions
        return result

    def _guide(self) -> pl.DataFrame:
        """6막 기반 축 가이드.

        Returns
        -------
        pl.DataFrame
            축별 메타데이터 테이블. 컬럼:

            - axis : str - 정규 축 키 (예: ``"cycle"``, ``"rates"``).
            - label : str - 한글 축 이름 (예: ``"사이클"``, ``"금리"``).
            - description : str - 축이 수행하는 분석 한 줄 설명.
            - example : str - 호출 예시 코드 문자열.
            - group : str - 6막 내 위치 (예: ``"제1막: 경제는 어디에 있나"``).
            - apiKey : str - 필요한 API 키 안내.
        """
        from dartlab.synth.axisGuide import buildAxisGuideDataFrame

        def _group(_key: str, entry) -> str:
            act_label = _ACT_LABELS.get(entry.act, "")
            act_str = f"제{entry.act}막" if entry.act > 0 else "종합"
            return f"{act_str}: {act_label}"

        return buildAxisGuideDataFrame(
            _AXIS_REGISTRY,
            groupExtractor=_group,
            apiKey="불필요 (기본 HF SSOT, 직접 API 선택 시 ECOS/FRED apiKey)",
        )

    def __repr__(self) -> str:
        n = len(_AXIS_REGISTRY)
        lines = [f"Macro - 6막 인과 서사, {n}축 시장 레벨 매크로 분석"]
        lines.append("")

        lines.append("━━━ 6막 구조 ━━━")
        # 막별 축 매핑
        for act_num in sorted(_ACT_LABELS.keys()):
            if act_num == 0:
                continue
            act_label = _ACT_LABELS[act_num]
            act_axes = [e.label for e in _AXIS_REGISTRY.values() if e.act == act_num]
            if act_axes:
                axes_str = ", ".join(act_axes)
                lines.append(f"  {act_num}막: {act_label:<16s} {axes_str}")

        lines.append("")
        lines.append("━━━ 빠른 시작 ━━━")
        lines.append("  dartlab.macro()                              # 이 가이드")
        lines.append('  dartlab.macro("사이클")                       # 1막: 국면 진단')
        lines.append('  dartlab.macro("금리")                         # 3막: 정책 대응')
        lines.append('  dartlab.macro("종합")                         # 전체 종합 판정')
        lines.append('  dartlab.macro("시나리오", "2008 금융위기")     # 6막: 시나리오')
        lines.append("")
        lines.append("━━━ API 키 ━━━")
        lines.append("  기본: 불필요 (HF 벌크 데이터셋)")
        lines.append("  직접 API: gather('macro', ..., apiKey=...) 로 ECOS/FRED 키 명시")
        lines.append("")
        lines.append(
            "노트북: https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/06_macro.py"
        )
        return "\n".join(lines)

    # accessor 패턴: macro.cycle, macro.rates ...
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            key = _resolve(name)
        except KeyError:
            raise AttributeError(f"Macro has no axis '{name}'") from None

        def _run(*args: Any, market: str = "US", **kwargs: Any) -> dict:
            entry = _AXIS_REGISTRY[key]
            mod = importlib.import_module(entry.module)
            fn = getattr(mod, entry.fn)
            if args:
                return fn(args[0], market=market, **kwargs)
            return fn(market=market, **kwargs)

        return _run
