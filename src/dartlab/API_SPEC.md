# dartlab API 스팩

## 공통 규칙

- 모든 pipeline 함수는 `stockCode: str` (6자리 종목코드)를 첫 번째 인자로 받는다
- 내부에서 `core.loadData(stockCode)` → DataFrame 로딩
- 반환 타입은 각 모듈의 Result dataclass 또는 None (데이터 부족 시)
- 모든 Result는 `corpName` 필드를 공통으로 가진다
- 시계열 모듈은 `nYears` (기간 수) 포함, 스냅샷 모듈은 `year` (기준연도) 포함
- period 파라미터를 받는 모듈만 `period` 필드 포함

## Company 클래스

```python
from dartlab import Company

c = Company("005930")       # 생성 시 데이터 로딩 + 기업명 추출
c.corpName                  # "삼성전자"
```

종목코드 하나로 16개 분석 모듈에 접근하는 통합 래퍼.
각 메서드는 기존 pipeline 함수에 `stockCode`를 넘기는 얇은 래퍼다.

### 인덱스·메타

| 메서드 | 파라미터 | 반환 타입 | 설명 |
|--------|----------|-----------|------|
| `Company.status()` | - | DataFrame | 로컬 보유 전체 종목 인덱스 (static) |
| `docs()` | - | DataFrame | 이 종목의 공시 문서 목록 + DART 뷰어 링크 |

`status()` 반환 컬럼: `stockCode, corpName, rows, yearFrom, yearTo, nDocs`
`docs()` 반환 컬럼: `year, reportType, rceptDate, rceptNo, dartUrl`

### 분석 메서드

| 메서드 | 파라미터 | 반환 타입 | 설명 |
|--------|----------|-----------|------|
| `analyze()` | ifrsOnly, period | AnalysisResult | 요약재무정보 + 브릿지 매칭 + 전환점 |
| `statements()` | ifrsOnly, period | StatementsResult | BS·IS·CF 시계열 |
| `segments()` | period | SegmentsResult | 부문별 보고 |
| `costByNature()` | period | CostByNatureResult | 비용의 성격별 분류 |
| `majorHolder()` | - | MajorHolderResult | 최대주주 현황 시계열 |
| `holderOverview()` | - | HolderOverview | 5% 주주·소액주주·의결권 |
| `shareCapital()` | - | ShareCapitalResult | 발행·자기·유통 주식 |
| `dividend()` | - | DividendResult | 배당 시계열 |
| `employee()` | - | EmployeeResult | 직원 현황 시계열 |
| `subsidiary()` | - | SubsidiaryResult | 타법인출자 현황 |
| `bond()` | - | BondResult | 채무증권 발행실적 |
| `affiliates()` | period | AffiliatesResult | 관계기업 투자 |
| `business()` | - | BusinessResult | 사업의 내용 섹션 + 변경 탐지 |
| `overview()` | - | OverviewResult | 회사의 개요 정량 데이터 |
| `mdna()` | - | MdnaResult | 경영진단 및 분석의견 |
| `rawMaterial()` | - | RawMaterialResult | 원재료·유형자산·시설투자 |

모든 메서드는 데이터 부족 시 `None`을 반환한다.

## finance.summary

```python
from dartlab.finance.summary import analyze

result = analyze("005930")
result = analyze("005930", ifrsOnly=True, period="y")
```

### analyze(stockCode, ifrsOnly=True, period="y") -> AnalysisResult | None

요약재무정보 시계열 추출 + 브릿지 매칭 + 전환점 탐지.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| ifrsOnly | bool | True | K-IFRS 이후(2011~)만 분석 |
| period | str | "y" | "y" (연간) \| "q" (분기) \| "h" (반기) |

### AnalysisResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 기간 수 |
| period | str | "y" \| "q" \| "h" |
| allRate | float \| None | 전체 매칭률 |
| contRate | float \| None | 연속 구간 매칭률 |
| segments | list[Segment] | 구간 목록 |
| breakpoints | list[BridgeResult] | 전환점 목록 |
| FS | DataFrame \| None | 전체 재무제표 |
| BS | DataFrame \| None | 재무상태표 |
| IS | DataFrame \| None | 손익계산서 |

## finance.statements

```python
from dartlab.finance.statements import statements

result = statements("005930")
result = statements("005930", ifrsOnly=True, period="y")
```

### statements(stockCode, ifrsOnly=True, period="y") -> StatementsResult | None

