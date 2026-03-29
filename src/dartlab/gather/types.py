"""Gather 엔진 데이터 타입 — 멀티소스 수집 결과."""

from __future__ import annotations

from dataclasses import dataclass, field

# ══════════════════════════════════════
# 도메인 설정
# ══════════════════════════════════════


@dataclass(slots=True)
class DomainConfig:
    """도메인별 rate limit + 동시 연결 정책."""

    rpm: int = 30
    concurrency: int = 2
    timeout: float = 10.0
    jitter_min: float = 0.3  # 요청 전 최소 랜덤 대기 (초)
    jitter_max: float = 1.5  # 요청 전 최대 랜덤 대기 (초)
    min_interval: float = 0.0  # 요청 간 최소 간격 (초, 0=제한 없음)


# ══════════════════════════════════════
# 수집 데이터 타입
# ══════════════════════════════════════


@dataclass
class PriceSnapshot:
    """주가 스냅샷."""

    current: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    high_52w: float = 0.0
    low_52w: float = 0.0
    volume: int = 0
    market_cap: float = 0.0  # 억원
    per: float | None = None
    pbr: float | None = None
    dividend_yield: float | None = None
    source: str = ""
    fetched_at: str = ""
    # 글로벌 확장 (기본값 → 하위호환)
    currency: str = "KRW"
    exchange: str = ""
    market: str = "KR"
    is_stale: bool = False

    def __repr__(self) -> str:
        stale_tag = " [stale]" if self.is_stale else ""
        lines = [f"[주가 — {self.source}{stale_tag}]"]
        lines.append(f"  현재가: {self.current:,.0f}")
        if self.change != 0:
            lines.append(f"  변동: {self.change:+,.0f} ({self.change_pct:+.2f}%)")
        if self.per is not None:
            lines.append(f"  PER: {self.per:.2f}")
        if self.pbr is not None:
            lines.append(f"  PBR: {self.pbr:.2f}")
        if self.high_52w > 0:
            lines.append(f"  52주: {self.low_52w:,.0f}~{self.high_52w:,.0f}")
        return "\n".join(lines)


@dataclass
class ConsensusData:
    """애널리스트 컨센서스."""

    target_price: float = 0.0
    analyst_count: int = 0
    buy_ratio: float = 0.0  # 매수 비율 (0~1)
    high: float = 0.0
    low: float = 0.0
    source: str = ""

    def __repr__(self) -> str:
        return (
            f"Consensus(target={self.target_price:,.0f}, "
            f"analysts={self.analyst_count}, "
            f"buy={self.buy_ratio:.0%}, "
            f"range={self.low:,.0f}~{self.high:,.0f})"
        )


@dataclass
class RevenueConsensus:
    """애널리스트 매출/이익 컨센서스 — 네이버 금융 finance/annual API."""

    fiscal_year: int = 0
    revenue_est: float = 0.0  # 예상 매출 (억원)
    operating_profit_est: float | None = None  # 예상 영업이익 (억원)
    net_income_est: float | None = None  # 예상 순이익 (억원)
    eps_est: float | None = None  # 예상 EPS (원)
    per_est: float | None = None  # 예상 PER (배)
    source: str = ""

    def __repr__(self) -> str:
        parts = [f"RevenueConsensus({self.fiscal_year})"]
        if self.revenue_est:
            parts.append(f"매출={self.revenue_est:,.0f}억")
        if self.operating_profit_est:
            parts.append(f"영업이익={self.operating_profit_est:,.0f}억")
        if self.eps_est:
            parts.append(f"EPS={self.eps_est:,.0f}원")
        return " ".join(parts)


@dataclass
class FlowData:
    """투자자별 수급 데이터."""

    foreign_net: float = 0.0  # 외국인 순매수 (주)
    institution_net: float = 0.0  # 기관 순매수 (주)
    foreign_holding_ratio: float = 0.0  # 외국인 보유 비율 (%)
    source: str = ""

    def __repr__(self) -> str:
        return (
            f"Flow(외국인={self.foreign_net:+,.0f}, "
            f"기관={self.institution_net:+,.0f}, "
            f"외국인비중={self.foreign_holding_ratio:.1f}%)"
        )


@dataclass
class NewsItem:
    """뉴스 항목."""

    date: str = ""  # ISO date (YYYY-MM-DD)
    title: str = ""
    source: str = ""
    url: str = ""


@dataclass
class SectorInfo:
    """업종 분류 정보."""

    sectorCode: str = ""
    sectorName: str = ""
    industryCode: str = ""
    industryName: str = ""
    market: str = ""  # KOSPI/KOSDAQ
    source: str = ""

    def __repr__(self) -> str:
        parts = [f"Sector({self.sectorName}"]
        if self.industryName:
            parts[0] += f"/{self.industryName}"
        parts[0] += f", {self.market})"
        return parts[0]


