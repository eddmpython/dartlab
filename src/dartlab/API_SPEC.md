# dartlab API 스펙

이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다. 직접 수정하지 마세요.


---

## Company (통합 facade)

입력을 자동 판별하여 DART 또는 EDGAR 시장 전용 Company를 생성한다.
현재 DART Company의 공개 진입점은 **index → show(topic) → trace(topic)** 이다.
`profile`은 향후 terminal/notebook 문서형 보고서 뷰로 확장될 예정이다.

```python
import dartlab

kr = dartlab.Company("005930")
kr = dartlab.Company("삼성전자")
us = dartlab.Company("AAPL")

kr.market                    # "KR"
us.market                    # "US"
```

### 판별 규칙

| 입력 | 결과 | 예시 |
|------|------|------|
| 6자리 숫자 | DART Company | `Company("005930")` |
| 한글 포함 | DART Company | `Company("삼성전자")` |
| 영문 1~5자리 | EDGAR Company | `Company("AAPL")` |

## DART Company

### 현재 공개 진입점

| surface | 설명 |
|---------|------|
| `index` | 회사 데이터 구조 인덱스 DataFrame |
| `show(topic)` | topic의 실제 데이터 payload 조회 |
| `trace(topic, period)` | docs / finance / report source provenance 조회 |
| `docs` | pure docs source namespace |
| `finance` | authoritative finance source namespace |
| `report` | authoritative structured disclosure source namespace |
| `profile` | 향후 보고서형 렌더용 예약 뷰 |

### 정적 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `dartlab.engines.dart.Company.listing()` | DataFrame | KRX 전체 상장법인 목록 |
| `dartlab.engines.dart.Company.search(keyword)` | DataFrame | 회사명 부분 검색 |
| `dartlab.engines.dart.Company.status()` | DataFrame | 로컬 보유 전체 종목 인덱스 |
| `dartlab.engines.dart.Company.resolve(codeOrName)` | str \| None | 종목코드/회사명 → 종목코드 |

### 핵심 property

| property | 반환 | 설명 |
|----------|------|------|
| `BS` | DataFrame | 재무상태표 |
| `IS` | DataFrame | 손익계산서 |
| `CIS` | DataFrame | 포괄손익계산서 |
| `CF` | DataFrame | 현금흐름표 |
| `SCE` | tuple \| DataFrame | 자본변동표 |
| `sections` | DataFrame | merged topic x period company table |
| `timeseries` | (series, periods) | 분기별 standalone 시계열 |
| `annual` | (series, years) | 연도별 시계열 |
| `ratios` | RatioResult | 재무비율 |
| `index` | DataFrame | 회사 구조 인덱스 |
| `docs` | Accessor | pure docs source |
| `finance` | Accessor | authoritative finance source |
| `report` | Accessor | authoritative report source |
| `profile` | _BoardView | 향후 보고서형 뷰 예약 |
| `sector` | SectorInfo | 섹터 분류 |
| `insights` | AnalysisResult | 7영역 인사이트 등급 |
| `rank` | RankInfo | 시장 순위 |
| `notes` | Notes | K-IFRS 주석 접근 |
| `market` | str | `"KR"` |

### 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `get(name)` | Result | 모듈 전체 Result 객체 |
| `all()` | dict | 전체 데이터 dict |
| `show(topic, period=None, raw=False)` | Any | topic payload 조회 |
| `trace(topic, period=None)` | dict \| None | 선택 source provenance 조회 |
| `fsSummary(period)` | AnalysisResult | 요약재무정보 |
| `getTimeseries(period, fsDivPref)` | (series, periods) | 커스텀 시계열 |
| `getRatios(fsDivPref)` | RatioResult | 커스텀 비율 |

`index`는 회사 전체 구조를 먼저 보여주고, `show(topic)`가 실제 데이터를 연다.
`trace(topic)`는 같은 topic에서 docs / finance / report 중 어떤 source가 채택됐는지 설명한다.
docs가 없는 회사는 `docsStatus` 안내 row와 `현재 사업보고서 부재` notice가 표시된다.

report/disclosure property는 registry에서 자동 디스패치된다 (`_MODULE_REGISTRY`).
등록된 모든 property는 아래 "데이터 레지스트리" 섹션 참조.

