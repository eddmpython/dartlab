"""KRX 시장 데이터 수집 -- 업종 분류 + 시총 + 피어 목록.

KRX data.krx.co.kr은 봇 차단이 강력하므로,
KIND 상장목록(listing.py) + Naver 업종 API를 조합하여 수집한다.

소스:
- KIND (kind.krx.co.kr): 업종 분류, 시장구분 -- listing.py 재활용
- Naver (m.stock.naver.com): 업종코드, 업종별 종목 목록(시총 포함)
"""

from __future__ import annotations

import logging

from ..infra.http import GatherHttpClient
from ..types import SectorInfo, SourceUnavailableError

log = logging.getLogger(__name__)

_NAVER_INDUSTRY_LIST = "https://m.stock.naver.com/api/stocks/industry"
_NAVER_INDUSTRY_DETAIL = "https://m.stock.naver.com/api/stocks/industry/{code}"
_NAVER_INTEGRATION = "https://m.stock.naver.com/api/stock/{code}/integration"


async def fetchSectorInfo(
    stockCode: str,
    client: GatherHttpClient,
    *,
    limit: int | None = None,
) -> SectorInfo | None:
    """종목의 업종 분류 조회 -- KIND + Naver 조합.

    Capabilities: KIND industry + Naver sector PER 조합 → SectorInfo.
    AIContext: gather.sector KR backend — industry 분석의 진짜 진입점.
    Guide: KIND fetch + Naver enrich 2 단계. KIND 없으면 None.
    When: gather.sector KR 호출 시.
    How: KIND industryName → industryCode 변환 + Naver PER 부가.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: ``"005930"``).
    client : GatherHttpClient
        비동기 HTTP 클라이언트.
    limit : int | None
        단건 SectorInfo 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    SectorInfo | None
        sectorCode : str — 업종코드 (네이버)
        sectorName : str — 업종명 (KIND 우선)
        industryCode : str — 산업코드 (네이버)
        industryName : str — 산업명 (네이버)
        market : str — 시장구분 (코스피/코스닥)
        source : str — ``"kind+naver"``

    Raises
    ------
    SourceUnavailableError
        KIND 정보도 없고 Naver 요청도 실패한 경우.

    Example
    -------
    >>> info = await fetchSectorInfo("005930", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com``) + KIND 캐시 (``listing.getKindList``).
    Naver 차단 시 KIND 단독 fallback (sectorCode 빈 문자열).

    See Also
    --------
    mixins/info.sector : 본 함수의 caller.
    fetchIndustryPeers : industryCode 후속 peer 조회.
    listing.getKindList : KIND 업종명 source.
    """
    del limit
    # 1) KIND에서 업종명 가져오기 (동기 -- 이미 캐시됨)
    kindSector = _getKindSector(stockCode)

    # 2) Naver에서 업종코드 가져오기
    naverIndustryCode = None
    naverIndustryName = None
    market = ""
    naverError: Exception | None = None
    naverAvailable = False
    try:
        url = _NAVER_INTEGRATION.format(code=stockCode)
        resp = await client.get(url)
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError("Naver integration 응답은 JSON object여야 합니다")
        naverAvailable = True
        naverIndustryCode = str(data.get("industryCode", ""))
        exchange = data.get("stockExchangeType", {})
        if isinstance(exchange, dict):
            market = exchange.get("nameKor", "")
        elif isinstance(data.get("sosok"), str):
            market = "코스피" if data["sosok"] == "0" else "코스닥"
    except (SourceUnavailableError, OSError, KeyError, ValueError, TypeError) as exc:
        naverError = exc

    # 3) 업종코드로 업종명 확인
    if naverIndustryCode:
        naverIndustryName = await _getIndustryName(naverIndustryCode, client)

    sectorName = kindSector or naverIndustryName or ""
    resolvedMarket = market or _getKindMarket(stockCode)
    if not any((sectorName, naverIndustryCode, resolvedMarket)):
        if naverError is not None:
            raise SourceUnavailableError(f"sector 공급자를 사용할 수 없습니다: {stockCode}") from naverError
        return None
    source = "kind+naver" if kindSector and naverAvailable else "kind" if kindSector else "naver"
    return SectorInfo(
        sectorCode=naverIndustryCode or "",
        sectorName=sectorName,
        industryCode=naverIndustryCode or "",
        industryName=naverIndustryName or "",
        market=resolvedMarket,
        source=source,
    )


