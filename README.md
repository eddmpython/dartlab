<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="120">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/hero.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/assets/hero.svg">
  <img alt="DartLab Timeline" src=".github/assets/hero.svg" width="100%">
</picture>

<br>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-fb923c?style=for-the-badge&labelColor=050811&logo=github&logoColor=white" alt="Docs"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-v1"><img src="https://img.shields.io/badge/Data-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Data"></a>
</p>

<p>
<a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

</div>

---

DART 전자공시 문서를 완벽하게 분석하는 Python 라이브러리.

종목코드 하나면 재무제표, 배당, 주주, 자회사, 사업의 내용, 경영진단의견까지 — 숫자와 텍스트 모두 시계열로 추출한다.

## 설치

```bash
pip install dartlab
```

```bash
uv add dartlab
```

## 빠른 시작

```python
from dartlab import Company

samsung = Company("005930")    # 종목코드
samsung = Company("삼성전자")   # 회사명도 가능
samsung.corpName               # "삼성전자"
```

데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다. 전체 데이터를 수동으로 받을 수도 있다.

```python
from dartlab.core import downloadAll
downloadAll()  # 260+ 종목 일괄 다운로드
```

---

## 무엇을 할 수 있나

DartLab은 DART 전자공시 문서에서 **숫자(재무제표)**와 **텍스트(사업보고서)**를 모두 추출한다.

### 재무제표

요약재무정보를 시계열로 추출하고, K-IFRS 개정으로 계정명이 바뀌어도 같은 계정을 자동 추적한다 (Bridge Matching).

```python
result = samsung.fsSummary()

result.FS          # 전체 재무제표 시계열 (Polars DataFrame)
result.BS          # 재무상태표
result.IS          # 손익계산서
result.allRate     # 전체 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록
```

재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)를 분리해서 상세 항목까지 추출할 수도 있다.

```python
result = samsung.statements()

result.BS    # 재무상태표 상세 항목
result.IS    # 손익계산서 상세 항목
result.CF    # 현금흐름표
```

### 배당

DPS, 배당성향, 배당수익률 등 배당 관련 지표를 시계열로 추출한다.

```python
result = samsung.dividend()
result.timeSeries
# ┌──────┬───────────┬───────┬──────────────┬─────────────┬──────────────┬──────┐
# │ year ┆ netIncome ┆ eps   ┆ totalDividend┆ payoutRatio ┆ dividendYield┆ dps  │
# ├──────┼───────────┼───────┼──────────────┼─────────────┼──────────────┼──────┤
# │ 2024 ┆ ...       ┆ ...   ┆ ...          ┆ ...         ┆ ...          ┆ 1444 │
# │ 2023 ┆ ...       ┆ ...   ┆ ...          ┆ ...         ┆ ...          ┆ 1444 │
# └──────┴───────────┴───────┴──────────────┴─────────────┴──────────────┴──────┘
```

### 최대주주

최대주주와 특수관계인의 지분율 변화를 추적한다.

```python
result = samsung.majorHolder()
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 포함 합계
result.holders       # 개별 주주 목록
result.timeSeries    # 지분율 시계열
```

5% 이상 주주, 소액주주, 의결권 현황도 별도로 제공한다.

```python
overview = samsung.holderOverview()
overview.bigHolders  # 5% 이상 주주 목록
overview.minority    # 소액주주 현황 (주주수, 주식수, 비율)
overview.voting      # 의결권 현황
```

### 직원 현황

총 직원수, 평균연봉, 근속연수를 시계열로 추출한다.

```python
result = samsung.employee()
result.timeSeries  # year, totalEmployees, avgSalary, avgTenure, ...
```

### 부문별 매출

사업부문, 제품, 지역별 매출 데이터를 추출한다.

```python
result = samsung.segments()
result.revenue  # 부문별 매출 시계열 DataFrame
result.tables   # {연도: [SegmentTable]} 상세 테이블
```

### 주식 현황

발행주식, 자기주식, 유통주식 수를 시계열로 추적한다.

```python
result = samsung.shareCapital()
result.outstandingShares  # 발행주식 총수
result.treasuryShares     # 자기주식수
result.floatingShares     # 유통주식수
result.treasuryRatio      # 자기주식 보유비율 (%)
```

### 자회사 투자

타법인 출자 현황 — 자회사 포트폴리오 전체를 추출한다.

