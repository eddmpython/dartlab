"""거시 forward 시뮬레이션 엔진 — BVAR 팬 + IRF + 국면경로.

공개 진입 = simulateMacro(dartlab.macro.simulate). leaf 수학(BVAR·fan·IRF)은 순수 numpy,
국면경로는 cycles.regimeSwitching 전이행렬을 재사용한다.
"""

from __future__ import annotations

from dartlab.macro.simulate._types import BvarFit, MacroSimResult, VarSpec
from dartlab.macro.simulate.bvar import estimateBvar, maxCompanionModulus
from dartlab.macro.simulate.calibration import fanCalibration
from dartlab.macro.simulate.fan import forwardFan
from dartlab.macro.simulate.irf import impulseResponse
from dartlab.macro.simulate.regimePath import simulateRegimePath
from dartlab.macro.simulate.scenarioPath import buildScenarios, conditionalPath
from dartlab.macro.simulate.simulate import simulateMacro

__all__ = [
    "BvarFit",
    "MacroSimResult",
    "VarSpec",
    "buildScenarios",
    "conditionalPath",
    "estimateBvar",
    "fanCalibration",
    "forwardFan",
    "impulseResponse",
    "maxCompanionModulus",
    "simulateMacro",
    "simulateRegimePath",
]
