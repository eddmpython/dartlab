# 01. Current State Audit

## 1. 감사 기준

- 저장소 HEAD: `b3e5505b122e7acafa3588b54088598c79bb3a3f`
- HF map buildId: `20260714-195628`, commitSha `2176d8b`
- 감사 시점: 2026-07-15 KST
- 데이터 파일 수와 byte는 Hugging Face repository tree API의 recursive file metadata를 합산했다.
- 라이브 dataset card: [eddmpython/dartlab-data](https://huggingface.co/datasets/eddmpython/dartlab-data)

### 2026-07-15 재감사 스냅샷

최초 감사 수치는 역사적 기준선으로 보존한다. 같은 날 후속 live meta에서 다음 세대가 확인되었다.

| 항목 | 재감사 값 |
|---|---:|
| map buildId | `20260715-084444` |
| map commitSha | `bc10468` |
| ecosystem | 6,015,104 bytes |
| atlas | 27,517 bytes |
| industryStats | 244,656 bytes |
| search index | 306,450 bytes |
| company payload total | 79,532,356 bytes |
| industry | 34 |
| atlas flow | 50 |

source freshness는 finance `2026-07-15T08:37:55Z`, reviews와 taxonomy `2026-07-15T08:36:58Z`였으나 dart는 null이었다. 이 상태에서 단일 map buildId만으로 공시, search, panel, finance exact replay를 주장할 수 없다. `SourceSnapshotSet`과 source별 `unreplayable` 표시가 필요하다.

## 2. HF 전수 계수

전체는 68,199파일, 275,755,437,729 bytes다. dataset card의 276GB와 일치한다.

| 1단계 경로 | 파일 | Parquet | bytes | 약 GB |
|---|---:|---:|---:|---:|
| `dart` | 17,162 | 14,525 | 217,885,810,153 | 217.89 |
| `edgar` | 35,289 | 35,288 | 53,785,383,424 | 53.79 |
| `news` | 9,235 | 9,235 | 3,413,153,052 | 3.41 |
| `gov` | 3,738 | 3,738 | 498,513,111 | 0.50 |
| `landing` | 2,715 | 0 | 107,049,110 | 0.11 |
| `pyodide` | 3 | 0 | 59,549,835 | 0.06 |
| 나머지 | 57 | 44 | 6,029,044 | 0.01 |

상위 데이터군은 다음과 같다.

| 경로 | 파일 | bytes | 제품 해석 |
|---|---:|---:|---|
| `dart/contentIndex` | 2,191 | 154,229,779,394 | 대부분 과거 `_staging` 세대. Universe 정본으로 직접 순회 금지 |
| `dart/docs` | 3,141 | 42,540,801,719 | 은퇴했지만 과거 호환을 위해 보존 |
| `edgar/panel` | 7,413 | 29,910,948,050 | US 회사별 panel 정본 |
| `edgar/docs` | 7,003 | 20,610,167,176 | 과거 호환 surface |
| `dart/panel` | 2,932 | 11,787,290,051 | KR 회사별 panel 정본 |
| `dart/allFilings` | 1,156 | 6,705,608,621 | 공시 전수 및 검색 소스 |
| `news/public` | 9,235 | 3,413,153,052 | public 뉴스 source lane |
| `edgar/allFilingsContent` | 215 | 2,474,711,340 | EDGAR 본문 검색 소스 |
| `dart/scan` | 65 | 712,154,311 | 횡단 prebuild SSOT |
| `dart/finance` | 3,222 | 607,297,754 | KR 재무 |
| `edgar/finance` | 9,997 | 523,767,266 | US finance 계열 |
| `landing/map` | 2,710 | 93,196,172 | 현재 public 지도 배포면 |

### 저장 수명주기 재분류

| 분류 | 파일 | bytes | 판정 |
|---|---:|---:|---|
| 검색 `_staging` 세대 | 2,173 | 153,910,337,279 | 운영 임시 세대. retention은 search ops 소유 |
| 호환 `dart/docs`, `dart/sections`, `edgar/docs` | 11,344 | 63,656,962,973 | 삭제 금지 호환 정본 |
| 두 분류를 제외한 활성 및 기타 | 54,682 | 58,188,137,477 | 실제 제품 hot 및 current 데이터 범위 |
| current contentIndex 비staging | 18 | 319,442,115 | 검색 runtime surface |

결론: "276GB를 우주화"는 물리 용량의 문제가 아니라 수명주기와 query boundary의 문제다. 제품은 staging과 compatibility를 scene source로 취급하지 않는다.

## 3. 동형 cross-market 데이터

`dart/panel/005930.parquet`은 67,993행 16컬럼, 압축 13.44MB, 메모리 추정 193.11MB다. `edgar/panel/AAPL.parquet`은 6,489행 16컬럼이고 같은 컬럼 계약을 갖는다.

공통 핵심 컬럼:

`chapter`, `sectionLeaf`, `sectionPath`, `leafType`, `blockLeaf`, `xbrlClass`, `xbrlMatched`, `contentRaw`, `period`, `corp`, `rceptNo`, `disclosureKey`

이 동형성은 cross-market Universe의 가장 강한 기존 자산이다. 시장간 장면은 새 global document schema가 아니라 이 계약 위에서 만든다.

`dart/finance/005930.parquet`은 13,074행 27컬럼, 압축 299.6KB다. 숫자 관측은 graph node가 아니라 이 표를 column projection으로 읽는 것이 맞다.

## 4. 현재 public map

현재 map은 이미 3단계 LOD를 갖는다.

| 단계 | artifact | 현재 크기 및 수 | 역할 |
|---|---|---:|---|
| L1 | `landing/map/atlas.json` | 27,517 bytes, 산업 34개 | 산업 overview |
| L2 | `landing/map/industries/{id}.json` | 산업별 | 공정, 회사, 내부 edge |
| L3 | `landing/map/companies/{stockCode}.json` | 총 79,517,001 bytes | 회사 1-hop egograph |
| 전체 | `landing/map/ecosystem.json` | 6,015,606 bytes | 회사 2,664, link 20,560 |

그러나 `landing/src/lib/browser/dartlabBrowser.ts::marketMap()`은 ecosystem, atlas, industryStats, meta, movers, timeline을 `Promise.all`로 모두 읽는다. atlas 27KB만 필요한 첫 화면도 6MB ecosystem을 함께 기다린다. 첫 제품 성능 개선은 새 데이터가 아니라 semantic LOD에 맞는 호출 분리다.

브라우저 runtime에는 이미 필요한 기반이 있다.

- `ui/packages/runtime/src/data/fetch/request.ts`: origin, cache, request dedup, resilient fetch의 단일 진입점
- `ui/packages/runtime/src/data/parquet/hfRange.ts`: hyparquet row/column/range read
- `ui/packages/runtime/src/data/search/filingSearch.ts`: postings와 meta 조각만 HTTP range fetch하는 exact BM25
- `ui/packages/runtime/src/data/origins/hf.ts`: public 및 local 공통 HF 경로

현 코드 주석의 실측은 range 요청을 프록시로 보낼 때 약 2.8초, HF 직결은 약 0.38초다. 외부 [hyparquet](https://github.com/hyparam/hyparquet)도 browser HTTP range와 row/column projection을 공식 지원한다.

## 5. 관계 그래프 품질

### 전체 분포

| 항목 | 값 |
|---|---:|
| node | 2,664 |
| edge | 20,560 |
| linked node | 2,656 |
| isolated node | 8 |
| median degree | 6 |
| p90 degree | 23 |
| p99 degree | 81 |
| max degree | 2,585 |
| self-loop | 13 |

source 분포:

| source | edge | 비율 |
|---|---:|---:|
| `panel_text` | 17,400 | 84.6% |
| `network` | 2,952 | 14.4% |
| `panel_table` | 208 | 1.0% |

type 분포:

| type | edge |
|---|---:|
| affiliate | 11,571 |
| supplier | 6,679 |
| investor | 2,306 |
| customer | 4 |

근거 표면:

- `evidence` non-empty 20,496건이지만 unique 문자열은 486개뿐이다.
- `product` 30건, `amount` 123건, `ratio` 131건만 값이 있다.
- 정확한 `rceptNo`, `sourceRef`, `period`, `validFrom`, `observedAt`, `availableAt` 필드는 schema에 없다.

### 구조적 오탐

`extractDocsEdges()`는 3글자 이상 상장사명이 `contentRaw` 부분문자열에 있으면 관계를 생성한다. `OCI`는 일반 영문 텍스트에 자주 나타나므로 4,474개 edge에 관여한다.

- `OCI` degree: 2,585
- 전체 edge 관여: 4,474, 전체의 21.8%
- 그중 `panel_text`: 4,464
- 반복 evidence: `3. 원재료 및 생산설비` 2,521, `IX. 계열회사 등에 관한 사항` 1,905

이는 confidence 0.5 또는 0.7이라는 숫자로 해결되지 않는다. entity mention boundary와 exact evidence가 없는 relation은 fact가 아니라 retrieval candidate다.

### assertion 손실

`buildAllEdges()`는 source 우선순위로 정렬한 뒤 `(fromCode, toCode, edgeType)`으로 중복 제거한다. 서로 다른 보고서와 기간의 같은 관계가 한 행으로 붕괴한다. `IndustryEdge`에는 12개 표현 필드만 있고 assertion identity와 revision이 없다.

따라서 현재 edge는 다음 역할로만 안전하다.

- 탐색 후보와 layout hint
- 회사 1-hop seed
- exact evidence를 찾기 위한 retrieval hint

다음 역할에는 부적합하다.

- source-backed factual claim
- 특정 시점 관계
- 정정 및 revision 비교
- causal propagation의 사실 근거

## 6. 엔진 및 capability 전수

현재 live capability catalog는 226개다. Skill OS는 286개이며 category는 engines 66, operation 36, recipes 156, runtime 19, start 9다. Analysis Graph는 node 67, edge 116, contract 9, processMap 8, route 8이다.

핵심 dispatch 축:

| 엔진 | 축 수 | 실제 축 | Universe 역할 |
|---|---:|---|---|
| analysis | 22 | 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성, 가치평가, 지배구조, 공시변화, 비교분석, 매출전망, 예측신호, 매크로민감도, 밸류에이션밴드 | 회사 재무 lens |
| scan | 27 | governance, workforce, capital, debt, account, ratio, note, network, cashflow, audit, insider, quality, liquidity, growth, profitability, efficiency, valuation, dividendTrend, macroBeta, fields, screen, disclosureRisk, orders, ipo, salesByProduct, narrativeMetric, earningsFlash | 횡단 filter와 rank lens |
| gather | 18 | price, flow, macro, news, sector, insider, ownership, peers, krx, krxIndex, narrative, research, naverTheme, naverIndustry, naverEtf, naverEtn, dartDoc, calendar | raw source. naver 계열 localOnly, dartDoc/calendar hidden |
| macro | 15 | cycle, inventory, corporate, trade, transmission, rates, liquidity, crisis, assets, sentiment, narrative, forecast, scenario, simulate, summary | 경제 및 shock lens |
| industry | 9 | summary, timeline, lifecycle, concentration, dynamics, polarization, edges, map, theme | market relation 및 value-chain lens |
| credit | 8 | grade, repayment, leverage, liquidity, cashflow, business, reliability, disclosure | risk lens |
| quant | 48 | indicators, signals, verdict, momentum, volatility, forecast, marketContext, regime, pattern, chartPatterns, beta, benchmark, factor, tailrisk, residual, liquidity, flow, volume, divergence, quality, value, earnings, sentiment, toneChange, eventSignal, riskText, governanceQuant, ranking, pairs, screen, altman, piotroski, beneish, accruals, qfactor, qmj, bab, surprise, fundmom, meanvar, riskparity, allocation, strategy, backtest, style, entry, walkforward, multi | price, risk, factor, portfolio, strategy lens |

엔진별 수동 adapter 147개를 만들면 capability와 UI가 즉시 drift한다. Universe executor는 엔진 이름이 아니라 기존 표준 evidence ref를 소비해야 한다.

## 7. 재사용해야 하는 기존 계약

| 자산 | 경로 | 재사용 이유 |
|---|---|---|
| `Ref` | `src/dartlab/ai/contracts.py` | source, payload, provenance, docId/page/line/sourcePath/confidence 표준 |
| `VariableObservation` | `src/dartlab/simulate/stateCompiler.py` | entityId, signalId, eventAt, availableAt, knowledgeAsOf, revisionId, content hash |
| `VintageRef` | `src/dartlab/simulate/vintage.py` | artifact hash, payload hash, exact as-known와 시간 인과 |
| capability live builder | `src/dartlab/reference/capability/builder.py` | docstring에서 생성, 사본 drift 0 |
| search graph sidecar | `src/dartlab/providers/dart/search/entityGraph*.py` | optional relation hint와 manifest/rollback 선례. factual assertion 정본으로는 사용 금지 |
| data core | `ui/packages/runtime/src/data/fetch/request.ts` | public/local 공통 fetch, cache, dedup |
| map components | `ui/packages/surfaces/src/map/**` | atlas, ecosystem, card, simulator 재사용 |

## 8. public 라이선스 경계

HF dataset card는 CC BY 4.0으로 표시되고 라이브러리 코드는 Apache 2.0이다. 그러나 dataset 단위 표시는 모든 upstream field의 재배포 허가 receipt가 아니다. gather의 `naverTheme`, `naverIndustry`, `naverEtf`, `naverEtn`은 registry 자체가 local personal use 및 public redistribution 위험을 명시한다.

Universe public scene은 provenance별 `redistributionClass`를 검사해야 한다.

- `public`: DART, SEC EDGAR, 허용된 KRX 및 공공 source
- `metadataOnly`: brokerage title, date, original link. 본문 없음
- `localOnly`: 네이버 편집 데이터와 명시된 개인용 source
- `unknown`: 기본 차단

`scan-screener-os`의 valuation publish boundary P0가 해결되기 전 `per`, `pbr`, `dividendYield` public 확대는 금지한다.

source별 `RedistributionReceipt`는 allowedFields, prohibitedFields, attribution, policyVersion, reviewedAt을 가져야 한다. receipt가 없거나 만료되면 `unknown`으로 fail closed한다.

## 9. 감사 판정

### 이미 있는 것

- 서버리스 public hosting
- 3단계 map LOD artifact
- 2,664개 KR 회사와 34개 산업
- company 1-hop egograph
- browser Parquet range read
- exact BM25 range search
- DART와 EDGAR 동형 panel
- capability 및 Skill OS graph
- evidence와 vintage primitives

### 없는 것

- relation assertion identity
- exact sourceRef 및 시간
- fact, candidate, inference, scenario 분리
- atlas-first lazy loader
- projection contract
- evidence drawer와 known-at time lens
- renderer-independent scene contract

### 최종 ROI

새 graph platform을 만들 이유는 없다. 현재 자산의 약 80%를 재사용할 수 있다. 제품 가치는 남은 20%인 evidence contract, quality gate, projection runtime, UX truthfulness에서 생긴다.
