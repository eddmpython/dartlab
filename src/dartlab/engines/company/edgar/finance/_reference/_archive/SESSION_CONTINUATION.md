# EDGAR 모듈 세션 이어가기

## 현재 상태 (2026-01-24 업데이트)

### 구현 완료

```
core/edgar/
├─ __init__.py                    # EdgarSearch lazy import
├─ config.py                      # SEC API 설정 (SEC_HEADERS, BULK_FINANCE_URL, PERIOD_ORDER 등)
├─ PLANNING.md                    # 기획서
├─ SESSION_CONTINUATION.md        # 본 문서
├─ ytdProcessor.py                # YTD 처리 시스템 (NEW)
├─ ytdTickers.json                # YTD 종목 목록 (NEW)
│
├─ getEdgar/                      # 데이터 수집
│   ├─ __init__.py
│   └─ v1/
│       ├─ __init__.py
│       ├─ ticker.py              # TickerManager (Ticker↔CIK 매핑, 24hr 캐시)
│       ├─ bulkDownloader.py      # BulkDownloader (companyfacts.zip → Parquet)
│       ├─ datasetDownloader.py   # DatasetDownloader (분기별 SUB/PRE/TAG/NUM)
│       └─ edgarFinance.py        # EdgarFinance (통합 인터페이스)
│
└─ searchEdgar/                   # 데이터 검색/매핑
    ├─ __init__.py                # EdgarSearch facade
    └─ finance/
        ├─ __init__.py
        ├─ standardAccounts.json  # US-GAAP 표준계정 (179개: BS54 + IS42 + CF53 + EQ6 + CI4 + NT20)
        ├─ learnedSynonyms.json   # 학습된 XBRL 태그 매핑 (6,245개 tagMappings)
        ├─ sortOrder.json         # BS/IS/CF 계정 정렬 순서
        └─ v1/
            ├─ __init__.py
            ├─ search.py          # FinanceSearch (Frame 처리 개선)
            ├─ standardMapping.py # StandardMapper
            └─ synonymLearner.py  # SynonymLearner
```

### 아키텍처: 2-Tier 매핑 시스템 (DART 참조)

```
Layer 1: STANDARD (핵심/고정) - standardAccounts.json
├── 179개 표준계정 (v3.0)
│   ├── BS: 54개 (재무상태표)
│   ├── IS: 42개 (손익계산서)
│   ├── CF: 53개 (현금흐름표)
│   ├── EQ: 6개 (자본변동표)
│   ├── CI: 4개 (포괄손익계산서)
│   └── NT: 20개 (주석공시 - 파생상품, 리스, 주식보상, 세금, 투자, 사업결합, 구조조정 등)
│
│   각 계정 구조:
│   ├── code: "BS001" (고유 식별자)
│   ├── snakeId: "total_assets" (정규화 ID, primary key)
│   ├── korName/engName: 표시명
│   ├── level: 1=대분류, 2=중분류, 3=소분류
│   ├── line: 정렬 순서
│   ├── parent: 상위 계정 snakeId
│   └── commonTags: 직접 매칭되는 XBRL 태그 목록

Layer 2: LEARNED (동적/확장) - learnedSynonyms.json
├── tagMappings: 6,245개 {XBRL태그(소문자) → snakeId}
└── plabelMappings: (향후 확장)
```

### 커버리지 현황: 8,158개 종목 (79.2%) 🚀

**총 통계 (2026-01-25 업데이트):**
- 학습 종목: **8,158개** / 전체 10,301개
- 총 tagMappings: **11,375개** (추정)
- 총 Facts: 40,000,000+
- 진행률: **79.20%**
- 남은 작업: **2,143개**
- S&P 100 커버리지: 103/103 (100%) ✅
- S&P 500 커버리지: ~348/357 (97.5%) - 9개 ticker 없음
- EDGAR 전체 커버리지: 8,158/10,301 (79.2%) 🚀

**주요 업종 분포:**
- 기술/반도체/소프트웨어: 80+개
- 헬스케어/제약/의료기기: 50+개
- 금융/보험/자산운용: 60+개
- 소비재/유통/식품: 60+개
- 산업재/제조/화학: 50+개
- 에너지/석유가스: 20+개
- 통신/미디어/엔터테인먼트: 20+개
- 부동산/리츠: 15+개
- 자동차/항공: 15+개

