---
id: engines.company
title: Company
kind: curated
scope: builtin
status: observed
category: engines
purpose: Company 엔진은 종목코드 하나를 target으로 고정하고 재무, 공시, 검색, 분석, 신용, 수집, 퀀트, 매크로, 스토리, 산업 연결을 제공하는 facade 실행 스킬이다. 트리거 — '회사 분석', '단일 기업', '005930', 'Company.panel'.
whenToUse:
  - Company
  - company
  - 단일 기업 분석
  - show
  - disclosure
  - filings
  - analysis
  - credit
  - gather
  - quant
  - macro
  - story
inputs:
  - stockCode 또는 ticker
  - topic
  - period
  - axis
outputs:
  - Company 객체
  - topic DataFrame
  - 하위 엔진 결과
  - evidence refs
capabilityRefs:
  - Company
  - Company.panel
  - Company.select
  - Company.trace
  - Company.filings
  - Company.analysis
  - Company.credit
  - Company.gather
  - Company.quant
  - Company.macro
  - Company.story
  - Company.reportModel
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.analysis
  - engines.credit
  - engines.gather
  - engines.quant
  - engines.macro
  - engines.story
sourceRefs:
  - dartlab://skills/engines.company
requiredEvidence:
  - target
  - period
  - topic
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 대상 기업
  - 공개 호출
  - topic/axis
  - 반환 타입과 근거
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
failureModes:
  - 종목코드/market을 확정하지 않고 분석을 시작함
  - show topic과 analysis axis를 혼동함
  - 원자료 조회 결과를 분석 결론으로 바로 말함
forbidden:
  - target 없는 Company 작업을 완료 처리하지 않는다.
  - table/value/date ref 없이 숫자를 말하지 않는다.
  - 공개 메서드, 반환 형태, 하위 엔진 연결이 바뀌었는데 이 skill을 갱신하지 않은 상태로 완료 처리하지 않는다.
examples:
  - 삼성전자 재무제표 조회
  - 미국 기업 공시와 분석 연결
  - 단일 기업 story 생성
  - dartlab.Company 사용법
  - 005930 분석 시작
  - AAPL EDGAR 재무 분석
  - 단일 기업 topic catalog 확인
  - 기간 간 텍스트 변화 (diff) 추적
procedure:
  - dartlab.Company(code) 로 종목코드 또는 ticker 로 facade 생성.
  - 정식 topic 은 IS · BS · CF · CIS · SCE · ratios. 주석은 섹션명으로 검색.
  - c.panel(topic) 으로 단일 topic 본문 (source priority — finance > report > docs).
  - 깊이 분석은 c.analysis · c.credit · c.quant · c.macro · c.story 같은 하위 엔진.
  - 답변에 target · period · topic · tableRef · valueRef · dateRef · executionRef 묶음.
linkedSkills:
  - engines.panel
  - engines.analysis
  - engines.scan
  - engines.story
  - engines.credit
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-07'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`Company`는 DartLab의 단일 기업 facade다. 사용자는 종목코드나 ticker로 `Company`를 만들고, 이 객체에서 원자료 조회, 공시 탐색, 분석, 신용, gather, quant, macro, story를 호출한다.

한국 DART 회사와 미국 EDGAR 회사 모두 같은 facade 패턴을 따른다. 세부 topic/컬럼은 시장과 provider별로 다를 수 있으므로 반환값의 source와 기준일을 확인한다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

raw = c.panel("BS")
selected = c.select("매출액")
trace = c.trace("영업이익")

analysis = c.analysis("financial", "수익성")
credit = c.credit()
price = c.gather("price")
quant = c.quant("모멘텀")
macro = c.macro("사이클")                          # 시장 매크로 (사이클/위기/시나리오/유동성/심리)
sensitivity = c.analysis("macro", "매크로민감도")  # 기업 단위 매크로 민감도는 analysis 엔진
story = c.story()
reportModel = c.reportModel()                      # 전문 리포트 계약(ReportModel, schemaVersion=2)
industry = c.industry()
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

단일 종목 질문은 본 엔진이 1 차 진입점. 다음 4 룰 강행:

1. **`EngineCall(apiRef="Company.panel", args={"stockCode": "...", "topic": "..."})` 1 회로 다수 답변 가능** — 응답 `data` dict 에 `dcrBadge` (Track G 7 축 신용) + `industryBadge` (Track E 산업/lifecycle/peers) 자동 부착. 신용·산업 질문은 추가 EngineCall 불필요.
2. **본문 안 숫자 / 점수 / 등급 / peers 명에 inline ref 표기 필수** — tool result 의 `refs` 배열에 들어온 id 그대로 `table:Company.panel:005930` 또는 `tableRef:id` literal 로 표기한다.
3. **다중 종목 비교는 `PeerCompareN` 1 회 강제** (2~12 종목) — Company.panel 를 N 회 반복 호출 + RunPython 정렬 패턴 금지. 메모리 압박 + refs 가치체인 약화.
4. **RunPython 직접 BS/IS/CF 비율 계산 금지** — Company.panel 결과의 `dcrBadge.axes` (7 축 신용) 또는 Company.analysis 결과의 `items` / `history` 인용. 같은 비율 재계산은 raw fallback 만.

