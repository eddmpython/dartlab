"""1 차 출처 deep-link 헬퍼 — Track A v1 (filing 단위).

Company.filings() 의 (period → rceptNo + dartUrl) 매핑을 만들어 ref payload 에 부착.
v1 은 page/line 단위 highlight 가 아닌 *filing 단위* — EvidenceChip 에서 DART 원문
viewer 외부 링크 click-through 까지만. line-level 은 v2 (raw HTML cache 도입 후).

reportType 패턴 (`분기보고서 (YYYY.MM)` · `반기보고서` · `사업보고서`) → 분기 매핑:
- 03 월 → Q1, 06 월 → Q2, 09 월 → Q3, 12 월 → Q4 (annual report).
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

_REPORT_RE = re.compile(r"\((\d{4})\.(\d{2})\)")
_MONTH_TO_QUARTER = {"03": "Q1", "06": "Q2", "09": "Q3", "12": "Q4"}


def buildPeriodToFiling(company: Any) -> dict[str, dict[str, Any]]:
    """company.filings() → {period(2024Q3) → {docId, sourcePath, reportType, rceptDate}}.

    실패 (filings 메서드 없음·빈 df) 시 빈 dict. ref 부착부는 KeyError 안 나도록 .get 으로 조회.
    """
    if not hasattr(company, "filings"):
        return {}
    try:
        df = company.filings()
    except Exception:
        return {}
    if not isinstance(df, pl.DataFrame) or df.height == 0:
        return {}
    needed = {"reportType", "rceptNo", "dartUrl"}
    if not needed <= set(df.columns):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in df.to_dicts():
        report = str(row.get("reportType") or "")
        period = str(row.get("period") or "")
        if re.fullmatch(r"\d{4}", period):
            period += "Q4"
        if not re.fullmatch(r"\d{4}Q[1-4]", period):
            match = _REPORT_RE.search(report)
            if not match or match.group(2) not in _MONTH_TO_QUARTER:
                continue
            period = match.group(1) + _MONTH_TO_QUARTER[match.group(2)]
        if period in out:
            continue
        out[period] = {
            "docId": str(row.get("rceptNo") or ""),
            "sourcePath": str(row.get("dartUrl") or ""),
            "reportType": report,
            "rceptDate": str(row.get("rceptDate") or ""),
        }
        if period.endswith("Q4"):
            out[period[:4] + "FY"] = out[period]
    return out


def attachDocRef(payload: dict[str, Any], period: str, filingMap: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """payload 에 docId/sourcePath/reportType/rceptDate 키 부착 (있는 경우만).

    Track A 표준 키 — Ref.payload docstring 정의 와 일치. page/lineStart/lineEnd 는 v2
    (raw HTML cache 도입 후) 에 추가, v1 은 filing 단위 까지만.
    """
    filing = filingMap.get(period)
    if not filing:
        return payload
    out = dict(payload)
    out["docId"] = filing["docId"]
    out["sourcePath"] = filing["sourcePath"]
    out["reportType"] = filing["reportType"]
    out["rceptDate"] = filing["rceptDate"]
    return out


__all__ = ["buildPeriodToFiling", "attachDocRef"]
