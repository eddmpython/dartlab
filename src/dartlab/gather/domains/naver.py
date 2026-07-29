"""네이버 금융 데이터 수집 — 주가 + 수급 + 업종PER.

네이버 금융 API에서 한국 시장 데이터를 수집한다.
robots.txt 준수, 도메인당 30RPM 이하.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from dartlab.core.market import isKrStockCode

from ..types import (
    FlowData,
    GatherResult,
    PriceSnapshot,
    RevenueConsensus,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)

# NaverPay 증권 API (JSON)
_API_BASE = "https://m.stock.naver.com/api/stock"
# NaverPay 증권 front-api — 투자자별 매매동향 페이지네이션.
_FLOW_TREND_URL = "https://m.stock.naver.com/front-api/stock/domestic/trend"
_FLOW_DEFAULT_LATEST_LIMIT = 5
_FLOW_MAX_SERVER_PAGE_SIZE = 50
# 네이버 차트 API (XML) — FDR 방식, 한번에 6000일
_CHART_URL = "https://fchart.stock.naver.com/sise.nhn"
# 네이버 분봉 API (JSON). 당일 + startDateTime/endDateTime 로 과거 세션도 조회.
_INTRADAY_URL = "https://api.stock.naver.com/chart/domestic/item/{code}/minute"
# 분봉 타임스탬프는 YYYYMMDDHHMM 12 자리만 인식 (8 자리 날짜만은 빈 응답).
_INTRADAY_OPEN_HHMM = "0900"
_INTRADAY_CLOSE_HHMM = "1530"
# 최근 거래일 폴백. 오늘이 휴장/장전이라 빈 응답이면 며칠 뒤로 걸어가 최근 세션을 찾는다.
_INTRADAY_FALLBACK_DAYS = 8
_KST = timezone(timedelta(hours=9))


def _cleanNumber(text: str | None) -> float | None:
    """숫자 텍스트 파싱 — 콤마, 공백, +/- 처리.

    Parameters
    ----------
    text : str | None
        파싱할 숫자 문자열. "N/A", "-", 빈 문자열은 None 처리.

    Returns
    -------
    float | None
        파싱된 숫자값. 변환 불가 시 None.
    """
    if not text:
        return None
    cleaned = str(text).strip().replace(",", "").replace("+", "").replace(" ", "")
    if not cleaned or cleaned in ("N/A", "-"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalizeDateToken(value: str | date | None) -> str | None:
    """날짜 입력을 Naver flow cursor용 ``YYYYMMDD`` 문자열로 정규화."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    token = str(value).strip().replace("-", "")
    if len(token) != 8 or not token.isdigit():
        raise ValueError(f"날짜 포맷 오류: {value!r} (YYYYMMDD 또는 YYYY-MM-DD)")
    return token


def _nextDateToken(token: str | None) -> str | None:
    """Naver flow cursor는 해당 날짜 이전을 반환하므로 end+1일을 사용한다."""
    if token is None:
        return None
    d = datetime.strptime(token, "%Y%m%d").date()
    return (d + timedelta(days=1)).strftime("%Y%m%d")


def _parseFlowNumber(value, field: str) -> float | None:
    """Naver flow 숫자를 파싱하고 손상된 값은 source 오류로 구분한다."""
    token = str(value).strip().replace("%", "") if value is not None else ""
    if token in ("", "N/A", "-"):
        return None
    parsed = _cleanNumber(token)
    if parsed is None:
        raise SourceUnavailableError(f"Naver flow {field} 값을 해석할 수 없습니다: {value!r}")
    return parsed


def _parseFlowTrendRows(items: list[dict]) -> list[dict]:
    """Naver flow raw row → dartlab 표준 flow row."""
    result = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Naver flow result 행이 객체가 아닙니다")
        bizdate = str(item.get("bizdate") or "")
        if len(bizdate) != 8 or not bizdate.isdigit():
            raise ValueError(f"Naver flow bizdate가 올바르지 않습니다: {bizdate!r}")

        fn = _parseFlowNumber(item.get("foreignerPureBuyQuant"), "foreignerPureBuyQuant")
        on = _parseFlowNumber(item.get("organPureBuyQuant"), "organPureBuyQuant")
        ind = _parseFlowNumber(item.get("individualPureBuyQuant"), "individualPureBuyQuant")
        ratio = _parseFlowNumber(item.get("foreignerHoldRatio"), "foreignerHoldRatio")
        result.append(
            {
                "date": bizdate,
                "foreignNet": fn or 0.0,
                "institutionNet": on or 0.0,
                "individualNet": ind or 0.0,
                "foreignHoldingRatio": ratio or 0.0,
            }
        )
    return result


