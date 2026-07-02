"""proxyParse. DEF 14A 거버넌스 3표 파서 단위 (합성 HTML fixture, 네트워크/OOM 무관).

실측 검증은 tests/_attempts/proxyGovernance(20사 스윕 85/75/80%). 여기는 계약 고정:
단위(thousands) 보정, 연도 셀 위치 가변, percent 컬럼 지정(나이 오인 차단), 직함 분리.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_audit_fees_years_and_thousands():
    """연도 컬럼 매핑 + 'in thousands' 단위 1000배 보정."""
    from dartlab.providers.edgar.report.proxyParse import parseAuditFees

    html = """
    <p>Fees paid to the auditor (in thousands)</p>
    <table>
      <tr><th></th><th>2025</th><th>2024</th></tr>
      <tr><td>Audit Fees</td><td>$24,703</td><td>$22,381</td></tr>
      <tr><td>Audit-Related Fees</td><td>2,274</td><td>2,418</td></tr>
      <tr><td>Tax Fees</td><td>153</td><td>170</td></tr>
      <tr><td>All Other Fees</td><td>12</td><td>9</td></tr>
    </table>"""
    rows = {r["year"]: r for r in parseAuditFees(html)}
    assert rows["2025"]["auditFee"] == 24_703_000.0  # thousands 보정
    assert rows["2024"]["auditFee"] == 22_381_000.0
    assert rows["2025"]["taxFee"] == 153_000.0


def test_audit_fees_plain_dollars_without_marker():
    """thousands 마커 없으면 원값 유지(소형주 달러 표기)."""
    from dartlab.providers.edgar.report.proxyParse import parseAuditFees

    html = """
    <table>
      <tr><th></th><th>2025</th></tr>
      <tr><td>Audit Fees</td><td>$108,385</td></tr>
    </table>"""
    rows = parseAuditFees(html)
    assert rows[0]["auditFee"] == 108_385.0


def test_sct_variable_year_cell_and_title_split():
    """연도 셀 위치 가변(MSFT 류) + 이름/직함 분리 + 마지막 금액=Total."""
    from dartlab.providers.edgar.report.proxyParse import parseSummaryComp

    html = """
    <table>
      <tr><th>Name and Principal Position</th><th>Year</th><th>Salary ($)</th><th>Bonus</th><th>Total ($)</th></tr>
      <tr><td>Tim Cook Chief Executive Officer</td><td></td><td>2025</td><td>3,000,000</td><td>74,294,811</td></tr>
      <tr><td></td><td>2024</td><td></td><td>3,000,000</td><td>74,609,802</td></tr>
    </table>"""
    rows = parseSummaryComp(html)
    assert rows[0]["name"] == "Tim Cook"
    assert rows[0]["title"].startswith("Chief Executive")
    assert rows[0]["year"] == "2025"
    assert rows[0]["totalPay"] == 74_294_811.0
    assert rows[1]["year"] == "2024"  # 이름 셀 빈 후속 연도행은 직전 인물 계승
    assert rows[1]["totalPay"] == 74_609_802.0


def test_ownership_percent_column_only_blocks_age():
    """percent 명명 컬럼에서만 추출. 나이(Age) 컬럼 오인 차단."""
    from dartlab.providers.edgar.report.proxyParse import parseBeneficialOwnership

    html = """
    <table>
      <tr><th>Name of Beneficial Owner</th><th>Age</th><th>Shares Beneficially Owned</th><th>Percent of Class</th></tr>
      <tr><td>The Vanguard Group</td><td></td><td>145,000,000</td><td>9.63%</td></tr>
      <tr><td>Jane Doe (2)</td><td>82</td><td>1,000</td><td>*</td></tr>
      <tr><td>BlackRock, Inc.</td><td></td><td>107,000,000</td><td>7.1</td></tr>
    </table>"""
    rows = parseBeneficialOwnership(html)
    got = {r["holder"]: r["pct"] for r in rows}
    assert got["The Vanguard Group"] == 9.63
    assert got["BlackRock, Inc."] == 7.1
    assert "Jane Doe" not in got  # '*'(1% 미만)·나이 82 는 pct 아님


def test_audit_fees_no_year_header_emits_nothing():
    """연도 헤더 미검출 표는 행을 emit 하지 않음(year='1' 쓰레기 행 회귀 가드, MSFT 실측)."""
    from dartlab.providers.edgar.report.proxyParse import parseAuditFees

    html = """
    <table>
      <tr><th></th><th>Current</th><th>Prior</th></tr>
      <tr><td>Audit Fees</td><td>$56,300</td><td>$50,000</td></tr>
    </table>"""
    assert parseAuditFees(html) == []  # 연도 불명 = 정직 미emit


def test_empty_html_returns_empty():
    """표 없는 문서(특별총회 proxy 류)는 전부 빈 결과(패널 자연 미표시)."""
    from dartlab.providers.edgar.report.proxyParse import (
        parseAuditFees,
        parseBeneficialOwnership,
        parseSummaryComp,
    )

    html = "<html><body><p>Special meeting. No governance tables.</p></body></html>"
    assert parseAuditFees(html) == []
    assert parseSummaryComp(html) == []
    assert parseBeneficialOwnership(html) == []