연결재무제표에서 BS, IS, CF 시계열 DataFrame 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| ifrsOnly | bool | True | K-IFRS 이후(2011~)만 |
| period | str | "y" | "y" \| "q" \| "h" |

### StatementsResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 기간 수 |
| period | str | "y" \| "q" \| "h" |
| BS | DataFrame \| None | 재무상태표 |
| IS | DataFrame \| None | 손익계산서 |
| CF | DataFrame \| None | 현금흐름표 |

## finance.segment

```python
from dartlab.finance.segment import segments

result = segments("005930")
result = segments("005930", period="y")
```

### segments(stockCode, period="y") -> SegmentsResult | None

연결재무제표 주석에서 부문별 보고 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| period | str | "y" | "y" \| "q" \| "h" |

### SegmentsResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| period | str | "y" \| "q" \| "h" |
| tables | dict[str, list[SegmentTable]] | {year: [tables]} |
| revenue | DataFrame \| None | 부문별 매출 시계열 |

## finance.affiliate

```python
from dartlab.finance.affiliate import affiliates

result = affiliates("005930")
result = affiliates("005930", period="y")
```

### affiliates(stockCode, period="y") -> AffiliatesResult | None

연결재무제표 주석에서 관계기업/공동기업 투자 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| period | str | "y" | "y" \| "q" \| "h" |

### AffiliatesResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| period | str | "y" \| "q" \| "h" |
| profiles | dict[str, list[AffiliateProfile]] | {year: [profiles]} |
| movements | dict[str, list[AffiliateMovement]] | {year: [movements]} |
| movementDf | DataFrame \| None | 기업별 변동 시계열 |

## finance.dividend

```python
from dartlab.finance.dividend import dividend

result = dividend("005930")
```

### dividend(stockCode) -> DividendResult | None

사업보고서 "배당에 관한 사항"에서 배당지표 시계열 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### DividendResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| timeSeries | DataFrame \| None | 배당 시계열 (year, netIncome, eps, totalDividend, payoutRatio, dividendYield, dps, dpsPreferred) |

## finance.employee

```python
from dartlab.finance.employee import employee

result = employee("005930")
```

### employee(stockCode) -> EmployeeResult | None

사업보고서 "직원 등의 현황"에서 직원 현황 시계열 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### EmployeeResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| timeSeries | DataFrame \| None | 직원 시계열 (year, totalEmployees, avgTenure, totalSalary, avgSalary) |

## finance.majorHolder

```python
from dartlab.finance.majorHolder import majorHolder, holderOverview

result = majorHolder("005930")
overview = holderOverview("005930")
```

### majorHolder(stockCode) -> MajorHolderResult | None

사업보고서 "주주에 관한 사항"에서 최대주주 현황 시계열 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### MajorHolderResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| majorHolder | str \| None | 최대주주명 (최신) |
| majorRatio | float \| None | 최대주주 보통주 지분율 (%) |
| totalRatio | float \| None | 특수관계인 합계 지분율 (%) |
| holders | list[Holder] | 최신 연도 특수관계인 목록 |
| timeSeries | DataFrame \| None | 최대주주 시계열 (year, majorHolder, majorRatio, totalRatio, holderCount) |

### holderOverview(stockCode) -> HolderOverview | None

사업보고서에서 5% 이상 주주, 소액주주, 의결권 현황 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### HolderOverview

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| year | int \| None | 기준 사업연도 |
| bigHolders | list[BigHolder] | 5% 이상 주주 (name, shares, ratio) |
| minority | Minority \| None | 소액주주 현황 |
| voting | VotingRights \| None | 의결권 현황 |

### Minority

| 필드 | 타입 | 설명 |
|------|------|------|
| holders | int | 소액주주 수 |
| totalHolders | int | 전체 주주 수 |
| holderPct | float | 소액주주 비율 (%) |
| shares | int | 소액주주 보유 주식수 |
| totalShares | int | 총 발행주식수 |
| sharePct | float | 소액주주 주식 비율 (%) |

### VotingRights

| 필드 | 타입 | 설명 |
|------|------|------|
| issuedCommon/Pref | float \| None | 발행주식총수 |
| noVoteCommon/Pref | float \| None | 의결권 없는 주식수 |
| excludedCommon/Pref | float \| None | 정관에 의한 배제 |
| restrictedCommon/Pref | float \| None | 법률에 의한 제한 |
| restoredCommon/Pref | float \| None | 의결권 부활 |
| votableCommon/Pref | float \| None | 의결권 행사 가능 주식수 |

## finance.subsidiary

