"""렌즈 산출물의 시간 표기를 해석하고 knowledge boundary 와 견준다.

여기 있는 것은 "언제" 하나만 다룬다. 계약 검증 본체(`lensContract`)는 구조와 필수 필드를 보고,
시간 판정은 전부 이 모듈에 맡긴다. 시간 표기는 날짜와 회계 기간이 섞여 들어와 규칙이 따로
자라기 때문에, 한 파일에 두면 계약 검증 쪽 변경이 시간 규칙을 건드리게 된다.

핵심 구분은 하나다. 값이 "언제 알았나"(시점)인지 "어디까지 담았나"(범위)인지. 시점은 그
자체로 비교하고, 범위는 시작으로 비교한다. 범위를 끝으로 비교하면 진행 중인 기간을 부분
수집한 지극히 정상적인 결과가 미래를 봤다고 걸린다.
"""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, datetime
from typing import Any


def _validateTime(time: dict[str, Any]) -> None:
    for key in ("asOf", "period", "knowledgeBoundary"):
        value = time.get(key)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"lens product time.{key} 는 문자열 또는 None 이어야 합니다.")
    dataAsOf = time.get("dataAsOf")
    if dataAsOf is not None and not isinstance(dataAsOf, (str, dict)):
        raise TypeError("lens product time.dataAsOf 는 문자열, dict 또는 None 이어야 합니다.")

    asOf = _isoDate(time.get("asOf"), path="time.asOf")
    knowledgeBoundary = _isoDate(time.get("knowledgeBoundary"), path="time.knowledgeBoundary")
    if asOf is not None and knowledgeBoundary is not None and asOf > knowledgeBoundary:
        raise ValueError("lens product asOf 는 knowledgeBoundary 이후일 수 없습니다.")
    dataDates = _dataAsOfDates(dataAsOf)
    if knowledgeBoundary is not None and any(value > knowledgeBoundary for value in dataDates):
        raise ValueError("lens product dataAsOf 는 knowledgeBoundary 이후일 수 없습니다.")


def _isoDate(value: Any, *, path: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError(f"lens product {path} 는 YYYY-MM-DD 형식이어야 합니다.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"lens product {path} 는 유효한 YYYY-MM-DD 날짜여야 합니다.") from exc


def _temporalUpperBound(value: str) -> date | None:
    """날짜와 회계 기간 표기를 비교 가능한 마지막 날짜로 정규화한다."""
    normalized = value.strip().upper()
    if not normalized:
        return None

    isoMatch = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?", normalized
    )
    if isoMatch:
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    compactDate = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", normalized)
    if compactDate:
        try:
            return date(*(int(part) for part in compactDate.groups()))
        except ValueError:
            return None

    quarter = re.fullmatch(r"(\d{4})\s*[-./ ]?\s*Q([1-4])", normalized)
    if quarter is None:
        quarter = re.fullmatch(r"(\d{4})년\s*([1-4])분기", normalized)
    if quarter:
        year, quarterNumber = (int(part) for part in quarter.groups())
        month = quarterNumber * 3
        return date(year, month, monthrange(year, month)[1])

    half = re.fullmatch(r"(\d{4})\s*[-./ ]?\s*H([12])", normalized)
    if half:
        year, halfNumber = (int(part) for part in half.groups())
        month = halfNumber * 6
        return date(year, month, monthrange(year, month)[1])

    monthMatch = re.fullmatch(r"(\d{4})[-./](\d{1,2})", normalized)
    if monthMatch is None:
        monthMatch = re.fullmatch(r"(\d{4})(\d{2})", normalized)
    if monthMatch:
        year, month = (int(part) for part in monthMatch.groups())
        if 1 <= month <= 12:
            return date(year, month, monthrange(year, month)[1])
        return None

    yearMatch = re.fullmatch(r"(?:FY)?(\d{4})(?:FY)?", normalized)
    if yearMatch:
        return date(int(yearMatch.group(1)), 12, 31)
    return None


# 값이 "언제 알았나"(시점)를 뜻하는 키. 그 시점이 knowledge boundary 뒤면 look-ahead 다.
_INSTANT_KEYS = frozenset(
    {"date", "dataasof", "observedat", "retrievedat", "sourcedataasof", "marketasof", "financialasof"}
)

# 값이 "어디까지 담았나"(범위)를 뜻하는 키. 회계 기간 표기가 들어온다.
#
# 범위는 시점처럼 다루면 안 된다. `latestPeriod: "2026"` 을 2026-12-31 로 읽으면, 2026 년
# 7 월에 2026 년 반기까지 받은 지극히 정상적인 결과가 "미래 자료를 봤다"로 걸린다. 실제로
# `Company.analysis("종합평가")` 가 그 이유로 통째로 죽고 있었다.
#
# 범위에서 look-ahead 는 그 기간이 *시작하기도 전*에 담았다고 할 때 생긴다. 그래서 끝이
# 아니라 시작으로 잰다. `latestPeriod: "2027"` 은 2027-01-01 이 경계보다 뒤라 그대로 걸린다.
_COVERAGE_KEYS = frozenset({"latestperiod"})


def _temporalLowerBound(value: str) -> date | None:
    """기간 표기를 그 기간이 시작하는 날로 정규화한다. 날짜는 그대로 둔다.

    범위형 값의 look-ahead 판정에 쓴다. 기간이 경계보다 늦게 시작했으면 그 자료는 아직
    존재할 수 없다. 반대로 이미 시작한 기간을 부분적으로 담는 것은 정상이라 걸리면 안 된다.
    """
    upper = _temporalUpperBound(value)
    if upper is None:
        return None
    normalized = value.strip().upper()
    if re.fullmatch(r"(?:FY)?(\d{4})(?:FY)?", normalized):
        return date(upper.year, 1, 1)
    if re.fullmatch(r"(\d{4})\s*[-./ ]?\s*Q[1-4]", normalized) or re.fullmatch(r"(\d{4})년\s*[1-4]분기", normalized):
        return date(upper.year, upper.month - 2, 1)
    if re.fullmatch(r"(\d{4})\s*[-./ ]?\s*H[12]", normalized):
        return date(upper.year, upper.month - 5, 1)
    if re.fullmatch(r"(\d{4})[-./](\d{1,2})", normalized) or re.fullmatch(r"(\d{4})(\d{2})", normalized):
        return date(upper.year, upper.month, 1)
    return upper


def _dataAsOfDates(value: Any) -> list[date]:
    if isinstance(value, str):
        parsed = _temporalUpperBound(value)
        if parsed is None:
            raise ValueError("lens product dataAsOf 시간 형식을 해석할 수 없습니다.")
        return [parsed]
    if not isinstance(value, dict):
        return []
    dates: list[date] = []
    temporalKeys = _INSTANT_KEYS | _COVERAGE_KEYS
    foundTemporalValue = False
    for key, raw in value.items():
        if str(key).lower() not in temporalKeys or raw is None or raw == "":
            continue
        foundTemporalValue = True
        if not isinstance(raw, str):
            raise ValueError(f"lens product dataAsOf.{key} 는 문자열이어야 합니다.")
        isCoverage = str(key).lower() in _COVERAGE_KEYS
        parsed = _temporalLowerBound(raw) if isCoverage else _temporalUpperBound(raw)
        if parsed is None:
            raise ValueError(f"lens product dataAsOf.{key} 시간 형식을 해석할 수 없습니다.")
        dates.append(parsed)
    if value and not foundTemporalValue:
        raise ValueError("lens product dataAsOf dict에 해석 가능한 시간 필드가 없습니다.")
    return dates
