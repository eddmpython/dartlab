# scan/ — 상장사 전수 스캔 엔진

scan의 정식 축은 `network / governance / workforce / capital / debt / signal` 6개다.

- company-bound 축: `governance`, `workforce`, `capital`, `debt`
- market-level 축: `network`, `signal`

즉 scan 엔진은 6축이지만, `Company.get_scan_data()`와 company view는 여전히 4축만 다룬다.
`signal`은 `dartlab.signal()` market API로만 노출한다.

## 파일 구조

```
providers/dart/scan/
├── __init__.py              # available_scans() 목록
├── _helpers.py              # scan_parquets, parse_num, load_listing 등 공용 유틸
├── network/                 # 관계 네트워크 (별도 DEV.md)
├── signal/
│   └── __init__.py          # scan_signal() market-level docs keyword trend
├── governance/
│   ├── __init__.py          # scan_governance() 오케스트레이터
│   ├── scanner.py           # majorHolder, outsideDirector, executivePay, auditOpinion
│   └── scorer.py            # 4축 × 25점 = 100점 → A~E 등급
├── workforce/
│   ├── __init__.py          # scan_workforce() 오케스트레이터
│   ├── scanner.py           # employee, executivePayIndividual, revenue_per_employee
│   └── growth.py            # 급여성장률 vs 매출성장률 → 인건비부담
├── capital/
│   ├── __init__.py          # scan_capital() 오케스트레이터
│   ├── scanner.py           # dividend, treasuryStock, capitalChange
│   └── classifier.py        # 순환원 분류 (환원형/중립/희석형)
└── debt/
    ├── __init__.py          # scan_debt() 오케스트레이터
    ├── scanner.py           # corporateBond, finance BS 부채비율
    └── risk.py              # ICR 계산 + 위험등급 분류
```

## scan 프리빌드 (dart/scan/)

종목별 parquet 2700+개를 순차 스캔하면 수분 걸린다.
`dart/scan/`에 프리빌드 합산 parquet을 두면 **17초**로 단축된다.

### 구조

```
data/dart/scan/
├── changes.parquet              docs 변화 전종목 5Y (47MB, 1.9M행)
├── finance.parquet              finance 전종목 5Y (197MB, 11.7M행)
└── report/                      apiType별 분리 (10개, 합계 27MB)
    ├── majorHolder.parquet
    ├── executive.parquet
    ├── employee.parquet
    ├── dividend.parquet
    ├── treasuryStock.parquet
    ├── capitalChange.parquet
    ├── corporateBond.parquet
    ├── auditOpinion.parquet
    ├── executivePayAllTotal.parquet
    └── executivePayIndividual.parquet
```

### 빌드/배포 흐름

```
배포자: dartlab collect --scan → data/dart/scan/ 생성 → HF push
사용자: downloadAll("scan") (271MB) → 즉시 횡단 분석 가능
        (전종목 원본 8GB+ 불필요)
```

scan 파일이 없으면 `_helpers._ensureScanData()`가 HF에서 자동 다운로드를 시도한다.
다운로드 실패 시 기존 종목별 순회로 fallback.

### 가속 경로

scan/finance.parquet을 감지하면 종목별 파일 순회를 건너뛰고 단일 파일에서 즉시 처리한다.
감지 실패 시 기존 종목별 순회로 자동 fallback.

**market/_helpers.py** — 6축 scan 엔진용:
- `scan_parquets(apiType)` → `scan/report/{apiType}.parquet` 우선
- `scan_finance_parquets()` → `scan/finance.parquet` 우선

**providers/dart/finance/scanAccount.py** — 범용 계정/비율 조회:
- `scanAccount()` → `_scanAccountFromMerged()` 가속 경로
- `scanRatio()` → 내부에서 `scanAccount()` 2회 호출하므로 자동 가속

**축별 scanner** — 개별 가속 함수 내장:
- `debt/scanner.py` → `_debtMixFromMerged()` (scan_debt_mix)
- `workforce/scanner.py` → `_revenueFromMerged()` (scan_revenue_per_employee)

### 자동 다운로드

`_helpers._ensureScanData()` + `scanAccount`의 `_ensureScanData()` 호출:
1. `data/dart/scan/` 디렉토리에 parquet이 있으면 즉시 사용
2. 없으면 `downloadAll("scan")`으로 HF에서 자동 다운로드 (271MB)
3. 다운로드 실패 시 기존 종목별 순회로 fallback
4. 세션 내 1회만 체크 (`_scanDownloaded` 플래그)

### 속도 실측

