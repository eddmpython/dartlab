---
title: 전체 모듈 상세
---

# 전체 모듈 상세

`Company`의 공개 기본 경로는 `sections → show → trace`다. 이 문서는 그보다 한 단계 아래의 report/docs source namespace를 참고용으로 정리한 것이다.

> **⚠️ `c.report.extract(topic)`은 내부 API다.** 일상 분석은 `c.show(topic)`을 쓴다.
> 아래 예제의 `c.report.extract()` 호출은 `c.report.extract(topic)` 또는 `c.docs.notes`로 접근하는 deep access 패턴이다.
>
> ```python
> # 권장 경로
> c.show("dividend")           # show()가 source 우선순위 적용
> c.show("audit")
>
> # deep access (report namespace 직접)
> c.report.extract("dividend") # report Result 객체
> c.docs.notes.inventory       # K-IFRS 주석 직접
> ```

---

## 배당·주주·자본 구조

### c.dividend — 배당

배당 시계열. DPS, 배당성향, 배당수익률 등.

```python
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

**Result 속성:**

| 속성 | 타입 | 설명 |
|------|------|------|
| `corpName` | `str \| None` | 기업명 |
| `nYears` | `int` | 연도 수 |
| `timeSeries` | `pl.DataFrame \| None` | 배당 시계열 |

**활용 예시:**

```python
# 최근 배당 정보
div = c.dividend
if div is not None:
    last = div.row(-1, named=True)
    print(f"DPS: {last['dps']}원, 배당수익률: {last['dividendYield']}%")
```

---

### c.majorHolder — 최대주주

최대주주와 특수관계인 지분율 시계열.

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

report namespace로 개별 주주 목록 접근:

```python
result = c.report.extract("majorHolder")  # 또는 c.show("majorHolder")
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 합계 지분율
result.holders       # list[Holder] — 개별 주주 목록
```

**Holder 속성:**

| 속성 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 주주명 |
| `relation` | `str` | 관계 (본인, 친인척, 임원 등) |
| `stockType` | `str` | 주식 종류 |
| `sharesEnd` | `float \| None` | 기말 주식수 |
| `ratioEnd` | `float \| None` | 기말 지분율 (%) |

**활용 예시:**

```python
result = c.report.extract("majorHolder")
print(f"최대주주: {result.majorHolder} ({result.majorRatio}%)")
for h in result.holders:
    print(f"  {h.name} ({h.relation}): {h.ratioEnd}%")
```

---

### c.holderOverview — 주주 종합 현황

5% 이상 주주, 소액주주, 의결권 현황을 종합. Result 객체를 직접 반환한다.

```python
result = c.holderOverview

result.bigHolders    # list[BigHolder] — 5% 이상 주주
result.minority      # Minority — 소액주주 현황
result.voting        # VotingRights — 의결권 현황
```

**활용 예시:**

```python
result = c.holderOverview
for bh in result.bigHolders:
    print(f"{bh.name}: {bh.ratio}%")
print(f"소액주주 비율: {result.minority.ratio}%")
```

---

### c.shareCapital — 주식의 총수

발행주식, 자기주식, 유통주식 시계열.

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

report namespace로 전체 접근:

```python
result = c.report.extract("shareCapital")
result.authorizedShares    # 발행할 주식의 총수
result.issuedShares        # 발행한 주식의 총수
result.treasuryShares      # 자기주식
result.outstandingShares   # 유통주식
result.treasuryRatio       # 자사주 비율
result.timeSeries          # 시계열 DataFrame
```

---

### c.capitalChange — 자본변동

자본금 변동, 주식의 총수, 자기주식 변동.

```python
c.capitalChange
# year | commonShares | preferredShares | commonParValue | ...
```

report namespace로 추가 DataFrame:

```python
result = c.report.extract("capitalChange")
result.capitalDf     # 자본금 변동 시계열
result.shareTotalDf  # 주식의 총수 시계열
result.treasuryDf    # 자기주식 변동 시계열
```

---

### c.fundraising — 증자/감자

증자(감자) 현황.

```python
c.fundraising
# date | issueType | stockType | quantity | parValue | issuePrice | note
```

---

## 임원·거버넌스

### c.executive — 임원 현황

등기임원 집계 시계열.

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | otherNonexec | maleCount | femaleCount
```

report namespace로 미등기임원 보수 접근:

```python
result = c.report.extract("executive")
result.executiveDf   # 등기임원 집계 시계열
result.unregPayDf    # 미등기임원 보수 시계열
```

**executiveDf 주요 컬럼:**

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

### c.executivePay — 임원 보수

유형별(등기이사/사외이사/감사위원) 보수 시계열.

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

report namespace로 5억 초과 개인별 보수:

```python
result = c.report.extract("executivePay")
result.payByTypeDf   # 유형별 보수 시계열
result.topPayDf      # 5억 초과 개인별 보수
```

---

### c.boardOfDirectors — 이사회

이사회 구성, 개최 횟수, 출석률 시계열.

```python
c.boardOfDirectors
# year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
```

report namespace로 위원회 구성:

```python
result = c.report.extract("boardOfDirectors")
result.boardDf      # 이사회 시계열
result.committeeDf  # 위원회 구성 (committeeName, composition, members)
```

---

### c.audit — 감사의견

감사법인, 감사의견, 핵심감사사항 시계열.

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

report namespace로 감사보수:

```python
result = c.report.extract("audit")
result.opinionDf   # 감사의견 시계열
result.feeDf       # 감사보수 시계열 (auditor, contractFee, contractHours, actualFee, actualHours)
```

---

### c.auditSystem — 감사제도

감사위원회 구성, 감사활동 내역.

```python
c.auditSystem
# name | role | detail
```

report namespace로 감사활동:

```python
result = c.report.extract("auditSystem")
result.committeeDf   # 감사위원 구성
result.activityDf    # 감사활동 내역 (date, agenda, result)
```

---

### c.internalControl — 내부통제

내부회계관리제도 운영 실태 평가.

```python
c.internalControl
# year | opinion | auditor | hasWeakness
```

---

### c.shareholderMeeting — 주주총회

주주총회 안건, 결의 결과.

```python
c.shareholderMeeting
# agenda | result
```

---

## 리스크·규제

### c.contingentLiability — 우발부채

채무보증·소송 현황.

```python
c.contingentLiability
# year | totalGuaranteeAmount | lineCount
```

report namespace로 소송 현황:

```python
result = c.report.extract("contingentLiability")
result.guaranteeDf  # 채무보증 시계열
result.lawsuitDf    # 소송 현황 (filingDate, parties, description, amount, status)
```

---

### c.relatedPartyTx — 관계자거래

대주주 등과의 거래내용.

```python
c.relatedPartyTx
# year | entity | sales | purchases
```

report namespace로 채무보증, 자산 거래:

```python
result = c.report.extract("relatedPartyTx")
result.revenueTxDf   # 매출입 거래 시계열
result.guaranteeDf   # 채무보증 시계열
result.assetTxDf     # 자산 거래 시계열
```

---

### c.sanction — 제재

제재·처벌 현황.

```python
c.sanction
# year | date | agency | subject | action | amount | reason
```

---

### c.riskDerivative — 위험관리

환율 민감도, 파생상품 계약 현황.

```python
c.riskDerivative
# currency | upImpact | downImpact
```

report namespace로 파생상품:

```python
result = c.report.extract("riskDerivative")
result.fxDf          # 환율 민감도
result.derivativeDf  # 파생상품 계약
```

---

## 사업·제품·매출

### c.employee — 직원 현황

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

**활용 예시:**

```python
emp = c.employee
if emp is not None:
    last = emp.row(-1, named=True)
    print(f"직원수: {last['totalEmployees']:,}명, 평균연봉: {last['avgSalary']:,.0f}백만원")
```

---

### c.productService — 주요 제품

주요 제품 및 서비스 현황.

```python
c.productService
# label | amount | ratio
```

---

### c.salesOrder — 매출/수주

매출실적(부문/제품별) + 수주상황.

```python
c.salesOrder
# label | v1 | v2 | v3
```

report namespace로 수주 현황:

```python
result = c.report.extract("salesOrder")
result.salesDf   # 매출실적
result.orderDf   # 수주상황
```

---

### c.rnd — R&D

연구개발비용과 매출액 대비 비율.

```python
c.rnd
# year | rndExpense | revenueRatio
```

---

## 재무·자산

### c.subsidiary — 자회사

타법인 출자 종합 현황 시계열.

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

report namespace로 개별 투자법인:

```python
result = c.report.extract("subsidiary")
for inv in result.investments[:5]:
    print(f"{inv.name}: {inv.endRatio}%, 장부가 {inv.endBook}")
```

---

### c.bond — 채무증권

회사채, 기업어음 등 채무증권 발행실적.

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

report namespace로 개별 발행 내역:

```python
result = c.report.extract("bond")
for b in result.issuances:
    print(f"{b.bondType} | {b.amount}백만원 | {b.interestRate} | {b.rating}")
```

---

### c.otherFinance — 기타재무

대손충당금, 재고자산 현황.

```python
c.otherFinance
# account | period | totalDebt | provision
```

report namespace로 재고자산:

```python
result = c.report.extract("otherFinance")
result.badDebtDf     # 대손충당금
result.inventoryDf   # 재고자산 현황
```

---

### c.investmentInOther — 타법인출자

