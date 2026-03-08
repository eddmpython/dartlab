---
title: 빠른 시작
---

# 빠른 시작

DartLab은 DART 전자공시 문서를 분석하는 Python 라이브러리다. 종목코드 하나로 재무제표, 주석, 정기보고서, 텍스트를 구조화된 DataFrame으로 받는다.

## 설치

```bash
pip install dartlab
```

> uv 사용 시: `uv add dartlab`. Python 3.12 이상 필요.

---

## Company 생성

모든 분석의 시작점이다. 종목코드 또는 회사명으로 생성한다.

```python
from dartlab import Company

c = Company("005930")
c.corpName   # "삼성전자"
c.stockCode  # "005930"
```

회사명으로도 생성할 수 있다.

```python
c = Company("카카오")
c.stockCode  # "035720"
```

생성 시 아바타와 기업 정보가 터미널에 표시된다. 데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

---

## 재무제표

property 하나로 바로 DataFrame을 받는다. 괄호 없이 속성처럼 접근한다.

```python
c.BS   # 재무상태표 (Balance Sheet)
c.IS   # 손익계산서 (Income Statement)
c.CF   # 현금흐름표 (Cash Flow)
```

모두 Polars DataFrame이며, 행은 계정항목, 열은 연도다.

```python
print(c.BS)
# account      | 2015       | 2016       | ... | 2024
# 자산총계     | 262,174,324| 261,381,064| ... | ...
# 유동자산     | 124,140,661| 134,506,949| ... | ...
# 비유동자산   | 138,033,663| 126,874,115| ... | ...
# 부채총계     | 63,119,716 | 54,704,095 | ... | ...
# 자본총계     | 199,054,608| 206,676,969| ... | ...
```

### 분기별 / 반기별

`fsSummary()` 메서드로 기간을 변경한다. Bridge Matching으로 계정명 변경을 자동 추적한다.

```python
result = c.fsSummary(period="q")  # 분기별
result.BS    # 분기별 재무상태표
result.IS    # 분기별 손익계산서
```

| 값 | 의미 | 포함 보고서 |
|-----|------|------------|
| `"y"` | 연간 (기본값) | 사업보고서 |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 |
| `"h"` | 반기별 | 반기 + 사업 |

---

## 정기보고서

배당, 직원, 최대주주 등 정기보고서 데이터도 property로 바로 접근한다. 모든 property는 lazy loading + caching이다.

### 배당

```python
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

연도별 DPS, 배당수익률, 배당성향을 시계열로 확인한다.

### 직원 현황

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

총 직원수, 평균 근속연수, 평균 연봉의 시계열이다.

### 최대주주

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | ...
```

최대주주명, 지분율, 특수관계인 합계 지분율의 시계열이다.

### 감사의견

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

감사법인, 감사의견, 핵심감사사항을 연도별로 추적한다.

