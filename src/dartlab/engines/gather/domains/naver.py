"""네이버 금융 데이터 수집 — 주가 + 컨센서스 + 수급 + 업종PER.

네이버 금융 API에서 한국 시장 데이터를 수집한다.
robots.txt 준수, 도메인당 30RPM 이하.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..types import (
    ConsensusData,
    FlowData,
    GatherResult,
    PriceSnapshot,
    RevenueConsensus,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)

# NaverPay 증권 API (JSON)
_API_BASE = "https://m.stock.naver.com/api/stock"


def _clean_number(text: str | None) -> float | None:
    """숫자 텍스트 파싱 — 콤마, 공백, +/- 처리."""
    if not text:
        return None
    cleaned = str(text).strip().replace(",", "").replace("+", "").replace(" ", "")
    if not cleaned or cleaned in ("N/A", "-"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


# ══════════════════════════════════════
# 개별 데이터 수집 함수
# ══════════════════════════════════════


async def fetch_price(stock_code: str, client, **kwargs) -> PriceSnapshot | None:
    """네이버 → 현재가 + PER/PBR + 52주 범위."""
    url = f"{_API_BASE}/{stock_code}/basic"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver price API 실패 (%s): %s", stock_code, exc)
        return None

    current = _clean_number(data.get("closePrice"))
    if not current:
        return None

    return PriceSnapshot(
        current=current,
        change=_clean_number(data.get("compareToPreviousClosePrice")) or 0.0,
        change_pct=_clean_number(data.get("fluctuationsRatio")) or 0.0,
        high_52w=_clean_number(data.get("high52wPrice")) or 0.0,
        low_52w=_clean_number(data.get("low52wPrice")) or 0.0,
        volume=int(_clean_number(data.get("accumulatedTradingVolume")) or 0),
        market_cap=_clean_number(data.get("marketCap")) or 0.0,
        per=_clean_number(data.get("per")),
        pbr=_clean_number(data.get("pbr")),
        dividend_yield=_clean_number(data.get("dividendYield")),
        source="naver",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency="KRW",
        market="KR",
    )


async def fetch_consensus(stock_code: str, client) -> ConsensusData | None:
    """네이버 → 컨센서스 목표가 + 투자의견."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver consensus API 실패 (%s): %s", stock_code, exc)
        return None

    consensus_info = data.get("consensusInfo")
    if not consensus_info:
        return None

    # 네이버 API v2: priceTargetMean / v1: targetPrice
    target = _clean_number(
        consensus_info.get("priceTargetMean") or consensus_info.get("targetPrice")
    )
    if not target or target <= 0:
        return None

    analyst_count = consensus_info.get("analystCount", 0)
    if isinstance(analyst_count, str):
        analyst_count = int(_clean_number(analyst_count) or 0)

    # 투자의견: recommMean (1~5 스케일, 4+ ≈ 매수) 또는 investmentOpinion 리스트
    buy_ratio = 0.0
    recomm_mean = _clean_number(consensus_info.get("recommMean"))
    if recomm_mean is not None and recomm_mean > 0:
        buy_ratio = min(recomm_mean / 5.0, 1.0)
    else:
        total_opinions = 0
        buy_count = 0
        opinion_data = consensus_info.get("investmentOpinion")
        if opinion_data and isinstance(opinion_data, list):
            for item in opinion_data:
                count = int(item.get("count", 0))
                opinion = item.get("opinion", "")
                total_opinions += count
                if opinion in ("매수", "강력매수", "Buy", "StrongBuy"):
                    buy_count += count
            if total_opinions > 0:
                buy_ratio = buy_count / total_opinions

    high = _clean_number(consensus_info.get("targetPriceHigh") or consensus_info.get("priceTargetHigh"))
    low = _clean_number(consensus_info.get("targetPriceLow") or consensus_info.get("priceTargetLow"))

    return ConsensusData(
        target_price=target,
        analyst_count=analyst_count,
        buy_ratio=buy_ratio,
        high=high or target,
        low=low or target,
        source="naver",
    )


