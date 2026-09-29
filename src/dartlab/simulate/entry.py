"""Callable `simulate` wrapper over `Company.simulate` (L3).

`dartlab.simulate` is the callable entry for the simulator. It has two axes:

- ``scenario`` (default): ``dartlab.simulate(code, scenario=..., horizon=..., asOf=...)`` or
  ``dartlab.simulate("scenario", code, ...)`` evaluates the deterministic driver sheet for one preset.
- ``strategies``: ``dartlab.simulate("strategies", code, horizon=...)`` compares a fixed set of
  financial strategies on the company's current state across every KR preset, conditionally.

It resolves the code to a `Company`, guards the KR-only macro presets, and delegates to
`Company.simulate(axis, ...)` - mirroring how `dartlab.compare` wraps `panel.compare`.

Layer: L3. Imports forward only - constructs the root `Company` facade (L1) and calls the L3
drivers. The legacy `analysis/forecast/simulation.py` flow is never touched (born-clean).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dartlab.simulate.run import SimulationResult

SIMULATE_AXES = ("scenario", "strategies")


def resolveSimulateCall(target: str, code: str | None) -> tuple[str, str]:
    """Split a simulate call into its axis and company code.

    Args:
        target: the axis name, or the company code when ``code`` is None (the scenario shortcut).
        code: the company code when ``target`` names an axis.

    Returns:
        tuple[str, str]: ``(axis, code)``.

    Raises:
        ValueError: if an axis is named without a company, or ``target`` is not a known axis.

    Example:
        >>> resolveSimulateCall("005930", None)
        ('scenario', '005930')
        >>> resolveSimulateCall("strategies", "005930")
        ('strategies', '005930')
    """
    if code is None:
        if target in SIMULATE_AXES:
            raise ValueError(f"simulate('{target}', ...) 는 종목코드가 필요합니다. 예: simulate('{target}', '005930')")
        return "scenario", target
    if target not in SIMULATE_AXES:
        raise ValueError(f"알 수 없는 simulate 축: {target!r}; 유효값: {', '.join(SIMULATE_AXES)}")
    return target, code


def simulate(
    target: str,
    code: str | None = None,
    *,
    scenario: str | dict | None = None,
    horizon: int = 3,
    asOf: str | None = None,
    overrides: dict | None = None,
) -> SimulationResult | Any:
    """한 회사에 시나리오 하나를 결정론적으로 돌려 시나리오-조건부 경로·가치를 낸다 (시뮬레이터 엔진).

    Capabilities:
        - 매크로 프리셋(baseline/adverse/...) 하나를 골라 GDP·금리·환율 노드에서 매출·마진·WACC
          채널을 거쳐 proforma 와 dcf 까지 가는 결정론 드라이버 시트를 한 번에 평가한다. 금리는
          WACC 경로(과 금융업 마진)로, GDP 는 매출과 마진으로, 환율은 매출로 전달된다. 결과는
          시나리오-조건부 매출·마진·FCF·WACC 경로 + dcf 주당가치 + 노드별 근거(provenance/refs/
          품질 상태/asOf)를 담은 `SimulationResult`.
        - honest-gap: 결손 leaf 나 부재한 base 지표는 0 으로 채우지 않고 해당 필드를 None 으로
          두고 노드 품질을 ``partial`` 로 낮춘다.
        - 결정론: 같은 회사·시나리오·asOf 를 다시 돌리면 노드별 ``inputsHash`` 가 byte 단위 동일
          (이 경로에 난수 없음).
        - ``strategies`` 축은 회사의 현재 재무 상태에서 유지·증설·부채 축소 전략을 모든 KR
          프리셋의 같은 경로 위에서 비교해 프리셋별 리더, 리더가 뒤집히는 프리셋, 결정이 가장
          쉽게 뒤집히는 프리셋을 담은 `StrategyComparison` 을 낸다. 항상 조건부 비교이며 추천은
          없다.

    Args:
        target: 축 이름(``"scenario"``, ``"strategies"``) 또는 축을 생략할 때의 종목코드.
            축을 생략하면 ``scenario`` 축이다.
        code: ``target`` 이 축일 때의 종목코드("005930") 또는 한글 회사명("삼성전자"). 현재
            KR(DART) 전용 - 미국 ticker 는 `ValueError` (매크로 프리셋이 KR 기준이라 차단).
        scenario: ``scenario`` 축의 프리셋 id(``synth.scenario.getPresetScenarios("KR")`` 의 키, 예:
            ``"baseline"``, ``"adverse"``) 또는 사용자 시나리오 dict. 사용자 시나리오는
            ``{"name": "rateShock", "base": "baseline", "rate": [5.0, 5.5, 5.5]}`` 처럼 ``base``
            프리셋의 ``gdp``, ``rate``, ``fx`` 경로 중 준 것만 바꾼다. 생략하면 ``"baseline"``.
            ``strategies`` 축은 모든 프리셋을 비교하므로 받지 않는다.
        horizon: 예측 연수 (기본 3). 프리셋은 프리셋 경로 길이까지, 세 경로를 모두 준 사용자
            시나리오는 10년까지다.
        asOf: 명시 재무 기간(YYYY 또는 YYYY-Qn). 현재는 기간 단위 PIT이며 공시 접수일
            vintage 복원은 지원하지 않는다.
        overrides: 드라이버 override dict. ``baseWacc``, ``terminalGrowth``, ``baseMargin`` (%),
            ``revenueToGdp``, ``revenueToFx``, ``marginToGdp``, ``nimToRate`` (업종 탄성 단위) 중
            일부를 바꾼다. 적용한 값은 결과 ``assumptionLedger`` 에 ``source="user"`` 로 남는다.
            ``strategies`` 축은 아직 받지 않는다.

    Returns:
        SimulationResult: ``scenario`` 축. 시나리오 매출·마진·FCF·WACC 경로 + dcf 주당가치 +
        노드별 audit + 전체 품질 상태(``"ok"`` / ``"partial"``). 필드 상세는 `SimulationResult`.
        StrategyComparison: ``strategies`` 축. 필드 상세는 `StrategyComparison`.

    Raises:
        TypeError: scenario, horizon, overrides 타입이 잘못됐을 때.
        ValueError: KR 이 아닌 회사, 코드를 회사로 해소하지 못했거나 축/scenario/horizon/overrides/
            asOf 가 지원 범위 밖일 때. 사용자 가정 오류는 ``AssumptionInputError`` 다.

    Example:
        >>> import dartlab
        >>> r = dartlab.simulate("005930", scenario="baseline")  # doctest: +SKIP
        >>> r.scenarioName, len(r.revenuePath)  # doctest: +SKIP
        ('baseline', 3)
        >>> adverse = dartlab.simulate("005930", scenario="adverse")  # doctest: +SKIP
        >>> adverse.revenuePath[-1] < r.revenuePath[-1]  # 경기침체가 매출 경로를 낮춤  # doctest: +SKIP
        True
        >>> plan = dartlab.simulate("strategies", "005930")  # doctest: +SKIP
        >>> plan.decisionStatus, plan.recommendation  # doctest: +SKIP
        ('conditionalOnly', None)
        >>> shock = dartlab.simulate("005930", scenario={"name": "rateShock", "rate": [5.0, 5.5, 5.5]})  # doctest: +SKIP
        >>> shock.scenarioKind, shock.waccPath[-1] > r.waccPath[-1]  # doctest: +SKIP
        ('user', True)
        >>> tight = dartlab.simulate("005930", overrides={"baseWacc": 11.0})  # doctest: +SKIP

    Guide:
        시나리오 비교는 같은 회사에 시나리오마다 한 번씩 호출한다 (baseline vs adverse 는 매크로
        프리셋만 다르므로 adverse 매출 경로가 더 낮은 것이 정성 신호). 결과는 audit 객체이므로
        각 노드의 provenance/refs 를 읽어 숫자를 설명한다. 회사 간 비교는 `compare`, 한 회사
        수평화 보드는 `Company.panel`.

    SeeAlso:
        - ``Company.simulate``: 같은 동작의 Company 메서드 (``c.simulate(scenario=...)``).
        - ``dartlab.simulate.run.runScenario``: 내부 end-to-end 드라이버.
        - ``dartlab.synth.scenario.getPresetScenarios``: 유효한 시나리오 id.
        - ``compare``: N 회사 시점 비교 (회사 facade 밖, 같은 톱레벨 verb 결).

    Requires:
        KR 회사 하나. proforma 노드가 ``partial`` 이 아니려면 IS/BS/CF 가 ~3 년 이상인 재무
        시계열이 필요하다.

    AIContext:
        출력은 미래 예측이 아니라 *고정된 가정의 결정론 변환*이다 - 항상 시나리오 id, 노드별
        provenance/refs, asOf 를 같이 노출한다. ``partial`` 품질은 데이터 갭(None 필드)이지 0 이
        아니다. 갭을 보고하고 0 으로 대체하지 않는다. ``lensProducts``와
        ``assumptionLedger``는 설명 맥락이며 결정론 DriverSheet를 바꾸지 않는다.

    LLM Specifications:
        AntiPatterns:
            - ``dcfPerShare`` 를 목표주가로 인용 - 시나리오-조건부 변환이다.
            - None ``revenuePath`` 를 0 으로 취급 - 정직한 base 매출 갭이다.
            - asOf 를 바꿔 다시 돌린 뒤 inputsHash 비교 - 기준시점도 해시의 일부.
            - lensProducts의 가정을 DriverSheet에 적용된 override로 해석.
        OutputSchema: ``SimulationResult`` (해당 필드 docstring 참조).
        Prerequisites: 재무 시계열을 가진 KR `Company`.
        Freshness: 회사의 최신 재무 기간을 asOf/latestAsOf 로 상속.
        Dataflow: code -> Company -> runScenario(snapshot -> sheet -> evaluateSheet) ->
            SimulationResult.
        TargetMarkets: KR (getPresetScenarios("KR") + KR elasticity). US 는 US 프리셋 합류 후.
    """
    import dartlab

    axis, code = resolveSimulateCall(target, code)
    company = getattr(dartlab, "Company")(code)
    # KR 전용 가드 - 매크로 프리셋이 KR 기준이라 비-KR(US → EDGAR)은 차단한다. DART/EDGAR Company
    # 둘 다 .stockCode 를 노출하므로(EDGAR 는 ticker 를 stockCode 로 미러) market 을 식별자로 쓴다.
    market = getattr(company, "market", None)
    if market != "KR":
        raise ValueError(
            f"simulate 는 현재 KR(DART) 전용입니다 - '{code}' (market={market!r}) 은(는) 지원하지 "
            "않습니다. US 매크로 프리셋 합류 전까지 차단."
        )
    return company.simulate(axis, scenario=scenario, horizon=horizon, asOf=asOf, overrides=overrides)
