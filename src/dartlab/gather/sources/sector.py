"""업종 분류 facade -- KR(KIND+Naver)."""

from __future__ import annotations

from ..infra.http import GatherHttpClient
from ..types import SectorInfo


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    client: GatherHttpClient,
    limit: int | None = None,
) -> SectorInfo | None:
    """업종 분류 조회 -- KR만 지원.

    Capabilities:
        - KRX KIND + Naver sector 매핑
        - 단일 SectorInfo (sector + industry 1:1)
        - circuit breaker 자동 적용

    AIContext:
        - mixin.sector 의 backend — industry 분석의 진짜 진입점

    Guide:
        KR 외 시장은 ValueError. KR만 작동.

    When:
        gather.sector() 호출 시.

    How:
        stockCode → KIND lookup + Naver enrich → SectorInfo.

    Requires:
        네트워크 (KIND/Naver).

    Parameters
    ----------
    stockCode : str
        종목코드 (예: "005930").
    market : str
        시장 코드. "KR"만 지원.
    client : GatherHttpClient
        HTTP 클라이언트.
    limit : int | None
        단건 SectorInfo 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    SectorInfo | None
        업종 분류 정보. SectorInfo 필드:

        - sectorCode : str — 업종 코드
        - sectorName : str — 업종명
        - industryCode : str — 산업 코드
        - industryName : str — 산업명
        - market : str — 시장 구분 (KOSPI/KOSDAQ)
        - source : str — 데이터 출처

        정상 응답에 분류 정보가 없으면 None.

    Raises
    ------
    ValueError
        KR 외 시장.
    SourceUnavailableError
        KIND/Naver 공급자 장애.

    Example
    -------
    >>> info = await fetch("005930", market="KR", client=client)

    See Also:
        ``dartlab.gather.krx.listing.getKindList``.
    """
    del limit
    if market != "KR":
        raise ValueError(f"sector는 KR 시장만 지원합니다: {market!r}")
    # domains 는 gather 바로 아래다 (`..domains`). 이 줄만 점이 하나라 없는 경로
    # `gather.sources.domains` 를 가리켰고, ModuleNotFoundError 가 아래 ImportError 로
    # 잡혀 warning 한 줄만 남기고 None 이 됐다. 업종 축이 어느 회사에서도 비었고,
    # 업종코드로 피어를 찾는 축까지 같이 죽었다.
    from ..domains.krx import fetchSectorInfo

    return await fetchSectorInfo(stockCode, client)
