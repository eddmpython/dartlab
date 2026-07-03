"""calibrationMetrics 호환 경로.

계산 SSOT 는 ``dartlab.synth.calibrationMetrics`` 에 있다 (2026-07-03 승격,
mainPlan/expectation-grid/00 §9 A3). 기존 호출부 identity 보존용 re-export.
"""

from __future__ import annotations

from dartlab.synth.calibrationMetrics import (
    CalibrationBin,
    CalibrationReport,
    buildCalibrationBins,
    computeBrierScore,
    generateCalibrationReport,
)

__all__ = [
    "CalibrationBin",
    "CalibrationReport",
    "buildCalibrationBins",
    "computeBrierScore",
    "generateCalibrationReport",
]
