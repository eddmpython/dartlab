"""시장별 메타데이터 — ticker 변환 + fallback 체인 + 거래시간."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketConfig:
    """시장 중앙 설정."""

    code: str  # "KR", "US", "JP"
    name: str  # "한국", "미국"
    currency: str  # "KRW", "USD"
    exchange_suffix: str  # ".KS", "", ".T"
    benchmark_ticker: str  # "^KS11", "^GSPC"
    fallback_chain: tuple[str, ...]  # ("naver", "yahoo_direct", "yahoo")
    trading_hours_utc: tuple[int, int]  # (start_hour, end_hour)


# ══════════════════════════════════════
# 시장 레지스트리
# ══════════════════════════════════════

MARKETS: dict[str, MarketConfig] = {
    "KR": MarketConfig(
        code="KR", name="한국", currency="KRW",
        exchange_suffix=".KS", benchmark_ticker="^KS11",
        fallback_chain=("naver", "yahoo_direct", "yahoo"),
        trading_hours_utc=(0, 6),
    ),
    "US": MarketConfig(
        code="US", name="미국", currency="USD",
        exchange_suffix="", benchmark_ticker="^GSPC",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(14, 21),
    ),
    "JP": MarketConfig(
        code="JP", name="일본", currency="JPY",
        exchange_suffix=".T", benchmark_ticker="^N225",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(0, 6),
    ),
    "HK": MarketConfig(
        code="HK", name="홍콩", currency="HKD",
        exchange_suffix=".HK", benchmark_ticker="^HSI",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(1, 8),
    ),
    "UK": MarketConfig(
        code="UK", name="영국", currency="GBP",
        exchange_suffix=".L", benchmark_ticker="^FTSE",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(8, 16),
    ),
    "DE": MarketConfig(
        code="DE", name="독일", currency="EUR",
        exchange_suffix=".DE", benchmark_ticker="^GDAXI",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(7, 16),
    ),
    "CN": MarketConfig(
        code="CN", name="중국", currency="CNY",
        exchange_suffix=".SS", benchmark_ticker="000001.SS",
        fallback_chain=("yahoo_direct", "fmp"),
        trading_hours_utc=(1, 7),
    ),
    "IN": MarketConfig(
        code="IN", name="인도", currency="INR",
        exchange_suffix=".NS", benchmark_ticker="^NSEI",
        fallback_chain=("yahoo_direct", "fmp", "yahoo"),
        trading_hours_utc=(4, 10),
    ),
}

# 심천 거래소 종목 접미사 (상하이 .SS가 기본)
_CN_SZ_PREFIXES = ("00", "30")


def get_market_config(market: str) -> MarketConfig:
    """시장 코드 → MarketConfig. 없으면 US 기본값."""
    return MARKETS.get(market.upper(), MARKETS["US"])


def resolve_ticker(stock_code: str, market: str, source: str) -> str:
    """stock_code + market + source → 소스별 ticker 문자열.

    - naver: 종목코드 그대로 (KR only)
    - yahoo_direct / yahoo: 종목코드 + 거래소 접미사
    - fmp: 종목코드 + 거래소 접미사 (Yahoo와 동일 형식)
    """
    market = market.upper()
    config = get_market_config(market)

    # naver는 KR 종목코드를 그대로 사용
    if source == "naver":
        return stock_code

    # US는 접미사 없음
    if market == "US":
        return stock_code

    # CN 심천 거래소 분기
    if market == "CN":
        for prefix in _CN_SZ_PREFIXES:
            if stock_code.startswith(prefix):
                return f"{stock_code}.SZ"
        return f"{stock_code}.SS"

    # HK: 4자리 패딩 (Yahoo는 0293.HK 형식)
    if market == "HK" and stock_code.isdigit():
        return f"{stock_code.zfill(4)}{config.exchange_suffix}"

    return f"{stock_code}{config.exchange_suffix}"
