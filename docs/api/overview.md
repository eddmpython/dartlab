---
title: API Overview
---

# API Overview

DartLab의 모든 데이터는 `Company` 클래스를 통해 접근한다. 대부분의 데이터는 property로 바로 DataFrame을 반환하며, 전체 Result 객체가 필요하면 `get()` 메서드를 사용한다.

## Company 클래스

```python
from dartlab import Company

c = Company("005930")
c.corpName      # "삼성전자"
c.stockCode     # "005930"
```

종목코드(6자리) 또는 회사명으로 생성한다. 데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

### 정적 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `Company.search(query)` | `list[dict]` | 종목 검색 (이름 또는 코드) |
| `Company.listing()` | `pl.DataFrame` | 전체 상장기업 목록 |
| `Company.status()` | `pl.DataFrame` | 로컬 보유 데이터 현황 |
| `Company.resolve(nameOrCode)` | `str` | 종목코드 해석 |
| `Company.codeName(code)` | `str` | 종목코드 → 회사명 |

### 인스턴스 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `c.docs()` | `pl.DataFrame` | 공시 목록 + DART 뷰어 링크 |
| `c.all()` | `dict` | 전체 데이터 일괄 조회 |
| `c.get(name)` | `Result` | 모듈별 전체 Result 객체 |
| `c.guide()` | — | 사용 가능한 property 가이드 출력 |
| `c.fsSummary(period, ifrsOnly)` | `AnalysisResult` | 요약재무정보 (파라미터 있는 유일한 메서드) |

## Property 전체 목록

property는 lazy loading + caching이다. 처음 접근할 때 파싱하고 이후 캐싱한다.

### 재무제표

| property | 설명 | 반환 |
|----------|------|------|
| `c.BS` | 재무상태표 | `pl.DataFrame` |
| `c.IS` | 손익계산서 | `pl.DataFrame` |
| `c.CF` | 현금흐름표 | `pl.DataFrame` |

Bridge Matching으로 계정명 변경을 자동 추적한다. 행은 계정항목, 열은 연도.

### 정기보고서

| property | 설명 | 대표 DataFrame |
|----------|------|----------------|
| `c.dividend` | 배당 | `timeSeries` — dps, payoutRatio, dividendYield |
| `c.majorHolder` | 최대주주 | `timeSeries` — majorHolder, majorRatio, totalRatio |
| `c.employee` | 직원 현황 | `timeSeries` — totalEmployees, avgTenure, avgSalary |
| `c.subsidiary` | 자회사 | `timeSeries` — totalCount, listedCount, totalBook |
| `c.bond` | 채무증권 | `timeSeries` — totalIssuances, totalAmount |
| `c.shareCapital` | 주식총수 | `timeSeries` — issuedShares, treasuryShares |
| `c.executive` | 임원 현황 | `executiveDf` — insideDirectors, outsideDirectors |
| `c.executivePay` | 임원 보수 | `payByTypeDf` — category, totalPay, avgPay |
| `c.audit` | 감사의견 | `opinionDf` — auditor, opinion |
| `c.boardOfDirectors` | 이사회 | `boardDf` — meetingCount, avgAttendanceRate |
| `c.capitalChange` | 자본변동 | `capitalDf` — commonShares, preferredShares |
| `c.contingentLiability` | 우발부채 | `guaranteeDf` — totalGuaranteeAmount |
| `c.internalControl` | 내부통제 | `controlDf` — opinion, hasWeakness |
| `c.relatedPartyTx` | 관계자거래 | `revenueTxDf` — entity, sales, purchases |
| `c.rnd` | R&D | `rndDf` — rndExpense, revenueRatio |
| `c.sanction` | 제재 | `sanctionDf` — agency, action, amount |
| `c.affiliateGroup` | 계열사 | `affiliateDf` — name, listed |
| `c.fundraising` | 증자/감자 | `issuanceDf` — issueType, quantity, issuePrice |
| `c.productService` | 주요제품 | `productDf` — label, amount, ratio |
| `c.salesOrder` | 매출/수주 | `salesDf` — label, values |
| `c.riskDerivative` | 위험관리 | `fxDf` — currency, upImpact, downImpact |
| `c.articlesOfIncorporation` | 정관 | `changesDf` — date, changes, reason |
| `c.otherFinance` | 기타재무 | `badDebtDf` — account, totalDebt, provision |
| `c.companyHistory` | 연혁 | `eventsDf` — date, event |
| `c.shareholderMeeting` | 주주총회 | `agendaDf` — agenda, result |
| `c.auditSystem` | 감사제도 | `committeeDf` — name, role |
| `c.investmentInOther` | 타법인출자 | `investmentDf` — name, 지분율, 장부가 |

### 특수 반환

