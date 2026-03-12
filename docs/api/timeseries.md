---
title: 계정 표준화와 시계열
---

# 계정 표준화와 시계열

OpenDART 재무제표 원본 데이터를 **표준 계정으로 정규화**하여 기업 간 비교 가능한 시계열로 변환하는 엔진이다.

## 왜 필요한가

한국 상장사 2,700+개는 XBRL로 재무제표를 공시하지만, 같은 "매출"이라는 개념이 회사마다 다른 ID와 이름으로 존재한다.

```
ifrs-full_Revenue          → 삼성전자
dart_OperatingIncomeLoss   → LG화학
dart_ConstructionRevenue   → 현대건설
수익(매출액)               → 카카오
영업수익                   → KB금융
```

DartLab은 7단계 매핑 파이프라인으로 이를 **하나의 `revenue`**로 통합한다. 전체 2,564종목, 1,585만 행 중 **98.7%**가 표준 계정으로 매핑된다.

## 7단계 매핑 파이프라인

| 단계 | 처리 | 항목 수 |
|------|------|---------|
| 1 | account_id prefix 제거 (ifrs-full_, dart_, ifrs_, ifrs-smes_) | - |
| 2 | ID_SYNONYMS 적용 (영문 XBRL ID 동의어) | 70+ |
| 3 | ACCOUNT_NAME_SYNONYMS 적용 (한글 계정명 동의어) | 150+ |
| 4 | CORE_MAP 조회 (핵심 계정 우선 매핑) | ~50 |
| 5 | accountMappings.json 조회 (학습된 매핑) | 34,171 |
| 6 | 괄호 제거 후 재조회 (fallback) | - |
| 7 | 미매핑 → None (시계열에서 제외) | - |

## 시계열 생성

### 분기별 시계열

```python
series, periods = c.timeseries

# periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
# series["IS"]["revenue"]            → 분기별 매출 리스트
# series["BS"]["total_assets"]       → 분기별 총자산 리스트
# series["CF"]["operating_cashflow"] → 분기별 영업현금흐름 리스트
```

반환 구조:

```python
series = {
    "BS": {"total_assets": [v1, v2, ...], "current_assets": [...], ...},
    "IS": {"revenue": [...], "operating_income": [...], "net_income": [...], ...},
    "CF": {"operating_cashflow": [...], "investing_cashflow": [...], ...},
}
periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
```

값이 없는 기간은 `None`으로 표시된다. `0`과 `None`은 의미가 다르다.

### 정규화 방식

| 재무제표 | 원본 형태 | 변환 |
|---------|----------|------|
| BS (재무상태표) | 시점 잔액 | 그대로 |
| IS (손익계산서) | 누적합 (Q1, Q1+Q2, Q1+Q2+Q3, Q1~Q4) | 분기별 standalone 역산 |
| CF (현금흐름표) | 누적합 | 이전 분기 차분으로 standalone 역산 |

연결재무제표(CFS)가 있으면 우선 사용하고, 없으면 별도재무제표(OFS)로 자동 fallback한다.

### 직접 호출

```python
from dartlab.engines.dart.finance import buildTimeseries, buildAnnual, buildCumulative

series, periods = buildTimeseries("005930")              # 분기별 standalone
series, years   = buildAnnual("005930")                  # 연도별 합산
series, periods = buildCumulative("005930")              # 분기별 누적
series, periods = buildTimeseries("005930", fsDivPref="OFS")  # 별도재무제표 강제
```

| 함수 | periods 예시 | IS/CF 처리 | BS 처리 |
|------|-------------|-----------|---------|
| `buildTimeseries` | `["2016_Q1", ...]` | 분기별 standalone | 시점 잔액 |
| `buildAnnual` | `["2016", "2017", ...]` | 해당 연도 분기합 | Q4 시점 잔액 |
| `buildCumulative` | `["2016_Q1", ...]` | 연초부터 누적합 | 시점 잔액 |

## 값 추출 유틸리티

```python
from dartlab.engines.dart.finance import getTTM, getLatest, getAnnualValues, getRevenueGrowth3Y

series, periods = c.timeseries

# TTM (최근 4분기 합) — IS, CF 전용
getTTM(series, "IS", "revenue")            # 최근 4분기 매출 합
getTTM(series, "CF", "operating_cashflow") # 최근 4분기 영업CF 합

# 최신값 — BS, IS, CF 모두
getLatest(series, "BS", "total_assets")    # 최신 총자산
getLatest(series, "IS", "net_income")      # 최신 분기 순이익

# 전체 시계열 리스트
getAnnualValues(series, "IS", "revenue")   # 모든 연도 매출

# 매출 3년 CAGR
getRevenueGrowth3Y(series)                 # 3년 매출 성장률 (%)
```

