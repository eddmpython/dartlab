"""providers/dart/search/coerce.py mirror tests.

search/ 여러 모듈이 복제하고 있던 소형 강제변환 헬퍼를 한 자리로 모은 모듈이다.
여기서는 경계값 계약 (0 분모·변환 불가·빈 문자열·미설정 환경변수) 을 못박고,
호출부들이 같은 함수 객체를 보는지 (사본 재발생 회귀) 까지 확인한다.
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.search.coerce import (
    _asBool,
    _dateOrdinal,
    _envFlag,
    _int,
    _isFalse,
    _nameKey,
    _periodToReportName,
    _ratio,
)

pytestmark = pytest.mark.unit


def test_ratio_guards_zero_and_negative_denominator() -> None:
    """분모가 0 이하면 나눗셈 대신 0.0."""
    assert _ratio(3, 4) == 0.75
    assert _ratio(3, 0) == 0.0
    assert _ratio(3, -2) == 0.0
    assert isinstance(_ratio(1, 2), float)


def test_int_falls_back_on_unconvertible() -> None:
    """정수로 못 바꾸는 값은 default."""
    assert _int("12", 0) == 12
    assert _int(" 12 ", 0) == 12
    assert _int(3.9, 0) == 3
    assert _int("12.7", -1) == -1
    assert _int(None, 7) == 7
    assert _int([], 7) == 7


def test_asBool_treats_empty_as_default() -> None:
    """None 과 빈 문자열은 판단 보류라 default, 거짓 문자열만 False."""
    assert _asBool(True, default=False) is True
    assert _asBool(None, default=True) is True
    assert _asBool("", default=False) is False
    assert _asBool("false", default=True) is False
    assert _asBool(" NO ", default=True) is False
    assert _asBool("yes", default=False) is True
    assert _asBool(0, default=True) is False


def test_isFalse_only_for_explicit_falsehood() -> None:
    """None/빈 문자열은 거짓 단정 대상이 아니다."""
    assert _isFalse(False) is True
    assert _isFalse(None) is False
    assert _isFalse("") is False
    assert _isFalse("0") is True
    assert _isFalse(" False ") is True
    assert _isFalse("yes") is False
    assert _isFalse(0) is True


def test_envFlag_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """미설정·빈 값은 default, 거짓 문자열만 False."""
    name = "DARTLAB_TEST_COERCE_FLAG"
    monkeypatch.delenv(name, raising=False)
    assert _envFlag(name, default=True) is True
    assert _envFlag(name, default=False) is False
    monkeypatch.setenv(name, "")
    assert _envFlag(name, default=True) is True
    monkeypatch.setenv(name, "0")
    assert _envFlag(name, default=True) is False
    monkeypatch.setenv(name, " No ")
    assert _envFlag(name, default=True) is False
    monkeypatch.setenv(name, "on")
    assert _envFlag(name, default=False) is True


def test_nameKey_strips_corporate_decoration() -> None:
    """법인 접두어·괄호·구두점·공백을 지운 대조 키."""
    assert _nameKey("㈜삼성전자") == "삼성전자"
    assert _nameKey(" 주식회사 카카오 ") == "카카오"
    assert _nameKey("SK-Hynix (Co.)") == "skhynixco"
    assert _nameKey(None) == ""
    assert _nameKey("") == ""


def test_dateOrdinal_needs_eight_digits() -> None:
    """8 자리 숫자만 서수로. 나머지는 0."""
    assert _dateOrdinal("20240315") == 2024 * 372 + 3 * 31 + 15
    assert _dateOrdinal("2024-03-15") == _dateOrdinal("20240315")
    assert _dateOrdinal("2024031") == 0
    assert _dateOrdinal(None) == 0
    assert _dateOrdinal("") == 0
    assert _dateOrdinal("20240315999") == _dateOrdinal("20240315")


def test_dateOrdinal_orders_dates_monotonically() -> None:
    """서수는 날짜 순서를 보존한다."""
    assert _dateOrdinal("20240101") < _dateOrdinal("20240201") < _dateOrdinal("20250101")


def test_periodToReportName_maps_quarters() -> None:
    """panel period 를 DART 정기보고서명으로."""
    assert _periodToReportName("2024Q4") == "사업보고서"
    assert _periodToReportName("2024Q2") == "반기보고서"
    assert _periodToReportName("2024Q1") == "분기보고서"
    assert _periodToReportName("2024Q3") == "분기보고서"
    assert _periodToReportName("") == ""
    assert _periodToReportName("2024") == "2024"


def test_call_sites_share_one_definition() -> None:
    """호출부가 사본이 아니라 이 모듈의 같은 함수 객체를 본다 (중복 재발 가드)."""
    from dartlab.providers.dart.search import (
        answerability,
        canaryPack,
        catalog,
        entityGraph,
        entityGraphCatalog,
        fieldIndexRebuild,
        memoryCard,
        ngramIndex,
        pipeline,
        qualityGate,
        resultContract,
        resultSchema,
        semanticConstraints,
        unified,
    )

    assert canaryPack._ratio is _ratio
    assert qualityGate._ratio is _ratio
    assert resultContract._ratio is _ratio
    assert canaryPack._int is _int
    assert catalog._int is _int
    assert pipeline._int is _int
    assert canaryPack._asBool is _asBool
    assert resultSchema._asBool is _asBool
    assert answerability._isFalse is _isFalse
    assert memoryCard._isFalse is _isFalse
    assert entityGraphCatalog._envFlag is _envFlag
    assert fieldIndexRebuild._envFlag is _envFlag
    assert entityGraph._nameKey is _nameKey
    assert entityGraphCatalog._nameKey is _nameKey
    assert semanticConstraints._dateOrdinal is _dateOrdinal
    assert unified._dateOrdinal is _dateOrdinal
    assert fieldIndexRebuild._periodToReportName is _periodToReportName
    assert ngramIndex._periodToReportName is _periodToReportName