async def _fetchFlowTrend(
    stockCode: str,
    client,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
    limit: int | None = None,
    pageSize: int | None = None,
    sleepSec: float = 0.0,
    marketType: str = "KRX",
    maxPages: int | None = None,
    full: bool = False,
    proxy: str | None = None,
) -> list[dict] | None:
    """Naver front-api 투자자별 매매동향 페이지네이션."""
    startToken = _normalizeDateToken(start)
    endToken = _normalizeDateToken(end)
    cursor = _nextDateToken(endToken)
    effectiveLimit = limit
    parsedPageSize = int(pageSize) if pageSize is not None else 0
    explicitPageSize = parsedPageSize if parsedPageSize > 0 else None

    if startToken is None and endToken is None and effectiveLimit is None and not full:
        effectiveLimit = explicitPageSize or _FLOW_DEFAULT_LATEST_LIMIT
    serverPageSize = _FLOW_MAX_SERVER_PAGE_SIZE
    if explicitPageSize is not None and explicitPageSize > 0:
        serverPageSize = min(explicitPageSize, _FLOW_MAX_SERVER_PAGE_SIZE)
    if effectiveLimit is not None and effectiveLimit > 0:
        serverPageSize = min(serverPageSize, max(1, int(effectiveLimit)), _FLOW_MAX_SERVER_PAGE_SIZE)

    result: list[dict] = []
    reachedStart = False
    pages = 0
    while True:
        params: dict[str, str | int] = {
            "code": stockCode,
            "marketType": marketType,
            "pageSize": serverPageSize,
        }
        if cursor:
            params["bizdate"] = cursor

        resp = await client.get(
            _FLOW_TREND_URL,
            params=params,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": f"https://m.stock.naver.com/domestic/stock/{stockCode}/total",
            },
            proxy=proxy,
        )
        try:
            data = resp.json()
        except ValueError as exc:
            raise SourceUnavailableError("Naver flow trend JSON을 해석할 수 없습니다") from exc

        if isinstance(data, dict):
            if data.get("isSuccess") is False:
                raise SourceUnavailableError("Naver flow trend API가 실패 응답을 반환했습니다")
            if "result" not in data:
                raise SourceUnavailableError("Naver flow trend 응답에 result가 없습니다")
            rows = data["result"]
        elif isinstance(data, list):
            rows = data
        else:
            raise SourceUnavailableError("Naver flow trend 응답 schema가 올바르지 않습니다")

        if not isinstance(rows, list):
            raise SourceUnavailableError("Naver flow trend result가 배열이 아닙니다")
        if not rows:
            break

        pages += 1
        try:
            parsedRows = _parseFlowTrendRows(rows)
        except (TypeError, ValueError) as exc:
            raise SourceUnavailableError("Naver flow trend 행을 해석할 수 없습니다") from exc
        for row in parsedRows:
            rowDate = row.get("date") or ""
            if endToken is not None and rowDate > endToken:
                continue
            if startToken is not None and rowDate < startToken:
                reachedStart = True
                continue
            result.append(row)
            if effectiveLimit is not None and effectiveLimit > 0 and len(result) >= effectiveLimit:
                return result

        if reachedStart:
            break
        if len(rows) < serverPageSize:
            break
        if maxPages is not None and pages >= maxPages:
            break

        cursor = str(rows[-1].get("bizdate") or "")
        if not cursor:
            break
        if sleepSec > 0:
            await asyncio.sleep(sleepSec)

    return result or None


# ══════════════════════════════════════
# 개별 데이터 수집 함수
# ══════════════════════════════════════


def _parseInfos(infos: list[dict]) -> dict[str, str]:
    """totalInfos 배열을 {code: value} dict로 변환.

    Parameters
    ----------
    infos : list[dict]
        네이버 integration API의 totalInfos 배열.
        각 항목은 ``{"code": "per", "value": "12.5배"}`` 형태.

    Returns
    -------
    dict[str, str]
        code를 키, value를 값으로 하는 매핑.
        예: ``{"per": "12.5배", "pbr": "1.2배", "marketValue": "100조"}``.
    """
    if not isinstance(infos, list):
        raise SourceUnavailableError("Naver price totalInfos가 배열이 아닙니다")
    parsed: dict[str, str] = {}
    for item in infos:
        if not isinstance(item, dict):
            raise SourceUnavailableError("Naver price totalInfos 행이 객체가 아닙니다")
        code = item.get("code", "")
        if code:
            parsed[str(code)] = str(item.get("value") or "")
    return parsed


def _parseMarketCap(text: str) -> float:
    """한글 단위 시가총액 텍스트를 숫자로 변환.

    Parameters
    ----------
    text : str
        네이버 시총 텍스트. 예: ``"1,063조 7,589억"``.

    Returns
    -------
    float
        원 단위 시가총액 (원). 빈 문자열이면 0.0.
    """
    if not text:
        return 0.0
    total = 0.0
    text = text.replace(",", "")
    if "조" not in text and "억" not in text:
        parsed = _cleanNumber(text)
        if parsed is None:
            raise SourceUnavailableError(f"Naver price marketValue를 해석할 수 없습니다: {text!r}")
        return parsed
    if "조" in text:
        parts = text.split("조")
        trillions = _cleanNumber(parts[0])
        if trillions is None:
            raise SourceUnavailableError(f"Naver price marketValue를 해석할 수 없습니다: {text!r}")
        total += trillions * 1_0000_0000_0000
        text = parts[1] if len(parts) > 1 else ""
    if "억" in text:
        parts = text.split("억")
        hundredMillions = _cleanNumber(parts[0])
        if hundredMillions is None:
            raise SourceUnavailableError(f"Naver price marketValue를 해석할 수 없습니다: {text!r}")
        total += hundredMillions * 1_0000_0000
    return total


def _parsePriceNumber(value: object, field: str, *suffixes: str) -> float | None:
    """Naver price 숫자 필드의 정상 결측과 손상된 값을 구분한다."""
    token = str(value).strip() if value is not None else ""
    for suffix in suffixes:
        token = token.replace(suffix, "")
    token = token.strip()
    if token in ("", "N/A", "-"):
        return None
    parsed = _cleanNumber(token)
    if parsed is None:
        raise SourceUnavailableError(f"Naver price {field} 값을 해석할 수 없습니다: {value!r}")
    return parsed