## EDGAR Company

```python
import dartlab

us = dartlab.Company("AAPL")
us.ticker                    # "AAPL"
us.cik                       # "0000320193"
```

### property

| property | 반환 | 설명 |
|----------|------|------|
| `timeseries` | (series, periods) | 분기별 standalone 시계열 |
| `annual` | (series, years) | 연도별 시계열 |
| `ratios` | RatioResult | 재무비율 |
| `insights` | AnalysisResult | 7영역 인사이트 등급 |
| `market` | str | `"US"` |

---

## 데이터 레지스트리

`core/registry.py`에 등록된 전체 데이터 소스 목록.

모듈 추가 = registry에 DataEntry 한 줄 추가 → Company, Excel, LLM, Server, Skills 전부 자동 반영.

### 시계열 재무제표 (finance)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `annual.IS` | 손익계산서(연도별) | `timeseries` | 연도별 손익계산서 시계열. 매출액, 영업이익, 순이익 등 전체 계정. |
| `annual.BS` | 재무상태표(연도별) | `timeseries` | 연도별 재무상태표 시계열. 자산, 부채, 자본 전체 계정. |
| `annual.CF` | 현금흐름표(연도별) | `timeseries` | 연도별 현금흐름표 시계열. 영업/투자/재무활동 현금흐름. |
| `timeseries.IS` | 손익계산서(분기별) | `timeseries` | 분기별 손익계산서 standalone 시계열. |
| `timeseries.BS` | 재무상태표(분기별) | `timeseries` | 분기별 재무상태표 시점잔액 시계열. |
| `timeseries.CF` | 현금흐름표(분기별) | `timeseries` | 분기별 현금흐름표 standalone 시계열. |

