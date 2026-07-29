"""플러그인 시스템 테스트.

플러그인 발견, 등록, 충돌 검사, 레지스트리 연동을 검증한다.
데이터 로드 없이 순수 Python 검사 → unit 마커.
"""

import pytest

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# PluginMeta 검증
# ══════════════════════════════════════


class TestPluginMeta:
    """PluginMeta 유효성 검증."""

    def test_valid_meta(self):
        from dartlab.plugins import PluginMeta

        meta = PluginMeta(
            name="my-plugin",
            version="0.1.0",
            author="test",
            description="Test plugin",
            plugin_type="data",
        )
        assert meta.name == "my-plugin"
        assert meta.stability == "experimental"

    def test_invalid_name_uppercase(self):
        from dartlab.plugins import PluginMeta

        with pytest.raises(ValueError, match="규칙에 맞지 않습니다"):
            PluginMeta(
                name="MyPlugin",
                version="0.1.0",
                author="test",
                description="Bad name",
                plugin_type="data",
            )

    def test_invalid_name_too_short(self):
        from dartlab.plugins import PluginMeta

        with pytest.raises(ValueError, match="규칙에 맞지 않습니다"):
            PluginMeta(
                name="ab",
                version="0.1.0",
                author="test",
                description="Too short",
                plugin_type="data",
            )

    def test_invalid_plugin_type(self):
        from dartlab.plugins import PluginMeta

        with pytest.raises(ValueError, match="plugin_type"):
            PluginMeta(
                name="my-plugin",
                version="0.1.0",
                author="test",
                description="Bad type",
                plugin_type="invalid",
            )

    def test_invalid_stability(self):
        from dartlab.plugins import PluginMeta

        with pytest.raises(ValueError, match="stability"):
            PluginMeta(
                name="my-plugin",
                version="0.1.0",
                author="test",
                description="Bad stability",
                plugin_type="data",
                stability="alpha",
            )


# ══════════════════════════════════════
# Registry 동적 등록
# ══════════════════════════════════════


class TestRegistryDynamic:
    """registerEntry / unregisterEntry 동작 검증."""

    def test_register_and_query(self):
        from dartlab.core.registry import DataEntry, getEntry, registerEntry, unregisterEntry

        entry = DataEntry(
            name="__test_plugin_entry",
            label="테스트",
            category="plugin",
            dataType="dataframe",
            description="테스트 플러그인 엔트리",
        )
        try:
            registerEntry(entry, source="test")
            found = getEntry("__test_plugin_entry")
            assert found is not None
            assert found.label == "테스트"
        finally:
            unregisterEntry("__test_plugin_entry")

    def test_unregister_removes(self):
        from dartlab.core.registry import DataEntry, getEntry, registerEntry, unregisterEntry

        entry = DataEntry(
            name="__test_remove_entry",
            label="제거테스트",
            category="plugin",
            dataType="dataframe",
            description="제거 테스트",
        )
        registerEntry(entry, source="test")
        unregisterEntry("__test_remove_entry")
        assert getEntry("__test_remove_entry") is None

    def test_name_collision_raises(self):
        from dartlab.core.registry import PluginNameCollisionError, getEntry, registerEntry

        # "annual.IS"는 core에 이미 존재하는 이름
        existing = getEntry("annual.IS")
        assert existing is not None  # 존재 확인

        from dartlab.core.registry import DataEntry

        entry = DataEntry(
            name="annual.IS",
            label="충돌",
            category="plugin",
            dataType="dataframe",
            description="충돌 테스트",
        )
        with pytest.raises(PluginNameCollisionError, match="이미 존재"):
            registerEntry(entry)

    def test_category_filter_includes_plugin(self):
        from dartlab.core.registry import DataEntry, getEntries, registerEntry, unregisterEntry

        entry = DataEntry(
            name="__test_cat_entry",
            label="카테고리",
            category="plugin",
            dataType="dataframe",
            description="카테고리 필터 테스트",
        )
        try:
            registerEntry(entry, source="test")
            plugin_entries = getEntries(category="plugin")
            names = [e.name for e in plugin_entries]
            assert "__test_cat_entry" in names
        finally:
            unregisterEntry("__test_cat_entry")


# ══════════════════════════════════════
# PluginContext 통합
# ══════════════════════════════════════


