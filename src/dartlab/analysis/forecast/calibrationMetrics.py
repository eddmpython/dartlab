"""calibrationMetrics 호환 경로.

계산 SSOT는 ``dartlab.synth.calibrationMetrics``에 있다. 기존 호출부 identity 보존용 re-export다.
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