### 공시 파싱 모듈 (report)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `BS` | 재무상태표 | `dataframe` | K-IFRS 연결 재무상태표. finance XBRL 정규화(snakeId) 기반, 회사간 비교 가능. finance 없으면 docs fallback. |
| `IS` | 손익계산서 | `dataframe` | K-IFRS 연결 손익계산서. finance XBRL 정규화 기반. 매출액, 영업이익, 순이익 등 전체 계정 포함. |
| `CF` | 현금흐름표 | `dataframe` | K-IFRS 연결 현금흐름표. finance XBRL 정규화 기반. 영업/투자/재무활동 현금흐름. |
| `fsSummary` | 요약재무정보 | `dataframe` | DART 공시 요약재무정보. 다년간 주요 재무지표 비교. |
| `segments` | 부문정보 | `dataframe` | 사업부문별 매출·이익 데이터. 부문간 수익성 비교 가능. |
| `tangibleAsset` | 유형자산 | `dataframe` | 유형자산 변동표. 취득/처분/감가상각 내역. |
| `costByNature` | 비용성격별분류 | `dataframe` | 비용을 성격별로 분류한 시계열. 원재료비, 인건비, 감가상각비 등. |
| `dividend` | 배당 | `dataframe` | 배당 시계열. 연도별 DPS, 배당총액, 배당성향, 배당수익률. |
| `majorHolder` | 최대주주 | `dataframe` | 최대주주 지분율 시계열. 지분 변동은 경영권 안정성의 핵심 지표. |
| `employee` | 직원현황 | `dataframe` | 직원 수, 평균 근속연수, 평균 연봉 시계열. |
| `subsidiary` | 자회사투자 | `dataframe` | 종속회사 투자 시계열. 지분율, 장부가액 변동. |
| `bond` | 채무증권 | `dataframe` | 사채, CP 등 채무증권 발행·상환 시계열. |
| `shareCapital` | 주식현황 | `dataframe` | 발행주식수, 자기주식, 유통주식수 시계열. |
| `executive` | 임원현황 | `dataframe` | 등기임원 구성 시계열. 사내이사/사외이사/비상무이사 구분. |
| `executivePay` | 임원보수 | `dataframe` | 임원 유형별 보수 시계열. 등기이사/사외이사/감사 구분. |
| `audit` | 감사의견 | `dataframe` | 외부감사인의 감사의견과 감사보수 시계열. 적정 외 의견은 중대 위험 신호. |
| `boardOfDirectors` | 이사회 | `dataframe` | 이사회 구성 및 활동 시계열. 개최횟수, 출석률 포함. |
| `capitalChange` | 자본변동 | `dataframe` | 자본금 변동 시계열. 보통주/우선주 주식수·액면 변동. |
| `contingentLiability` | 우발부채 | `dataframe` | 채무보증, 소송 현황. 잠재적 재무 리스크 지표. |
| `internalControl` | 내부통제 | `dataframe` | 내부회계관리제도 감사의견 시계열. |
| `relatedPartyTx` | 관계자거래 | `dataframe` | 대주주 등과의 매출·매입 거래 시계열. 이전가격 리스크 확인. |
| `rnd` | R&D | `dataframe` | 연구개발비용 시계열. 기술 투자 강도 판단. |
| `sanction` | 제재현황 | `dataframe` | 행정제재, 과징금, 영업정지 등 규제 조치 이력. |
| `affiliateGroup` | 계열사 | `dataframe` | 기업집단 소속 계열회사 현황. 상장/비상장 구분. |
| `fundraising` | 증자감자 | `dataframe` | 유상증자, 무상증자, 감자 이력. |
| `productService` | 주요제품 | `dataframe` | 주요 제품/서비스별 매출액과 비중. |
| `salesOrder` | 매출수주 | `dataframe` | 매출실적 및 수주 현황. |
| `riskDerivative` | 위험관리 | `dataframe` | 환율·이자율·상품가격 리스크 관리. 파생상품 보유 현황. |
| `articlesOfIncorporation` | 정관 | `dataframe` | 정관 변경 이력. 사업목적 추가·변경으로 신사업 진출 파악. |
| `otherFinance` | 기타재무 | `dataframe` | 대손충당금, 재고자산 관련 기타 재무 데이터. |
| `companyHistory` | 연혁 | `dataframe` | 회사 주요 연혁 이벤트 목록. |
| `shareholderMeeting` | 주주총회 | `dataframe` | 주주총회 안건 및 의결 결과. |
| `auditSystem` | 감사제도 | `dataframe` | 감사위원회 구성 및 활동 현황. |
| `affiliate` | 관계기업투자 | `dataframe` | 관계기업/공동기업 투자 변동 시계열. 지분법손익, 기초/기말 장부가 포함. |
| `investmentInOther` | 타법인출자 | `dataframe` | 타법인 출자 현황. 투자목적, 지분율, 장부가 등. |
| `companyOverviewDetail` | 회사개요 | `dict` | 설립일, 상장일, 대표이사, 주소, 주요사업 등 기본 정보. |
| `holderOverview` | 주주현황 | `custom` | 5% 이상 주주, 소액주주 현황, 의결권 현황. majorHolder보다 상세한 주주 구성. |

### 서술형 공시 (disclosure)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `business` | 사업의내용 | `text` | 사업보고서 '사업의 내용' 서술. 사업 구조와 현황 파악. |
| `companyOverview` | 회사개요정량 | `dict` | 공시 기반 회사 정량 개요 데이터. |
| `mdna` | MD&A | `text` | 이사의 경영진단 및 분석의견. 경영진 시각의 실적 평가와 전망. |
| `rawMaterial` | 원재료설비 | `dict` | 원재료 매입, 유형자산 현황, 시설투자 데이터. |
| `sections` | 사업보고서섹션 | `dataframe` | 사업보고서 전체 섹션 텍스트를 topic(행) × period(열) DataFrame으로 구조화. leaf title 기준 수평 비교 가능. 연간+분기+반기 전 기간 포함. |