```python
result = samsung.subsidiary()
result.investments  # 투자 목록 (법인명, 지분율, 장부가 등)
result.timeSeries   # 연도별 총 투자건수, 장부가 시계열
```

### 관계기업

관계기업/공동기업 투자 데이터를 추출한다.

```python
result = samsung.affiliates()
result.profiles     # {연도: [기업 프로필]}
result.movementDf   # 기업별 변동 시계열
```

### 감사의견

외부감사인, 감사의견, 핵심감사사항, 감사보수를 시계열로 추출한다.

```python
result = samsung.audit()
result.opinionDf   # year, auditor, opinion, keyAuditMatters
result.feeDf       # year, auditor, contractFee, contractHours, actualFee, actualHours
```

### 임원 현황

등기임원 집계(사내이사/사외이사/기타비상무) + 미등기임원 보수를 시계열로 추출한다.

```python
result = samsung.executive()
result.executiveDf  # year, totalRegistered, insideDirectors, outsideDirectors, ...
result.unregPayDf   # year, headcount, totalSalary, avgSalary
```

### 임원 보수

유형별(등기이사/사외이사/감사위원) 보수 + 5억 초과 개인별 보수를 시계열로 추출한다.

```python
result = samsung.executivePay()
result.payByTypeDf  # year, category, headcount, totalPay, avgPay
result.topPayDf     # year, name, position, totalPay
```

### 유형자산 변동표

유형자산 변동표(취득, 처분, 감가상각 등)를 추출한다.

```python
result = samsung.tangibleAsset()
result.reliability  # "high" | "low" (합계 컬럼 유무)
result.warnings     # 신뢰도 관련 경고
result.movements    # {연도: [TangibleMovement]}
result.movementDf   # 카테고리별 기초/기말 시계열
```

### 이사회

이사회 구성, 개최 횟수, 출석률, 위원회 구성을 시계열로 추출한다.

```python
result = samsung.boardOfDirectors()
result.boardDf      # year, totalDirectors, outsideDirectors, meetingCount, avgAttendanceRate
result.committeeDf  # year, committeeName, composition, members
```

### 자본금 변동

자본금 변동, 주식의 총수, 자기주식 변동을 시계열로 추출한다.

```python
result = samsung.capitalChange()
result.capitalDf     # year, commonShares, preferredShares, commonCapital, ...
result.shareTotalDf  # year, authorizedTotal, issuedTotal, outstandingTotal, ...
result.treasuryDf    # year, totalBegin, totalEnd
```

### 우발부채

채무보증, 소송 현황을 추출한다.

```python
result = samsung.contingentLiability()
result.guaranteeDf  # year, totalGuaranteeAmount, lineCount
result.lawsuitDf    # year, filingDate, parties, amount, status
```

### 대주주 거래

대주주 등과의 거래내용 — 채무보증, 매출입 거래를 추출한다.

```python
result = samsung.relatedPartyTx()
result.guaranteeDf  # year, entity, relationship, amount
result.revenueTxDf  # year, entity, sales, purchases
```

### 제재 현황

제재·처벌 내역을 추출한다.

```python
result = samsung.sanction()
result.sanctionDf  # year, date, agency, subject, action, amount, reason
```

### 연구개발활동

연구개발비용과 매출액 대비 비율을 시계열로 추출한다.

```python
result = samsung.rnd()
result.rndDf  # year, rndExpense, revenueRatio
```

### 내부통제

내부회계관리제도 운영 실태 평가를 시계열로 추출한다.

```python
result = samsung.internalControl()
result.controlDf  # year, opinion, auditor, hasWeakness
```

### 계열회사

기업집단 내 계열사 현황 — 그룹명, 상장/비상장 계열사 목록을 추출한다.

```python
result = samsung.affiliateGroup()
result.groupName     # "삼성"
result.listedCount   # 17
result.unlistedCount # 46
result.totalCount    # 63
result.affiliateDf   # name | listed
```

### 증자/감자

증자(감자) 현황 — 발행일자, 형태, 종류, 수량, 발행가 등을 추출한다.

```python
result = samsung.fundraising()
result.issuances    # [{date, issueType, stockType, quantity, ...}]
result.noData       # True (삼성전자는 발행 실적 없음)
result.issuanceDf   # date | issueType | stockType | quantity | parValue | issuePrice
```

### 매출 및 수주

