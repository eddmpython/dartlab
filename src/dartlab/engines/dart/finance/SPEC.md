# dart/finance 엔진 스펙

## 역할

DART XBRL 재무제표 원본 → **snakeId 정규화** → 분기/연도별 시계열 dict로 변환.
회사마다 다른 계정명(XBRL account_id, 한글 account_nm)을 하나의 표준 식별자(snakeId)로 통일.

**핵심 가치**: 회사간 비교 가능한 정규화된 재무 시계열.

## 데이터 소스

- **원본**: `data/dart/finance/{stockCode}.parquet`
- **GitHub Release**: `data-finance-{1..4}` (4개 shard, 총 2,743개 종목)
- **기간**: 2015년~ (XBRL 전자공시 의무화 이후)
- **단위**: 원 (KRW)
- **갱신 주기**: 분기 공시 후 (통상 45일 내)

## 원본 parquet 스키마 (28개 컬럼)

| 컬럼 | 설명 |
|------|------|
| `stockCode` | 종목코드 (6자리) |
| `bsns_year` | 사업연도 |
| `reprt_nm` | 분기명 (1분기/2분기/3분기/4분기) |
| `sj_div` | 재무제표 구분 (BS/IS/CIS/CF/SCE) |
| `fs_div` | 연결/별도 구분 (CFS/OFS) |
| `account_id` | XBRL 계정 ID |
| `account_nm` | 한글 계정명 |
| `account_detail` | 상세 항목 (SCE용) |
| `thstrm_amount` | 당기 금액 (IS/CIS: 1분기만 standalone, 나머지 누적) |
| `thstrm_add_amount` | 당기 누적 금액 (IS/CIS 정규화의 핵심) |

## 재무제표 구분 (sj_div)

| sj_div | 설명 | 정규화 방식 |
|--------|------|-------------|
| **BS** | 재무상태표 | 시점잔액 그대로 |
| **IS** | 손익계산서 | thstrm_add_amount 기반 누적→standalone 차분 |
| **CIS** | 포괄손익계산서 | IS와 동일 방식, 출력 시 IS로 병합 |
| **CF** | 현금흐름표 | thstrm_amount 기반 이전분기 차분으로 standalone |
| **SCE** | 자본변동표 | 별도 매트릭스 피벗 (cause × detail × year) |

## 매핑 파이프라인 (mapper.py)

```
원본 account_id, account_nm
  ↓ prefix 제거 (ifrs-full_, dart_, ifrs_, ifrs-smes_)
  ↓ ID_SYNONYMS (89개 영문 동의어 → 표준 IFRS ID)
  ↓ ACCOUNT_NAME_SYNONYMS (104개 한글 동의어 → 표준 한글명)
  ↓ accountMappings.json 조회 (한글명 우선 → 영문ID)
  ↓ 공백제거 후 재조회
  ↓ 괄호제거 후 재조회
  ↓ 미매핑 → None (제외)
```

- **accountMappings.json**: 34,249개 매핑 (standardAccounts + learnedSynonyms)
- **매핑률**: 97.07% (전종목 평균)
- **sj_div 분리**: 동일 계정명이 다른 재무제표에서 다른 의미 → sj_div별 매핑 (cross-statement 오매핑 방지)

## AccountMapper 부가 기능

| 메서드 | 설명 |
|--------|------|
| `map(accountId, accountNm)` | snakeId 반환 (또는 None) |
| `labelMap()` | snakeId → 대표 한글명 (korName 우선) |
| `sortOrder(sjDiv)` | snakeId → 표시 순서 (common/ordering 위임) |
| `levelMap(sjDiv)` | snakeId → 들여쓰기 레벨 (common/ordering 위임) |

## 피벗 함수 (pivot.py)

### 핵심 시계열

| 함수 | 설명 | 반환 |
|------|------|------|
| `buildTimeseries(stockCode, fsDivPref)` | 분기별 standalone | `({"BS":{}, "IS":{}, "CF":{}}, ["2016-Q1", ...])` |
| `buildAnnual(stockCode, fsDivPref)` | 연도별 (IS/CF=분기합, BS=Q4잔액) | `({"BS":{}, "IS":{}, "CF":{}}, ["2016", ...])` |
| `buildCumulative(stockCode, fsDivPref)` | 분기별 누적 | `({"BS":{}, "IS":{}, "CF":{}}, ["2016-Q1", ...])` |

### SCE 시계열

| 함수 | 설명 | 반환 |
|------|------|------|
| `buildSceMatrix(stockCode, fsDivPref)` | 연도별 자본변동 매트릭스 | `(matrix[year][cause][detail], years)` |
| `buildSceAnnual(stockCode, fsDivPref)` | SCE 연도별 시계열 | `({"SCE":{"cause__detail":[...]}}, years)` |

