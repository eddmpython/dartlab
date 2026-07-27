"""historicalContext 헬퍼 — NBER 침체 + 시계열 변화량/YoY.

macro/corporate/historicalContext.py 가 1019 줄 god module 이라 헬퍼 분리.
identity 보존을 위해 historicalContext.py 가 본 모듈에서 re-export 한다.

상수:
- _NBER_RECESSIONS — 미국 NBER 침체 6 기간 (1980-2020)

함수:
- _isRecession(month) — month 가 NBER 침체 중인지
- _monthsToNextRecession(month) — 다음 침체 시작까지 개월 수
- _deltaN(d, n) — N 개월 전 대비 변화량
- _yoy(d) — YoY 변화율 dict
"""

from __future__ import annotations

_NBER_RECESSIONS: list[tuple[str, str]] = [
    ("1980-01", "1980-07"),
    ("1981-07", "1982-11"),
    ("1990-07", "1991-03"),
    ("2001-03", "2001-11"),
    ("2007-12", "2009-06"),
    ("2020-02", "2020-04"),
]


def _isRecession(month: str) -> bool:
    """month (YYYY-MM) 가 NBER 침체 중인지 판별."""
    for start, end in _NBER_RECESSIONS:
        if start <= month <= end:
            return True
    return False


def _monthsToNextRecession(month: str) -> int:
    """다음 침체 시작까지 남은 개월 수. 침체 중이면 0. 이후 침체 없으면 999."""
    if _isRecession(month):
        return 0
    for start, _ in _NBER_RECESSIONS:
        if month < start:
            y1, m1 = int(month[:4]), int(month[5:7])
            y2, m2 = int(start[:4]), int(start[5:7])
            return (y2 - y1) * 12 + (m2 - m1)
    return 999


def _deltaN(d: dict[str, float], n: int = 3) -> dict[str, float]:
    """N개월 전 대비 변화량."""
    months = sorted(d.keys())
    idx = {m: i for i, m in enumerate(months)}
    result: dict[str, float] = {}
    for m in months:
        i = idx[m]
        if i >= n:
            result[m] = d[m] - d[months[i - n]]
    return result


def _yoy(d: dict[str, float]) -> dict[str, float]:
    """YoY 변화율 (%)."""
    result: dict[str, float] = {}
    for m, v in d.items():
        y, mo = int(m[:4]), int(m[5:7])
        prev = f"{y - 1:04d}-{mo:02d}"
        if prev in d and abs(d[prev]) > 1e-10:
            result[m] = ((v - d[prev]) / abs(d[prev])) * 100
    return result


__all__ = [
    "_NBER_RECESSIONS",
    "_deltaN",
    "_isRecession",
    "_monthsToNextRecession",
    "_yoy",
]