async def fetchIndustryPeers(
    industryCode: str,
    client: GatherHttpClient,
    *,
    limit: int | None = None,
) -> list[dict]:
    """업종 내 종목 목록 (시총 포함) -- Naver 업종 API.

    Capabilities: industryCode 의 peer 종목 + 시총 list[dict].
    AIContext: industryPeers mixin backend — peer valuation 비교 진입.
    Guide: industryCode 정확 필요 (fetchSectorInfo 가 먼저).
    When: 동종업종 peer ranking 분석 시.
    How: finance.naver.com/sise/sise_group_detail → list[dict].

    Parameters
    ----------
    industryCode : str
        네이버 업종코드 (예: ``"263"``).
    client : GatherHttpClient
        비동기 HTTP 클라이언트.
    limit : int | None
        반환 행수 상한 (가장 위 N). None이면 전체.

    Returns
    -------
    list[dict]
        업종 내 종목 목록. 각 dict 키:

        - stockCode : str — 종목코드
        - stockName : str — 종목명
        - closePrice : int — 현재가 (원)
        - marketCap : int — 시가총액 (원)
        - fluctuationsRatio : float — 등락률 (%)
        - market : str — ``"KOSPI"`` | ``"KOSDAQ"``

        정상 응답에 종목이 없으면 빈 리스트.

    Raises
    ------
    SourceUnavailableError
        Naver 요청 또는 응답 해석 실패.

    Example
    -------
    >>> peers = await fetchIndustryPeers("263", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com/api/stocks/industry/{code}``) + industryCode
    정확 명시 (``fetchSectorInfo`` 결과의 ``industryCode``).

    See Also
    --------
    mixins/info.industryPeers : 본 함수의 caller.
    fetchSectorInfo : industryCode 추출 source.
    fetchIndustryList : 전체 universe.
    """
    try:
        url = _NAVER_INDUSTRY_DETAIL.format(code=industryCode)
        resp = await client.get(url)
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError("Naver industry 응답은 JSON object여야 합니다")
        stocks = data.get("stocks", [])
        if not isinstance(stocks, list):
            raise TypeError("Naver industry stocks는 list여야 합니다")
        result = []
        for s in stocks:
            code = s.get("itemCode", "")
            if not code:
                continue
            result.append(
                {
                    "stockCode": code,
                    "stockName": s.get("stockName", ""),
                    "closePrice": _cleanNumber(s.get("closePrice", "")),
                    "marketCap": _cleanNumber(s.get("marketValue", "")),
                    "fluctuationsRatio": _cleanFloat(s.get("fluctuationsRatio", "")),
                    "market": "KOSPI" if s.get("sosok") == "0" else "KOSDAQ",
                }
            )
        if limit is not None and limit > 0:
            return result[:limit]
        return result
    except SourceUnavailableError:
        raise
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise SourceUnavailableError(f"industry peers 응답 해석 실패: {industryCode}") from exc