async def fetchPrice(
    stockCode: str,
    client,
    *,
    limit: int | None = None,
    **kwargs,
) -> PriceSnapshot | None:
    """네이버 -> 현재가 + PER/PBR + 52주 범위 + 시총 (KR 전용).

    Capabilities: KR Naver M-Stock API fetch + PriceSnapshot 변환.
    AIContext: gather.price KR primary source — 가장 풍부한 단건 스냅샷.
    Guide: KR 종목코드 (KRX 단축코드) 만. 외 티커는 ValueError.
    When: gather("price", stockCode, market="KR") 진입 시 첫 시도.
    How: m.stock.naver.com integration JSON → PriceSnapshot 매핑.

    KR 종목코드(KRX 단축코드)가 아니면 ValueError. naver KR API에 잘못된
    티커를 보내 409 에러가 나는 것을 차단.

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``, ``"0008Z0"``). KRX 단축코드만 처리.
    client
        비동기 HTTP 클라이언트.
    limit : int | None
        단건 PriceSnapshot 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    PriceSnapshot | None
        현재가 스냅샷. KR 종목코드 아니면 None. 주요 필드:

        - current : float — 현재가 (원)
        - change : float — 전일 대비 변동액 (원)
        - change_pct : float — 전일 대비 변동률 (%)
        - high_52w : float — 52주 최고가 (원)
        - low_52w : float — 52주 최저가 (원)
        - volume : int — 누적 거래량 (주)
        - market_cap : float — 시가총액 (원)
        - per : float | None — PER (배)
        - pbr : float | None — PBR (배)
        - dividend_yield : float | None — 배당수익률 (%)
        - source : str — ``"naver"``

        유효한 응답에 현재가가 없으면 None.

    Raises
    ------
    ValueError
        KR 종목코드가 아닌 입력.
    SourceUnavailableError
        Naver 요청, JSON, schema 또는 숫자 파싱 실패.

    Example
    -------
    >>> snap = await fetchPrice("005930", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com/api/stock``) + KR 6 자리 종목코드. 30 RPM 이하 권장.

    See Also
    --------
    sources/price.fetch : 호출 체인 (KR primary).
    naverGlobal.fetchPrice : 외 시장 동행 source.
    fetchAll : 본 함수를 포함한 일괄 fetch.
    """
    del limit
    # KR 종목코드 검증. KRX 단축코드 아니면 차단 (US/글로벌 티커 -> naver_global로)
    if not isKrStockCode(stockCode or ""):
        raise ValueError(f"Naver price는 KR 종목코드만 지원합니다: {stockCode!r}")

    # basic: 현재가, 등락
    url = f"{_API_BASE}/{stockCode}/basic"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver price basic 요청 실패: {stockCode}") from exc
    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver price basic 응답 schema가 객체가 아닙니다")

    current = _parsePriceNumber(data.get("closePrice"), "closePrice")
    if not current:
        return None

    # integration: 시총, PER, PBR, 52주 범위
    marketCap = 0.0
    per = None
    pbr = None
    high52w = 0.0
    low52w = 0.0
    volume = int(_parsePriceNumber(data.get("accumulatedTradingVolume"), "accumulatedTradingVolume") or 0)
    dividendYield = None

    try:
        intUrl = f"{_API_BASE}/{stockCode}/integration"
        intResp = await client.get(intUrl, headers={"Accept": "application/json"})
        intData = intResp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver price integration 요청 실패: {stockCode}") from exc
    if not isinstance(intData, dict):
        raise SourceUnavailableError("Naver price integration 응답 schema가 객체가 아닙니다")
    if "totalInfos" not in intData:
        raise SourceUnavailableError("Naver price integration 응답에 totalInfos가 없습니다")
    infos = _parseInfos(intData["totalInfos"])

    marketCap = _parseMarketCap(infos.get("marketValue", ""))
    per = _parsePriceNumber(infos.get("per", ""), "per", "배")
    pbr = _parsePriceNumber(infos.get("pbr", ""), "pbr", "배")
    high52w = _parsePriceNumber(infos.get("highPriceOf52Weeks", ""), "highPriceOf52Weeks", "원") or 0.0
    low52w = _parsePriceNumber(infos.get("lowPriceOf52Weeks", ""), "lowPriceOf52Weeks", "원") or 0.0
    infoVolume = _parsePriceNumber(
        infos.get("accumulatedTradingVolume", ""),
        "accumulatedTradingVolume",
        "백만",
    )
    if infoVolume is not None:
        volume = int(infoVolume)
    dividendYield = _parsePriceNumber(infos.get("dividendYieldRatio", ""), "dividendYieldRatio", "%")

    return PriceSnapshot(
        current=current,
        change=_parsePriceNumber(data.get("compareToPreviousClosePrice"), "compareToPreviousClosePrice") or 0.0,
        change_pct=_parsePriceNumber(data.get("fluctuationsRatio"), "fluctuationsRatio") or 0.0,
        high_52w=high52w,
        low_52w=low52w,
        volume=volume,
        marketCap=marketCap,
        per=per,
        pbr=pbr,
        dividend_yield=dividendYield,
        source="naver",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency="KRW",
        market="KR",
    )


