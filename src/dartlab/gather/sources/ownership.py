"""지분 보유 facade -- KR(Naver flow)."""

from __future__ import annotations

from ..infra.http import GatherHttpClient
from ..types import InstitutionOwnership, SourceUnavailableError


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    client: GatherHttpClient,
    limit: int | None = None,
) -> list[InstitutionOwnership]:
    """기관/외국인 지분 보유 조회 -- KR만 지원.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: "005930").
    market : str
        시장 코드. "KR"만 지원.
    client : GatherHttpClient
        HTTP 클라이언트.
    limit : int | None
        반환 행수 상한. None이면 전체.

    Returns
    -------
    list[InstitutionOwnership]
        기관/외국인 지분 리스트. 각 InstitutionOwnership 필드:

        - holderName : str — 보유 주체명 (예: "외국인 합계")
        - ratio : float — 보유비율 (%)
        - source : str — 데이터 출처 ("naver")

        정상 응답에 보유 정보가 없으면 빈 리스트 [].

    Requires:
        네트워크 (Naver 직접 호출).

    Raises
    ------
    ValueError
        KR 외 시장.
    SourceUnavailableError
        Naver 요청 또는 응답 해석 실패.

    Example
    -------
    >>> rows = await fetch("005930", market="KR", client=client, limit=5)
    """
    if market != "KR":
        raise ValueError(f"ownership은 KR 시장만 지원합니다: {market!r}")
    try:
        url = f"https://m.stock.naver.com/api/stock/{stockCode}/integration"
        resp = await client.get(url)
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError("Naver ownership 응답은 JSON object여야 합니다")
        dealTrends = data.get("dealTrendInfos", [])
        if not isinstance(dealTrends, list):
            raise TypeError("Naver dealTrendInfos는 list여야 합니다")
        if not dealTrends:
            return []
        latest = dealTrends[0]
        if not isinstance(latest, dict):
            raise TypeError("Naver dealTrendInfos 항목은 JSON object여야 합니다")
        foreignRatio = _cleanFloat(latest.get("foreignerHoldRatio", "0"))
        result = []
        if foreignRatio > 0:
            result.append(
                InstitutionOwnership(
                    holderName="외국인 합계",
                    ratio=foreignRatio,
                    source="naver",
                )
            )
        if limit is not None and limit > 0:
            return result[:limit]
        return result
    except SourceUnavailableError:
        raise
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise SourceUnavailableError(f"ownership 응답 해석 실패: {stockCode}") from exc


def iterFetch(
    stockCode: str,
    *,
    market: str = "KR",
    client: GatherHttpClient | None = None,
    batchSize: int = 100,
):
    """fetch 의 streaming pair — list 를 batchSize 단위 yield (A 트랙 I2).

    Capabilities: list[InstitutionOwnership] 를 batchSize slice yield.
    AIContext: 외국인/기관 보유 흐름의 chunk 처리.
    Guide: fetch 가 빈 list 면 yield 없음. client=None 이면 자동 생성.
    When: 다수 보유자 ownership 데이터 chunk 처리 시.
    How: runAsync(fetch) → list slice iterate.

    Args:
        stockCode: 종목코드.
        market: 시장. "KR"만 지원.
        client: HTTP 클라이언트. None 이면 GatherHttpClient 자동 생성.
        batchSize: batch 크기.

    Yields:
        list[InstitutionOwnership] — 각 batch.

    Raises:
        없음.

    Example::

        for batch in iterFetch("005930"): aggregate(batch)

    Requires: 네트워크.
    See Also: ``fetch``.
    """
    from ..infra.http import runAsync

    if client is None:
        client = GatherHttpClient()
    owners = runAsync(fetch(stockCode, market=market, client=client))
    if not owners:
        return
    for i in range(0, len(owners), batchSize):
        yield owners[i : i + batchSize]


def _cleanFloat(text) -> float:
    """숫자 텍스트를 float로 변환. 콤마·공백 제거.

    Parameters
    ----------
    text : str | None
        변환할 텍스트. None이나 빈 문자열 또는 ``"-"``이면 0.0 반환.

    Returns
    -------
    float
        변환된 숫자값.
    """
    if text is None:
        return 0.0
    cleaned = str(text).replace(",", "").replace("%", "").strip()
    if cleaned in {"", "-"}:
        return 0.0
    return float(cleaned)
