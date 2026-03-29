"""업종 분류 facade -- KR(KIND+Naver)."""

from __future__ import annotations

import logging

from .http import GatherHttpClient
from .types import SectorInfo, SourceUnavailableError

log = logging.getLogger(__name__)


async def fetch(stockCode: str, *, market: str = "KR", client: GatherHttpClient) -> SectorInfo | None:
    """업종 분류 조회 -- KR만 지원."""
    if market != "KR":
        return None
    try:
        from .domains.krx import fetchSectorInfo

        return await fetchSectorInfo(stockCode, client)
    except (SourceUnavailableError, ImportError, OSError) as exc:
        log.warning("sector KR 실패 (%s): %s", stockCode, exc)
        return None