매출실적(부문/제품별) + 수주잔고를 추출한다.

```python
result = samsung.salesOrder()
result.unit      # "억원"
result.salesDf   # label | v1 | v2 | v3 (당기/전기/전전기)
result.orderDf   # 수주상황 DataFrame
```

### 주요 제품/서비스

주요 제품 및 서비스 현황 — 매출액, 비중을 추출한다.

```python
result = samsung.productService()
result.productDf   # label | amount | ratio
```

### 위험관리 및 파생거래

환율 민감도, 파생상품 계약 현황을 추출한다.

```python
result = samsung.riskDerivative()
result.fxDf          # currency | upImpact | downImpact
result.derivativeDf  # 파생상품 계약 DataFrame
```

### 주석 세부항목

재고자산, 차입금, 특수관계자 등 23개 주석 세부항목 테이블을 추출한다.

```python
result = samsung.notesDetail("재고자산")
result.tables     # {연도: [NotesPeriod]} 기간별 테이블
result.tableDf    # 항목별 시계열 DataFrame
```

지원 키워드 (23개): `재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

### 채무증권

회사채, 기업어음 등 채무증권 발행실적을 추출한다.

```python
result = samsung.bond()
result.issuances   # 채무증권 목록 (종류, 금액, 이자율, 만기일 등)
result.timeSeries  # 연도별 발행건수, 총액 시계열
```

### 비용 구조

비용의 성격별 분류 — 원재료비, 인건비, 감가상각비 등의 구성을 추출한다.

```python
result = samsung.costByNature()
result.timeSeries  # 비용 시계열
result.ratios      # 비용 구성비
```

### 정관에 관한 사항

정관 변경 이력, 사업목적 현황을 추출한다.

```python
result = samsung.articlesOfIncorporation()
result.changes       # 정관 변경 이력 [`{date, meetingName, changes, reason}`]
result.purposes      # 사업목적 [`{purpose, active}`]
result.changesDf     # DataFrame
```

### 기타 재무에 관한 사항

대손충당금, 재고자산 등 기타 재무 데이터를 추출한다.

```python
result = samsung.otherFinance()
result.badDebt       # 대손충당금 [`{account, period, totalDebt, provision}`]
result.inventory     # 재고자산 [`{item, values}`]
```

### 회사의 연혁

회사의 연혁 이벤트를 시계열로 추출한다.

```python
result = samsung.companyHistory()
result.events        # [`{date, event}`]
result.eventsDf      # DataFrame
```

### 주주총회 등에 관한 사항

주주총회 안건, 결의 결과를 추출한다.

```python
result = samsung.shareholderMeeting()
result.agendas       # [`{agenda, result}`]
result.agendaDf      # DataFrame
```

### 감사제도에 관한 사항

감사위원, 감사활동 데이터를 추출한다.

```python
result = samsung.auditSystem()
result.committee     # [`{name, role, detail}`]
result.activity      # [`{date, agenda, result}`]
```

### 타법인출자 현황

타법인 출자 현황 — 투자법인, 지분율, 장부가를 추출한다.

```python
result = samsung.investmentInOther()
result.investments   # [`{name, values}`]
result.investmentDf  # DataFrame
```

### 회사의 개요 상세

설립일, 상장일, 대표이사, 소재지 등 상세 정보를 추출한다.

```python
result = samsung.companyOverviewDetail()
result.foundedDate   # 설립일
result.ceo           # 대표이사
result.address       # 본점소재지
```

### 회사 개요

설립일, 본사주소, 종속기업 수, 신용등급 등 기본 정보를 추출한다.

```python
result = samsung.overview()
result.founded          # "1969-01-13"
result.address          # "경기도 수원시 영통구 ..."
result.subsidiaryCount  # 종속기업 수
result.creditRatings    # [CreditRating(agency="Moody's", grade="Aa2"), ...]
result.isSME            # False
```

### 경영진단의견 (MD&A)

이사의 경영진단 및 분석의견 — 사업 전망, 실적 분석, 위험 요인 등을 섹션별로 분류한다.

```python
result = samsung.mdna()
result.overview    # 사업 개요 텍스트
result.sections    # 섹션별 분류 (overview, forecast, financials, ...)

