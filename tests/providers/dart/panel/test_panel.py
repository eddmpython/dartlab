"""Panel(pl.DataFrame) subclass mirror — 생성·callable·부재 동작 (데이터 0).

``providers/dart/panel/panel.py`` 의 1:1 mirror. Panel 이 pl.DataFrame subclass + callable
이고, artifact 없는 종목은 빈 DataFrame + __call__ None 임을 검증 (network/lxml 0, R2).
실데이터 wide/검색은 tests/panel/test_panel_intra.py (requires_data) 담당.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_panel_is_dataframe_subclass_and_callable() -> None:
    """Panel 인스턴스는 pl.DataFrame 이고 callable (잡는 순간 wide + 검색)."""
    from dartlab.providers.dart.panel import Panel

    p = Panel("000000nonexistent")
    assert isinstance(p, pl.DataFrame)
    assert callable(p)


def test_panel_absent_is_empty_dataframe() -> None:
    """artifact 없는 종목 → 빈 DataFrame (예외 없음)."""
    from dartlab.providers.dart.panel import Panel

    p = Panel("000000nonexistent")
    assert p.is_empty()


def test_panel_call_none_on_empty_or_blank_key() -> None:
    """빈 key 또는 artifact 부재 시 __call__ → None (전체 반환 금지)."""
    from dartlab.providers.dart.panel import Panel

    p = Panel("000000nonexistent")
    assert p("") is None
    assert p("재고") is None


def test_is_strong_topic_classification() -> None:
    """isStrongTopic SSOT — finance 강함, 정형 비재무 docs 토픽·canonicalKey·한글 섹션명은 raw 공시.

    공개 show + docs 농장 은퇴로 dividend 등 ~35 정형 비재무 토픽 registry 항목 제거(§영구소실)
    → 강한 소스 아님(raw panel 검색). 강한 소스는 finance 통계표(BS/IS/CF/…)만 잔존.
    """
    from dartlab.providers.dart.builder.dataDispatcher import isStrongTopic

    assert isStrongTopic("IS") is True  # finance
    assert isStrongTopic("BS") is True  # finance
    assert isStrongTopic("dividend") is True  # 정형 report는 공개 panel의 강한 source
    assert isStrongTopic("NT_D826380") is False  # canonicalKey → raw panel
    assert isStrongTopic("재고") is False  # 한글 섹션명 → raw panel


def test_panel_facade_injection_routes_strong_to_showfn() -> None:
    """facade 주입(_showFn/_strongFn) 시 강한 소스는 showFn 위임, raw 는 panel 검색 (데이터 0)."""
    from dartlab.providers.dart.panel import Panel

    p = Panel("000000nonexistent")
    calls = []
    p._showFn = lambda topic: f"finance:{topic}"  # 가짜 show 주입
    p._strongFn = lambda topic: topic in {"IS", "BS"}  # 가짜 분류

    # 강한 소스 → showFn 위임
    assert p("IS") == "finance:IS"
    # source="finance" 강제 → strongFn 무관 위임
    assert p("anything", source="finance") == "finance:anything"
    # source="raw" → 주입 무시, raw panel 검색 (artifact 없어 None)
    assert p("IS", source="raw") is None
    # 약한 소스(strongFn False) → raw panel 검색 (artifact 없어 None)
    assert p("재고") is None
