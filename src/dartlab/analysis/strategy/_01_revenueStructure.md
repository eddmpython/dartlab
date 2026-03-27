# 1-1. 수익 구조 — 이 회사는 무엇으로 돈을 버는가

> c.review("수익구조")의 설계 문서.
> 가능한 것 / 불가능한 것 / 제약 / 해결 방안을 기록한다.

---

## 1. 세계적 기준 — 수익구조 분석이 계산하는 것

| 단계 | 분석 내용 | 핵심 지표 |
|------|----------|----------|
| 구조 분해 | 부문별/제품별/지역별 매출 비중 | 비중(%), 금액(조/억) |
| 집중도 | 매출이 얼마나 쏠려있는가 | HHI, CR4, Shannon Entropy, Gini |
| 성장 분해 | 어디서 성장하는가 | 부문별 growth contribution, YoY |
| 수익성 구조 | 어디서 남기는가 | 부문별 영업이익률, segment margin |
| 매출 품질 | 얼마나 믿을 수 있는가 | Cash Conversion, Accruals Ratio |
| 전략 판단 | 한 줄 요약 | 구조 변화 방향, 핵심 부문 식별 |

참고 도구: OpenBB(revenue_per_segment), FinanceToolkit(150+ 비율), concentrationMetrics(12개 집중도 지표), FMP(제품/지역 segmentation API).

---

## 2. dartlab 데이터 현황 — 가능한 것과 불가능한 것

### 2-1. 데이터 소스 3개

| 소스 | 접근 경로 | 내용 | 한계 |
|------|----------|------|------|
| **segments** | `c.segments()` (K-IFRS 주석 파싱) | 부문별 매출/영업이익/감가상각 | 연간만, 당기/전기 2년뿐. sections에 미노출 |
| **salesOrder** | `c.salesOrder()` (매출실적/수주) | 제품/서비스별 매출, 수주잔고 | 컬럼명 v1/v2/v3 문제, 50~60% 커버리지 |
| **IS (finance)** | `c.show("IS")` (XBRL 재무제표) | 매출액/매출원가/영업이익 분기별 시계열 | 연결 합산만, 부문 분해 불가 |

### 2-2. 가능한 분석

| 분석 | 소스 | 비고 |
|------|------|------|
| ✅ 부문별 매출 비중 (최근 연도) | segments | 당기 기준 비중 계산 가능 |
| ✅ 부문별 매출 추이 (다년간) | segments | `segments().revenue` — 전 연도 당기 매출 이어 붙임, 부문×연도 DataFrame |
| ✅ 부문별 영업이익률 | segments | 매출 + 영업이익 동시 존재 시 |
| ✅ 전체 매출/이익 YoY 성장률 | IS | 분기별 시계열 충분 |
| ✅ 영업이익률 추이 (분기별) | IS | 최대 40분기 |
| ✅ 매출총이익률 추이 | IS | grossMargin 계산 가능 |
| ✅ 매출 품질 (Cash Conversion) | IS + CF | 영업CF / 순이익 |
| ✅ DuPont 분해 (margin × turnover × leverage) | ratios | 이미 계산됨 |
| ✅ 매출 집중도 (HHI, CR 등) | segments | 부문 비중에서 계산 |

### 2-3. 재검토 — "불가능"을 줄인다

기존에 불가능으로 적었던 것들을 데이터 기준으로 재판정.

| 분석 | 기존 | 재판정 | 근거 |
|------|------|--------|------|
| 다년간 부문 추이 | ❌ | ✅ | `segments()`가 전 연도 순회, 당기 매출 이어 붙임. `segments().revenue` = 부문×연도 DataFrame |
| 부문별 영업이익 | ❌ | ✅ | `segments().tables`에 영업이익 행이 이미 있음. `_buildRevenueDf`가 매출만 뽑고 버리는 것뿐 — 영업이익도 동일 로직으로 추출 가능 |
| 지역별 매출 분해 | ❌ | ⚠️→✅ | parser가 `tableType="region"` 분류 이미 구현. 국내/미주/유럽/아시아 패턴 감지. 있는 회사는 바로 사용 가능 |
| 제품별 매출 | ⚠️ | ⚠️→✅ | parser가 `tableType="product"` 분류 구현. segments().tables에 제품 테이블 존재. salesOrder 안 써도 됨 |
| 부문별 분기 매출 | ❌ | ❌ | K-IFRS 주석이 연간 보고서에만 부문 공시. 분기 보고서에는 부문 없음 |
| 부문별 ROIC | ❌ | ⚠️ | 영업이익은 있지만 부문별 투하자본은 일부 회사만 공시. 영업이익률로 대체 |
| 고객 집중도 | ❌ | ❌ | DART에 개별 고객 매출 미공시 (SEC 10-K에만 존재) |
| Price/Volume/Mix | ❌ | ❌ | 가격/물량 분리 데이터 없음 |
| Organic vs Inorganic | ❌ | ❌ | M&A 매출 분리 불가 |

