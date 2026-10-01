"""공개 Company.topics에 표시된 모든 topic의 본문과 출처를 실제로 조회한다."""

from __future__ import annotations

import gc

import polars as pl
import pytest

from tests.conftest import SAMSUNG, _has_data

MISSING_DATA = "__missing_samsung_panel__"


def _publicTopics() -> list[str]:
    """은퇴한 내부 함수 등록부 대신 사용자가 보는 데이터 지도를 따른다."""
    if not _has_data(SAMSUNG, "panel"):
        return [MISSING_DATA]
    from dartlab import Company

    company = Company(SAMSUNG)
    try:
        catalog = company.topics
        assert isinstance(catalog, pl.DataFrame) and "topic" in catalog.columns
        topics = sorted(set(catalog["topic"].drop_nulls().to_list()))
        assert topics, "Company.topics가 비어 있어 전수 검사를 실행할 수 없습니다"
        return topics
    finally:
        del company
        gc.collect()


PUBLIC_TOPICS = _publicTopics()


@pytest.mark.realData
@pytest.mark.integration
@pytest.mark.parametrize("topic", PUBLIC_TOPICS)
def testPanelPublicTopicReturnsData(samsungRealData, topic):
    """공개 목록에 있는 topic은 실제 읽을 수 있는 본문을 반환해야 한다."""
    assert topic != MISSING_DATA, "samsungRealData의 데이터 부재 가드가 실행되지 않았습니다"
    result = samsungRealData.panel(topic)
    assert isinstance(result, pl.DataFrame), f"panel({topic!r}) 본문 없음: {type(result).__name__}"
    assert not result.is_empty(), f"panel({topic!r}) 빈 본문"


@pytest.mark.realData
@pytest.mark.integration
@pytest.mark.parametrize("topic", PUBLIC_TOPICS)
def testTracePublicTopicHasSource(samsungRealData, topic):
    """본문이 광고된 topic은 fixture 환경에서도 실제 출처를 제시해야 한다."""
    assert topic != MISSING_DATA, "samsungRealData의 데이터 부재 가드가 실행되지 않았습니다"
    result = samsungRealData.trace(topic)
    assert isinstance(result, dict), f"trace({topic!r}) 출처 없음"
    assert result.get("primarySource"), f"trace({topic!r}) primarySource 없음"
    assert result.get("availableSources"), f"trace({topic!r}) availableSources 없음"