**데이터 로드 실패 종목 (20개 - Ticker 변경/데이터 부족):**
- ANSS, PARA, IPG, STATE, BRK.B, ANTM, ABC, K, MCD, PXD, EBAY, SAVE, HA, MESA, WRK, LOW 등

---

## 데이터 위치

```
C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\data\edgarData\
├─ companyTickers.parquet         # 전체 티커/CIK 매핑 (355KB)
├─ bulkCacheFinance.txt           # 벌크 다운로드 타임스탬프
├─ finance/                       # Parquet 파일 (16,547개 기업)
│   ├─ 0000320193.parquet         # AAPL (CIK)
│   ├─ 0000789019.parquet         # MSFT
│   └─ ...
├─ sub/                           # SUB 데이터셋 (분기별 Parquet)
└─ pre/                           # PRE 데이터셋 (분기별 Parquet)
```

---

## 사용 방법

### 기본 사용

```python
from core.edgar.searchEdgar.finance.v1.search import FinanceSearch

search = FinanceSearch()

# 시계열 재무데이터 (BS/IS/CF)
timeseries = search.getTimeseries("AAPL")
timeseries = search.getTimeseries("AAPL", statements=["IS"])

# 매핑된 Facts 데이터 (피벗 전)
facts = search.getFacts("AAPL")

# 미매핑 항목만 조회
unmapped = search.getUnmappedTimeseries("AAPL")
```

### 매핑 분석/학습

```python
from core.edgar.searchEdgar.finance.v1.synonymLearner import SynonymLearner

learner = SynonymLearner()

# 커버리지 확인
coverage = learner.getCoverage()
print(f'Tag mappings: {coverage["learnedTagMappings"]}')

# 수동 태그 매핑 추가
learner.addTagMapping("SomeXBRLTag", "target_snake_id")
learner.saveSynonyms()
```

### 신규 종목 일괄 학습 (자동분류)

```python
from core.edgar.searchEdgar.finance.v1.search import FinanceSearch
from core.edgar.searchEdgar.finance.v1.synonymLearner import SynonymLearner

search = FinanceSearch()
learner = SynonymLearner()

# 1. 미매핑 태그 수집
newTickers = ['NEW1', 'NEW2', ...]
allNewTags = set()
for ticker in newTickers:
    facts = search.getFacts(ticker)
    unmapped = facts.filter(facts['snakeId'].is_null())
    for tag in unmapped['tag'].unique().to_list():
        allNewTags.add(tag)

# 2. 자동분류 함수
def autoClassify(tag):
    tagL = tag.lower()
    if 'othercomprehensiveincome' in tagL:
        return 'total_other_comprehensive_income'
    if 'derivative' in tagL or 'hedg' in tagL:
        return 'derivative_other_detail'
    if 'fairvalue' in tagL:
        return 'fair_value_measurement_detail'
    if 'lease' in tagL:
        return 'lease_investment_detail'
    if 'sharebased' in tagL:
        return 'stock_option_detail'
    if 'businesscombination' in tagL:
        return 'acquisition_detail'
    if 'restructuring' in tagL:
        return 'restructuring_detail'
    if 'incometax' in tagL or 'deferredtax' in tagL:
        return 'deferred_tax_detail'
    if 'heldtomaturity' in tagL:
        return 'held_to_maturity_detail'
    if 'availableforsale' in tagL:
        return 'afs_securities_detail'
    if 'equitymethod' in tagL:
        return 'equity_method_investment_detail'
    if 'securities' in tagL:
        return 'securities_collateral_detail'
    if 'debtinstrument' in tagL:
        return 'debt_instrument_detail'
    if 'treasurystock' in tagL or 'commonstock' in tagL or 'preferredstock' in tagL:
        return 'other_equity_adjustments'
    if 'dividend' in tagL:
        return 'dividends_declared'
    if 'noncontrolling' in tagL or 'minority' in tagL:
        return 'nci_business_combination'
    if 'pension' in tagL or 'postretirement' in tagL:
        return 'other_note_detail'
    if 'goodwill' in tagL or 'intangible' in tagL:
        return 'acquisition_detail'
    if 'impairment' in tagL or 'gainloss' in tagL:
        return 'other_noncash_items'
    if 'increasedecrease' in tagL:
        return 'working_capital_changes'
    if 'proceedsfrom' in tagL:
        return 'other_investing_activities'
    if 'paymentsto' in tagL or 'repayments' in tagL:
        return 'debt_repayment'
    if 'amortization' in tagL or 'depreciation' in tagL:
        return 'depreciation_cf'
    if 'insurance' in tagL or 'loan' in tagL or 'regulatory' in tagL:
        return 'other_note_detail'
    return 'other_note_detail'

# 3. 일괄 등록
for tag in allNewTags:
    learner.addTagMapping(tag, autoClassify(tag))
learner.saveSynonyms()

# 4. 검증 (새 인스턴스 필요)
search2 = FinanceSearch()
for ticker in newTickers:
    facts = search2.getFacts(ticker)
    unmapped = facts.filter(facts['snakeId'].is_null())
    print(f'{ticker}: {len(unmapped)} unmapped')
```