```python
from dartlab.finance.subsidiary import subsidiary

result = subsidiary("005930")
```

### subsidiary(stockCode) -> SubsidiaryResult | None

사업보고서 "타법인출자 현황(상세)"에서 자회사/투자 포트폴리오 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### SubsidiaryInvestment

| 필드 | 타입 | 설명 |
|------|------|------|
| name | str | 법인명 |
| listed | str \| None | 상장여부 ("상장" / "비상장") |
| firstAcquired | str \| None | 최초취득일자 |
| purpose | str \| None | 출자목적 ("경영참여" / "단순투자" 등) |
| firstAmount | float \| None | 최초취득금액 |
| beginShares | float \| None | 기초 수량 |
| beginRatio | float \| None | 기초 지분율 (%) |
| beginBook | float \| None | 기초 장부가액 |
| acquiredShares | float \| None | 취득(처분) 수량 |
| acquiredAmount | float \| None | 취득(처분) 금액 |
| valuationGain | float \| None | 평가손익 |
| endShares | float \| None | 기말 수량 |
| endRatio | float \| None | 기말 지분율 (%) |
| endBook | float \| None | 기말 장부가액 |
| totalAssets | float \| None | 피투자법인 총자산 |
| netIncome | float \| None | 피투자법인 당기순손익 |

### SubsidiaryResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| investments | list[SubsidiaryInvestment] | 최신 연도 투자 목록 |
| timeSeries | DataFrame \| None | 투자 시계열 (year, totalCount, listedCount, unlistedCount, totalBook) |

## finance.shareCapital

```python
from dartlab.finance.shareCapital import shareCapital

result = shareCapital("005930")
```

### shareCapital(stockCode) -> ShareCapitalResult | None

사업보고서 "주식의 총수 등"에서 발행주식/자기주식/유통주식 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### ShareCapitalResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| authorizedShares | float \| None | 발행할 주식의 총수 (정관) |
| issuedShares | float \| None | 현재까지 발행한 주식의 총수 |
| retiredShares | float \| None | 현재까지 감소한 주식의 총수 |
| outstandingShares | float \| None | 발행주식의 총수 (보통주 기준) |
| treasuryShares | float \| None | 자기주식수 |
| floatingShares | float \| None | 유통주식수 |
| treasuryRatio | float \| None | 자기주식 보유비율 (%) |
| timeSeries | DataFrame \| None | 주식 시계열 (year, outstandingShares, treasuryShares, floatingShares, treasuryRatio) |

## finance.bond

```python
from dartlab.finance.bond import bond

result = bond("005930")
```

### bond(stockCode) -> BondResult | None

사업보고서 "증권의 발행을 통한 자금조달에 관한 사항"에서 채무증권 발행실적 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### BondIssuance

| 필드 | 타입 | 설명 |
|------|------|------|
| issuer | str | 발행회사 |
| bondType | str \| None | 증권종류 |
| method | str \| None | 발행방법 |
| issueDate | str \| None | 발행일자 |
| amount | float \| None | 권면총액 |
| interestRate | str \| None | 이자율 |
| rating | str \| None | 평가등급 |
| maturityDate | str \| None | 만기일 |
| redeemed | str \| None | 상환여부 |
| underwriter | str \| None | 주관회사 |

### BondResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| issuances | list[BondIssuance] | 최신 연도 채무증권 목록 |
| timeSeries | DataFrame \| None | 채무증권 시계열 (year, totalIssuances, totalAmount, unredeemedCount) |

## finance.business

```python
from dartlab.finance.business import business

result = business("005930")
```

### business(stockCode) -> BusinessResult | None

사업보고서 "II. 사업의 내용"에서 하위 섹션 추출 + 연도별 변경 탐지.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### BusinessSection

| 필드 | 타입 | 설명 |
|------|------|------|
| key | str | 분류 키 (overview, products, materials, sales, risk, rnd, etc, financial) |
| title | str | 원본 섹션 제목 |
| chars | int | 텍스트 길이 |
| text | str | 섹션 전체 내용 |

### BusinessChange

| 필드 | 타입 | 설명 |
|------|------|------|
| year | int | 변경 감지 연도 |
| changedPct | float | 변경률 (%) — 30 초과 시 유의미한 변화 |
| added | int | 추가된 줄 수 |
| removed | int | 삭제된 줄 수 |
| totalChars | int | 해당 연도 텍스트 총 길이 |

### BusinessResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| year | int | 기준 사업연도 (최신) |
| sections | list[BusinessSection] | 하위 섹션 목록 |
| changes | list[BusinessChange] | 연도별 변경 정보 |

