"""스크린 조건의 3상태 판정과 설명 결과를 만드는 순수 의미 모듈.

데이터 로딩은 ``scan.builders``가 맡고, 이 모듈은 값과 조건만 받아
PASS/FAIL/UNKNOWN을 판정한다. 브라우저 ``scan/verdict.ts``와 공유하는
의미 계약이며 결측을 실패나 통과로 위장하지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Any, Literal

Verdict = Literal["PASS", "FAIL", "UNKNOWN"]


def hasValue(value: Any) -> bool:
    """``None``, 비유한 수, 빈 문자열을 결측으로 판정한다."""
    if value is None:
        return False
    if isinstance(value, float) and not isfinite(value):
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def evaluateValue(value: Any, condition: Mapping[str, Any], *, kind: str = "number") -> Verdict:
    """단일 값과 조건을 PASS/FAIL/UNKNOWN으로 판정한다."""
    op = str(condition.get("op", "=="))
    present = hasValue(value)
    if op == "exists":
        return "PASS" if present else "FAIL"
    if op == "not_exists":
        return "FAIL" if present else "PASS"
    if not present or "value" not in condition:
        return "UNKNOWN"

    expected = condition.get("value")
    try:
        if kind == "number":
            actualNumber = _number(value)
            if actualNumber is None:
                return "UNKNOWN"
            if op == "between":
                if not isinstance(expected, (list, tuple)) or len(expected) != 2:
                    return "UNKNOWN"
                passed = float(expected[0]) <= actualNumber <= float(expected[1])
            else:
                target = float(expected)
                passed = {
                    ">": actualNumber > target,
                    ">=": actualNumber >= target,
                    "<": actualNumber < target,
                    "<=": actualNumber <= target,
                    "==": actualNumber == target,
                    "!=": actualNumber != target,
                }.get(op)
                if passed is None:
                    return "UNKNOWN"
        else:
            actualText = str(value)
            expectedText = str(expected)
            if op == "contains":
                passed = expectedText in actualText
            elif op == "==":
                passed = actualText == expectedText
            elif op == "!=":
                passed = actualText != expectedText
            elif op == "in":
                passed = isinstance(expected, (list, tuple, set)) and actualText in {str(v) for v in expected}
            else:
                return "UNKNOWN"
    except (TypeError, ValueError, OverflowError):
        return "UNKNOWN"
    return "PASS" if passed else "FAIL"


def summarizeVerdicts(
    rows: Iterable[Mapping[str, Any]],
    conditions: list[Mapping[str, Any]],
    *,
    kinds: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """종목별 필드 행에서 coverage, funnel, near miss를 만든다."""
    kinds = kinds or {}
    materialized = [dict(row) for row in rows]
    rowResults: list[dict[str, Any]] = []
    for row in materialized:
        verdicts = []
        for condition in conditions:
            alternatives = condition.get("alternatives")
            if isinstance(alternatives, list):
                alternativeVerdicts = [
                    evaluateValue(
                        row.get(str(alternative.get("field", ""))),
                        alternative,
                        kind=kinds.get(str(alternative.get("field", "")), "number"),
                    )
                    for alternative in alternatives
                ]
                if "PASS" in alternativeVerdicts:
                    verdicts.append("PASS")
                elif "UNKNOWN" in alternativeVerdicts:
                    verdicts.append("UNKNOWN")
                else:
                    verdicts.append("FAIL")
            else:
                field = str(condition.get("field", ""))
                verdicts.append(evaluateValue(row.get(field), condition, kind=kinds.get(field, "number")))
        rowResults.append(
            {
                "stockCode": str(row.get("stockCode") or ""),
                "verdicts": verdicts,
                "passCount": verdicts.count("PASS"),
                "failCount": verdicts.count("FAIL"),
                "unknownCount": verdicts.count("UNKNOWN"),
            }
        )

    coverage = []
    funnel = []
    for index, condition in enumerate(conditions):
        verdictColumn = [row["verdicts"][index] for row in rowResults]
        valid = sum(value != "UNKNOWN" for value in verdictColumn)
        survivors = sum(all(value == "PASS" for value in row["verdicts"][: index + 1]) for row in rowResults)
        coverage.append(
            {
                "field": str(condition.get("field", "__any__")),
                "valid": valid,
                "missing": len(rowResults) - valid,
                "total": len(rowResults),
                "ratio": round(valid / len(rowResults), 4) if rowResults else 0.0,
            }
        )
        funnel.append(
            {
                "condition": dict(condition),
                "pass": verdictColumn.count("PASS"),
                "fail": verdictColumn.count("FAIL"),
                "unknown": verdictColumn.count("UNKNOWN"),
                "survivors": survivors,
            }
        )

    memberCodes = [row["stockCode"] for row in rowResults if row["failCount"] == 0 and row["unknownCount"] == 0]
    nearMissCodes = [row["stockCode"] for row in rowResults if row["failCount"] == 1 and row["unknownCount"] == 0]
    return {
        "universe": len(rowResults),
        "memberCodes": memberCodes,
        "memberCount": len(memberCodes),
        "excluded": {
            "failed": sum(row["failCount"] > 0 for row in rowResults),
            "missingOnly": sum(row["failCount"] == 0 and row["unknownCount"] > 0 for row in rowResults),
        },
        "coverage": coverage,
        "funnel": funnel,
        "nearMissCodes": nearMissCodes if len(conditions) > 1 else [],
    }


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.replace(",", "").replace("%", "").replace("배", "").strip()
    number = float(value)
    return number if isfinite(number) else None


__all__ = ["Verdict", "evaluateValue", "hasValue", "summarizeVerdicts"]
