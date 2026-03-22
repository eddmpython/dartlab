"""FRED 주요 경제지표 카탈로그 — 7개 그룹 × ~50개 시리즈.

사용자와 AI가 빠르게 핵심 지표에 접근하기 위한 사전 정의 카탈로그.
"""

from __future__ import annotations

import polars as pl

from .types import CatalogEntry

# ── 카탈로그 정의 ──

CATALOG: dict[str, list[CatalogEntry]] = {
    "growth": [
        CatalogEntry("GDP", "GDP (명목)", "growth", "Quarterly", "Billions of Dollars", "미국 명목 GDP"),
        CatalogEntry("GDPC1", "GDP (실질)", "growth", "Quarterly", "Billions of Chained 2017 Dollars", "미국 실질 GDP"),
        CatalogEntry("INDPRO", "산업생산지수", "growth", "Monthly", "Index 2017=100", "미국 산업생산지수"),
        CatalogEntry("PAYEMS", "비농업고용", "growth", "Monthly", "Thousands of Persons", "비농업 부문 총고용"),
        CatalogEntry("RSAFS", "소매판매", "growth", "Monthly", "Millions of Dollars", "소매 및 식품 서비스 판매"),
        CatalogEntry("DGORDER", "내구재주문", "growth", "Monthly", "Millions of Dollars", "제조업 내구재 신규 주문"),
        CatalogEntry("UMCSENT", "소비자심리", "growth", "Monthly", "Index 1966:Q1=100", "미시간대 소비자심리지수"),
    ],
    "inflation": [
        CatalogEntry(
            "CPIAUCSL", "CPI (전체)", "inflation", "Monthly", "Index 1982-84=100", "소비자물가지수 (도시 전체)"
        ),
        CatalogEntry("CPILFESL", "Core CPI", "inflation", "Monthly", "Index 1982-84=100", "식품·에너지 제외 CPI"),
        CatalogEntry("PCEPI", "PCE 물가", "inflation", "Monthly", "Index 2017=100", "개인소비지출 물가지수"),
        CatalogEntry("PCEPILFE", "Core PCE", "inflation", "Monthly", "Index 2017=100", "식품·에너지 제외 PCE"),
        CatalogEntry("T5YIE", "기대인플레이션 (5Y)", "inflation", "Daily", "Percent", "5년 손익분기 인플레이션율"),
        CatalogEntry("T10YIE", "기대인플레이션 (10Y)", "inflation", "Daily", "Percent", "10년 손익분기 인플레이션율"),
        CatalogEntry(
            "PPIFIS", "PPI (최종수요)", "inflation", "Monthly", "Index Nov 2009=100", "생산자물가지수 최종수요"
        ),
    ],
    "rates": [
        CatalogEntry("FEDFUNDS", "연방기금금리", "rates", "Monthly", "Percent", "실효 연방기금금리"),
        CatalogEntry("DFF", "연방기금금리 (일별)", "rates", "Daily", "Percent", "일별 실효 연방기금금리"),
        CatalogEntry("DGS2", "국채 2년", "rates", "Daily", "Percent", "미국 2년 국채 수익률"),
        CatalogEntry("DGS10", "국채 10년", "rates", "Daily", "Percent", "미국 10년 국채 수익률"),
        CatalogEntry("DGS30", "국채 30년", "rates", "Daily", "Percent", "미국 30년 국채 수익률"),
        CatalogEntry("T10Y2Y", "장단기 스프레드", "rates", "Daily", "Percent", "10년-2년 국채 수익률 스프레드"),
        CatalogEntry("T10Y3M", "10Y-3M 스프레드", "rates", "Daily", "Percent", "10년 국채-3개월 국채 스프레드"),
        CatalogEntry("BAMLH0A0HYM2", "하이일드 스프레드", "rates", "Daily", "Percent", "ICE BofA 하이일드 OAS"),
    ],
    "employment": [
        CatalogEntry("UNRATE", "실업률", "employment", "Monthly", "Percent", "미국 실업률 (U-3)"),
        CatalogEntry("U6RATE", "광의 실업률", "employment", "Monthly", "Percent", "미국 광의 실업률 (U-6)"),
        CatalogEntry("ICSA", "실업수당 청구", "employment", "Weekly", "Number", "신규 실업수당 청구건수"),
        CatalogEntry("JTSJOL", "구인건수", "employment", "Monthly", "Level in Thousands", "JOLTs 구인건수"),
        CatalogEntry("AWHAETP", "주당 근로시간", "employment", "Monthly", "Hours", "민간 비농업 주당 평균 근로시간"),
        CatalogEntry(
            "CES0500000003", "시간당 임금", "employment", "Monthly", "Dollars per Hour", "민간 비농업 시간당 평균 임금"
        ),
        CatalogEntry("CIVPART", "경제활동참가율", "employment", "Monthly", "Percent", "노동력 참가율"),
    ],
    "markets": [
        CatalogEntry("SP500", "S&P 500", "markets", "Daily", "Index", "S&P 500 지수"),
        CatalogEntry("NASDAQCOM", "NASDAQ", "markets", "Daily", "Index", "NASDAQ 종합지수"),
        CatalogEntry("DJIA", "다우존스", "markets", "Daily", "Index", "다우존스 산업평균지수"),
        CatalogEntry("VIXCLS", "VIX", "markets", "Daily", "Index", "CBOE 변동성 지수"),
        CatalogEntry("DTWEXBGS", "달러인덱스", "markets", "Daily", "Index Jan 2006=100", "무역가중 달러인덱스 (광의)"),
        CatalogEntry("DCOILWTICO", "WTI 유가", "markets", "Daily", "Dollars per Barrel", "WTI 원유 현물 가격"),
        CatalogEntry(
            "GOLDAMGBD228NLBM", "금 가격", "markets", "Daily", "U.S. Dollars per Troy Ounce", "런던 금 현물 (오전)"
        ),
    ],
    "housing": [
        CatalogEntry("HOUST", "주택착공", "housing", "Monthly", "Thousands of Units", "신규 주택착공 건수"),
        CatalogEntry("PERMIT", "건축허가", "housing", "Monthly", "Thousands of Units", "신규 건축허가 건수"),
        CatalogEntry(
            "CSUSHPISA",
            "케이스실러 주택가격",
            "housing",
            "Monthly",
            "Index Jan 2000=100",
            "S&P/케이스실러 20대도시 주택가격",
        ),
        CatalogEntry("MORTGAGE30US", "30년 모기지", "housing", "Weekly", "Percent", "30년 고정 모기지 금리"),
        CatalogEntry("MORTGAGE15US", "15년 모기지", "housing", "Weekly", "Percent", "15년 고정 모기지 금리"),
        CatalogEntry("EXHOSLUSM495S", "기존주택판매", "housing", "Monthly", "Number of Units", "기존 주택 판매건수"),
    ],
    "money": [
        CatalogEntry("M2SL", "M2 통화량", "money", "Monthly", "Billions of Dollars", "M2 통화공급"),
        CatalogEntry("BOGMBASE", "본원통화", "money", "Biweekly", "Billions of Dollars", "본원통화 (Monetary Base)"),
        CatalogEntry("WALCL", "연준 총자산", "money", "Weekly", "Millions of Dollars", "연준 대차대조표 총자산"),
        CatalogEntry("RRPONTSYD", "역레포", "money", "Daily", "Billions of Dollars", "오버나이트 역레포 잔액"),
        CatalogEntry(
            "TOTRESNS", "은행 지급준비금", "money", "Monthly", "Billions of Dollars", "예금기관 총 지급준비금"
        ),
    ],
}


