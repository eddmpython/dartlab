"""P1 report de-gate 신규 소비자 회귀 (합성 데이터, 네트워크 불요).

카탈로그 도출 24 apiType 중 신규 7 종(채무증권·5억+보수·미등기보수·주식총수·최대주주변동·
공모/사모 자금사용)의 sub-scanner 와 이벤트-데이터 최신연도 선택 헬퍼(latestDataRows)를
monkeypatch 로 검증한다. 실 parquet 없이 결정적.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.io.parquet import latestDataRows

pytestmark = pytest.mark.unit


class TestLatestDataRows:
    def test_skips_status_only_latest(self):
        # 2026 null, 2025 "-", 2024 실값 → 최신 실데이터 = 2024
        g = pl.DataFrame({"year": ["2024", "2025", "2026"], "v": ["100", "-", None]})
        out = latestDataRows(g, "v")
        assert out["year"].to_list() == ["2024"]

    def test_empty_when_no_real_value(self):
        g = pl.DataFrame({"year": ["2025", "2026"], "v": ["-", None]})
        assert latestDataRows(g, "v").is_empty()

    def test_missing_column(self):
        g = pl.DataFrame({"year": ["2025"], "x": ["1"]})
        assert latestDataRows(g, "v").is_empty()


def test_scan_debt_securities(monkeypatch):
    import dartlab.scan.debt.scanner as m

    df = pl.DataFrame(
        {
            "stockCode": ["A", "A", "B"],
            "year": ["2024", "2025", "2025"],
            "facvalu_totamt": ["1,000", "-", "2,000"],
            "intrt": ["3.5", "-", "2.0"],
            "scrits_knd_nm": ["회사채", "-", "회사채"],
        }
    )
    monkeypatch.setattr(m, "scanParquets", lambda a, c: df)
    r = m.scanDebtSecurities()
    assert r["A"]["채무증권발행액"] == 1000.0  # 2025 는 status-only, 최신 실데이터 2024
    assert r["A"]["채무증권평균이자율"] == 3.5
    assert r["B"]["채무증권발행액"] == 2000.0


def test_scan_high_pay(monkeypatch):
    import dartlab.scan.workforce.scanner as m

    df = pl.DataFrame(
        {
            "stockCode": ["A", "A"],
            "year": ["2025", "2025"],
            "nm": ["갑", "을"],
            "ofcps": ["대표", "부사장"],
            "mendng_totamt": ["1,000,000,000", "600,000,000"],
        }
    )
    monkeypatch.setattr(m, "scanParquets", lambda a, c: df)
    r = m.scanHighPay()
    assert r["A"]["최고개인보수_억"] == 10.0  # 10억
    assert r["A"]["고액보수인원"] == 2.0


def test_scan_share_total_prefers_total(monkeypatch):
    import dartlab.scan.capital.scanner as m

    df = pl.DataFrame(
        {
            "stockCode": ["A", "A"],
            "year": ["2025", "2025"],
            "se": ["보통주", "합계"],
            "isu_stock_totqy": ["800", "1,000"],
            "tesstk_co": ["50", "100"],
        }
    )
    monkeypatch.setattr(m, "scanParquets", lambda a, c: df)
    r = m.scanShareTotal()
    assert r["A"]["발행주식총수"] == 1000.0  # 합계 우선
    assert r["A"]["자기주식비율"] == 10.0


def test_scan_offering_usage_accumulates_and_flags(monkeypatch):
    import dartlab.scan.capital.scanner as m

    pub = pl.DataFrame(
        {
            "stockCode": ["A"],
            "year": ["2020"],
            "pay_amount": ["1,000"],
            "dffrnc_occrrnc_resn": ["목적변경"],
        }
    )
    pri = pl.DataFrame(
        {
            "stockCode": ["A"],
            "year": ["2021"],
            "pay_amount": ["500"],
            "dffrnc_occrrnc_resn": ["-"],
        }
    )
    calls = iter([pub, pri])
    monkeypatch.setattr(m, "scanParquets", lambda a, c: next(calls))
    r = m.scanOfferingUsage()
    assert r["A"]["조달금액"] == 1500.0  # 공모 1000 + 사모 500
    assert r["A"]["목적외사용"] is True  # 공모 목적변경 기재


def test_scan_major_holder_changes(monkeypatch):
    import dartlab.scan.governance.scanner as m

    df = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A"],
            "year": ["2023", "2024", "2025"],
            "qota_rt": ["30.0", "-", "35.5"],
            "change_cause": ["장내매수", "-", "상속"],
        }
    )
    monkeypatch.setattr(m, "scanParquets", lambda a, c: df)
    r = m.scanMajorHolderChanges()
    assert r["A"]["최대주주변동건수"] == 2.0  # 장내매수 + 상속 ("-" 제외)
    assert r["A"]["최대주주지분율"] == 35.5  # 최신 실값


def test_scan_report_apitypes_derive_24():
    from dartlab.scan.builders.kr.report.build import _NO_DATA_REPORT_APITYPES, SCAN_API_TYPES

    assert len(SCAN_API_TYPES) == 24
    assert not (set(SCAN_API_TYPES) & _NO_DATA_REPORT_APITYPES)  # 무데이터 4 제외 확인
    for new in ("topPay", "stockTotal", "debtSecurities", "publicOfferingUsage"):
        assert new in SCAN_API_TYPES