async def fetchFlow(
    stockCode: str,
    client,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
    limit: int | None = None,
    pageSize: int | None = None,
    sleepSec: float = 0.0,
    marketType: str = "KRX",
    maxPages: int | None = None,
    full: bool = False,
    proxy: str | None = None,
) -> list[dict] | None:
    """네이버 → 외국인/기관 수급 시계열.

    Capabilities: KR Naver 일별 외국인/기관/개인 순매수 fetch + 표준 dict 변환.
    AIContext: gather.flow KR 의 backend — sources/flow.fetch 호출자.
    Guide: KR 종목만. 외 시장은 빈 list. 최근일 우선 (latest first).
    When: gather("flow", stockCode) 진입 시 fallback chain 첫 시도.
    How: m.stock.naver.com 일별 deal trend JSON → list[dict].

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.
    start, end : str | date | None
        조회 기간. 지정 시 Naver front-api 페이지네이션으로 과거 구간까지 조회.
    limit : int | None
        반환 행수 상한 (가장 최근 N건). None이면 기간 조건까지 조회.
    pageSize : int | None
        호환용 고급 옵션. None이면 최신 조회는 5건, 기간/limit 조회는 내부에서
        Naver 최대 단위(50건)로 자동 페이지네이션한다.
    sleepSec : float
        페이지 호출 사이 대기 시간.
    full : bool
        True면 가능한 전체 이력을 끝까지 자동 수집한다.
    proxy : str | None
        사용자 제공 HTTP(S) 프록시 URL.

    Returns
    -------
    list[dict] | None
        수급 시계열 (최신순). 각 dict 키:

        - date : str — 거래일 (YYYYMMDD 또는 빈 문자열)
        - foreignNet : float — 외국인 순매수 (주)
        - institutionNet : float — 기관 순매수 (주)
        - individualNet : float — 개인 순매수 (주)
        - foreignHoldingRatio : float — 외국인 보유 비율 (%)

        데이터 없으면 None.

    Raises
    ------
    없음
        Naver API 내부 예외 (SourceUnavailableError/ValueError) 는 흡수.

    Example
    -------
    >>> flow = await fetchFlow("005930", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com``) + KR 6 자리 종목코드.
    ``front-api/stock/domestic/trend`` 페이지네이션 우선, integration fallback.

    See Also
    --------
    sources/flow.fetch : 호출 체인 (KR primary).
    fetchAll : 본 함수의 FlowData 변환 caller.
    """
    # KR 종목코드 검증
    if not isKrStockCode(stockCode or ""):
        raise ValueError(f"Naver flow는 KR 종목코드만 지원합니다: {stockCode!r}")

    _normalizeDateToken(start)
    _normalizeDateToken(end)
    trendFailure: Exception | None = None
    try:
        trend = await _fetchFlowTrend(
            stockCode,
            client,
            start=start,
            end=end,
            limit=limit,
            pageSize=pageSize,
            sleepSec=sleepSec,
            marketType=marketType,
            maxPages=maxPages,
            full=full,
            proxy=proxy,
        )
        if trend:
            return trend
    except (SourceUnavailableError, ValueError, KeyError, TypeError) as exc:
        log.warning("naver flow trend API 실패 (%s): %s", stockCode, exc)
        trendFailure = exc

    url = f"{_API_BASE}/{stockCode}/integration"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"}, proxy=proxy)
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        raise SourceUnavailableError(f"Naver flow integration 요청 실패: {stockCode}") from exc

    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver flow integration 응답 schema가 객체가 아닙니다")

    # v2: dealTrendInfos 배열 전체 활용 (최신순)
    deal_trends = data.get("dealTrendInfos", [])
    if not isinstance(deal_trends, list):
        raise SourceUnavailableError("Naver flow dealTrendInfos가 배열이 아닙니다")
    if deal_trends:
        try:
            result = _parseFlowTrendRows(deal_trends)
        except (TypeError, ValueError) as exc:
            raise SourceUnavailableError("Naver flow integration 행을 해석할 수 없습니다") from exc
        if result:
            if limit is not None and limit > 0:
                return result[:limit]
            return result

    # v1 fallback: foreignSummary + dealTrendByInvestor (스냅샷 1건)
    foreign_net = 0.0
    institution_net = 0.0
    foreign_holding_ratio = 0.0

    foreign_info = data.get("foreignSummary")
    if foreign_info is not None and not isinstance(foreign_info, dict):
        raise SourceUnavailableError("Naver flow foreignSummary가 객체가 아닙니다")
    if foreign_info:
        ratio = _parseFlowNumber(foreign_info.get("foreignOwnershipRatio"), "foreignOwnershipRatio")
        if ratio is not None:
            foreign_holding_ratio = ratio

    investor_info = data.get("dealTrendByInvestor")
    if investor_info is not None and not isinstance(investor_info, list):
        raise SourceUnavailableError("Naver flow dealTrendByInvestor가 배열이 아닙니다")
    if investor_info:
        for item in investor_info:
            if not isinstance(item, dict):
                raise SourceUnavailableError("Naver flow 투자자 행이 객체가 아닙니다")
            investor_type = item.get("investorType", "")
            net_buy = _parseFlowNumber(item.get("accumulatedNetBuyVolume"), "accumulatedNetBuyVolume")
            if net_buy is None:
                continue
            if "외국인" in investor_type or investor_type == "FOREIGNER":
                foreign_net = net_buy
            elif "기관" in investor_type or investor_type == "INSTITUTION":
                institution_net = net_buy

    if foreign_net == 0.0 and institution_net == 0.0 and foreign_holding_ratio == 0.0:
        if trendFailure is not None:
            raise SourceUnavailableError(
                "Naver flow trend가 실패했고 integration에도 데이터가 없습니다"
            ) from trendFailure
        if not any(key in data for key in ("dealTrendInfos", "foreignSummary", "dealTrendByInvestor")):
            raise SourceUnavailableError("Naver flow integration 응답에 수급 필드가 없습니다")
        return None

    snapshot = [
        {
            "date": "",
            "foreignNet": foreign_net,
            "institutionNet": institution_net,
            "foreignHoldingRatio": foreign_holding_ratio,
        }
    ]
    if limit is not None and limit > 0:
        return snapshot[:limit]
    return snapshot


