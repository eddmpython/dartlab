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


def fetch_price(stock_code: str, client) -> PriceSnapshot | None:
    """네이버 → 현재가 + PER/PBR + 52주 범위."""
    url = f"{_API_BASE}/{stock_code}/basic"
    try:
        resp = client.get(url, headers={"Accept": "application/json"})
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
    )


def fetch_consensus(stock_code: str, client) -> ConsensusData | None:
    """네이버 → 컨센서스 목표가 + 투자의견."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver consensus API 실패 (%s): %s", stock_code, exc)
        return None

    consensus_info = data.get("consensusInfo")
    if not consensus_info:
        return None

    target = _clean_number(consensus_info.get("targetPrice"))
    if not target or target <= 0:
        return None

    analyst_count = consensus_info.get("analystCount", 0)
    if isinstance(analyst_count, str):
        analyst_count = int(_clean_number(analyst_count) or 0)

    # 투자의견 비율
    buy_ratio = 0.0
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

    high = _clean_number(consensus_info.get("targetPriceHigh"))
    low = _clean_number(consensus_info.get("targetPriceLow"))

    return ConsensusData(
        target_price=target,
        analyst_count=analyst_count,
        buy_ratio=buy_ratio,
        high=high or target,
        low=low or target,
        source="naver",
    )


def fetch_flow(stock_code: str, client) -> FlowData | None:
    """네이버 → 외국인/기관 순매수."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except (SourceUnavailableError, ValueError) as exc:
        log.warning("naver flow API 실패 (%s): %s", stock_code, exc)
        return None

    foreign_net = 0.0
    institution_net = 0.0
    foreign_holding_ratio = 0.0

    # 외국인 보유 비율
    foreign_info = data.get("foreignSummary")
    if foreign_info:
        ratio = _clean_number(foreign_info.get("foreignOwnershipRatio"))
        if ratio is not None:
            foreign_holding_ratio = ratio

    # 투자자별 매매동향
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

    return FlowData(
        foreign_net=foreign_net,
        institution_net=institution_net,
        foreign_holding_ratio=foreign_holding_ratio,
        source="naver",
    )


def fetch_sector_per(stock_code: str, client) -> float | None:
    """네이버 → 동종업종 PER."""
    url = f"{_API_BASE}/{stock_code}/integration"
    try:
        resp = client.get(url, headers={"Accept": "application/json"})
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


def fetch_all(stock_code: str, client) -> GatherResult:
    """네이버에서 가져올 수 있는 모든 데이터를 수집."""
    result = GatherResult(domain="naver")
    try:
        result.price = fetch_price(stock_code, client)
        result.consensus = fetch_consensus(stock_code, client)
        result.flow = fetch_flow(stock_code, client)
        result.sector_per = fetch_sector_per(stock_code, client)
    except SourceUnavailableError as exc:
        result.error = str(exc)
    return result
