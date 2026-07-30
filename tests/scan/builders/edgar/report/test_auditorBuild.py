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


def test_panel_report_build_reads_panel_once_for_employee_and_auditor(tmp_path, monkeypatch):
    """workflow용 빌더가 같은 panel pass에서 employee와 auditor 두 artifact를 만든다."""
    import dartlab.config as cfg
    from dartlab.scan.builders.edgar import helpers
    from dartlab.scan.builders.edgar.report import auditorBuild, employeeBuild

    panelDir = tmp_path / "edgar" / "panel"
    panelDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "chapter": ["10-K"],
            "period": ["2024Q4"],
            "contentRaw": [
                "We had approximately 5,000 employees. "
                "Ernst & Young LLP has served as the Company's auditor since 2009."
            ],
        }
    ).write_parquet(panelDir / "TST.parquet")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(helpers, "edgarCikToTicker", lambda: {"0000000001": "TST"})
    monkeypatch.setattr(employeeBuild, "_loadPriorEmployee", lambda: pl.DataFrame(schema=employeeBuild.EMPLOYEE_COLS))
    monkeypatch.setattr(auditorBuild, "_loadPriorAuditor", lambda: pl.DataFrame(schema=auditorBuild.AUDITOR_COLS))

    employeePath, auditorPath = auditorBuild.buildEdgarPanelReports()
    employee = pl.read_parquet(employeePath)
    auditor = pl.read_parquet(auditorPath)
    assert employee.select(["stockCode", "year", "employeeCount"]).to_dicts() == [
        {"stockCode": "TST", "year": "2024", "employeeCount": 5000}
    ]
    assert auditor.select(["stockCode", "year", "auditor", "sinceYear"]).to_dicts() == [
        {"stockCode": "TST", "year": "2024", "auditor": "Ernst & Young LLP", "sinceYear": 2009}
    ]