async def fetchRevenueConsensus(
    stockCode: str,
    client,
    *,
    limit: int | None = None,
) -> list[RevenueConsensus]:
    """네이버 → 연간 매출/영업이익/순이익 컨센서스.

    Capabilities: KR Naver finance/annual API → 연간 재무 컨센서스 list.
    AIContext: 분석 엔진 (analysis/credit) 의 forward 추정 라인 진입.
    Guide: isConsensus='Y' 기간만. 일반 history 와 분리.
    When: gather.revenueConsensus 류 호출 (사용 빈도 낮음) 시.
    How: finance/annual JSON → list[RevenueConsensus].

    finance/annual API에서 isConsensus='Y'인 기간의 재무 추정치를 추출한다.
    실적 확정 기간(isConsensus='N')도 함께 반환하여 시계열 비교 가능.

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.

    Returns
    -------
    list[RevenueConsensus]
        연간 컨센서스 목록. 각 항목 주요 필드:

        - fiscal_year : int — 사업연도
        - revenue_est : float — 매출액 추정치 (억원)
        - operating_profit_est : float | None — 영업이익 추정치 (억원)
        - net_income_est : float | None — 당기순이익 추정치 (억원)
        - eps_est : float | None — EPS 추정치 (원)
        - per_est : float | None — PER 추정치 (배)
        - source : str — ``"naver_consensus"`` 또는 ``"naver_actual"``

        정상적으로 컨센서스 데이터가 없으면 빈 리스트.

    Other Parameters
    ----------------
    limit : int | None
        반환 행수 상한. None이면 전체.

    Raises
    ------
    ValueError
        KR 종목코드 입력 계약 위반.
    SourceUnavailableError
        Naver 요청, JSON 또는 응답 schema 실패.

    Example
    -------
    >>> rows = await fetchRevenueConsensus("005930", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com/api/stock/{code}/finance/annual``) + KR 6 자리 종목코드.
    Naver financeInfo 미존재 시 빈 list.

    See Also
    --------
    analysis/forecast : 본 함수 결과의 caller (forward 추정 라인).
    """
    # KR 종목코드 검증
    if not isKrStockCode(stockCode or ""):
        raise ValueError(f"Naver revenue consensus는 KR 종목코드만 지원합니다: {stockCode!r}")

    url = f"{_API_BASE}/{stockCode}/finance/annual"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver revenue consensus 요청 실패: {stockCode}") from exc
    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver revenue consensus 응답 schema가 객체가 아닙니다")

    fi = data.get("financeInfo")
    if fi is None:
        return []
    if not isinstance(fi, dict):
        raise SourceUnavailableError("Naver revenue consensus financeInfo가 객체가 아닙니다")

    titles = fi.get("trTitleList")
    rows = fi.get("rowList")
    if titles is None and rows is None:
        return []
    if not isinstance(titles, list) or not isinstance(rows, list):
        raise SourceUnavailableError("Naver revenue consensus title/row schema가 배열이 아닙니다")
    if not titles or not rows:
        return []

    # 항목별 dict 구축
    row_map: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise SourceUnavailableError("Naver revenue consensus row가 객체가 아닙니다")
        title = row.get("title", "")
        cols = row.get("columns")
        if title and isinstance(cols, dict):
            row_map[str(title)] = cols

    results: list[RevenueConsensus] = []
    for t in titles:
        if not isinstance(t, dict):
            raise SourceUnavailableError("Naver revenue consensus title이 객체가 아닙니다")
        key = str(t.get("key") or "")
        is_consensus = t.get("isConsensus") == "Y"
        if not key or len(key) < 4:
            raise SourceUnavailableError(f"Naver revenue consensus period key가 올바르지 않습니다: {key!r}")

        try:
            fiscal_year = int(key[:4])
        except ValueError as exc:
            raise SourceUnavailableError(f"Naver revenue consensus fiscal year를 해석할 수 없습니다: {key!r}") from exc

        revenue = _cleanNumber(row_map.get("매출액", {}).get(key, {}).get("value"))
        op_profit = _cleanNumber(row_map.get("영업이익", {}).get(key, {}).get("value"))
        net_income = _cleanNumber(row_map.get("당기순이익", {}).get(key, {}).get("value"))
        eps = _cleanNumber(row_map.get("EPS", {}).get(key, {}).get("value"))
        per = _cleanNumber(row_map.get("PER", {}).get(key, {}).get("value"))

        if revenue is None:
            continue

        results.append(
            RevenueConsensus(
                fiscal_year=fiscal_year,
                revenue_est=revenue,
                operating_profit_est=op_profit,
                net_income_est=net_income,
                eps_est=eps,
                per_est=per,
                source="naver_consensus" if is_consensus else "naver_actual",
            )
        )

    if limit is not None and limit > 0:
        return results[:limit]
    return results


