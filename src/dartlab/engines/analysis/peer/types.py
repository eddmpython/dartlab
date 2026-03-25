"""Peer discovery/consensus 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PeerMatch:
    """개별 peer 매칭 결과."""

    stockCode: str
    name: str
    similarity: float
    revenueCorrelation: float | None = None


@dataclass
class PeerResult:
    """peer 발견 결과."""

    stockCode: str
    name: str
    peers: list[PeerMatch] = field(default_factory=list)
    topicCoverage: dict[str, bool] = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """peer consensus 예측 결과."""

    stockCode: str
    name: str
    predictedGrowth: float | None = None
    peerGrowths: dict[str, float] = field(default_factory=dict)
    nPeers: int = 0
    method: str = "median"
