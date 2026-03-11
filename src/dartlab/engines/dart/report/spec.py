"""dart/report 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """dart/report 엔진 스펙 반환."""
    from dartlab.engines.dart.report.types import API_TYPE_LABELS, API_TYPES

    return {
        "name": "dart.report",
        "description": "DART 정기보고서 API 데이터 (배당, 직원, 임원 등)",
        "summary": {
            "apiTypes": len(API_TYPES),
            "keyModules": ["dividend", "employee", "majorHolder", "executive", "auditOpinion"],
        },
        "detail": {
            "apiTypes": {t: API_TYPE_LABELS.get(t, t) for t in API_TYPES},
        },
    }
