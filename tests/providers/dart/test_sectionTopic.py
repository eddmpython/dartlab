"""providers/dart/sectionTopic.py 물류부문 영업설비 패턴 회귀.

예전 패턴 ``(?:(?:\\[.+?\\]|\\(.+?\\))\\s*)*`` 는 괄호 접두 토큰 분할이 지수적으로 늘어 ReDoS 였다
(CodeQL py/redos). 토큰 내용에서 자기 닫는 괄호를 뺀 선형 패턴으로 바꾼 뒤에도 현실적인 제목은 그대로
매칭되는지, 병적인 입력이 즉시 끝나는지 고정한다.
"""

from __future__ import annotations

import time

import pytest

pytestmark = pytest.mark.unit

_LOGISTICS_MARK = "물류부문영업설비현황"
# 예전 패턴이면 "[" + "a][" * 26 한 건에 수 초가 걸린다(2 회 늘 때마다 약 4 배). 새 패턴은 수십 마이크로초.
_FAST_SECONDS = 0.5


def _logisticsPattern():
    from dartlab.providers.dart.sectionTopic import _PATTERN_MAPPINGS

    return next(pattern for pattern, _topic in _PATTERN_MAPPINGS if _LOGISTICS_MARK in pattern.pattern)


@pytest.mark.parametrize(
    "title",
    [
        "해외생산설비현황(상세)",
        "물류부문영업설비현황(국내)",
        "물류부문영업설비현황(국외)",
        "물류부문영업설비현황(해외)",
        "[물류부문]물류부문영업설비현황(국내)",
        "(가)물류부문영업설비현황(국외)",
        "[A사][B사]물류부문영업설비현황(해외)",
        "[국내](상세)물류부문영업설비현황(국내)",
        "[주요종속회사(A사)]물류부문영업설비현황(국내)",
        "[(주)한진]물류부문영업설비현황(국내)",
        "(물류[국내])물류부문영업설비현황(국내)",
        "[상세] 물류부문영업설비현황(국내)",
    ],
)
def test_logistics_pattern_matches_realistic_titles(title: str) -> None:
    """괄호 접두가 평평하거나 다른 종류 괄호만 품은 제목은 예전처럼 매칭된다."""
    assert _logisticsPattern().match(title) is not None


@pytest.mark.parametrize(
    "title",
    [
        "물류부문영업설비현황(기타)",
        "물류부문영업설비현황",
        "해외생산설비현황",
        "물류부문영업설비현황(국내)(상세)",
        "(주)한진물류부문영업설비현황(국내)",
        "[]물류부문영업설비현황(국내)",
        "()물류부문영업설비현황(국내)",
        "[국내물류부문영업설비현황(국내)",
    ],
)
def test_logistics_pattern_rejects_other_titles(title: str) -> None:
    """예전에도 매칭되지 않던 제목은 계속 매칭되지 않는다."""
    assert _logisticsPattern().match(title) is None


@pytest.mark.parametrize(
    "title",
    [
        "[[국내]]물류부문영업설비현황(국내)",
        "((주)한진)물류부문영업설비현황(국내)",
        "[a]b]물류부문영업설비현황(국내)",
        "(a)b)물류부문영업설비현황(국내)",
    ],
)
def test_logistics_pattern_drops_same_type_nesting(title: str) -> None:
    """의도된 변경: 같은 종류 괄호 중첩이나 짝 없는 닫는 괄호가 접두에 든 제목은 더는 매칭하지 않는다.

    예전 ``.+?`` 는 backtracking 으로 닫는 괄호까지 내용에 삼켜 이런 제목을 받아들였다. 그 여지가 곧 ReDoS 의
    원인이라 함께 사라졌다.
    """
    assert _logisticsPattern().match(title) is None


@pytest.mark.parametrize(
    "title",
    [
        "[" + "a][" * 26,
        "(" + "a)(" * 26,
        "[a]" * 26 + "물류부문영업설비현황(기타)",
    ],
)
def test_logistics_pattern_is_linear_on_pathological_input(title: str) -> None:
    """괄호 토큰을 길게 늘인 입력도 즉시 끝난다 (예전 패턴은 지수 시간)."""
    pattern = _logisticsPattern()
    started = time.perf_counter()
    assert pattern.match(title) is None
    assert time.perf_counter() - started < _FAST_SECONDS


def test_map_section_title_routes_logistics_titles() -> None:
    """정규화(공백 제거) 뒤 mapSectionTitle 경로에서도 rawMaterial 로 간다."""
    from dartlab.providers.dart.sectionTopic import mapSectionTitle

    assert mapSectionTitle("[물류부문] 물류부문 영업설비 현황(국내)") == "rawMaterial"
    assert mapSectionTitle("해외생산설비 현황(상세)") == "rawMaterial"


def test_map_section_title_pathological_title_is_fast() -> None:
    """병적인 제목이 전체 패턴 목록을 거쳐도 빨리 끝나고 매핑 없이 정규화 문자열로 돌아온다."""
    from dartlab.providers.dart.sectionTopic import mapSectionTitle, normalizeSectionTitle

    title = "[" + "a][" * 26
    started = time.perf_counter()
    result = mapSectionTitle(title)
    assert time.perf_counter() - started < _FAST_SECONDS
    assert result == normalizeSectionTitle(title)