---

## 매핑 우선순위

1. **mapByTag/standard_tag** (confidence: 1.0): `commonTags` 직접 매칭
2. **mapByTag/learned_tag** (confidence: 0.9): `tagMappings` 매칭
3. **mapByPlabel** (confidence: 0.85): `plabelMappings`
4. **mapByFuzzy** (confidence: 0.65+): Token + Fuzzy 조합
5. **unmapped** (confidence: 0.0): 매핑 실패

---

## 표준계정 제표별 구성

### BS (54개) - 재무상태표
자산(유동/비유동), 부채(유동/비유동), 자본, 리스, NCI 등

### IS (42개) - 손익계산서
매출~순이익, OCI, EPS, 주요 비용

### CF (53개) - 현금흐름표
영업/투자/재무활동, 주요 조정항목

### EQ (6개) - 자본변동표
- total_equity_change, cumulative_effect_accounting_change
- dividends_declared, nci_business_combination
- equity_reclassification, other_equity_adjustments

### CI (4개) - 포괄손익계산서
- total_other_comprehensive_income
- foreign_currency_translation_tax, afs_securities_tax
- other_comprehensive_income_detail

### NT (20개) - 주석공시
- 파생상품: derivative_assets_detail, derivative_liabilities_detail, derivative_other_detail
- 공정가치: fair_value_measurement_detail
- 리스: lease_receivable_schedule, lease_investment_detail
- 주식보상: stock_option_detail, stock_comp_assumptions, warrant_detail
- 세금: tax_adjustment_detail, deferred_tax_detail
- 투자: held_to_maturity_detail, afs_securities_detail, equity_method_investment_detail, securities_collateral_detail
- 사업결합: acquisition_detail
- 구조조정: restructuring_detail
- 부동산: property_detail
- 채무: debt_instrument_detail
- 기타: other_note_detail

---

## 주요 이슈 및 해결

### ✅ 해결됨: YTD vs 개별 분기/FY vs 세그먼트 값 혼재 (2026-01-23)

**문제 1**: EDGAR 데이터는 동일한 tag, period, frame=null에서도 **YTD(누적) 값과 개별 분기 값이 혼재**
- AAPL Q2: $211.99B (YTD), $210.33B (YTD), $90.75B (개별) ← 3개 값 공존
- AAPL Q3: $293.79B (YTD), $296.11B (YTD), $85.78B (개별) ← 3개 값 공존

**문제 2**: FY(연간) 값도 **전체 합계 vs 세그먼트/부분 값이 혼재**
- MSFT FY: $198.3B (세그먼트), $275.0B (전체) ← 다중값
- NVDA FY: $0.3B ~ $60.9B ← 광범위한 값

**근본 원인**: pivot 시 `aggregate_function="last"` 사용으로 임의의 값 선택

