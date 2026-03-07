"""종목 단위 통합 분석 클래스.

사용법::

    from dartlab import Company

    c = Company("005930")
    c.corpName                         # "삼성전자"
    c.dividend()                       # DividendResult | None
    c.statements(period="q")           # StatementsResult (분기)
"""

from __future__ import annotations

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    buildIndex,
    loadData,
    extractCorpName,
)


class Company:
    """종목코드 하나로 전체 분석에 접근.

    생성 시 parquet 데이터를 로딩하고 기업명을 추출한다.
    로컬에 데이터가 없으면 GitHub Release에서 자동 다운로드한다.

    Attributes:
        stockCode: 6자리 KRX 종목코드.
        corpName: DART 공시 기업명.

    Example::

        c = Company("005930")
        print(c)                    # Company(005930, 삼성전자)
        result = c.statements()     # StatementsResult
        result.BS                   # 재무상태표 DataFrame

        Company.status()            # 로컬 보유 전체 종목 인덱스
        c.docs()                    # 이 종목의 문서 목록 + DART 뷰어 링크
    """

    def __init__(self, stockCode: str):
        self.stockCode = stockCode
        df = loadData(stockCode)
        self.corpName = extractCorpName(df)

    def __repr__(self):
        return f"Company({self.stockCode}, {self.corpName})"

    # ── 인덱스·메타 ──

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스.

        Returns:
            DataFrame (stockCode, corpName, rows, yearFrom, yearTo, nDocs).
            종목코드 순 정렬.

        Example::

            df = Company.status()
            print(df)
            # ┌───────────┬──────────┬──────┬──────────┬────────┬───────┐
            # │ stockCode ┆ corpName ┆ rows ┆ yearFrom ┆ yearTo ┆ nDocs │
            # ├───────────┼──────────┼──────┼──────────┼────────┼───────┤
            # │ 005930    ┆ 삼성전자 ┆ 4156 ┆ 1999     ┆ 2025   ┆ 106   │
            # └───────────┴──────────┴──────┴──────────┴────────┴───────┘
        """
        return buildIndex()

    def docs(self) -> pl.DataFrame:
        """이 종목의 공시 문서 목록 + DART 뷰어 링크.

        Returns:
            DataFrame (year, reportType, rceptDate, rceptNo, dartUrl).
            최신 연도순 정렬.

        Example::

            c = Company("005930")
            c.docs()
            # ┌──────┬───────────────────────┬───────────┬────────────────┬──────────────────┐
            # │ year ┆ reportType            ┆ rceptDate ┆ rceptNo        ┆ dartUrl          │
            # ├──────┼───────────────────────┼───────────┼────────────────┼──────────────────┤
            # │ 2024 ┆ 사업보고서 (2024.12)  ┆ 20250313  ┆ 20250313000798 ┆ https://dart...  │
            # └──────┴───────────────────────┴───────────┴────────────────┴──────────────────┘
        """
        df = loadData(self.stockCode)
        docs = (
            df.select("year", "rcept_date", "rcept_no", "report_type")
            .unique(subset=["rcept_no"])
            .with_columns(
                pl.lit(DART_VIEWER).add(pl.col("rcept_no")).alias("dartUrl"),
            )
            .rename({
                "report_type": "reportType",
                "rcept_date": "rceptDate",
                "rcept_no": "rceptNo",
            })
            .sort("year", "rceptDate", descending=[True, True])
        )
        return docs

    # ── 재무제표 ──

    def analyze(self, ifrsOnly: bool = True, period: str = "y"):
        """요약재무정보 시계열 + 브릿지 매칭 + 전환점 탐지.

        Args:
            ifrsOnly: True면 K-IFRS 도입(2011~) 이후만 분석.
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            AnalysisResult | None.
            - FS/BS/IS: 재무제표 DataFrame
            - allRate/contRate: 전체/연속 매칭률
            - segments: 연속 구간 목록
            - breakpoints: 계정과목 전환점 목록
        """
        from dartlab.finance.summary import analyze
        return analyze(self.stockCode, ifrsOnly=ifrsOnly, period=period)

    def statements(self, ifrsOnly: bool = True, period: str = "y"):
        """연결재무제표 BS·IS·CF 시계열 DataFrame 추출.

        Args:
            ifrsOnly: True면 K-IFRS 도입(2011~) 이후만.
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            StatementsResult | None.
            - BS: 재무상태표 DataFrame
            - IS: 손익계산서 DataFrame
            - CF: 현금흐름표 DataFrame
        """
        from dartlab.finance.statements import statements
        return statements(self.stockCode, ifrsOnly=ifrsOnly, period=period)

    def segments(self, period: str = "y"):
        """연결재무제표 주석 부문별 보고 데이터 추출.

        Args:
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            SegmentsResult | None.
            - tables: {연도: [SegmentTable]} 부문/제품/지역별 테이블
            - revenue: 부문별 매출 시계열 DataFrame
        """
        from dartlab.finance.segment import segments
        return segments(self.stockCode, period=period)

    def costByNature(self, period: str = "y"):
        """연결재무제표 주석 비용의 성격별 분류 시계열 추출.

        Args:
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            CostByNatureResult | None.
            - timeSeries: 비용 시계열 DataFrame
            - ratios: 비용 구성비 DataFrame
            - crossCheck: 교차검증 결과
        """
        from dartlab.finance.costByNature import costByNature
        return costByNature(self.stockCode, period=period)

    # ── 주주·자본 ──

    def majorHolder(self):
        """최대주주 및 특수관계인 현황 시계열 추출.

        Returns:
            MajorHolderResult | None.
            - majorHolder/majorRatio: 최대주주명 및 지분율
            - totalRatio: 특수관계인 합계 지분율
            - holders: 최신 연도 특수관계인 목록
            - timeSeries: 최대주주 시계열 DataFrame
        """
        from dartlab.finance.majorHolder import majorHolder
        return majorHolder(self.stockCode)

    def holderOverview(self):
        """5% 이상 주주, 소액주주, 의결권 현황 추출.

        Returns:
            HolderOverview | None.
            - bigHolders: 5% 이상 대량보유 주주 목록
            - minority: 소액주주 현황 (주주수, 주식수, 비율)
            - voting: 의결권 현황 (보통주/우선주별)
        """
        from dartlab.finance.majorHolder import holderOverview
        return holderOverview(self.stockCode)

    def shareCapital(self):
        """발행주식·자기주식·유통주식 현황 시계열 추출.

        Returns:
            ShareCapitalResult | None.
            - authorizedShares: 정관상 발행할 주식의 총수
            - outstandingShares/treasuryShares/floatingShares: 발행·자기·유통 주식수
            - treasuryRatio: 자기주식 보유비율 (%)
            - timeSeries: 주식 시계열 DataFrame
        """
        from dartlab.finance.shareCapital import shareCapital
        return shareCapital(self.stockCode)

    # ── 사업 현황 ──

    def dividend(self):
        """배당 지표 시계열 추출.

        Returns:
            DividendResult | None.
            - timeSeries: 배당 시계열 DataFrame
              (year, netIncome, eps, totalDividend, payoutRatio,
               dividendYield, dps, dpsPreferred)
        """
        from dartlab.finance.dividend import dividend
        return dividend(self.stockCode)

    def employee(self):
        """직원 현황 시계열 추출.

        Returns:
            EmployeeResult | None.
            - timeSeries: 직원 시계열 DataFrame
              (year, totalEmployees, avgTenure, totalSalary, avgSalary)
        """
        from dartlab.finance.employee import employee
        return employee(self.stockCode)

    def subsidiary(self):
        """타법인출자 현황 (자회사·투자 포트폴리오) 추출.

        Returns:
            SubsidiaryResult | None.
            - investments: 최신 연도 투자 목록 (SubsidiaryInvestment)
            - timeSeries: 투자 시계열 DataFrame
              (year, totalCount, listedCount, unlistedCount, totalBook)
        """
        from dartlab.finance.subsidiary import subsidiary
        return subsidiary(self.stockCode)

    def bond(self):
        """채무증권 발행실적 추출.

        Returns:
            BondResult | None.
            - issuances: 최신 연도 채무증권 목록 (BondIssuance)
            - timeSeries: 발행 시계열 DataFrame
              (year, totalIssuances, totalAmount, unredeemedCount)
        """
        from dartlab.finance.bond import bond
        return bond(self.stockCode)

    def affiliates(self, period: str = "y"):
        """관계기업·공동기업 투자 데이터 추출.

        Args:
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            AffiliatesResult | None.
            - profiles: {연도: [AffiliateProfile]} 기업 프로필
            - movements: {연도: [AffiliateMovement]} 기업별 변동
            - movementDf: 기업별 변동 시계열 DataFrame
        """
        from dartlab.finance.affiliate import affiliates
        return affiliates(self.stockCode, period=period)

    # ── 기타 ──

    def mdna(self):
        """이사의 경영진단 및 분석의견 (MD&A) 텍스트 추출.

        Returns:
            MdnaResult | None.
            - sections: 최신 연도 섹션 목록 (MdnaSection)
              각 섹션은 category(overview, forecast, financials 등)로 분류
            - overview: 개요 텍스트 (테이블 제외)
        """
        from dartlab.finance.mdna import mdna
        return mdna(self.stockCode)

    def rawMaterial(self):
        """원재료 매입·유형자산·시설투자 현황 추출.

        Returns:
            RawMaterialResult | None.
            - materials: 원재료 매입 항목 목록 (RawMaterial)
            - equipment: 유형자산 기말잔액 (Equipment)
            - capexItems: 시설투자 항목 목록 (CapexItem)
        """
        from dartlab.finance.rawMaterial import rawMaterial
        return rawMaterial(self.stockCode)
