"""core/render/ — ChartHtmlRenderer Protocol + registry 단위 테스트.

P1 PR 2: viz protocol 역전 검증. dartlab full import 회피하여 직접 모듈 조작.
"""

from __future__ import annotations

import pytest

from dartlab.core.render import registry as _registryModule
from dartlab.reference.render import ChartHtmlRenderer, getRenderer, register

pytestmark = pytest.mark.unit


class _FakeRenderer:
    """ChartHtmlRenderer 테스트용 더미 — htmlFromSpec 만 구현."""

    def htmlFromSpec(self, spec: dict) -> str:
        """spec dict 를 echo 형태 HTML 로 변환."""
        return f"<div data-chart='{spec.get('chartType', '')}'>fake</div>"


@pytest.fixture
def _resetRegistry():
    """각 테스트 전후 registry 초기화 — 상태 누수 차단."""
    original = _registryModule._renderer
    _registryModule._renderer = None
    yield
    _registryModule._renderer = original


def test_protocolDuckType(_resetRegistry):
    """ChartHtmlRenderer 는 runtime_checkable Protocol — duck-type 인스턴스 OK."""
    fake = _FakeRenderer()
    assert isinstance(fake, ChartHtmlRenderer)


def test_registerStoresRenderer(_resetRegistry):
    """register 후 getRenderer 가 동일 인스턴스 반환."""
    fake = _FakeRenderer()
    register(fake)
    assert getRenderer() is fake


def test_registerOverwritesPrevious(_resetRegistry):
    """후속 register 는 이전 등록을 덮어씌움 (단일 슬롯 정책)."""
    first = _FakeRenderer()
    second = _FakeRenderer()
    register(first)
    register(second)
    assert getRenderer() is second


def test_getRendererPropagatesBootstrapFailure(_resetRegistry, monkeypatch: pytest.MonkeyPatch):
    """renderer bootstrap 실패를 ``None``으로 삼키지 않고 원인 그대로 전파한다."""
    import importlib

    from dartlab.core import pluginDiscovery

    def _fakeImport(name: str):
        raise ImportError(f"simulated missing: {name}")

    pluginDiscovery._COMPLETED.discard("dartlab.core.render")
    monkeypatch.setattr(importlib, "import_module", _fakeImport)
    with pytest.raises(ImportError, match="simulated missing: dartlab.viz"):
        getRenderer()
    assert "dartlab.core.render" not in pluginDiscovery._COMPLETED


def test_htmlFromSpecRoundTrip(_resetRegistry):
    """등록된 렌더러의 htmlFromSpec 호출 — spec 받아 문자열 반환."""
    register(_FakeRenderer())
    out = getRenderer().htmlFromSpec({"chartType": "line"})
    assert "data-chart='line'" in out
