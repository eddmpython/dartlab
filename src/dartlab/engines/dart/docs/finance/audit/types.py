"""감사의견 모듈 결과 타입."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass
class AuditResult:
    """감사의견 + 감사보수 시계열 결과.

    Attributes:
        corpName: 기업명.
        nYears: 데이터 연도 수.
        opinionDf: 감사의견 시계열 (year, auditor, opinion, keyAuditMatters).
        feeDf: 감사보수 시계열 (year, auditor, contractFee, contractHours, actualFee, actualHours).
            보수 단위는 백만원.
    """

    corpName: str | None = None
    nYears: int = 0
    opinionDf: pl.DataFrame | None = None
    feeDf: pl.DataFrame | None = None
