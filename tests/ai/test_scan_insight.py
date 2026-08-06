"""스크리닝 결과의 함정 검출을 잠근다.

실측(2026-08-06) 그대로를 표본으로 쓴다. "ROE 15% 이상 부채비율 100% 미만" 으로 거른
6 종목 중 001140 은 2025FY 부채총계 771억원에 지배주주지분 -169억원인 완전자본잠식이었고,
그 음수 부채비율(-456.39%)이 조건을 통과했다.
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools.scanInsight import (
    impairedEquityDetail,
    impairedEquityRows,
    missingNameRows,
    screenTrapNotes,
)

pytestmark = pytest.mark.unit

# 실측 표본. 종목명이 비어 오는 것과 부채비율이 음수인 것이 같은 표에 섞여 있었다.
_MEASURED_COLUMNS = ["종목코드", "종목명", "finance.ratio.roe", "finance.ratio.debtRatio"]
_MEASURED_ROWS = [
    {"종목코드": "000660", "종목명": "SK하이닉스", "finance.ratio.roe": 24.54, "finance.ratio.debtRatio": 35.56},
    {"종목코드": "001140", "종목명": None, "finance.ratio.roe": 70.71, "finance.ratio.debtRatio": -456.39},
    {"종목코드": "0203K0", "종목명": "송우인포텍", "finance.ratio.roe": 15.27, "finance.ratio.debtRatio": 28.81},
    {"종목코드": "023460", "종목명": None, "finance.ratio.roe": 41.0, "finance.ratio.debtRatio": -758.21},
    {"종목코드": "039790", "종목명": None, "finance.ratio.roe": 20.29, "finance.ratio.debtRatio": -799.51},
    {"종목코드": "049130", "종목명": None, "finance.ratio.roe": 15.34, "finance.ratio.debtRatio": 4.46},
]


def testNegativeDebtRatioRowsAreCollected() -> None:
    """부채비율이 음수인 세 종목을 빠짐없이 집는다."""
    assert impairedEquityRows(_MEASURED_COLUMNS, _MEASURED_ROWS) == ["001140", "023460", "039790"]


def testHealthyRowsRaiseNoImpairment() -> None:
    """양수 부채비율만 남기면 자본잠식 신호가 없다."""
    rows = [row for row in _MEASURED_ROWS if row["finance.ratio.debtRatio"] > 0]
    assert impairedEquityRows(_MEASURED_COLUMNS, rows) == []


def testKoreanColumnNameIsRecognized() -> None:
    """열 이름이 한글로 rename 돼 와도 같은 판정을 한다."""
    columns = ["종목코드", "부채비율"]
    rows = [{"종목코드": "001140", "부채비율": -456.39}, {"종목코드": "000660", "부채비율": 35.56}]
    assert impairedEquityRows(columns, rows) == ["001140"]


def testBooleanIsNotCountedAsNumber() -> None:
    """파이썬에서 False 는 0 이라 수치로 조용히 섞인다. 음수로 읽히면 안 된다."""
    columns = ["종목코드", "부채비율"]
    rows = [{"종목코드": "000660", "부채비율": False}]
    assert impairedEquityRows(columns, rows) == []


def testMissingCorpNameRowsAreCollected() -> None:
    """상장목록에 없는 코드는 이름이 비어 온다. 그 사실을 알려야 재조회를 막는다."""
    assert missingNameRows(_MEASURED_COLUMNS, _MEASURED_ROWS) == ["001140", "023460", "039790", "049130"]


def testNotesCoverBothImpairmentAndMissingName() -> None:
    """두 함정이 같은 표에 있으면 둘 다 적는다."""
    notes = screenTrapNotes(_MEASURED_COLUMNS, _MEASURED_ROWS)
    assert len(notes) == 2
    assert "자본잠식 의심 3건" in notes[0]
    assert "001140" in notes[0]
    # 왜 위험한지까지 적어야 모델이 수치가 좋아 보이는 쪽으로 읽지 않는다.
    assert "ROE" in notes[0]
    assert "종목명이 비어 있는 행 4건" in notes[1]


def testCleanResultProducesNoNotes() -> None:
    """없는 경고를 만들지 않는다. 소음은 그 자체로 답변을 흐린다."""
    columns = ["종목코드", "종목명", "부채비율"]
    rows = [{"종목코드": "000660", "종목명": "SK하이닉스", "부채비율": 35.56}]
    assert screenTrapNotes(columns, rows) == []


def testEmptyResultProducesNoNotes() -> None:
    """행이 없으면 판정할 것도 없다."""
    assert screenTrapNotes(_MEASURED_COLUMNS, []) == []


@pytest.mark.parametrize("column", ["finance.ratio.debtRatio", "axis.debt.debtRatio", "부채비율"])
def testColumnNameVariantsAreAllRecognized(column: str) -> None:
    """같은 지표가 경로마다 다른 이름으로 온다. 하나만 보면 조용히 놓친다."""
    rows = [{"종목코드": "001140", column: -456.39}]
    assert impairedEquityRows(["종목코드", column], rows) == ["001140"]


def testNoteNamesOnlyTheColumnThatWasActuallyNegative() -> None:
    """표에 없는 열을 근거로 대지 않는다. 모델은 이 문장을 그대로 인용한다."""
    columns = ["종목코드", "자기자본비율"]
    rows = [{"종목코드": "001140", "자기자본비율": -28.1}]
    impaired, signals = impairedEquityDetail(columns, rows)
    assert impaired == ["001140"]
    assert signals == ["자기자본비율"]
    note = screenTrapNotes(columns, rows)[0]
    assert "자기자본비율이 음수" in note
    # 부채비율 열이 표에 없으므로 그 이름을 근거로 말하면 안 된다.
    assert "부채비율이 음수" not in note
