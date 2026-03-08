---
title: 전체 모듈 상세
---

# 전체 모듈 상세

각 property가 어떤 DataFrame을 반환하는지, `get()`으로 접근 가능한 추가 데이터는 무엇인지 상세하게 다룬다.

> 모든 예제에서 `c = Company("005930")`으로 생성된 상태를 가정한다.

---

## c.dividend — 배당

배당 시계열. DPS, 배당성향, 배당수익률 등.

```python
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 연도 수 |
| `timeSeries` | `pl.DataFrame \| None` | 배당 시계열 |

---

## c.employee — 직원 현황

직원수, 평균연봉, 근속연수의 시계열이다.

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 연도 수 |
| `timeSeries` | `pl.DataFrame \| None` | 직원 현황 시계열 |

---

## c.majorHolder — 최대주주

최대주주와 특수관계인 지분율 시계열.

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

`get()`으로 전체 Result를 받으면 개별 주주 목록도 접근 가능하다.

```python
result = c.get("majorHolder")
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 합계 지분율
result.holders       # list[Holder] — 개별 주주 목록
```

### Holder

| 속성 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 주주명 |
| `relation` | `str` | 관계 |
| `stockType` | `str` | 주식 종류 |
| `sharesEnd` | `float \| None` | 기말 주식수 |
| `ratioEnd` | `float \| None` | 기말 지분율 |

---

## c.holderOverview — 주주 종합 현황

5% 이상 주주, 소액주주, 의결권 현황을 종합. 이 property는 Result 객체를 직접 반환한다.

```python
result = c.holderOverview

result.bigHolders    # list[BigHolder] — 5% 이상 주주
result.minority      # Minority — 소액주주 현황
result.voting        # VotingRights — 의결권 현황
```

---

## c.shareCapital — 주식의 총수

발행주식, 자기주식, 유통주식 시계열.

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

`get()`으로 전체 접근:

```python
result = c.get("shareCapital")
result.authorizedShares    # 발행할 주식의 총수
result.issuedShares        # 발행한 주식의 총수
result.treasuryShares      # 자기주식
result.outstandingShares   # 유통주식
result.treasuryRatio       # 자사주 비율
result.timeSeries          # 시계열 DataFrame
```

---

## c.executive — 임원 현황

등기임원 집계 시계열.

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | otherNonexec | maleCount | femaleCount
```

`get()`으로 미등기임원 보수도 접근 가능하다.

```python
result = c.get("executive")
result.executiveDf   # 등기임원 집계 시계열
result.unregPayDf    # 미등기임원 보수 시계열
```

### executiveDf 컬럼

| 컬럼 | 설명 |
|------|------|
| `totalRegistered` | 등기임원 총 수 |
| `insideDirectors` | 사내이사 |
| `outsideDirectors` | 사외이사 |
| `otherNonexec` | 기타비상무이사 |
| `fullTimeCount` | 상근 |
| `partTimeCount` | 비상근 |
| `maleCount` | 남성 |
| `femaleCount` | 여성 |

---

## c.executivePay — 임원 보수

유형별(등기이사/사외이사/감사위원) 보수 시계열.

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

`get()`으로 5억 초과 개인별 보수도 접근 가능하다.

```python
result = c.get("executivePay")
result.payByTypeDf   # 유형별 보수 시계열
result.topPayDf      # 5억 초과 개인별 보수
```

---

## c.audit — 감사의견

감사법인, 감사의견, 핵심감사사항 시계열.

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

`get()`으로 감사보수도 접근 가능하다.

```python
result = c.get("audit")
result.opinionDf   # 감사의견 시계열
result.feeDf       # 감사보수 시계열 (auditor, contractFee, contractHours, actualFee, actualHours)
```

---

## c.boardOfDirectors — 이사회

이사회 구성, 개최 횟수, 출석률 시계열.

```python
c.boardOfDirectors
# year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
```

`get()`으로 위원회 구성도 접근 가능하다.

```python
result = c.get("boardOfDirectors")
result.boardDf      # 이사회 시계열
result.committeeDf  # 위원회 구성 (committeeName, composition, members)
```

---