async def fetchSectorPer(
    stockCode: str,
    client,
    *,
    limit: int | None = None,
) -> float | None:
    """네이버 → 동종업종 PER.

    Capabilities: KR Naver finance/sector API → 동종업종 평균 PER 단건 float.
    AIContext: peer-relative valuation 분석 baseline — relativeValuation 진입.
    Guide: 단건 float 반환 — limit 무시.
    When: 종목의 동종업종 평균 PER 비교 시.
    How: finance/sector JSON parse → sector PER float.

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.
    limit : int | None
        단건 float 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    float | None
        동종업종 평균 PER (배). 정상적으로 업종 데이터가 없으면 None.

    Raises
    ------
    ValueError
        KR 종목코드 입력 계약 위반.
    SourceUnavailableError
        Naver 요청, JSON 또는 응답 schema 실패.

    Example
    -------
    >>> per = await fetchSectorPer("005930", client)

    Requires
    --------
    네트워크 (``m.stock.naver.com``) + KR 6 자리 종목코드. industryInfo 없으면 None.

    See Also
    --------
    fetchPrice : PER 자체 (peer-relative 비교 baseline 으로 본 함수 결과와 비교).
    fetchAll : 본 함수 호출 caller.
    """
    del limit
    # KR 종목코드 검증
    if not isKrStockCode(stockCode or ""):
        raise ValueError(f"Naver sector PER는 KR 종목코드만 지원합니다: {stockCode!r}")

    url = f"{_API_BASE}/{stockCode}/integration"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver sector PER 요청 실패: {stockCode}") from exc
    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver sector PER 응답 schema가 객체가 아닙니다")

    industry_info = data.get("industryInfo")
    if industry_info is None:
        return None
    if not isinstance(industry_info, dict):
        raise SourceUnavailableError("Naver sector PER industryInfo가 객체가 아닙니다")

    return _parsePriceNumber(industry_info.get("per"), "industryInfo.per", "배")


# ══════════════════════════════════════
# 통합 수집
# ══════════════════════════════════════


async def fetchAll(
    stockCode: str,
    client,
    *,
    limit: int | None = None,
) -> GatherResult:
    """네이버에서 가져올 수 있는 모든 데이터를 수집.

    Capabilities: 한 종목코드 fetch 1 회로 GatherResult (price + flow + ...) 일괄.
    AIContext: collect mixin 의 KR 도메인 fan-out 진입.
    Guide: 부분 결과 가능 — 일부 axis 실패는 다른 axis 결과로 진행.
    When: gather.collect mixin 호출 시 KR 도메인 진입.
    How: fetchPrice/fetchFlow 등 병렬 호출 → GatherResult 통합.

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.
    limit : int | None
        단건 GatherResult 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    GatherResult
        domain : str — ``"naver"``
        price : PriceSnapshot | None — 현재가 스냅샷
        flow : FlowData | None — 외국인/기관 수급 스냅샷
        sector_per : float | None — 동종업종 PER (배)
        error : str | None — 수집 실패 시 에러 메시지

    Raises
    ------
    없음
        SourceUnavailableError 는 GatherResult.error 로 흡수.

    Example
    -------
    >>> r = await fetchAll("005930", client)

    Requires
    --------
    네트워크 + KR 6 자리 종목코드. fetchPrice/fetchFlow/fetchSectorPer 모두 호출.
    부분 실패 OK — GatherResult.error 로 흡수.

    See Also
    --------
    mixins/collect : 본 함수의 fan-out caller.
    fetchPrice · fetchFlow · fetchSectorPer : 본 함수가 호출하는 backend.
    """
    del limit
    result = GatherResult(domain="naver")
    try:
        result.price = await fetchPrice(stockCode, client)
        # flow: 시계열 → 스냅샷 변환 (GatherResult 호환)
        flow_series = await fetchFlow(stockCode, client)
        if flow_series:
            latest = flow_series[0]
            result.flow = FlowData(
                foreign_net=latest.get("foreignNet") or 0.0,
                institution_net=latest.get("institutionNet") or 0.0,
                foreign_holding_ratio=latest.get("foreignHoldingRatio") or 0.0,
                source="naver",
            )
        result.sector_per = await fetchSectorPer(stockCode, client)
    except SourceUnavailableError as exc:
        result.error = str(exc)
    return result


def _intradayStamp(value: str, *, isEnd: bool) -> str:
    """분봉 조회 파라미터 정규화 → ``YYYYMMDDHHMM`` (12 자리).

    ``"2026-07-03"`` 처럼 날짜만 오면 장 시작(0900)/마감(1530) 시각을 채운다.
    구분자(``-`` ``:`` ``T`` 공백)는 제거하고, 이미 12 자리면 그대로 통과한다.
    8 자리 미만이면 빈 문자열 (파라미터 미부착).
    """
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) >= 12:
        return digits[:12]
    if len(digits) >= 8:
        return digits[:8] + (_INTRADAY_CLOSE_HHMM if isEnd else _INTRADAY_OPEN_HHMM)
    return ""


def _parseIntradayRows(data: object) -> list[dict]:
    """네이버 분봉 JSON(list) → 정규화 OHLCV list[dict] (datetime 오름차순).

    list 가 아니거나 파싱 불가한 항목은 건너뛴다. 다일 응답이면 세션 경계는
    ``datetime[:10]`` (날짜) 로 구분된다.
    """
    if not isinstance(data, list):
        raise SourceUnavailableError("Naver intraday 응답 schema가 배열이 아닙니다")
    rows: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            raise SourceUnavailableError("Naver intraday 행이 객체가 아닙니다")
        dt = str(item.get("localDateTime") or "")
        if len(dt) < 14 or not dt[:14].isdigit():
            raise SourceUnavailableError(f"Naver intraday localDateTime이 올바르지 않습니다: {dt!r}")
        close = item.get("currentPrice")
        if close is None:
            raise SourceUnavailableError("Naver intraday currentPrice가 없습니다")
        try:
            rows.append(
                {
                    "datetime": f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}T{dt[8:10]}:{dt[10:12]}:{dt[12:14]}",
                    "open": float(item.get("openPrice") or 0.0),
                    "high": float(item.get("highPrice") or 0.0),
                    "low": float(item.get("lowPrice") or 0.0),
                    "close": float(close),
                    "volume": int(item.get("accumulatedTradingVolume") or 0),
                }
            )
        except (TypeError, ValueError) as exc:
            raise SourceUnavailableError("Naver intraday 숫자 필드를 해석할 수 없습니다") from exc
    rows.sort(key=lambda r: r["datetime"])
    return rows


