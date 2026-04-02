"""review 통합 테스트 — MockCompany로 buildBlocks 전체 코드 경로 검증.

builders.py(3,559줄)의 모든 빌더 함수를 합성 데이터로 통과시킨다.
"""

from __future__ import annotations

import pytest

from dartlab.review.blockMap import BlockMap

pytestmark = pytest.mark.unit


# ── buildBlocks 전체 ──


def test_buildBlocks_all(mock_company):
    """전체 블록 빌드 — crash 없음, 비어있지 않음."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    blocks = buildBlocks(mock_company)
    assert isinstance(blocks, (dict, BlockMap))
    assert len(blocks) > 0


def test_buildBlocks_returns_lists(mock_company):
    """각 블록 값은 list여야 한다 (Block 리스트 또는 빈 리스트)."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    blocks = buildBlocks(mock_company)
    for key in blocks:
        value = blocks[key]
        assert isinstance(value, list), f"Block '{key}' is {type(value)}, expected list"


# ── 선택적 빌드 ──


def test_buildBlocks_selective_keys(mock_company):
    """특정 키만 빌드 — 요청 키만 반환."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    keys = {"profile", "growth", "marginTrend"}
    blocks = buildBlocks(mock_company, keys=keys)
    assert isinstance(blocks, (dict, BlockMap))
    # 반환된 키는 요청 키의 부분집합이어야 한다
    for key in blocks:
        assert key in keys, f"Unexpected key '{key}' not in requested keys"


def test_buildBlocks_single_section_keys(mock_company):
    """수익구조 관련 키만 빌드."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    keys = {"profile", "segmentComposition", "segmentTrend", "growth", "concentration", "revenueQuality"}
    blocks = buildBlocks(mock_company, keys=keys)
    assert isinstance(blocks, (dict, BlockMap))


def test_buildBlocks_capital_keys(mock_company):
    """자금조달 관련 키만 빌드."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    keys = {"fundingSources", "capitalOverview", "capitalTimeline", "debtTimeline", "interestBurden", "liquidity"}
    blocks = buildBlocks(mock_company, keys=keys)
    assert isinstance(blocks, (dict, BlockMap))


# ── 빈 데이터 안전성 ──


def test_buildBlocks_empty_company(empty_mock_company):
    """빈 회사 데이터로도 crash 없음."""
    from dartlab.review.registry import buildBlocks

    empty_mock_company._cache.clear()
    blocks = buildBlocks(empty_mock_company)
    assert isinstance(blocks, (dict, BlockMap))
    # 빈 데이터면 대부분 빈 리스트여야 한다
    for key, value in blocks.items():
        assert isinstance(value, list), f"Block '{key}' is {type(value)} with empty data"


# ── currency 분기 ──


def test_buildBlocks_usd_currency(mock_company):
    """USD currency로도 crash 없음."""
    mock_company.currency = "USD"
    mock_company._cache.clear()
    from dartlab.review.registry import buildBlocks

    blocks = buildBlocks(mock_company)
    assert isinstance(blocks, (dict, BlockMap))
    # 원복
    mock_company.currency = "KRW"


# ── basePeriod 전달 ──


def test_buildBlocks_with_basePeriod(mock_company):
    """basePeriod 전달 — crash 없음."""
    from dartlab.review.registry import buildBlocks

    mock_company._cache.clear()
    blocks = buildBlocks(mock_company, basePeriod="2023")
    assert isinstance(blocks, (dict, BlockMap))


# ── 블록 타입 검증 ──


def test_block_items_are_valid_types(mock_company):
    """생성된 블록 내 아이템이 올바른 Block 타입인지 검증."""
    from dartlab.review.blocks import (
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )
    from dartlab.review.registry import buildBlocks

    valid_types = (HeadingBlock, TextBlock, TableBlock, FlagBlock, MetricBlock)

    mock_company._cache.clear()
    blocks = buildBlocks(mock_company)
    for key, block_list in blocks.items():
        for item in block_list:
            assert isinstance(item, valid_types), (
                f"Block '{key}' contains {type(item).__name__}, expected one of {[t.__name__ for t in valid_types]}"
            )
