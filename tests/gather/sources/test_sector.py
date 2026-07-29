"""dartlab.gather.sources.sector의 시장·오류 전달 계약."""

from __future__ import annotations

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.sector`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.sector")


def test_sector_non_kr_raises() -> None:
    """market != "KR"이면 지원 범위를 명시한다."""
    from dartlab.gather.sources import sector as sectorMod

    with pytest.raises(ValueError, match="KR 시장만"):
        asyncio.run(sectorMod.fetch("AAPL", market="US", client=object()))


def test_sector_provider_failure_propagates() -> None:
    """공급자 장애를 미분류 종목으로 바꾸지 않는다."""
    from dartlab.gather.sources import sector as sectorMod
    from dartlab.gather.types import SourceUnavailableError

    backend = AsyncMock(side_effect=SourceUnavailableError("krx down"))
    with patch("dartlab.gather.domains.krx.fetchSectorInfo", new=backend):
        with pytest.raises(SourceUnavailableError, match="krx down"):
            asyncio.run(sectorMod.fetch("005930", market="KR", client=object()))