| 구간 | scan 프리빌드 전 | scan 프리빌드 후 |
|------|-----------------|-----------------|
| buildScanSnapshot 전체 | 4분+ | **17초** |
| scan_parquets(majorHolder) | 수십 초 | **21ms** |
| scan_finance_parquets(IS) | 수분 | **494ms** |
| scan_debt_mix | 11초 | **0.5초** |
| scan_revenue_per_employee | 12초 | **0.5초** |
| scanAccount("매출액") 분기별 | 3초+ | **0.37초** |
| scanAccount("매출액") 연간 | 3초+ | **0.30초** |
| scanRatio("roe") 연간 | 6초+ | **0.54초** |
| scanRatio("operatingMargin") 분기별 | 6초+ | **0.55초** |

## 데이터 흐름

```
[프리빌드 경로 — scan 파일 존재 시]
data/dart/scan/report/{apiType}.parquet
  ↓ _helpers.scan_parquets() — 단일 파일 즉시 로드
apiType별 DataFrame

data/dart/scan/finance.parquet
  ↓ _helpers.scan_finance_parquets() — 단일 파일 필터
종목별 dict

[기존 경로 — fallback]
DART report parquet (employee, dividend, majorHolder, ...)
  ↓ _helpers.scan_parquets(apiType, keep_cols)
apiType별 DataFrame (전 종목)

공통:
  ↓ scanner.py: scan_*() 함수
종목별 dict (핵심 지표)
  ↓ scorer.py / classifier.py / risk.py
등급/분류/위험도
  ↓ __init__.py: scan_*() 오케스트레이터
종합 pl.DataFrame
  ↓ Company.governance() / .workforce() / .capital() / .debt()
view별 필터 (이 회사 / 전체 / 시장별)

DART docs parquet (sections)
  ↓ signal.scan_signal()
연도 × 키워드 × category 집계
  ↓ dartlab.signal()
시장 단위 keyword trend DataFrame

[scanAccount/scanRatio 경로]
data/dart/scan/finance.parquet
  ↓ scanAccount._scanAccountFromMerged()
  ↓ sjDiv+CFS 필터 → 계정 매칭 → 분기 standalone 계산
  ↓ pivot → 전종목 × 기간 DataFrame
  ↓ scanRatio: scanAccount(분자) / scanAccount(분모) → 비율

[fallback — scan 파일 없을 때]
data/dart/finance/{stockCode}.parquet × 2700+
  ↓ _FileProcessor (ThreadPoolExecutor 병렬)
  ↓ 종목별 CFS 필터 → 계정 매칭 → standalone
  ↓ concat → pivot → 동일 출력
```

## 공용 유틸 (_helpers.py)

| 함수 | 역할 |
|------|------|
| `scan_parquets(api_type, keep_cols)` | report parquet LazyFrame 스캔 → DataFrame |
| `parse_num(s)` | 문자열/숫자 → float (쉼표, `-`, 빈값 처리) |
| `find_latest_year(raw, check_col, min_count)` | 유효 데이터 min_count 이상인 최신 연도 |
| `pick_best_quarter(df)` | 최적 분기 필터 (Q2 > Q4 > Q3 > Q1) |
| `load_listing()` | 상장사 목록 (network/scanner.py 위임) |
| `parse_date_year(s)` | 날짜 문자열 → 연도 int |
| `scan_finance_parquets(statement, account_ids, account_nms)` | finance parquet 전수 스캔 → {code: value} |

### scan_parquets vs network/scanner.py의 _scan_parquets

- `_helpers.scan_parquets`: available-columns 필터링 포함, 새 축에서 사용
- `network/scanner.py._scan_parquets`: 기존 버전 유지 (backward compatibility)

## 축별 상세

### governance (지배구조)

**소스**: majorHolder, executive(사외이사), executivePayAllTotal + employee(보수비율), auditOpinion

| scanner 함수 | 출력 |
|-------------|------|
| `scan_major_holder_pct()` | {code: 지분율%} |
| `scan_outside_directors()` | {code: 사외이사비율%} |
| `scan_pay_ratio()` | {code: 임원/직원 보수비율} |
| `scan_audit_opinion()` | {code: 감사의견} |

**scoring (scorer.py)**:
- 4축 × 25점 = 100점 만점
- `score_ownership`: 30~50% 최적(25점), 극단치 감점
- `score_outside_ratio`: 40%+ 만점(25점), 0% 최저(3점)
- `score_pay_ratio`: ≤2배 만점(25점), 20배+ 최저(3점)
- `score_audit`: 적정(25점), 한정(5점), 부적정/거절(0점)
- 등급: A(85+) B(70+) C(55+) D(40+) E(<40)

**DataFrame 컬럼**: 종목코드, 지분율, 사외이사비율, pay_ratio, 감사의견, S_지분, S_사외, S_보수, S_감사, 총점, 등급, 유효축수

### workforce (인력/급여)

**소스**: employee, executivePayIndividual, finance IS

