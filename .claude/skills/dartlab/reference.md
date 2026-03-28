# dartlab API Reference (Skills용)

이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다.


---

## Python API (48개)

`import dartlab` 후 사용 가능한 공개 API.

| 이름 | 종류 | 설명 |
|------|------|------|
| `Company` | function | 종목코드/회사명/ticker → 적절한 Company 인스턴스 생성. |
| `Fred` | class | FRED 경제지표 facade. |
| `OpenDart` | class | OpenDART API 통합 클라이언트. |
| `OpenEdgar` | class | SEC public API facade. |
| `config` | module | dartlab 전역 설정. |
| `core` | module | - |
| `engines` | - | - |
| `llm` | module | LLM 기반 기업분석 엔진. |
| `ask` | function | LLM에게 기업에 대해 질문. |
| `chat` | function | 에이전트 모드: LLM이 도구를 선택하여 심화 분석. |
| `setup` | function | AI provider 설정 안내 + 인터랙티브 설정. |
| `search` | function | 종목 검색 (KR + US 통합). |
| `listing` | function | 전체 상장법인 목록. |
| `collect` | function | 지정 종목 DART 데이터 수집 (OpenAPI). 멀티키 시 병렬. |
| `collectAll` | function | 전체 상장종목 DART 데이터 수집. DART_API_KEY(S) 필요. 멀티키 시 병렬. |
| `downloadAll` | function | HuggingFace에서 전체 시장 데이터를 다운로드. |
| `scan` | function | 시장 전체 횡단분석 통합 엔트리포인트. |
| `analysis` | function | 재무제표 완전 분석 통합 진입점. |
| `network` | function | 한국 상장사 전체 관계 지도. |
| `news` | function | 기업 뉴스 수집. |
| `audit` | function | 감사 Red Flag 분석. |
| `forecast` | function | 매출 앙상블 예측. |
| `valuation` | function | 종합 밸류에이션 (DCF + DDM + 상대가치). |
| `insights` | function | 7영역 등급 분석. |
| `simulation` | function | 경제 시나리오 시뮬레이션. |
| `governance` | function | 한국 상장사 전체 지배구조 스캔. |
| `workforce` | function | 한국 상장사 전체 인력/급여 스캔. |
| `capital` | function | 한국 상장사 전체 주주환원 스캔. |
| `debt` | function | 한국 상장사 전체 부채 구조 스캔. |
| `research` | function | 종합 기업분석 리포트. |
| `digest` | function | 시장 전체 공시 변화 다이제스트. |
| `scanAccount` | function | 전종목 단일 계정 시계열. |
| `scanRatio` | function | 전종목 단일 재무비율 시계열. |
| `plugins` | function | 로드된 플러그인 목록 반환. |
| `reload_plugins` | function | 플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식. |
| `verbose` | module | bool(x) -> bool |
| `dataDir` | module | str(object='') -> str |
| `getKindList` | function | KRX KIND 상장법인 전체 목록. |
| `codeToName` | function | 종목코드 → 회사명. |
| `nameToCode` | function | 회사명 → 종목코드. 정확히 일치하는 첫 번째 결과. |
| `searchName` | function | 회사명 부분 검색. |
| `fuzzySearch` | function | 한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리. |
| `chart` | module | Plotly 기반 재무 차트 도구. |
| `table` | module | 재무 테이블 가공 도구. |
| `text` | module | 텍스트 분석 도구. |
| `Review` | class | 분석 리뷰 — AnalysisReport + core/Report 통합. |
| `SelectResult` | class | select() 반환 객체 — DataFrame 위임 + 체이닝. |
| `ChartResult` | class | chart() 반환 객체 — 시각화 + 렌더링. |

---

## CLI (18개 명령)

`dartlab <command>` 형태로 사용.

