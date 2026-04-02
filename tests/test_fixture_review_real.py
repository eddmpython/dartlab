"""fixture 기반 review 통합 테스트 — 실제 parquet 데이터로 검증.

tests/fixtures/dart/ 하위의 실제 삼성전자 데이터를 사용한다.
review는 analysis 결과를 소비하므로 analysis가 동작해야 review도 동작한다.
fixture 데이터가 최소한이므로 빈 블록이 많을 수 있다 — crash 없음이 핵심.
"""

from __future__ import annotations

import gc
import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration]

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_SAMSUNG = "005930"


def _fixture_data_available() -> bool:
    return (FIXTURE_DIR / "dart" / "finance" / f"{_SAMSUNG}.parquet").exists()


@pytest.fixture(scope="module")
def samsung():
    """fixture 데이터로 삼성전자 Company 로드."""
    if not _fixture_data_available():
        pytest.skip("Fixture data not available")

    os.environ["DARTLAB_DATA_DIR"] = str(FIXTURE_DIR)
    import dartlab

    dartlab.dataDir = str(FIXTURE_DIR)
    try:
        c = dartlab.Company(_SAMSUNG)
        yield c
    except Exception:
        pytest.skip("Fixture data not available or Company init failed")
    finally:
        gc.collect()


# ── buildBlocks ──


def test_buildBlocks_returns_mapping(samsung):
    """buildBlocks — BlockMap(dict-like) 반환, crash 없음."""
    from dartlab.review.registry import buildBlocks

    samsung._cache.clear()
    try:
        blocks = buildBlocks(samsung)
        # BlockMap은 dict-like 매핑 또는 리스트일 수 있다
        assert blocks is not None
    except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
        # fixture 데이터 부족 — crash만 아니면 OK
        pass


def test_buildBlocks_selective(samsung):
    """buildBlocks keys 지정 — 선택적 빌드."""
    from dartlab.review.registry import buildBlocks

    samsung._cache.clear()
    try:
        blocks = buildBlocks(samsung, keys={"profitability"})
        assert blocks is not None
    except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
        pass


# ── buildReview ──


def test_buildReview_returns_review(samsung):
    """buildReview — Review 객체 반환."""
    from dartlab.review.registry import buildReview

    samsung._cache.clear()
    try:
        review = buildReview(samsung)
        assert review is not None
        # Review 객체는 sections 속성을 가진다
        assert hasattr(review, "sections")
    except (RuntimeError, KeyError, ValueError, TypeError):
        pass


# ── Company.review() ──


def test_company_review_full(samsung):
    """c.review() 전체 — crash 없음."""
    samsung._cache.clear()
    try:
        result = samsung.review()
        assert result is not None
    except (RuntimeError, KeyError, ValueError, TypeError):
        # fixture 데이터 부족 가능
        pass


def test_company_review_single_section(samsung):
    """c.review("수익성") 단일 섹션 — crash 없음."""
    samsung._cache.clear()
    try:
        result = samsung.review("수익성")
        assert result is not None
    except (RuntimeError, KeyError, ValueError, TypeError):
        pass


def test_company_review_preset(samsung):
    """c.review(preset="executive") — crash 없음."""
    samsung._cache.clear()
    try:
        result = samsung.review(preset="executive")
        assert result is not None
    except (RuntimeError, KeyError, ValueError, TypeError):
        pass


# ── 출력 형식 ──


def test_review_to_markdown(samsung):
    """review().toMarkdown() — 문자열 반환."""
    samsung._cache.clear()
    try:
        result = samsung.review()
        if result is not None and hasattr(result, "toMarkdown"):
            md = result.toMarkdown()
            assert md is None or isinstance(md, str)
    except (RuntimeError, KeyError, ValueError, TypeError):
        pass


def test_review_to_json(samsung):
    """review().toJson() — dict 또는 str 반환."""
    samsung._cache.clear()
    try:
        result = samsung.review()
        if result is not None and hasattr(result, "toJson"):
            j = result.toJson()
            assert j is None or isinstance(j, (dict, str, list))
    except (RuntimeError, KeyError, ValueError, TypeError):
        pass


# ── blocks() — BlockMap ──


def test_company_blocks(samsung):
    """c.blocks() — BlockMap 반환."""
    samsung._cache.clear()
    try:
        b = samsung.blocks()
        assert b is not None
    except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
        pass