**핵심: segments().tables에 데이터가 이미 다 있는데 revenue DataFrame만 만들고 나머지를 버리고 있었다.**

- `_buildRevenueDf()`는 segment+당기+매출 행만 추출
- 영업이익, 감가상각, region 테이블, product 테이블은 allTables에 있지만 DataFrame화 안 됨
- 이걸 확장하면 ✅로 전환되는 항목이 3~4개 더 있음

### 2-4. 확장 방안 — allTables 완전 활용

현재 `_buildRevenueDf`가 하는 것:
```
allTables → segment + 당기 + 매출 행만 → revenue DataFrame
```

확장하면:
```
allTables → segment 매출 → revenueDf
         → segment 영업이익 → operatingIncomeDf
         → segment 영업이익률 → marginDf (매출 ÷ 영업이익)
         → region 매출 → regionDf
         → product 매출 → productDf
```

**같은 파서, 같은 데이터, 추출 로직만 확장.**

---

## 3. 핵심 제약 — "부문" 문제

### 3-1. sections에서 segments가 안 나오는 문제

**현상**: `c.show("segments")`가 sections 경로로 접근 시 실패.
- sections 수평화에서 segments가 독립 토픽으로 추출되지 않음

**원인**: segments 데이터는 K-IFRS 주석(footnote) 29번 항목에 있음.
sections는 사업보고서 본문 수평화이고, 주석은 별도 파싱(`c.segments()`) 경로.

**해결 방안**: review에서는 `c.segments()` (notes 파싱) 직접 호출.
sections 경로에 의존하지 않는다.

**다년간 데이터**: `segments()`는 이미 전 연도를 순회하여 각 보고서의 당기 매출을 이어 붙인다.
`segments().revenue`가 부문×연도 wide DataFrame을 반환. "2년뿐"이 아니라 보유 데이터 전체 연도를 커버.

### 3-2. 부문명 표준화 — 업계 조사 결과

**문제**: 같은 회사도 연도별 부문 재편. 삼성전자 2022년 "CE/IM/반도체/DP/Harman" → 2024년 "DX/DS/SDC/Harman".

**업계 조사 결과: 완전 자동 솔루션은 어디에도 없다.**

| 주체 | 접근법 |
|------|--------|
| FactSet RBICS | 섹터 전문 애널리스트가 수작업 매핑 (~45,000사, 연 1회 리뷰) |
| S&P Capital IQ | "As Reported" + "Standardized" 이중 제공, 표준화는 수작업 |
| Refinitiv | 35년+ 수작업 수집 |
| Compustat | "considerable measurement error/noise" 인정, 세그먼트 SIC 수작업 |
| OpenBB/FinanceToolkit | 데이터 제공자에 의존, 자체 처리 없음 |
| EdgarTools | concept 수준 매핑만 (Revenue 등), segment member 변경 추적 없음 |

**XBRL dimension member도 해결 못 함**: 기업이 부문을 바꾸면 새 member ID를 만듦.
`CESegmentMember` → `DXSegmentMember`. 이전 member와의 연결 정보 없음.

**회계 기준이 주는 무기 — recast(재작성)**:
- IFRS 8 / ASC 280: 부문 변경 시 **이전 기간을 새 구조로 재작성** 의무
- 즉, 2024년 Filing의 "전기"는 이미 DX/DS 기준으로 재작성되어 있음
- 같은 Filing 내 당기/전기 비교는 항상 정합 → **Filing 내 recast 데이터가 가장 신뢰할 수 있는 연결 고리**

**dartlab 해결 방안**:

1. **recast 우선**: 같은 Filing의 당기/전기를 1차 시계열로 사용 (이미 구조 맞춤)
2. **Filing 간 연결**: 연도별 당기 매출을 이어 붙이되, 부문명 변경 시 **break를 명시적으로 표시**
3. **강제 연결 금지**: DX ≠ CE+IM을 자동 매핑하지 않음. 업계 표준이 "사람이 매핑"인데 코드로 억지로 하면 오류
4. **변경 감지**: 부문 목록이 바뀌면 "부문 재편 감지" 플래그 표시
5. **수작업 매핑 테이블**: 주요 기업의 알려진 변경은 `sectionMappings.json` 패턴처럼 점진 축적 가능

**한 줄 원칙: break를 숨기지 않는다. 업계 표준이 수작업인 영역을 코드로 억지 자동화하면 신뢰성을 잃는다.**

### 3-3. 금액 단위 불일치

- segments: 백만원 단위 (XBRL 원본)
- salesOrder: 백만원/억원 혼재
- IS: 백만원 단위

**해결**: 출력 시 조/억 단위로 통일 변환. `_formatAmount()` 활용.

---

## 4. review 출력 설계

### 4-1. 출력 원칙

- **review = 뷰어다**. 보기 좋아야 한다. 데이터 나열이 아니라 판단이 있는 보고서.
- **기간**: 분기 + 반기 모두 제공하되, 지면 제약에 따라 축약.
  - 부문별 구조: 최근 연간 (1~2년) — segments가 연간이므로
  - 전체 손익 추이: 최근 4~8분기
  - 영업이익률: 최근 4~8분기