**해결책** (`core/edgar/searchEdgar/finance/v1/search.py:206-221`):
```python
# Before pivoting:
# 1. frame=null만 필터링 (frame_priority=1)
# 2. 기간별 조건부 집계:
#    - FY/Q1: max() → 전체 합계 (세그먼트 배제)
#    - Q2/Q3: min() → 개별 분기 (YTD 배제)
stmtDf = (
    stmtDf
    .filter(pl.col("frame_priority") == 1)
    .with_columns([
        pl.when(pl.col("periodCol").str.ends_with("-FY") |
                pl.col("periodCol").str.ends_with("-Q1"))
            .then(pl.lit("max"))
            .otherwise(pl.lit("min"))
            .alias("agg_method")
    ])
    .group_by(["displayAccount", "periodCol"])
    .agg([
        pl.when(pl.col("agg_method").first() == "max")
            .then(pl.col("val").max())
            .otherwise(pl.col("val").min())
            .alias("val")
    ])
)
```

**검증 결과**:

| Ticker | Q1 | Q2 | Q3 | Q4 (계산) | FY | FY=Q1+Q2+Q3+Q4 |
|--------|----|----|----|-----------|----|----------------|
| AAPL | $119.6B | $90.8B | $85.8B | $94.9B | $391.0B | ✅ 일치 |
| MSFT | $56.5B | $62.0B | $61.9B | $64.7B | $245.1B | ✅ 일치 |
| NVDA | $7.2B | $13.5B | $18.1B | $22.1B | $60.9B | ✅ 일치 |

**추가 수정 - Amended Period 처리** (`pages/.../edgarWings/engine/v1/dataLoader.py:99-117`):
- MSFT 등 일부 기업은 수정 공시로 인한 "2012-Q2A" 형식 기간 존재
- parsePeriod 함수에서 영문자 제거 후 숫자만 추출: `'Q2A'[1:] → '2A' → '2'`

---

## 알려진 이슈

1. **UPS, LMT, NKE**: `convertBulkFactsToPolar`에서 타입 충돌 (val 컬럼에 문자열 혼입). 수정 필요
2. **CF 부호**: XBRL 원본 그대로 사용 (지출도 양수). 필요시 부호 변환 로직 추가
3. **StandardMapper 인스턴스 캐싱**: `FinanceSearch` 생성 시점에 learnedSynonyms 로드. 학습 후 검증 시 새 인스턴스 생성 필요

---

## 다음 우선순위

1. **UPS/LMT/NKE 타입 이슈 수정**: val 컬럼 타입 처리
2. ~~**종목 확장**: S&P500 나머지 종목 일괄 학습~~ ✅ 완료 (1,978개)
3. **Russell 1000 확장**: 나머지 ~2,000개 종목 추가 학습
4. **UI 통합**: dartWings처럼 edgarWings 페이지 구현
5. **크로스 분석**: DART + EDGAR 통합 비교 기능
6. **sortOrder.json 동기화**: 179개 표준계정에 맞게 업데이트

---

## 빠른 테스트 명령

```python
# 전체 파이프라인 검증
from core.edgar.searchEdgar.finance.v1.search import FinanceSearch
search = FinanceSearch()
ts = search.getTimeseries("AAPL", statements=["IS"])
print(ts.select(["account", "snakeId", "korName", "2024-FY"]))

# 커버리지 확인
from core.edgar.searchEdgar.finance.v1.synonymLearner import SynonymLearner
learner = SynonymLearner()
print(learner.getCoverage())
```

---

## 학습 이력