### 공통 파라미터

- `fsDivPref`: `"CFS"` (연결, 기본) 또는 `"OFS"` (별도). CFS 없으면 OFS fallback.
- CIS → IS 자동 병합 (CIS만 있는 회사 2,329개)

## 주요 snakeId (IS)

| snakeId | 한글명 | 비고 |
|---------|--------|------|
| `sales` | 매출액 | |
| `cost_of_sales` | 매출원가 | |
| `gross_profit` | 매출총이익 | |
| `sga_expense` | 판매비와관리비 | |
| `operating_profit` | 영업이익 | |
| `profit_before_tax` | 법인세비용차감전순이익 | |
| `income_tax` | 법인세비용 | |
| `net_profit` | 당기순이익 | |
| `comprehensive_income` | 총포괄이익 | |
| `basic_eps` | 기본주당이익 | |

## 주요 snakeId (BS)

| snakeId | 한글명 | 비고 |
|---------|--------|------|
| `current_assets` | 유동자산 | |
| `cash` | 현금및현금성자산 | |
| `trade_receivables` | 매출채권및기타채권 | |
| `inventories` | 재고자산 | |
| `noncurrent_assets` | 비유동자산 | |
| `ppe` | 유형자산 | |
| `total_assets` | 자산총계 | |
| `current_liabilities` | 유동부채 | |
| `noncurrent_liabilities` | 비유동부채 | |
| `total_liabilities` | 부채총계 | |
| `total_equity` | 자본총계 (지배기업) | EquityAttributableToOwnersOfParent |
| `equity_including_nci` | 자본총계 (NCI 포함) | Equity |

## 주요 snakeId (CF)

| snakeId | 한글명 | 비고 |
|---------|--------|------|
| `operating_cashflow` | 영업활동현금흐름 | |
| `investing_cashflow` | 투자활동현금흐름 | |
| `financing_cashflow` | 재무활동현금흐름 | |
| `net_cash_change` | 현금및현금성자산증감 | |

## 추출 함수 (extract.py → common/finance/extract.py)

| 함수 | 설명 |
|------|------|
| `getTTM(series, periods, snakeId, sjDiv)` | 최근 4분기 합 (IS/CF) 또는 최신 잔액 (BS) |
| `getLatest(series, periods, snakeId, sjDiv)` | 최신 분기 값 |
| `getAnnualValues(series, years, snakeId, sjDiv)` | 연도별 시계열 리스트 |

## 재무비율 (ratios.py → common/finance/ratios.py)

| 비율 | 산식 |
|------|------|
| `roe` | net_profit / total_equity × 100 |
| `roa` | net_profit / total_assets × 100 |
| `operatingMargin` | operating_profit / sales × 100 |
| `netMargin` | net_profit / sales × 100 |
| `debtRatio` | total_liabilities / total_equity × 100 |
| `currentRatio` | current_assets / current_liabilities × 100 |
| `fcf` | operating_cashflow + investing_cashflow |
| ... | 30+ 비율 (RatioResult dataclass) |

## 파일 구조

```
engines/dart/finance/
├── mapper.py           # 계정 매핑 (AccountMapper)
├── pivot.py            # 시계열 피벗 (buildTimeseries/Annual/Cumulative/Sce)
├── extract.py          # 재수출 (common/finance/extract)
├── ratios.py           # 재수출 (common/finance/ratios)
├── sceMapper.py        # SCE 변동원인/자본항목 정규화
├── mapperData/         # 매핑 JSON
│   └── accountMappings.json  # 34,249개 매핑
└── SPEC.md             # 이 파일
```

## Company에서의 활용

| Company property | finance 함수 | 비고 |
|-----------------|--------------|------|
| `c.timeseries` | `buildTimeseries("CFS")` | 분기별 |
| `c.annual` | `buildAnnual("CFS")` | 연도별 |
| `c.cumulative` | `buildCumulative("CFS")` | 누적 |
| `c.sceMatrix` | `buildSceMatrix("CFS")` | SCE 매트릭스 |
| `c.sce` | `buildSceAnnual("CFS")` | SCE 시계열 |
| `c.ratios` | `calcRatios(series)` | 재무비율 |
| `c.ratioSeries` | `calcRatioSeries(annualSeries)` | 비율 시계열 |
| `c.getTimeseries(period, fsDivPref)` | 위 3개 builder 선택 | 유연 접근 |
| `c.getRatios(fsDivPref)` | `calcRatios(series)` | fsDivPref 지정 |