## 호출 동작

Company 생성 시 target과 market/provider를 확정한다. 이후 `show/select/trace`는 원자료 조회, `analysis/credit/quant/macro/story`는 하위 엔진 호출, `gather`는 보조 데이터 수집, `disclosure/liveFilings/readFiling`은 공시 접근을 담당한다.

무인자 또는 topic 누락 호출은 가능한 topic/axis 가이드를 반환할 수 있다. 데이터가 없으면 결손을 0으로 채우지 않고 빈 DataFrame, `None`, flags, 제한 메시지로 표현한다.

### `c.panel()` 응답 data 의 자동 부착 필드 (단일 종목 답변의 1 차 진입점)

`c.panel(topic)` 의 반환 dict (server agent/MCP 경유 시 `EngineCall(apiRef="Company.panel")` 결과의 `data`) 에는 원자료 외에 다음이 자동 부착된다 — 별도 도구 호출 없이 그대로 인용:

| key | 내용 | 사용처 |
| --- | --- | --- |
| `dcrBadge.grade` · `dcrBadge.score` · `dcrBadge.healthScore` · `dcrBadge.outlook` | dCR 등급 + 위험/건전성 점수 + 전망 | 답변 헤더 chip · 신용 한 줄 결론 |
| `dcrBadge.axes` | **7 축 완전 형태** — 각 항목 `{name, weight, score}` (채무상환 25w/X / 자본구조 20w/X / 유동성 15w/X / 현금흐름 15w/X / 사업안정성 10w/X / 재무신뢰성 10w/X / 공시 5w/X) | 7 축 약점 분해 — 추가 `c.credit()` 호출 불필요 |
| `dcrBadge.confidence` · `dcrBadge.confidenceMethod` | 신뢰도 (0-100, "ratio" 등) | `[conf:N]` chip |
| `industryBadge.industryId` · `industryBadge.industryName` · `industryBadge.stageName` · `industryBadge.phase` | 산업 식별 + 라이프사이클 단계 (도입·성장·성숙·재도약·쇠퇴) | 답변 헤더 chip · 산업 맥락 |
| `industryBadge.peers` | 같은 산업 노드의 동종 종목 list | 비교 후보 |

**가드** — 7 축 점수가 `dcrBadge.axes` 에 *이미 있다*. "7 축 약점 / 점수 차이" 질문에 `EngineCall("credit")` 재호출 금지 (반환은 axis 가이드 metadata 만 — 실제 점수 아님). 약점 분해 양식: `약점 = weight × score 기여도`. 예: 재무신뢰성 10% × 25.0 = 2.50, 채무상환 25% × 6.77 = 1.69.

### stockCode resolve 실패 시 행동 (회복 절차)

`c = dartlab.Company(code)` 가 코드 미발견 / 비상장 / 데이터셋 미수집 면 fail-fast — 같은 코드로 `c.panel / c.credit / c.analysis` 등 반복 호출 금지. 한 번 `company_not_resolved` 면 즉시 답변에 "데이터 없음" + 가능한 원인 (잘못된 6 자리 / 비상장 / 미수집) 명시. 회사명만 주어졌으면 `dartlab.Company.search("회사명")` 1 회로 코드 lookup 후 재시도, 그것도 fail 이면 멈춤.

### dataAsOf freshness

`c.panel()` / `c.analysis()` 결과의 `latestPeriod` (또는 `dataAsOf`) 가 *오늘* 기준 stale (예: 2 분기 이상 뒤) 일 수 있다. 정기보고서 공시 지연 / 분기 잠정실적 미반영 / fixture 환경 가능성. 답변 헤더 chip 옆에 `📅 데이터 as-of {latestPeriod}` 노출 권장 — 사용자가 "지금이 최신인가" 즉시 판단.

## 전체 축/메서드 목록

| method | 담당 | 대표 호출 |
| --- | --- | --- |
| search/listing/resolve/codeName/status | 기업 식별/목록 | `dartlab.Company.search("삼성전자")` |
| filings/disclosure/liveFilings/readFiling | 공시 목록/본문 | `c.filings()` |
| rawFinance/rawReport | raw parquet 접근 | `c.rawFinance()` |
| panel/select/trace/diff | 원자료 조회/추적/비교 | `c.panel("BS")` |
| keywordTrend/news/watch | 텍스트/뉴스/감시 | `c.news()` |
| story/validateStory/storyTree/narrativeDiff | 보고서/스토리 | `c.story()` |
| reportModel | 전문 리포트 계약(thesis·섹션·pro 블록) | `c.reportModel("valuation")` |
| analysis | 재무/가치/전망 분석 | `c.analysis("financial", "수익성")` |
| credit | 신용/부실위험 | `c.credit()` |
| gather | 외부/보조 데이터 | `c.gather("price")` |
| quant | 정량 분석 | `c.quant("모멘텀")` |
| macro | 시장 매크로 (사이클/위기/시나리오/유동성/심리, KR 자동) | `c.macro("사이클")` |
| table/topics/sources/index/facts | 탐색 메타 | `c.index()` |
| retrievalBlocks/contextSlices/ask | AI 컨텍스트/질의 | `c.ask("질문")` |
| sector/rank/audit/market/currency/fiscalYearEnd | 회사 메타/검증 | `c.market()` |
| network/governance/workforce/capital/debt | scan view 연결 | `dartlab.scan("governance")` |
| causalWeights/valuationImpact/industry/view | story/industry/view 연결 | `c.industry()` |

