"""gather/bulkData/dateKey.py 미러 . HF 벌크 날짜 키 파싱 규칙."""

from __future__ import annotations

from datetime import date

import pytest

from dartlab.gather.bulkData.dateKey import parseDateKey

pytestmark = pytest.mark.unit


def test_parsesHyphenAndCompactAndYear() -> None:
    """세 표기가 같은 규칙으로 date 로 좁혀진다."""
    assert parseDateKey("2024-03-05") == date(2024, 3, 5)
    assert parseDateKey("20240305") == date(2024, 3, 5)
    assert parseDateKey("2024") == date(2024, 1, 1)


def test_passesDateThrough() -> None:
    """date 는 그대로 돌려준다."""
    value = date(1999, 12, 31)
    assert parseDateKey(value) is value


def test_ignoresSurroundingSpace() -> None:
    """앞뒤 공백은 무시한다."""
    assert parseDateKey("  2024-03-05  ") == date(2024, 3, 5)


def test_rejectsUnparsableValue() -> None:
    """알아볼 수 없으면 대체값 없이 끝낸다."""
    with pytest.raises(ValueError):
        parseDateKey("24-3")


def test_bulkModulesShareOneRule() -> None:
    """가격 벌크와 지수 벌크가 같은 함수 객체를 본다."""
    from dartlab.gather.bulkData import hfBulk, hfIndexBulk

    assert hfBulk.parseDateKey is parseDateKey
    assert hfIndexBulk.parseDateKey is parseDateKey
