"""peer 엔진 테스트."""

import pytest

numpy = pytest.importorskip("numpy", reason="numpy 미설치")

pytestmark = pytest.mark.unit

from dartlab.engines.analysis.peer import (
    ConsensusResult,
    PeerMatch,
    PeerResult,
    consensus,
    discover,
)


class TestTypes:
    """타입 생성 테스트."""

    def test_peerMatch(self):
        m = PeerMatch(stockCode="000660", name="SK하이닉스", similarity=0.35)
        assert m.stockCode == "000660"
        assert m.similarity == 0.35
        assert m.revenueCorrelation is None

    def test_peerResult(self):
        r = PeerResult(stockCode="005930", name="삼성전자")
        assert r.stockCode == "005930"
        assert r.peers == []
        assert r.topicCoverage == {}

    def test_consensusResult(self):
        c = ConsensusResult(stockCode="005930", name="삼성전자")
        assert c.predictedGrowth is None
        assert c.nPeers == 0
        assert c.method == "median"


class TestConsensusFromPeerResult:
    """consensus가 빈 PeerResult를 올바르게 처리하는지."""

    def test_emptyPeers(self):
        pr = PeerResult(stockCode="005930", name="삼성전자")
        result = consensus(pr)
        assert result.predictedGrowth is None
        assert result.nPeers == 0

    def test_consensusWithMockPeers(self):
        """peer가 있지만 매출 데이터가 없으면 None."""
        pr = PeerResult(
            stockCode="005930",
            name="삼성전자",
            peers=[
                PeerMatch(stockCode="FAKE01", name="가짜종목", similarity=0.5),
            ],
        )
        result = consensus(pr)
        # 가짜 종목은 매출 데이터 없으므로 None
        assert result.predictedGrowth is None


class TestDiscoverImport:
    """discover 함수가 올바르게 import 되는지."""

    def test_callable(self):
        assert callable(discover)

    def test_callable_consensus(self):
        assert callable(consensus)
