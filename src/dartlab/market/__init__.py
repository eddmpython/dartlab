"""시장 전체 조회/분석 엔진.

Company = 기업 하나. Market = 기업 밖 전부.

가용 축:
    network     — 관계 네트워크 (출자/지분/계열)
    governance  — 지배구조 (지분율, 사외이사, 보수비율, 감사의견)
    workforce   — 인력/급여 (직원수, 평균급여, 성장률, 고액보수)
    capital     — 주주환원 (배당, 자사주, 증자/감자)
    debt        — 부채 구조 (사채만기, 부채비율, ICR, 위험등급)
    signal      — 서술형 공시 시장 시그널 (키워드 트렌드)
    screen      — 전 종목 스크리닝 (향후 analysis/rank에서 이전)
"""

from __future__ import annotations

from dartlab.market.payload import (  # noqa: F401
    build_scan_payload,
    build_unified_payload,
)
from dartlab.market.snapshot import (  # noqa: F401
    buildScanSnapshot,
    getScanPosition,
)


def available_scans() -> list[str]:
    """가용한 scan 축 목록."""
    return ["network", "governance", "workforce", "capital", "debt", "signal"]
