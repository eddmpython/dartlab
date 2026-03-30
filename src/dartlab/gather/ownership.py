"""지분 보유 facade -- KR(Naver flow)."""

from __future__ import annotations

import logging

from .http import GatherHttpClient
from .types import InstitutionOwnership, SourceUnavailableError

log = logging.getLogger(__name__)


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    client: GatherHttpClient,
) -> list[InstitutionOwnership]:
    """기관/외국인 지분 보유 조회 -- KR만 지원."""
    if market != "KR":
        return []
    try:
        url = f"https://m.stock.naver.com/api/stock/{stockCode}/integration"
        resp = await client.get(url)
        data = resp.json()
        dealTrends = data.get("dealTrendInfos", [])
        if not dealTrends:
            return []
        latest = dealTrends[0]
        foreignRatio = _cleanFloat(latest.get("foreignerHoldRatio", "0").replace("%", ""))
        result = []
        if foreignRatio > 0:
            result.append(
                InstitutionOwnership(
                    holderName="외국인 합계",
                    ratio=foreignRatio,
                    source="naver",
                )
            )
        return result
    except (SourceUnavailableError, KeyError, ValueError, TypeError) as exc:
        log.debug("ownership KR 실패 (%s): %s", stockCode, exc)
        return []


def _cleanFloat(text) -> float:
    """숫자 텍스트 -> float."""
    if not text:
        return 0.0
    try:
        return float(str(text).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0
