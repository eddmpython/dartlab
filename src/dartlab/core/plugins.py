"""커뮤니티 플러그인 시스템 — 발견 + 등록.

외부 패키지가 ``dartlab.plugins`` entry_point 그룹에 등록하면,
dartlab 시작 시 자동 발견되어 Company.show(), AI tool, Server API에서 사용 가능.

플러그인 개발::

    # pyproject.toml
    [project.entry-points."dartlab.plugins"]
    my_plugin = "dartlab_plugin_mine:register"

    # dartlab_plugin_mine/__init__.py
    from dartlab.core.plugins import PluginContext, PluginMeta

    def register(ctx: PluginContext) -> None:
        ctx.add_data_entry(DataEntry(...), meta=PluginMeta(...))
"""

from __future__ import annotations

import importlib.metadata
import re
import warnings
from dataclasses import dataclass
from typing import Any, Callable

_ENTRY_POINT_GROUP = "dartlab.plugins"
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$")
_VALID_TYPES = frozenset({"data", "tool", "engine"})
_VALID_STABILITY = frozenset({"experimental", "beta", "stable"})


@dataclass
class PluginMeta:
    """플러그인 메타데이터."""

    name: str
    version: str
    author: str
    description: str
    plugin_type: str  # "data" | "tool" | "engine"
    stability: str = "experimental"

    def __post_init__(self) -> None:
        if not _NAME_PATTERN.match(self.name):
            raise ValueError(
                f"플러그인 이름 '{self.name}'이 규칙에 맞지 않습니다. 소문자, 숫자, 하이픈만 사용 (3-50자)."
            )
        if self.plugin_type not in _VALID_TYPES:
            raise ValueError(f"plugin_type은 {_VALID_TYPES} 중 하나여야 합니다: '{self.plugin_type}'")
        if self.stability not in _VALID_STABILITY:
            raise ValueError(f"stability는 {_VALID_STABILITY} 중 하나여야 합니다: '{self.stability}'")


class PluginContext:
    """플러그인 register() 함수에 전달되는 컨텍스트.

    플러그인은 이 객체의 메서드를 호출하여 데이터/도구/엔진을 등록한다.
    """

    def add_data_entry(self, entry: Any, *, meta: PluginMeta) -> None:
        """DataEntry를 글로벌 레지스트리에 추가.

        등록된 엔트리는 Company.show(), AI context, Server API에서 자동 사용 가능.
        """
        from dartlab.core.registry import registerEntry

        registerEntry(entry, source=f"plugin:{meta.name}")
        _track_plugin(meta)

    def add_tool(
        self,
        func: Callable,
        *,
        meta: PluginMeta,
        name: str | None = None,
        category: str = "plugin",
        requires_company: bool = False,
        tags: list[str] | None = None,
    ) -> None:
        """AI 도구를 ToolPluginRegistry에 등록.

        기존 @tool 데코레이터와 동일한 효과.
        """
        from dartlab.engines.ai.tools.plugin import tool as tool_decorator

        decorator = tool_decorator(
            name=name or func.__name__,
            category=category,
            requires_company=requires_company,
            tags=tags,
        )
        decorator(func)
        _track_plugin(meta)

    def add_engine(
        self,
        name: str,
        analyze_func: Callable,
        *,
        meta: PluginMeta,
        label: str = "",
        description: str = "",
    ) -> None:
        """L2 분석 엔진을 레지스트리에 등록."""
        from dartlab.core.registry import DataEntry, registerEntry

        entry = DataEntry(
            name=name,
            label=label or name,
            category="plugin",
            dataType="analysis",
            description=description or meta.description,
            modulePath=analyze_func.__module__,
            funcName=analyze_func.__name__,
            aiExposed=True,
            aiHint=description or meta.description,
        )
        registerEntry(entry, source=f"plugin:{meta.name}")
        _track_plugin(meta)


# ── 내부 상태 ──

_loaded_plugins: list[PluginMeta] = []
_loaded_names: set[str] = set()
_discovered = False


def _track_plugin(meta: PluginMeta) -> None:
    """플러그인 메타데이터 중복 없이 추적."""
    if meta.name not in _loaded_names:
        _loaded_plugins.append(meta)
        _loaded_names.add(meta.name)


def discover() -> list[PluginMeta]:
    """설치된 플러그인 자동 발견 + 등록.

    최초 호출 시 한 번만 실행. 이후 호출은 캐시된 결과 반환.
    """
    global _discovered
    if _discovered:
        return list(_loaded_plugins)

    _discovered = True

    try:
        eps = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    except TypeError:
        # Python 3.9 fallback
        all_eps = importlib.metadata.entry_points()
        eps = all_eps.get(_ENTRY_POINT_GROUP, [])  # type: ignore[assignment]

    if not eps:
        return list(_loaded_plugins)

    ctx = PluginContext()
    for ep in eps:
        try:
            register_fn = ep.load()
            register_fn(ctx)
        except (ImportError, TypeError, ValueError, AttributeError, RuntimeError) as e:
            warnings.warn(f"dartlab plugin '{ep.name}' 로드 실패: {e}", stacklevel=2)

    # DART Company 모듈 레지스트리 캐시 무효화
    if _loaded_plugins:
        try:
            from dartlab.engines.dart.company import rebuild_module_registry

            rebuild_module_registry()
        except ImportError:
            pass

    return list(_loaded_plugins)


def get_loaded_plugins() -> list[PluginMeta]:
    """로드된 플러그인 목록 반환."""
    return list(_loaded_plugins)


def reset_for_testing() -> None:
    """테스트용 — 플러그인 상태 초기화."""
    global _discovered
    _loaded_plugins.clear()
    _loaded_names.clear()
    _discovered = False