async def fetch_flow(stock_code: str, client) -> list[dict] | None:
    """네이버 → 외국인/기관 수급 시계열."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver flow API 실패 (%s): %s", stock_code, exc)
        return None

    # v2: dealTrendInfos 배열 전체 활용 (최신순)
    deal_trends = data.get("dealTrendInfos") or []
    if deal_trends and isinstance(deal_trends, list):
        result = []
        for item in deal_trends:
            fn = _clean_number(item.get("foreignerPureBuyQuant"))
            on = _clean_number(item.get("organPureBuyQuant"))
            ind = _clean_number(item.get("individualPureBuyQuant"))
            ratio_str = item.get("foreignerHoldRatio", "")
            ratio = None
            if ratio_str:
                ratio = _clean_number(str(ratio_str).replace("%", ""))
            row = {
                "date": item.get("bizdate", ""),
                "foreignNet": fn or 0.0,
                "institutionNet": on or 0.0,
                "individualNet": ind or 0.0,
                "foreignHoldingRatio": ratio or 0.0,
            }
            result.append(row)
        if result:
            return result

    # v1 fallback: foreignSummary + dealTrendByInvestor (스냅샷 1건)
    foreign_net = 0.0
    institution_net = 0.0
    foreign_holding_ratio = 0.0

    foreign_info = data.get("foreignSummary")
    if foreign_info:
        ratio = _clean_number(foreign_info.get("foreignOwnershipRatio"))
        if ratio is not None:
            foreign_holding_ratio = ratio

    investor_info = data.get("dealTrendByInvestor")
    if investor_info and isinstance(investor_info, list):
        for item in investor_info:
            investor_type = item.get("investorType", "")
            net_buy = _clean_number(item.get("accumulatedNetBuyVolume"))
            if net_buy is None:
                continue
            if "외국인" in investor_type or investor_type == "FOREIGNER":
                foreign_net = net_buy
            elif "기관" in investor_type or investor_type == "INSTITUTION":
                institution_net = net_buy

    if foreign_net == 0.0 and institution_net == 0.0 and foreign_holding_ratio == 0.0:
        return None

    return [{"date": "", "foreignNet": foreign_net, "institutionNet": institution_net, "foreignHoldingRatio": foreign_holding_ratio}]


async def fetch_revenue_consensus(stock_code: str, client) -> list[RevenueConsensus]:
    """네이버 → 연간 매출/영업이익/순이익 컨센서스.

    finance/annual API에서 isConsensus='Y'인 기간의 재무 추정치를 추출한다.
    실적 확정 기간(isConsensus='N')도 함께 반환하여 시계열 비교 가능.
    """
    url = f"{_API_BASE}/{stock_code}/finance/annual"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver finance/annual API 실패 (%s): %s", stock_code, exc)
        return []

    fi = data.get("financeInfo")
    if not fi:
        return []

    titles = fi.get("trTitleList", [])
    rows = fi.get("rowList", [])
    if not titles or not rows:
        return []

    # 항목별 dict 구축
    row_map: dict[str, dict] = {}
    for row in rows:
        title = row.get("title", "")
        cols = row.get("columns")
        if title and isinstance(cols, dict):
            row_map[title] = cols

    results: list[RevenueConsensus] = []
    for t in titles:
        key = t.get("key", "")
        is_consensus = t.get("isConsensus") == "Y"
        if not key or len(key) < 4:
            continue

        fiscal_year = int(key[:4])

        revenue = _clean_number(row_map.get("매출액", {}).get(key, {}).get("value"))
        op_profit = _clean_number(row_map.get("영업이익", {}).get(key, {}).get("value"))
        net_income = _clean_number(row_map.get("당기순이익", {}).get(key, {}).get("value"))
        eps = _clean_number(row_map.get("EPS", {}).get(key, {}).get("value"))
        per = _clean_number(row_map.get("PER", {}).get(key, {}).get("value"))

        if revenue is None and op_profit is None:
            continue

        results.append(
            RevenueConsensus(
                fiscal_year=fiscal_year,
                revenue_est=revenue or 0.0,
                operating_profit_est=op_profit,
                net_income_est=net_income,
                eps_est=eps,
                per_est=per,
                source="naver_consensus" if is_consensus else "naver_actual",
            )
        )

    return results


async def fetch_sector_per(stock_code: str, client) -> float | None:
    """네이버 → 동종업종 PER."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver sector PER API 실패 (%s): %s", stock_code, exc)
        return None

    industry_info = data.get("industryInfo")
    if not industry_info:
        return None

    return _clean_number(industry_info.get("per"))


# ══════════════════════════════════════
# 통합 수집
# ══════════════════════════════════════


async def fetch_all(stock_code: str, client) -> GatherResult:
    """네이버에서 가져올 수 있는 모든 데이터를 수집."""
    result = GatherResult(domain="naver")
    try:
        result.price = await fetch_price(stock_code, client)
        result.consensus = await fetch_consensus(stock_code, client)
        # flow: 시계열 → 스냅샷 변환 (GatherResult 호환)
        flow_series = await fetch_flow(stock_code, client)
        if flow_series:
            latest = flow_series[0]
            result.flow = FlowData(
                foreign_net=latest.get("foreignNet") or 0.0,
                institution_net=latest.get("institutionNet") or 0.0,
                foreign_holding_ratio=latest.get("foreignHoldingRatio") or 0.0,
                source="naver",
            )
        result.sector_per = await fetch_sector_per(stock_code, client)
    except SourceUnavailableError as exc:
        result.error = str(exc)
    return result


async def fetch_history(
    stock_code: str,
    client,
    *,
    start: str = "",
    end: str = "",
    market: str = "KR",
) -> list[dict]:
    """네이버 → 주가 OHLCV 시계열 (KR 전용, 페이징)."""
    if market != "KR":
        return []
    url = f"{_API_BASE}/{stock_code}/price"
    all_rows: list[dict] = []
    page = 1
    max_pages = 20  # 최대 1000일 (50 * 20)

    while page <= max_pages:
        try:
            resp = await client.get(
                url,
                params={"pageSize": 50, "page": page},
                headers={"Accept": "application/json"},
            )
            items = resp.json()
        except (SourceUnavailableError, ValueError) as exc:
            log.debug("naver history page %d 실패: %s", page, exc)
            break
        if not items or not isinstance(items, list):
            break
        for item in items:
            dt = item.get("localTradedAt", "")
            if start and dt < start:
                all_rows.append({
                    "date": dt,
                    "open": _clean_number(item.get("openPrice")) or 0.0,
                    "high": _clean_number(item.get("highPrice")) or 0.0,
                    "low": _clean_number(item.get("lowPrice")) or 0.0,
                    "close": _clean_number(item.get("closePrice")) or 0.0,
                    "volume": item.get("accumulatedTradingVolume") or 0,
                })
                return list(reversed(all_rows))  # 날짜 오름차순
            if end and dt > end:
                continue
            all_rows.append({
                "date": dt,
                "open": _clean_number(item.get("openPrice")) or 0.0,
                "high": _clean_number(item.get("highPrice")) or 0.0,
                "low": _clean_number(item.get("lowPrice")) or 0.0,
                "close": _clean_number(item.get("closePrice")) or 0.0,
                "volume": item.get("accumulatedTradingVolume") or 0,
            })
        if len(items) < 50:
            break
        page += 1

    return list(reversed(all_rows))  # 날짜 오름차순
