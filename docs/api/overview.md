---
title: API Overview
---

# API Overview

DartLab의 모든 데이터는 `Company` 클래스를 통해 접근한다. 대부분의 데이터는 **property**로 바로 DataFrame을 반환하며, 전체 Result 객체가 필요하면 `get()` 메서드를 사용한다.

## Company 클래스

### 생성

종목코드(6자리) 또는 회사명으로 생성한다. 데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

```python
from dartlab import Company

c = Company("005930")      # 종목코드로 생성
c = Company("삼성전자")     # 회사명으로 생성

c.corpName      # "삼성전자"
c.stockCode     # "005930"
```

생성하면 아바타와 함께 기업 정보가 터미널에 표시된다.

### 정적 메서드

Company를 생성하지 않고도 사용할 수 있는 메서드.

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `Company.search(query)` | `pl.DataFrame` | 종목 검색 (이름 부분 매칭) |
| `Company.listing()` | `pl.DataFrame` | KRX 전체 상장기업 목록 |
| `Company.status()` | `pl.DataFrame` | 로컬 보유 데이터 현황 |
| `Company.resolve(nameOrCode)` | `str \| None` | 종목코드 또는 회사명 → 종목코드 |
| `Company.codeName(code)` | `str \| None` | 종목코드 → 회사명 |

```python
# 종목 검색
Company.search("반도체")
# stockCode | corpName | market | sector | ...

# 로컬 데이터 현황
Company.status()
# stockCode | corpName | rows | yearFrom | yearTo | nDocs

# 전체 상장기업
Company.listing()
```

### 인스턴스 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `c.docs()` | `pl.DataFrame` | 공시 목록 + DART 뷰어 링크 |
| `c.all()` | `dict` | 전체 데이터 일괄 조회 (progress bar 표시) |
| `c.get(name)` | `Result` | 모듈별 전체 Result 객체 반환 |
| `c.guide()` | — | 사용 가능한 property 가이드 출력 |
| `c.fsSummary(period, ifrsOnly)` | `AnalysisResult` | 요약재무정보 + Bridge Matching |

```python
# 공시 목록
c.docs()
# year | reportType | rceptDate | rceptNo | dartUrl

# 전체 일괄 조회
d = c.all()   # 40개 모듈 + 12개 Notes를 dict로

# 가이드 출력
c.guide()     # 터미널에 예쁘게 출력
```

---

## property 전체 목록

property는 **lazy loading + caching**이다. 처음 접근할 때만 파싱하고, 이후 캐싱된 결과를 즉시 반환한다. 메서드 호출이 아닌 속성 접근이다.

```python
c = Company("005930")
c.BS          # ← 괄호 없음, property 접근
c.dividend    # ← 괄호 없음, property 접근
```

### 재무제표

핵심 3대 재무제표. 행은 계정항목, 열은 연도.

| property | 설명 | 반환 | 소스 |
|----------|------|------|------|
| `c.BS` | 재무상태표 | `pl.DataFrame` | statements |
| `c.IS` | 손익계산서 | `pl.DataFrame` | statements |
| `c.CF` | 현금흐름표 | `pl.DataFrame` | statements |

```python
c.BS
# account      | 2015  | 2016  | ... | 2024
# 자산총계     | ...   | ...   | ... | ...
# 유동자산     | ...   | ...   | ... | ...
# 비유동자산   | ...   | ...   | ... | ...
# 부채총계     | ...   | ...   | ... | ...
# 자본총계     | ...   | ...   | ... | ...
```

### 정기보고서

모든 정기보고서 데이터는 시계열 DataFrame을 반환한다.