타법인출자 현황.

```python
c.investmentInOther
# name | 상장여부 | 최초취득일자 | 출자목적 | ...
```

---

## 회사 정보

### c.companyOverviewDetail — 회사 기본정보

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

### c.affiliateGroup — 계열사

계열회사 현황.

```python
c.affiliateGroup
# name | listed
```

report namespace로 추가 정보:

```python
result = c.report.extract("affiliateGroup")
result.groupName      # "삼성"
result.listedCount    # 상장 계열사 수
result.unlistedCount  # 비상장 계열사 수
result.totalCount     # 총 계열사 수
result.affiliateDf    # 계열사 DataFrame
```

---

### c.companyHistory — 연혁

회사의 연혁 이벤트.

```python
c.companyHistory
# date | event
```

---

### c.articlesOfIncorporation — 정관

정관 변경 이력, 사업목적 현황.

```python
c.articlesOfIncorporation
# date | meetingName | changes | reason
```

report namespace로 사업목적:

```python
result = c.report.extract("articlesOfIncorporation")
result.changesDf    # 정관 변경 이력
result.purposesDf   # 사업목적 현황 (purpose, active)
```

---

## 공시 텍스트

> **권장 경로**: 공시 서술형 텍스트는 `c.show("businessOverview")`, `c.show("companyOverview")` 등 sections 기반 show()로 접근한다.
> 아래 `c.business`, `c.mdna`는 docs namespace의 legacy 접근 경로다.

### c.docs.business — 사업의 내용

```python
biz = c.docs.business
for s in biz:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])
```

**주요 섹션 key:**

| key | 설명 |
|-----|------|
| `overview` | 사업 개요 |
| `products` | 주요 제품·서비스 |
| `materials` | 원재료·가격변동 |
| `sales` | 매출·수주 현황 |
| `risk` | 위험 요인 |
| `rnd` | 연구개발 현황 |
| `financial` | 재무 관련 사항 |
| `etc` | 기타 참고사항 |

---

### c.docs.mdna — MD&A

이사의 경영진단 및 분석의견.

```python
c.docs.mdna   # 사업 개요 텍스트
```

---

### c.docs.overview — 회사의 개요

설립일, 주소, 신용등급 등 정량 데이터. Result 객체를 반환한다.

```python
result = c.docs.overview

result.founded          # 설립 연도
result.address          # 소재지
result.homepage         # 홈페이지
result.subsidiaryCount  # 종속회사 수
result.isSME            # 중소기업 여부
result.isVenture        # 벤처기업 여부
result.listedDate       # 상장일
```

신용등급 확인:

```python
for cr in result.creditRatings:
    print(f"{cr.agency}: {cr.grade}")
```

파싱 상태 확인:

```python
print(f"원문에 없음: {result.missing}")
print(f"파싱 실패: {result.failed}")
```

---

### c.docs.rawMaterial — 원재료/설비

원재료 매입, 유형자산, 설비투자 현황. Result 객체를 반환한다.

```python
result = c.docs.rawMaterial

result.materials     # list[RawMaterial] — 원재료 목록
result.equipment     # Equipment — 유형자산 현황
result.capexItems    # list[CapexItem] — 설비투자 항목
```

**활용 예시:**

```python
result = c.rawMaterial
for m in result.materials:
    print(f"{m.item}: {m.amount}백만원 ({m.ratio}%) — {m.supplier}")

eq = result.equipment
print(f"합계: {eq.total}, CAPEX: {eq.capex}")
```

---

## K-IFRS 주석 (Notes)

`c.notes`로 통합 접근한다. 상세는 [API Overview](./overview)의 Notes 섹션 참고.

### 12개 주요 항목

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

### 한글 키 접근

```python
c.notes["재고자산"]         # c.notes.inventory와 동일
```

### 유형자산 변동표

```python
result = c.notes.tangibleAsset
result.reliability    # "high" 또는 "low"
result.warnings       # 신뢰도 경고
result.movementDf     # 카테고리별 기초/기말 시계열
```

### 부문정보

```python
result = c.notes.segments
result.revenue   # 부문별 매출 시계열 DataFrame
for year, tables in result.tables.items():
    for t in tables:
        print(f"[{year}] {t.tableType}: {t.columns}")
```

### 비용의 성격별 분류

```python
result = c.notes.costByNature
result.timeSeries    # 비용 항목별 시계열
result.ratios        # 구성비
result.crossCheck    # 교차 검증 결과
```

### 미등록 키워드 직접 조회

```python
c.notes.detail("법인세")       # NotesDetail result
c.notes.detail("법인세").tableDf

c.notes.detail("특수관계자")
c.notes.detail("특수관계자").tableDf
```

전체 23개 키워드: `재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

