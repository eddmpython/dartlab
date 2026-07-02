"""auditorText. 10-K 감사인 추출 단위 (합성 텍스트, 네트워크/OOM 무관).

canonical 매칭 + 스타일드 small-caps 정규화 + 주어 변형(the Firm) since 추출.
실측 검증은 tests/_attempts/proxyGovernance/auditorProbe (대형 10사 firm 10/10·since 9/10).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_canonical_firm_and_since():
    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    firm, since = extractAuditorFromText(
        "Report of Independent Registered Public Accounting Firm ... "
        "We have served as the Company's auditor since 2009. Ernst & Young LLP San Jose, California"
    )
    assert firm == "Ernst & Young LLP"
    assert since == 2009


def test_smallcaps_styling_normalized():
    """스타일드 small-caps 공백(D ELOITTE & T OUCHE) 정규화 후 canonical 매칭 (MSFT 실측 패턴)."""
    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    firm, since = extractAuditorFromText("D ELOITTE & T OUCHE LLP We have served as the Firm's auditor since 1983.")
    assert firm == "Deloitte & Touche LLP"
    assert since == 1983  # 주어가 the Firm(JPM 류)이어도 since 추출


def test_no_auditor_returns_none():
    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    firm, since = extractAuditorFromText("Item 1. Business. We make widgets.")
    assert firm is None
    assert since is None


def test_absurd_since_year_rejected():
    """1900~2035 밖 since 는 None (오염 방어)."""
    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    _, since = extractAuditorFromText("auditor since 1789. KPMG LLP")
    assert since is None