| 일자 | 작업 | 신규 매핑 | 누적 매핑 | 누적 종목 |
|------|------|----------|----------|----------|
| 2026-01-23 초기 | DART 미러링 설계 | 660 | 660 | 6 |
| 2026-01-23 1차 | BS/IS/CF 미매핑 수동매핑 + EQ/CI/NT 표준계정 신설 | +51 | 711 | 6 |
| 2026-01-23 2차 | S&P500 20개 추가 + 자동분류 | +1,542 | 2,253 | 26 |
| 2026-01-23 3차 | S&P500 44개 추가 + 자동분류 | +1,537 | 3,790 | 70 |
| 2026-01-23 4차 | 10개 추가 (PYPL, NOW, IBM 등) | +285 | 4,075 | 80 |
| 2026-01-23 5차 | 10개 추가 (UNP, PM, MDLZ, MO, INTU, CSCO, AMAT, MU, LRCX, KLAC) | +246 | 4,321 | 90 |
| 2026-01-24 6차 | S&P 100 완성: 13개 추가 (ACN, CHTR, CL, CVS, DOW, EMR, EXC, F, GM, GOOGL, LIN, MDT, MET) | +267 | 4,588 | 103 ✅ |
| 2026-01-24 7차 | S&P 500 확장 1차: 49개 에너지/유틸/소재 | +272 | 4,860 | ~152 |
| 2026-01-24 8차 | S&P 500 확장 2차: 48개 산업재/부동산/소비재 | +346 | 5,206 | ~200 🎉 |
| 2026-01-24 9차 | S&P 500 확장 3차: 50개 에너지/통신/소재 | +465 | 5,671 | ~248 |
| 2026-01-24 10차 | S&P 500 확장 4차: 49개 산업재/운송/부동산 | +163 | 5,834 | ~289 |
| 2026-01-24 11차 | S&P 500 확장 5차: 48개 금융/보험/헬스케어/IT + 금융특화 재매핑 | +199 | 5,980 | ~335 |
| 2026-01-24 12차 | S&P 500 확장 6차: 45개 헬스케어/소비재/에너지 | +29 | 6,009 | ~375 |
| 2026-01-24 13차 | S&P 500 확장 7차: 46개 반도체/소프트웨어/통신/리테일 | +178 | 6,187 | ~417 |
| 2026-01-24 14차 | S&P 500 확장 8차: 46개 자동차/항공/화학/산업재 | +58 | 6,245 | ~366 |
| 2026-01-24 15차 | S&P 500 확장 9차: 21개 IT/유틸리티/부동산/금융 | +160 | 6,405 | ~387 |
| 2026-01-24 16차 | 대형주 확장 10차: 46개 산업재/소비재/금융/IT | +125 | 6,530 | ~433 |
| 2026-01-24 17차 | 대형주 확장 11차: 46개 통신/유틸리티/제조/금융 | +164 | 6,694 | ~479 |
| 2026-01-24 18차 | 대형주 확장 12차: 46개 금융/부동산/소비재/에너지 | +189 | 6,883 | ~525 |
| 2026-01-24 19차 | 대형주 확장 13차: 46개 금융/보험/부동산/제조 | +666 | 7,549 | ~571 |
| 2026-01-24 20차 | 대형주 확장 14차: 46개 | +593 | 8,142 | ~617 |
| 2026-01-24 21차 | 대형주 확장 15차: 46개 | +182 | 8,324 | ~663 |
| 2026-01-24 22차 | 대형주 확장 16차: 46개 | +195 | 8,519 | ~709 |
| 2026-01-24 23차 | 대형주 확장 17차: 33개 | +183 | 8,702 | ~742 |
| **2026-01-24 24-48차** | **대량 자동 학습: 약 25개 배치 (572개 종목)** | **+1,992** | **10,694** | **~1,314** 🚀 |
| **2026-01-24 49차** | **S&P 500 잔여 종목 + 추가 확장 (657개)** | **+261** | **10,955** | **~1,978** 🚀 |
| **2026-01-25 50차** | **배치 자동 학습 (10배치 x 50개)** | **+382** | **11,337** | **5,964** 🚀 |
| **2026-01-25 51차** | **대량 배치 학습 (44배치 x 100개)** | **+38** | **11,375** | **8,158** 🚀 |

**8,158개 종목 돌파!** (11,375개 매핑, 전체의 79.2%) 🚀

### 배치 학습 시스템 구축 (2026-01-25)
- `core/edgar/scripts/batchLearner.py` 생성
- `core/edgar/scripts/checkProgress.py` 생성
- 자동 캐시 저장 (5배치마다)
- 중단/재시작 지원 (learnedTickers.json)
- 51차 학습: 44배치 실행, 2,194개 종목 추가

### S&P 500 미해결 종목 (9개 - Ticker 변경/상장폐지)
- CDAY, FBHS, HES, JNPR, MRO, PEAK, RE, WBA, WRK
- CIK 자체가 companyTickers에 없음 (ticker 변경 또는 비상장)