## finance.companyOverview

```python
from dartlab.finance.companyOverview import companyOverview

result = companyOverview("005930")
```

### companyOverview(stockCode) -> OverviewResult | None

사업보고서 "I. 회사의 개요" → "1. 회사의 개요"에서 정량 데이터 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### CreditRating

| 필드 | 타입 | 설명 |
|------|------|------|
| agency | str | 평가기관 (한국신용평가, Moody's 등) |
| grade | str | 신용등급 (AA+, Aa2 등) |

### OverviewResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| year | int | 기준 사업연도 |
| founded | str \| None | 설립일자 (YYYY-MM-DD) |
| address | str \| None | 본사 주소 |
| homepage | str \| None | 홈페이지 URL |
| subsidiaryCount | int \| None | 연결대상 종속기업 수 |
| isSME | bool \| None | 중소기업 해당 여부 |
| isVenture | bool \| None | 벤처기업 해당 여부 |
| creditRatings | list[CreditRating] | 신용등급 목록 |
| listedDate | str \| None | 상장일 (YYYY-MM-DD) |
| missing | list[str] | 원문에 해당 항목이 없는 필드 |
| failed | list[str] | 항목은 있지만 파싱 실패한 필드 |

## finance.mdna

```python
from dartlab.finance.mdna import mdna

result = mdna("005930")
```

### mdna(stockCode) -> MdnaResult | None

사업보고서 "이사의 경영진단 및 분석의견"에서 MD&A 텍스트 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### MdnaSection

| 필드 | 타입 | 설명 |
|------|------|------|
| title | str | 섹션 제목 (예: "2. 개요") |
| category | str | 분류 (overview, forecast, financials, liquidity, offBalance, other, ...) |
| text | str | 섹션 전체 내용 |
| textLines | int | 텍스트 줄 수 |
| tableLines | int | 테이블 줄 수 |

### MdnaResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 연도 수 |
| sections | list[MdnaSection] | 최신 연도 섹션 목록 |
| overview | str \| None | 개요 텍스트 (테이블 제외) |

## finance.rawMaterial

```python
from dartlab.finance.rawMaterial import rawMaterial

result = rawMaterial("005930")
```

### rawMaterial(stockCode) -> RawMaterialResult | None

사업보고서 "원재료 및 생산설비" 섹션에서 원재료 매입, 유형자산, 시설투자 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |

### RawMaterialResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| year | int \| None | 기준 사업연도 |
| materials | list[RawMaterial] | 원재료 매입 항목 목록 |
| equipment | Equipment \| None | 유형자산 기말잔액 |
| capexItems | list[CapexItem] | 시설투자 항목 목록 |

### RawMaterial

| 필드 | 타입 | 설명 |
|------|------|------|
| segment | str \| None | 사업부문 |
| item | str \| None | 품목명 |
| usage | str \| None | 용도 |
| amount | float \| None | 매입액 |
| ratio | float \| None | 비율 (%) |
| supplier | str \| None | 매입처/비고 |

### Equipment

| 필드 | 타입 | 설명 |
|------|------|------|
| land | float \| None | 토지 |
| buildings | float \| None | 건물/구축물 |
| machinery | float \| None | 기계장치 |
| construction | float \| None | 건설중인자산 |
| total | float \| None | 합계 |
| depreciation | float \| None | 감가상각비 |
| capex | float \| None | 자본적지출 |

### CapexItem

| 필드 | 타입 | 설명 |
|------|------|------|
| segment | str | 구분/사업부문 |
| amount | float | 투자금액 |

## finance.costByNature

```python
from dartlab.finance.costByNature import costByNature

result = costByNature("005930")
result = costByNature("005930", period="y")
```

### costByNature(stockCode, period="y") -> CostByNatureResult | None

연결재무제표 주석에서 비용의 성격별 분류 시계열 추출.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| stockCode | str | - | 종목코드 (6자리) |
| period | str | "y" | "y" (연간) \| "q" (분기) \| "h" (반기) |

### CostByNatureResult

| 필드 | 타입 | 설명 |
|------|------|------|
| corpName | str \| None | 기업명 |
| nYears | int | 기간 수 |
| timeSeries | DataFrame \| None | 비용 시계열 (account, 연도별 금액) |
| crossCheck | dict | 교차검증 결과 {연도: {matches, mismatches}} |
| ratios | DataFrame \| None | 비용 구성비 (year, account, amount, ratio) |