| 명령 | 설명 |
|------|------|
| `show` | topic 기반 데이터 조회 |
| `search` | 종목코드/회사명 검색 |
| `statement` | 재무제표 출력 (BS/IS/CIS/CF/SCE) |
| `sections` | docs 수평화 sections 출력 |
| `profile` | Company index/facts 출력 |
| `modules` | 사용 가능한 데이터 모듈 목록 |
| `ask` | 자연어 원스톱 AI 분석 |
| `chat` | 대화형 AI 분석 REPL |
| `report` | Markdown 분석 보고서 생성 |
| `excel` | 기업 데이터 Excel 내보내기 |
| `review` | 기업 분석 검토서 (데이터/AI) |
| `collect` | DART/EDGAR 데이터 수집 |
| `ai` | AI 분석 웹 인터페이스 실행 |
| `share` | 터널로 로컬 서버 외부 공유 |
| `status` | LLM 연결 상태 확인 |
| `setup` | LLM provider/API 키 설정 |
| `mcp` | MCP 서버 실행 (stdio) |
| `plugin` | 플러그인 관리 (list/create) |

---

## Data Modules (69개)

`core/registry.py` DataEntry 기반. 모듈 추가 = 한 줄 → 7곳 자동 반영.

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
| `keywordTrend` | 키워드 트렌드 | `dataframe` | 공시 텍스트 키워드 빈도 추이 (topic × period × keyword). 54개 내장 키워드 또는 사용자 지정. |
| `news` | 뉴스 | `dataframe` | 최근 뉴스 수집 (KR: Google News 한국어, US: Google News 영어). 날짜/제목/출처/URL. |

---

## Company (통합 facade)

입력을 자동 판별하여 DART 또는 EDGAR 시장 전용 Company를 생성한다.
현재 DART Company의 공개 진입점은 **index -> show(topic) -> trace(topic)** 이다.

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

### 핵심 property

| property | 반환 | 설명 |
|----------|------|------|
| `BS` | DataFrame | 재무상태표 |
| `IS` | DataFrame | 손익계산서 |
| `CIS` | DataFrame | 포괄손익계산서 |
| `CF` | DataFrame | 현금흐름표 |
| `sections` | DataFrame | merged topic x period company table |
| `ratios` | RatioResult | 재무비율 |
| `index` | DataFrame | 회사 구조 인덱스 |
| `insights` | AnalysisResult | 7영역 인사이트 등급 |

### 핵심 메서드

| 메서드 | 설명 |
|--------|------|
| `show(topic)` | topic payload 조회 |
| `trace(topic)` | source provenance 조회 |
| `diff()` | 기간간 변화 감지 |
| `filings()` | 공시 문서 목록 |

---

## 주요 데이터 타입

### RatioResult

