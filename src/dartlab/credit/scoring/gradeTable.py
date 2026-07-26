"""[shim] credit/scoring/gradeTable → synth/creditGradeTable 본체 SSOT.

본체: src/dartlab/synth/creditGradeTable.py (L1.5)

20단계 신용등급 표는 도메인-중립 universal 표준 (credit/analysis/bond 공통).
SSOT 는 L1.5(synth), L2(credit) 는 본 shim 통해 호출 (L2↔L2 우회 방지).

신규 코드는 `from dartlab.synth.creditGradeTable import ...` 직접 호출 권장.
0.11 release 시 본 shim 제거 검토.
"""

from __future__ import annotations

from dartlab.synth.creditGradeTable import (  # noqa: F401
    estimatePD,
    gradeCategory,
    gradeRank,
    isInvestmentGrade,
    mapTo20Grade,
    notchGrade,
)

__all__ = [
    "estimatePD",
    "gradeCategory",
    "gradeRank",
    "isInvestmentGrade",
    "mapTo20Grade",
    "notchGrade",
]