| property | 설명 | 대표 컬럼 |
|----------|------|-----------|
| `c.dividend` | 배당 | dps, payoutRatio, dividendYield |
| `c.majorHolder` | 최대주주 | majorHolder, majorRatio, totalRatio |
| `c.employee` | 직원 현황 | totalEmployees, avgTenure, avgSalary |
| `c.subsidiary` | 자회사 | totalCount, listedCount, totalBook |
| `c.bond` | 채무증권 | totalIssuances, totalAmount |
| `c.shareCapital` | 주식총수 | issuedShares, treasuryShares |
| `c.executive` | 임원 현황 | insideDirectors, outsideDirectors |
| `c.executivePay` | 임원 보수 | category, totalPay, avgPay |
| `c.audit` | 감사의견 | auditor, opinion, keyAuditMatters |
| `c.boardOfDirectors` | 이사회 | meetingCount, avgAttendanceRate |
| `c.capitalChange` | 자본변동 | commonShares, preferredShares |
| `c.contingentLiability` | 우발부채 | totalGuaranteeAmount |
| `c.internalControl` | 내부통제 | opinion, hasWeakness |
| `c.relatedPartyTx` | 관계자거래 | entity, sales, purchases |
| `c.rnd` | R&D | rndExpense, revenueRatio |
| `c.sanction` | 제재 | agency, action, amount |
| `c.affiliateGroup` | 계열사 | name, listed |
| `c.fundraising` | 증자/감자 | issueType, quantity, issuePrice |
| `c.productService` | 주요제품 | label, amount, ratio |
| `c.salesOrder` | 매출/수주 | label, values |
| `c.riskDerivative` | 위험관리 | currency, upImpact, downImpact |
| `c.articlesOfIncorporation` | 정관 | date, changes, reason |
| `c.otherFinance` | 기타재무 | account, totalDebt, provision |
| `c.companyHistory` | 연혁 | date, event |
| `c.shareholderMeeting` | 주주총회 | agenda, result |
| `c.auditSystem` | 감사제도 | name, role |
| `c.investmentInOther` | 타법인출자 | name, 지분율, 장부가 |

```python
# 배당 시계열
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps

# 감사의견
c.audit
# year | auditor | opinion | keyAuditMatters

# 임원 현황
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | maleCount | femaleCount
```

### 특수 반환

DataFrame이 아닌 다른 타입을 반환하는 property.

| property | 설명 | 반환 타입 |
|----------|------|-----------|
| `c.companyOverviewDetail` | 회사 기본정보 | `dict` |
| `c.business` | 사업의 내용 | `list[Section]` |
| `c.mdna` | MD&A | `str \| None` |
| `c.overview` | 회사개요 정량 | Result 객체 |
| `c.rawMaterial` | 원재료/설비 | Result 객체 |
| `c.holderOverview` | 주주 종합 | Result 객체 |

```python
# 회사 기본정보 (dict)
info = c.companyOverviewDetail
info["foundedDate"]    # "1969-01-13"
info["listedDate"]     # "1975-06-11"
info["ceo"]            # 대표이사
info["address"]        # 본점소재지
info["website"]        # 홈페이지

# 사업의 내용 (섹션 리스트)
for s in c.business:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])

# MD&A (텍스트)
c.mdna   # 이사의 경영진단 및 분석의견

# 회사개요 정량 (Result 객체)
result = c.overview
result.founded          # 설립 연도
result.subsidiaryCount  # 종속회사 수
result.isSME            # 중소기업 여부
result.creditRatings    # 신용등급 리스트

# 주주 종합 (Result 객체)
result = c.holderOverview
result.bigHolders    # 5% 이상 주주 리스트
result.minority      # 소액주주 현황
result.voting        # 의결권 현황
```

---

## K-IFRS 주석 (Notes)

`c.notes`로 12개 K-IFRS 주석 항목에 통합 접근한다. 영문 속성과 한글 딕셔너리 키 모두 지원한다.

### 지원 항목

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

```python
# 영문 속성
c.notes.inventory    # 재고자산 DataFrame

# 한글 키
c.notes["재고자산"]   # 위와 동일
```

### Notes 메서드

