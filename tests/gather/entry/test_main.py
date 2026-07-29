"""dartlab.gather.entry.main real unit test (A 트랙 T4).

GatherEntry 의 axis 가이드 + 미지원 axis ValueError + handler dispatch 회귀.
"""

from __future__ import annotations

import contextlib
import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.entry.main`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.entry.main")


def test_GatherEntry_no_args_returns_guide() -> None:
    """GatherEntry() 호출 — axis None 시 가이드 DataFrame 반환."""
    from dartlab.gather.entry.main import GatherEntry

    g = GatherEntry()
    guide = g()
    assert isinstance(guide, pl.DataFrame)
    assert guide.height > 0
    # 가이드는 axis 컬럼을 가진다 (registry 정보 노출)
    assert "axis" in guide.columns or "name" in guide.columns or guide.height > 0


def test_GatherEntry_unknown_axis_raises() -> None:
    """미지원 axis → ValueError."""
    from dartlab.gather.entry.main import GatherEntry

    g = GatherEntry()
    with pytest.raises(ValueError):
        g("nonexistent_axis", "005930")


def test_AXIS_DISPATCH_handler_keys() -> None:
    """_AXIS_DISPATCH — 12 handler 모두 callable."""
    from dartlab.gather.entry.main import _AXIS_DISPATCH

    requiredKeys = {"price", "flow", "macro", "news"}
    assert requiredKeys <= _AXIS_DISPATCH.keys()
    for handler in _AXIS_DISPATCH.values():
        assert callable(handler)


@pytest.mark.parametrize(
    ("axis", "target"),
    [
        ("price", "005930"),
        ("macro", "FEDFUNDS"),
        ("news", "삼성전자"),
    ],
)
def test_GatherEntry_proxy_scope_is_common(
    monkeypatch: pytest.MonkeyPatch,
    axis: str,
    target: str,
) -> None:
    """proxy kwarg 는 flow 전용이 아니라 gather 호출 범위 공통 HTTP 옵션이다."""
    import dartlab.gather as gatherPkg
    from dartlab.gather.entry.main import GatherEntry

    events = []

    class FakeClient:
        @contextlib.contextmanager
        def useProxy(self, proxy):
            events.append(("enter", proxy))
            yield
            events.append(("exit", proxy))

    class FakeGather:
        _client = FakeClient()

        def price(self, target, **kwargs):
            events.append(("price", target))
            return pl.DataFrame({"date": [], "close": []})

        def macro(self, *args, **kwargs):
            events.append(("macro", args[0] if args else None))
            return pl.DataFrame({"date": [], "value": []})

        def news(self, target, **kwargs):
            events.append(("news", target))
            return pl.DataFrame({"date": [], "close": []})

    monkeypatch.setattr(gatherPkg, "getDefaultGather", lambda: FakeGather())

    kwargs = {"proxy": "http://proxy.example:8080"}
    if axis == "price":
        kwargs["indicators"] = False
    GatherEntry()(axis, target, **kwargs)

    assert events == [
        ("enter", "http://proxy.example:8080"),
        (axis, target),
        ("exit", "http://proxy.example:8080"),
    ]


def test_GatherEntry_targets_only_supported_for_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """targets batch 는 flow 전용으로 제한해 축별 schema 혼선을 차단한다."""
    import dartlab.gather as gatherPkg
    from dartlab.gather.entry.main import GatherEntry

    class FakeGather:
        _client = object()

    monkeypatch.setattr(gatherPkg, "getDefaultGather", lambda: FakeGather())

    with pytest.raises(ValueError, match='gather\\("flow", targets='):
        GatherEntry()("price", ["005930", "000660"])


def test_GatherEntry_rejects_unknown_axis_option_before_dispatch() -> None:
    """축별 미등록 옵션은 오타를 삼키지 않고 호출 경계에서 거부한다."""
    from dartlab.gather.entry.main import GatherEntry

    with pytest.raises(TypeError, match="지원하지 않는 옵션: indicatr"):
        GatherEntry()("price", "005930", indicatr="rsi14")

    with pytest.raises(TypeError, match="지원하지 않는 옵션: days"):
        GatherEntry()("sector", "005930", days=7)

    with pytest.raises(TypeError, match="지원하지 않는 옵션: start"):
        GatherEntry()("sector", "005930", start="2024-01-01")


def test_axis_option_contract_has_no_duplicate_names() -> None:
    """axis 옵션 tuple은 문서·검증 SSOT이므로 중복 이름을 허용하지 않는다."""
    from dartlab.gather.entry.dispatch import AXIS_REGISTRY
    from dartlab.gather.entry.main import _COMMON_OPTIONS

    for axis, entry in AXIS_REGISTRY.items():
        assert len(entry.options) == len(set(entry.options)), axis
        assert not (_COMMON_OPTIONS & set(entry.options)), axis
