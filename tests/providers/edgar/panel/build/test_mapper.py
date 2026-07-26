"""EDGAR panel mapper — role→statement·context→cell·period·item (순수, data 0).

DART ``panel.mapper`` 의 us-gaap 미러 검증. role 패턴 분류, instant/duration mode, calendar quarter.
"""

from __future__ import annotations

from datetime import date

import pytest

pytestmark = pytest.mark.unit


def test_role_to_statement() -> None:
    from dartlab.providers.edgar.panel.build.mapper import roleToStatement

    assert roleToStatement("http://x/role/StatementConsolidatedBalanceSheets") == "BS"
    assert roleToStatement("http://x/role/StatementConsolidatedStatementsOfIncome") == "IS"
    assert roleToStatement("http://x/role/StatementConsolidatedStatementsOfCashFlows") == "CF"
    assert roleToStatement("http://x/role/StatementConsolidatedStatementsOfComprehensiveIncome") == "CIS"
    assert roleToStatement("http://x/role/StatementConsolidatedStatementsOfChangesInEquity") == "EF"
    # parenthetical = 본표 아님, Disclosure = 주석 → None
    assert roleToStatement("http://x/role/StatementBalanceSheetsParenthetical") is None
    assert roleToStatement("http://x/role/DisclosureLeases") is None
    assert roleToStatement("") is None


def test_comprehensive_income_before_income() -> None:
    """ComprehensiveIncome 은 IS 가 아니라 CIS (검사 순서 가드)."""
    from dartlab.providers.edgar.panel.build.mapper import roleToStatement

    assert roleToStatement("http://x/role/StatementOfComprehensiveIncome") == "CIS"


def test_edgar_section_status_catalog_gate() -> None:
    """edgarSectionStatus — 카탈로그 표준명 정확 일치 게이트 (오검출 Item·표지·prose tail → junk)."""
    from dartlab.providers.edgar.panel.build.mapper import edgarSectionStatus

    # navi — 표준 카탈로그명 정확 일치
    assert edgarSectionStatus("10-K", "Item 1. Business") == "navi"
    assert edgarSectionStatus("10-K", "Item 1A. Risk Factors") == "navi"
    assert edgarSectionStatus("10-K", "Item 7. Management's Discussion and Analysis") == "navi"
    assert edgarSectionStatus("10-Q", "Item 1. Financial Statements") == "navi"
    # stmt — 재무제표 terse 키 (relabel 대상)
    assert edgarSectionStatus("10-K", "BS") == "stmt"
    assert edgarSectionStatus("10-K", "IS") == "stmt"
    # junk — 표지(==form) / 카탈로그 밖 번호 / prose tail / 폼에 없는 Item
    assert edgarSectionStatus("10-K", "10-K") == "junk"  # front-matter 표지
    assert edgarSectionStatus("10-K", "Item 405. Of Regulation S-K (§229") == "junk"  # Reg S-K 조문번호
    assert edgarSectionStatus("10-Q", "Item 8. Of Our Annual Report On Form") == "junk"  # 10-Q 엔 Item 8 없음
    assert edgarSectionStatus("10-K", "Item 1A. Risk Factors You Should Carefully Consider") == "junk"  # prose tail
    assert edgarSectionStatus("10-K", "Cover Page Boilerplate") == "junk"  # Item 형식 아님


def test_edgar_section_status_unknown_form_keeps_all() -> None:
    """카탈로그 없는 폼(20-F 등)은 과잉필터 회피 — Item 형식이면 전부 navi (honest)."""
    from dartlab.providers.edgar.panel.build.mapper import edgarSectionStatus

    assert edgarSectionStatus("20-F", "Item 16A. Audit Committee Financial Expert") == "navi"
    assert edgarSectionStatus("20-F", "Item 8. Financial Information") == "navi"
    assert edgarSectionStatus("20-F", "20-F") == "junk"  # 표지는 폼 무관 junk
    assert edgarSectionStatus("20-F", "BS") == "stmt"  # 재무키는 폼 무관 stmt


def test_role_short_names_and_ifrs() -> None:
    """Statement prefix 없는 짧은 이름 + IFRS role 흡수 (BalanceSheet/CashFlows/ProfitOrLoss)."""
    from dartlab.providers.edgar.panel.build.mapper import roleToStatement

    assert roleToStatement("http://x/role/BalanceSheet") == "BS"
    assert roleToStatement("http://x/role/CashFlows") == "CF"
    assert roleToStatement("http://x/role/IncomeStatement") == "IS"
    assert roleToStatement("http://x/role/StatementOfProfitOrLoss") == "IS"  # IFRS
    assert roleToStatement("http://x/role/StatementOfFinancialPosition") == "BS"  # IFRS
    # 주석·디테일·괄호표는 짧은 이름이어도 배제(BalanceSheet 포함해도)
    assert roleToStatement("http://x/role/DisclosureBalanceSheetDetails") is None
    assert roleToStatement("http://x/role/BalanceSheetParenthetical") is None


