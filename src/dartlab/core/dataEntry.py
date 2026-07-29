"""DataEntry 타입과 provider-import-free 내장 metadata 카탈로그 SSOT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DataEntry:
    """데이터 소스 메타데이터 — registry의 최소 단위.

    category별 역할:
    - finance: 시계열 재무제표 (annual.IS, timeseries.BS 등)
    - report: XBRL 정규화 재무제표 (BS, IS, CF)
    - notes: K-IFRS 주석 (notes.receivables 등)
    - raw: 원본 parquet (rawFinance, rawReport)
    - analysis: L2 분석 엔진 (ratios, insight, sector, rank)
    """

    name: str
    label: str
    category: str
    dataType: str
    description: str

    modulePath: str | None = None
    funcName: str | None = None
    extractor: Any = None

    apiType: str | None = None

    notesDispatch: tuple[str, str] | None = None

    aliases: tuple[str, ...] = ()

    requires: str | None = None
    unit: str = "백만원"


_BUILTIN_ENTRIES: tuple[DataEntry, ...] = (
    # finance — 시계열 재무제표
    DataEntry(
        name="annual.IS",
        label="손익계산서(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 손익계산서 시계열. 매출액, 영업이익, 순이익 등 전체 계정.",
        requires="finance",
    ),
    DataEntry(
        name="annual.BS",
        label="재무상태표(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 재무상태표 시계열. 자산, 부채, 자본 전체 계정.",
        requires="finance",
    ),
    DataEntry(
        name="annual.CF",
        label="현금흐름표(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 현금흐름표 시계열. 영업/투자/재무활동 현금흐름.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.IS",
        label="손익계산서(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 손익계산서 standalone 시계열.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.BS",
        label="재무상태표(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 재무상태표 시점잔액 시계열.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.CF",
        label="현금흐름표(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 현금흐름표 standalone 시계열.",
        requires="finance",
    ),
    # report — finance XBRL 정규화 재무제표
    DataEntry(
        name="BS",
        label="재무상태표",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 재무상태표. finance XBRL 정규화(snakeId) 기반, 회사간 비교 가능.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
    DataEntry(
        name="IS",
        label="손익계산서",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 손익계산서. finance XBRL 정규화 기반. 매출액, 영업이익, 순이익 등 전체 계정 포함.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
    DataEntry(
        name="CF",
        label="현금흐름표",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 현금흐름표. finance XBRL 정규화 기반. 영업/투자/재무활동 현금흐름.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
    # notes — K-IFRS 주석
    DataEntry(
        name="notes.receivables",
        label="매출채권",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 매출채권 주석. 채권 잔액 및 대손충당금 내역.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "매출채권"),
        requires="panel",
    ),
    DataEntry(
        name="notes.inventory",
        label="재고자산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 재고자산 주석. 원재료/재공품/제품 내역별 금액.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "재고자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.tangibleAsset",
        label="유형자산(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 유형자산 변동 주석. 토지, 건물, 기계 등 항목별 변동.",
        extractor=lambda result: result.movementDf,
        notesDispatch=("tangibleAsset", "유형자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.intangibleAsset",
        label="무형자산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 무형자산 주석. 영업권, 개발비 등 항목별 변동.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "무형자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.investmentProperty",
        label="투자부동산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 투자부동산 주석. 공정가치 및 변동 내역.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "투자부동산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.affiliates",
        label="관계기업(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 관계기업 투자 주석. 지분법 적용 내역.",
        extractor=lambda result: result.movementDf,
        notesDispatch=("affiliate", "관계기업"),
        requires="panel",
    ),
    DataEntry(
        name="notes.borrowings",
        label="차입금",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 차입금 주석. 단기/장기 차입 잔액 및 이자율.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "차입금"),
        requires="panel",
    ),
    DataEntry(
        name="notes.provisions",
        label="충당부채",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 충당부채 주석. 판매보증, 소송, 복구 등.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "충당부채"),
        requires="panel",
    ),
    DataEntry(
        name="notes.eps",
        label="주당이익",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 주당이익 주석. 기본/희석 EPS 계산 내역.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "주당이익"),
        requires="panel",
    ),
    DataEntry(
        name="notes.lease",
        label="리스",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 리스 주석. 사용권자산, 리스부채 내역.",
        extractor=lambda result: result.tableDf,
        notesDispatch=("notesDetail", "리스"),
        requires="panel",
    ),
    DataEntry(
        name="notes.segments",
        label="부문정보(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 부문정보 주석. 사업부문별 상세 데이터.",
        extractor=lambda result: result.revenue,
        notesDispatch=("segments", "부문정보"),
        requires="panel",
    ),
    DataEntry(
        name="notes.costByNature",
        label="비용의성격별분류(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 비용의 성격별 분류 주석.",
        extractor=lambda result: result.timeSeries,
        notesDispatch=("costByNature", "비용의성격별분류"),
        requires="panel",
    ),
    # raw — 원본 parquet
    DataEntry(
        name="rawFinance",
        label="XBRL 원본",
        category="raw",
        dataType="dataframe",
        description="XBRL 재무제표 원본 parquet. 매핑/정규화 전 원본 데이터.",
        requires="finance",
    ),
    DataEntry(
        name="rawReport",
        label="보고서 원본",
        category="raw",
        dataType="dataframe",
        description="정기보고서 API 원본 parquet. 파싱 전 원본 데이터.",
        requires="report",
    ),
    # analysis — L2 분석 엔진 metadata
    DataEntry(
        name="ratios",
        label="재무비율",
        category="analysis",
        dataType="ratios",
        description="financeEngine이 자동계산한 수익성·안정성·밸류에이션 비율.",
        requires="finance",
        unit="%",
    ),
    DataEntry(
        name="insight",
        label="인사이트",
        category="analysis",
        dataType="custom",
        description="7영역 A~F 등급 분석 (실적, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회).",
        requires="finance",
    ),
    DataEntry(
        name="sector",
        label="섹터분류",
        category="analysis",
        dataType="custom",
        description="WICS 11대 섹터 분류. 대분류/중분류 + 섹터별 파라미터.",
    ),
    DataEntry(
        name="rank",
        label="시장순위",
        category="analysis",
        dataType="custom",
        description="전체 시장 및 섹터 내 매출/자산/성장률 순위.",
        requires="finance",
    ),
    DataEntry(
        name="keywordTrend",
        label="키워드 트렌드",
        category="analysis",
        dataType="dataframe",
        description="공시 텍스트 키워드 빈도 추이 (topic × period × keyword). 54개 내장 키워드 또는 사용자 지정.",
        requires="panel",
    ),
    DataEntry(
        name="news",
        label="뉴스",
        category="analysis",
        dataType="dataframe",
        description="최근 뉴스 수집 (KR: Google News 한국어, US: Google News 영어). 날짜/제목/출처/URL.",
    ),
)


__all__ = ["DataEntry"]
