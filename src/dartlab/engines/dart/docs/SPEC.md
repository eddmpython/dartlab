# dart/docs 엔진 스펙

## 역할

DART 사업보고서 HTML → **섹션별 파싱** → 구조화된 DataFrame/Result 반환.
재무제표, 배당, 직원, 임원, 감사, 부문정보, K-IFRS 주석 등 공시 문서의 모든 정보를 추출.

시장 진입점은 `dartlab.engines.dart.Company`와 `dartlab.engines.dart.Compare`다.
루트 `dartlab.Company` / `dartlab.Compare`는 이 DART 진입점을 통합 facade로 감싼다.

**핵심 가치**: 1999년부터의 장기 히스토리 + 서술형 정보 + 구조화 불가능한 데이터.

## 데이터 소스

- **원본**: `data/dart/docs/{stockCode}.parquet`
- **GitHub Release**: `data-docs` (단일 태그, 현재 283개 종목 기준 운영)
- **기간**: 1999년~ (전자공시 시작 이후)
- **단위**: 대부분 백만원 (KRW)
- **parquet 스키마**: year, rcept_date, rcept_no, report_type, section_title, section_content 등 10개 컬럼
- **갱신 주기**: 사업보고서 제출 시

## 모듈 구조 (40개)

### finance/ (36개 모듈)

#### 재무제표 (2개) — Company 내부 디스패치 전용

| 모듈 | 함수 | Result | 설명 |
|------|------|--------|------|
| `statements` | `statements(stockCode, ifrsOnly, period, scope)` | `StatementsResult` | BS/IS/CF DataFrame. **주의: IS는 실제로 CIS(포괄손익계산서)를 반환** — 매출액/영업이익 없음 |
| `summary` | `fsSummary(stockCode, ifrsOnly, period)` | `AnalysisResult` | 요약재무정보 (BS+IS 합산), YearAccounts 원본 보존 |

#### 정량 재무 파싱 (8개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `dividend` | `dividend(stockCode)` | `DividendResult` | `timeSeries` | DPS, 배당총액, 배당성향, 배당수익률 시계열 |
| `employee` | `employee(stockCode)` | `EmployeeResult` | `timeSeries` | 직원수, 근속연수, 평균연봉 시계열 |
| `majorHolder` | `majorHolder(stockCode)` | `MajorHolderResult` | `timeSeries` | 최대주주 지분율 시계열, holders 목록 |
| `majorHolder` | `holderOverview(stockCode)` | `HolderOverview` | (custom) | 5%+ 주주, 소액주주, 의결권 현황 |
| `executive` | `executive(stockCode)` | `ExecutiveResult` | `executiveDf` | 등기임원 구성 시계열 (사내/사외/기타) |
| `executivePay` | `executivePay(stockCode)` | `ExecutivePayResult` | `payByTypeDf` | 유형별 보수 시계열 + 고액보수 목록 |
| `audit` | `audit(stockCode)` | `AuditResult` | `opinionDf` | 감사의견/감사인/핵심감사사항 + feeDf |
| `subsidiary` | `subsidiary(stockCode)` | `SubsidiaryResult` | `timeSeries` | 종속회사 지분율/장부가 시계열 |

#### 자본/주식 (3개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `shareCapital` | `shareCapital(stockCode)` | `ShareCapitalResult` | `timeSeries` | 발행주식수, 자기주식, 유통주식수 시계열 |
| `capitalChange` | `capitalChange(stockCode)` | `CapitalChangeResult` | `capitalDf` | 보통주/우선주 변동 + shareTotalDf + treasuryDf |
| `fundraising` | `fundraising(stockCode)` | `FundraisingResult` | `issuanceDf` | 증자/감자 이력 |

#### 거버넌스/리스크 (7개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `boardOfDirectors` | `boardOfDirectors(stockCode)` | `BoardResult` | `boardDf` | 이사회 구성/활동 + committeeDf |
| `contingentLiability` | `contingentLiability(stockCode)` | `ContingentLiabilityResult` | `guaranteeDf` | 채무보증 + lawsuitDf |
| `internalControl` | `internalControl(stockCode)` | `InternalControlResult` | `controlDf` | 내부회계관리 감사의견 시계열 |
| `auditSystem` | `auditSystem(stockCode)` | `AuditSystemResult` | `committeeDf` | 감사위원회 구성 + activityDf |
| `sanction` | `sanction(stockCode)` | `SanctionResult` | `sanctionDf` | 행정제재/과징금 이력 |
| `relatedPartyTx` | `relatedPartyTx(stockCode)` | `RelatedPartyTxResult` | `revenueTxDf` | 관계자 매출/매입/보증 거래 |
| `riskDerivative` | `riskDerivative(stockCode)` | `RiskDerivativeResult` | `fxDf` | 환/금리 리스크 + 파생상품 |