- **금액 단위**: 조/억 단위 (원 단위 아님)
- **모든 것을 보여주지 않는다**. 핵심만. 상세는 `c.show("IS")`, `c.segments()` 등 개별 호출.

### 4-2. 출력 구조 (목표)

```
■ 수익 구조 — 이 회사는 무엇으로 돈을 버는가

  ▸ 핵심 요약
    "삼성전자는 DX(디바이스경험)와 DS(반도체) 2대 축으로 매출 30.1조를 창출.
     DS 부문이 전년 대비 +68% 급반등하며 수익 구조가 재편 중."

  ▸ 부문별 매출 구성 (2024 연간)
    부문          매출        비중      영업이익률
    DX 부문      17.5조     58.1%      7.1%
    DS 부문      11.1조     36.9%     13.6%
    SDC          2.9조      9.7%      12.8%
    Harman       1.4조      4.7%       9.2%

  ▸ 매출 집중도
    HHI 2,847 — 중간 집중 (DX + DS 95%)

  ▸ 손익 추이 (분기)
    분기        매출       영업이익    영업이익률
    2025Q4     93.8조     20.1조      21.4%
    2025Q3     79.1조     11.1조      14.1%
    2025Q2     74.1조      4.7조       6.3%
    2024Q4     86.1조     10.1조      11.7%

  ▸ 수익 품질
    Cash Conversion  1.2 — 양호 (현금 뒷받침 충분)
    매출총이익률      42.3% → 38.1% → 35.2% (최근 3분기)

  ⚠ DS 부문 영업이익률 급등 — 반도체 사이클 의존도 높음
  ✦ DX 부문 안정적 마진 유지 — 수익 기반 역할
```

### 4-3. 지면 제약 규칙

- 부문 테이블: **최대 8행** (8개 부문 초과 시 상위 7개 + "기타" 합산)
- 분기 추이: **최근 4~8분기** (전체 40분기 나열 금지)
- 서술: **2~3문장** 핵심 판단만
- Flag: **최대 3개** (경고 2 + 기회 1 정도)

---

## 5. 구현 계획

### Phase 1 — revenue.py calc 함수 (구현 완료)

9개 calc 함수로 "이 회사는 무엇으로 돈을 버는가" 질문에 답한다:

1. **calcCompanyProfile** — 업종/주요제품 맥락
2. **calcSegmentComposition** — 부문별 매출/비중/영업이익률
3. **calcSegmentTrend** — 다년간 부문별 매출 추이 + YoY
4. **calcBreakdown(sub)** — 지역별/제품별 매출 분해
5. **calcRevenueGrowth** — 매출 YoY, 3Y CAGR, 분기 매출 시계열
6. **calcGrowthContribution** — 부문별 성장 기여 분해 (어디에서 성장이 왔는가)
7. **calcConcentration** — HHI, 1위 부문 비중, 내수 비중
8. **calcRevenueQuality** — 영업CF/순이익, 매출총이익률 추세
9. **calcFlags** — 경고/기회 플래그 (고집중, 역성장, 매출≠이익 1위 괴리)

데이터 접근 (DEV.md §11 준수):
- `company.select("segments")` — 원본 (기본 경로)
- `company.select("IS", [...])` — 원본 (기본 경로)
- `company.finance.ratios` — 파생 편의
- `company.finance.ratioSeries` — 파생 편의 (시계열)
- `company.sector` — 메타
- gather import 없음 ✅

### Phase 2 — 향후 확장

- 제품별 매출 (salesOrder 데이터 품질 개선 후)
- 지역별 매출 (segments에서 지역 테이블 추출)
- 다년간 부문 추이 (여러 보고서 기간 파싱)
- 부문별 성장 기여도 분해

---

## 6. 토론 기록

### 2026-03-26 — 수익구조 분석 설계

**문제 인식:**
- 기존 revenue.py는 show() 데이터를 그대로 던지는 것에 불과
- "분석"이 아니라 "데이터 나열"
- 세계적 기준 대비 1/10 수준

**조사 결과:**
- OpenBB, FinanceToolkit, FMP 등이 segment/geographic 분해 제공
- 집중도 지표 12종 (HHI, CR, Shannon, Gini 등)
- 성장 분해, 수익 품질, 전략 포지셔닝까지 계산

**핵심 제약:**
- segments가 sections에 없음 → `c.segments()` 직접 호출로 우회
- 연간 2년만 → 분기 부문 분해 불가
- 부문 재편 시 시계열 연결 불가

**결정:**
- review는 뷰어다 — 보기 좋아야 한다
- 기간: 부문=연간, 손익=분기 4~8개
- 금액: 조/억 단위
- 모든 것을 보여주지 않는다 — 핵심만
- Phase 1으로 먼저 실질적 분석을 구현, Phase 2로 확장
