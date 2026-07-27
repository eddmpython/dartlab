"""어댑터 이름 하나가 어느 빌더를 어떤 인자로 부르고 결과를 어떻게 합칠지 선언한 표.

예전에는 `builder.py` 안에 47 갈래짜리 `elif adapter_name == ...` 사슬이 있었다. 갈래마다
하는 일은 사실 같았다. adapters 의 빌더 하나를 부르고, 결과 dict 의 몇 키를 view 로 옮기는
것이다. 갈리는 것은 세 가지뿐이다. 어느 빌더냐, 인자가 회사냐 종목코드냐 정규화 표냐,
결과를 통째로 합치냐 특정 키만 옮기냐.

그 셋을 자료로 적어 두면 새 카드를 붙일 때 사슬에 줄을 더 얹지 않고 표에 한 줄만 적으면
된다. 사슬은 길어질수록 옆 갈래를 복사해 붙이게 되고, 그러면 세 번째 갈래에서 빠뜨린
options 병합 같은 것이 조용히 굳는다.

키 옮기기에는 두 가지 뜻이 있고 둘은 다르다. `always` 는 결과에 없으면 기본값으로 덮어쓰고,
`present` 는 결과에 있을 때만 옮긴다. 앞은 이전 값을 지우고 뒤는 남긴다. 원래 사슬이 그렇게
갈라져 있었으므로 그대로 보존한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 결과 키를 옮기는 두 가지 방식.
ALWAYS = "always"
PRESENT = "present"


@dataclass(frozen=True, slots=True)
class AdapterPlan:
    """어댑터 한 종류의 호출 방식과 결과 병합 방식."""

    builder: str
    """`viz.display.adapters` 안 빌더 함수 이름."""

    arg: str
    """`company` · `stockCode` · `norm` 중 하나. `norm` 은 `(norm, periods)` 두 인자."""

    full: bool = False
    """참이면 결과 dict 를 view 에 통째로 합친다."""

    fields: tuple[tuple[str, str, Any], ...] = ()
    """`(키, ALWAYS|PRESENT, 기본값)` 목록. `full` 이 참이면 안 쓴다."""

    mergeOptions: bool = False
    """참이면 결과의 `options` 를 기존 options 위에 얹는다."""

    needsNorm: bool = field(default=False)
    """참이면 정규화 표와 기간 목록을 미리 만들어야 한다."""


def _series() -> tuple[tuple[str, str, Any], ...]:
    """`categories` 와 `series` 를 기본값으로 덮어쓰는 가장 흔한 모양."""
    return (("categories", ALWAYS, []), ("series", ALWAYS, []))


def _seriesIfPresent() -> tuple[tuple[str, str, Any], ...]:
    """결과에 있을 때만 옮긴다. 없으면 기존 값을 지우지 않는다."""
    return (("categories", PRESENT, None), ("series", PRESENT, None))


# 회사를 인자로 받아 결과를 통째로 합치는 어댑터들.
_FULL_FROM_COMPANY = (
    ("peerComparison", "buildPeerComparison"),
    ("distressGauge", "buildDistressGauge"),
    ("beneishGauge", "buildBeneishGauge"),
    ("lifeCyclePhase", "buildLifeCyclePhase"),
    ("distressDecomp", "buildDistressDecomp"),
    ("scenarioSensitivity", "buildScenarioSensitivity"),
    ("peerScatter", "buildPeerScatter"),
    ("narrativeBridge", "buildNarrativeBridge"),
    ("snowflakeAlert", "buildSnowflakeAlert"),
    ("scoreBadge", "buildScoreBadge"),
    ("distressEnsembleGauge", "buildDistressEnsembleGauge"),
)

# 회사를 받아 categories/series 를 있을 때만 옮기는 어댑터들.
_SERIES_IF_PRESENT_FROM_COMPANY = (
    ("penmanRoeBars", "buildPenmanRoeBars"),
    ("roicWaccGap", "buildRoicWaccGap"),
    ("segmentBreakdown", "buildSegmentBreakdown"),
    ("segmentConcentration", "buildSegmentConcentration"),
    ("dolBreakeven", "buildDolBreakeven"),
)

# 종목코드를 받아 categories/series 를 기본값으로 덮어쓰는 어댑터들.
_SERIES_FROM_STOCK_CODE = (
    ("quantEquityCurve", "buildQuantEquityCurve", False),
    ("quantAnnualReturns", "buildQuantAnnualReturns", False),
    ("quantVolatilityTerm", "buildQuantVolatilityTerm", False),
    ("quantDrawdownDistribution", "buildQuantDrawdownDistribution", False),
    ("quantForecastFan", "buildQuantForecastFan", False),
    ("quantPriceTrend", "buildQuantPriceTrend", True),
    ("quantRsiTrend", "buildQuantRsiTrend", True),
    ("quantMacdTrend", "buildQuantMacdTrend", True),
    ("quantDrawdownChart", "buildQuantDrawdownChart", True),
    ("quantRollingSharpe", "buildQuantRollingSharpe", True),
    ("quantSnowflakeRadar", "buildQuantSnowflakeRadar", True),
    ("quantMonteCarloPaths", "buildQuantMonteCarloPaths", True),
)

# 종목코드를 받아 tiles 만 꺼내는 어댑터들.
_TILES_FROM_STOCK_CODE = (
    ("quantVerdictKpi", "buildQuantVerdictKpi"),
    ("quantMomentumKpi", "buildQuantMomentumKpi"),
    ("quantVolatilityKpi", "buildQuantVolatilityKpi"),
    ("quantBetaKpi", "buildQuantBetaKpi"),
    ("quantForecastKpi", "buildQuantForecastKpi"),
)


def _buildTable() -> dict[str, AdapterPlan]:
    """선언 묶음들을 하나의 표로 편다."""
    table: dict[str, AdapterPlan] = {}
    for name, builder in _FULL_FROM_COMPANY:
        table[name] = AdapterPlan(builder=builder, arg="company", full=True)
    for name, builder in _SERIES_IF_PRESENT_FROM_COMPANY:
        table[name] = AdapterPlan(builder=builder, arg="company", fields=_seriesIfPresent())
    for name, builder, withOptions in _SERIES_FROM_STOCK_CODE:
        table[name] = AdapterPlan(builder=builder, arg="stockCode", fields=_series(), mergeOptions=withOptions)
    for name, builder in _TILES_FROM_STOCK_CODE:
        table[name] = AdapterPlan(builder=builder, arg="stockCode", fields=(("tiles", ALWAYS, []),))

    # 정규화 표를 쓰는 어댑터들.
    table["cashflowSankey"] = AdapterPlan(
        builder="buildCashflowAllocationSankey", arg="norm", full=True, needsNorm=True
    )
    table["capitalAllocationBars"] = AdapterPlan(
        builder="buildCapitalAllocationBars",
        arg="norm",
        fields=(("series", PRESENT, None),),
        needsNorm=True,
    )
    table["capitalAllocationWaterfall"] = AdapterPlan(
        builder="buildCapitalAllocationWaterfall",
        arg="norm",
        fields=_seriesIfPresent(),
        needsNorm=True,
    )
    table["duPontRadar"] = AdapterPlan(builder="buildDuPontRadar", arg="norm", fields=_series(), needsNorm=True)

    # 나머지 개별 모양들.
    table["snowflakeRadar"] = AdapterPlan(
        builder="buildSnowflakeRadar", arg="company", fields=_series(), mergeOptions=True
    )
    table["quantMonthlyHeatmap"] = AdapterPlan(
        builder="buildQuantMonthlyHeatmap",
        arg="stockCode",
        fields=(
            ("cells", ALWAYS, []),
            ("rowOrder", ALWAYS, []),
            ("colOrder", ALWAYS, []),
            ("tone", ALWAYS, "diverging"),
        ),
        mergeOptions=True,
    )
    table["quantStyleMatrix"] = AdapterPlan(
        builder="buildQuantStyleMatrix",
        arg="stockCode",
        fields=(("rows", ALWAYS, []), ("peerCount", ALWAYS, 0)),
        mergeOptions=True,
    )
    table["quantBetaScatter"] = AdapterPlan(
        builder="buildQuantBetaScatter",
        arg="stockCode",
        fields=tuple((key, PRESENT, None) for key in ("points", "xLabel", "yLabel", "xUnit", "yUnit", "xRef", "yRef")),
        mergeOptions=True,
    )
    table["quantRegimePhase"] = AdapterPlan(
        builder="buildQuantRegimePhase",
        arg="stockCode",
        fields=tuple((key, PRESENT, None) for key in ("phases", "current", "confidence", "subtitle")),
    )
    return table


ADAPTER_PLANS: dict[str, AdapterPlan] = _buildTable()

# 정규화 표가 필요한 어댑터 이름. 표에서 도출하므로 따로 관리하지 않는다. 예전에는 별도
# 튜플로 손수 적어 두어서 표와 어긋날 수 있었다.
NORM_ADAPTERS: frozenset[str] = frozenset(name for name, plan in ADAPTER_PLANS.items() if plan.needsNorm) | {
    "kpiFromNorm",
    "diffFromNorm",
}

__all__ = ["ADAPTER_PLANS", "ALWAYS", "AdapterPlan", "NORM_ADAPTERS", "PRESENT"]