| 메서드 | 설명 |
|--------|------|
| `c.notes.keys()` | 영문 속성명 목록 |
| `c.notes.keys_kr()` | 한글 키워드 목록 |
| `c.notes.all()` | 전체 주석을 dict로 반환 |

### 미등록 키워드 직접 조회

12개 주요 키워드 외에도 23개 키워드를 지원한다. Notes에 등록되지 않은 키워드는 `get()`으로 직접 호출한다.

```python
result = c.get("notesDetail", keyword="법인세")
result.tableDf   # 법인세 관련 주석 테이블

result = c.get("notesDetail", keyword="특수관계자")
result.tableDf   # 특수관계자 거래 테이블
```

전체 23개 키워드: `재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

---

## property vs get()

property는 대표 DataFrame **하나**를 반환한다. 모듈에 따라 복수의 DataFrame이 있을 수 있는데, 전체가 필요하면 `get()`으로 원본 Result 객체를 받는다.

### 기본 패턴

```python
# property — 대표 DataFrame 하나
c.audit           # → opinionDf만 반환

# get() — 전체 Result 객체
result = c.get("audit")
result.opinionDf  # 감사의견
result.feeDf      # 감사보수 (추가 DataFrame)
```

### 복수 DataFrame을 가진 모듈

| property | 대표 DataFrame | get()으로 추가 접근 가능 |
|----------|---------------|-------------------------|
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
| `boardOfDirectors` | `boardDf` | `committeeDf` |

```python
# 관계자거래 — property는 매출입 거래만
c.relatedPartyTx   # revenueTxDf

# get()으로 채무보증, 자산거래까지
result = c.get("relatedPartyTx")
result.revenueTxDf    # 매출입 거래
result.guaranteeDf    # 채무보증
result.assetTxDf      # 자산 거래
```

---

## all()

전체 데이터를 한 번에 dict로 받는다. 40개 모듈 + 12개 Notes를 순회하며 progress bar가 표시된다.

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
d["audit"]           # 감사의견

# K-IFRS 주석
d["notes"]["inventory"]    # 재고자산
d["notes"]["borrowings"]   # 차입금
d["notes"]["segments"]     # 부문정보
```

---

## verbose 설정

```python
import dartlab

dartlab.verbose = False    # 진행 표시 끄기
dartlab.verbose = True     # 다시 켜기 (기본값)
```

`False`로 설정하면 Company 생성 시 아바타 출력, property 접근 시 진행 표시, `all()` 호출 시 progress bar 모두 비활성화된다.

---

## period 파라미터

일부 모듈은 `period` 파라미터로 분석 단위를 변경할 수 있다. property 접근은 연간(`"y"`) 기본값을 사용한다.

| 값 | 의미 | 포함 보고서 |
|-----|------|------------|
| `"y"` | 연간 (기본값) | 사업보고서 |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 |
| `"h"` | 반기별 | 반기 + 사업 |

지원 모듈: `fsSummary`, `statements`, `segments`, `costByNature`, `affiliates`, `notesDetail`

```python
# fsSummary — 유일하게 메서드로 호출
c.fsSummary(period="q")              # 분기별 요약재무

# get()으로 period 전달
c.get("segments", period="q")        # 분기별 부문정보
c.get("costByNature", period="q")    # 분기별 비용분류
c.get("statements", period="q")      # 분기별 재무제표
```

---

## 함수 직접 호출

Company 클래스 없이 모듈 함수를 직접 호출할 수도 있다. 전체 Result 객체를 반환한다.

```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend

result = fsSummary("005930")     # AnalysisResult
result = statements("005930")   # StatementsResult
result = dividend("005930")     # DividendResult
```

---

## 유틸리티

```python
from dartlab.core import loadData, buildIndex, downloadAll, extractCorpName

loadData("005930")       # Parquet 로드 (없으면 자동 다운로드)
buildIndex()             # 전체 종목 인덱스 생성
downloadAll()            # 전체 데이터 일괄 다운로드
extractCorpName(df)      # DataFrame에서 기업명 추출
```