## 대표 반환 형태

Company 메서드는 topic별 DataFrame, dict/list, 하위 엔진 결과 객체, 또는 `None`을 반환한다.

```text
stockCode/ticker, companyName, market, period/date,
topic/axis, source, metric, value, unit,
tableRef, valueRef, dateRef, executionRef
```

`show/select/trace`는 원자료 기반 table/selection/lineage가 중심이고, `analysis/credit/quant/macro/story`는 각 엔진의 반환 계약을 따른다.

## evidence 기준

단일 기업 답변은 target, period, topic/axis, tableRef, valueRef, dateRef, executionRef를 남긴다. 공시나 뉴스는 filing id, URL/source, 접수일/게시일을 함께 확인한다.

## 기본 실행 순서

1. `dartlab.Company(code_or_ticker)`로 target을 고정한다.
2. 원자료 확인이면 `show/select/trace`, 심층 분석이면 하위 엔진 메서드를 고른다.
3. 반환값의 기준일, source, 결손/flags를 확인한다.
4. 숫자 claim은 valueRef/tableRef에 묶는다.
5. 여러 축을 조합하는 최종 서술은 `story`로 넘긴다.

## 기본 검증

스킬은 공개 실행 문서다. Company 공개 메서드, 하위 엔진 연결, 대표 반환 형태가 바뀌면 이 파일과 관련 응용 스킬을 같은 변경에서 갱신한다.

## 메모리 안전 — 다중 회사 loop

Polars = 네이티브 Rust 힙, `gc.collect()` 회수 불가, Company 1 개 ≈ 200~500MB. 다중 회사 loop 진입점은 매 iteration 끝에 `cleanupBetweenCompanies(label=...)` 호출 또는 `with Company(code) as c:` (context manager `__exit__` 자동 호출) 강행. 누락 시 OOM.

자동 검출 lint:

| 스크립트 | 룰 |
|---|---|
| `tests/audit/cleanupBetweenCompaniesCalls.py` | M8 — AST heuristic 으로 (1) `for x in <stockCodes\|codes\|tickers\|parquetFiles>:` 패턴 (2) body 안 `loadData()` / `Company()` 무거운 호출 (3) body 안 `cleanupBetweenCompanies(` 부재 — 세 조건 AND 시 violation. baseline `tests/audit/_baselines/cleanupCalls.json` 외만 fail |


---

# 흡수된 sub-spec 본문 (Phase D-1, 2026-05-18)

## (흡수) engines.company.disclosureEvent 본문

## 절차

- 공시 목록의 접수일, 제목, 유형을 확인한다.
- 가능한 경우 경량 본문 조회로 제목 기준 판단을 보강한다.
- 본문 미조회 상태에서는 제목 기준 우선순위라고 명시한다.

## 공개 호출 방식

- `c = dartlab.Company("005930")`
- `c.panel()`
- `c.panel("BS")`
- `c.index()`
- `c.trace()`

## 호출 동작

- 종목코드 또는 ticker를 target으로 고정하고 재무, 공시, 가격, 하위 엔진 호출의 단일 진입점을 제공한다. 무인자 호출은 사용 가능한 topic/axis 가이드를 반환한다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- Company 객체 메서드는 topic별 DataFrame, dict, 또는 하위 엔진 결과를 반환한다. 핵심 식별자는 stockCode/ticker, companyName, period, topic, source, value, unit이다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.

## (흡수) engines.company.docsInternals 본문

## 엔진 역할

Company panel internals 는 DART 본문을 `panel` 산출물로 읽는 내부 추적 skill 이다. 공개 사용자 API 는 `c.panel` / `c.panel(topic)` 이고, 서버/뷰어/AI 는 동일한 panel artifact 를 읽는다.

## 공개 호출 방식

내부 점검은 panel 모듈을 직접 호출한다.

```python
import dartlab
from dartlab.providers.dart.panel.text import panelTextWide

c = dartlab.Company("005930")
df = panelTextWide(c.stockCode)
view = c.panel("businessOverview")
```

## 호출 동작

- 원천 zip XML 은 original archive 계층에 남을 수 있지만, 분석/뷰어/검색의 read SSOT 는 `data/dart/panel` 산출물이다.
- panel build 는 `src/dartlab/providers/dart/panel/build` 가 담당한다. topic 매핑은 `src/dartlab/providers/dart/panel/mapper.py` 와 panel schema 계층에서 관리한다.
- row identity 는 panel 컬럼의 `topic`, `blockType`, `blockOrder`, `sectionLeaf`, `contentRaw`/`content` 조합으로 판단한다.
- DART 본문 조회의 사용자/API 표면은 panel topic catalog 와 `c.panel(topic)` 뿐이다.

## 대표 반환 형태

