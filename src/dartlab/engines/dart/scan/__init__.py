"""DART 전수 스캔 엔진 — 상장사 전체를 축별로 분석.

가용 축:
    network     — 관계 네트워크 (출자/지분/계열)
    governance  — 지배구조 (지분율, 사외이사, 보수비율, 감사의견)
    workforce   — 인력/급여 (직원수, 평균급여, 성장률, 고액보수)
    capital     — 주주환원 (배당, 자사주, 증자/감자)
    debt        — 부채 구조 (사채만기, 부채비율, ICR, 위험등급)
"""

from __future__ import annotations

from dartlab.engines.dart.scan.payload import (  # noqa: F401
    build_scan_payload,
    build_unified_payload,
)


def available_scans() -> list[str]:
    """가용한 scan 축 목록."""
    return ["network", "governance", "workforce", "capital", "debt", "signal"]
