# dart/report 엔진 스펙

## 역할

OpenDART 정기보고서 API 데이터 → **apiType별 추출/정제/피벗**.
배당, 직원, 최대주주, 임원, 감사 등 정기보고서에 의무 기재되는 구조화된 항목을 시계열로 제공.

**핵심 가치**: DART API가 제공하는 정형 데이터의 정확한 시계열화.

## 데이터 소스

- **원본**: `data/dart/report/{stockCode}.parquet`
- **GitHub Release**: `data-report-{1..4}` (4개 shard)
- **기간**: 2015년~ (분기별 데이터)
- **수집**: eddmpython이 OpenDART API 28개를 호출하여 parquet으로 통합 저장
- **갱신 주기**: 분기 보고서 제출 후

## 원본 parquet 구조

하나의 parquet에 모든 apiType이 `apiType` 컬럼으로 구분되어 저장.

| 공통 컬럼 | 설명 |
|-----------|------|
| `stockCode` | 종목코드 |
| `year` | 사업연도 |
| `quarter` | 분기명 (1분기/2분기/3분기/4분기) |
| `apiType` | API 종류 (22개) |
| `stlm_dt` | 결산일 |

나머지 컬럼은 apiType별로 다르며, null이 아닌 것만 유효.

## 전체 apiType 목록 (22개)

### 주주/지배구조 (6개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `majorHolder` | 최대주주현황 | Q2 | nm, relate, stock_knd, trmend_posesn_stock_co, trmend_posesn_stock_qota_rt |
| `majorHolderChange` | 최대주주변동 | Q2 | mxmm_shrholdr_nm, change_on, change_cause |
| `minorityHolder` | 소액주주현황 | Q2 | se, shrholdr_co, shrholdr_tot_co, shrholdr_rate |
| `outsideDirector` | 사외이사현황 | Q2 | nm, main_career, apnt, rlsofc |
| `executive` | 임원현황 | Q2 | nm, sexdstn, birth_ym, ofcps, rgist_exctv_at, mxmm_shrholdr_relate |
| `stockTotal` | 주식총수현황 | Q2 | se, istc_totqy, tesstk_co, distb_stock_co |

### 보수 (4개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `executivePayAllTotal` | 임원보수전체 | Q2 | se, nmpr, mendng_totamt, jan_avrg_mendng_am, rm |
| `executivePayIndividual` | 임원보수개인별 | Q2 | nm, ofcps, mendng_totamt, mendng_totamt_ct_incls_mendng |
| `topPay` | 개인별보수(5억+) | Q2 | nm, ofcps, mendng_totamt |
| `unregisteredExecutivePay` | 미등기임원보수 | Q2 | nmpr, mendng_totamt, jan_avrg_mendng_am |

### 배당/감사 (4개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `dividend` | 배당 | Q4 | se, stock_knd, thstrm, frmtrm, lwfr |
| `auditOpinion` | 감사의견 | Q4 | adt_opinion, adtor, adt_reprt_spcmnt_matter |
| `auditContract` | 감사용역체결 | Q4 | adtor, audting_trm, cn, mendng |
| `nonAuditContract` | 비감사용역계약 | Q4 | cntrct_cncls_de, servc_cn, servc_exc_pd, mendng |

### 자본/자금 (4개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `capitalChange` | 증자감자현황 | Q2 | isu_dcrs_de, isu_dcrs_stle, isu_dcrs_stock_knd, isu_dcrs_qy |
| `treasuryStock` | 자기주식현황 | Q2 | stock_knd, bgtmn_trmend_qy, acqs_qy, dsps_qy, trmend_qy |
| `publicOfferingUsage` | 공모자금사용내역 | Q2 | se_nm, on_dclrt_cptal_use_plan, real_cptal_use_sttus |
| `privateOfferingUsage` | 사모자금사용내역 | Q2 | se_nm, cptal_use_plan, real_cptal_use_sttus |

### 직원/투자 (2개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `employee` | 직원현황 | Q2 | sexdstn, sm, fyer_salary_totamt, jan_salary_am |
| `investedCompany` | 타법인출자현황 | Q2 | inv_prm, frst_acqs_de, invstmnt_purps, trmend_blce_qy, trmend_blce_qota_rt |

### 채무 (2개)

| apiType | 한글명 | 기준분기 | 주요 컬럼 |
|---------|--------|----------|-----------|
| `corporateBond` | 회사채미상환잔액 | Q2 | tm, knd, issue_de, expire_de, balace |
| `shortTermBond` | 단기사채미상환잔액 | Q2 | tm, nm, issue_de, expire_de, balace |

### eddmpython에 있지만 미수집 (6개)

아래 apiType은 eddmpython에 정의되어 있으나 현재 parquet에 포함되지 않음:

| apiType | 한글명 | 미수집 사유 |
|---------|--------|-------------|
| `debtSecurities` | 채무증권발행실적 | 대부분 회사에 해당 없음 |
| `commercialPaper` | 기업어음증권미상환잔액 | 일부 금융회사만 |
| `hybridSecurities` | 채권혼합증권미상환잔액 | 일부 금융회사만 |
| `contingentCapital` | 조건부자본증권미상환잔액 | 은행/보험만 |
| `executivePayTotal` | 이사/감사전체보수(구) | executivePayAllTotal로 대체 |
| `executivePayByType` | 유형별보수(구) | executivePayAllTotal로 대체 |

## 추출 레이어 (extract.py)

4단계 추출 파이프라인:

| 함수 | 설명 | 반환 |
|------|------|------|
| `extractRaw(stockCode, apiType)` | parquet에서 apiType 필터 + null컬럼 제거 + 정렬 | `pl.DataFrame` |
| `extractClean(stockCode, apiType)` | + 숫자 변환 (70%+ 변환률이면 Float64) | `pl.DataFrame` |
| `extractAnnual(stockCode, apiType, quarterNum)` | + 특정분기 필터 (기본: PREFERRED_QUARTER) | `pl.DataFrame` |
| `extractResult(stockCode, apiType, quarterNum)` | + ReportResult 래핑 | `ReportResult` |

### PREFERRED_QUARTER

- Q4 (사업보고서): dividend, auditOpinion, auditContract, nonAuditContract
- Q2 (반기보고서): 나머지 전체

Q2에 데이터 없으면 Q4 fallback, 역도 동일.

## 피벗 함수 (pivot.py) — 현재 5개

| 함수 | 반환 타입 | 주요 지표 |
|------|-----------|-----------|
| `pivotDividend(stockCode)` | `DividendResult` | years, dps, dividendYield, stockDividend, stockDividendYield |
| `pivotEmployee(stockCode)` | `EmployeeResult` | years, totalEmployee, avgMonthlySalary, totalAnnualSalary |
| `pivotMajorHolder(stockCode)` | `MajorHolderResult` | years, totalShareRatio, latestHolders (top 10) |
| `pivotExecutive(stockCode)` | `ExecutiveResult` | df, totalCount, registeredCount, outsideCount |
| `pivotAudit(stockCode)` | `AuditResult` | years, opinions, auditors |

## 피벗 미구현 apiType (17개)

| apiType | 한글명 | 피벗 필요성 |
|---------|--------|-------------|
| `majorHolderChange` | 최대주주변동 | 이벤트 목록 (피벗보다 목록 제공) |
| `minorityHolder` | 소액주주현황 | 소액주주비율 시계열 |
| `outsideDirector` | 사외이사현황 | 사외이사 구성 목록 |
| `stockTotal` | 주식총수현황 | 발행/유통주식수 시계열 |
| `executivePayAllTotal` | 임원보수전체 | 유형별 보수총액 시계열 |
| `executivePayIndividual` | 임원보수개인별 | 최신 개인별 보수 목록 |
| `topPay` | 개인별보수(5억+) | 고액보수 목록 |
| `unregisteredExecutivePay` | 미등기임원보수 | 미등기임원 보수 시계열 |
| `capitalChange` | 증자감자현황 | 이벤트 목록 |
| `treasuryStock` | 자기주식현황 | 자기주식 시계열 |
| `publicOfferingUsage` | 공모자금사용내역 | 사용실적 대비표 |
| `privateOfferingUsage` | 사모자금사용내역 | 사용실적 대비표 |
| `investedCompany` | 타법인출자현황 | 투자 포트폴리오 |
| `corporateBond` | 회사채미상환잔액 | 만기별 잔액 |
| `shortTermBond` | 단기사채미상환잔액 | 만기별 잔액 |
| `auditContract` | 감사용역체결 | 감사보수/시간 시계열 |
| `nonAuditContract` | 비감사용역계약 | 비감사서비스 목록 |

## Result 타입 (types.py)

| 타입 | 필드 | 용도 |
|------|------|------|
| `ReportResult` | apiType, label, df, years, nYears | 범용 |
| `DividendResult` | years, dps, dividendYield, stockDividend, stockDividendYield, df | 배당 시계열 |
| `EmployeeResult` | years, totalEmployee, avgMonthlySalary, totalAnnualSalary, df | 직원 시계열 |
| `MajorHolderResult` | years, totalShareRatio, latestHolders, df | 주주 시계열 |
| `ExecutiveResult` | df, totalCount, registeredCount, outsideCount | 임원 스냅샷 |
| `AuditResult` | years, opinions, auditors, df | 감사의견 시계열 |

## 파일 구조

```
engines/dart/report/
├── __init__.py     # 재수출 (extract*, pivot*)
├── extract.py      # 4단계 추출 파이프라인
├── pivot.py        # apiType별 시계열 피벗 (5개)
├── types.py        # API_TYPES, Result 타입, 컬럼 메타
└── SPEC.md         # 이 파일
```

## Company에서의 활용

### 현재: _ReportAccessor (c.report.*)

| 접근 | 함수 | 반환 |
|------|------|------|
| `c.report.dividend` | `pivotDividend` | DividendResult |
| `c.report.employee` | `pivotEmployee` | EmployeeResult |
| `c.report.majorHolder` | `pivotMajorHolder` | MajorHolderResult |
| `c.report.executive` | `pivotExecutive` | ExecutiveResult |
| `c.report.audit` | `pivotAudit` | AuditResult |
| `c.report.extract(apiType)` | `extractClean` | DataFrame |
| `c.report.extractAnnual(apiType, qNum)` | `extractAnnual` | DataFrame |

### docs와의 중복

| 데이터 | docs (현재 c.dividend 등) | report (c.report.dividend 등) |
|--------|--------------------------|-------------------------------|
| 배당 | HTML 파싱, 1999~ | API 정형, 2015~ |
| 직원 | HTML 파싱, 1999~ | API 정형, 2015~ |
| 최대주주 | HTML 파싱, 1999~ | API 정형, 2015~ |
| 임원 | HTML 파싱, 1999~ | API 정형, 2015~ |
| 감사 | HTML 파싱, 1999~ | API 정형, 2015~ |

**report가 더 정확하고 구조화됨** (API 정형 데이터 vs HTML 파싱).
단, docs가 **기간이 더 넓음** (1999~ vs 2015~).

## eddmpython 출처

eddmpython `core/dart/getDart/v2/config.py`에 28개 API 정의:
- `dividend`, `employee`, `executive` 등 22개가 현재 수집됨
- 6개는 일부 업종만 해당되어 미수집