# ── 헬퍼 ──


def get_groups() -> list[str]:
    """카탈로그 그룹 이름 목록."""
    return list(CATALOG.keys())


def get_group(name: str) -> list[CatalogEntry]:
    """그룹 내 시리즈 목록. 없으면 빈 리스트."""
    return CATALOG.get(name, [])


def get_group_ids(name: str) -> list[str]:
    """그룹 내 시리즈 ID 목록."""
    return [e.id for e in CATALOG.get(name, [])]


def get_all_ids() -> list[str]:
    """전체 카탈로그 시리즈 ID."""
    return [e.id for entries in CATALOG.values() for e in entries]


def get_all_entries() -> list[CatalogEntry]:
    """전체 카탈로그 엔트리."""
    return [e for entries in CATALOG.values() for e in entries]


def find_entry(series_id: str) -> CatalogEntry | None:
    """시리즈 ID로 카탈로그 엔트리 검색."""
    for entries in CATALOG.values():
        for e in entries:
            if e.id == series_id:
                return e
    return None


def to_dataframe(group: str | None = None) -> pl.DataFrame:
    """카탈로그 → Polars DataFrame.

    Args:
        group: 특정 그룹만. None이면 전체.
    """
    entries = get_group(group) if group else get_all_entries()
    if not entries:
        return pl.DataFrame(
            schema={
                "id": pl.Utf8,
                "label": pl.Utf8,
                "group": pl.Utf8,
                "frequency": pl.Utf8,
                "unit": pl.Utf8,
                "description": pl.Utf8,
            }
        )
    return pl.DataFrame(
        [
            {
                "id": e.id,
                "label": e.label,
                "group": e.group,
                "frequency": e.frequency,
                "unit": e.unit,
                "description": e.description,
            }
            for e in entries
        ]
    )