`panelTextWide(code)` 와 `c.panel(topic)` 은 topic/block 행과 period 컬럼을 가진 wide DataFrame 을 반환한다. 핵심 식별자는 stockCode, corpName, topic, blockType, blockOrder, period, content/contentRaw 이다.

## 기본 검증

- panel 계약 변경 시 `engines.panel`, `operation.dataLineage`, 서버 viewer 계약, landing viewer 검증을 함께 갱신한다.
- DART 본문 계층에서 옛 문서 읽기 경로, 폐기된 섹션 표면, 폐기된 대량 다운로드 표면이 되살아나면 SSOT 회귀로 본다.

## (흡수) engines.company.finance 본문

## 엔진 역할

`company.finance` 는 사용자 capability 가 아니라 *Company 엔진 내부 sub-module* 이다. XBRL 표준 계정 매핑 + 주석 영역 6 sub-domain 파서를 묶어 단일 회사의 재무 시계열을 빌드한다. dartlab 공개 호출은 Company facade 경유.

본 sub-spec 은 운영 SSOT — 파일 구조 · 6 sub-domain 책임 · 검증 결과 · 매핑 사이클을 한 곳에서 관리.

## 공개 호출 방식

```python
import dartlab

with dartlab.Company("005930") as c:
    # 시계열 (분기 / 연도 / 누적) — Plan v10: c.panel 단일 진입
    q = c.panel("IS", freq="Q")
    y = c.panel("IS", freq="Y")
    cum = c.panel("IS", freq="YTD")

    # 재무비율
    r = c.panel("ratios")                       # CFS 기본
    rOfs = c.panel("ratios", scope="separate")  # OFS

# 6 sub-domain — 주석 영역 파서
from dartlab.finance.summary import fsSummary
from dartlab.finance.majorHolder import majorHolder, holderOverview
from dartlab.finance.segment import segments
from dartlab.finance.affiliate import affiliates
from dartlab.finance.costByNature import costByNature
from dartlab.finance.rawMaterial import rawMaterial

result = fsSummary("005930")        # 요약재무 브릿지 매칭
mh = majorHolder("005930")          # 최대주주 + 시계열
seg = segments("005930")            # 사업부문 / 제품 / 지역
aff = affiliates("005930")          # 관계기업 / 공동기업
cbn = costByNature("005930", "y")   # 비용 성격별
raw = rawMaterial("005930")         # 원재료 / 생산설비 / 시설투자
```

## 호출 동작

- `Company.timeseries` / `annual` / `cumulative` — `buildTimeseries(stockCode, fsDivPref)` 위임. CFS 우선, 없으면 OFS fallback. snakeId × period 의 nested dict 반환.
- `Company.ratios` — `calcRatios(series, marketCap=None)` 위임. ROE · ROA · 마진 · 부채비율 · FCF 등.
- `Company.getTimeseries(period, fsDivPref)` — 4 조합 (q/y/cum × CFS/OFS) 명시 조회.
- `fsSummary(source, ifrsOnly=True)` — 4 단계 브릿지 매칭. 2 년 미만 → None.
- `majorHolder(stockCode)` — 사업보고서 "VII. 주주에 관한 사항" 파싱.
- `segments(stockCode)` / `affiliates(stockCode)` — 주석 표 추출 (일반 + 횡전개).
- `costByNature(stockCode, period)` — 3 가지 테이블 유형 (inline / split / multiCol) 자동 감지.
- `rawMaterial(stockCode)` — 원재료 + 유형자산 변동 + 시설투자 3 영역 동시 추출.

미매핑 계정 발견 시 `engines.mappers` 학습 후보 데이터로 흐른다 (사람 검토 후 `AccountMapper.release()`).

## 대표 반환 형태

```text
Company.ratios
→ RatioResult
   roe : float          # 자기자본이익률 (%)
   roa : float          # 총자산이익률 (%)
   operatingMargin : float
   debtRatio : float
   currentRatio : float
   fcf : float          # Free Cash Flow

fsSummary(source)
→ AnalysisResult | None
   corpName : str | None
   nYears : int
   allRate : float | None        # 전체 매칭률
   contRate : float | None       # 연속 매칭률
   segments : list[Segment]      # 구간 통계
   breakpoints : list[BridgeResult]
   yearAccounts : dict[str, YearAccounts]

majorHolder(stockCode)
→ MajorHolderResult | None
   majorHolder : str | None      # 최대주주명
   majorRatio : float | None
   totalRatio : float | None
   holders : list[Holder]
   timeSeries : pl.DataFrame
```

## 코어 finance 엔진

`src/dartlab/providers/dart/finance/` — 분기별 · 연도별 · 누적 시계열 + 재무비율.

| 파일 | 역할 |
|------|------|
| `__init__.py` | public API export |
| `mapper.py` | XBRL account_id + 한글명 → snakeId 매핑 (engines.mappers 위임) |
| `sceMapper.py` | 자본변동표 (SCE) 별도 매퍼 |
| `pivot.py` | parquet → 시계열 dict 피벗 + 동의어 병합 + 연도별/누적 집계 |
| `scanAccount.py` | 미매핑 계정 스캔 (학습 후속 데이터) |
| `spec.py` | 엔진 명세 (`summary.mappedAccounts` 등) |

