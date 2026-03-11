"""period 포맷 표준화.

모든 시장(KR/US/CN/JP)의 분기 period를 통일된 형식으로 생성/파싱.

표준 포맷: YYYY-QN (예: "2024-Q1", "2024-Q4")
연도 포맷: YYYY (예: "2024")
"""

from __future__ import annotations


def formatPeriod(year: str | int, quarter: int) -> str:
    """연도 + 분기 → 표준 period 문자열.

    Args:
        year: 연도 (문자열 또는 정수)
        quarter: 분기 (1~4)

    Returns:
        "YYYY-QN" 형식 문자열.
    """
    return f"{year}-Q{quarter}"


def parsePeriod(period: str) -> tuple[str, int]:
    """period 문자열 → (연도, 분기).

    "2024-Q1" → ("2024", 1)
    "2024_Q1" → ("2024", 1)  (하위호환)

    Args:
        period: "YYYY-QN" 또는 "YYYY_QN" 형식.

    Returns:
        (연도 문자열, 분기 정수).
    """
    sep = "-" if "-" in period else "_"
    parts = period.split(sep, 1)
    year = parts[0]
    quarter = int(parts[1].replace("Q", ""))
    return year, quarter


def extractYear(period: str) -> str:
    """period에서 연도만 추출.

    "2024-Q1" → "2024"
    "2024_Q1" → "2024"  (하위호환)
    """
    sep = "-" if "-" in period else "_"
    return period.split(sep, 1)[0]
