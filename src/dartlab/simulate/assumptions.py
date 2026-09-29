"""사용자 가정 입력 계약. 사용자 시나리오 경로와 드라이버 override 를 검증해 시트 입력으로 바꾼다.

시뮬레이터는 미래를 맞히지 않는다. 명시한 가정 아래에서 무엇이 벌어지는지를 보여 준다. 그 가정은
프리셋 다섯 개에 갇히지 않고 사용자가 직접 켜고 끌 수 있어야 한다. 이 모듈은 두 입력을 받는다.

- 사용자 시나리오: 프리셋 하나를 바탕으로 GDP 성장률, 기준금리, 원달러 경로 중 일부를 바꾼다.
  세 경로를 모두 주면 프리셋 길이(3년)를 넘어 최대 10년까지 펼칠 수 있다.
- 드라이버 override: 회사 snapshot 의 기준 WACC, 영구성장률, 기준 영업이익률, 업종 탄성을 바꾼다.

둘 다 허용 범위를 벗어나거나 모르는 키가 있으면 실행 전에 실패한다. 적용한 값은 결과의
``assumptionLedger`` 에 ``source="user"`` 로 남고 노드 provenance 와 refs 에도 드러난다. 난수는 없다.
같은 가정은 같은 ``inputsHash`` 를 만든다.

Layer: L3. Forward imports: L1.5 (`synth.scenario`), `simulate.channels`, `simulate.registry`.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import replace

from dartlab.simulate.channels import PRESET_MARKET, SCENARIO_VARIABLES, ScenarioPaths
from dartlab.simulate.registry import validateScenarioSpec
from dartlab.synth.scenario import SectorElasticity, getPresetScenarios

DEFAULT_USER_SCENARIO_NAME = "custom"
MAX_USER_HORIZON = 10
# 거시 경로 허용 범위. GDP 성장률과 기준금리는 %, 환율은 원달러 수준이다. 범위 밖은 오타나 단위
# 착오일 가능성이 커서 조용히 자르지 않고 실행 전에 실패한다.
SCENARIO_PATH_BOUNDS = {
    "gdp": (-30.0, 30.0),
    "rate": (0.0, 30.0),
    "fx": (100.0, 10000.0),
}
# 드라이버 override 허용 범위와 단위. WACC, 영구성장률, 영업이익률은 %, 탄성은 SectorElasticity 단위다.
DRIVER_OVERRIDE_BOUNDS = {
    "baseWacc": (0.5, 50.0),
    "terminalGrowth": (-5.0, 10.0),
    "baseMargin": (-100.0, 100.0),
    "revenueToGdp": (-10.0, 10.0),
    "revenueToFx": (-100.0, 100.0),
    "marginToGdp": (-1000.0, 1000.0),
    "nimToRate": (-1000.0, 1000.0),
}
_PRESET_FIELDS = {"gdp": "gdpGrowth", "rate": "interestRate", "fx": "krwUsd"}
_SCENARIO_KEYS = frozenset({"name", "base", *SCENARIO_VARIABLES})
_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
_ELASTICITY_FIELDS = ("revenueToGdp", "revenueToFx", "marginToGdp", "nimToRate")
# override 가 대신하는 snapshot 기본값 가정 id. 값을 사용자가 정하면 그 기본값은 더 이상 쓰이지 않는다.
_SUPERSEDED_DEFAULTS = {
    "baseWacc": "baseWacc10Pct",
    "terminalGrowth": "terminalGrowth3Pct",
    "baseMargin": "baseMargin10Pct",
}


class AssumptionInputError(ValueError):
    """사용자 시나리오나 드라이버 override 가 입력 계약을 어길 때 발생한다."""


def _presetPaths(name: str) -> dict[str, tuple[float, ...]]:
    preset = getPresetScenarios(PRESET_MARKET)[name]
    return {
        variable: tuple(float(item) for item in getattr(preset, field)) for variable, field in _PRESET_FIELDS.items()
    }


def _finiteNumber(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssumptionInputError(f"{label} 는 숫자여야 합니다: {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise AssumptionInputError(f"{label} 는 유한한 숫자여야 합니다: {value!r}")
    return number


def _userPath(variable: str, raw: object, horizon: int) -> tuple[float, ...]:
    if isinstance(raw, (str, bytes)) or not hasattr(raw, "__iter__"):
        raise AssumptionInputError(f"{variable} 경로는 연도별 숫자 목록이어야 합니다")
    lower, upper = SCENARIO_PATH_BOUNDS[variable]
    path = tuple(_finiteNumber(item, f"{variable} 경로 값") for item in raw)
    if len(path) < horizon:
        raise AssumptionInputError(f"{variable} 경로가 {len(path)}년이라 horizon={horizon} 보다 짧습니다")
    outside = [item for item in path if not lower <= item <= upper]
    if outside:
        raise AssumptionInputError(f"{variable} 경로 값 {outside[0]} 이 허용 범위 [{lower}, {upper}] 밖입니다")
    return path


def _userScenario(spec: Mapping, horizon: int) -> ScenarioPaths:
    unknown = sorted(set(spec) - _SCENARIO_KEYS)
    if unknown:
        raise AssumptionInputError(f"사용자 시나리오에 모르는 키가 있습니다: {unknown}; 허용: {sorted(_SCENARIO_KEYS)}")
    presets = getPresetScenarios(PRESET_MARKET)
    name = spec.get("name", DEFAULT_USER_SCENARIO_NAME)
    if not isinstance(name, str) or not _NAME_PATTERN.match(name):
        raise AssumptionInputError("사용자 시나리오 name 은 영문으로 시작하는 40자 이하 영숫자, -, _ 여야 합니다")
    if name in presets:
        raise AssumptionInputError(
            f"사용자 시나리오 name {name!r} 이 프리셋과 같습니다. 바뀐 경로를 프리셋 이름으로 부르지 않습니다"
        )
    base = spec.get("base", "baseline")
    if not isinstance(base, str) or base not in presets:
        raise AssumptionInputError(f"base 는 프리셋 id 여야 합니다: {base!r}; 유효값: {', '.join(sorted(presets))}")
    userVariables = tuple(variable for variable in SCENARIO_VARIABLES if spec.get(variable) is not None)
    if not userVariables:
        raise AssumptionInputError("사용자 시나리오는 gdp, rate, fx 중 하나 이상의 경로를 바꿔야 합니다")
    paths = _presetPaths(base)
    for variable in userVariables:
        paths[variable] = _userPath(variable, spec[variable], horizon)
    resolved = ScenarioPaths(name=name, base=base, userVariables=userVariables, **paths)
    if horizon > resolved.maxHorizon:
        missing = [variable for variable in SCENARIO_VARIABLES if len(resolved.path(variable)) < horizon]
        raise AssumptionInputError(
            f"horizon={horizon} 을 펼치려면 {', '.join(missing)} 경로도 {horizon}년 이상 줘야 합니다 "
            f"(base 프리셋 {base!r} 는 {len(paths[missing[0]])}년)"
        )
    return resolved


def resolveScenarioPaths(scenario: str | Mapping | ScenarioPaths | None, horizon: int) -> ScenarioPaths:
    """프리셋 id 나 사용자 시나리오를 한 실행의 거시 경로로 해소한다.

    Args:
        scenario: 프리셋 id(``"adverse"``), 사용자 시나리오 mapping, 이미 해소한 ``ScenarioPaths``,
            또는 ``None``(``"baseline"``). mapping 키는 ``name``, ``base``, ``gdp``, ``rate``, ``fx`` 다.
        horizon: 펼칠 연수. 프리셋은 프리셋 길이, 사용자 시나리오는 ``MAX_USER_HORIZON`` 까지다.

    Returns:
        거시 경로 세 개와 출처를 담은 ``ScenarioPaths``.

    Raises:
        TypeError: scenario 나 horizon 의 타입이 잘못됐을 때.
        ValueError: 프리셋 id, 사용자 경로, horizon 이 허용 범위를 벗어났을 때.
            사용자 입력 오류는 ``AssumptionInputError`` 다.

    Example:
        ``resolveScenarioPaths({"name": "rateShock", "rate": [4.5, 5.0, 5.0]}, 3).userVariables``
        는 ``("rate",)`` 이다.
    """

    if isinstance(horizon, bool) or not isinstance(horizon, int):
        raise TypeError("horizon 은 정수여야 합니다.")
    if isinstance(scenario, ScenarioPaths):
        if not scenario.isUser:
            validateScenarioSpec(scenario.name, horizon)
        elif not 1 <= horizon <= min(MAX_USER_HORIZON, scenario.maxHorizon):
            raise AssumptionInputError(f"horizon={horizon} 이 사용자 시나리오 경로 범위를 벗어납니다")
        return scenario
    if scenario is None or isinstance(scenario, str):
        name = "baseline" if scenario is None else scenario
        validateScenarioSpec(name, horizon)
        return ScenarioPaths(name=name, base=name, **_presetPaths(name))
    if not isinstance(scenario, Mapping):
        raise TypeError("scenario 는 프리셋 id 문자열이나 사용자 시나리오 mapping 이어야 합니다.")
    if not 1 <= horizon <= MAX_USER_HORIZON:
        raise AssumptionInputError(f"사용자 시나리오 horizon 은 1 이상 {MAX_USER_HORIZON} 이하입니다: {horizon}")
    return _userScenario(scenario, horizon)


def resolveDriverOverrides(overrides: Mapping | None) -> tuple[tuple[str, float], ...]:
    """드라이버 override mapping 을 검증해 키 순서로 고정한다.

    Args:
        overrides: ``baseWacc``, ``terminalGrowth``, ``baseMargin``, ``revenueToGdp``,
            ``revenueToFx``, ``marginToGdp``, ``nimToRate`` 중 일부를 숫자로 준 mapping, 또는 ``None``.

    Returns:
        ``(키, 값)`` 쌍을 키 순서로 정렬한 tuple. ``None`` 이면 빈 tuple.

    Raises:
        TypeError: overrides 가 mapping 이 아닐 때.
        AssumptionInputError: 모르는 키, 숫자가 아닌 값, 허용 범위 밖 값이 있을 때.

    Example:
        ``resolveDriverOverrides({"baseWacc": 9.0})`` 는 ``(("baseWacc", 9.0),)`` 이다.
    """

    if overrides is None:
        return ()
    if not isinstance(overrides, Mapping):
        raise TypeError("overrides 는 드라이버 이름을 키로 둔 mapping 이어야 합니다.")
    unknown = sorted(set(overrides) - set(DRIVER_OVERRIDE_BOUNDS))
    if unknown:
        raise AssumptionInputError(f"모르는 드라이버 override: {unknown}; 허용: {sorted(DRIVER_OVERRIDE_BOUNDS)}")
    resolved = []
    for key in sorted(overrides):
        value = _finiteNumber(overrides[key], key)
        lower, upper = DRIVER_OVERRIDE_BOUNDS[key]
        if not lower <= value <= upper:
            raise AssumptionInputError(f"{key}={value} 가 허용 범위 [{lower}, {upper}] 밖입니다")
        resolved.append((key, value))
    return tuple(resolved)


def applyDriverOverrides(snapshot: dict, overrides: tuple[tuple[str, float], ...]) -> dict:
    """snapshot 의 드라이버 값을 override 로 바꾼 새 snapshot 을 돌려준다.

    Args:
        snapshot: ``buildSnapshot`` 이 만든 frozen snapshot. 바꾸지 않는다.
        overrides: ``resolveDriverOverrides`` 결과.

    Returns:
        override 를 반영한 snapshot 복사본. 값을 사용자가 정한 기본값 가정 id 는 ``assumptions`` 에서
        빠진다. 탄성 네 개를 모두 정하면 ``defaultSectorElasticity`` 도 빠진다.

    Raises:
        없음. 입력 검증은 ``resolveDriverOverrides`` 가 끝냈다.

    Example:
        ``applyDriverOverrides(snapshot, (("baseWacc", 9.0),))["baseWacc"]`` 는 ``9.0`` 이다.
    """

    if not overrides:
        return snapshot
    values = dict(overrides)
    updated = dict(snapshot)
    for key in ("baseWacc", "terminalGrowth", "baseMargin"):
        if key in values:
            updated[key] = values[key]
    elasticityValues = {key: values[key] for key in _ELASTICITY_FIELDS if key in values}
    if elasticityValues:
        elasticity: SectorElasticity = snapshot["elasticity"]
        updated["elasticity"] = replace(elasticity, **elasticityValues)
    superseded = {_SUPERSEDED_DEFAULTS[key] for key in values if key in _SUPERSEDED_DEFAULTS}
    if all(key in values for key in _ELASTICITY_FIELDS):
        superseded.add("defaultSectorElasticity")
    updated["assumptions"] = tuple(item for item in snapshot.get("assumptions", ()) if item not in superseded)
    return updated


def userAssumptionRows(
    scenarioPaths: ScenarioPaths,
    overrides: tuple[tuple[str, float], ...],
    horizon: int,
) -> tuple[dict, ...]:
    """사용자가 정한 경로와 override 를 가정 원장 행으로 만든다.

    Args:
        scenarioPaths: ``resolveScenarioPaths`` 결과.
        overrides: ``resolveDriverOverrides`` 결과.
        horizon: 실행 연수. 경로는 이 길이로 잘라 적는다.

    Returns:
        ``source="user"``, ``appliedToDriverSheet=True`` 인 행 tuple. 프리셋 실행에 override 도 없으면 빈 tuple.

    Raises:
        없음.

    Example:
        ``userAssumptionRows(paths, (("baseWacc", 9.0),), 3)[-1]["id"]`` 는 ``"baseWacc"`` 다.
    """

    rows: list[dict] = [
        {
            "source": "user",
            "kind": "scenarioPath",
            "id": variable,
            "scenario": scenarioPaths.name,
            "base": scenarioPaths.base,
            "value": list(scenarioPaths.path(variable)[:horizon]),
            "appliedToDriverSheet": True,
        }
        for variable in scenarioPaths.userVariables
    ]
    rows.extend(
        {
            "source": "user",
            "kind": "driverOverride",
            "id": key,
            "value": value,
            "appliedToDriverSheet": True,
        }
        for key, value in overrides
    )
    return tuple(rows)