#### 사업/제품/투자 (7개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `productService` | `productService(stockCode)` | `ProductServiceResult` | `productDf` | 주요 제품/서비스별 매출·비중 |
| `salesOrder` | `salesOrder(stockCode)` | `SalesOrderResult` | `salesDf` | 매출실적 + orderDf (수주잔고) |
| `segment` | `segments(stockCode, period)` | `SegmentsResult` | `revenue` | 부문별 매출 시계열 |
| `affiliateGroup` | `affiliateGroup(stockCode)` | `AffiliateGroupResult` | `affiliateDf` | 기업집단 계열회사 현황 |
| `affiliate` | `affiliates(stockCode, period)` | `AffiliatesResult` | `movementDf` | 관계기업 투자 변동 시계열 |
| `investmentInOther` | `investmentInOther(stockCode)` | `InvestmentInOtherResult` | `investmentDf` | 타법인 출자 현황 |
| `bond` | `bond(stockCode)` | `BondResult` | `timeSeries` | 사채/CP 발행·상환 시계열 |

#### K-IFRS 주석 (4개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `tangibleAsset` | `tangibleAsset(stockCode)` | `TangibleAssetResult` | `movementDf` | 유형자산 변동표 |
| `costByNature` | `costByNature(stockCode, period)` | `CostByNatureResult` | `timeSeries` | 비용 성격별 분류 + ratios |
| `notesDetail` | `notesDetail(stockCode, keyword, period)` | `NotesDetailResult` | `tableDf` | 범용 주석 추출 (keyword 기반) |
| `companyOverviewDetail` | `companyOverviewDetail(stockCode)` | `CompanyOverviewDetailResult` | (dict) | 설립일/상장일/대표이사/주소 등 |

#### 기타 (5개)

| 모듈 | 함수 | Result | primary DataFrame | 설명 |
|------|------|--------|-------------------|------|
| `companyHistory` | `companyHistory(stockCode)` | `CompanyHistoryResult` | `eventsDf` | 회사 주요 연혁 |
| `shareholderMeeting` | `shareholderMeeting(stockCode)` | `ShareholderMeetingResult` | `agendaDf` | 주주총회 안건/의결 |
| `articlesOfIncorporation` | `articlesOfIncorporation(stockCode)` | `ArticlesResult` | `changesDf` | 정관 변경이력 + purposesDf |
| `otherFinance` | `otherFinance(stockCode)` | `OtherFinanceResult` | `badDebtDf` | 대손충당금 + inventoryDf |
| `rnd` | `rnd(stockCode)` | `RndResult` | `rndDf` | R&D 비용 시계열 |

### disclosure/ (4개 모듈) — 서술형 정보

| 모듈 | 함수 | Result | 주요 필드 | 설명 |
|------|------|--------|-----------|------|
| `business` | `business(stockCode)` | `BusinessResult` | `sections: list[BusinessSection]` | 사업의 내용 (최신 + 다년도) |
| `companyOverview` | `companyOverview(stockCode)` | `OverviewResult` | (스칼라) | 회사 정량 개요 (설립, 주소, 신용등급) |
| `mdna` | `mdna(stockCode)` | `MdnaResult` | `overview: str`, `sections` | MD&A (경영진단/분석의견) |
| `rawMaterial` | `rawMaterial(stockCode)` | `RawMaterialResult` | `materials`, `equipment`, `capexItems` | 원재료 + 설비 + 시설투자 |

### sections runtime — 무손실 수평화 계층

`Company.sections`, `Company.retrievalBlocks`, `Company.contextSlices`는 docs parquet 위에서 동작하는 공통 text runtime이다.

| API | 반환 | 역할 |
|-----|------|------|
| `sections(stockCode)` | `topic x period DataFrame` | core canonical 비교축. markdown/table 무손실 보존 |
| `retrievalBlocks(stockCode)` | long `DataFrame` | 원문 block 단위 증거층. `sourceTopic`, `semanticTopic`, `detailTopic`, `cellKey` 포함 |
| `contextSlices(stockCode)` | long `DataFrame` | LLM 입력용 slice. placeholder/boilerplate 기본 제외, semantic/detail 우선 |

운영 원칙:
- per-stock 결과를 패키지 data로 저장하지 않는다.
- learned rules와 compact artifact만 패키지에 포함한다.
- appendix/detail은 core wide view에서 숨기고 `detailTopic`으로 retrieval layer에서 회수한다.

### notes.py — K-IFRS 주석 통합 접근

`c.notes.{name}` 또는 `c.notes["한글명"]`으로 접근. 12개 항목:

