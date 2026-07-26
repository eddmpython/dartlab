"""Callable `simulate` wrapper over `Company.simulate` (L2.5).

`dartlab.simulate(code, scenario=..., horizon=..., asOf=...)` is the callable entry for
the deterministic scenario-simulator core. It resolves the code to a `Company`, guards the
KR-only macro presets, and delegates to the internal `simulate.run.runScenario` driver - mirroring
how `dartlab.compare` wraps `panel.compare` (top-level verb, outside the Company facade).

This is the deterministic subset only (`scenario` + `horizon` + `asOf`). The full
`mainPlan/scenario-simulator/01` signature also carries `drivers` / `lens` / `mode`. The current
Company surface attaches representative lens products as explicit context while keeping the
DriverSheet deterministic. Multi-driver overrides and Play replay remain separate work.

Layer: L2.5. Imports forward only - constructs the root `Company` facade (L1) and calls the L2.5
`run` driver. The legacy `analysis/forecast/simulation.py` flow is never touched (born-clean).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dartlab.simulate.run import SimulationResult


def simulate(
    code: str,
    *,
    scenario: str = "baseline",
    horizon: int = 3,
    asOf: str | None = None,
) -> SimulationResult:
    """한 회사에 시나리오 하나를 결정론적으로 돌려 시나리오-조건부 경로·가치를 낸다 (시뮬레이터 엔진).

    Capabilities:
        - 매크로 프리셋(baseline/adverse/...) 하나를 골라 ``macro.path -> rev.path -> proforma ->
          dcf`` 결정론 드라이버 시트를 한 번에 평가한다. 결과는 시나리오-조건부 매출·마진·FCF
          경로 + dcf 주당가치 + 노드별 근거(provenance/refs/품질 상태/asOf)를 담은
          `SimulationResult`.
        - honest-gap: 결손 leaf 나 부재한 base 지표는 0 으로 채우지 않고 해당 필드를 None 으로
          두고 노드 품질을 ``partial`` 로 낮춘다.
        - 결정론: 같은 회사·시나리오·asOf 를 다시 돌리면 노드별 ``inputsHash`` 가 byte 단위 동일
          (이 경로에 난수 없음).

    Args:
        code: 종목코드("005930") 또는 한글 회사명("삼성전자"). 현재 KR(DART) 전용 - 미국 ticker
            는 `ValueError` (매크로 프리셋이 KR 기준이라 US 프리셋 합류 전까지 차단).
        scenario: 시나리오 id - ``synth.scenario.getPresetScenarios("KR")`` 의 키
            (예: ``"baseline"``, ``"adverse"``, ``"severelyAdverse"``).
        horizon: 예측 연수 (기본 3). 선택한 프리셋의 실제 경로 길이를 넘길 수 없다.
        asOf: 명시 재무 기간(YYYY 또는 YYYY-Qn). 현재는 기간 단위 PIT이며 공시 접수일
            vintage 복원은 지원하지 않는다.

    Returns:
        SimulationResult: 시나리오 매출·마진·FCF 경로 + dcf 주당가치 + 노드별 audit + 전체 품질
        상태(``"ok"`` / ``"partial"``). 필드 상세는 `SimulationResult` docstring.

    Raises:
        TypeError: scenario 또는 horizon 타입이 잘못됐을 때.
        ValueError: KR 이 아닌 회사, 코드를 회사로 해소하지 못했거나 scenario/horizon/asOf 가
            지원 범위 밖일 때.

    Example:
        >>> import dartlab
        >>> r = dartlab.simulate("005930", scenario="baseline")  # doctest: +SKIP
        >>> r.scenarioName, len(r.revenuePath)  # doctest: +SKIP
        ('baseline', 3)
        >>> adverse = dartlab.simulate("005930", scenario="adverse")  # doctest: +SKIP
        >>> adverse.revenuePath[-1] < r.revenuePath[-1]  # 경기침체가 매출 경로를 낮춤  # doctest: +SKIP
        True

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

    company = dartlab.Company(code)
    # KR 전용 가드 - 매크로 프리셋이 KR 기준이라 비-KR(US → EDGAR)은 차단한다. DART/EDGAR Company
    # 둘 다 .stockCode 를 노출하므로(EDGAR 는 ticker 를 stockCode 로 미러) market 을 식별자로 쓴다.
    market = getattr(company, "market", None)
    if market != "KR":
        raise ValueError(
            f"simulate 는 현재 KR(DART) 전용입니다 - '{code}' (market={market!r}) 은(는) 지원하지 "
            "않습니다. US 매크로 프리셋 합류 전까지 차단."
        )
    return company.simulate(scenario=scenario, horizon=horizon, asOf=asOf)