## c.capitalChange — 자본변동

자본금 변동, 주식의 총수, 자기주식 변동.

```python
c.capitalChange
# year | commonShares | preferredShares | commonParValue | ...
```

`get()`으로 추가 DataFrame 접근:

```python
result = c.get("capitalChange")
result.capitalDf     # 자본금 변동 시계열
result.shareTotalDf  # 주식의 총수 시계열
result.treasuryDf    # 자기주식 변동 시계열
```

---

## c.contingentLiability — 우발부채

채무보증·소송 현황.

```python
c.contingentLiability
# year | totalGuaranteeAmount | lineCount
```

`get()`으로 소송 현황도 접근 가능하다.

```python
result = c.get("contingentLiability")
result.guaranteeDf  # 채무보증 시계열
result.lawsuitDf    # 소송 현황 (filingDate, parties, description, amount, status)
```

---

## c.relatedPartyTx — 관계자거래

대주주 등과의 거래내용.

```python
c.relatedPartyTx
# year | entity | sales | purchases
```

`get()`으로 채무보증, 자산 거래도 접근 가능하다.

```python
result = c.get("relatedPartyTx")
result.revenueTxDf   # 매출입 거래 시계열
result.guaranteeDf   # 채무보증 시계열
result.assetTxDf     # 자산 거래 시계열
```

---

## c.rnd — R&D

연구개발비용과 매출액 대비 비율.

```python
c.rnd
# year | rndExpense | revenueRatio
```

---

## c.sanction — 제재

제재·처벌 현황.

```python
c.sanction
# year | date | agency | subject | action | amount | reason
```

---

## c.internalControl — 내부통제

내부회계관리제도 운영 실태 평가.

```python
c.internalControl
# year | opinion | auditor | hasWeakness
```

---

## c.affiliateGroup — 계열사

계열회사 현황.

```python
c.affiliateGroup
# name | listed
```

`get()`으로 추가 정보:

```python
result = c.get("affiliateGroup")
result.groupName      # "삼성"
result.listedCount    # 상장 계열사 수
result.unlistedCount  # 비상장 계열사 수
result.totalCount     # 총 계열사 수
result.affiliateDf    # 계열사 DataFrame
```

---

## c.subsidiary — 자회사

타법인 출자 종합 현황 시계열.

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

`get()`으로 개별 투자법인 접근:

```python
result = c.get("subsidiary")
for inv in result.investments[:5]:
    print(f"{inv.name}: {inv.endRatio}%, 장부가 {inv.endBook}")
```

---

## c.bond — 채무증권

회사채, 기업어음 등 채무증권 발행실적.

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

`get()`으로 개별 발행 내역:

```python
result = c.get("bond")
for b in result.issuances:
    print(f"{b.bondType} | {b.amount}백만원 | {b.interestRate} | {b.rating}")
```

---

## c.fundraising — 증자/감자

증자(감자) 현황.

```python
c.fundraising
# date | issueType | stockType | quantity | parValue | issuePrice | note
```

---

## c.productService — 주요 제품

주요 제품 및 서비스 현황.

```python
c.productService
# label | amount | ratio
```

---

## c.salesOrder — 매출/수주

매출실적(부문/제품별) + 수주상황.

```python
c.salesOrder
# label | v1 | v2 | v3
```

`get()`으로 수주 현황도 접근:

```python
result = c.get("salesOrder")
result.salesDf   # 매출실적
result.orderDf   # 수주상황
```

---

## c.riskDerivative — 위험관리

환율 민감도, 파생상품 계약 현황.

```python
c.riskDerivative
# currency | upImpact | downImpact
```

`get()`으로 파생상품 접근:

```python
result = c.get("riskDerivative")
result.fxDf          # 환율 민감도
result.derivativeDf  # 파생상품 계약
```

---

## c.articlesOfIncorporation — 정관

정관 변경 이력, 사업목적 현황.

```python
c.articlesOfIncorporation
# date | meetingName | changes | reason
```

`get()`으로 사업목적도 접근:

```python
result = c.get("articlesOfIncorporation")
result.changesDf    # 정관 변경 이력
result.purposesDf   # 사업목적 현황 (purpose, active)
```