async def _requestIntraday(url: str, client, *, params: dict | None) -> list[dict]:
    """분봉 엔드포인트 1 회 호출 → 파싱 rows."""
    try:
        if params:
            resp = await client.get(url, params=params, headers={"Accept": "application/json"})
        else:
            resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver intraday 요청 실패: {url}") from exc
    return _parseIntradayRows(data)


async def fetchIntraday(
    stockCode: str,
    client,
    *,
    market: str = "KR",
    start: str = "",
    end: str = "",
    limit: int | None = None,
    fallbackDays: int = _INTRADAY_FALLBACK_DAYS,
    **_: object,
) -> list[dict]:
    """네이버 → 1분봉 OHLCV. 당일 + 과거 세션(start/end) + 최근 거래일 폴백.

    Capabilities: KR Naver api.stock.naver.com 1분봉 list[dict] (당일·과거·폴백).
    AIContext: intraday 분석 (gap/spike 분 단위) 의 raw 원천.
    Guide: 기본은 당일. start/end 로 과거 세션, 휴장일엔 최근 거래일로 폴백.
    When: intraday 가격 변동 분석 시 (당일 실시간 또는 특정 과거 세션).
    How: api.stock.naver.com minute JSON + startDateTime/endDateTime → list[dict].

    ``minuteType``/``count`` 는 서버가 무시하지만 ``startDateTime``/``endDateTime``
    (YYYYMMDDHHMM 12 자리) 는 유효해서 과거 세션도 조회된다. 구간이 여러 거래일을
    걸치면 다일이 한 번에 오며(주말/휴장일은 자동 제외), 세션은 날짜로 구분된다.
    3/5/15/30/60분봉은 이 1분봉 결과를 Polars 로 리샘플하여 얻는다.

    호출 모드:

    - start/end 미지정 → 당일 세션. 오늘이 휴장/장전이라 빈 응답이면
      ``fallbackDays`` 범위 내 최근 거래일 세션으로 폴백.
    - start(또는 end) 지정 → 그 구간(다일 가능)을 그대로 반환. 폴백 없음.

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.
    market : str
        시장 코드. ``"KR"`` 외에는 ValueError.
    start : str
        시작 시각. ``"2026-07-03"`` (날짜만이면 0900) 또는
        ``"2026-07-03T09:30"``/``"202607030930"``. 빈 문자열이면 당일 모드.
    end : str
        종료 시각. 날짜만이면 1530. 빈 문자열이면 start 부터 현재까지.
    limit : int | None
        반환 행수 상한 (가장 최근 N분). None이면 전체.
    fallbackDays : int
        당일 빈 응답 시 최근 거래일을 찾을 소급 일수. 0이면 폴백 비활성.

    Returns
    -------
    list[dict]
        1분봉 OHLCV 목록 (datetime 오름차순). 각 dict 키:

        - datetime : str. ISO8601 (``YYYY-MM-DDTHH:MM:SS``, KST)
        - open : float. 시가 (원)
        - high : float. 고가 (원)
        - low : float. 저가 (원)
        - close : float. 종가 (원)
        - volume : int. 누적 거래량 (주)

        유효한 응답에 분봉이 없으면 빈 리스트.

    Raises
    ------
    ValueError
        KR 외 시장 또는 잘못된 종목코드.
    SourceUnavailableError
        Naver 요청, JSON, schema 또는 행 파싱 실패.

    Example
    -------
    >>> rows = await fetchIntraday("005930", client, market="KR")
    >>> past = await fetchIntraday("005930", client, start="2026-07-03")

    Requires
    --------
    네트워크 (``api.stock.naver.com/chart/domestic/item/{code}/minute``) + KR 6 자리
    종목코드. 과거 세션은 ``startDateTime``/``endDateTime`` (12 자리) 로 조회.

    See Also
    --------
    fetchHistory : 일별 OHLCV (장기).
    transforms/indicatorDispatch : 분봉 리샘플 + 보조지표.
    """
    if market != "KR":
        raise ValueError(f"Naver intraday는 KR 시장만 지원합니다: {market!r}")
    sc = stockCode.strip() if stockCode else ""
    # KR 종목코드 검증
    if not isKrStockCode(sc):
        raise ValueError(f"Naver intraday는 KR 종목코드만 지원합니다: {stockCode!r}")

    url = _INTRADAY_URL.format(code=sc)

    def _cap(rows: list[dict]) -> list[dict]:
        return rows[-limit:] if (limit is not None and limit > 0) else rows

    # 1) 명시 구간 조회. start/end 지정 시 그 구간(다일 가능)을 한 번에.
    if start or end:
        params: dict[str, str] = {}
        s = _intradayStamp(start, isEnd=False)
        if s:
            params["startDateTime"] = s
        e = _intradayStamp(end, isEnd=True)
        if e:
            params["endDateTime"] = e
        return _cap(await _requestIntraday(url, client, params=params))

    # 2) 기본 = 당일 세션 (기존 동작 보존: 파라미터 없는 단일 호출).
    rows = await _requestIntraday(url, client, params=None)
    if rows:
        return _cap(rows)

    # 3) 폴백 = 오늘이 휴장/장전이라 빈 응답이면 최근 거래일 세션으로.
    if fallbackDays > 0:
        windowStart = (datetime.now(_KST).date() - timedelta(days=fallbackDays)).strftime("%Y%m%d")
        spanned = await _requestIntraday(url, client, params={"startDateTime": windowStart + _INTRADAY_OPEN_HHMM})
        if spanned:
            latestDay = spanned[-1]["datetime"][:10]
            return _cap([r for r in spanned if r["datetime"][:10] == latestDay])
    return rows


