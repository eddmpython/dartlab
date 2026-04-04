"""macro 보고서 블록 카탈로그 — 3막 서사 구조 정의.

review/catalog.py 패턴. macro 경제분석 보고서의 섹션과 블록 메타데이터.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroSectionMeta:
    """macro 보고서 섹션 메타데이터."""

    key: str
    partId: str
    title: str
    helper: str  # 이 섹션에서 봐야 할 것
    aiGuide: str  # AI에게 전달할 분석 관점


SECTIONS: list[MacroSectionMeta] = [
    MacroSectionMeta(
        "dashboard", "0", "경제 신호등",
        "11축의 상태를 한눈에. 초록=우호, 노랑=중립, 빨강=경계.",
        "종합 점수와 기여도를 분석하고, 가장 주목할 축을 식별하라.",
    ),
    MacroSectionMeta(
        "phase", "1", "제1막: 국면 진단",
        "사이클 4국면 + 금리 방향 + 자산 신호. 지금 어디에 있는가.",
        "현재 경기 국면을 한 문장으로 정의하고, 핵심 근거 3개를 제시하라.",
    ),
    MacroSectionMeta(
        "causation", "2", "제2막: 인과 역추적",
        "왜 이 국면인가. 전파 경로 + 구조적 위험 + 기업 실태.",
        "현 국면을 만든 인과 체인을 3-4단계로 서술하라. 전파 경로를 명시하라.",
    ),
    MacroSectionMeta(
        "outlook", "3", "제3막: 전망과 리스크",
        "침체확률 + 시나리오 + 리스크. 다음에 무엇이 올 것인가.",
        "기본/상방/하방 시나리오를 구분하고, 각각의 트리거를 명시하라.",
    ),
    MacroSectionMeta(
        "allocation", "4", "자산배분 시사점",
        "포트폴리오 매핑 + 40전략 요약. So What.",
        "현재 환경에서의 자산배분 근거를 설명하고, 가장 주목할 전략 3개를 선택하라.",
    ),
]