### 임원 현황

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | maleCount | femaleCount
```

등기임원 구성, 사내이사/사외이사 비율, 성별 구성을 시계열로 본다.

### 임원 보수

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

유형별(등기이사/사외이사/감사위원) 보수 시계열이다.

### 전체 property 목록

한 줄로 접근 가능한 전체 목록이다.

| property | 설명 | 주요 컬럼 |
|----------|------|-----------|
| `c.dividend` | 배당 | dps, payoutRatio, dividendYield |
| `c.majorHolder` | 최대주주 | majorHolder, majorRatio |
| `c.employee` | 직원 | totalEmployees, avgSalary |
| `c.executive` | 임원 | insideDirectors, outsideDirectors |
| `c.executivePay` | 임원보수 | category, totalPay, avgPay |
| `c.audit` | 감사의견 | auditor, opinion |
| `c.subsidiary` | 자회사 | totalCount, totalBook |
| `c.bond` | 채무증권 | totalIssuances, totalAmount |
| `c.shareCapital` | 주식총수 | issuedShares, treasuryShares |
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
| `c.companyOverviewDetail` | 회사개요 | foundedDate, ceo, address |

---

## K-IFRS 주석 (Notes)

재무제표 주석 데이터는 `c.notes`로 통합 접근한다. 12개 항목을 지원하며, 영문 속성과 한글 키 모두 사용할 수 있다.

### 영문 속성

```python
c.notes.inventory          # 재고자산
c.notes.receivables        # 매출채권
c.notes.borrowings         # 차입금
c.notes.tangibleAsset      # 유형자산 변동표
c.notes.intangibleAsset    # 무형자산
c.notes.provisions         # 충당부채
c.notes.eps                # 주당이익
c.notes.lease              # 리스
c.notes.investmentProperty # 투자부동산
c.notes.affiliates         # 관계기업
c.notes.segments           # 부문정보
c.notes.costByNature       # 비용의 성격별 분류
```

### 한글 키

```python
c.notes["재고자산"]         # c.notes.inventory와 동일
c.notes["차입금"]           # c.notes.borrowings와 동일
```

### 전체 조회

```python
c.notes.keys()     # 영문 속성명 목록
c.notes.keys_kr()  # 한글 키워드 목록
c.notes.all()      # 모든 항목을 dict로
```

---

## 공시 텍스트

숫자 뒤에 숨겨진 텍스트도 분석한다.

### 사업의 내용

```python
sections = c.business
for s in sections:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])
```

### MD&A

```python
c.mdna   # 이사의 경영진단 및 분석의견 텍스트
```

### 회사 개요

```python
c.overview       # 설립연도, 소재지, 신용등급, 종속회사 수 등 정량 데이터
c.rawMaterial    # 원재료 매입, 유형자산, 설비투자 현황
```

---

## 전체 일괄 조회

`all()`을 호출하면 모든 모듈을 순회하면서 전체 데이터를 dict로 반환한다. 진행 상황이 progress bar로 표시된다.

```python
d = c.all()

d["BS"]                  # 재무상태표
d["IS"]                  # 손익계산서
d["CF"]                  # 현금흐름표
d["dividend"]            # 배당
d["notes"]["inventory"]  # 재고자산
# ...40개 모듈 전체
```

---

## 가이드 출력

`guide()`를 호출하면 사용 가능한 property 목록이 터미널에 예쁘게 출력된다.

```python
c.guide()
```

---

## Result 객체 접근

property는 대표 DataFrame 하나를 반환한다. 해당 모듈의 전체 데이터가 필요하면 `get()` 메서드로 원본 Result 객체를 받는다.

```python
# property → 대표 DataFrame
c.audit   # opinionDf만 반환

# get() → 전체 Result 객체
result = c.get("audit")
result.opinionDf   # 감사의견
result.feeDf       # 감사보수 (property로는 안 보이는 추가 데이터)
```

이 방법으로 하나의 모듈에서 복수의 DataFrame을 모두 확인할 수 있다.

---

## 유틸리티

### 종목 검색

```python
Company.search("반도체")     # 키워드로 검색
Company.listing()            # 전체 상장기업 목록
Company.status()             # 로컬 보유 데이터 현황
```

### 공시 목록

```python
c.docs()
# year | reportType | rceptDate | rceptNo | dartUrl
```

해당 종목의 공시 목록과 DART 뷰어 링크를 조회한다.

---

## 진행 표시 끄기

```python
import dartlab

dartlab.verbose = False      # 전역 설정
c = Company("005930")        # 조용히 생성
d = c.all()                  # progress bar 없이 실행
```

---

## 다음 단계

- [API Reference](../api/overview) — property 전체 목록과 Result 타입 상세
- [Bridge Matching](../user-guide/bridge-matching) — 시계열 매칭 알고리즘 상세
- [Tutorial: Financial Deep Dive](../tutorials/financial) — 배당, 직원, 최대주주 심화 분석