## 재무비율 (RatioResult)

```python
r = c.ratios

# 수익성
r.roe               # ROE (%)
r.roa               # ROA (%)
r.operatingMargin   # 영업이익률 (%)
r.netMargin         # 순이익률 (%)

# 안정성
r.debtRatio         # 부채비율 (%)
r.currentRatio      # 유동비율 (%)
r.netDebt           # 순부채 (원)
r.netDebtRatio      # 순부채비율 (%)
r.equityRatio       # 자기자본비율 (%)

# 현금흐름 / 성장성
r.fcf               # 자유현금흐름 (원)
r.revenueGrowth3Y   # 매출 3년 CAGR (%)

# TTM 값
r.revenueTTM            # 매출 TTM (원)
r.operatingIncomeTTM    # 영업이익 TTM (원)
r.netIncomeTTM          # 순이익 TTM (원)
r.operatingCashflowTTM  # 영업CF TTM (원)

# BS 최신값
r.totalAssets       # 자산총계 (원)
r.totalEquity       # 지배기업 자본 (원)
r.totalLiabilities  # 부채총계 (원)
r.cash              # 현금 (원)

# 밸류에이션 (시가총액 제공 시)
r.per               # PER
r.pbr               # PBR
r.psr               # PSR
r.evEbitda          # EV/EBITDA
```

직접 호출:

```python
from dartlab.engines.dart.finance import calcRatios, buildTimeseries

series, _ = buildTimeseries("005930")
r = calcRatios(series, marketCap=400_000_000_000_000)  # 시가총액 제공 시 밸류에이션 포함
```

## 주요 snakeId

### BS (재무상태표)

| snakeId | 한글 |
|---------|------|
| `total_assets` | 자산총계 |
| `current_assets` | 유동자산 |
| `non_current_assets` | 비유동자산 |
| `cash_and_equivalents` | 현금및현금성자산 |
| `inventories` | 재고자산 |
| `trade_receivables` | 매출채권 |
| `ppe` | 유형자산 |
| `intangible_assets` | 무형자산 |
| `total_liabilities` | 부채총계 |
| `current_liabilities` | 유동부채 |
| `short_term_borrowings` | 단기차입금 |
| `long_term_borrowings` | 장기차입금 |
| `bonds` | 사채 |
| `total_equity` | 지배기업 자본 |

### IS (손익계산서)

| snakeId | 한글 |
|---------|------|
| `revenue` | 매출액 |
| `cost_of_sales` | 매출원가 |
| `gross_profit` | 매출총이익 |
| `operating_income` | 영업이익 |
| `profit_before_tax` | 법인세비용차감전순이익 |
| `income_tax_expense` | 법인세비용 |
| `net_income` | 당기순이익 |
| `basic_eps` | 기본주당이익 |
| `diluted_eps` | 희석주당이익 |

### CF (현금흐름표)

| snakeId | 한글 |
|---------|------|
| `operating_cashflow` | 영업활동현금흐름 |
| `investing_cashflow` | 투자활동현금흐름 |
| `financing_cashflow` | 재무활동현금흐름 |
| `dividend_paid` | 배당금 지급 |

실제 매핑된 snakeId는 종목에 따라 수백~수천 개가 될 수 있다. 위 표는 가장 자주 쓰이는 핵심 계정만 정리한 것이다.

## 기업 간 비교

두 기업의 매출 시계열을 비교하는 예시:

```python
import dartlab

samsung = dartlab.Company("005930")
sk = dartlab.Company("000660")

s1, p1 = samsung.timeseries
s2, p2 = sk.timeseries

# 두 기업 모두 동일한 "revenue" 키로 접근
samsung_rev = s1["IS"]["revenue"]
sk_rev = s2["IS"]["revenue"]
```

동일한 snakeId 체계를 사용하므로, 어떤 두 기업이든 동일한 키로 비교할 수 있다.

## 금융업 특수성

은행, 보험, 증권사 등 금융업은 일반 제조업과 재무제표 구조가 다르다.

- `revenue`, `cost_of_sales`, `current_assets` 등이 없을 수 있다
- 부채비율이 500%를 넘는 것이 정상이다
- `interest_income`, `insurance_revenue` 같은 금융업 고유 계정이 존재한다

insight 엔진은 금융업을 자동 감지하여 별도 기준으로 분석한다.