def test_caption_to_statement_title_form() -> None:
    """표 캡션 제목 → statement (INS-era fallback). 제목 형식만 — prose·off-balance 오탐 배제."""
    from dartlab.providers.edgar.panel.build.mapper import captionToStatement

    assert captionToStatement("AAR CORP. AND SUBSIDIARIES CONSOLIDATED BALANCE SHEETS ASSETS") == "BS"
    assert captionToStatement("CONSOLIDATED STATEMENTS OF CASH FLOWS") == "CF"
    assert captionToStatement("CONSOLIDATED STATEMENTS OF INCOME") == "IS"
    assert captionToStatement("CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME (LOSS)") == "CIS"
    assert captionToStatement("CONSOLIDATED STATEMENTS OF CHANGES IN EQUITY FOR THE THREE YEARS") == "EF"
    assert captionToStatement("STATEMENT OF FINANCIAL POSITION") == "BS"  # IFRS
    # prose(주석 본문)·off-balance·빈 캡션 = None (제목 아님)
    assert captionToStatement("A summary of the components of comprehensive income is as follows:") is None
    assert captionToStatement("contractual cash obligations and off-balance sheet arrangements") is None
    assert captionToStatement("") is None


def test_caption_comprehensive_before_income() -> None:
    """ComprehensiveIncome 캡션은 IS 가 아니라 CIS (검사 순서 가드 — role 규칙과 동형)."""
    from dartlab.providers.edgar.panel.build.mapper import captionToStatement

    assert captionToStatement("CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME") == "CIS"


def test_context_to_cell_instant_year_vs_interim() -> None:
    from dartlab.providers.edgar.panel.build.mapper import contextToCell

    # 연말(FYE 12월) instant → mode Y
    assert contextToCell({"instant": "2024-12-31", "start": None, "end": None, "members": []}, fyEndMonth=12) == (
        2024,
        "e",
        4,
        "Y",
        "",
    )
    # 중간 instant(8월, FYE 12월 아님) → mode A
    assert contextToCell({"instant": "2024-08-31", "start": None, "end": None, "members": []}, fyEndMonth=12) == (
        2024,
        "e",
        3,
        "A",
        "",
    )


def test_context_to_cell_duration_modes() -> None:
    from dartlab.providers.edgar.panel.build.mapper import contextToCell

    # FY duration(~365d) → Y
    assert contextToCell({"instant": None, "start": "2024-01-01", "end": "2024-12-31", "members": []}) == (
        2024,
        "d",
        4,
        "Y",
        "",
    )
    # 단독 분기(~90d) → Q
    assert contextToCell({"instant": None, "start": "2024-07-01", "end": "2024-09-30", "members": []}) == (
        2024,
        "d",
        3,
        "Q",
        "",
    )
    # YTD(~180d) → A
    out = contextToCell({"instant": None, "start": "2024-01-01", "end": "2024-06-30", "members": []})
    assert out[3] == "A"


def test_context_to_cell_axis_members() -> None:
    from dartlab.providers.edgar.panel.build.mapper import contextToCell

    ctx = {"instant": "2024-12-31", "start": None, "end": None, "members": [("srt:SegAxis", "air:NorthMember")]}
    out = contextToCell(ctx, fyEndMonth=12)
    assert out[4] == "NorthMember"  # member local-name only (DART axisPath 동형)


def test_period_from_report_no_hyphen() -> None:
    """periodFromReport 는 'YYYYQn' (하이픈 금지 — isPeriodColumn 규약)."""
    from dartlab.providers.edgar.panel.build.mapper import periodFromReport

    assert periodFromReport("10-K", date(2024, 12, 31)) == "2024Q4"
    assert periodFromReport("10-K", date(2025, 5, 31)) == "2025Q2"  # May-end → Q2 (calendar)
    assert periodFromReport("10-K", None) is None
    # 10-Q (분기보고) — period-of-report 분기말 → 해당 calendar Qn
    assert periodFromReport("10-Q", date(2024, 9, 30)) == "2024Q3"
    assert periodFromReport("10-Q", date(2024, 6, 30)) == "2024Q2"


def test_canonical_item() -> None:
    from dartlab.providers.edgar.panel.build.mapper import canonicalItem

    leaf, path = canonicalItem("10-K", "ITEM 1A. RISK FACTORS")
    assert leaf == "Item 1A. Risk Factors"
    assert path == "10-K␟Item 1A. Risk Factors"
    leaf2, _ = canonicalItem("10-K", "Item 1.")
    assert leaf2 == "Item 1. Business"  # 카탈로그 표준명