for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(section.text[:200])
```

### 사업의 내용

사업보고서 "사업의 내용" 전체를 섹션별로 분류하고, 연도별 변경 시점을 탐지한다.

```python
result = samsung.business()
result.sections  # 하위 섹션 목록 (overview, products, risk, rnd, ...)
result.changes   # 연도별 변경 정보 (changedPct > 30이면 유의미한 변화)
```

### 원재료/설비투자

원재료 매입, 유형자산, 시설투자 현황을 추출한다.

```python
result = samsung.rawMaterial()
result.materials   # 원재료 매입 항목
result.equipment   # 유형자산 기말잔액
result.capexItems  # 시설투자 항목
```

---

## 종목 검색

```python
from dartlab import Company

# 회사명으로 검색
Company.search("삼성")
# ┌──────────────┬──────────┬────────────────┐
# │ 회사명       ┆ 종목코드 ┆ 업종           │
# ├──────────────┼──────────┼────────────────┤
# │ 삼성전자     ┆ 005930   ┆ 반도체         │
# │ 삼성SDI      ┆ 006400   ┆ 일차전지       │
# │ ...          ┆ ...      ┆ ...            │
# └──────────────┴──────────┴────────────────┘

# KRX 전체 상장법인 목록
Company.listing()

# 로컬 보유 종목 인덱스
Company.status()

# 공시 문서 목록 + DART 뷰어 링크
samsung.docs()
```

---

## 패키지 구조

DartLab은 데이터의 성격에 따라 두 패키지로 나뉜다.

### finance — 정량 재무 데이터 (36개 모듈)

숫자 테이블을 파싱해서 DataFrame으로 변환한다.

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.summary` | `fsSummary(stockCode)` | `.fsSummary()` | 요약재무정보, Bridge Matching |
| `finance.statements` | `statements(stockCode)` | `.statements()` | 연결재무제표 BS, IS, CF |
| `finance.segment` | `segments(stockCode)` | `.segments()` | 부문별 매출 |
| `finance.costByNature` | `costByNature(stockCode)` | `.costByNature()` | 비용의 성격별 분류 |
| `finance.majorHolder` | `majorHolder(stockCode)` | `.majorHolder()` | 최대주주 지분율 |
| `finance.majorHolder` | `holderOverview(stockCode)` | `.holderOverview()` | 5% 주주, 소액주주, 의결권 |
| `finance.shareCapital` | `shareCapital(stockCode)` | `.shareCapital()` | 발행·자기·유통 주식 |
| `finance.dividend` | `dividend(stockCode)` | `.dividend()` | 배당 시계열 |
| `finance.employee` | `employee(stockCode)` | `.employee()` | 직원 현황 |
| `finance.subsidiary` | `subsidiary(stockCode)` | `.subsidiary()` | 타법인 출자 현황 |
| `finance.bond` | `bond(stockCode)` | `.bond()` | 채무증권 발행실적 |
| `finance.affiliate` | `affiliates(stockCode)` | `.affiliates()` | 관계기업 투자 |
| `finance.articlesOfIncorporation` | `articlesOfIncorporation(stockCode)` | `.articlesOfIncorporation()` | 정관 변경 이력, 사업목적 현황 |
| `finance.audit` | `audit(stockCode)` | `.audit()` | 감사의견 + 감사보수 |
| `finance.auditSystem` | `auditSystem(stockCode)` | `.auditSystem()` | 감사위원, 감사활동 |
| `finance.executive` | `executive(stockCode)` | `.executive()` | 임원 현황 (등기임원 집계 + 미등기 보수) |
| `finance.executivePay` | `executivePay(stockCode)` | `.executivePay()` | 임원 보수 (유형별 + 5억 초과 개인별) |
| `finance.tangibleAsset` | `tangibleAsset(stockCode)` | `.tangibleAsset()` | 유형자산 변동표 |
| `finance.notesDetail` | `notesDetail(stockCode, keyword)` | `.notesDetail(keyword)` | 주석 세부항목 (23개 키워드) |
| `finance.otherFinance` | `otherFinance(stockCode)` | `.otherFinance()` | 대손충당금, 재고자산 |
| `finance.boardOfDirectors` | `boardOfDirectors(stockCode)` | `.boardOfDirectors()` | 이사회 구성·출석률·위원회 |
| `finance.capitalChange` | `capitalChange(stockCode)` | `.capitalChange()` | 자본금 변동·주식 총수·자기주식 |
| `finance.companyHistory` | `companyHistory(stockCode)` | `.companyHistory()` | 연혁 이벤트 시계열 |
| `finance.companyOverviewDetail` | `companyOverviewDetail(stockCode)` | `.companyOverviewDetail()` | 설립일, 상장일, 대표이사, 소재지 |
| `finance.contingentLiability` | `contingentLiability(stockCode)` | `.contingentLiability()` | 우발부채·채무보증·소송 |
| `finance.relatedPartyTx` | `relatedPartyTx(stockCode)` | `.relatedPartyTx()` | 대주주 거래 (보증·매출입) |
| `finance.sanction` | `sanction(stockCode)` | `.sanction()` | 제재·처벌 현황 |
| `finance.shareholderMeeting` | `shareholderMeeting(stockCode)` | `.shareholderMeeting()` | 안건, 결의 결과 |
| `finance.rnd` | `rnd(stockCode)` | `.rnd()` | 연구개발비·매출 대비 비율 |
| `finance.internalControl` | `internalControl(stockCode)` | `.internalControl()` | 내부통제 평가 |
| `finance.investmentInOther` | `investmentInOther(stockCode)` | `.investmentInOther()` | 투자법인, 지분율, 장부가 |
| `finance.affiliateGroup` | `affiliateGroup(stockCode)` | `.affiliateGroup()` | 계열회사 현황 (그룹명·상장/비상장) |
| `finance.fundraising` | `fundraising(stockCode)` | `.fundraising()` | 증자(감자) 현황 |
| `finance.salesOrder` | `salesOrder(stockCode)` | `.salesOrder()` | 매출실적·수주상황 |
| `finance.productService` | `productService(stockCode)` | `.productService()` | 주요 제품/서비스 매출·비중 |
| `finance.riskDerivative` | `riskDerivative(stockCode)` | `.riskDerivative()` | 위험관리·환율민감도·파생상품 |