async def fetchHistory(
    stockCode: str,
    client,
    *,
    start: str = "",
    end: str = "",
    market: str = "KR",
    limit: int | None = None,
) -> list[dict]:
    """네이버 차트 API — 한번에 6000일 수정주가 OHLCV (FDR 방식).

    Capabilities: KR Naver fchart 6000일 수정주가 일별 OHLCV bulk fetch.
    AIContext: gather.history KR primary backend — backtest/timeseries 진입.
    Guide: 단일 호출로 6000일 수정주가. fchart 의 adjustment 표준.
    When: KR 종목의 장기 일별 OHLCV 필요 시 (백테스트, 추세 분석).
    How: fchart.stock.naver.com sise.nhn → text parse → list[dict].

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    client
        비동기 HTTP 클라이언트.
    start : str
        시작일 (YYYY-MM-DD). 빈 문자열이면 필터 없음.
    end : str
        종료일 (YYYY-MM-DD). 빈 문자열이면 필터 없음.
    market : str
        시장 코드. ``"KR"`` 외에는 빈 리스트 반환.
    limit : int | None
        반환 행수 상한 (가장 최근 N일). None이면 [start, end] 전체.

    Returns
    -------
    list[dict]
        수정주가 OHLCV 행 목록 (날짜 오름차순). 각 dict 키:

        - date : str — 거래일 (YYYY-MM-DD)
        - open : float — 시가 (원)
        - high : float — 고가 (원)
        - low : float — 저가 (원)
        - close : float — 종가 (원)
        - volume : int — 거래량 (주)

        KR 외 시장 또는 정상 응답에 데이터가 없으면 빈 리스트.

    Raises
    ------
    SourceUnavailableError
        네트워크, 응답 형식 또는 행 파싱에 실패한 경우.

    Example
    -------
    >>> rows = await fetchHistory("005930", client, start="2024-01-01")

    Requires
    --------
    네트워크 (``fchart.stock.naver.com/sise.nhn``) + KR 6 자리 종목코드 또는 지수 심볼
    (KOSPI/KOSDAQ/KPI200). 단일 호출 6000 일 수정주가.

    See Also
    --------
    sources/history.fetch : 호출 체인 (KR primary).
    fdr.fetchHistory · yahooChart.fetchHistory · fmp.fetchHistory : 동행 source.
    fetchIntraday : 당일 분봉 진입.
    """
    if market != "KR":
        return []
    # KR 종목코드 검증 (지수 심볼 KOSPI/KOSDAQ 등도 허용)
    sc = stockCode.strip() if stockCode else ""
    if not isKrStockCode(sc) and sc not in ("KOSPI", "KOSDAQ", "KPI200"):
        return []
    import re

    try:
        resp = await client.get(
            _CHART_URL,
            params={
                "timeframe": "day",
                "count": "6000",
                "requestType": "0",
                "symbol": stockCode,
            },
        )
        text = resp.text
    except (SourceUnavailableError, OSError) as exc:
        raise SourceUnavailableError(f"Naver history 요청 실패: {stockCode}") from exc

    if not isinstance(text, str) or not text.strip():
        raise SourceUnavailableError("Naver history 응답 본문이 비어 있습니다")

    items = re.findall(r'<item\s+data="(.*?)"\s*/>', text)
    if not items:
        if "<protocol" in text and "<chartdata" in text:
            return []
        raise SourceUnavailableError("Naver history 응답 schema를 확인할 수 없습니다")

    rows: list[dict] = []
    try:
        for item in items:
            parts = item.split("|")
            if len(parts) < 6:
                raise ValueError("OHLCV 필드 수가 6개보다 적습니다")
            d = parts[0]
            if len(d) != 8 or not d.isdigit():
                raise ValueError(f"거래일 형식이 올바르지 않습니다: {d!r}")
            dt = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            if start and dt < start:
                continue
            if end and dt > end:
                continue
            if not all(parts[index] for index in (1, 2, 3, 4)):
                raise ValueError(f"OHLC 필드가 비어 있습니다: {d}")
            o = float(parts[1])
            # 거래정지일 (open=0) 건너뛰기
            if o == 0.0:
                continue
            rows.append(
                {
                    "date": dt,
                    "open": o,
                    "high": float(parts[2]),
                    "low": float(parts[3]),
                    "close": float(parts[4]),
                    "volume": int(parts[5]) if parts[5] else 0,
                }
            )
    except (TypeError, ValueError) as exc:
        raise SourceUnavailableError("Naver history 행을 해석할 수 없습니다") from exc
    if limit is not None and limit > 0:
        return rows[-limit:]  # 날짜 오름차순 (수정주가)
    return rows  # 날짜 오름차순 (수정주가)