| 영문명 | 한글명 | 디스패치 | extractor |
|--------|--------|----------|-----------|
| `receivables` | 매출채권 | notesDetail | tableDf |
| `inventory` | 재고자산 | notesDetail | tableDf |
| `tangibleAsset` | 유형자산 | tangibleAsset 모듈 | movementDf |
| `intangibleAsset` | 무형자산 | notesDetail | tableDf |
| `investmentProperty` | 투자부동산 | notesDetail | tableDf |
| `affiliates` | 관계기업 | affiliates 모듈 | movementDf |
| `borrowings` | 차입금 | notesDetail | tableDf |
| `provisions` | 충당부채 | notesDetail | tableDf |
| `eps` | 주당이익 | notesDetail | tableDf |
| `lease` | 리스 | notesDetail | tableDf |
| `segments` | 부문정보 | segments 모듈 | revenue |
| `costByNature` | 비용의성격별분류 | costByNature 모듈 | timeSeries |

## Result 클래스 공통 패턴

```python
@dataclass
class XxxResult:
    corpName: str | None = None
    nYears: int = 0
    period: str = "y"
    primaryDf: pl.DataFrame | None = None   # primary DataFrame
    secondaryDf: pl.DataFrame | None = None # 보조 DataFrame
```

- 모든 Result는 `@dataclass`
- `nYears`로 시계열 기간 수
- primary DataFrame은 registry extractor가 추출하는 것
- 하나의 Result에 여러 DataFrame 가능 (audit: opinionDf + feeDf 등)

## 함수 시그니처 통일

```python
def moduleFunc(stockCode: str, ...) -> XxxResult | None:
```

- 필수: `stockCode`
- 선택: `period="y"`, `ifrsOnly=True`, `keyword` (notesDetail)
- 반환: Result 또는 None (데이터 없음)

## docs 고유 강점 (finance/report에 없는 것)

### 1. 서술형 정보
- `business` — 사업의 내용 (텍스트)
- `mdna` — MD&A (경영진단 서술)
- `rawMaterial` — 원재료/설비/투자 (혼합)

### 2. 1999년부터의 장기 히스토리
- finance는 2015~, report도 2015~
- docs는 1999~ (전자공시 시작)
- 장기 추세 분석, 사업보고서 연혁 추적

### 3. K-IFRS 주석 상세
- notesDetail: 23개+ 주석 섹션 동적 추출
- tangibleAsset: 유형자산 변동표 (취득/처분/감가상각)
- costByNature: 비용 성격별 분류

### 4. 복합 구조 데이터
- holderOverview: 5%+ 주주 + 소액주주 + 의결권 (단일 API로 불가)
- relatedPartyTx: 매출/매입/보증 3종 거래 (단일 API로 불가)
- contingentLiability: 채무보증 + 소송 (단일 API로 불가)
- capitalChange: 자본금 + 주식총수 + 자기주식 (3개 테이블)

### 5. Company property 없는 모듈 (c.get()으로 접근)
- `fsSummary` — 요약재무정보 (파라미터 필요: ifrsOnly, period)
- `statements` — BS/IS/CF (내부 디스패치, c.BS/IS/CF로 접근)
- `tangibleAsset` — notes에서 접근 (c.notes.tangibleAsset)
- `costByNature` — notes에서 접근 (c.notes.costByNature)
- `companyOverview` — c.overview로 접근

## docs vs finance vs report 비교

| 기준 | docs | finance | report |
|------|------|---------|--------|
| 소스 | HTML 파싱 | XBRL 정형 | DART API 정형 |
| 기간 | 1999~ | 2015~ | 2015~ |
| 단위 | 백만원 | 원 | 원 |
| 정확도 | 파서 품질 의존 | 높음 (XBRL) | 높음 (API) |
| 정규화 | 계정명 직접 매칭 | snakeId | 컬럼명 고정 |
| 장점 | 장기 + 서술형 + 주석 | 정규화 + 비교 | 정형 + 22종 |
| 회사간 비교 | 어려움 | 쉬움 (snakeId) | 가능 (API 구조) |

## 파일 구조

```
engines/dart/docs/
├── __init__.py
├── notes.py                    # K-IFRS 주석 통합 (Notes 클래스)
├── finance/                    # 정량 재무 모듈 (36개)
│   ├── __init__.py
│   ├── statements/             # BS/IS/CF
│   ├── summary/                # 요약재무정보
│   ├── segment/                # 부문정보
│   ├── dividend/               # 배당
│   ├── employee/               # 직원
│   ├── majorHolder/            # 최대주주 + holderOverview
│   ├── executive/              # 임원
│   ├── executivePay/           # 임원보수
│   ├── audit/                  # 감사의견
│   ├── boardOfDirectors/       # 이사회
│   ├── ... (24개 더)
│   └── notesDetail/            # 범용 주석 추출
├── disclosure/                 # 서술형 공시 (4개)
│   ├── business/               # 사업의 내용
│   ├── companyOverview/        # 회사 정량 개요
│   ├── mdna/                   # MD&A
│   └── rawMaterial/            # 원재료/설비
└── SPEC.md                     # 이 파일
```