데이터 SSOT — `reference/data/accountMappings.json` (`learnedSynonyms: 31,489` / `standardAccounts: 3,402` / `merged: 34,171`). 학습 사이클은 `engines.mappers` 참조.

### 시계열 API

| 함수 | 반환 | 설명 |
|------|------|------|
| `buildTimeseries(stockCode, fsDivPref="CFS")` | `(series, periods)` | 분기별 standalone |
| `buildAnnual(stockCode, fsDivPref="CFS")` | `(series, years)` | 연도별 |
| `buildCumulative(stockCode, fsDivPref="CFS")` | `(series, periods)` | 분기별 누적 |

### 값 추출

| 함수 | 설명 |
|------|------|
| `getTTM(series, sjDiv, snakeId)` | 최근 4 분기 합 (IS/CF) |
| `getLatest(series, sjDiv, snakeId)` | 최신 non-null 값 (BS) |
| `getAnnualValues(series, sjDiv, snakeId)` | 전체 시계열 리스트 |
| `getRevenueGrowth3Y(series)` | 매출 3 년 CAGR (%) |

### 비율 계산

`calcRatios(series, marketCap=None)` → `RatioResult` (ROE · ROA · 마진 · 부채 · FCF 등).

### Company 통합

| 호출 | 설명 |
|--------|------|
| `c.panel(topic, freq="Q")` | 분기별 (CFS) — topic ∈ BS·IS·CF·CIS·SCE·ratios |
| `c.panel(topic, freq="Y")` | 연도별 (CFS) |
| `c.panel(topic, freq="YTD")` | 분기별 누적 (CFS) |
| `c.panel("ratios")` | 재무비율 (CFS) |
| `c.panel(topic, freq=..., scope="separate")` | 커스텀 (CFS/OFS scope) |

### scope 파라미터

- `"consolidated"` — 연결재무제표 (기본값). 없으면 separate fallback.
- `"separate"` — 별도재무제표. 없으면 consolidated fallback.

### 검증 결과 (삼성전자 005930, 2024)

| 지표 | CFS | OFS |
|------|-----|-----|
| Revenue | 300.9T | 209.1T |
| ROE | 8.29% | 5.19% |
| Debt Ratio | 27.40% | 20.67% |

## 6 sub-domain (주석 영역 파서)

`src/dartlab/providers/dart/docs/finance/{name}/` + `disclosure/rawMaterial/` 의 6 영역.

### 1. summary — 요약재무 브릿지 매칭

`dartlab.finance.summary.fsSummary(source, ifrsOnly=True)` → `AnalysisResult | None`.

DART 공시 요약재무정보에서 숫자 브릿지 매칭으로 계정명을 연도간 매핑하여 시계열 생성.

| 파일 | 설명 |
|------|------|
| `constants.py` | 매칭 임계값, 핵심 계정 목록 |
| `types.py` | `AnalysisResult` · `Segment` · `BridgeResult` · `YearAccounts` |
| `contentExtractor.py` | 요약재무 영역 추출 (연결 우선) |
| `bridgeMatcher.py` | 4 단계 숫자 브릿지 매칭 알고리즘 |
| `segmentation.py` | 전환점 탐지, 구간 분리 |
| `pipeline.py` | `fsSummary()` · `loadYearData()` 오케스트레이터 |

**매칭 알고리즘 (4 단계)**:
1. **정확 매칭** — N년 전기 금액 == N-1년 당기 금액 (차이 &lt; 0.5)
2. **재작성 보정** — 이름 유사도 0.8+ 금액 차이 5% 이내
3. **명칭변경 보정** — 이름 유사도 0.6+ 금액 차이 5% 이내
4. **특수항목** — EPS · 회사수 등 이름 강제 매칭

**검증** — 158 개 기업 구간 내 97.7%, 오매칭 0.07%. 임계 `BREAKPOINT_THRESHOLD = 0.85`. 핵심 계정 10 개.

**AnalysisResult 필드** — corpName / nYears / nPairs / nBreakpoints / nSegments / allRate / contRate / segments / breakpoints / pairResults / yearAccounts.

**BridgeResult** — `pairs: {당해년도 계정명: 전년도 계정명}` · `yearGap` (보통 1, 갭 있으면 2+).

**입력 데이터** — polars DataFrame 또는 parquet. 필수: `year` / `report_type` / `rcept_date` / `section_title` / `section_content`. 선택: `corp_name`.

### 2. majorHolder — 주주 현황

`dartlab.finance.majorHolder.majorHolder(stockCode)` → `MajorHolderResult | None`.
`dartlab.finance.majorHolder.holderOverview(stockCode)` → `HolderOverview | None`.

**MajorHolderResult** — corpName / majorHolder (최대주주명) / majorRatio / totalRatio (특수관계인 포함) / holders / timeSeries.

**HolderOverview** — bigHolders (5% 이상) · minority (소액주주) · voting (의결권).

**파싱 성공률 (267 종목)** — 최대주주 100% (227/0/40) · 5% 이상 주주 100% (217/0/50) · 소액주주 100% (214/0/53) · 의결권 100% (223/0/44).

