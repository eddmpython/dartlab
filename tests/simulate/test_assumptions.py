"""사용자 가정 입력 회귀. 사용자 거시 경로와 드라이버 override 가 시트까지 정직하게 흐르는지 고정한다."""

from __future__ import annotations

import pytest

from dartlab.simulate import run as runModule
from dartlab.simulate.assumptions import (
    MAX_USER_HORIZON,
    AssumptionInputError,
    applyDriverOverrides,
    resolveDriverOverrides,
    resolveScenarioPaths,
    userAssumptionRows,
)
from dartlab.simulate.channels import ScenarioPaths
from dartlab.simulate.registry import buildScenarioSheet, nodeIdFor
from dartlab.simulate.sheet import evaluateSheet
from dartlab.synth.scenario import SectorElasticity, getPresetScenarios

_BASELINE = getPresetScenarios("KR")["baseline"]
_SEMI = SectorElasticity(1.8, 0.8, 50, 0, "high")


def _series() -> dict:
    """buildProforma 가 3년을 투영할 수 있는 최소 IS/BS/CF 네 분기."""

    revenue = [70.0, 72.0, 74.0, 76.0]
    return {
        "IS": {
            "sales": revenue,
            "gross_profit": [item * 0.4 for item in revenue],
            "selling_and_administrative_expenses": [item * 0.2 for item in revenue],
            "operating_profit": [item * 0.2 for item in revenue],
            "profit_before_tax": [item * 0.18 for item in revenue],
            "income_tax_expense": [item * 0.04 for item in revenue],
            "net_profit": [item * 0.14 for item in revenue],
        },
        "CF": {
            "operating_cashflow": [item * 0.22 for item in revenue],
            "purchase_of_property_plant_and_equipment": [-item * 0.06 for item in revenue],
            "depreciation_and_amortization": [item * 0.05 for item in revenue],
            "dividends_paid": [-item * 0.03 for item in revenue],
        },
        "BS": {
            "current_assets": [120.0, 122.0, 124.0, 126.0],
            "current_liabilities": [60.0, 61.0, 62.0, 63.0],
            "cash_and_cash_equivalents": [40.0, 41.0, 42.0, 43.0],
            "total_assets": [300.0, 305.0, 310.0, 315.0],
            "total_liabilities": [120.0, 121.0, 122.0, 123.0],
            "total_stockholders_equity": [180.0, 184.0, 188.0, 192.0],
            "shortterm_borrowings": [20.0, 20.0, 20.0, 20.0],
            "longterm_borrowings": [30.0, 30.0, 30.0, 30.0],
            "trade_receivables": [50.0, 51.0, 52.0, 53.0],
            "inventories": [40.0, 41.0, 42.0, 43.0],
            "trade_payables": [30.0, 31.0, 32.0, 33.0],
        },
    }


def _snapshot(**overrides) -> dict:
    """buildSnapshot 모양의 합성 snapshot. 기본값 가정 두 개를 기록해 둔다."""

    snap = {
        "series": _series(),
        "baseRevenue": 300.0,
        "baseMargin": 20.0,
        "netDebt": 10.0,
        "shares": 1000,
        "elasticity": _SEMI,
        "sectorKey": "반도체",
        "baseWacc": 10.0,
        "terminalGrowth": 3.0,
        "asOf": "2024Q4",
        "latestAsOf": "2024Q4",
        "requestedAsOf": "2024Q4",
        "assumptions": ("baseWacc10Pct", "terminalGrowth3Pct"),
        "warnings": (),
        "parameterVintageStatus": "available",
    }
    snap.update(overrides)
    return snap


def testPresetResolutionKeepsThePresetPaths() -> None:
    """프리셋 id 와 None 은 프리셋 경로 그대로이고 사용자 변수가 없다."""

    adverse = resolveScenarioPaths("adverse", 3)
    baseline = resolveScenarioPaths(None, 3)

    assert (adverse.name, adverse.base, adverse.isUser) == ("adverse", "adverse", False)
    assert baseline.name == "baseline"
    assert baseline.rate == tuple(float(item) for item in _BASELINE.interestRate)
    assert resolveScenarioPaths(adverse, 3) is adverse


