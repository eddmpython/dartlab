"""검색 엔진 공용 강제변환 헬퍼 (SSOT).

`search/` 안 여러 모듈이 본문까지 똑같은 소형 헬퍼 (비율·정수·불리언·환경 플래그·
이름 키·날짜 서수·정기보고서명) 를 각자 복제하고 있었다. 한쪽만 고쳐지고 다른 쪽은
남는 표류를 막으려고 정의를 이 모듈 한 자리로 모은다. 전부 부작용 없는 순수 함수라
호출부의 의미는 이전과 같다.

호출부는 `from dartlab.providers.dart.search.coerce import _int` 처럼 필요한 것만
가져온다. 새 강제변환 헬퍼도 두 모듈 이상이 쓰게 되면 여기로 올린다.
"""

from __future__ import annotations

import os
from typing import Any


def _ratio(numerator: float, denominator: int) -> float:
    """분자/분모 비율. 분모가 0 이하면 0 나눗셈 대신 0.0."""
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _int(value: Any, default: int) -> int:
    """정수 강제변환. 변환 불가면 `default`."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _asBool(value: Any, *, default: bool) -> bool:
    """불리언 강제변환. None/빈 문자열은 `default`, 거짓 문자열 집합만 False."""
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "n"}
    return bool(value)


def _isFalse(value: Any) -> bool:
    """명시적 거짓 판정. None/빈 문자열은 판정 보류라 False."""
    if isinstance(value, bool):
        return not value
    if value in (None, ""):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no", "n"}
    return not bool(value)


def _envFlag(name: str, *, default: bool) -> bool:
    """환경변수 on/off 판독. 미설정·빈 값은 `default`."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "n"}


def _nameKey(value: Any) -> str:
    """회사명 대조 키. 소문자화 + 괄호·법인 접두어·구두점 제거."""
    text = str(value or "").strip().lower()
    removable = set(" \t\r\n()[]{}㈜주식회사,.-_")
    return "".join(ch for ch in text if ch not in removable)


def _dateOrdinal(value: Any) -> int:
    """YYYYMMDD 문자열을 비교용 정수로. 8 자리 숫자가 아니면 0."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())[:8]
    if len(digits) != 8:
        return 0
    try:
        year = int(digits[:4])
        month = int(digits[4:6])
        day = int(digits[6:8])
    except ValueError:
        return 0
    return year * 372 + month * 31 + day


def _periodToReportName(period: str) -> str:
    """panel period(YYYYQn) → DART 정기보고서명 추정."""
    if not period:
        return ""
    if period.endswith("Q4"):
        return "사업보고서"
    if period.endswith("Q2"):
        return "반기보고서"
    if period.endswith("Q1") or period.endswith("Q3"):
        return "분기보고서"
    return period
