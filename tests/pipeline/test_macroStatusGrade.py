"""macro 수집이 0 행을 성공으로 기록하지 않는다는 계약.

세 수집 단계(fred·ecos·customs)가 `status = "ok"` 를 먼저 두고 예외가 날 때만 바꿨다.
그래서 호출이 멀쩡히 끝나고 0 행을 돌려주면 그대로 성공으로 기록됐다. 실측으로 ECOS
쉰세 지표 중 열여덟 개가 status ok 에 rowCount 0 이었고, 그 안에 국고채 3·5·10 년과
코어 CPI 와 PPI 와 실질 GDP 가 있었다. 소비자는 manifest 를 믿고 지표가 있는 줄 알았고,
거시 베타 축은 그 GDP 공백 하나 때문에 전종목 빈 표를 냈다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_gradeStatus_marksEmptyFetch():
    """예외 없이 0 행이면 empty 로 내리고 사유를 남긴다."""
    from dartlab.pipeline.stages.macro import _gradeStatus

    status, error = _gradeStatus("ok", "", 0, "ecos", "GDP")

    assert status == "empty"
    assert error


def test_gradeStatus_keepsOkWhenRowsPresent():
    """행이 있으면 그대로 ok."""
    from dartlab.pipeline.stages.macro import _gradeStatus

    assert _gradeStatus("ok", "", 9695, "ecos", "BASE_RATE") == ("ok", "")


def test_gradeStatus_doesNotOverwriteFailure():
    """예외로 이미 stale·error 로 내려간 것은 건드리지 않는다."""
    from dartlab.pipeline.stages.macro import _gradeStatus

    assert _gradeStatus("stale", "TimeoutError: ...", 0, "fred", "GDP") == ("stale", "TimeoutError: ...")
    assert _gradeStatus("error", "KeyError: ...", 0, "fred", "GDP") == ("error", "KeyError: ...")