| property | 설명 | 반환 타입 |
|----------|------|-----------|
| `c.companyOverviewDetail` | 회사 기본정보 | `dict` (foundedDate, listedDate, ceo, address, website) |
| `c.business` | 사업의 내용 | `list[Section]` |
| `c.mdna` | MD&A | 텍스트 (overview) |
| `c.overview` | 회사개요 정량 | Result 객체 |
| `c.rawMaterial` | 원재료/설비 | Result 객체 |
| `c.holderOverview` | 주주 종합 | Result 객체 (5% 이상, 소액주주, 의결권) |

### K-IFRS 주석 (Notes)

`c.notes`로 통합 접근한다. 영문 속성, 한글 딕셔너리 키 모두 지원한다.

| 영문 속성 | 한글 키 | 데이터 소스 |
|-----------|---------|------------|
| `c.notes.receivables` | `c.notes["매출채권"]` | notesDetail |
| `c.notes.inventory` | `c.notes["재고자산"]` | notesDetail |
| `c.notes.tangibleAsset` | `c.notes["유형자산"]` | tangibleAsset |
| `c.notes.intangibleAsset` | `c.notes["무형자산"]` | notesDetail |
| `c.notes.investmentProperty` | `c.notes["투자부동산"]` | notesDetail |
| `c.notes.affiliates` | `c.notes["관계기업"]` | affiliates |
| `c.notes.borrowings` | `c.notes["차입금"]` | notesDetail |
| `c.notes.provisions` | `c.notes["충당부채"]` | notesDetail |
| `c.notes.eps` | `c.notes["주당이익"]` | notesDetail |
| `c.notes.lease` | `c.notes["리스"]` | notesDetail |
| `c.notes.segments` | `c.notes["부문정보"]` | segments |
| `c.notes.costByNature` | `c.notes["비용의성격별분류"]` | costByNature |

Notes 메서드:

| 메서드 | 설명 |
|--------|------|
| `c.notes.keys()` | 영문 속성명 목록 |
| `c.notes.keys_kr()` | 한글 키워드 목록 |
| `c.notes.all()` | 전체 주석을 dict로 반환 |

## property vs get()

property는 대표 DataFrame 하나를 반환한다. 모듈에 따라 복수의 DataFrame이 있을 수 있는데, 전체가 필요하면 `get()`으로 원본 Result 객체를 받는다.

```python
# property — 대표 DataFrame 하나
c.audit           # → opinionDf

# get() — 전체 Result 객체
result = c.get("audit")
result.opinionDf  # 감사의견
result.feeDf      # 감사보수 (추가 DataFrame)
```

복수 DataFrame을 가진 모듈 예시:

| property | 대표 | get()으로 추가 접근 가능 |
|----------|------|-------------------------|
| `audit` | `opinionDf` | `feeDf` |
| `executive` | `executiveDf` | `unregPayDf` |
| `capitalChange` | `capitalDf` | `shareTotalDf`, `treasuryDf` |
| `contingentLiability` | `guaranteeDf` | `lawsuitDf` |
| `relatedPartyTx` | `revenueTxDf` | `guaranteeDf`, `assetTxDf` |
| `riskDerivative` | `fxDf` | `derivativeDf` |
| `articlesOfIncorporation` | `changesDf` | `purposesDf` |
| `otherFinance` | `badDebtDf` | `inventoryDf` |
| `salesOrder` | `salesDf` | `orderDf` |
| `auditSystem` | `committeeDf` | `activityDf` |

## all()

전체 데이터를 한 번에 dict로 받는다. progress bar가 표시된다.

```python
d = c.all()

# 재무제표
d["BS"]       # 재무상태표
d["IS"]       # 손익계산서
d["CF"]       # 현금흐름표

# 정기보고서
d["dividend"]        # 배당
d["majorHolder"]     # 최대주주
d["employee"]        # 직원

# K-IFRS 주석
d["notes"]["inventory"]    # 재고자산
d["notes"]["borrowings"]   # 차입금
```

## verbose 설정

```python
import dartlab

dartlab.verbose = False    # 진행 표시 끄기
dartlab.verbose = True     # 다시 켜기 (기본값)
```

## period 파라미터

`fsSummary`, `statements`, `segments`, `costByNature`, `affiliates`, `notesDetail`은 `period` 파라미터를 지원한다. property 접근(예: `c.BS`)은 연간 기본값을 사용하며, 분기/반기가 필요하면 메서드를 직접 호출한다.

```python
c.fsSummary(period="q")              # 분기별 요약재무
c.get("segments", period="q")        # 분기별 부문정보
c.get("costByNature", period="q")    # 분기별 비용분류
```

## 함수 직접 호출

Company 클래스 없이 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend

result = fsSummary("005930")
result = statements("005930")
result = dividend("005930")
```

## 유틸리티

```python
from dartlab.core import loadData, buildIndex, downloadAll, extractCorpName

loadData("005930")       # Parquet 로드 (없으면 자동 다운로드)
buildIndex()             # 전체 종목 인덱스 생성
downloadAll()            # 전체 데이터 일괄 다운로드
```
