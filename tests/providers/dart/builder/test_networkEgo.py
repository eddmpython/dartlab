"""관계망 ego 진입점 단위 가드.

서버 엔드포인트가 예전에 ``company._ensureNetwork()`` 를 불렀다. 그 헬퍼는 모듈 함수로
옮겨졌고 Company 에 남지 않아 AttributeError 가 났는데, 서버의 except 가 그것을 흡수해
어느 회사든 관계망 없음으로 응답했다. 이름 있는 진입점이 그 자리를 대신한다.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.providers.dart.builder import scanAggregator


class _Company:
    stockCode = "005930"

    def __init__(self) -> None:
        self._cache: dict = {}


class TestBuildNetworkEgo:
    def test_returns_ego_payload(self):
        data = {"code_to_group": {"005930": "삼성"}}
        full = {"nodes": [], "edges": []}
        ego = {"nodes": [{"id": "005930"}], "edges": []}

        with (
            patch.object(scanAggregator, "_ensureNetwork", return_value=(data, full)),
            patch("dartlab.scan.network.exportEgo", return_value=ego) as exportEgo,
        ):
            out = scanAggregator.buildNetworkEgo(_Company(), hops=2)

        assert out == ego
        exportEgo.assert_called_once_with(data, full, "005930", hops=2)

    def test_missing_graph_is_none(self):
        with patch.object(scanAggregator, "_ensureNetwork", return_value=None):
            assert scanAggregator.buildNetworkEgo(_Company()) is None


class TestMarketScanMemo:
    def test_axis_scan_is_built_once_per_process(self):
        """capital 축은 실측 회사당 8 초다. 회사가 바뀌어도 시장 전체를 다시 훑지 않아야 한다."""
        scanAggregator._marketScan.cache_clear()
        frame = object()
        try:
            with patch("dartlab.scan.capital.scanCapital", return_value=frame) as scanCapital:
                first = scanAggregator._ensureCapital(_Company())
                second = scanAggregator._ensureCapital(_Company())

            assert first is frame
            assert second is frame
            assert scanCapital.call_count == 1
        finally:
            scanAggregator._marketScan.cache_clear()

    def test_axes_do_not_evict_each_other(self):
        """축이 넷이라 캐시 칸도 넷이어야 한다. 한 칸이면 축을 번갈아 부를 때 매번 다시 훑는다."""
        scanAggregator._marketScan.cache_clear()
        try:
            with (
                patch("dartlab.scan.capital.scanCapital", return_value="capital") as scanCapital,
                patch("dartlab.scan.debt.scanDebt", return_value="debt") as scanDebt,
            ):
                scanAggregator._ensureCapital(_Company())
                scanAggregator._ensureDebt(_Company())
                scanAggregator._ensureCapital(_Company())

            assert scanCapital.call_count == 1
            assert scanDebt.call_count == 1
        finally:
            scanAggregator._marketScan.cache_clear()

    def test_every_axis_is_wired(self):
        """축 표와 _ensure 진입점이 어긋나면 KeyError 로 죽는다."""
        assert set(scanAggregator._SCAN_AXES) == {"governance", "workforce", "capital", "debt"}


class TestMarketGraphMemo:
    def test_graph_is_built_once_per_process(self):
        """그래프 빌드는 실측 735 초다. 회사가 바뀌어도 다시 만들지 않아야 한다."""
        scanAggregator._marketGraph.cache_clear()
        data = {"code_to_group": {}}
        full = {"nodes": []}
        try:
            with (
                patch("dartlab.scan.network.buildGraph", return_value=data) as buildGraph,
                patch("dartlab.scan.network.exportFull", return_value=full),
            ):
                first = scanAggregator._ensureNetwork(_Company())
                second = scanAggregator._ensureNetwork(_Company())

            assert first == (data, full)
            assert second == (data, full)
            assert buildGraph.call_count == 1
        finally:
            scanAggregator._marketGraph.cache_clear()