async def fetchIndustryList(
    client: GatherHttpClient,
    *,
    limit: int | None = None,
) -> list[dict]:
    """전체 업종 목록 조회 -- Naver.

    Capabilities: KR 전체 업종 코드/이름/평균지표 list[dict].
    AIContext: industry 분석 / sector rotation 의 universe 진입.
    Guide: 호출 비용 큼 — caller 측 caching 권장.
    When: 전체 업종 ranking / sector PER 분포 분석 시.
    How: finance.naver.com/sise/sise_group → list[dict].

    Parameters
    ----------
    client : GatherHttpClient
        비동기 HTTP 클라이언트.
    limit : int | None
        반환 행수 상한. None이면 전체.

    Returns
    -------
    list[dict]
        업종 목록. 각 dict 키:

        - industryCode : str — 업종코드
        - industryName : str — 업종명
        - totalCount : int — 소속 종목 수 (개)
        - changeRate : float — 업종 등락률 (%)

        정상 응답에 업종이 없으면 빈 리스트.

    Raises
    ------
    SourceUnavailableError
        Naver 요청 또는 응답 해석 실패.

    Example
    -------
    >>> inds = await fetchIndustryList(client)

    Requires
    --------
    네트워크 (``m.stock.naver.com/api/stocks/industry``). 호출 비용 큼 — caller 측
    caching 권장 (``_industryNameCache``).

    See Also
    --------
    fetchIndustryPeers : 본 list 의 industryCode 로 peer 조회.
    fetchSectorInfo : 단일 종목의 sectorCode 진입.
    """
    try:
        resp = await client.get(_NAVER_INDUSTRY_LIST)
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError("Naver industry list 응답은 JSON object여야 합니다")
        groups = data.get("groups", [])
        if not isinstance(groups, list):
            raise TypeError("Naver industry groups는 list여야 합니다")
        rows = [
            {
                "industryCode": str(g.get("no", "")),
                "industryName": g.get("name", ""),
                "totalCount": g.get("totalCount", 0),
                "changeRate": _cleanFloat(g.get("changeRate", "")),
            }
            for g in groups
            if g.get("no") and g.get("name")
        ]
        if limit is not None and limit > 0:
            return rows[:limit]
        return rows
    except SourceUnavailableError:
        raise
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise SourceUnavailableError("industry list 응답 해석 실패") from exc


# ── 내부 헬퍼 ──


def _getKindSector(stockCode: str) -> str:
    """KIND 상장목록에서 업종명을 조회.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: ``"005930"``).

    Returns
    -------
    str
        업종명 (예: ``"전기전자"``). 조회 실패 또는 미등록 시 빈 문자열.
    """
    try:
        import polars as pl

        from dartlab.gather.krx.listing import getKindList

        df = getKindList()
        match = df.filter(pl.col("종목코드") == stockCode)
        if match.height > 0 and "업종" in match.columns:
            return match["업종"][0]
    except (ImportError, FileNotFoundError, ValueError):
        pass
    return ""


def _getKindMarket(stockCode: str) -> str:
    """KIND 상장목록에서 시장구분을 조회.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: ``"005930"``).

    Returns
    -------
    str
        시장명 (``"코스피"`` | ``"코스닥"`` | 원본값). 조회 실패 시 빈 문자열.
    """
    try:
        import polars as pl

        from dartlab.gather.krx.listing import getKindList

        df = getKindList()
        match = df.filter(pl.col("종목코드") == stockCode)
        if match.height > 0 and "시장구분" in match.columns:
            raw = match["시장구분"][0]
            if "유가" in raw:
                return "코스피"
            if "코스닥" in raw:
                return "코스닥"
            return raw
    except (ImportError, FileNotFoundError, ValueError):
        pass
    return ""


_industryNameCache: dict[str, str] = {}


async def _getIndustryName(industryCode: str, client: GatherHttpClient) -> str:
    """업종코드로 업종명을 조회 (모듈 캐시 사용).

    Parameters
    ----------
    industryCode : str
        네이버 업종코드 (예: ``"263"``).
    client : GatherHttpClient
        비동기 HTTP 클라이언트.

    Returns
    -------
    str
        업종명 (예: ``"반도체"``). 매핑 실패 시 빈 문자열.
    """
    if industryCode in _industryNameCache:
        return _industryNameCache[industryCode]
    industries = await fetchIndustryList(client)
    for ind in industries:
        _industryNameCache[ind["industryCode"]] = ind["industryName"]
    return _industryNameCache.get(industryCode, "")


def _cleanNumber(text) -> int:
    """콤마/+기호가 포함된 숫자 텍스트를 int로 변환.

    Parameters
    ----------
    text
        변환할 값. 콤마, +기호는 자동 제거.

    Returns
    -------
        int
        변환된 정수. 빈 값이면 0.
    """
    if not text:
        return 0
    cleaned = str(text).replace(",", "").replace("+", "").strip()
    return int(cleaned)


def _cleanFloat(text) -> float:
    """콤마/+기호가 포함된 숫자 텍스트를 float로 변환.

    Parameters
    ----------
    text
        변환할 값. 콤마, +기호는 자동 제거.

    Returns
    -------
        float
        변환된 실수. 빈 값이면 0.0.
    """
    if not text:
        return 0.0
    cleaned = str(text).replace(",", "").replace("+", "").strip()
    return float(cleaned)