### K-IFRS 주석 (notes)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `notes.receivables` | 매출채권 | `dataframe` | K-IFRS 매출채권 주석. 채권 잔액 및 대손충당금 내역. |
| `notes.inventory` | 재고자산 | `dataframe` | K-IFRS 재고자산 주석. 원재료/재공품/제품 내역별 금액. |
| `notes.tangibleAsset` | 유형자산(주석) | `dataframe` | K-IFRS 유형자산 변동 주석. 토지, 건물, 기계 등 항목별 변동. |
| `notes.intangibleAsset` | 무형자산 | `dataframe` | K-IFRS 무형자산 주석. 영업권, 개발비 등 항목별 변동. |
| `notes.investmentProperty` | 투자부동산 | `dataframe` | K-IFRS 투자부동산 주석. 공정가치 및 변동 내역. |
| `notes.affiliates` | 관계기업(주석) | `dataframe` | K-IFRS 관계기업 투자 주석. 지분법 적용 내역. |
| `notes.borrowings` | 차입금 | `dataframe` | K-IFRS 차입금 주석. 단기/장기 차입 잔액 및 이자율. |
| `notes.provisions` | 충당부채 | `dataframe` | K-IFRS 충당부채 주석. 판매보증, 소송, 복구 등. |
| `notes.eps` | 주당이익 | `dataframe` | K-IFRS 주당이익 주석. 기본/희석 EPS 계산 내역. |
| `notes.lease` | 리스 | `dataframe` | K-IFRS 리스 주석. 사용권자산, 리스부채 내역. |
| `notes.segments` | 부문정보(주석) | `dataframe` | K-IFRS 부문정보 주석. 사업부문별 상세 데이터. |
| `notes.costByNature` | 비용의성격별분류(주석) | `dataframe` | K-IFRS 비용의 성격별 분류 주석. |

### 원본 데이터 (raw)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `rawDocs` | 공시 원본 | `dataframe` | 공시 문서 원본 parquet. 가공 전 전체 테이블과 텍스트. |
| `rawFinance` | XBRL 원본 | `dataframe` | XBRL 재무제표 원본 parquet. 매핑/정규화 전 원본 데이터. |
| `rawReport` | 보고서 원본 | `dataframe` | 정기보고서 API 원본 parquet. 파싱 전 원본 데이터. |

### 분석 엔진 (analysis)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `ratios` | 재무비율 | `ratios` | financeEngine이 자동계산한 수익성·안정성·밸류에이션 비율. |
| `insight` | 인사이트 | `custom` | 7영역 A~F 등급 분석 (실적, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회). |
| `sector` | 섹터분류 | `custom` | WICS 11대 섹터 분류. 대분류/중분류 + 섹터별 파라미터. |
| `rank` | 시장순위 | `custom` | 전체 시장 및 섹터 내 매출/자산/성장률 순위. |

---

## 주요 데이터 타입

### RatioResult

비율 계산 결과 (최신 단일 시점).

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `revenueTTM` | `Optional` | None |
| `operatingIncomeTTM` | `Optional` | None |
| `netIncomeTTM` | `Optional` | None |
| `operatingCashflowTTM` | `Optional` | None |
| `investingCashflowTTM` | `Optional` | None |
| `totalAssets` | `Optional` | None |
| `totalEquity` | `Optional` | None |
| `ownersEquity` | `Optional` | None |
| `totalLiabilities` | `Optional` | None |
| `currentAssets` | `Optional` | None |
| `currentLiabilities` | `Optional` | None |
| `cash` | `Optional` | None |
| `shortTermBorrowings` | `Optional` | None |
| `longTermBorrowings` | `Optional` | None |
| `bonds` | `Optional` | None |
| `grossProfit` | `Optional` | None |
| `costOfSales` | `Optional` | None |
| `sga` | `Optional` | None |
| `inventories` | `Optional` | None |
| `receivables` | `Optional` | None |
| `payables` | `Optional` | None |
| `tangibleAssets` | `Optional` | None |
| `intangibleAssets` | `Optional` | None |
| `retainedEarnings` | `Optional` | None |
| `financeIncome` | `Optional` | None |
| `financeCosts` | `Optional` | None |
| `capex` | `Optional` | None |
| `dividendsPaid` | `Optional` | None |
| `depreciationExpense` | `Optional` | None |
| `noncurrentAssets` | `Optional` | None |
| `noncurrentLiabilities` | `Optional` | None |
| `roe` | `Optional` | None |
| `roa` | `Optional` | None |
| `operatingMargin` | `Optional` | None |
| `netMargin` | `Optional` | None |
| `grossMargin` | `Optional` | None |
| `ebitdaMargin` | `Optional` | None |
| `costOfSalesRatio` | `Optional` | None |
| `sgaRatio` | `Optional` | None |
| `debtRatio` | `Optional` | None |
| `currentRatio` | `Optional` | None |
| `quickRatio` | `Optional` | None |
| `equityRatio` | `Optional` | None |
| `interestCoverage` | `Optional` | None |
| `netDebt` | `Optional` | None |
| `netDebtRatio` | `Optional` | None |
| `noncurrentRatio` | `Optional` | None |
| `revenueGrowth` | `Optional` | None |
| `operatingProfitGrowth` | `Optional` | None |
| `netProfitGrowth` | `Optional` | None |
| `assetGrowth` | `Optional` | None |
| `equityGrowthRate` | `Optional` | None |
| `revenueGrowth3Y` | `Optional` | None |
| `totalAssetTurnover` | `Optional` | None |
| `inventoryTurnover` | `Optional` | None |
| `receivablesTurnover` | `Optional` | None |
| `payablesTurnover` | `Optional` | None |
| `fcf` | `Optional` | None |
| `operatingCfMargin` | `Optional` | None |
| `operatingCfToNetIncome` | `Optional` | None |
| `capexRatio` | `Optional` | None |
| `dividendPayoutRatio` | `Optional` | None |
| `per` | `Optional` | None |
| `pbr` | `Optional` | None |
| `psr` | `Optional` | None |
| `evEbitda` | `Optional` | None |
| `marketCap` | `Optional` | None |
| `ebitdaEstimated` | `bool` | True |
| `warnings` | `list` | [] |