def testUserScenarioReplacesOnlyTheGivenPaths() -> None:
    """사용자가 준 금리 경로만 바뀌고 GDP 와 환율은 base 프리셋에서 온다."""

    paths = resolveScenarioPaths({"name": "rateShock", "base": "baseline", "rate": [5, 5.5, 5.5]}, 3)

    assert (paths.name, paths.base, paths.userVariables, paths.isUser) == ("rateShock", "baseline", ("rate",), True)
    assert paths.rate == (5.0, 5.5, 5.5)
    assert paths.gdp == tuple(float(item) for item in _BASELINE.gdpGrowth)
    assert paths.fx == tuple(float(item) for item in _BASELINE.krwUsd)


def testUserScenarioCanExtendTheHorizonOnlyWithAllThreePaths() -> None:
    """프리셋은 3년이다. 세 경로를 모두 주면 더 길게 펼칠 수 있고, 하나라도 빠지면 거부한다."""

    long = {"name": "decade", "gdp": [2.0] * 5, "rate": [3.0] * 5, "fx": [1400.0] * 5}
    assert resolveScenarioPaths(long, 5).maxHorizon == 5
    with pytest.raises(AssumptionInputError, match="fx"):
        resolveScenarioPaths({"name": "partial", "gdp": [2.0] * 5, "rate": [3.0] * 5}, 5)
    with pytest.raises(AssumptionInputError, match="이하"):
        resolveScenarioPaths({"name": "tooLong", "gdp": [2.0] * 12}, MAX_USER_HORIZON + 1)


@pytest.mark.parametrize(
    ("spec", "message"),
    (
        ({"name": "x1", "gdb": [1.0, 1.0, 1.0]}, "모르는 키"),
        ({"name": "adverse", "rate": [3.0, 3.0, 3.0]}, "프리셋과 같습니다"),
        ({"name": "1bad", "rate": [3.0, 3.0, 3.0]}, "name"),
        ({"name": "noPath"}, "하나 이상"),
        ({"name": "badBase", "base": "severe", "rate": [3.0, 3.0, 3.0]}, "base"),
        ({"name": "short", "rate": [3.0, 3.0]}, "짧습니다"),
        ({"name": "percentMix", "rate": [0.035, 0.04, 45.0]}, "허용 범위"),
        ({"name": "nanPath", "gdp": [1.0, float("nan"), 1.0]}, "유한한"),
        ({"name": "textPath", "fx": "1400,1400,1400"}, "목록"),
        ({"name": "boolPath", "gdp": [True, 1.0, 1.0]}, "숫자"),
    ),
)
def testUserScenarioFailsClosedOnBrokenInput(spec: dict, message: str) -> None:
    """모르는 키, 프리셋 이름 도용, 빈 경로, 짧거나 범위 밖이거나 숫자가 아닌 경로는 실행 전에 거부한다."""

    with pytest.raises(AssumptionInputError, match=message):
        resolveScenarioPaths(spec, 3)


def testScenarioTypeAndHorizonTypeAreChecked() -> None:
    """scenario 와 horizon 의 타입이 틀리면 TypeError 다."""

    with pytest.raises(TypeError):
        resolveScenarioPaths(["baseline"], 3)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        resolveScenarioPaths("baseline", True)


def testDriverOverridesAreValidatedAndSorted() -> None:
    """override 는 키 순서로 고정되고, 모르는 키와 범위 밖 값은 거부한다."""

    assert resolveDriverOverrides(None) == ()
    assert resolveDriverOverrides({"terminalGrowth": 2, "baseWacc": 9.5}) == (
        ("baseWacc", 9.5),
        ("terminalGrowth", 2.0),
    )
    with pytest.raises(AssumptionInputError, match="모르는"):
        resolveDriverOverrides({"wacc": 9.0})
    with pytest.raises(AssumptionInputError, match="허용 범위"):
        resolveDriverOverrides({"baseWacc": 0.09 * 1000})
    with pytest.raises(AssumptionInputError, match="숫자"):
        resolveDriverOverrides({"baseMargin": "12"})
    with pytest.raises(TypeError):
        resolveDriverOverrides([("baseWacc", 9.0)])  # type: ignore[arg-type]


