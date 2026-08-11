"""Gather 엔진 데이터 타입 — 멀티소스 수집 결과."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

# ══════════════════════════════════════
# 도메인 설정
# ══════════════════════════════════════


@dataclass(slots=True)
class DomainConfig:
    """도메인별 rate limit + 동시 연결 정책.

    Attributes
    ----------
    rpm : int
        분당 최대 요청 수 (회/분). 기본 30.
    concurrency : int
        동시 연결 수 상한. 기본 2.
    timeout : float
        요청 타임아웃 (초). 기본 10.0.
    jitter_min : float
        요청 전 최소 랜덤 대기 (초). 기본 0.3.
    jitter_max : float
        요청 전 최대 랜덤 대기 (초). 기본 1.5.
    min_interval : float
        요청 간 최소 간격 (초). 0이면 제한 없음. 기본 0.0.
    """

    rpm: int = 30
    concurrency: int = 2
    timeout: float = 10.0
    jitter_min: float = 0.3  # 요청 전 최소 랜덤 대기 (초)
    jitter_max: float = 1.5  # 요청 전 최대 랜덤 대기 (초)
    minInterval: float = 0.0  # 요청 간 최소 간격 (초, 0=제한 없음)


# ══════════════════════════════════════
# 수집 데이터 타입
# ══════════════════════════════════════


@dataclass
class PriceSnapshot:
    """주가 스냅샷.

    Attributes
    ----------
    current : float
        현재가 (원 또는 해당 통화).
    change : float
        전일 대비 변동 (원).
    change_pct : float
        전일 대비 변동률 (%).
    high_52w : float
        52주 최고가 (원).
    low_52w : float
        52주 최저가 (원).
    volume : int
        거래량 (주).
    market_cap : float
        시가총액 (억원).
    per : float | None
        PER (배).
    pbr : float | None
        PBR (배).
    dividend_yield : float | None
        배당수익률 (%).
    source : str
        데이터 출처.
    fetched_at : str
        수집 시각 (ISO 형식).
    currency : str
        통화 코드 ("KRW", "USD" 등).
    exchange : str
        거래소 코드.
    market : str
        시장 코드 ("KR", "US" 등).
    is_stale : bool
        stale cache 반환 여부.
    """

    current: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    high_52w: float = 0.0
    low_52w: float = 0.0
    volume: int = 0
    marketCap: float = 0.0  # 억원
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
    # Sprint 3 PR3 — 글로벌 ID (OpenFIGI). 사용자 입력이 ISIN/FIGI 인 경우 보존.
    isin: str | None = None
    figi: str | None = None

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
    """애널리스트 컨센서스 (목표가·분석가수·출처) — backward compat shim.

    Notes
    -----
    legacy test_analyst.py 와의 호환을 위한 stub. 신규 코드는 RevenueConsensus
    또는 MarketSnapshot 사용 권장.

    Attributes
    ----------
    target_price : float | None
        애널리스트 목표주가 평균.
    analyst_count : int
        분석가 수.
    source : str
        데이터 출처 (예: "naver").
    """

    target_price: float | None = None
    analyst_count: int = 0
    buy_ratio: float = 0.0
    high: float = 0.0
    low: float = 0.0
    source: str = ""


@dataclass
class RevenueConsensus:
    """애널리스트 매출/이익 컨센서스 — 네이버 금융 finance/annual API.

    Attributes
    ----------
    fiscal_year : int
        회계연도.
    revenue_est : float
        예상 매출 (억원).
    operating_profit_est : float | None
        예상 영업이익 (억원).
    net_income_est : float | None
        예상 순이익 (억원).
    eps_est : float | None
        예상 EPS (원).
    per_est : float | None
        예상 PER (배).
    source : str
        데이터 출처.
    """

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
    """투자자별 수급 데이터.

    Attributes
    ----------
    foreign_net : float
        외국인 순매수 (주).
    institution_net : float
        기관 순매수 (주).
    foreign_holding_ratio : float
        외국인 보유 비율 (%).
    source : str
        데이터 출처.
    """

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
    """뉴스 항목.

    Attributes
    ----------
    date : str
        발행일 (YYYY-MM-DD).
    title : str
        기사 제목.
    source : str
        언론사/출처.
    url : str
        기사 URL.
    description : str
        기사 요약/스니펫. naver 검색 API 가 채우고, rss/gdelt 는 빈 문자열
        (기본값 → 하위호환). 언론사 저작권 본문 발췌이므로 공개 재배포 금지.
    """

    date: str = ""  # ISO date (YYYY-MM-DD)
    title: str = ""
    source: str = ""
    url: str = ""
    description: str = ""


@dataclass
class SectorInfo:
    """업종 분류 정보.

    Attributes
    ----------
    sectorCode : str
        업종 코드.
    sectorName : str
        업종명.
    industryCode : str
        산업 코드.
    industryName : str
        산업명.
    market : str
        시장 구분 (KOSPI/KOSDAQ).
    source : str
        데이터 출처.
    """

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
    """공매도 잔고/거래 데이터.

    Attributes
    ----------
    date : str
        기준일 (YYYY-MM-DD).
    shortVolume : int
        공매도 거래량 (주).
    shortAmount : int
        공매도 거래대금 (원).
    totalVolume : int
        전체 거래량 (주).
    shortRatio : float
        공매도 비중 (%).
    balance : int
        공매도 잔고 수량 (주).
    balanceRatio : float
        공매도 잔고 비율 (%).
    source : str
        데이터 출처.
    """

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
    """내부자(임원/주요주주) 주식 거래.

    Attributes
    ----------
    date : str
        거래일 (YYYY-MM-DD).
    name : str
        거래자 이름.
    position : str
        직위/관계.
    tradeType : str
        거래 유형 (취득/처분/장내매수/장내매도).
    changeShares : int
        변동 주식수 (주).
    afterShares : int
        변동 후 보유 주식수 (주).
    reason : str
        변동 사유.
    source : str
        데이터 출처.
    """

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
    """5% 이상 대량보유 주주.

    Attributes
    ----------
    holderName : str
        보유자 이름.
    shares : int
        보유 주식수 (주).
    ratio : float
        보유비율 (%).
    changeDate : str
        변동일 (YYYY-MM-DD).
    changeType : str
        변동 유형 (취득/처분/변동).
    source : str
        데이터 출처.
    """

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
    """기관/외국인 지분 보유.

    Attributes
    ----------
    holderName : str
        보유 주체명 (예: "외국인 합계").
    shares : int
        보유 주식수 (주).
    ratio : float
        보유비율 (%).
    value : float
        보유금액 (원).
    changeShares : int
        변동수량 (주).
    source : str
        데이터 출처.
    """

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
    """애널리스트 등급 변경.

    Attributes
    ----------
    date : str
        변경일 (YYYY-MM-DD).
    firm : str
        증권사/리서치 하우스.
    toGrade : str
        변경 후 등급.
    fromGrade : str
        변경 전 등급.
    action : str
        변경 유형 (upgrade/downgrade/init/maintain/reiterated).
    source : str
        데이터 출처.
    """

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
    """도메인 1개의 수집 결과 — 병렬 수집 시 반환 단위.

    Attributes
    ----------
    domain : str
        소스 도메인 이름.
    price : PriceSnapshot | None
        주가 스냅샷.
    flow : FlowData | None
        투자자별 수급.
    sector_per : float | None
        업종 평균 PER (배).
    sectorInfo : SectorInfo | None
        업종 분류 정보.
    insiderTrades : list[InsiderTrade]
        내부자 거래 리스트.
    shortSelling : ShortSellingData | None
        공매도 데이터.
    error : str | None
        오류 메시지. 정상이면 None.
    """

    domain: str = ""
    price: PriceSnapshot | None = None
    flow: FlowData | None = None
    sector_per: float | None = None
    sectorInfo: SectorInfo | None = None
    insiderTrades: list[InsiderTrade] = field(default_factory=list)
    shortSelling: ShortSellingData | None = None
    error: str | None = None

    @property
    def hasData(self) -> bool:
        """분석에 넘길 실제 값이 하나라도 있는지 판정한다.

        Returns:
            가격·수급·업종·내부자·공매도 값 중 하나라도 있으면 ``True``.

        Requires:
            없음.

        Raises:
            없음.

        Example:
            >>> GatherResult(sector_per=0.0).hasData
            True
        """
        return any(
            (
                self.price is not None,
                self.flow is not None,
                self.sector_per is not None,
                self.sectorInfo is not None,
                bool(self.insiderTrades),
                self.shortSelling is not None,
            )
        )


@dataclass
class GatherSnapshot:
    """전체 병렬 수집 통합 결과."""

    stockCode: str = ""
    results: dict[str, GatherResult] = field(default_factory=dict)
    collected_at: str = ""
    _news: list[NewsItem] = field(default_factory=list)
    _sectorInfo: SectorInfo | None = None
    _insiderTrades: list[InsiderTrade] = field(default_factory=list)
    _shortSelling: ShortSellingData | None = None
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def price(self) -> PriceSnapshot | None:
        """첫 번째 가용 주가.

        Capabilities: results dict iterate → 첫 r.price not None 반환.
        AIContext: gather.collect 결과의 사용자-friendly accessor — multi-source 통합.
        Guide: results dict 순서 = chain 순서. 첫 성공 source 가 우선.
        When: gather.collect 후 단일 price 만 필요 시.
        How: ``for r in results.values(): if r.price: return r.price``.

        Returns
        -------
        PriceSnapshot | None
            수집된 소스 중 첫 번째 유효한 주가 스냅샷. 없으면 None.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` dict 의 ``GatherResult.price`` 필드 가용.

        Example
        -------
        >>> snap.price

        See Also
        --------
        flow · sectorInfo · insiderTrades : 동행 accessor.
        toMarketSnapshot : flat 변환.
        """
        for r in self.results.values():
            if r.price:
                return r.price
        return None

    @property
    def flow(self) -> FlowData | None:
        """수집된 수급 데이터 반환.

        Capabilities: results dict iterate → 첫 r.flow not None 반환.
        AIContext: gather.collect 결과의 flow accessor — multi-source 통합.
        Guide: results dict 순서 = chain 순서. 첫 성공 source.
        When: gather.collect 후 단일 flow 만 필요 시.
        How: ``for r in results.values(): if r.flow: return r.flow``.

        Returns
        -------
        FlowData | None
            첫 번째 유효한 수급 데이터. 없으면 None.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` 의 ``GatherResult.flow`` 필드 가용.

        Example
        -------
        >>> snap.flow

        See Also
        --------
        price : 가격 동행 accessor.
        toMarketSnapshot : flat 변환.
        """
        for r in self.results.values():
            if r.flow:
                return r.flow
        return None

    @property
    def news(self) -> list[NewsItem]:
        """수집된 뉴스 항목.

        Capabilities: ``_news`` private 필드 직접 반환.
        AIContext: gather.collect 결과의 news accessor.
        Guide: 외부 본문은 untrusted external — 마커 wrap 필요.
        When: 종목 관련 뉴스 list 접근 시.
        How: ``return self._news``.

        Returns
        -------
        list[NewsItem]
            뉴스 항목 리스트.

        Raises
        ------
        없음.

        Requires
        --------
        ``_news`` private 필드.

        Example
        -------
        >>> snap.news

        See Also
        --------
        formatting.wrapExternalInResult : untrusted 마커 wrap.
        """
        return self._news

    @property
    def sectorInfo(self) -> SectorInfo | None:
        """수집된 업종 분류.

        Capabilities: results dict iterate → 첫 r.sectorInfo not None 반환, fallback to private.
        AIContext: gather.collect 결과의 sector accessor — peer matching 진입.
        Guide: source 별 sectorInfo 가 다를 수 있음. 첫 성공만 반환.
        When: 종목의 업종 분류 단건 조회 시.
        How: results iterate + ``_sectorInfo`` private fallback.

        Returns
        -------
        SectorInfo | None
            업종 분류 정보. 없으면 None.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` dict 또는 ``_sectorInfo`` 필드 가용.

        Example
        -------
        >>> snap.sectorInfo

        See Also
        --------
        domains/krx.fetchSectorInfo : 실제 sectorInfo 추출 backend.
        """
        for r in self.results.values():
            if r.sectorInfo:
                return r.sectorInfo
        return self._sectorInfo

    @property
    def insiderTrades(self) -> list[InsiderTrade]:
        """수집된 내부자 거래.

        Capabilities: results dict iterate → 첫 r.insiderTrades not empty 반환, fallback to private.
        AIContext: gather.collect 결과의 insider accessor — informed trading 분석.
        Guide: source 별 다를 수 있음. 첫 non-empty 만.
        When: 단일 종목의 내부자 거래 list 접근 시.
        How: results iterate + ``_insiderTrades`` private fallback.

        Returns
        -------
        list[InsiderTrade]
            내부자 거래 리스트.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` 또는 ``_insiderTrades`` 필드.

        Example
        -------
        >>> snap.insiderTrades

        See Also
        --------
        sources/insider.fetchInsiderTrading : 실제 backend.
        accessors.iterInsiderTrades : streaming 동행.
        """
        for r in self.results.values():
            if r.insiderTrades:
                return r.insiderTrades
        return self._insiderTrades

    @property
    def shortSelling(self) -> ShortSellingData | None:
        """수집된 공매도 데이터.

        Capabilities: results dict iterate → 첫 r.shortSelling not None, fallback to private.
        AIContext: gather.collect 결과의 short-selling accessor — bearish signal 분석.
        Guide: KR 한정. 외 시장 None.
        When: 단일 종목 공매도 상태 조회 시.
        How: results iterate + ``_shortSelling`` private fallback.

        Returns
        -------
        ShortSellingData | None
            공매도 데이터. 없으면 None.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` 또는 ``_shortSelling`` 필드.

        Example
        -------
        >>> snap.shortSelling

        See Also
        --------
        domains/krx.fetchShortSelling : 실제 KR backend (있을 경우).
        """
        for r in self.results.values():
            if r.shortSelling:
                return r.shortSelling
        return self._shortSelling

    @property
    def sourcesAvailable(self) -> list[str]:
        """실제 데이터를 하나라도 제공한 소스 목록.

        Capabilities: results dict filter → 실제 값이 있는 source name list.
        AIContext: gather.collect 의 partial success 추적 — 어느 source 가 살아있나.
        Guide: 일부 축이 실패해 error가 있어도 다른 실제 값이 있으면 포함. sourcesFailed와 중복 가능.
        When: collect 결과의 source-level diagnostic 필요 시.
        How: ``[d for d, r in results.items() if r.hasData]``.

        Returns
        -------
        list[str]
            실제 값을 하나라도 제공한 소스 이름 리스트.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` dict 의 ``GatherResult.error`` 필드.

        Example
        -------
        >>> snap.sourcesAvailable

        See Also
        --------
        sourcesFailed : 전체 또는 일부 축이 실패한 소스 list.
        """
        return [d for d, r in self.results.items() if r.hasData]

    @property
    def sourcesFailed(self) -> list[str]:
        """오류가 발생한 소스 목록.

        Capabilities: results dict filter → error not None 인 source name list.
        AIContext: partial failure 진단 — telemetry 신호로 emit 가능한 source list.
        Guide: error 가 None 아닌 것만. sourcesAvailable 의 짝.
        When: collect 결과 진단 / 실패 분석 시.
        How: ``[d for d, r in results.items() if r.error is not None]``.

        Returns
        -------
        list[str]
            오류가 발생한 소스 이름 리스트.

        Raises
        ------
        없음.

        Requires
        --------
        ``results`` dict.

        Example
        -------
        >>> snap.sourcesFailed

        See Also
        --------
        sourcesAvailable : 짝.
        """
        return [d for d, r in self.results.items() if r.error is not None]

    def toMarketSnapshot(self) -> MarketSnapshot:
        """Analyst 엔진 호환 flat 스냅샷으로 변환.

        Capabilities: GatherSnapshot multi-source 결과 → flat MarketSnapshot dataclass.
        AIContext: analysis/credit 엔진 진입 시 데이터 통합 변환 SSOT.
        Guide: price 부재 시 빈 multiples / None range — graceful (예외 없음).
        When: gather.collect 결과를 analysis/credit 가 소비할 때.
        How: self.price/flow 추출 → multiples dict + 52w range → MarketSnapshot.

        Returns
        -------
        MarketSnapshot
            현재가, 컨센서스, 멀티플, 수급, 52주 범위를 포함한 flat 구조.

        Raises
        ------
        없음
            price 부재면 빈 multiples/None price_range 로 graceful 반환.

        Requires
        --------
        ``MarketSnapshot`` 타입 정의 가용.

        Example
        -------
        >>> snap.toMarketSnapshot()

        See Also
        --------
        analysis/* : 본 함수 결과의 caller.
        price · flow : 본 함수가 호출하는 accessor.
        """
        price = self.price
        flow = self.flow

        multiples: dict[str, float] = {}
        price_range: tuple[float, float] | None = None
        currentPrice = 0.0

        if price:
            currentPrice = price.current
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
            stockCode=self.stockCode,
            currentPrice=currentPrice,
            multiples=multiples,
            supply_demand=supply_demand,
            price_range_52w=price_range,
            collected_at=self.collected_at,
            sourcesAvailable=self.sourcesAvailable,
            sourcesFailed=self.sourcesFailed,
        )

    def __repr__(self) -> str:
        lines = [f"[GatherSnapshot — {self.stockCode}]"]
        if self.price:
            lines.append(f"  {self.price}")
        if self.flow:
            lines.append(f"  {self.flow}")
        lines.append(f"  소스: {', '.join(self.sourcesAvailable)}")
        if self.sourcesFailed:
            lines.append(f"  실패: {', '.join(self.sourcesFailed)}")
        return "\n".join(lines)


# ══════════════════════════════════════
# Analyst 호환 스냅샷 (flat 구조)
# ══════════════════════════════════════


# PeerData / MarketSnapshot 은 L0 (core/types) 로 강등됨 (F4 — 정공법 A — Hierarchy).
# gather.types 는 SSOT 위치 (core) 에서 import. 모듈 namespace 호환 노출.
from dartlab.core.types import MarketSnapshot, PeerData  # noqa: F401, E402

# ══════════════════════════════════════
# 예외
# ══════════════════════════════════════


class GatherError(Exception):
    """Gather 엔진 기본 예외."""


class SourceUnavailableError(GatherError):
    """소스 접근 불가."""


def isOptionalSourceError(exc: BaseException) -> bool:
    """OS별 네트워크 예외 포장 차이를 선택적 source 실패로 정규화한다."""
    if isinstance(exc, BaseExceptionGroup):
        return bool(exc.exceptions) and all(isOptionalSourceError(child) for child in exc.exceptions)
    if isinstance(exc, (ImportError, OSError, RuntimeError, AttributeError, GatherError)):
        return True
    try:
        import httpx
    except ImportError:
        return False
    return isinstance(exc, httpx.HTTPError)


class SourceAttemptsExhaustedError(SourceUnavailableError):
    """Fallback source가 모두 실패했음을 원인별로 보존하는 예외.

    Parameters
    ----------
    operation : str
        실패한 수집 작업 이름.
    attempts : Iterable[tuple[str, Exception]]
        시도한 source 이름과 해당 실패 원인의 순서쌍.

    Attributes
    ----------
    operation : str
        실패한 수집 작업 이름.
    attempts : tuple[tuple[str, Exception], ...]
        fallback 순서대로 보존한 source별 실패 원인.
    failures : Mapping[str, Exception]
        source 이름으로 실패 원인을 조회하는 읽기 전용 매핑.
    """

    def __init__(self, operation: str, attempts: Iterable[tuple[str, Exception]]) -> None:
        self.operation = operation
        self.attempts = tuple(attempts)
        self.failures: Mapping[str, Exception] = MappingProxyType(dict(self.attempts))

        if self.attempts:
            detail = ", ".join(f"{source}={type(exc).__name__}" for source, exc in self.attempts)
        else:
            detail = "설정된 source 없음"
        super().__init__(f"{operation} fallback source가 모두 실패했습니다 ({detail})")


class RateLimitExceededError(GatherError):
    """Rate limit 초과."""


class CircuitOpenError(SourceUnavailableError):
    """Circuit breaker open — 소스 일시 차단."""
