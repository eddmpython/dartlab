"""재무제표 시계열에서 판단 재료를 뽑아 답변 표면에 함께 싣는다.

왜 필요한가. DartLab 은 모델 루프를 설치형 CLI 에 넘긴 중개상이라 답변을 직접 고쳐 쓸 수
없다. 답변 품질을 올리는 유일한 정공법은 **건네주는 근거 자체를 판단 가능한 형태로 만드는
것**이다. 원시 수치 표만 주면 마진과 증감률과 기저효과 판별을 모델이 매번 손으로 해야 하고,
그 계산을 잘하는 모델과 못하는 모델 사이에서 답변 품질이 갈린다.

실측 배경(2026-08-06). 강한 모델은 손익 표만 받고도 원가율 하락이 이익 개선의 몸통임을
스스로 찾아냈고 2023FY 저점이 기저효과임을 지적했다. 같은 표를 받은 약한 모델은 "영업이익
5 배 성장" 으로 끝낼 수 있다. 그 차이를 모델에 맡기지 않고 표에 실어 보낸다.

계산은 이미 손에 있는 시계열만 쓴다. 추가 조회가 없으므로 지연이 늘지 않는다.
`Panel` wide DataFrame 의 형태와 내용은 건드리지 않는다. 여기서 만드는 것은 표현 계층의
병존 projection 이다.
"""

from __future__ import annotations

from .anchors import balanceTripwires, contextMarkdown, sectorPositionLines
from .derived import (
    cashFlowAnchors,
    cashFlowPattern,
    derivedRows,
    insightMarkdown,
    observedRangeAnchors,
    positionNotes,
    profitBridge,
)

__all__ = [
    "balanceTripwires",
    "cashFlowAnchors",
    "cashFlowPattern",
    "contextMarkdown",
    "derivedRows",
    "insightMarkdown",
    "observedRangeAnchors",
    "positionNotes",
    "profitBridge",
    "sectorPositionLines",
]