def testApplyDriverOverridesReplacesValuesAndRetiresSupersededDefaults() -> None:
    """정한 값은 snapshot 을 바꾸고, 그 값이 대신한 기본값 가정은 원장에서 빠진다. 원본은 그대로다."""

    snap = _snapshot()
    overrides = resolveDriverOverrides({"baseWacc": 8.0, "revenueToGdp": 1.2})
    updated = applyDriverOverrides(snap, overrides)

    assert updated["baseWacc"] == 8.0
    assert updated["elasticity"].revenueToGdp == 1.2
    assert updated["elasticity"].marginToGdp == _SEMI.marginToGdp
    assert updated["assumptions"] == ("terminalGrowth3Pct",)
    assert snap["baseWacc"] == 10.0 and snap["elasticity"] is _SEMI
    assert applyDriverOverrides(snap, ()) is snap

    allElasticity = applyDriverOverrides(
        _snapshot(assumptions=("defaultSectorElasticity",)),
        resolveDriverOverrides({"revenueToGdp": 1.0, "revenueToFx": 0.5, "marginToGdp": 20.0, "nimToRate": 0.0}),
    )
    assert allElasticity["assumptions"] == ()


def testUserPathsFlowIntoTheSheetWithProvenance() -> None:
    """바꾼 금리 root 는 사용자 경로와 user ref 를 내고, 바꾸지 않은 GDP root 는 프리셋 node 와 hash 가 같다."""

    rateShock = resolveScenarioPaths({"name": "rateShock", "rate": [5.0, 5.5, 5.5]}, 3)
    user = evaluateSheet(buildScenarioSheet(_snapshot(), scenario=rateShock, horizon=3))
    preset = evaluateSheet(buildScenarioSheet(_snapshot(), scenario="baseline", horizon=3))

    userRate = user[nodeIdFor("macro.rate", "rateShock")]
    assert userRate.vector == (5.0, 5.5, 5.5)
    assert userRate.provenance == "user:rateShock"
    assert userRate.refs == ("user:scenario/rateShock#rate",)
    userGdp = user[nodeIdFor("macro.path", "rateShock")]
    presetGdp = preset[nodeIdFor("macro.path", "baseline")]
    assert userGdp.vector == presetGdp.vector
    assert userGdp.inputsHash == presetGdp.inputsHash
    assert userRate.inputsHash != preset[nodeIdFor("macro.rate", "baseline")].inputsHash
    userWacc = user[nodeIdFor("wacc.path", "rateShock")].vector
    presetWacc = preset[nodeIdFor("wacc.path", "baseline")].vector
    assert all(shocked > base for shocked, base in zip(userWacc, presetWacc))


def testRunScenarioRecordsUserAssumptionsInTheResult(monkeypatch: pytest.MonkeyPatch) -> None:
    """runScenario 결과가 쓴 거시 경로, 시나리오 종류, 사용자 가정 원장 행을 함께 낸다."""

    monkeypatch.setattr(runModule, "buildSnapshot", lambda company, asOf=None: _snapshot())
    baseline = runModule.runScenario(object(), scenario="baseline", horizon=3)
    result = runModule.runScenario(
        object(),
        scenario={"name": "rateShock", "rate": [5.0, 5.5, 5.5]},
        horizon=3,
        overrides={"baseWacc": 8.0},
    )

    assert (baseline.scenarioKind, baseline.scenarioBase) == ("preset", "baseline")
    assert baseline.macroPaths["rate"] == tuple(float(item) for item in _BASELINE.interestRate)
    assert (result.scenarioName, result.scenarioKind, result.scenarioBase) == ("rateShock", "user", "baseline")
    assert result.macroPaths["rate"] == (5.0, 5.5, 5.5)
    userRows = [row for row in result.assumptionLedger if row["source"] == "user"]
    assert [(row["kind"], row["id"]) for row in userRows] == [("scenarioPath", "rate"), ("driverOverride", "baseWacc")]
    assert all(row["appliedToDriverSheet"] for row in userRows)
    assert "baseWacc10Pct" not in result.assumptions
    assert result.nodes["macro.rate"].provenance == "user:rateShock"
    assert baseline.waccPath != result.waccPath


def testUserAssumptionRowsAreEmptyForPresetRunsWithoutOverrides() -> None:
    """프리셋 실행에 override 도 없으면 사용자 가정 행이 없다."""

    assert userAssumptionRows(resolveScenarioPaths("baseline", 3), (), 3) == ()
    rows = userAssumptionRows(ScenarioPaths("s1", "baseline", (1.0,) * 5, (2.0,) * 5, (3.0,) * 5, ("gdp",)), (), 2)
    assert rows[0]["value"] == [1.0, 1.0]
