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
        CatalogEntry("BAMLC0A0CM", "IG 스프레드", "rates", "Daily", "Percent", "ICE BofA 투자등급 OAS"),
        CatalogEntry("DFII10", "실질금리 10년", "rates", "Daily", "Percent", "10년 TIPS 실질금리"),
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
    "ism": [
        CatalogEntry("NAPM", "ISM PMI", "ism", "Monthly", "Index", "ISM 제조업 PMI (구 NAPM)"),
        CatalogEntry("NAPMNOI", "ISM 신규수주", "ism", "Monthly", "Index", "ISM 제조업 신규수주 지수"),
        CatalogEntry("NAPMII", "ISM 재고", "ism", "Monthly", "Index", "ISM 제조업 재고 지수"),
        CatalogEntry("NEWORDER", "제조업 신규수주", "ism", "Monthly", "Millions of Dollars", "제조업 신규수주"),
        CatalogEntry("BUSINV", "총사업재고", "ism", "Monthly", "Millions of Dollars", "총 사업 재고"),
        CatalogEntry("AMTMNO", "제조업 총수주", "ism", "Monthly", "Millions of Dollars", "제조업 총 신규수주"),
    ],
    "lei": [
        CatalogEntry("AWHMAN", "제조업 주당근로시간", "lei", "Monthly", "Hours", "제조업 평균 주당 근로시간"),
        CatalogEntry("ACOGNO", "소비재 신규수주", "lei", "Monthly", "Millions of Dollars", "비국방 소비재 신규수주"),
        CatalogEntry(
            "ACDGNO", "비국방자본재 신규수주", "lei", "Monthly", "Millions of Dollars", "비국방 자본재 신규수주 (항공기 제외)"
        ),
        CatalogEntry("M2REAL", "실질 M2", "lei", "Monthly", "Billions of 1982-84 Dollars", "실질 M2 통화량"),
        CatalogEntry(
            "A191RL1Q225SBEA", "실질GDP 성장률", "lei", "Quarterly", "Percent", "실질 GDP 성장률 (QoQ SAAR)"
        ),
    ],
    "credit": [
        CatalogEntry(
            "TCMDO", "총신용시장부채", "credit", "Quarterly", "Billions of Dollars", "비금융부문 총 신용시장 부채"
        ),
        CatalogEntry("GFDEBTN", "연방정부 부채", "credit", "Quarterly", "Millions of Dollars", "연방정부 총 공공부채"),
        CatalogEntry("TDSP", "부채서비스비율", "credit", "Quarterly", "Percent", "가계 부채 서비스 비율"),
        CatalogEntry(
            "DRSFRMACBS", "부실대출비율", "credit", "Quarterly", "Percent", "상업은행 부실대출 비율"
        ),
    ],
    "conditions": [
        CatalogEntry("NFCI", "시카고Fed NFCI", "conditions", "Weekly", "Index", "시카고Fed 금융상태지수"),
        CatalogEntry("ANFCI", "조정 NFCI", "conditions", "Weekly", "Index", "시카고Fed 조정 금융상태지수"),
        CatalogEntry("WEI", "주간경제지수", "conditions", "Weekly", "Percent", "NY Fed 주간 경제지수 (GDP 성장률 스케일)"),
        CatalogEntry("SAHMREALTIME", "Sahm Rule", "conditions", "Monthly", "Percentage Points", "Sahm 실시간 침체지표"),
    ],
    "commodities": [
        CatalogEntry("PCOPPUSDM", "구리 가격", "commodities", "Monthly", "U.S. Dollars per Metric Ton", "구리 가격 (월간)"),
    ],
    "yieldcurve": [
        CatalogEntry("DGS1", "국채 1년", "yieldcurve", "Daily", "Percent", "미국 1년 국채 수익률"),
        CatalogEntry("DGS3", "국채 3년", "yieldcurve", "Daily", "Percent", "미국 3년 국채 수익률"),
        CatalogEntry("DGS5", "국채 5년", "yieldcurve", "Daily", "Percent", "미국 5년 국채 수익률"),
        CatalogEntry("DGS7", "국채 7년", "yieldcurve", "Daily", "Percent", "미국 7년 국채 수익률"),
        CatalogEntry("DGS20", "국채 20년", "yieldcurve", "Daily", "Percent", "미국 20년 국채 수익률"),
    ],
    "flowoffunds": [
        CatalogEntry("W987RC1Q027SBEA", "민간 저축", "flowoffunds", "Quarterly", "Billions of Dollars", "민간 부문 총저축"),
        CatalogEntry("GPDI", "민간 총투자", "flowoffunds", "Quarterly", "Billions of Dollars", "민간 국내총투자"),
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