### disclosure — 공시 서술형 섹션 (4개 모듈)

텍스트에서 정보를 추출하고 섹션별로 분류한다.

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `disclosure.business` | `business(stockCode)` | `.business()` | 사업의 내용 + 변경 탐지 |
| `disclosure.companyOverview` | `companyOverview(stockCode)` | `.overview()` | 회사의 개요 (설립일, 주소, 신용등급) |
| `disclosure.mdna` | `mdna(stockCode)` | `.mdna()` | 경영진단의견 (MD&A) |
| `disclosure.rawMaterial` | `rawMaterial(stockCode)` | `.rawMaterial()` | 원재료, 유형자산, 설비투자 |

### 함수 직접 호출

Company를 거치지 않고 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend
from dartlab.finance.audit import audit
from dartlab.finance.executive import executive
from dartlab.finance.executivePay import executivePay
from dartlab.finance.tangibleAsset import tangibleAsset
from dartlab.finance.notesDetail import notesDetail
from dartlab.finance.boardOfDirectors import boardOfDirectors
from dartlab.finance.capitalChange import capitalChange
from dartlab.finance.contingentLiability import contingentLiability
from dartlab.finance.relatedPartyTx import relatedPartyTx
from dartlab.finance.sanction import sanction
from dartlab.finance.rnd import rnd
from dartlab.finance.internalControl import internalControl
from dartlab.finance.affiliateGroup import affiliateGroup
from dartlab.finance.fundraising import fundraising
from dartlab.finance.salesOrder import salesOrder
from dartlab.finance.productService import productService
from dartlab.finance.riskDerivative import riskDerivative
from dartlab.finance.articlesOfIncorporation import articlesOfIncorporation
from dartlab.finance.otherFinance import otherFinance
from dartlab.finance.companyHistory import companyHistory
from dartlab.finance.shareholderMeeting import shareholderMeeting
from dartlab.finance.auditSystem import auditSystem
from dartlab.finance.investmentInOther import investmentInOther
from dartlab.finance.companyOverviewDetail import companyOverviewDetail
from dartlab.disclosure.business import business
from dartlab.disclosure.mdna import mdna

