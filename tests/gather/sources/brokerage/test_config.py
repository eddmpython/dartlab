"""brokerage.config 단위 테스트 — 레지스트리 구조 회귀 가드."""

from __future__ import annotations

import pytest

from dartlab.gather.sources.brokerage import config as _config

pytestmark = pytest.mark.unit


def test_enabled_set() -> None:
    enabled = _config.enabledBrokers()
    assert set(enabled) == {"miraeasset", "nh", "yuanta", "hanyang", "bookook"}


def test_spa_deferred() -> None:
    for key in ("koreainvestment", "kb", "kiwoom", "hana"):
        assert _config.BROKERS[key]["enabled"] is False
        assert _config.BROKERS[key]["mechanism"] == "spaAjax"


def test_hanyang_boards_use_board_numbers() -> None:
    """한양 보드는 개편 뒤 번호 주소만 직접 열린다(옛 /board/<이름>/list 는 리다이렉트에 기댄다)."""
    urls = _config.BROKERS["hanyang"]["categories"].values()
    assert len(set(urls)) == 4
    for url in urls:
        assert url.startswith("https://www.hygood.co.kr/board/00000000-0000-0000-0000-0000090000"), url


def test_each_broker_has_categories() -> None:
    for key, cfg in _config.BROKERS.items():
        assert cfg["categories"], f"{key} categories 비어있음"
        assert "name" in cfg and "mechanism" in cfg