**파싱 전략**:
- majorHolder — "VII. 주주에 관한 사항" → "성 명 | 관 계" 헤더 + 8-cell 데이터행, "본인"/"최대주주" 관계 식별
- 5% 이상 주주 — `| 5% 이상 주주 | 주주명 | 소유주식수 | 지분율 | 비고 |` 구조
- 소액주주 — 단일행 `| 주주수 | 전체주주수 | 비율 | 소액주식수 | 총발행 | 비율 |`
- 의결권 — A(발행총수) ~ F(행사가능) 보통주/우선주 분리

**주의** — 2015 년 이전 보고서 테이블 구조 차이로 지분율 오류 가능. 스팩/비상장사 5% 이상 주주/소액주주 부재.

### 3. segment — 사업부문 보고

`dartlab.finance.segment.segments(stockCode)` → `SegmentsResult` (사업부문 · 제품 · 지역 테이블).

| 파일 | 설명 |
|------|------|
| `types.py` | `SegmentsResult` · `SegmentTable` |
| `extractor.py` | `core.notesExtractor` re-export |
| `parser.py` | 부문 테이블 파싱 (일반 + 횡전개) |
| `pipeline.py` | `segments()` 오케스트레이터 |

### 4. affiliate — 관계기업 / 공동기업

`dartlab.finance.affiliate.affiliates(stockCode)` → `AffiliatesResult` (지분 현황 + 변동).

| 파일 | 설명 |
|------|------|
| `types.py` | `AffiliatesResult` · `AffiliateProfile` · `AffiliateMovement` |
| `extractor.py` | 마크다운 테이블 행 추출 (`parseTableRows`) |
| `parser.py` | 프로필 / 변동 파싱 (일반 + 횡전개) |
| `pipeline.py` | `affiliates()` 오케스트레이터 |

### 5. costByNature — 비용의 성격별 분류

`dartlab.finance.costByNature.costByNature(stockCode, period)` → `CostByNatureResult`.

**파일 구성** — `types.py` (`CostByNatureResult`) · `parser.py` (inline/split/multiCol 3 방식) · `pipeline.py`.

**성능** — 171 / 171 (100%) 파싱 성공 · 시계열 173 종목 · 교차검증 일치율 87.8% · null 17.5%.

**파서 구조**:
- 3 가지 테이블 유형 자동 감지 (inline / split / multiCol)
- 30 개 정규화 매핑 (487 원본 → 표준)
- 22 가지 합계행 패턴 자동 제거

**period** — `"y"` 사업보고서 (연간) · `"q"` Q1/반기/Q3/사업보고서 (분기) · `"h"` 반기.

**ratios** — 각 비용 항목의 양수 합계 대비 비율 (%) DataFrame (year · account · amount · ratio).

**제한** — 금융업/리츠/지주회사 58 / 267 미공시. 교차검증 불일치 12.2% 는 소급 재작성 (파서 오류 아님).

### 6. rawMaterial — 원재료 · 생산설비 · 시설투자

`dartlab.finance.rawMaterial.rawMaterial(stockCode)` → `RawMaterialResult | None`.

**RawMaterialResult** — corpName / year / materials / equipment / capexItems.

- **RawMaterial** — segment · item · usage · amount · ratio · supplier
- **Equipment** — land · buildings · structures · machinery · construction · vehicles · fixtures · rou · undelivered · other · total · depreciation · capex
- **CapexItem** — segment · amount

**파싱 성공률 (267 종목)** — 원재료 93.0% · 생산설비 33.8% · 시설투자 16.2%. 125 종목 None (해당사항 없음 또는 매입 테이블 부재).

**품질 검증** — ratio 이상 (>100%) 2 / DL이앤씨 1, 그 외 0 건 (amt-None / 숫자 item / total 음수 / 1조 초과 / 런타임 에러).

**검증 완료 종목 스팟체크** — 삼성전자 (14 건 매입 · 2,059,452 설비) · 현대차 (17 건 · 44,533,941) · SK하이닉스 (5 건 · 60,157,474) · LG화학 (5 건 · 54,570,446) · LG · SK · F&F.

**파싱 전략 (원재료 12 단계)**:
1. 헤더 직접 감지 — `(매입액|투입액)` + `(품목|원재료|부문)` 조합
2. `_findHeaderIndices()` 동적 매핑
3. shifted 행 감지 (segment 생략 시 왼쪽 밀림)
4. 합쳐진 "매입액 (비율)" 셀 분리 — `1,483,067 (43.8%)` 패턴
5. 연도별 헤더 (`제N기`, `20XX년`) 지원
6. 분할 헤더 (row1 + row2 병합)
7. 비율 > 100 shifted 감지
8. 연도 컬럼 ratio 제외
9. 생산 테이블 필터 (생산능력/수량 키워드)
10. 숫자 item 필터 (shift 데이터 판단)
11. 각주 참조 필터 (`(주N)`)
12. amount 없는 헤더 진입 차단

**제한** — DL이앤씨 헤더 shifted 2 건 · 단위 혼재 (USD/천USD/백만원) 미지원 · 생산설비 33.8% (테이블 형식 다양).

## 의존 (sub-domain 공통)