---

## c.otherFinance — 기타재무

대손충당금, 재고자산 현황.

```python
c.otherFinance
# account | period | totalDebt | provision
```

`get()`으로 재고자산도 접근:

```python
result = c.get("otherFinance")
result.badDebtDf     # 대손충당금
result.inventoryDf   # 재고자산 현황
```

---

## c.companyHistory — 연혁

회사의 연혁 이벤트.

```python
c.companyHistory
# date | event
```

---

## c.shareholderMeeting — 주주총회

주주총회 안건, 결의 결과.

```python
c.shareholderMeeting
# agenda | result
```

---

## c.auditSystem — 감사제도

감사위원회 구성, 감사활동 내역.

```python
c.auditSystem
# name | role | detail
```

`get()`으로 감사활동 접근:

```python
result = c.get("auditSystem")
result.committeeDf   # 감사위원 구성
result.activityDf    # 감사활동 내역 (date, agenda, result)
```

---

## c.investmentInOther — 타법인출자

타법인출자 현황.

```python
c.investmentInOther
# name | 상장여부 | 최초취득일자 | 출자목적 | ...
```

---

## c.companyOverviewDetail — 회사 기본정보

`dict`를 반환한다 (DataFrame이 아님).

```python
info = c.companyOverviewDetail

info["foundedDate"]    # "1969-01-13"
info["listedDate"]     # "1975-06-11"
info["ceo"]            # "한종희"
info["address"]        # 본점소재지
info["mainBusiness"]   # 주요사업
info["website"]        # 홈페이지 URL
```

---

## K-IFRS 주석

`c.notes`로 통합 접근한다. 상세는 [API Overview](./overview)의 Notes 섹션 참고.

```python
c.notes.inventory          # 재고자산 DataFrame
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

한글로도 접근 가능하다.

```python
c.notes["재고자산"]         # c.notes.inventory와 동일
```

Notes의 데이터 소스 중 `notesDetail`은 23개 키워드를 지원한다. 12개 주요 키워드가 Notes에 등록되어 있고, 나머지 키워드는 직접 호출로 접근한다.

```python
# Notes 미등록 키워드 직접 조회
result = c.get("notesDetail", keyword="법인세")
result.tableDf
```

전체 23개 키워드: `재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

---

## 공시 텍스트

### c.business — 사업의 내용

섹션 리스트를 반환한다.

```python
sections = c.business
for s in sections:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])
```

주요 섹션 key: `overview`, `products`, `materials`, `sales`, `risk`, `rnd`, `financial`, `etc`

`get()`으로 연도별 변경 탐지도 접근:

```python
result = c.get("business")
for change in result.changes:
    print(f"{change.year}: 변경 {change.changedPct:.1%} | +{change.added}자 -{change.removed}자")
```

### c.mdna — MD&A

이사의 경영진단 및 분석의견. 개요 텍스트를 반환한다.

```python
c.mdna   # 사업 개요 텍스트
```

`get()`으로 전체 섹션 접근:

```python
result = c.get("mdna")
for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(f"  텍스트 {section.textLines}줄, 테이블 {section.tableLines}줄")
```

주요 category: `overview`, `forecast`, `financials`, `liquidity`

### c.overview — 회사의 개요

설립일, 주소, 신용등급 등 정량 데이터. Result 객체를 반환한다.

```python
result = c.overview

result.founded          # 설립 연도
result.address          # 소재지
result.homepage         # 홈페이지
result.subsidiaryCount  # 종속회사 수
result.isSME            # 중소기업 여부
result.isVenture        # 벤처기업 여부
result.listedDate       # 상장일
```

신용등급도 확인 가능하다.

```python
for cr in result.creditRatings:
    print(f"{cr.agency}: {cr.grade}")
```

### c.rawMaterial — 원재료/설비

원재료 매입, 유형자산, 설비투자 현황. Result 객체를 반환한다.

```python
result = c.rawMaterial

result.materials     # list[RawMaterial] — 원재료 목록
result.equipment     # Equipment — 유형자산 현황
result.capexItems    # list[CapexItem] — 설비투자 항목
```
