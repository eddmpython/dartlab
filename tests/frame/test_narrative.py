"""frame.narrative 단일 메커니즘 불변식.

데이터 없이 항상 실행 가능(카탈로그 앵커 구동 계약 검증). 실제 추출은 로컬 panel 필요라
requires_data 스팟체크(별도). 본 파일은 앵커 계약 + 비대상 None 계약만.
"""

from __future__ import annotations

from dartlab.core.extractionCatalog import getExtractionConcepts
from dartlab.frame.narrative import extractNarrative, listNarrativeConcepts


def test_listNarrativeCoversCatalog():
    """listNarrativeConcepts 는 DART-anchored narrative 개념을 전수 커버한다.

    US-only narrative(edgarOnly Item, narrativeAnchor 없음)는 extractNarrative(DART 전용) 대상 아니라 제외.
    """
    listed = {c["conceptId"] for c in listNarrativeConcepts()}
    catalog = {c.conceptId for c in getExtractionConcepts(category="narrative") if c.narrativeAnchor is not None}
    assert listed == catalog


def test_everyNarrativeHasAnchorKeyword():
    """모든 narrative 개념은 비어있지 않은 sectionLeaf 키워드 앵커를 가진다."""
    for c in listNarrativeConcepts():
        assert c["keyword"], f"{c['conceptId']}: 앵커 키워드 누락"


def test_nonKrReturnsNone():
    """kr 외 시장은 None(정직, US 는 SEC Item 별도 경로)."""
    assert extractNarrative("005930", "narrative.salesOrder", marketNs="us") is None


def test_nonNarrativeConceptReturnsNone():
    """narrative 아닌 conceptId 는 None(계약 방어)."""
    assert extractNarrative("005930", "note.tax") is None
    assert extractNarrative("005930", "존재하지않음") is None