- `dartlab.frame.dataLoader` — `loadData` · `extractCorpName` · `PERIOD_KINDS`
- `dartlab.providers.notesExtractor` — `extractNotesContent` · `findNumberedSection`
- `dartlab.providers.reportSelector` — 보고서 선택
- `dartlab.providers.tableParser` — 마크다운 테이블 파싱, 금액/단위 처리
- `engines.mappers` — 계정명 → snakeId 정규화

## evidence 기준

- finance 시계열 인용 시 `stockCode` · `fsDivPref` · `period` · `snakeId` · `source` (DART).
- 6 sub-domain 인용 시 `parsing_success_rate` 명시 (예 — 원재료 93.0%, 생산설비 33.8%).
- 미매핑 계정 발견 시 `engines.mappers` 후속 학습 후보로 로그.

## 기본 검증

```python
import dartlab
with dartlab.Company("005930") as c:
    print(c.panel("ratios").roe)                       # 8.29 (CFS)
    print(c.panel("ratios", scope="separate").roe)     # 5.19 (OFS)

from dartlab.finance.summary import fsSummary
result = fsSummary("005930")
print(f"{result.corpName}: {result.allRate:.1%}")  # 매칭률
```

## 변경 이력

- 2026-03-06 — 6 sub-domain 패키지 초기 구축 (affiliate / segment / summary / majorHolder / costByNature / rawMaterial)
- 2026-03-06 — `stockCode` 시그니처 전환, `extractor` 중복 제거 → `core` re-export
- 2026-03-07 — rawMaterial 실무 투입
- 2026-03-09 — XBRL 계정 표준화 + Company `docs/finance` 통합
- 2026-05-12 — STATUS.md 7 곳 → 본 sub-spec 통합 (Skill OS 운영 SSOT 승격)

## (흡수) engines.company.researchStarter 본문

## 절차

- 기업명, 종목코드, ticker 중 무엇이 입력됐는지 먼저 식별한다.
- 질문 목적이 수익성, 현금흐름, 신용, 공시, 비교, 밸류에이션, 배당, 지배구조 중 어디에 가까운지 skill 검색으로 고른다.
- 단일 기업과 특정 축이 함께 있으면 해당 engine skill과 Company.analysis/Company.panel를 먼저 사용한다. scan skill은 “후보”, “랭킹”, “전체 종목”, “많이 오른” 같은 횡단 의도가 있을 때만 1차 경로가 된다.
- 목적이 불명확하면 engines.story.companyCausal를 기본 후보로 두되, macro와 scan 맥락도 함께 확인한다.
- 선택한 skill의 requiredEvidence를 실행 전 체크리스트로 둔다.
- 실행 가능한 분석 질문이면 첫 답변에서 사용법만 설명하지 말고 target, period, source table ref를 만든 뒤 검산 가능한 결론을 낸다. 데이터가 부족하면 어떤 Company topic 또는 prebuild가 부족한지 한계로 남긴다.

## 공개 호출 방식

- `c = dartlab.Company("005930")`
- `c.panel()`
- `c.panel("BS")`
- `c.index()`
- `c.trace()`

## 호출 동작

- 종목코드 또는 ticker를 target으로 고정하고 재무, 공시, 가격, 하위 엔진 호출의 단일 진입점을 제공한다. 무인자 호출은 사용 가능한 topic/axis 가이드를 반환한다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- Company 객체 메서드는 topic별 DataFrame, dict, 또는 하위 엔진 결과를 반환한다. 핵심 식별자는 stockCode/ticker, companyName, period, topic, source, value, unit이다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.

## (흡수) engines.panel 본문

## 엔진 역할

`panel` 은 한 회사의 전체 공시 지도다. 각 보고기간 공시 문서를 topic 별로 쪼개고 시간축으로 옆으로 늘어놓아 가로화 보드 하나로 만든다. 개별 사업보고서를 하나씩 열지 않고 모든 공시 블록을 시계열로 한 번에 비교한다.

한국 DART 사업보고서는 수십 개 장/하위 항목을 갖는다 — 제 I 장 (회사 개황) ~ 제 XII 장 (상세표). 각 보고서가 분기/연도별로 별도 파일이라서 같은 topic ("사업의 개요") 이 여러 기간에 흩어진다. `panel` 은 이 흩어진 원문을 **topic × 기간 매트릭스**로 재구성한다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")
c.panel.shape                    # 항목 x 기간 격자 크기
c.panel("BS")                    # 단일 topic + source priority
c.trace("BS")                    # 어떤 source 가 선택됐나
c.panel("companyOverview")       # 특정 topic 의 실제 데이터
```

미국 종목도 같은 API:

```python
us = dartlab.Company("AAPL")
us.topics
us.panel("10-K::item1Business")
us.panel("BS")
```

panelTextWide 내부 wide view 는 Polars DataFrame 이므로 자유 필터:

```python
import polars as pl
from dartlab.providers.dart.panel.text import panelTextWide