### InsightResult

단일 영역 분석 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `grade` | `str` |  |
| `summary` | `str` |  |
| `details` | `list` | [] |
| `risks` | `list` | [] |
| `opportunities` | `list` | [] |

### Anomaly

이상치 탐지 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `severity` | `str` |  |
| `category` | `str` |  |
| `text` | `str` |  |
| `value` | `Optional` | None |

### Flag

리스크/기회 플래그.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `level` | `str` |  |
| `category` | `str` |  |
| `text` | `str` |  |

### AnalysisResult

종합 분석 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `corpName` | `str` |  |
| `stockCode` | `str` |  |
| `isFinancial` | `bool` |  |
| `performance` | `InsightResult` |  |
| `profitability` | `InsightResult` |  |
| `health` | `InsightResult` |  |
| `cashflow` | `InsightResult` |  |
| `governance` | `InsightResult` |  |
| `risk` | `InsightResult` |  |
| `opportunity` | `InsightResult` |  |
| `anomalies` | `list` | [] |
| `summary` | `str` |  |
| `profile` | `str` |  |

### SectorInfo

섹터 분류 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `sector` | `Sector` |  |
| `industryGroup` | `IndustryGroup` |  |
| `confidence` | `float` |  |
| `source` | `str` |  |

### SectorParams

섹터별 밸류에이션 파라미터.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `discountRate` | `float` |  |
| `growthRate` | `float` |  |
| `perMultiple` | `float` |  |
| `pbrMultiple` | `float` |  |
| `evEbitdaMultiple` | `float` |  |
| `label` | `str` |  |
| `description` | `str` |  |

### RankInfo

단일 종목의 랭크 정보.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `stockCode` | `str` |  |
| `corpName` | `str` |  |
| `sector` | `str` |  |
| `industryGroup` | `str` |  |
| `revenue` | `Optional` | None |
| `totalAssets` | `Optional` | None |
| `revenueGrowth3Y` | `Optional` | None |
| `revenueRank` | `Optional` | None |
| `revenueTotal` | `int` | 0 |
| `revenueRankInSector` | `Optional` | None |
| `revenueSectorTotal` | `int` | 0 |
| `assetRank` | `Optional` | None |
| `assetTotal` | `int` | 0 |
| `assetRankInSector` | `Optional` | None |
| `assetSectorTotal` | `int` | 0 |
| `growthRank` | `Optional` | None |
| `growthTotal` | `int` | 0 |
| `growthRankInSector` | `Optional` | None |
| `growthSectorTotal` | `int` | 0 |
| `sizeClass` | `str` |  |