@dataclass
class ShortSellingData:
    """공매도 잔고/거래 데이터."""

    date: str = ""
    shortVolume: int = 0
    shortAmount: int = 0  # 원
    totalVolume: int = 0
    shortRatio: float = 0.0  # 공매도 비중 (%)
    balance: int = 0  # 잔고 수량
    balanceRatio: float = 0.0  # 잔고 비율 (%)
    source: str = ""

    def __repr__(self) -> str:
        return f"Short(비중={self.shortRatio:.1f}%, 잔고비율={self.balanceRatio:.1f}%)"


@dataclass
class InsiderTrade:
    """내부자(임원/주요주주) 주식 거래."""

    date: str = ""
    name: str = ""
    position: str = ""
    tradeType: str = ""  # 취득/처분/장내매수/장내매도
    changeShares: int = 0
    afterShares: int = 0
    reason: str = ""
    source: str = ""

    def __repr__(self) -> str:
        return f"Insider({self.name} {self.tradeType} {self.changeShares:+,}주 {self.date})"


@dataclass
class MajorHolder:
    """5% 이상 대량보유 주주."""

    holderName: str = ""
    shares: int = 0
    ratio: float = 0.0  # 보유비율 (%)
    changeDate: str = ""
    changeType: str = ""  # 취득/처분/변동
    source: str = ""

    def __repr__(self) -> str:
        return f"MajorHolder({self.holderName} {self.ratio:.1f}% {self.changeType})"


@dataclass
class InstitutionOwnership:
    """기관/외국인 지분 보유."""

    holderName: str = ""
    shares: int = 0
    ratio: float = 0.0  # 보유비율 (%)
    value: float = 0.0  # 보유금액
    changeShares: int = 0  # 변동수량
    source: str = ""

    def __repr__(self) -> str:
        return f"Institution({self.holderName} {self.ratio:.1f}%)"


@dataclass
class UpgradeDowngrade:
    """애널리스트 등급 변경."""

    date: str = ""
    firm: str = ""
    toGrade: str = ""
    fromGrade: str = ""
    action: str = ""  # upgrade/downgrade/init/maintain/reiterated
    source: str = ""

    def __repr__(self) -> str:
        return f"Rating({self.firm} {self.action}: {self.fromGrade}->{self.toGrade})"


@dataclass
class GatherResult:
    """도메인 1개의 수집 결과 — 병렬 수집 시 반환 단위."""

    domain: str = ""
    price: PriceSnapshot | None = None
    consensus: ConsensusData | None = None
    flow: FlowData | None = None
    sector_per: float | None = None
    sectorInfo: SectorInfo | None = None
    insiderTrades: list[InsiderTrade] = field(default_factory=list)
    shortSelling: ShortSellingData | None = None
    error: str | None = None