| scanner/growth 함수 | 출력 |
|--------------------|------|
| `scan_employee()` | {code: {직원수, 평균급여_만원, 남녀격차, 근속_년}} |
| `scan_revenue_per_employee()` | {code: 직원당매출_억} |
| `scan_salary_growth()` | {code: {급여성장률, 급여_신, 급여_구}} |
| `scan_revenue_growth()` | {code: 매출성장률%} |
| `compute_salary_vs_revenue()` | DataFrame(종목코드, 급여성장률, 매출성장률, 인건비부담) |
| `scan_top_pay()` | {code: {공개인원, 최고보수_억}} |

**인건비부담** = 급여성장률 - 매출성장률 (양수 = 인건비 부담↑)

**DataFrame 컬럼**: 종목코드, 직원수, 평균급여_만원, 남녀격차, 근속_년, 직원당매출_억, 급여성장률, 매출성장률, 인건비부담, 최고보수_억, 공개인원

### capital (주주환원)

**소스**: dividend, treasuryStock, capitalChange

| scanner 함수 | 출력 |
|-------------|------|
| `scan_dividend()` | {code: {배당여부, DPS, 배당수익률}} |
| `scan_treasury_stock()` | {code: {자사주보유, 당기취득}} |
| `scan_capital_change()` | {code: {최근증자, 증자유형}} |

**분류 (classifier.py)**:
- return_score = +1(배당) +1(자사주취득) -1(최근증자)
- ≥1 → "환원형", 0 → "중립", <0 → "희석형"
- 모순형: 배당 AND 최근증자 동시

**DataFrame 컬럼**: 종목코드, 배당여부, DPS, 배당수익률, 자사주보유, 자사주취득, 최근증자, 환원점수, 분류, 모순형

### debt (부채 구조)

**소스**: corporateBond, finance BS, finance IS

| scanner/risk 함수 | 출력 |
|------------------|------|
| `scan_bonds()` | {code: {사채잔액, 단기잔액, 단기비중}} |
| `scan_debt_mix()` | {code: {총부채, 부채비율}} |
| `scan_icr()` | {code: ICR} |

**위험등급 (risk.py)**:
- ICR = 영업이익 / 이자비용
- 고위험: 단기비중 ≥ 50% AND ICR < 1
- 주의: 단기비중 ≥ 50% OR ICR < 1
- 관찰: ICR < 3
- 안전: ICR ≥ 3

**DataFrame 컬럼**: 종목코드, 사채잔액, 단기잔액, 단기비중, 총부채, 부채비율, ICR, 위험등급

## 인터페이스 경계

`providers/dart/company.py`의 company-bound scan 메서드는 4개만 유지한다:

```python
c = dartlab.Company("005930")

# 이 회사 (view=None)
c.governance()     # 삼성전자 거버넌스 1행
c.workforce()      # 삼성전자 인력 1행
c.capital()        # 삼성전자 주주환원 1행
c.debt()           # 삼성전자 부채 1행

# 전체 (view="all")
c.governance("all")   # 전체 상장사 DataFrame

# 시장별 요약 (view="market")
c.governance("market")  # 유가/코스닥/코넥스 요약 통계

# 모듈 레벨 (전체 스캔)
dartlab.governance()
dartlab.workforce()
dartlab.capital()
dartlab.debt()
```

`signal`은 company-bound API로 연결하지 않는다:

```python
df = dartlab.signal()        # 전체 키워드 트렌드
df = dartlab.signal("AI")    # 특정 키워드 연도별 추이
```

현재 `signal` 결과는 local docs corpus에 존재하는 기업 범위에 한정된다.
즉 시장 전체를 대표하는 실험적 market scan이지만, finance/report 기반 4축처럼 전종목 완전 커버리지는 아니다.

`_ensure*()` 메서드가 `scan_*(verbose=False)`를 1회 실행하고 `_cache`에 저장.
`_scanView(df, view)`가 view 분기 처리 (None=이 회사, "all"=전체, "market"=시장별).

## 검증 데이터

- 소스 실험: `experiments/073_scanInsight/` (18개 실험 완료)
- signal 재검증: `experiments/076_marketLab/013_signalRevalidation.py`
- 거버넌스: 001~005, 인력: 006~009, 주주환원: 010~013, 부채: 014~016, 교차검증: 017~018
- 실험 017: 4축 교차 상관분석 (거버넌스↔배당, 부채↔지배구조)
- 실험 018: 시장별 분포 비교 (유가/코스닥 통계)

## 금지

- scanner 내부에서 Company를 import하지 않는다 (역의존)
- Company에서 `scan_*` 직접 import 금지 — 반드시 `_ensure*()` 경유
- `_helpers.py`의 공용 유틸을 수정할 때는 기존 축에 영향 없는지 확인
- 실험 없이 스코어링/분류 로직 변경 금지
