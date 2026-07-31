"""scanAccount 계정 이름 해소와 ticker universe 정규화 회귀."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.providers.edgar.finance.scanAccount.taxonomy import (
    _buildEdgarTagKeys,
    _canonicalSnakeId,
    _joinCorpName,
)
from dartlab.providers.edgar.finance.scanAccount.types import EdgarScanMappingError

pytestmark = pytest.mark.unit


def testCanonicalSnakeIdIsIdempotent() -> None:
    """이미 canonical 인 이름은 그대로 둔다."""
    assert _canonicalSnakeId("sales") == "sales"
    assert _canonicalSnakeId(_canonicalSnakeId("sales")) == "sales"


def testCanonicalSnakeIdTerminatesOnAliasCycle() -> None:
    """alias 가 순환해도 무한 루프에 빠지지 않는다."""
    assert isinstance(_canonicalSnakeId("ifrs-full_Revenue"), str)


def testTagKeysCoverBothTaxonomies() -> None:
    """매출은 us-gaap 과 ifrs-full concept 을 모두 갖는다."""
    keys = _buildEdgarTagKeys("sales")

    assert len(keys.usGaap) > 1
    assert len(keys.ifrsFull) > 0
    assert keys.usGaapCommon <= set(keys.usGaap)


def testTagKeysAreLowercasedForMatching() -> None:
    """tag 매칭은 소문자 비교라 key 도 소문자여야 한다."""
    keys = _buildEdgarTagKeys("sales")

    assert all(k == k.lower() for k in keys.usGaap)


def testJoinCorpNameRejectsFrameWithoutStockCode() -> None:
    """stockCode 없는 프레임은 조용히 통과시키지 않는다."""
    with pytest.raises(EdgarScanMappingError):
        _joinCorpName(pl.DataFrame({"period": ["2024"]}), {"AAA": "Alpha Inc"})


def testJoinCorpNameAttachesTitle() -> None:
    """정상 경로는 ticker 에 회사명을 붙이고 기간 열을 보존한다."""
    frame = pl.DataFrame({"stockCode": ["AAA"], "2024": [1.0]})

    out = _joinCorpName(frame, {"AAA": "Alpha Inc"})

    assert out["corpName"].to_list() == ["Alpha Inc"]
    assert out.columns[:2] == ["stockCode", "corpName"]
