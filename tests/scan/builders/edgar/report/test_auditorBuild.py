"""auditorBuild. panel 텍스트 감사인 scan 빌더 단위 (합성 프레임, 네트워크/OOM 무관)."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_auditor_rows_from_panel_by_year():
    """기(period)별 블록 연결 → 연도별 canonical 감사인 + since. 미검출 연도 제외."""
    from dartlab.scan.builders.edgar.report.auditorBuild import auditorRowsFromPanel

    panel = pl.DataFrame(
        {
            "period": ["2025Q4", "2025Q4", "2024Q4", "2023Q4"],
            "contentRaw": [
                "Report of Independent Registered Public Accounting Firm",
                "We have served as the Company's auditor since 2009. Ernst & Young LLP",
                "KPMG LLP We have served as the Firm's auditor since 2002.",
                "Item 1. Business only. No audit text.",  # 미검출 연도 → 제외
            ],
        }
    )
    rows = auditorRowsFromPanel(panel, "TST")
    got = {r["year"]: (r["auditor"], r["sinceYear"]) for r in rows}
    assert got["2025"] == ("Ernst & Young LLP", 2009)  # 같은 기 블록 연결
    assert got["2024"] == ("KPMG LLP", 2002)
    assert "2023" not in got  # 정직 미emit
    assert all(r["stockCode"] == "TST" for r in rows)
