"""이슈 자동 탐지 휴리스틱 — 감사 결과에서 문제 식별."""

from __future__ import annotations

from typing import Any


def detectIssues(
    rows: list[dict[str, Any]],
    *,
    coverageThreshold: float = 0.5,
) -> list[dict[str, Any]]:
    """parquet row 리스트에서 이슈를 자동 탐지한다.

    Args:
        rows: auditOne()이 생성한 row 리스트.
        coverageThreshold: 이 비율 미만이면 coverage 이슈.

    Returns:
        이슈 dict 리스트.
    """
    issues: list[dict[str, Any]] = []

    if not rows:
        return issues

    # ── 축별 coverage 계산 ──
    axisCounts: dict[str, dict[str, int]] = {}
    for row in rows:
        axis = row.get("axis", "")
        if not axis:
            continue
        if axis not in axisCounts:
            axisCounts[axis] = {"total": 0, "ok": 0, "none": 0, "error": 0}
        axisCounts[axis]["total"] += 1
        status = row.get("status", "")
        if status in axisCounts[axis]:
            axisCounts[axis][status] += 1

    # ── 축별 coverage 이슈 ──
    for axis, counts in axisCounts.items():
        total = counts["total"]
        ok = counts["ok"]
        if total == 0:
            continue
        rate = ok / total
        if rate < coverageThreshold:
            severity = "critical" if rate == 0 else "warning"
            issues.append({
                "category": "quality",
                "severity": severity,
                "axis": axis,
                "blockKey": "",
                "description": f"{axis} coverage {rate:.0%} ({ok}/{total})",
            })

    # ── 전체 error 비율 ──
    totalRows = len(rows)
    errorRows = sum(1 for r in rows if r.get("status") == "error")
    if totalRows > 0 and errorRows / totalRows > 0.2:
        issues.append({
            "category": "calcError",
            "severity": "critical",
            "axis": "",
            "blockKey": "",
            "description": f"전체 error 비율 {errorRows}/{totalRows} ({errorRows/totalRows:.0%})",
        })

    return issues
