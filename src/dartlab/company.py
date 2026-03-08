"""종목 단위 통합 분석 클래스.

사용법::

    from dartlab import Company

    c = Company("005930")
    c = Company("삼성전자")
    c.corpName                         # "삼성전자"
    c.dividend()                       # DividendResult | None
    c.statements(period="q")           # StatementsResult (분기)
"""

from __future__ import annotations

import re

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    buildIndex,
    extractCorpName,
    loadData,
)
from dartlab.core.kindList import (
    codeToName,
    getKindList,
    nameToCode,
    searchName,
)


class Company:
    """종목코드 또는 회사명으로 전체 분석에 접근.

    종목코드(6자리 숫자) 또는 회사명을 넘기면 자동으로 변환한다.
    생성 시 parquet 데이터를 로딩하고 기업명을 추출한다.
    로컬에 데이터가 없으면 GitHub Release에서 자동 다운로드한다.

    Attributes:
        stockCode: 6자리 KRX 종목코드.
        corpName: DART 공시 기업명.

    Example::

        c = Company("005930")
        c = Company("삼성전자")
        print(c)                    # Company(005930, 삼성전자)
        result = c.statements()     # StatementsResult
        result.BS                   # 재무상태표 DataFrame

        Company.search("삼성")       # KIND 목록에서 검색
        Company.listing()           # KRX 전체 상장법인 목록
        Company.status()            # 로컬 보유 전체 종목 인덱스
        c.docs()                    # 이 종목의 문서 목록 + DART 뷰어 링크
    """

    def __init__(self, codeOrName: str):
        if re.match(r"^\d{6}$", codeOrName):
            self.stockCode = codeOrName
        else:
            code = nameToCode(codeOrName)
            if code is None:
                raise ValueError(f"'{codeOrName}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        df = loadData(self.stockCode)
        self.corpName = extractCorpName(df)

    def __repr__(self):
        return f"Company({self.stockCode}, {self.corpName})"

    # ── 인덱스·메타 ──

    @staticmethod
    def listing(*, forceRefresh: bool = False) -> pl.DataFrame:
        """KRX 전체 상장법인 목록 (KIND 기준).

        Args:
            forceRefresh: True면 캐시 무시하고 KIND API 재요청.

        Returns:
            DataFrame (회사명, 종목코드, 업종, 주요제품, 상장일, 결산월, ...).

        Example::

            df = Company.listing()
            print(df.head(3))
        """
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준).

        Args:
            keyword: 검색 키워드 (예: "삼성", "반도체").

        Returns:
            매칭된 종목 DataFrame (회사명, 종목코드, ...).

        Example::

            Company.search("삼성")
            # ┌──────────────┬──────────┬─────────┐
            # │ 회사명       ┆ 종목코드 ┆ 업종    │
            # ├──────────────┼──────────┼─────────┤
            # │ 삼성전자     ┆ 005930   ┆ ...     │
            # │ 삼성SDI      ┆ 006400   ┆ ...     │
            # └──────────────┴──────────┴─────────┘
        """
        return searchName(keyword)

    @staticmethod
    def resolve(codeOrName: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환.

        Args:
            codeOrName: 6자리 종목코드 또는 회사명.

        Returns:
            종목코드 (str) 또는 None.
        """
        if re.match(r"^\d{6}$", codeOrName):
            return codeOrName
        return nameToCode(codeOrName)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환."""
        return codeToName(stockCode)

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

    def fsSummary(self, ifrsOnly: bool = True, period: str = "y"):
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
        from dartlab.finance.summary import fsSummary
        return fsSummary(self.stockCode, ifrsOnly=ifrsOnly, period=period)

    def statements(
        self,
        ifrsOnly: bool = True,
        period: str = "y",
        scope: str | None = None,
    ):
        """재무제표 BS·IS·CF 시계열 DataFrame 추출.

        Args:
            ifrsOnly: True면 K-IFRS 도입(2011~) 이후만.
            period: "y" (연간) | "q" (분기) | "h" (반기).
            scope: "consolidated" (연결) | "separate" (별도) | None (연결 우선, 별도 fallback).

        Returns:
            StatementsResult | None.
            - BS: 재무상태표 DataFrame
            - IS: 손익계산서 DataFrame
            - CF: 현금흐름표 DataFrame
        """
        from dartlab.finance.statements import statements
        return statements(self.stockCode, ifrsOnly=ifrsOnly, period=period, scope=scope)

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

    def notesDetail(self, keyword: str, period: str = "y"):
        """주석 세부항목 테이블 추출.

        Args:
            keyword: 주석 키워드 (재고자산, 주당이익, 충당부채, 차입금, 매출채권, 리스, 투자부동산, 무형자산)
            period: "y" (연간) | "q" (분기) | "h" (반기).

        Returns:
            NotesDetailResult | None.
            - tables: {연도: [NotesPeriod]} 기간별 테이블
            - tableDf: 항목별 시계열 DataFrame
        """
        from dartlab.finance.notesDetail import notesDetail
        return notesDetail(self.stockCode, keyword=keyword, period=period)

    def affiliateGroup(self):
        """계열회사 현황 추출.

        Returns:
            AffiliateGroupResult | None.
            - groupName: 기업집단명
            - listedCount/unlistedCount/totalCount: 상장/비상장/합계 수
            - affiliates: 계열사 목록 [{name, listed}, ...]
            - affiliateDf: 계열사 목록 DataFrame (name, listed)
        """
        from dartlab.finance.affiliateGroup import affiliateGroup
        return affiliateGroup(self.stockCode)

    def fundraising(self):
        """증권 발행(증자/감자) 이력 추출.

        Returns:
            FundraisingResult | None.
            - issuances: 발행 이력 [{date, issueType, stockType, quantity, ...}]
            - noData: 발행 실적 없음 여부
            - issuanceDf: 발행 이력 DataFrame
        """
        from dartlab.finance.fundraising import fundraising
        return fundraising(self.stockCode)

    def productService(self):
        """주요 제품 및 서비스 추출.

        Returns:
            ProductServiceResult | None.
            - unit: 단위
            - products: [{label, amount, ratio}]
            - productDf: DataFrame (label | amount | ratio)
        """
        from dartlab.finance.productService import productService
        return productService(self.stockCode)

    def salesOrder(self):
        """매출 및 수주상황 추출.

        Returns:
            SalesOrderResult | None.
            - unit: 단위 (억원, 백만원 등)
            - sales: 매출실적 [{label, values}]
            - orders: 수주상황 [{label, values}]
            - salesDf/orderDf: DataFrame
        """
        from dartlab.finance.salesOrder import salesOrder
        return salesOrder(self.stockCode)

    def riskDerivative(self):
        """위험관리 및 파생거래 추출.

        Returns:
            RiskDerivativeResult | None.
            - fxSensitivity: 환율 민감도 [{currency, upImpact, downImpact}]
            - derivatives: 파생상품 계약 [{label, values}]
            - fxDf/derivativeDf: DataFrame
        """
        from dartlab.finance.riskDerivative import riskDerivative
        return riskDerivative(self.stockCode)

    def articlesOfIncorporation(self):
        """정관에 관한 사항 추출.

        Returns:
            ArticlesResult | None.
            - changes: 정관 변경 이력 [{date, meetingName, changes, reason}]
            - purposes: 사업목적 현황 [{purpose, active}]
            - changesDf/purposesDf: DataFrame
        """
        from dartlab.finance.articlesOfIncorporation import articlesOfIncorporation
        return articlesOfIncorporation(self.stockCode)

    def otherFinance(self):
        """기타 재무에 관한 사항 추출.

        Returns:
            OtherFinanceResult | None.
            - badDebt: 대손충당금 [{account, period, totalDebt, provision}]
            - inventory: 재고자산 [{item, values}]
            - badDebtDf/inventoryDf: DataFrame
        """
        from dartlab.finance.otherFinance import otherFinance
        return otherFinance(self.stockCode)

    def companyHistory(self):
        """회사의 연혁 추출.

        Returns:
            CompanyHistoryResult | None.
            - events: 연혁 이벤트 [{date, event}]
            - eventsDf: DataFrame
        """
        from dartlab.finance.companyHistory import companyHistory
        return companyHistory(self.stockCode)

    def shareholderMeeting(self):
        """주주총회 등에 관한 사항 추출.

        Returns:
            ShareholderMeetingResult | None.
            - agendas: 안건 [{agenda, result}]
            - agendaDf: DataFrame
        """
        from dartlab.finance.shareholderMeeting import shareholderMeeting
        return shareholderMeeting(self.stockCode)

    def auditSystem(self):
        """감사제도에 관한 사항 추출.

        Returns:
            AuditSystemResult | None.
            - committee: 감사위원 [{name, role, detail}]
            - activity: 감사활동 [{date, agenda, result}]
            - committeeDf/activityDf: DataFrame
        """
        from dartlab.finance.auditSystem import auditSystem
        return auditSystem(self.stockCode)

    def investmentInOther(self):
        """타법인출자 현황 추출.

        Returns:
            InvestmentInOtherResult | None.
            - investments: 투자법인 [{name, values}]
            - investmentDf: DataFrame
        """
        from dartlab.finance.investmentInOther import investmentInOther
        return investmentInOther(self.stockCode)

    def companyOverviewDetail(self):
        """회사의 개요 상세 추출.

        Returns:
            CompanyOverviewDetailResult | None.
            - foundedDate, listedDate, address, ceo, mainBusiness, website
        """
        from dartlab.finance.companyOverviewDetail import companyOverviewDetail
        return companyOverviewDetail(self.stockCode)

    def audit(self):
        """감사의견 + 감사보수 시계열 추출.

        Returns:
            AuditResult | None.
            - opinionDf: 감사의견 시계열 DataFrame
              (year, auditor, opinion, keyAuditMatters)
            - feeDf: 감사보수 시계열 DataFrame
              (year, auditor, contractFee, contractHours, actualFee, actualHours)
        """
        from dartlab.finance.audit import audit
        return audit(self.stockCode)

    def executive(self):
        """임원 현황 시계열 추출 (등기임원 집계 + 미등기임원 보수).

        Returns:
            ExecutiveResult | None.
            - executiveDf: 등기임원 집계 시계열 DataFrame
              (year, totalRegistered, insideDirectors, outsideDirectors,
               otherNonexec, fullTimeCount, partTimeCount, maleCount, femaleCount)
            - unregPayDf: 미등기임원 보수 시계열 DataFrame
              (year, headcount, totalSalary, avgSalary)
        """
        from dartlab.finance.executive import executive
        return executive(self.stockCode)

    def executivePay(self):
        """임원 보수 시계열 추출 (유형별 + 5억 초과 개인별).

        Returns:
            ExecutivePayResult | None.
            - payByTypeDf: 유형별 보수 시계열 DataFrame
              (year, category, headcount, totalPay, avgPay)
            - topPayDf: 5억 초과 개인별 보수 DataFrame
              (year, name, position, totalPay)
        """
        from dartlab.finance.executivePay import executivePay
        return executivePay(self.stockCode)

    def boardOfDirectors(self):
        """이사회 시계열 추출 (이사 수, 개최횟수, 출석률, 위원회).

        Returns:
            BoardResult | None.
            - boardDf: 이사회 시계열 DataFrame
              (year, totalDirectors, outsideDirectors, meetingCount, avgAttendanceRate)
            - committeeDf: 위원회 구성 DataFrame
              (year, committeeName, composition, members)
        """
        from dartlab.finance.boardOfDirectors import boardOfDirectors
        return boardOfDirectors(self.stockCode)

    def capitalChange(self):
        """자본금 변동·주식 총수·자기주식 시계열 추출.

        Returns:
            CapitalChangeResult | None.
            - capitalDf: 자본금 변동 시계열 (보통주/우선주 발행주식·액면·자본금)
            - shareTotalDf: 주식 총수 시계열 (수권·발행·감소·유통주식)
            - treasuryDf: 자기주식 변동 시계열 (기초·기말)
        """
        from dartlab.finance.capitalChange import capitalChange
        return capitalChange(self.stockCode)

    def contingentLiability(self):
        """우발부채·채무보증·소송 시계열 추출.

        Returns:
            ContingentLiabilityResult | None.
            - guaranteeDf: 채무보증 시계열 (year, totalGuaranteeAmount, lineCount)
            - lawsuitDf: 소송 현황 (year, filingDate, parties, amount, status)
        """
        from dartlab.finance.contingentLiability import contingentLiability
        return contingentLiability(self.stockCode)

    def internalControl(self):
        """내부회계관리제도 시계열 추출.

        Returns:
            InternalControlResult | None.
            - controlDf: 내부통제 시계열 (year, period, opinion, auditor, hasWeakness)
        """
        from dartlab.finance.internalControl import internalControl
        return internalControl(self.stockCode)

    def relatedPartyTx(self):
        """대주주 등과의 거래 시계열 추출.

        Returns:
            RelatedPartyTxResult | None.
            - guaranteeDf: 대주주 채무보증 (year, entity, amount)
            - revenueTxDf: 매출입 거래 (year, entity, sales, purchases)
        """
        from dartlab.finance.relatedPartyTx import relatedPartyTx
        return relatedPartyTx(self.stockCode)

    def rnd(self):
        """연구개발비 시계열 추출.

        Returns:
            RndResult | None.
            - rndDf: R&D 비용 시계열 (year, rndExpense, revenueRatio)
        """
        from dartlab.finance.rnd import rnd
        return rnd(self.stockCode)

    def sanction(self):
        """제재 현황 시계열 추출.

        Returns:
            SanctionResult | None.
            - sanctionDf: 제재 현황 (year, date, agency, action, amount, reason)
        """
        from dartlab.finance.sanction import sanction
        return sanction(self.stockCode)

    def tangibleAsset(self):
        """유형자산 변동표 추출 (연결재무제표 주석).

        Returns:
            TangibleAssetResult | None.
            - reliability: "high" (합계 컬럼 있음) | "low" (합계 없음)
            - warnings: 신뢰도 관련 경고 메시지 리스트
            - movements: {연도: [TangibleMovement]} 당기/전기 변동표
            - movementDf: 카테고리별 기초/기말 시계열 DataFrame
        """
        from dartlab.finance.tangibleAsset import tangibleAsset
        return tangibleAsset(self.stockCode)

    # ── 공시 서술 (disclosure) ──

    def business(self):
        """사업의 내용 섹션 추출 + 연도별 변경 탐지.

        Returns:
            BusinessResult | None.
            - sections: 하위 섹션 목록 (BusinessSection)
              각 섹션은 key(overview, products, materials, sales, risk, rnd, etc, financial)로 분류
            - changes: 연도별 변경 정보 (BusinessChange)
              changedPct > 30 이면 유의미한 변화 시점
        """
        from dartlab.disclosure.business import business
        return business(self.stockCode)

    def overview(self):
        """회사의 개요 정량 데이터 추출.

        Returns:
            OverviewResult | None.
            - founded/address/homepage/listedDate: 기본 정보
            - subsidiaryCount: 종속기업 수
            - isSME/isVenture: 중소기업/벤처기업 해당 여부
            - creditRatings: 신용등급 목록 (CreditRating)
            - missing: 원문에 해당 항목이 없는 필드 목록
            - failed: 항목은 있지만 파싱 실패한 필드 목록
        """
        from dartlab.disclosure.companyOverview import companyOverview
        return companyOverview(self.stockCode)

    def mdna(self):
        """이사의 경영진단 및 분석의견 (MD&A) 텍스트 추출.

        Returns:
            MdnaResult | None.
            - sections: 최신 연도 섹션 목록 (MdnaSection)
              각 섹션은 category(overview, forecast, financials 등)로 분류
            - overview: 개요 텍스트 (테이블 제외)
        """
        from dartlab.disclosure.mdna import mdna
        return mdna(self.stockCode)

    def rawMaterial(self):
        """원재료 매입·유형자산·시설투자 현황 추출.

        Returns:
            RawMaterialResult | None.
            - materials: 원재료 매입 항목 목록 (RawMaterial)
            - equipment: 유형자산 기말잔액 (Equipment)
            - capexItems: 시설투자 항목 목록 (CapexItem)
        """
        from dartlab.disclosure.rawMaterial import rawMaterial
        return rawMaterial(self.stockCode)
