"""EDGAR scan 직원수 빌더. parseEmployeeCount 패턴/범위 + employeeRowsFromPanel 연도 추출.

합성 텍스트/panel 이라 네트워크·OOM 무관.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_parse_employee_count_patterns():
    """대표 패턴(approximately/had/workforce of/단순)에서 직원수 추출."""
    from dartlab.providers.edgar.report.employee import parseEmployeeCount

    assert parseEmployeeCount("we had approximately 164,000 full-time employees") == 164000
    assert parseEmployeeCount("employed approximately 228,000 people worldwide") == 228000
    assert parseEmployeeCount("our workforce of approximately 150,000 spans") == 150000
    assert parseEmployeeCount("a total of 12,300 employees") == 12300


def test_parse_employee_count_range_guard():
    """상식 범위 밖(연도·과대)은 None. 무매칭도 None."""
    from dartlab.providers.edgar.report.employee import parseEmployeeCount

    assert parseEmployeeCount("revenue grew in 2024") is None  # 'employees' 없음
    assert parseEmployeeCount("we had 3 employees") is None  # 10 미만 하한
    assert parseEmployeeCount("operating cash flow rose") is None


def test_employee_rows_first_match_per_year():
    """연도당 첫 유효 매칭 채택. period 앞 4자리=연도."""
    from dartlab.scan.builders.edgar.report.employeeBuild import employeeRowsFromPanel

    panel = pl.DataFrame(
        {
            "period": ["2023", "2024", "2024Q4"],
            "contentRaw": [
                "As of year end we had approximately 161,000 employees.",
                "We employed approximately 164,000 full-time employees.",
                "ignored second 2024 row with 999,999 employees",
            ],
        }
    )
    rows = employeeRowsFromPanel(panel, "AAPL")
    by = {r["year"]: r for r in rows}
    assert by["2023"]["employeeCount"] == 161000
    assert by["2024"]["employeeCount"] == 164000  # 첫 2024 매칭(둘째 무시)
    assert by["2024"]["stockCode"] == "AAPL"
    assert by["2024"]["source"] == "10-K"


def test_employee_rows_empty_without_match():
    """직원 문구 없는 panel 은 빈 list."""
    from dartlab.scan.builders.edgar.report.employeeBuild import employeeRowsFromPanel

    panel = pl.DataFrame({"period": ["2024"], "contentRaw": ["no headcount disclosure here"]})
    assert employeeRowsFromPanel(panel, "X") == []


def test_build_merges_prior_seed(tmp_path, monkeypatch):
    """누적 병합: 기존 발행본 시드 + 로컬 panel 추출 합산. 충돌은 로컬 우선, 시드 전용 종목 유지."""
    import dartlab.config as cfg
    from dartlab.scan.builders.edgar import helpers
    from dartlab.scan.builders.edgar.report import employeeBuild

    # 로컬 panel 1종(NEWCO) 합성
    panelDir = tmp_path / "edgar" / "panel"
    panelDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "chapter": ["10-K", "10-K"],
            "period": ["2024", "2023"],
            "contentRaw": ["we had approximately 5,000 employees", "we had approximately 4,000 employees"],
        }
    ).write_parquet(panelDir / "NEWCO.parquet")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(helpers, "edgarCikToTicker", lambda: {"0000000001": "NEWCO", "0000000002": "OLDCO"})

    # 시드: OLDCO(로컬에 없음) + NEWCO 2024(로컬이 덮어써야 함, 9999 -> 5000)
    seed = pl.DataFrame(
        {
            "stockCode": ["OLDCO", "NEWCO"],
            "year": ["2022", "2024"],
            "employeeCount": [777, 9999],
            "source": ["10-K", "10-K"],
        }
    ).cast(employeeBuild.EMPLOYEE_COLS)
    monkeypatch.setattr(employeeBuild, "_loadPriorEmployee", lambda: seed)

    p = employeeBuild.buildEdgarEmployee(verbose=False)
    out = pl.read_parquet(p)
    by = {(r["stockCode"], r["year"]): r["employeeCount"] for r in out.to_dicts()}
    assert by[("OLDCO", "2022")] == 777  # 시드 전용 종목 유지
    assert by[("NEWCO", "2024")] == 5000  # 로컬이 시드(9999) 덮어씀
    assert by[("NEWCO", "2023")] == 4000  # 로컬 신규
