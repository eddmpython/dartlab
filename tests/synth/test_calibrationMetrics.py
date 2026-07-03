"""calibrationMetrics synth 승격 검증 : 계산 identity + 옛 경로 re-export 호환.

승격(analysis/forecast → synth, expectation-grid 00 §9 A3) 후에도
①계산 골든값 불변 ②옛 import 경로 동작 ③두 경로가 같은 객체를 가리킴을 고정한다.
"""

from __future__ import annotations

import pytest

from dartlab.synth.calibrationMetrics import computeBrierScore, generateCalibrationReport


def test_brier_golden():
    assert computeBrierScore([0.7, 0.3], [1, 0]) == pytest.approx(0.09)


def test_report_requires_min_five():
    assert generateCalibrationReport([0.5] * 4, [1, 0, 1, 0]) is None
    r = generateCalibrationReport([0.5] * 10, [1, 0] * 5)
    assert r is not None and r.totalPredictions == 10


def test_legacy_import_path_identity():
    from dartlab.analysis.forecast import calibrationMetrics as legacy
    from dartlab.synth import calibrationMetrics as ssot

    assert legacy.computeBrierScore is ssot.computeBrierScore
    assert legacy.CalibrationReport is ssot.CalibrationReport
