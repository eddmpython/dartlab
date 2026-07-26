"""L0 DataFrame 유효성 판정 회귀.

`core/polarsUtil.py` 는 공개 함수 둘이 테스트 참조 0 이었다. 이 판정이 저장소 전역에서
`df is None or df.is_empty()` 를 대신하고 있어서, 여기서 한 번 잘못 판정하면 "데이터
없음" 과 "조회 실패" 가 수십 곳에서 동시에 뒤섞인다.

두 함수는 서로의 부정이라는 것이 계약의 절반이다. 그 대칭이 깨지면 호출부마다 다른
답을 받는다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.core.polarsUtil import isEmptyDf, isValidDf


def testNoneIsNeverValid() -> None:
    """조회 실패로 None 이 오면 유효하지 않다."""

    assert isValidDf(None) is False
    assert isEmptyDf(None) is True


def testEmptyFrameIsNotValid() -> None:
    """행이 없는 결과는 유효하지 않다. 여기가 True 면 빈 표가 데이터로 흘러간다."""

    assert isValidDf(pl.DataFrame()) is False
    assert isEmptyDf(pl.DataFrame()) is True


def testFrameWithColumnsButNoRowsIsNotValid() -> None:
    """스키마만 있고 행이 0 인 것도 데이터가 아니다."""

    empty = pl.DataFrame({"a": []})

    assert isValidDf(empty) is False
    assert isEmptyDf(empty) is True


def testFrameWithRowsIsValid() -> None:
    """행이 하나라도 있으면 유효하다."""

    assert isValidDf(pl.DataFrame({"a": [1]})) is True
    assert isEmptyDf(pl.DataFrame({"a": [1]})) is False


def testLazyFrameIsTreatedAsValidBecauseEmptinessNeedsCollect() -> None:
    """LazyFrame 은 collect 전에는 비었는지 알 수 없어 유효로 본다.

    `is_empty` 가 없는 객체를 유효로 두는 선택이다. 여기서 False 를 돌려주면 아직
    실행하지 않은 질의가 전부 빈 결과로 취급돼 조용히 버려진다.
    """

    lazy = pl.DataFrame({"a": [1]}).lazy()

    assert isValidDf(lazy) is True
    assert isEmptyDf(lazy) is False


@pytest.mark.parametrize(
    "value",
    [None, pl.DataFrame(), pl.DataFrame({"a": []}), pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [1]}).lazy()],
)
def testTheTwoJudgementsAreAlwaysExactOpposites(value: object) -> None:
    """둘은 서로의 부정이다. 대칭이 깨지면 호출부마다 다른 답을 받는다."""

    assert isValidDf(value) is not isEmptyDf(value)
