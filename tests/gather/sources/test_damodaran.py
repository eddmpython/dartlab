"""gather/sources/damodaran.py 단위 테스트 — DOC 파싱 + fetch 위임 (network-free)."""

from __future__ import annotations

import pytest

from dartlab.gather.sources import damodaran
from dartlab.gather.types import SourceUnavailableError

pytestmark = pytest.mark.unit


def test_extract_mature_market_erp() -> None:
    html = "<p>The mature market equity risk premium is 4.60% as of 2026.</p>"
    assert damodaran._extractMatureMarketERP(html) == 4.60


def test_extract_mature_market_erp_missing() -> None:
    assert damodaran._extractMatureMarketERP("<p>no premium here</p>") is None


def test_extract_countries_parses_table() -> None:
    html = (
        "<table>"
        "<tr><th>Country</th><th>Rating</th><th>Spread</th><th>ERP</th></tr>"
        "<tr><td>Korea</td><td>Aa2</td><td>0.60%</td><td>5.20%</td></tr>"
        "<tr><td>NoNums</td><td>x</td><td>y</td><td>z</td></tr>"
        "</table>"
    )
    out = damodaran._extractCountries(html)
    assert "Korea" in out
    assert out["Korea"]["rawNumbers"] == [0.60, 5.20]
    assert "NoNums" not in out  # 숫자 < 2 행은 제외


def test_fetch_country_erp_delegates_and_structures(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetchHtml(외부 fetch) 위임 후 구조화 dict 반환 — online fetch=gather SSOT 회귀 가드."""
    html = (
        "<p>mature market equity risk premium 4.60%</p>"
        "<table><tr><td>Korea</td><td>Aa2</td><td>0.60%</td><td>5.20%</td></tr></table>"
    )
    monkeypatch.setattr(damodaran, "_fetchHtml", lambda *a, **k: html)
    out = damodaran.getDamodaranCountryErp()
    assert out is not None
    assert out["matureMarketERP"] == 4.60
    assert out["countries"]["Korea"]["rawNumbers"] == [0.60, 5.20]


def test_fetch_country_erp_propagates_fetch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    upstream = OSError("network down")

    def failFetch(*_args, **_kwargs):
        raise SourceUnavailableError("fetch failed") from upstream

    monkeypatch.setattr(damodaran, "_fetchHtml", failFetch)
    with pytest.raises(SourceUnavailableError, match="fetch failed") as excInfo:
        damodaran.getDamodaranCountryErp()
    assert excInfo.value.__cause__ is upstream


def test_fetch_country_erp_rejects_changed_page_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(damodaran, "_fetchHtml", lambda *a, **k: "<html>changed</html>")
    with pytest.raises(SourceUnavailableError, match="schema"):
        damodaran.getDamodaranCountryErp()