result = fsSummary("005930")
result = statements("005930")
result = dividend("005930")
result = audit("005930")
result = executive("005930")
result = executivePay("005930")
result = tangibleAsset("005930")
result = notesDetail("005930", "재고자산")
result = boardOfDirectors("005930")
result = capitalChange("005930")
result = contingentLiability("005930")
result = relatedPartyTx("005930")
result = sanction("005930")
result = rnd("005930")
result = internalControl("005930")
result = affiliateGroup("005930")
result = fundraising("005930")
result = salesOrder("005930")
result = productService("005930")
result = riskDerivative("005930")
result = business("005930")
result = mdna("005930")
```

### 유틸리티

| 함수 | 설명 |
|------|------|
| `Company.listing()` | KRX 전체 상장법인 목록 |
| `Company.search(keyword)` | 회사명 부분 검색 |
| `Company.status()` | 로컬 보유 전체 종목 인덱스 |
| `company.docs()` | 해당 종목의 공시 목록 + DART 뷰어 링크 |
| `core.loadData(stockCode)` | Parquet 로드 (없으면 자동 다운로드) |
| `core.downloadAll()` | 전체 데이터 일괄 다운로드 |

모든 분석 함수는 종목코드(6자리)를 받아서 Result 객체를 반환한다. 데이터가 부족하면 `None`을 반환한다. 연간/분기/반기 분석은 `period` 파라미터로 제어한다 (`"y"`, `"q"`, `"h"`).

---

## 핵심 기술

### 공시 수평 정렬

DART 전자공시는 보고서마다 담고 있는 기간이 다르다.

```
                           1분기      2분기      3분기      4분기
                          ┌──────┐
 1분기 보고서              │  Q1  │
                          └──────┘
                          ┌──────────────┐
 반기 보고서               │   Q1 + Q2    │
                          └──────────────┘
                          ┌─────────────────────┐
 3분기 보고서              │    Q1 + Q2 + Q3     │
                          └─────────────────────┘
                          ┌──────────────────────────────┐
 사업 보고서               │       Q1 + Q2 + Q3 + Q4      │
                          └──────────────────────────────┘
```

1분기 보고서에는 Q1만, 반기에는 Q1+Q2 누적, 사업보고서에는 1년 전체가 들어있다. 이 누적 구조에서 개별 분기 실적을 역산하고, 보고서 간 계정명이 바뀌어도 같은 계정을 추적하는 것이 DartLab의 핵심이다.

### Bridge Matching

K-IFRS 개정이나 내부 구조 변경으로 **동일 기업 안에서** 계정명이 바뀌는 경우가 빈번하다. Bridge Matching은 인접 연도의 재무제표에서 금액과 명칭 유사도를 조합해 동일 계정을 자동으로 연결한다.

```
             2022년            2023년            2024년
             ──────            ──────            ──────
 매출액 ────────────── 매출액 ────────────── 수익(매출액)
                              ↑ 명칭 변경                ↑ 명칭 변경
 영업이익 ──────────── 영업이익 ──────────── 영업이익
 당기순이익 ────────── 당기순이익 ────────── 당기순이익(손실)
