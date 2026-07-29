"""커뮤니티 플러그인 시스템 — 발견 + 등록.

외부 패키지가 ``dartlab.plugins`` entry_point 그룹에 등록하면,
dartlab 시작 시 자동 발견되어 Company.panel(), AI tool, Server API에서 사용 가능.

플러그인 개발::

    # pyproject.toml
    [project.entry-points."dartlab.plugins"]
    my_plugin = "dartlab_plugin_mine:register"

    # dartlab_plugin_mine/__init__.py
    from dartlab.plugins import PluginContext, PluginMeta

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

    def addDataEntry(self, entry: Any, *, meta: PluginMeta) -> None:
        """DataEntry를 글로벌 레지스트리에 추가.

        등록된 엔트리는 Company.panel(), AI context, Server API에서 자동 사용 가능.
        """
        from dartlab.core.registry import registerEntry

        registerEntry(entry, source=f"plugin:{meta.name}")
        _trackPlugin(meta)

    def addTool(
        self,
        func: Callable,
        *,
        meta: PluginMeta,
        name: str | None = None,
        category: str = "plugin",
        requiresCompany: bool = False,
        tags: list[str] | None = None,
    ) -> None:
        """AI 도구를 canonical tool registry에 등록.

        Plugin tool도 Workbench/MCP가 보는 단일 도구 레지스트리에 붙는다.
        """
        from dartlab.ai.tools import registerTool

        tagsText = f" tags={','.join(tags)}" if tags else ""
        description = (func.__doc__ or "").strip() or f"{meta.name} plugin tool"
        description = f"{description} category={category} requires_company={requiresCompany}{tagsText}"
        registerTool(
            name=name or func.__name__,
            func=func,
            description=description,
        )
        _trackPlugin(meta)

    def addEngine(
        self,
        name: str,
        analyzeFunc: Callable,
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
            modulePath=analyzeFunc.__module__,
            funcName=analyzeFunc.__name__,
        )
        registerEntry(entry, source=f"plugin:{meta.name}")
        _trackPlugin(meta)


# ── 내부 상태 ──

_loadedPlugins: list[PluginMeta] = []
_loadedNames: set[str] = set()
_discovered = False


def _trackPlugin(meta: PluginMeta) -> None:
    """플러그인 메타데이터 중복 없이 추적."""
    if meta.name not in _loadedNames:
        _loadedPlugins.append(meta)
        _loadedNames.add(meta.name)


def discover() -> list[PluginMeta]:
    """설치된 플러그인 자동 발견 + 등록.

    최초 호출 시 한 번만 실행. 이후 호출은 캐시된 결과 반환.
    """
    global _discovered
    if _discovered:
        return list(_loadedPlugins)

    _discovered = True

    try:
        eps = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    except TypeError:
        # Python 3.9 fallback
        all_eps = importlib.metadata.entry_points()
        eps = all_eps.get(_ENTRY_POINT_GROUP, [])  # type: ignore[assignment]

    if not eps:
        return list(_loadedPlugins)

    ctx = PluginContext()
    for ep in eps:
        try:
            register_fn = ep.load()
            register_fn(ctx)
        except (ImportError, TypeError, ValueError, AttributeError, RuntimeError) as e:
            warnings.warn(f"dartlab plugin '{ep.name}' 로드 실패: {e}", stacklevel=2)

    # DART Company 모듈 레지스트리 캐시 무효화
    if _loadedPlugins:
        try:
            from dartlab.providers.dart.company import rebuildModuleRegistry

            rebuildModuleRegistry()
        except ImportError:
            pass

    return list(_loadedPlugins)


def getLoadedPlugins() -> list[PluginMeta]:
    """로드된 플러그인 목록 반환."""
    return list(_loadedPlugins)


def rediscover() -> list[PluginMeta]:
    """플러그인을 다시 스캔. pip install 후 호출하면 재시작 없이 인식."""
    global _discovered
    _loadedPlugins.clear()
    _loadedNames.clear()
    _discovered = False
    return discover()


def resetForTesting() -> None:
    """테스트용 — 플러그인 상태 초기화."""
    global _discovered
    _loadedPlugins.clear()
    _loadedNames.clear()
    _discovered = False


# `help` 가 `dartlab.plugins.listPlugins` 를 안내하는데 그 이름이 여기 없어서
# 안내대로 따라 치면 AttributeError 였다. 조회 구현은 `core.plugins` 가 이미
# 가지고 있으므로 여기서 그 이름을 세워 안내가 실재하게 만든다. 두 모듈이 같은
# entry point group 을 각자 읽는 문제는 외부 플러그인 계약을 바꾸는 일이라
# 여기서 손대지 않는다.
def listPlugins() -> list[dict[str, Any]]:
    """설치된 dartlab plugin 목록을 메타와 함께 돌려준다."""

    from dartlab.core.plugins import listPlugins as _listPlugins

    return _listPlugins()


def describePlugin(name: str) -> dict[str, Any]:
    """plugin 하나의 상세 메타를 돌려준다."""

    from dartlab.core.plugins import describePlugin as _describePlugin

    return _describePlugin(name)
