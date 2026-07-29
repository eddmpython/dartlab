"""EDGAR panel 공개 계약 — 보드 read + finance dispatch + 배포 config.

build round-trip(합성 text→build→Panel(us)) + us finance 라우팅 + isStrongTopic + 배포 config.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_panel_us_build_roundtrip(builtTicker) -> None:
    """합성 원본 → build → EDGAR Panel 보드 wide + 재무표 검색 + 본문검색."""
    from dartlab.providers.edgar.panel import Panel
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanel

    from .synthData import synthSubmissionTxt

    buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}])
    p = Panel(builtTicker)
    assert isinstance(p, pl.DataFrame) and not p.is_empty()
    for col in ("chapter", "sectionLeaf", "disclosureKey", "scope"):
        assert col in p.columns
    assert "2024Q4" in p.columns
    # 재무표 disclosureKey 행 검색
    assert p("BS") is not None
    # 서술 본문 전체검색
    assert p.search("widgets") is not None
    # EDGAR 연결-only → scope consolidated
    assert set(p["scope"].unique().to_list()) == {"consolidated"}


def test_panel_us_dispatch_native_lower_finance_upper() -> None:
    """us: 소문자 재무 키는 native, 대문자 강한 재무 키는 finance(_showFn) 위임."""
    from dartlab.providers.edgar.panel import Panel

    p = Panel("000000nonexistent")
    p._nativeFn = lambda statement, **kw: f"native:{statement}"
    p._showFn = lambda topic, **kw: f"fin:{topic}"
    p._strongFn = lambda t: t in {"IS", "BS", "CF", "CIS", "SCE", "RATIOS"}

    assert p("is") == "native:is"
    assert p("bs") == "native:bs"
    assert p("ratios") == "native:ratios"
    assert p("IS") == "fin:IS"
    assert p("RATIOS") == "fin:ratios"
    assert p("Risk") is None  # 약한 소스 → board(artifact 없어 None)


def test_panel_upper_ratios_reaches_real_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.providers.edgar.builder import dataDispatcher
    from dartlab.providers.edgar.panel import Panel

    expected = pl.DataFrame({"항목": ["영업이익률"], "2024": [20.0]})
    monkeypatch.setattr(dataDispatcher, "buildRatios", lambda company: expected)
    company = object()
    panel = Panel("000000nonexistent")
    panel._showFn = lambda topic, **kwargs: dataDispatcher.showImpl(company, topic, **kwargs)
    panel._strongFn = dataDispatcher.isStrongTopic

    assert panel("RATIOS").equals(expected)


def test_show_finance_forwards_scope_and_period_list_options() -> None:
    from dartlab.providers.edgar.builder.dataDispatcher import showImpl

    calls: list[tuple[str, str, str]] = []

    class Finance:
        SCE = None

        def _stmtDf(self, topic: str, *, freq: str, scope: str):
            calls.append((topic, freq, scope))
            return pl.DataFrame({"snakeId": ["sales"], "항목": ["매출액"], "2024Q1": [10.0]})

    class Company:
        _finance = Finance()

        def _showImpl(self, topic: str, block=None, **kwargs):
            return showImpl(self, topic, block, **kwargs)

    result = showImpl(Company(), "IS", period=["2024Q1"], freq="Y", scope="separate")

    assert result is not None
    assert calls == [("IS", "Y", "separate")]


def test_edgar_ytd_is_rejected_instead_of_returning_annual() -> None:
    from dartlab.providers.edgar.builder.dataDispatcher import buildFinanceSeries

    with pytest.raises(ValueError, match="YTD"):
        buildFinanceSeries(object(), freq="YTD")


def test_is_strong_topic_edgar() -> None:
    from dartlab.providers.edgar.builder.dataDispatcher import isStrongTopic

    assert isStrongTopic("IS") and isStrongTopic("RATIOS")
    assert not isStrongTopic("is") and not isStrongTopic("bs") and not isStrongTopic("ratios")
    assert not isStrongTopic("Risk") and not isStrongTopic("item1Business") and not isStrongTopic("")


def test_edgar_panel_distribution_config() -> None:
    """edgarPanel 단일 DATA_RELEASES + deploy _CATEGORY_MAP 배선."""
    from dartlab.core.dataConfig import DATA_RELEASES, repoFor
    from dartlab.providers.edgar.openapi.deploy import _CATEGORY_MAP

    assert DATA_RELEASES["edgarPanel"]["dir"] == "edgar/panel"
    assert "edgarPanelCell" not in DATA_RELEASES
    assert _CATEGORY_MAP["panel"] == "edgarPanel"
    assert "panelCell" not in _CATEGORY_MAP
    assert repoFor("edgarPanel")


def test_panel_us_ticker_case_insensitive(builtTicker) -> None:
    """EDGAR Panel("test") 소문자도 TEST artifact 해석."""
    from dartlab.providers.edgar.panel import Panel
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanel

    from .synthData import synthSubmissionTxt

    buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}])
    p = Panel("test")
    assert not p.is_empty()


def test_panel_us_standalone_lower_native_from_panel_payload(builtTicker) -> None:
    """EDGAR Panel 직접 진입도 소문자 native 를 panel payload 에서 분해한다."""
    from dartlab.providers.edgar.panel import Panel
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanel

    from .synthData import synthSubmissionTxt

    buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}])
    p = Panel("test")
    isWide = p("is", freq="year")
    bsWide = p("bs", freq="year")
    assert isWide is not None and not isWide.is_empty()
    assert bsWide is not None and not bsWide.is_empty()
    assert "2024" in isWide.columns and "2024" in bsWide.columns