class TestPluginContext:
    """PluginContext를 통한 등록 검증."""

    def test_add_data_entry(self):
        from dartlab.core.registry import DataEntry, getEntry, unregisterEntry
        from dartlab.plugins import PluginContext, PluginMeta, resetForTesting

        meta = PluginMeta(
            name="test-data-plugin",
            version="0.1.0",
            author="test",
            description="테스트",
            plugin_type="data",
        )
        entry = DataEntry(
            name="__test_ctx_data",
            label="CTX데이터",
            category="plugin",
            dataType="dataframe",
            description="PluginContext 테스트",
        )
        ctx = PluginContext()
        try:
            ctx.addDataEntry(entry, meta=meta)
            assert getEntry("__test_ctx_data") is not None
        finally:
            unregisterEntry("__test_ctx_data")
            resetForTesting()

    def test_add_tool(self):
        from dartlab.ai.tools import listToolNames, unregisterTool
        from dartlab.plugins import PluginContext, PluginMeta, resetForTesting

        meta = PluginMeta(
            name="test-tool-plugin",
            version="0.1.0",
            author="test",
            description="테스트",
            plugin_type="tool",
        )

        def my_test_tool(query: str) -> str:
            """테스트 도구."""
            return f"result: {query}"

        ctx = PluginContext()
        try:
            ctx.addTool(my_test_tool, meta=meta, name="__test_ctx_tool")
            assert "__test_ctx_tool" in listToolNames()
        finally:
            unregisterTool("__test_ctx_tool")
            resetForTesting()

    def test_add_engine(self):
        from dartlab.core.registry import getEntry, unregisterEntry
        from dartlab.plugins import PluginContext, PluginMeta, resetForTesting

        meta = PluginMeta(
            name="test-engine-plugin",
            version="0.1.0",
            author="test",
            description="테스트 엔진",
            plugin_type="engine",
        )

        def analyze_test(stockCode: str) -> dict:
            return {"score": 42}

        ctx = PluginContext()
        try:
            ctx.addEngine(
                "__test_ctx_engine",
                analyze_test,
                meta=meta,
                label="테스트엔진",
                description="테스트 분석 엔진",
            )
            found = getEntry("__test_ctx_engine")
            assert found is not None
            assert found.category == "plugin"
        finally:
            unregisterEntry("__test_ctx_engine")
            resetForTesting()


# ══════════════════════════════════════
# Discovery
# ══════════════════════════════════════


class TestDiscovery:
    """discover() 함수 동작 검증."""

    def test_discover_returns_list(self):
        from dartlab.plugins import discover, resetForTesting

        resetForTesting()
        result = discover()
        assert isinstance(result, list)
        # 플러그인 미설치 상태에서 빈 리스트
        resetForTesting()

    def test_discover_idempotent(self):
        from dartlab.plugins import discover, resetForTesting

        resetForTesting()
        r1 = discover()
        r2 = discover()
        assert r1 == r2
        resetForTesting()

    def test_plugin_tracking_no_duplicates(self):
        from dartlab.plugins import PluginMeta, _trackPlugin, getLoadedPlugins, resetForTesting

        resetForTesting()
        meta = PluginMeta(
            name="test-tracking",
            version="0.1.0",
            author="test",
            description="트래킹 테스트",
            plugin_type="data",
        )
        _trackPlugin(meta)
        _trackPlugin(meta)  # 중복 호출
        plugins = getLoadedPlugins()
        names = [p.name for p in plugins]
        assert names.count("test-tracking") == 1
        resetForTesting()


# ══════════════════════════════════════
# Module Registry 재구축
# ══════════════════════════════════════


class TestModuleRegistryRebuild:
    """dart/company.py의 lazy 모듈 레지스트리 재구축 검증."""

    def test_rebuild_invalidates_cache(self):
        from dartlab.providers.dart.company import (
            _getModuleRegistry,
            rebuildModuleRegistry,
        )

        # 최초 구축
        reg1 = _getModuleRegistry()
        assert reg1 is not None
        assert len(reg1) > 0

        # 무효화 후 재구축
        rebuildModuleRegistry()
        reg2 = _getModuleRegistry()
        assert reg2 is not None
        assert len(reg2) == len(reg1)  # 플러그인 미추가 시 동일 크기

    def test_get_module_index_consistent(self):
        from dartlab.providers.dart.company import (
            _getModuleIndex,
            _getModuleRegistry,
        )

        registry = _getModuleRegistry()
        index = _getModuleIndex()
        # 인덱스 크기 == 레지스트리 크기
        assert len(index) == len(registry)
        # 모든 인덱스 값이 유효 범위
        for name, idx in index.items():
            assert 0 <= idx < len(registry)
            assert registry[idx][1] == name
