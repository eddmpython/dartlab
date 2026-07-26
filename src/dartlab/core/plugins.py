"""dartlab 외부 plugin 로더 — entry_points 기반 discover + introspection (T5-1).

외부 plugin 패키지가 `pyproject.toml [project.entry-points."dartlab.plugins"]`
선언으로 dartlab 에 새 recipe / engine / tool 을 등록할 수 있다.

목적:
    - 외부 기여자가 dartlab fork 없이 *분석 recipe 1 개* 추가 가능
    - 회사 내부 / private plugin 도 동일 인터페이스

API:
    discoverPlugins() -> list[PluginDescriptor]  # entry_points 스캔
    loadPlugin(name) -> module
    listPlugins() -> list[dict]   # introspection (dartlab.plugins.list 진입점)

Example::

    >>> from dartlab.core.plugins import discoverPlugins
    >>> for d in discoverPlugins():
    ...     print(d.name, d.kind, d.version)

후속 트랙:
    - T5-2 plugin example 패키지 (examples/plugin-example/)
    - T5-5 introspection API (dartlab.plugins namespace + MCP ListPlugins)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from importlib.metadata import entry_points
from types import ModuleType
from typing import Any

_ENTRY_GROUP = "dartlab.plugins"


@dataclass
class PluginDescriptor:
    """단일 plugin 메타 — entry_points 스캔 결과 (T10-4).

    Capabilities:
        plugin 의 *load 없이 알 수 있는* 메타 (name/moduleName/version/distName)
        + load 후 채워지는 메타 (kind/docstring/schema). dataclass 라 mutable.

    Fields:
        name: entry_point 이름.
        moduleName: import path (예: "dartlab_plugin_example.hello:main").
        kind: "scan"/"analysis"/"tool"/"recipe"/"example"/"unknown".
        version: 패키지 버전.
        distName: 배포 패키지 이름.
        docstring: 모듈 docstring 첫 200 자 (load 후).
        schema: PLUGIN_SCHEMA dict (load 후).

    Example:
        >>> from dartlab.core.plugins import PluginDescriptor
        >>> d = PluginDescriptor(name="x", moduleName="x.y:main")
        >>> d.kind  # default
        'unknown'

    SeeAlso:
        discoverPlugins: 메타 수집.
        loadPlugin: 모듈 import + 메타 보강.

    AIContext:
        T5-1 외부 plugin 시스템의 unit 표현.
    """

    name: str
    moduleName: str
    kind: str = "unknown"  # "scan" / "analysis" / "tool" / "recipe" / "unknown"
    version: str = "0.0.0"
    distName: str = ""  # 배포 패키지 이름
    docstring: str = ""
    schema: dict[str, Any] = field(default_factory=dict)


# 이름별 descriptor 단일 인스턴스. `loadPlugin` 의 메타 보강이 이후 조회에
# 살아남게 하는 유일한 장치다.
_DESCRIPTOR_CACHE: dict[str, PluginDescriptor] = {}


def discoverPlugins() -> list[PluginDescriptor]:  # noqa: N802  (Python convention)
    """`dartlab.plugins` entry group 의 plugin 목록 메타 수집 (T10-4).

    Capabilities:
        importlib.metadata.entry_points 스캔 — load 없이 메타만 수집 (load 비용
        피함). listPlugins / describePlugin 의 backing.

    Args:
        없음.

    Returns:
        PluginDescriptor 리스트 (sorted by name).

    Example:
        >>> from dartlab.core.plugins import discoverPlugins
        >>> for d in discoverPlugins():
        ...     print(d.name, d.kind, d.version)

    Guide:
        load 가 필요하면 loadPlugin 또는 listPlugins. 동일 name 충돌 시 첫
        발견 우선 (silent).

    SeeAlso:
        loadPlugin: 단일 plugin 모듈 import + 메타 보강.
        listPlugins: 전체 load + dict list.
        describePlugin: 단일 상세.

    Requires:
        Python 3.10+ entry_points API (3.9 fallback 포함).

    AIContext:
        T5-1 외부 plugin 시스템의 진입점.

    Raises:
        없음 — 실패는 silent skip.
    """
    # 이름별 단일 인스턴스를 공유한다. 예전에는 호출마다 새 객체를 만들어서
    # `loadPlugin` 이 보강한 kind, schema, docstring 이 그 자리에서 버려졌고
    # `listPlugins` 와 `describePlugin` 은 언제나 기본값만 내보냈다.
    descriptors: dict[str, PluginDescriptor] = {}
    try:
        eps = entry_points(group=_ENTRY_GROUP)
    except TypeError:
        # Python <= 3.9 의 dict-based API fallback
        try:
            eps = entry_points().get(_ENTRY_GROUP, [])  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            return []

    for ep in eps:
        if ep.name in descriptors:
            # 중복 — 첫 발견 우선 (logger.warn 도 가능, 본 v1 은 silent)
            continue
        # 메타 수집 — load 는 lazy
        descriptor = PluginDescriptor(
            name=ep.name,
            moduleName=ep.value,
            distName=getattr(ep.dist, "name", "") if hasattr(ep, "dist") and ep.dist else "",
            version=getattr(ep.dist, "version", "0.0.0") if hasattr(ep, "dist") and ep.dist else "0.0.0",
        )
        descriptors[ep.name] = descriptor

    for name, descriptor in descriptors.items():
        cached = _DESCRIPTOR_CACHE.get(name)
        if cached is not None and cached.moduleName == descriptor.moduleName:
            descriptors[name] = cached
        else:
            _DESCRIPTOR_CACHE[name] = descriptor
    for stale in set(_DESCRIPTOR_CACHE) - set(descriptors):
        _DESCRIPTOR_CACHE.pop(stale, None)
    return sorted(descriptors.values(), key=lambda d: d.name)


def loadPlugin(name: str) -> ModuleType:  # noqa: N802
    """지정된 plugin 의 모듈 로드 + 메타 보강 (T10-4).

    Capabilities:
        entry_point name 로 모듈 import + PLUGIN_KIND / PLUGIN_SCHEMA / docstring
        보강. 실패 시 KeyError 또는 ImportError raise.

    Args:
        name: entry_point 이름.

    Returns:
        로드된 모듈.

    Example:
        >>> from dartlab.core.plugins import loadPlugin
        >>> mod = loadPlugin("hello")
        >>> mod.main(name="dartlab")
        {'greeting': 'Hello, dartlab!'}

    Guide:
        load 후 모듈의 PLUGIN_KIND / PLUGIN_SCHEMA 변수가 PluginDescriptor 에
        반영됨. 미정의 시 default ("unknown", {}).

    SeeAlso:
        discoverPlugins / listPlugins / describePlugin.

    Requires:
        해당 plugin 패키지가 pip install 된 상태.

    AIContext:
        T5-1 외부 plugin 시스템. 외부 LLM 이 listPlugins 후 특정 plugin 호출 시.

    Raises:
        KeyError: 해당 name 의 plugin 없음.
        ImportError: 모듈 import 실패.
    """
    for d in discoverPlugins():
        if d.name == name:
            module = import_module(d.moduleName)
            # 메타 보강 — docstring + schema (선택)
            d.docstring = (getattr(module, "__doc__", "") or "").strip()[:200]
            if hasattr(module, "PLUGIN_KIND"):
                d.kind = str(module.PLUGIN_KIND)
            if hasattr(module, "PLUGIN_SCHEMA"):
                schema = module.PLUGIN_SCHEMA
                if isinstance(schema, dict):
                    d.schema = dict(schema)
            # T1-1 structured log 발급
            try:
                from dartlab.core.logger import logEvent

                logEvent("info", "plugin_loaded", name=name, kind=d.kind, version=d.version)
            except ImportError:
                pass
            return module
    raise KeyError(f"plugin not found: {name!r}")


def listPlugins() -> list[dict[str, Any]]:  # noqa: N802
    """plugin introspection — dict list 반환 (외부 LLM / MCP tool 호환) (T10-4).

    Capabilities:
        등록된 모든 dartlab.plugins entry_point 를 load 한 뒤 메타 dict 로 변환.
        외부 LLM agent / MCP tool 이 *현재 환경 가능한 plugin* 을 동적 조회.

    Args:
        없음.

    Returns:
        list[dict] — 각 entry: name / moduleName / kind / version / distName /
        docstring / schema. docstring 과 schema 는 load 후에만 채워짐.

    Example:
        >>> from dartlab.core.plugins import listPlugins
        >>> for p in listPlugins():
        ...     print(p["name"], p["kind"], p["version"])

    Guide:
        모든 plugin 을 *즉시 load* 하므로 import 비용 발생. 단순 카운트만 필요
        하면 ``discoverPlugins()`` 사용 (load 안 함).

    SeeAlso:
        discoverPlugins: load 없이 메타만.
        describePlugin: 단일 plugin 상세.
        dartlab.plugins: dartlab top-level 의 PluginMeta 기반 함수 (기존).

    Requires:
        importlib.metadata.entry_points 지원 (Python 3.10+).

    AIContext:
        외부 LLM 의 *현재 가능한 도구* 발견 — MCP server 의 ListPlugins tool 의
        backing 함수 후보 (T5-5).

    Raises:
        없음 — 개별 plugin load 실패는 silent skip.
    """
    plugins: list[dict[str, Any]] = []
    for d in discoverPlugins():
        try:
            loadPlugin(d.name)
        except (KeyError, ImportError):
            pass
        plugins.append(
            {
                "name": d.name,
                "moduleName": d.moduleName,
                "kind": d.kind,
                "version": d.version,
                "distName": d.distName,
                "docstring": d.docstring,
                "schema": d.schema,
            }
        )
    return plugins


def describePlugin(name: str) -> dict[str, Any]:  # noqa: N802
    """단일 plugin 상세 — load 후 dict 반환 (T10-4).

    Capabilities:
        listPlugins 의 단일 entry 등가. MCP server 가 사용자의 *특정 plugin
        조회* 요청 시 호출.

    Args:
        name: entry_point 이름.

    Returns:
        dict — name / moduleName / kind / version / distName / docstring / schema.

    Example:
        >>> from dartlab.core.plugins import describePlugin
        >>> describePlugin("hello")
        {'name': 'hello', 'kind': 'example', ...}

    Guide:
        plugin 이 무겁다면 load 비용 발생. 단순 존재 확인만 필요하면
        discoverPlugins 사용.

    SeeAlso:
        listPlugins: 전체.
        discoverPlugins: load 없이.

    Requires:
        해당 plugin pip install 된 상태.

    AIContext:
        T5-1 외부 plugin 시스템 + T5-5 MCP introspection 의 backing.

    Raises:
        KeyError: plugin 없음.
        ImportError: 모듈 import 실패.
    """
    for d in discoverPlugins():
        if d.name == name:
            loadPlugin(name)
            return {
                "name": d.name,
                "moduleName": d.moduleName,
                "kind": d.kind,
                "version": d.version,
                "distName": d.distName,
                "docstring": d.docstring,
                "schema": d.schema,
            }
    raise KeyError(f"plugin not found: {name!r}")


__all__ = [
    "PluginDescriptor",
    "discoverPlugins",
    "loadPlugin",
    "listPlugins",
    "describePlugin",
]