비율 계산 결과 (최신 단일 시점).

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `revenueTTM` | `float | None` | None |
| `operatingIncomeTTM` | `float | None` | None |
| `netIncomeTTM` | `float | None` | None |
| `operatingCashflowTTM` | `float | None` | None |
| `investingCashflowTTM` | `float | None` | None |
| `totalAssets` | `float | None` | None |
| `totalEquity` | `float | None` | None |
| `ownersEquity` | `float | None` | None |
| `totalLiabilities` | `float | None` | None |
| `currentAssets` | `float | None` | None |
| `currentLiabilities` | `float | None` | None |
| `cash` | `float | None` | None |
| `shortTermBorrowings` | `float | None` | None |
| `longTermBorrowings` | `float | None` | None |
| `bonds` | `float | None` | None |
| `grossProfit` | `float | None` | None |
| `costOfSales` | `float | None` | None |
| `sga` | `float | None` | None |
| `inventories` | `float | None` | None |
| `receivables` | `float | None` | None |
| `payables` | `float | None` | None |
| `tangibleAssets` | `float | None` | None |
| `intangibleAssets` | `float | None` | None |
| `retainedEarnings` | `float | None` | None |
| `profitBeforeTax` | `float | None` | None |
| `incomeTaxExpense` | `float | None` | None |
| `financeIncome` | `float | None` | None |
| `financeCosts` | `float | None` | None |
| `capex` | `float | None` | None |
| `dividendsPaid` | `float | None` | None |
| `depreciationExpense` | `float | None` | None |
| `noncurrentAssets` | `float | None` | None |
| `noncurrentLiabilities` | `float | None` | None |
| `roe` | `float | None` | None |
| `roa` | `float | None` | None |
| `roce` | `float | None` | None |
| `operatingMargin` | `float | None` | None |
| `netMargin` | `float | None` | None |
| `preTaxMargin` | `float | None` | None |
| `grossMargin` | `float | None` | None |
| `ebitdaMargin` | `float | None` | None |
| `costOfSalesRatio` | `float | None` | None |
| `sgaRatio` | `float | None` | None |
| `effectiveTaxRate` | `float | None` | None |
| `incomeQualityRatio` | `float | None` | None |
| `debtRatio` | `float | None` | None |
| `currentRatio` | `float | None` | None |
| `quickRatio` | `float | None` | None |
| `cashRatio` | `float | None` | None |
| `equityRatio` | `float | None` | None |
| `interestCoverage` | `float | None` | None |
| `netDebt` | `float | None` | None |
| `netDebtRatio` | `float | None` | None |
| `noncurrentRatio` | `float | None` | None |
| `workingCapital` | `float | None` | None |
| `revenueGrowth` | `float | None` | None |
| `operatingProfitGrowth` | `float | None` | None |
| `netProfitGrowth` | `float | None` | None |
| `assetGrowth` | `float | None` | None |
| `equityGrowthRate` | `float | None` | None |
| `revenueGrowth3Y` | `float | None` | None |
| `totalAssetTurnover` | `float | None` | None |
| `fixedAssetTurnover` | `float | None` | None |
| `inventoryTurnover` | `float | None` | None |
| `receivablesTurnover` | `float | None` | None |
| `payablesTurnover` | `float | None` | None |
| `operatingCycle` | `float | None` | None |
| `fcf` | `float | None` | None |
| `operatingCfMargin` | `float | None` | None |
| `operatingCfToNetIncome` | `float | None` | None |
| `operatingCfToCurrentLiab` | `float | None` | None |
| `capexRatio` | `float | None` | None |
| `dividendPayoutRatio` | `float | None` | None |
| `fcfToOcfRatio` | `float | None` | None |
| `roic` | `float | None` | None |
| `dupontMargin` | `float | None` | None |
| `dupontTurnover` | `float | None` | None |
| `dupontLeverage` | `float | None` | None |
| `debtToEbitda` | `float | None` | None |
| `ccc` | `float | None` | None |
| `dso` | `float | None` | None |
| `dio` | `float | None` | None |
| `dpo` | `float | None` | None |
| `piotroskiFScore` | `int | None` | None |
| `piotroskiMaxScore` | `int` | 9 |
| `altmanZScore` | `float | None` | None |
| `beneishMScore` | `float | None` | None |
| `sloanAccrualRatio` | `float | None` | None |
| `ohlsonOScore` | `float | None` | None |
| `ohlsonProbability` | `float | None` | None |
| `altmanZppScore` | `float | None` | None |
| `springateSScore` | `float | None` | None |
| `zmijewskiXScore` | `float | None` | None |
| `eps` | `float | None` | None |
| `bps` | `float | None` | None |
| `dps` | `float | None` | None |
| `per` | `float | None` | None |
| `pbr` | `float | None` | None |
| `psr` | `float | None` | None |
| `evEbitda` | `float | None` | None |
| `marketCap` | `float | None` | None |
| `sharesOutstanding` | `int | None` | None |
| `ebitdaEstimated` | `bool` | True |
| `currency` | `str` | KRW |
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
| `predictability` | `Optional` | None |
| `uncertainty` | `Optional` | None |
| `coreEarnings` | `Optional` | None |
| `anomalies` | `list` | [] |
| `distress` | `Optional` | None |
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