@dataclass
class GatherSnapshot:
    """전체 병렬 수집 통합 결과."""

    stock_code: str = ""
    results: dict[str, GatherResult] = field(default_factory=dict)
    collected_at: str = ""
    _news: list[NewsItem] = field(default_factory=list)
    _sectorInfo: SectorInfo | None = None
    _insiderTrades: list[InsiderTrade] = field(default_factory=list)
    _shortSelling: ShortSellingData | None = None

    @property
    def price(self) -> PriceSnapshot | None:
        """첫 번째 가용 주가."""
        for r in self.results.values():
            if r.price:
                return r.price
        return None

    @property
    def consensus(self) -> ConsensusData | None:
        """수집된 컨센서스 데이터 반환."""
        for r in self.results.values():
            if r.consensus:
                return r.consensus
        return None

    @property
    def flow(self) -> FlowData | None:
        """수집된 수급 데이터 반환."""
        for r in self.results.values():
            if r.flow:
                return r.flow
        return None

    @property
    def news(self) -> list[NewsItem]:
        """수집된 뉴스 항목."""
        return self._news

    @property
    def sectorInfo(self) -> SectorInfo | None:
        """수집된 업종 분류."""
        for r in self.results.values():
            if r.sectorInfo:
                return r.sectorInfo
        return self._sectorInfo

    @property
    def insiderTrades(self) -> list[InsiderTrade]:
        """수집된 내부자 거래."""
        for r in self.results.values():
            if r.insiderTrades:
                return r.insiderTrades
        return self._insiderTrades

    @property
    def shortSelling(self) -> ShortSellingData | None:
        """수집된 공매도 데이터."""
        for r in self.results.values():
            if r.shortSelling:
                return r.shortSelling
        return self._shortSelling

    @property
    def sources_available(self) -> list[str]:
        """정상 응답한 소스 목록."""
        return [d for d, r in self.results.items() if r.error is None]

    @property
    def sources_failed(self) -> list[str]:
        """오류가 발생한 소스 목록."""
        return [d for d, r in self.results.items() if r.error is not None]

    def to_market_snapshot(self) -> MarketSnapshot:
        """Analyst 엔진 호환 flat 스냅샷으로 변환."""
        price = self.price
        flow = self.flow

        multiples: dict[str, float] = {}
        price_range: tuple[float, float] | None = None
        current_price = 0.0

        if price:
            current_price = price.current
            if price.per is not None:
                multiples["per"] = price.per
            if price.pbr is not None:
                multiples["pbr"] = price.pbr
            if price.dividend_yield is not None:
                multiples["dividend_yield"] = price.dividend_yield
            if price.low_52w > 0 and price.high_52w > 0:
                price_range = (price.low_52w, price.high_52w)

        # sector_per — 첫 번째 가용 결과에서
        for r in self.results.values():
            if r.sector_per:
                multiples["sector_per"] = r.sector_per
                break

        supply_demand: dict[str, float] = {}
        if flow:
            supply_demand["foreign_net"] = flow.foreign_net
            supply_demand["institution_net"] = flow.institution_net
            supply_demand["foreign_holding_ratio"] = flow.foreign_holding_ratio

        return MarketSnapshot(
            stock_code=self.stock_code,
            current_price=current_price,
            consensus=self.consensus,
            multiples=multiples,
            supply_demand=supply_demand,
            price_range_52w=price_range,
            collected_at=self.collected_at,
            sources_available=self.sources_available,
            sources_failed=self.sources_failed,
        )

    def __repr__(self) -> str:
        lines = [f"[GatherSnapshot — {self.stock_code}]"]
        if self.price:
            lines.append(f"  {self.price}")
        if self.consensus:
            lines.append(f"  {self.consensus}")
        if self.flow:
            lines.append(f"  {self.flow}")
        lines.append(f"  소스: {', '.join(self.sources_available)}")
        if self.sources_failed:
            lines.append(f"  실패: {', '.join(self.sources_failed)}")
        return "\n".join(lines)


# ══════════════════════════════════════
# Analyst 호환 스냅샷 (flat 구조)
# ══════════════════════════════════════


@dataclass
class PeerData:
    """피어 기업 멀티플 데이터."""

    ticker: str = ""
    name: str = ""
    per: float | None = None
    pbr: float | None = None
    ev_ebitda: float | None = None
    market_cap: float | None = None

    def __repr__(self) -> str:
        parts = [f"{self.ticker}({self.name})"]
        if self.per is not None:
            parts.append(f"PER={self.per:.1f}")
        if self.pbr is not None:
            parts.append(f"PBR={self.pbr:.2f}")
        if self.ev_ebitda is not None:
            parts.append(f"EV/EBITDA={self.ev_ebitda:.1f}")
        return " ".join(parts)


@dataclass
class MarketSnapshot:
    """Analyst 호환 flat 시장 데이터 — GatherSnapshot → MarketSnapshot 변환용."""

    stock_code: str = ""
    current_price: float = 0.0
    consensus: ConsensusData | None = None
    multiples: dict[str, float] = field(default_factory=dict)
    peer_multiples: list[PeerData] = field(default_factory=list)
    supply_demand: dict[str, float] = field(default_factory=dict)
    macro: dict[str, float] = field(default_factory=dict)
    price_range_52w: tuple[float, float] | None = None
    collected_at: str = ""
    sources_available: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        lines = [f"[MarketSnapshot — {self.stock_code}]"]
        lines.append(f"  현재가: {self.current_price:,.0f}")
        if self.consensus:
            lines.append(f"  컨센서스: {self.consensus}")
        if self.multiples:
            mult_str = ", ".join(f"{k}={v:.2f}" for k, v in self.multiples.items())
            lines.append(f"  멀티플: {mult_str}")
        if self.price_range_52w:
            lines.append(f"  52주 범위: {self.price_range_52w[0]:,.0f}~{self.price_range_52w[1]:,.0f}")
        return "\n".join(lines)


# ══════════════════════════════════════
# 예외
# ══════════════════════════════════════


class GatherError(Exception):
    """Gather 엔진 기본 예외."""


class SourceUnavailableError(GatherError):
    """소스 접근 불가."""


class RateLimitExceededError(GatherError):
    """Rate limit 초과."""


class CircuitOpenError(SourceUnavailableError):
    """Circuit breaker open — 소스 일시 차단."""
