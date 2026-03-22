"""날짜 유틸리티 — 유연한 날짜 입력 파싱.

지원 포맷:
- "2024"        → start: 20240101, end: 20241231
- "2024-01"     → start: 20240101, end: 20240131
- "2024-01-15"  → 20240115
- "20240115"    → 20240115
- datetime      → YYYYMMDD
- None          → 기본값 적용
"""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, datetime


def _validateDate(year: int, month: int, day: int) -> None:
    """날짜 유효성 검증."""
    if not (1 <= month <= 12):
        raise ValueError(f"잘못된 월: {month} (1~12)")
    maxDay = monthrange(year, month)[1]
    if not (1 <= day <= maxDay):
        raise ValueError(f"잘못된 일: {year}-{month:02d}-{day} (최대 {maxDay}일)")


def parseDate(value: str | datetime | date | None, asEnd: bool = False) -> str | None:
    """유연한 날짜 → YYYYMMDD 변환.

    Parameters
    ----------
    value : str | datetime | date | None
        날짜 입력. None이면 None 반환.
    asEnd : bool
        True면 기간의 끝 날짜로 해석.
        - "2024" → "20241231"
        - "2024-06" → "20240630"

    Returns
    -------
    str | None
        YYYYMMDD 형식 문자열.
    """
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.strftime("%Y%m%d")

    s = str(value).strip()

    # YYYYMMDD (8자리 숫자)
    if re.match(r"^\d{8}$", s):
        return s

    # YYYY (4자리)
    if re.match(r"^\d{4}$", s):
        return f"{s}1231" if asEnd else f"{s}0101"

    # YYYY-MM 또는 YYYYMM (6자리)
    m = re.match(r"^(\d{4})-?(\d{1,2})$", s)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        if not (1 <= month <= 12):
            raise ValueError(f"잘못된 월: {month} (1~12)")
        if asEnd:
            lastDay = monthrange(year, month)[1]
            return f"{year:04d}{month:02d}{lastDay:02d}"
        return f"{year:04d}{month:02d}01"

    # YYYY-MM-DD 또는 YYYY-M-D (zero-pad 없어도 OK)
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        _validateDate(year, month, day)
        return f"{year:04d}{month:02d}{day:02d}"

    raise ValueError(
        f"날짜 형식을 인식할 수 없습니다: '{value}'. 지원: '2024', '2024-01', '2024-01-15', '20240115', datetime"
    )


def defaultStart() -> str:
    """기본 시작일: 1년 전 오늘."""
    now = datetime.now()
    try:
        oneYearAgo = now.replace(year=now.year - 1)
    except ValueError:
        # 2월 29일 → 2월 28일
        oneYearAgo = now.replace(year=now.year - 1, day=28)
    return oneYearAgo.strftime("%Y%m%d")


def defaultEnd() -> str:
    """기본 종료일: 오늘."""
    return datetime.now().strftime("%Y%m%d")
