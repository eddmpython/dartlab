"""proxyBuild. DEF 14A 거버넌스 scan 빌더 단위 (합성 메타 + fetch 모킹, 네트워크/OOM 무관)."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_PROXY_HTML = """
<p>Our Board of Directors currently consists of eight directors. 6 of our 8 directors are independent.</p>
<p>(in thousands)</p>
<table>
  <tr><th></th><th>2025</th><th>2024</th></tr>
  <tr><td>Audit Fees</td><td>$1,000</td><td>$900</td></tr>
</table>
<table>
  <tr><th>Name and Principal Position</th><th>Year</th><th>Salary ($)</th><th>Total ($)</th></tr>
  <tr><td>Jane Roe Chief Executive Officer</td><td>2025</td><td>500,000</td><td>2,000,000</td></tr>
</table>
<table>
  <tr><th>Name of Beneficial Owner</th><th>Shares Beneficially Owned</th><th>Percent of Class</th></tr>
  <tr><td>Big Fund LP</td><td>9,000,000</td><td>12.5%</td></tr>
</table>
"""


def test_proxy_rows_from_html_four_tables():
    """단일 HTML 에서 4표 행 동시 생성 + stockCode/기준연도 주입."""
    from dartlab.scan.builders.edgar.report.proxyBuild import proxyRowsFromHtml

    af, ep, ow, bd = proxyRowsFromHtml(_PROXY_HTML, "TST", "2026")
    byYear = {r["year"]: r for r in af}
    assert byYear["2025"]["stockCode"] == "TST" and byYear["2025"]["auditFee"] == 1_000_000.0  # thousands 보정
    assert byYear["2024"]["auditFee"] == 900_000.0
    assert ep[0]["name"] == "Jane Roe" and ep[0]["totalPay"] == 2_000_000.0
    assert ow[0] == {"stockCode": "TST", "year": "2026", "holder": "Big Fund LP", "pct": 12.5}
    assert bd == [{"stockCode": "TST", "year": "2026", "directors": 8, "independentDirectors": 6}]


def test_build_skips_done_and_uses_latest_proxy(tmp_path, monkeypatch):
    """리줌(doneTickers skip) + 회사별 최신 DEF 14A 1건 선정 + fetch 위임."""
    import dartlab.scan.builders.edgar.report.proxyBuild as mod

    meta = pl.DataFrame(
        {
            "stockCode": ["AAA", "AAA", "BBB", "CCC"],
            "form": ["DEF 14A", "DEF 14A", "DEF 14A", "8-K"],  # CCC 는 proxy 없음
            "filingDate": ["20260401", "20250401", "20260501", "20260601"],
            "url": ["u-new", "u-old", "u-b", "u-x"],
        }
    )
    mp = tmp_path / "recent.parquet"
    meta.write_parquet(mp)

    fetched: list[str] = []

    def _fakeFetch(url, *, client, timeout=30.0):
        fetched.append(url)
        return _PROXY_HTML, "ok"

    monkeypatch.setattr("dartlab.gather.edgar.allFilingsContent.getFilingBody", _fakeFetch)
    monkeypatch.setattr(mod, "_PACE_SECONDS", 0)

    out = mod.buildEdgarProxyReport(metaPath=mp, doneTickers={"BBB"})
    assert fetched == ["u-new"]  # AAA 최신만 (u-old 아님) · BBB skip · CCC 는 proxy 없음
    assert {r["stockCode"] for r in out["auditFees"]} == {"AAA"}


def test_future_year_rows_gated_by_filing_year():
    """proxy 제출연도 이후 연도 행 차단 (옵션 만기연도 오인 등 미래연도 오염 불변식)."""
    from dartlab.scan.builders.edgar.report.proxyBuild import proxyRowsFromHtml

    html = """
    <p>(in thousands)</p>
    <table>
      <tr><th></th><th>2025</th><th>2042</th></tr>
      <tr><td>Audit Fees</td><td>$1,000</td><td>$900</td></tr>
    </table>"""
    af, ep, ow, bd = proxyRowsFromHtml(html, "TST", "2026")
    assert {r["year"] for r in af} == {"2025"}  # 2042 행 차단
