"""gather entry — axis registry · alias · 시장지수 fetch · 축 정규화.

GatherEntry 클래스 (main.py) 가 의존하는 공유 데이터 + 헬퍼.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import polars as pl

# targetType — gather contract 명세 (axis 별 target 의 의미).
#   stockCode  : 종목코드/티커 (예: "005930", "AAPL")
#   columnName : OHLCV 또는 보조지표 컬럼 명 (예: "close", "rsi14")
#   indicator  : 거시지표 코드 (예: "CPI", "FEDFUNDS")
#   keyword    : 검색어 (자유 문자열)
#   none       : target 안 받음
TargetType = Literal["stockCode", "columnName", "indicator", "keyword", "rceptNo", "none"]


@dataclass(frozen=True)
class GatherAxisEntry:
    """gather 축 메타데이터.

    targetType 은 axis 가 받는 target 의 의미를 명시 — test_gatherAxisContract 가
    이 메타데이터로 axis-별 적절 target 을 dispatch.

    hidden=True 인 axis 는 _guide() / __repr__ / 공개 가이드 출력에서 제외.
    내부 구현·테스트는 가능 (데이터 미준비/베타 axis 용).
    """

    label: str
    description: str
    example: str
    targetRequired: bool = True
    targetType: TargetType = "stockCode"
    hidden: bool = False


AXIS_REGISTRY: dict[str, GatherAxisEntry] = {
    "price": GatherAxisEntry(
        label="주가",
        description=(
            "OHLCV 시계열 (수정주가). "
            "KR: Naver, US: Yahoo. 기본 1년, 최대 6000거래일. "
            "시장 지수 (KOSPI/KOSDAQ/KPI200) 도 자동 인식."
        ),
        example='gather("price", "005930") / gather("price", "AAPL")',
        targetType="stockCode",
    ),
    "flow": GatherAxisEntry(
        label="수급",
        description="외국인/기관 순매수 시계열 (KR 전용, Naver).",
        example='gather("flow", "005930") / gather("flow", targets=["005930", "000660"], parallel=2)',
        targetType="stockCode",
    ),
    "macro": GatherAxisEntry(
        label="거시지표",
        description=(
            "거시지표 시계열. KR(ECOS)/US(FRED) 는 HF 벌크 (키 불필요, apiKey 명시 시 직접 API), "
            "EU(ECB)·GLOBAL(BIS/OECD/IMF) 는 live SDMX (키 불필요). ID prefix 로 시장 자동 감지: "
            "ECOS/FRED 코드 → KR/US, ECB_ → EU, BIS_/OECD_/IMF_ → GLOBAL."
        ),
        example='gather("macro", "CPI") / gather("macro", "FEDFUNDS") / gather("macro", "ECB_HICP") / gather("macro", "IMF_OIL_BRENT")',
        targetRequired=False,
        targetType="indicator",
    ),
    "news": GatherAxisEntry(
        label="뉴스",
        description="Google News RSS 뉴스 수집 (기본 최근 30일).",
        example='gather("news", "삼성전자", days=7)',
        targetType="keyword",
    ),
    "sector": GatherAxisEntry(
        label="업종",
        description="업종 분류 (KR KIND+Naver / US sectorCode).",
        example='gather("sector", "005930")',
        targetType="stockCode",
    ),
    "insider": GatherAxisEntry(
        label="내부자거래",
        description="내부자 (임원·주요주주) 거래 (KR DART · DART_API_KEY 필요).",
        example='gather("insider", "005930")',
        targetType="stockCode",
    ),
    "ownership": GatherAxisEntry(
        label="지분 보유",
        description="기관/외국인 지분 보유 현황 (KR Naver).",
        example='gather("ownership", "005930")',
        targetType="stockCode",
    ),
    "peers": GatherAxisEntry(
        label="피어",
        description="동종업종 피어 종목 목록 (종목코드+시총). KR: KRX/네이버",
        example='gather("peers", "005930")',
        targetType="stockCode",
    ),
    "krx": GatherAxisEntry(
        label="KRX 회사별 시계열",
        description=(
            "KOSPI/KOSDAQ 전종목 wide pivot — 행=stockCode+corpName, 열=일자. "
            "target (positional) 으로 raw OHLCV (close/open/high/low/volume/marketCap/...) "
            "또는 보조지표 (rsi14/ma20/ema60/macd/atr14/obv/...) 28+ 디스패치. "
            "target='raw' 면 long (KRX 원본 컬럼). "
            "apiKey 없음 (기본): HF SSOT. apiKey 명시: KRX OpenAPI 직접. 환경변수 자동 read X."
        ),
        example='gather("krx", "close", start=, end=) / gather("krx", "rsi14", start=, end=) / gather("krx", "marketCap", date=)',
        targetRequired=False,
        targetType="columnName",
    ),
    # 공개 축 (hidden=False) — HF SSOT 일별 지수 패키지. 정식 표기 krxIndex
    # (camelCase, dartlab 표준 — 모듈/함수명과 일관). 직접 KRX idx OpenAPI 경로는
    # sto 종목 키와 분리된 idx 카테고리 권한을 별도 신청해야 한다.
    "krxIndex": GatherAxisEntry(
        label="KRX 지수 일별 매매현황 (시장군별 전체 지수 패키지)",
        description=(
            "KRX/KOSPI/KOSDAQ 시장군의 모든 지수 (종합/200/100/섹터/스타일/사이즈/ESG/테마) "
            "OHLCV + 거래량 + 시가총액. target=close/open/high/low/volume/marketCap/raw. "
            "indexFilter=[지수명] 으로 특정 지수 (예: 코스피 200 + 보조지표 자동). "
            "apiKey 없음 (기본): HF SSOT. apiKey 명시: KRX idx OpenAPI 직접. "
            "직접 호출 시 idx 카테고리 권한 별도 신청 (sto 종목 키와 분리)."
        ),
        example='gather("krxIndex", "close", market="KOSPI", start=, end=)',
        targetRequired=False,
        targetType="columnName",
    ),
    "narrative": GatherAxisEntry(
        label="뉴스 내러티브 archive",
        description=(
            "Phase A/B/C/D 통합 archive (RSS + GDELT) 진입. "
            "target 분기: None/'raw'=원본 archive, 'pulse'=date×topic 격자, "
            "'score'=12 번째 macro 축 dict, 'topics'=top topic 랭킹, "
            "6자리 코드=종목명 keyword 필터, 그 외 문자열=키워드 필터. "
            "days kwarg 기본 30 (start/end 미명시 시 today-days~today). "
            "asof PIT-safe."
        ),
        example='gather("narrative", market="KR", days=30) / gather("narrative", "score") / gather("narrative", "005930", days=30)',
        targetRequired=False,
        targetType="keyword",
    ),
    "research": GatherAxisEntry(
        label="증권사 리서치",
        description=(
            "증권사 공개 게시판 리서치 *메타 인덱스* (제목·발간일·종목·증권사·구분·투자의견·저자). "
            "본문은 호스팅 안 하고 url 로 원본 링크아웃(링크=합법). 서버렌더 5개사 "
            "(미래에셋·NH·유안타·한양·부국). 위치 target: 6자리=종목코드 필터, 그 외=제목 검색. "
            "query/broker/reportType/start/end kwarg 추가 필터. 절대 매수/매도 신호로 재가공 금지(메타 사실만)."
        ),
        example=(
            'gather("research") / gather("research", "005930") / gather("research", query="2차전지", broker="hanyang")'
        ),
        targetRequired=False,
        targetType="keyword",
    ),
    "theme": GatherAxisEntry(
        label="테마 분류 (KR, 로컬 개인용)",
        description=(
            "네이버 금융 테마 분류 (KR). 기본(target 없음)은 전 테마(약 280)를 개별 수집해 하나의 "
            "long DataFrame(themeNo/themeName/stockCode/stockName/reason)으로 결합. 'list'=테마 목록만, "
            "테마명/번호=해당 테마만 필터. ⚠ 네이버 편집저작물 — 로컬 개인 분석은 무방하나 재배포·공개"
            "(HF 적재·서비스 배포·제3자 공개)는 DB권(저작권법 제4장)·저작권 문제 발생 가능."
        ),
        example='gather("theme") / gather("theme", "list") / gather("theme", "2차전지")',
        targetRequired=False,
        targetType="keyword",
    ),
    "dartDoc": GatherAxisEntry(
        label="DART 공시 원문",
        description=(
            "14자리 rcept_no 만으로 DART 공시 viewer 의 원문 본문 fetch (무인증). "
            "공시 인덱스 페이지에서 sub-doc 목차를 받고 각 섹션 HTML 을 텍스트 "
            "(테이블 마크다운 보존) 로 변환. API key 불필요 — providers/dart/openapi "
            "(key 기반 OpenDART) 와 분리된 viewer 단건 fetch 진입점."
        ),
        example='gather("dartDoc", "20240315000123")',
        targetType="rceptNo",
        hidden=True,
    ),
    "calendar": GatherAxisEntry(
        label="catalyst 일정 (폐기 → Company.calendar)",
        description=(
            "[0.10 폐기] gather('calendar') 는 ValueError 로 막힘 — gather→providers "
            "cycle 회피 위해 책임 분리. 다가오는 정기공시 due date 는 "
            "Company.calendar(horizonDays=30) 로 조회 (한국 fiscal cycle 가정 + "
            "DART disclosure 시계열에서 last 보고서 → next due). API 키: DART_API_KEY."
        ),
        example='Company("005930").calendar(horizonDays=30)  # gather("calendar") 는 0.10 폐기',
        targetType="stockCode",
        hidden=True,
    ),
}


# axis 별 필요한 API 키 — _guide() 와 test_gatherAxisContract 가 공통 소비.
# 값이 "불필요" 가 아니면 환경변수에 키가 설정돼야 axis 호출 가능.
API_KEY_INFO: dict[str, str] = {
    "price": "불필요",
    "flow": "불필요",
    "macro": "불필요 (기본 HF SSOT, apiKey 명시 시 ECOS/FRED 직접 호출)",
    "news": "불필요",
    "sector": "불필요",
    "insider": "DART_API_KEY",
    "ownership": "불필요",
    "peers": "불필요",
    "krx": "불필요 (기본 HF SSOT, apiKey 명시 시 KRX OpenAPI 직접 호출)",
    "krxIndex": "불필요 (기본 HF SSOT, apiKey 명시 시 KRX idx OpenAPI 직접 호출)",
    "narrative": "불필요 (Phase A/D HF + 로컬 archive)",
    "research": "불필요 (명시 6자리코드 무키, 제목→회사명 fallback 시 DART_API_KEY 로 커버리지↑)",
    "theme": "불필요 (네이버 직독·로컬 개인용 — 재배포 금지)",
    "dartDoc": "불필요 (viewer 무인증 단건 fetch)",
    "calendar": "DART_API_KEY (Company.disclosure 사용)",
}

AXIS_ALIASES: dict[str, str] = {
    "주가": "price",
    "수급": "flow",
    "거시": "macro",
    "매크로": "macro",
    "뉴스": "news",
    "업종": "sector",
    "내부자": "insider",
    "지분": "ownership",
    "피어": "peers",
    "동종업종": "peers",
    "테마": "theme",
    "일정": "calendar",
    "캘린더": "calendar",
    "내러티브": "narrative",
    "뉴스내러티브": "narrative",
    "뉴스심리": "narrative",
    "헤드라인": "narrative",
}


# 시장 지수 심볼 매핑 (네이버 차트 API 직접 수집).
# 정식 표기 = 네이버 fchart 가 받는 외부 API 심볼 (uppercase). 사용자는 정식 표기
# 또는 명시 한글 alias 만 사용한다. ``"kospi"`` 같은 case alias 는 인정하지 않음
# (consistency_no_alias 원칙 — silent case-insensitive lookup 은 alias).
INDEX_SYMBOLS: dict[str, str] = {
    # 정식 외부 API 심볼 (self-map — registry 등록 표시)
    "KOSPI": "KOSPI",
    "KOSDAQ": "KOSDAQ",
    "KPI200": "KPI200",
    # 명시 한글 alias
    "코스피": "KOSPI",
    "코스닥": "KOSDAQ",
    "코스피200": "KPI200",
}


def _fetchNaverIndex(symbol: str, limit: int = 500) -> pl.DataFrame:
    """네이버 차트 API로 시장 지수 OHLCV 수집.

    Parameters
    ----------
    symbol : str
        지수 심볼 (예: ``"KOSPI"``, ``"KOSDAQ"``, ``"KPI200"``).
    limit : int
        요청 거래일 수 (일). 기본 500.

    Returns
    -------
    pl.DataFrame
        date : date — 거래일
        open : float — 시가 (포인트)
        high : float — 고가 (포인트)
        low : float — 저가 (포인트)
        close : float — 종가 (포인트)
        volume : int — 거래량 (주)
        데이터 없으면 빈 DataFrame.
    """
    import re

    import httpx

    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={symbol}&timeframe=day&count={limit}&requestType=0"
    r = httpx.get(url, timeout=15)
    items = re.findall(r'data="([^"]+)"', r.text)
    if not items:
        return pl.DataFrame()

    rows = []
    for item in items:
        parts = item.split("|")
        if len(parts) < 6:
            continue
        try:
            rows.append(
                {
                    "date": f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:8]}",
                    "open": float(parts[1]),
                    "high": float(parts[2]),
                    "low": float(parts[3]),
                    "close": float(parts[4]),
                    "volume": int(parts[5]),
                }
            )
        except (ValueError, IndexError):
            continue

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).with_columns(pl.col("date").str.to_date("%Y-%m-%d"))


def _resolveAxis(axis: str) -> str:
    """축 이름/한글 별칭 → 정규 키.

    consistency_no_alias 원칙: registry key 와 ``AXIS_ALIASES`` 의 명시적 한글 매핑만
    유효. case-insensitive lookup (예: ``"PRICE"`` → ``"price"``) 는 silent
    alias 라 인정하지 않는다 — 사용자가 정식 표기 (``"price"``, ``"krxIndex"``)
    를 정확히 쓰도록 유도.

    Parameters
    ----------
    axis : str
        축 정식 이름 (registry key) 또는 명시 한글 별칭 (예: ``"price"``,
        ``"주가"``, ``"krxIndex"``).

    Returns
    -------
    str
        정규 축 키 (예: ``"price"``, ``"krxIndex"``).

    Raises
    ------
    ValueError
        미등록 축 이름 또는 case 불일치 (``"Price"``, ``"krxindex"``) 일 때.
    """
    if axis in AXIS_REGISTRY:
        return axis
    if axis in AXIS_ALIASES:
        return AXIS_ALIASES[axis]
    available = ", ".join(sorted(AXIS_REGISTRY))
    raise ValueError(
        f"알 수 없는 gather 축: '{axis}'. 가용 축: {available}\n"
        f"  사용법: c.gather() 또는 dartlab.gather() 로 전체 축 가이드를 확인하세요."
    )