df = panelTextWide("005930")
df = df.filter(pl.col("topic") == "companyOverview")
```

## 호출 동작

옛 section 공개 facade 는 폐기됐다. 사용자는 `c.panel` 로 격자 전체를 보고 `c.panel(topic)` 으로 진입한다. 내부 panelTextWide view 는 각 행이 한 topic 블록, 각 열이 한 기간인 검증/파이프라인용 구조다.

`c.panel(topic)` 는 source priority 를 적용한다:

1. **finance** (BS, IS, CF, CIS, SCE) — 숫자는 권위 있으므로 docs 본문보다 우선.
2. **report** — DART 정형 공시 데이터.
3. **docs** — 원본 산문 텍스트와 표.

`c.trace(topic)` 는 어떤 source 가 실제 선택됐는지 확인:
- 선택된 source (docs / finance / report).
- 기간별 데이터 커버리지.
- chapter, label 같은 메타.

기간 컬럼의 `null` 은 그 기간 데이터 없음. 0 으로 대체하지 않는다.

## 대표 반환 형태

panelTextWide DataFrame 구조:

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ null         │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
```

### 구조 컬럼

| 컬럼 | 설명 |
|---|---|
| `chapter` | 최상위 장 번호 (I ~ XII). |
| `topic` | snakeCase 표준 식별자 (`companyOverview`, `businessOverview`, `BS`, `IS`, `CF`). |
| `blockType` | `"text"` 또는 `"table"`. |
| `blockOrder` | topic 내 블록 순서 (원문 순서 보존). |
| `textNodeType` | text 블록 sub-type — `"heading"` 또는 `"body"`. table 은 null. |
| `textLevel` | heading 깊이 (1, 2, 3, ...). body / table 은 null. |
| `textPath` | heading 의 구조 경로. |

### 기간 컬럼

`2025Q4`, `2024Q4`, `2024Q3`, ... 최신순. 사업보고서는 Q4. 각 셀 = 그 기간의 원본 payload (text 블록은 산문, table 블록은 markdown table). null = 데이터 없음.

EDGAR 도 같은 구조. topic 이름만 SEC form 규약 (`10-K::item1Business`, `10-K::item7MDA`). 재무 topic (BS, IS, CF) 은 DART 와 같은 이름.

## evidence 기준

- target (종목코드 / ticker).
- period (어느 분기/연도).
- topic (어떤 섹션).
- tableRef / valueRef / dateRef / executionRef.

## 기본 실행 순서

1. `dartlab.Company(code)` 로 회사 객체 생성.
2. 정식 topic 은 IS · BS · CF · CIS · SCE · ratios. 주석은 섹션명 검색.
3. 분석할 topic 선택 → `c.panel(topic)` 으로 본문 확인.
4. 기간 비교가 필요하면 `c.diff()` · `c.diff(topic)`.
5. source 가 의심되면 `c.trace(topic)` 으로 검증.

## 기본 검증

- 결과 DataFrame 의 행 수와 기간 컬럼 수 확인.
- null 비율이 비정상이면 `coverage()` 또는 `trace()` 로 source 점검.
- 숫자 답변은 `tableRef` / `valueRef` / `dateRef` / `executionRef` 묶어서 답변.

## 다음 단계

- [engines.company](/skills/engines.company) — Company facade 전체 메서드 카탈로그.
- **engines.company.disclosureEvent** — 공시 이벤트 추적 (본문 § "(흡수) engines.company.disclosureEvent 본문" 참고).
- **engines.company.usEdgarReview** — 미국 종목 EDGAR 리뷰 (본문 § "(흡수) engines.company.usEdgarReview 본문" 참고).
- [start.quickStart](/skills/start.quickStart) — 8 단계 walkthrough.

## (흡수) engines.company.usEdgarReview 본문

## 절차

- ticker를 식별하고 EDGAR Company 경로가 가능한지 확인한다.
- EDGAR prefetched finance/docs snapshot 또는 OpenEdgar/Company.filings 경로가 있는지 먼저 확인한다. 없으면 데이터 부재를 한계로 좁혀 말하고 DART 전용 경로로 대체하지 않는다.
- Company.analysis, Company.panel, Company.filings/readFiling capability를 찾아 재무와 공시 근거를 분리한다.
- 재무 숫자는 EDGAR finance table/value ref가 있을 때만 말한다. 숫자 claim은 period, metric, value가 들어간 supporting ref에 직접 묶는다.
- filing claim은 접수일, form, 제목 또는 본문 ref에 묶는다.
- fiscal period가 있는 경우 calendar period와 혼동하지 않도록 기준을 밝힌다.
- 검산이 숫자 claim을 거절하면, ref로 뒷받침되는 filing/데이터 가용성 중심의 좁은 답변으로 줄인다.

## 공개 호출 방식

- `c = dartlab.Company("005930")`
- `c.panel()`
- `c.panel("BS")`
- `c.index()`
- `c.trace()`

## 호출 동작

- 종목코드 또는 ticker를 target으로 고정하고 재무, 공시, 가격, 하위 엔진 호출의 단일 진입점을 제공한다. 무인자 호출은 사용 가능한 topic/axis 가이드를 반환한다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- Company 객체 메서드는 topic별 DataFrame, dict, 또는 하위 엔진 결과를 반환한다. 핵심 식별자는 stockCode/ticker, companyName, period, topic, source, value, unit이다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.