```

4단계 매칭으로 구성된다.

1. **정확 매칭** — 금액이 완전히 동일한 계정 연결
2. **재작성 매칭** — 소수점 오차(0.5 이내) 허용
3. **명칭 변경 매칭** — 금액 오차 5% 이내 + 명칭 유사도 60% 이상
4. **특수 항목 매칭** — 주당이익(EPS) 등 소수점 단위 항목

매칭률이 85% 이하로 떨어지면 변경점(breakpoint)으로 판정하고 구간을 분리한다.

---

## 데이터

DartLab이 제공하는 데이터는 DART 전자공시 원문을 eddmpython의 노하우로 상세하게 파싱하여 만든 구조화 데이터다. 단순 API 호출 결과가 아니라 문서 구조를 분석하고 항목별로 분류·정제한 결과물이다.

각 Parquet 파일에는 하나의 기업에 대한 모든 공시 문서가 들어있다.

- **메타데이터**: 종목코드, 회사명, 보고서 유형, 제출일, 사업연도
- **정량 데이터**: 요약재무정보, 재무제표 본문, 주석
- **텍스트 데이터**: 사업의 내용, 감사의견, 위험관리, 임원/주주 현황

[GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에 260개 이상의 상장 기업 데이터가 있다. `loadData()`는 로컬에 파일이 없으면 자동으로 다운로드한다.

> **데이터 업데이트 주기**
>
> 비용이 발생하는 프록시를 사용하지 않고 직접 수집하고 있어서 데이터 업데이트가 매우 느리다. 새로운 종목 추가나 최신 공시 반영에 시간이 걸릴 수 있다.

---

## 왜 만들었나

DART 전자공시에는 재무제표 숫자뿐 아니라 사업의 내용, 위험 요인, 감사의견, 소송 현황, 지배구조 변동 같은 텍스트 정보가 함께 들어있다. 대부분의 도구는 숫자만 뽑아간다. 나머지는 버려진다.

DartLab은 숫자와 텍스트를 모두 추출한다. 분기/반기/사업보고서를 하나의 시간축 위에 정렬하고, 동일 기업 안에서 K-IFRS 개정이나 구조 변경으로 계정명이 바뀌어도 같은 계정을 자동으로 추적한다.

> **현재 범위와 향후 계획**
>
> Bridge Matching은 **한 회사 내**에서 연도 간 계정명 변경을 추적하는 기능이다. 서로 다른 회사 간 계정을 직접 비교하는 기능은 아직 제공하지 않는다.
>
> 다만, eddmpython이 다른 프로젝트에서 축적해 온 계정 표준화 노하우가 있다. 이를 바탕으로 **전체 상장사 재무제표의 95% 이상을 커버하는 교차 비교 기능**을 배치 적용할 예정이다. 또한 텍스트 분석 영역은 **별도 프로젝트에서 추진 중인 전문 텍스트 분석 모듈**을 DartLab에 통합할 계획이다.
>
> 종목 하나가 아니라 시장 전체를 한 번에 분석할 수 있는 도구가 최종 목표다.

## 비전

DartLab의 최종 목표는 **전자공시 데이터의 완전한 활용**이다.

**현재 (v0.1.x)** — 문서 파싱 도구
- 36개 분석 모듈로 단일 기업의 재무제표, 주석, 텍스트를 시계열로 추출
- Bridge Matching으로 동일 기업 내 계정명 변경 자동 추적
- 260+ 상장사 데이터 제공
- DART 전자공시 문서를 구조화된 데이터로 파싱하는 도구를 만드는 단계

**다음 단계** — 기업 간 비교
- 계정 표준화 엔진 도입 (eddmpython 타 프로젝트의 계정 매핑 노하우 활용)
- 전체 상장사 재무제표의 95% 이상 교차 비교 커버리지 목표
- 업종별, 규모별 그룹 비교 및 시장 전체 스크리닝

**텍스트 분석 고도화** — AI + 별도 프로젝트 연계
- 현재 별도 프로젝트에서 전문 텍스트 이해 패키지를 개발 중
- 공시 문서 텍스트의 시계열 비교, 섹션별 변경 추적, 의미 분석 등
- 추후 AI와 eddmpython의 텍스트 이해 패키지를 결합하여, 공시 문서의 모든 경우에 대응되는 범용 헬퍼로 DartLab에 투입할 예정
- 현재 DartLab이 파싱한 구조화 데이터 위에서 동작하는 지능형 분석 레이어가 최종 형태

**최종 목표** — 정량·정성 교차 검증
- 정량 변동과 정성 변화의 연결 (실적 악화 ↔ 위험 요인 텍스트 변화)
- 감사의견, 지배구조 변동 등 리스크 시그널 자동 탐지
- 종목 하나가 아니라 시장 전체를 한 번에 분석

## 로드맵

- [x] 요약재무정보 시계열 (Bridge Matching)
- [x] 연결재무제표 BS, IS, CF
- [x] 부문별 매출, 관계기업, 배당, 직원, 주주, 자회사
- [x] 채무증권, 비용 성격별 분류, 원재료/설비투자
- [x] 감사의견, 임원 현황, 임원 보수
- [x] 유형자산 변동표, 주석 세부항목 (23개 키워드)
- [x] 이사회, 자본금 변동, 우발부채, 대주주 거래, 제재, 연구개발, 내부통제
- [x] 계열회사, 증자/감자, 매출·수주, 주요 제품, 위험관리·파생거래
- [x] 경영진단의견, 사업의 내용, 회사의 개요
- [x] Company 통합 인터페이스
- [x] finance/disclosure 패키지 분리
- [ ] 계정 표준화 및 기업 간 교차 비교
- [ ] 텍스트 분석 모듈 통합 (별도 프로젝트에서 배치 예정)
- [ ] 정량 + 정성 교차 검증
- [ ] 시각화

## Sponsor

<a href="https://buymeacoffee.com/eddmpython">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180"/>
</a>

## 라이선스

MIT License
