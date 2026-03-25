"""TF-IDF 멀티토픽 peer 발견 + consensus 예측.

사업보고서 텍스트 유사도로 경쟁그룹을 발견하고,
peer 매출 성장률 중앙값을 예측 앵커로 사용.

사용법::

    from dartlab.engines.analysis.peer import discover, consensus

    peers = discover("005930")                  # 삼성전자 peer 발견
    peers.peers[0].name                         # 'LG전자'
    peers.peers[0].similarity                   # 0.342

    pred = consensus(peers, targetYear="2024")  # peer consensus 예측
    pred.predictedGrowth                        # 12.3 (%)
    pred.nPeers                                 # 4

실험 근거:
- 098-001~005: TF-IDF peer 발견 (멀티토픽 상관 0.27 > KIND 0.16)
- 098-009: peer consensus MdAE=9.0% (naive 13.7%, sector 12.3%)
- 098-013: avg3y+peer 앙상블 MdAE=12.0% (3개년 평균)
"""

from dartlab.engines.analysis.peer.consensus import consensus
from dartlab.engines.analysis.peer.discover import discover
from dartlab.engines.analysis.peer.types import (
    ConsensusResult,
    PeerMatch,
    PeerResult,
)

__all__ = [
    "consensus",
    "discover",
    "ConsensusResult",
    "PeerMatch",
    "PeerResult",
]
