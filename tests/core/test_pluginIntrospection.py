"""plugin 조회 계약 회귀.

두 결함이 겹쳐 있었다.

`loadPlugin` 이 메타를 보강해도 그 자리에서 버려졌다. `discoverPlugins` 가 호출마다 새
객체를 만들어 돌려주기 때문에, 보강 대상과 이후 조회 대상이 서로 다른 객체였다. 그래서
`PLUGIN_KIND` 와 `PLUGIN_SCHEMA` 를 선언한 플러그인도 조회하면 언제나 kind 'unknown',
schema 빈 dict 로 보였다. MCP 와 외부 LLM 이 보는 표면이 통째로 비어 있던 셈이다.

`help` 는 `dartlab.plugins.listPlugins` 를 안내하는데 그 이름이 거기에 없었다. 안내대로
따라 치면 AttributeError 였다.
"""

from __future__ import annotations

import sys
import types
from unittest import mock

import pytest

import dartlab.core.plugins as corePlugins
import dartlab.plugins as topLevelPlugins


class _FakeEntryPoint:
    name = "fakeIntrospect"
    value = "fakeDartlabIntrospectPlugin"
    dist = None


@pytest.fixture
def fakePlugin():
    """kind 와 schema 를 선언한 가짜 플러그인을 등록한다."""

    module = types.ModuleType("fakeDartlabIntrospectPlugin")
    module.__doc__ = "테스트용 가짜 플러그인."
    module.PLUGIN_KIND = "scan"
    module.PLUGIN_SCHEMA = {"input": "stockCode"}
    sys.modules["fakeDartlabIntrospectPlugin"] = module
    corePlugins._DESCRIPTOR_CACHE.clear()
    try:
        with mock.patch.object(corePlugins, "entry_points", lambda **_kw: [_FakeEntryPoint()]):
            yield module
    finally:
        sys.modules.pop("fakeDartlabIntrospectPlugin", None)
        corePlugins._DESCRIPTOR_CACHE.clear()


def testDiscoveryStartsWithDefaultMetadata(fakePlugin) -> None:
    """load 전에는 아직 모른다. 그 상태 자체는 정상이다."""

    descriptor = corePlugins.discoverPlugins()[0]

    assert descriptor.kind == "unknown"
    assert descriptor.schema == {}


def testLoadedMetadataSurvivesIntoLaterLookups(fakePlugin) -> None:
    """보강한 메타가 다음 조회에서 사라지면 조회 표면이 언제나 비어 있게 된다."""

    corePlugins.loadPlugin("fakeIntrospect")
    entry = corePlugins.listPlugins()[0]

    assert entry["kind"] == "scan"
    assert entry["schema"] == {"input": "stockCode"}
    assert entry["docstring"].startswith("테스트용")


def testDescribeReportsTheDeclaredMetadata(fakePlugin) -> None:
    """단건 상세도 같은 인스턴스를 봐야 목록과 답이 어긋나지 않는다."""

    corePlugins.loadPlugin("fakeIntrospect")
    described = corePlugins.describePlugin("fakeIntrospect")

    assert described["kind"] == "scan"
    assert described["schema"] == {"input": "stockCode"}


def testDiscoveryReturnsTheSameInstanceAcrossCalls(fakePlugin) -> None:
    """같은 이름은 같은 객체여야 보강이 누적된다."""

    first = corePlugins.discoverPlugins()[0]
    second = corePlugins.discoverPlugins()[0]

    assert first is second


def testDocumentedTopLevelPathResolves() -> None:
    """`help` 가 안내하는 이름이 실재해야 한다. 없으면 안내가 거짓말이 된다."""

    assert callable(topLevelPlugins.listPlugins)
    assert callable(topLevelPlugins.describePlugin)


def testDocumentedPathReturnsTheSameAnswerAsTheImplementation(fakePlugin) -> None:
    """안내 경로와 구현이 다른 답을 내면 두 개의 진실이 생긴다."""

    corePlugins.loadPlugin("fakeIntrospect")

    assert topLevelPlugins.listPlugins() == corePlugins.listPlugins()
