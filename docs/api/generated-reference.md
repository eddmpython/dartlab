---
title: API Reference (Auto-generated)
---

# API Reference

> 이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다. 직접 수정 금지.

## dartlab 공개 API

### `dartlab.Company(codeOrName: str) -> CompanyProtocol`

종목코드/회사명/ticker → 적절한 Company 인스턴스 생성.

**Args:**

- codeOrName: 종목코드, 회사명, 또는 영문 ticker.

**Returns:** CompanyProtocol — DART 또는 EDGAR Company 인스턴스.

```python
import dartlab
c = dartlab.Company("005930")     # 삼성전자 (DART)
c = dartlab.Company("삼성전자")    # 회사명으로도 가능
c = dartlab.Company("AAPL")       # Apple (EDGAR)

c.IS                              # 손익계산서
c.show("businessOverview")        # 사업 개요
c.insights                        # 7영역 인사이트
c.review()                        # 분석 보고서
```

### `dartlab.Fred`

FRED 경제지표 facade.

**Args:**

- api_key: FRED API 키. None이면 ``FRED_API_KEY`` 환경변수 사용.

```python
f = Fred()
gdp = f.series("GDP")
f.compare(["GDP", "UNRATE"], start="2020-01-01")
f.correlation(["GDP", "UNRATE", "FEDFUNDS"])
```

### `dartlab.OpenDart`

OpenDART API 통합 클라이언트.

### `dartlab.OpenEdgar`

SEC public API facade.

### `dartlab.config`

dartlab 전역 설정.

### `dartlab.core`

### `dartlab.llm`

LLM 기반 기업분석 엔진.

### `dartlab.ask(args: str, *, include: list[str] | None = None, exclude: list[str] | None = None, provider: str | None = None, model: str | None = None, stream: bool = True, raw: bool = False, reflect: bool = False, pattern: str | None = None, kwargs)`

LLM에게 기업에 대해 질문.

**Args:**

- *args: 자연어 질문 (1개) 또는 (종목, 질문) 2개.
- provider: LLM provider ("openai", "codex", "oauth-codex", "ollama").
- model: 모델 override.
- stream: True면 스트리밍 출력 (기본값). False면 조용히 전체 텍스트 반환.
- raw: True면 Generator를 직접 반환 (커스텀 UI용).
- include: 포함할 데이터 모듈.
- exclude: 제외할 데이터 모듈.
- reflect: True면 답변 자체 검증 (1회 reflection).

**Returns:** str | None: 전체 답변 텍스트. 설정 오류 시 None. (raw=True일 때만 Generator[str])

```python
import dartlab
dartlab.llm.configure(provider="openai", api_key="sk-...")

# 호출하면 스트리밍 출력 + 전체 텍스트 반환
answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

# provider + model 지정
answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

# (종목, 질문) 분리
answer = dartlab.ask("005930", "영업이익률 추세는?")

# 조용히 전체 텍스트만 (배치용)
answer = dartlab.ask("삼성전자 분석", stream=False)

# Generator 직접 제어 (커스텀 UI용)
for chunk in dartlab.ask("삼성전자 분석", raw=True):
custom_process(chunk)
```

### `dartlab.chat(args: str, *, provider: str | None = None, model: str | None = None, max_turns: int = 5, on_tool_call = None, on_tool_result = None, kwargs) -> str`

에이전트 모드: LLM이 도구를 선택하여 심화 분석.

**Args:**

- *args: (종목, 질문) 2개 또는 질문만 1개.
- provider: LLM provider.
- model: 모델 override.
- max_turns: 최대 도구 호출 반복 횟수.

**Returns:** str: 최종 답변 텍스트.

```python
import dartlab
dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
dartlab.chat("코스피 ROE 높은 회사 알려줘")  # 종목 없이 시장 질문
```

### `dartlab.setup(provider: str | None = None)`

AI provider 설정 안내 + 인터랙티브 설정.

**Args:**

- provider: provider명 또는 alias. None이면 전체 현황 표시.
- 지원: "chatgpt", "openai", "gemini", "groq", "cerebras",
- "mistral", "ollama", "codex", "custom".

**Returns:** None (터미널/노트북에 안내 출력).

```python
import dartlab
dartlab.setup()              # 전체 provider 현황
dartlab.setup("chatgpt")     # ChatGPT OAuth 브라우저 로그인
dartlab.setup("openai")      # OpenAI API 키 설정
dartlab.setup("ollama")      # Ollama 설치 안내
```

### `dartlab.search(keyword: str)`

종목 검색 (KR + US 통합).

**Args:**

- keyword: 종목명, 종목코드, 또는 ticker. 한글이면 KR, 영문이면 US 자동 감지.

**Returns:** pl.DataFrame — 검색 결과 (code, name, market 등).

```python
import dartlab
dartlab.search("삼성전자")
dartlab.search("AAPL")
```

### `dartlab.listing(market: str | None = None)`

전체 상장법인 목록.

**Args:**

- market: "KR" 또는 "US". None이면 KR 기본.

**Returns:** pl.DataFrame — 전체 상장법인 (code, name, market, sector 등).

```python
import dartlab
dartlab.listing()          # KR 전체
dartlab.listing("US")      # US 전체 (향후)
```

### `dartlab.collect(codes: str, *, categories: list[str] | None = None, incremental: bool = True) -> dict`

지정 종목 DART 데이터 수집 (OpenAPI).

**Args:**

- *codes: 종목코드 1개 이상 ("005930", "000660").
- categories: 수집 카테고리 ["finance", "docs", "report"]. None이면 전체.
- incremental: True면 증분 수집 (기본). False면 전체 재수집.

**Returns:** dict — {종목코드: {카테고리: 수집 건수}}.

```python
import dartlab
dartlab.collect("005930")                              # 삼성전자 전체
dartlab.collect("005930", "000660", categories=["finance"])  # 재무만
```

### `dartlab.collectAll(*, categories: list[str] | None = None, mode: str = 'new', maxWorkers: int | None = None, incremental: bool = True) -> dict`

전체 상장종목 DART 데이터 일괄 수집.

**Args:**

- categories: 수집 카테고리 ["finance", "docs", "report"]. None이면 전체.
- mode: "new" (미수집만, 기본) 또는 "all" (전체 재수집).
- maxWorkers: 병렬 워커 수. None이면 키 수에 따라 자동.
- incremental: True면 증분 수집. False면 전체 재수집.

**Returns:** dict — {종목코드: {카테고리: 수집 건수}}.

```python
import dartlab
dartlab.collectAll()                          # 전체 미수집 종목
dartlab.collectAll(categories=["finance"])    # 재무만
dartlab.collectAll(mode="all")                # 기수집 포함 전체
```

### `dartlab.downloadAll(category: str = 'finance', *, forceUpdate: bool = False) -> None`

HuggingFace에서 전체 시장 데이터 다운로드.

**Args:**

- category: "finance" (재무 ~600MB), "docs" (공시 ~8GB), "report" (보고서 ~320MB).
- forceUpdate: True면 이미 있는 파일도 최신으로 갱신.

**Returns:** None.

```python
import dartlab
dartlab.downloadAll("finance")   # 재무 전체 — scanAccount/scanRatio 등에 필요
dartlab.downloadAll("report")    # 보고서 전체 — governance/workforce/capital/debt에 필요
dartlab.downloadAll("docs")      # 공시 전체 — digest에 필요 (대용량 ~8GB)
```

### `dartlab.scan(axis: str | None = None, target: str | None = None, kwargs: Any) -> pl.DataFrame | Any`

시장 전체 횡단분석 -- 15축, 전부 Polars DataFrame.

**Args:**

- axis: 축 이름. None이면 13축 가이드 반환.
- target: 축별 대상 (종목코드, 계정명, 비율명 등).
- **kwargs: 축별 옵션 (annual, fsPref, market 등).

**Returns:** pl.DataFrame — 전종목 횡단 데이터. axis=None이면 13축 가이드 DataFrame.

```python
import dartlab
dartlab.scan()                           # 가이드
dartlab.scan("governance")               # 전종목 지배구조
dartlab.scan("account", "매출액")          # 전종목 매출액
dartlab.scan("ratio", "roe")             # 전종목 ROE
```

### `dartlab.analysis(axis: str | None = None, company: Any | None = None, kwargs: Any) -> pl.DataFrame | dict`

재무제표 완전 분석 — 15축, 단일 종목 심층.

**Args:**

- axis: 축 이름 ("수익구조", "수익성" 등). None이면 15축 가이드.
- company: Company 객체. None이면 해당 축의 분석 항목 목록.
- **kwargs: 축별 옵션.

**Returns:** axis=None → pl.DataFrame (15축 가이드)
company=None → pl.DataFrame (해당 축 calc 목록)
둘 다 있으면 → dict (분석 결과)

```python
import dartlab
dartlab.analysis()                      # 15축 가이드
dartlab.analysis("수익구조")              # 항목 목록
c = dartlab.Company("005930")
dartlab.analysis("수익구조", c)           # 삼성전자 수익구조
c.analysis("수익성")                     # Company 바인딩
```

### `dartlab.gather(axis: str | None = None, target: str | None = None, kwargs: Any) -> pl.DataFrame`

외부 시장 데이터 통합 수집 — 4축, 전부 Polars DataFrame.

**Args:**

- axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
- target: 종목코드/지표코드/검색어. 축별로 다름.
- **kwargs: market ("KR"/"US"), start, end, days 등 축별 옵션.

**Returns:** pl.DataFrame — 축별 시계열 데이터. axis=None이면 4축 가이드 DataFrame.

```python
import dartlab
dartlab.gather()                              # 가이드
dartlab.gather("price", "005930")             # 삼성전자 1년 OHLCV
dartlab.gather("flow", "005930")              # 수급
dartlab.gather("macro")                       # KR 거시 전체
dartlab.gather("macro", "FEDFUNDS")           # 자동 US 감지
dartlab.gather("news", "삼성전자")             # 뉴스
```

### `dartlab.network()`

한국 상장사 전체 관계 지도.

**Args:**

- 없음.

**Returns:** NetworkResult — .show()로 브라우저 시각화, .nodes/.edges로 데이터 접근.

```python
import dartlab
dartlab.network().show()  # 브라우저에서 전체 네트워크
```

### `dartlab.audit(codeOrName: str)`

감사 Red Flag 분석.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명 ("삼성전자").

**Returns:** dict — opinion, auditorChanges, goingConcern, kam, internalControl 등.

```python
import dartlab
dartlab.audit("005930")
```

### `dartlab.forecast(codeOrName: str, *, horizon: int = 3)`

매출 앙상블 예측.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명.
- horizon: 예측 기간 (년). 기본 3.

**Returns:** ForecastResult — predicted, confidence80, confidence95, components.

```python
import dartlab
dartlab.forecast("005930")
dartlab.forecast("005930", horizon=5)
```

### `dartlab.valuation(codeOrName: str, *, shares: int | None = None)`

종합 밸류에이션 (DCF + DDM + 상대가치).

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명.
- shares: 발행주식수. None이면 프로필에서 자동 조회.

**Returns:** ValuationResult — dcf, ddm, relative, summary.

```python
import dartlab
dartlab.valuation("005930")
```

### `dartlab.insights(codeOrName: str)`

7영역 등급 분석.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명.

**Returns:** InsightResult — grades (영역별 등급), summary, strengths, weaknesses.

```python
import dartlab
dartlab.insights("005930")
```

### `dartlab.simulation(codeOrName: str, *, scenarios: list[str] | None = None)`

경제 시나리오 시뮬레이션.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명.
- scenarios: 시나리오명 목록. None이면 전체 기본 시나리오.

**Returns:** SimulationResult — scenarios별 재무 영향 추정.

```python
import dartlab
dartlab.simulation("005930")
```

### `dartlab.governance()`

한국 상장사 전체 지배구조 스캔.

**Args:**

- 없음.

**Returns:** pl.DataFrame — 전종목 지배구조 지표 (종목코드, 종목명, 최대주주지분율, ...).

```python
import dartlab
df = dartlab.governance()
```

### `dartlab.workforce()`

한국 상장사 전체 인력/급여 스캔.

**Args:**

- 없음.

**Returns:** pl.DataFrame — 전종목 인력 지표 (종목코드, 종목명, 직원수, 평균급여, ...).

```python
import dartlab
df = dartlab.workforce()
```

### `dartlab.capital()`

한국 상장사 전체 주주환원 스캔.

**Args:**

- 없음.

**Returns:** pl.DataFrame — 전종목 주주환원 지표 (종목코드, 종목명, 배당수익률, ...).

```python
import dartlab
df = dartlab.capital()
```

### `dartlab.debt()`

한국 상장사 전체 부채 구조 스캔.

**Args:**

- 없음.

**Returns:** pl.DataFrame — 전종목 부채 지표 (종목코드, 종목명, 부채비율, ...).

```python
import dartlab
df = dartlab.debt()
```

### `dartlab.research(codeOrName: str, *, sections: list[str] | None = None, includeMarket: bool = True)`

종합 기업분석 리포트.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명.
- sections: 포함할 섹션명 목록. None이면 전체.
- includeMarket: True면 시장 분석 포함 (기본).

**Returns:** ResearchResult — 구조화된 분석 리포트.

```python
import dartlab
dartlab.research("005930")
```

### `dartlab.digest(*, sector: str | None = None, top_n: int = 20, format: str = 'dataframe', stock_codes: list[str] | None = None, verbose: bool = False)`

시장 전체 공시 변화 다이제스트.

**Args:**

- sector: 섹터 필터 (예: "반도체"). None이면 전체.
- top_n: 상위 N개.
- format: "dataframe", "markdown", "json".
- stock_codes: 직접 종목코드 목록 지정.
- verbose: 진행 상황 출력.

**Returns:** pl.DataFrame | str — format에 따라 DataFrame 또는 마크다운/JSON 문자열.

```python
import dartlab
dartlab.digest()                          # 전체 시장
dartlab.digest(sector="반도체")             # 섹터별
dartlab.digest(format="markdown")          # 마크다운 출력
```

### `dartlab.scanAccount(snakeId: str, *, market: str = 'dart', sjDiv: str | None = None, fsPref: str = 'CFS', annual: bool = False)`

전종목 단일 계정 시계열.

**Args:**

- snakeId: 계정 식별자. 영문("sales") 또는 한글("매출액") 모두 가능.
- market: "dart" (한국, 기본) 또는 "edgar" (미국).
- sjDiv: 재무제표 구분 ("IS", "BS", "CF"). None이면 자동 결정. (dart만)
- fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선). (dart만)
- annual: True면 연간 (기본 False=분기별 standalone).

**Returns:** pl.DataFrame — 종목코드 × 기간 피벗 테이블.

```python
import dartlab
dartlab.scan("account", "매출액")                      # DART 분기별
dartlab.scan("account", "매출액", annual=True)          # DART 연간
dartlab.scan("account", "sales", market="edgar")        # EDGAR 분기별
dartlab.scan("account", "total_assets", market="edgar", annual=True)
```

### `dartlab.scanRatio(ratioName: str, *, market: str = 'dart', fsPref: str = 'CFS', annual: bool = False)`

전종목 단일 재무비율 시계열.

**Args:**

- ratioName: 비율 식별자 ("roe", "operatingMargin", "debtRatio" 등).
- market: "dart" (한국, 기본) 또는 "edgar" (미국).
- fsPref: 연결/별도 우선순위. (dart만)
- annual: True면 연간 (기본 False=분기별).

**Returns:** pl.DataFrame — 종목코드 × 기간 피벗 테이블.

```python
import dartlab
dartlab.scan("ratio", "roe")                           # DART 분기별
dartlab.scan("ratio", "operatingMargin", annual=True)  # DART 연간
dartlab.scan("ratio", "roe", market="edgar", annual=True)  # EDGAR 연간
```

### `dartlab.plugins()`

로드된 플러그인 목록 반환.

**Args:**

- 없음.

**Returns:** list[PluginMeta] — 로드된 플러그인 목록.

```python
import dartlab
dartlab.plugins()  # [PluginMeta(name="esg-scores", ...)]
```

### `dartlab.reload_plugins()`

플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식.

**Args:**

- 없음.

**Returns:** list[PluginMeta] — 재스캔 후 플러그인 목록.

```python
# 1. 새 플러그인 설치
# !uv pip install dartlab-plugin-esg

# 2. 재스캔
dartlab.reload_plugins()

# 3. 즉시 사용
dartlab.Company("005930").show("esgScore")
```

### `dartlab.verbose`

bool(x) -> bool

### `dartlab.dataDir`

str(object='') -> str

### `dartlab.getKindList(*, forceRefresh: bool = False) -> pl.DataFrame`

KRX KIND 상장법인 전체 목록.

**Args:**

- forceRefresh: True면 캐시 무시하고 KIND API 재요청.

**Returns:** DataFrame (회사명, 종목코드, 업종, 주요제품, 상장일, 결산월, 대표자명, 홈페이지, 지역, ...).

### `dartlab.codeToName(stockCode: str) -> str | None`

종목코드 → 회사명.

### `dartlab.nameToCode(corpName: str) -> str | None`

회사명 → 종목코드. 정확히 일치하는 첫 번째 결과.

### `dartlab.searchName(keyword: str) -> pl.DataFrame`

회사명 부분 검색.

**Args:**

- keyword: 검색 키워드 (예: "삼성", "반도체").

**Returns:** 매칭된 종목 DataFrame (회사명, 종목코드, ...).

### `dartlab.fuzzySearch(keyword: str, *, maxResults: int = 10) -> pl.DataFrame`

한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리.

**Args:**

- keyword: 검색어 (한글, 영문, 초성, 혼합 모두 가능)
- maxResults: 최대 반환 수 (기본 10)

**Returns:** 매칭된 종목 DataFrame (회사명, 종목코드, ...), 관련도 순.

### `dartlab.table(axis: str | None = None, target: Any = None, kwargs: Any) -> pl.DataFrame`

테이블 가공 엔진 -- DataFrame 변환/포맷팅.

**Args:**

- axis: 가공 축. None이면 가이드 반환.
- target: 가공 대상 DataFrame.
- **kwargs: 축별 옵션 (unit, value_cols 등).

**Returns:** pl.DataFrame -- 가공된 데이터. axis=None이면 가이드 DataFrame.

```python
import dartlab
c = dartlab.Company("005930")
dartlab.table()                          # 가이드
dartlab.table("yoy", c.IS)               # YoY 변동률
dartlab.table("format", c.BS, unit="억원") # 한국어 단위
```

### `dartlab.text`

텍스트 분석 도구.

### `dartlab.Review`

분석 리뷰 — 14축 전략분석 결과를 구조화 보고서로 렌더링.

**Args:**

- itemsOrStockCode: Block 리스트 (자유 조립) 또는 종목코드 문자열.
- stockCode: 종목코드.
- corpName: 회사명.
- sections: Section 리스트.
- layout: ReviewLayout 설정.
- aiNote: AI 미설정 시 안내 메시지.
- circulationSummary: 재무제표 순환 서사 요약.

**Returns:** Review 인스턴스. repr/render 호출 시 보고서 텍스트.

```python
import dartlab
c = dartlab.Company("005930")
c.review()                        # 전체 리뷰
c.review("수익구조")               # 수익구조 섹션만

from dartlab.review import blocks, Review, buildReview
b = blocks(c)
b["growth"]                       # 매출 성장률 블록
Review([b["growth"], b["margin"]])  # 자유 조립
```

### `dartlab.SelectResult`

select() 반환 객체 — DataFrame 위임 + 체이닝.

### `dartlab.ChartResult`

chart() 반환 객체 — 시각화 + 렌더링.

### `dartlab.capabilities(key: str | None = None, *, search: str | None = None) -> dict | list[str]`

dartlab 전체 기능 카탈로그 조회.

**Args:**

- key: 조회할 기능 키. None이면 전체 목차.
- search: 자연어 질문 기반 검색. key와 동시 사용 불가.

**Returns:** dict | list[str] — key 있으면 해당 항목 dict, 없으면 키+summary 목록.

```python
dartlab.capabilities()                       # 전체 목차
dartlab.capabilities("analysis")             # analysis 상세 (guide, capabilities)
dartlab.capabilities("Company.analysis")     # Company.analysis 상세
dartlab.capabilities("scan")                 # scan 상세
dartlab.capabilities(search="재무건전성")     # 질문 기반 검색 → 상위 10개
```

---

## Company

### `Company.BS` (property)

재무상태표 (Balance Sheet) — 계정명 × 기간 DataFrame.

```python
c = Company("005930")
c.BS  # 재무상태표
```

### `Company.CF` (property)

현금흐름표 (Cash Flow Statement) — 계정명 × 기간 DataFrame.

```python
c = Company("005930")
c.CF  # 현금흐름표
```

### `Company.CIS` (property)

포괄손익계산서 (Comprehensive Income Statement) — 계정명 × 기간 DataFrame.

```python
c = Company("005930")
c.CIS  # 포괄손익계산서
```

### `Company.IS` (property)

손익계산서 (Income Statement) — 계정명 × 기간 DataFrame.

```python
c = Company("005930")
c.IS  # 손익계산서
```

### `Company.SCE` (property)

자본변동표 (Statement of Changes in Equity) — 계정명 × 연도 DataFrame.

```python
c = Company("005930")
c.SCE  # 자본변동표
```

### `analysis(axis: str | None = None, kwargs)`

재무제표 완전 분석 — 14축, 단일 종목 심층.

**Args:**

- axis: 분석 축 이름. None이면 14축 가이드 반환.
- **kwargs: 축별 추가 옵션.

```python
c = Company("005930")
c.analysis()              # 14축 가이드
c.analysis("수익구조")     # 수익구조 분석
```

### `Company.annual` (property)

연도별 시계열 (연결 기준).

```python
c = Company("005930")
series, years = c.annual
series["IS"]["sales"]  # 연도별 매출 시계열
```

### `ask(question: str, *, include: list[str] | None = None, exclude: list[str] | None = None, provider: str | None = None, model: str | None = None, stream: bool = False, reflect: bool = False, kwargs) -> str`

LLM에게 이 기업에 대해 질문.

**Args:**

- question: 질문 텍스트.
- include: 포함할 분석 패키지 목록. None이면 자동 선택.
- exclude: 제외할 분석 패키지 목록.
- provider: LLM provider 이름 (openai, ollama, codex 등). None이면 기본값.
- model: 모델명. None이면 provider 기본값.
- stream: True면 스트리밍 제너레이터 반환.
- reflect: True면 답변 후 자기 평가 수행.
- **kwargs: provider별 추가 옵션.

```python
c = Company("005930")
c.ask("영업이익률 추세는?")
c.ask("핵심 리스크 3가지", provider="codex")

# 스트리밍
for chunk in c.ask("배당 분석해줘", stream=True):
print(chunk, end="")
```

### `audit()`

감사 리스크 종합 분석.

**Args:**

- 없음 (self 바인딩).

```python
c = Company("005930")
c.audit()
```

### `canHandle(code: str) -> bool`

DART 종목코드(6자) 또는 한글 회사명이면 처리 가능.

### `capital(view: str | None = None) -> pl.DataFrame | None`

주주환원 분석 (배당, 자사주, 총환원율).

**Args:**

- view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

```python
c = Company("005930")
c.capital()              # 삼성전자 주주환원
c.capital("all")         # 전체 상장사
```

### `chat(question: str, *, provider: str | None = None, model: str | None = None, max_turns: int = 5, on_tool_call = None, on_tool_result = None, kwargs) -> str`

에이전트 모드: LLM이 도구를 선택하여 심화 분석.

**Args:**

- question: 질문 텍스트.
- provider: LLM provider 이름. None이면 기본값.
- model: 모델명. None이면 provider 기본값.
- max_turns: 최대 tool calling 턴 수. 기본 5.
- on_tool_call: tool 호출 시 콜백.
- on_tool_result: tool 결과 수신 시 콜백.
- **kwargs: provider별 추가 옵션.

```python
c = Company("005930")
c.chat("배당 추세를 분석하고 이상 징후를 찾아줘")
```

### `codeName(stockCode: str) -> str | None`

종목코드 → 회사명 변환.

**Args:**

- stockCode: 6자리 종목코드.

### `Company.contextSlices` (property)

LLM 투입용 context slice DataFrame.

```python
c = Company("005930")
c.contextSlices            # LLM용 context 슬라이스
```

### `Company.cumulative` (property)

분기별 누적 시계열 (연결 기준).

```python
c = Company("005930")
series, periods = c.cumulative
```

### `Company.currency` (property)

통화 코드 (DART 제공자는 항상 KRW).

```python
c = Company("005930")
c.currency  # "KRW"
```

### `debt(view: str | None = None) -> pl.DataFrame | None`

부채 구조 분석 (차입금, 부채비율, 만기 구조).

**Args:**

- view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

```python
c = Company("005930")
c.debt()                 # 삼성전자 부채 구조
c.debt("all")            # 전체 상장사
```

### `diff(topic: str | None = None, fromPeriod: str | None = None, toPeriod: str | None = None) -> pl.DataFrame | None`

기간간 텍스트 변경 비교.

**Args:**

- topic: topic 이름. None이면 전체 변경 요약.
- fromPeriod: 비교 시작 기간 ("2023").
- toPeriod: 비교 끝 기간 ("2024").

```python
c.diff()                                    # 전체 변경 요약
c.diff("businessOverview")                  # 사업개요 변경 이력
c.diff("businessOverview", "2023", "2024")  # 줄 단위 diff
```

### `disclosure(start: str | None = None, end: str | None = None, *, days: int = 365, type: str | None = None, keyword: str | None = None, finalOnly: bool = False) -> pl.DataFrame`

OpenDART 전체 공시 목록 조회.

**Args:**

- start: 조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD). None이면 최근 days일.
- end: 조회 종료일. None이면 오늘.
- days: start/end 없을 때 최근 일수. 기본 365.
- type: 공시유형 필터 (A=정기, B=주요사항, C=발행, D=지분, E=기타, F=외부감사). None이면 전체.
- keyword: 제목/회사명 키워드 필터.
- finalOnly: True면 최종보고서만 (정정 이전 제외).

```python
c = Company("005930")
c.disclosure()                  # 최근 1년 전체 공시
c.disclosure(days=30)           # 최근 30일
c.disclosure(type="A")          # 정기공시만
c.disclosure(keyword="사업보고서")
```

### `filings() -> pl.DataFrame | None`

공시 문서 목록 + DART 뷰어 링크.

### `forecast(*, horizon: int = 3)`

매출 앙상블 예측 (다중 모델 가중 평균).

**Args:**

- horizon: 예측 기간 (연 단위, 기본 3년).

```python
c = Company("005930")
c.forecast()
c.forecast(horizon=5)
```

### `gather(axis: str | None = None, kwargs)`

외부 시장 데이터 수집 — 4축 (price/flow/macro/news).

**Args:**

- axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
- **kwargs: market, start, end, days 등 축별 옵션.

```python
c = Company("005930")
c.gather()                 # 4축 가이드
c.gather("price")          # 주가 시계열
c.gather("news")           # 뉴스
```

### `getRatios(fsDivPref: str = 'CFS')`

Deprecated — use ``c.ratios`` property instead.

### `getTimeseries(period: str = 'q', fsDivPref: str = 'CFS')`

Deprecated — use ``c.timeseries`` property instead.

**Args:**

- period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
- fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

### `governance(view: str | None = None) -> pl.DataFrame | None`

지배구조 분석 (이사회, 감사위원, 최대주주).

**Args:**

- view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

```python
c = Company("005930")
c.governance()           # 삼성전자 거버넌스
c.governance("all")      # 전체 상장사
```

### `Company.index` (property)

현재 공개 Company 구조 인덱스 DataFrame -- 전체 데이터 목차.

```python
c = Company("005930")
c.index                    # 전체 구조 목차
c.index.filter(pl.col("source") == "docs")  # docs 항목만
```

### `Company.insights` (property)

종합 인사이트 분석 (7영역 등급 + 이상치 + 요약).

```python
c = Company("005930")
c.insights.grades()       # {'performance': 'A', ...}
c.insights.summary        # "삼성전자는 실적, 재무건전성 등..."
c.insights.anomalies      # [Anomaly(...), ...]
c.insights.profile        # "premium"
```

### `keywordTrend(keyword: str | None = None, keywords: list[str] | None = None) -> pl.DataFrame | None`

공시 텍스트 키워드 빈도 추이 (topic x period x keyword).

**Args:**

- keyword: 단일 키워드. None이면 내장 키워드 전체.
- keywords: 복수 키워드 리스트.

```python
c.keywordTrend("AI")
c.keywordTrend(keywords=["AI", "ESG"])
c.keywordTrend()                  # 54개 내장 키워드 전체
```

### `listing(*, forceRefresh: bool = False) -> pl.DataFrame`

KRX 전체 상장법인 목록 (KIND 기준).

**Args:**

- forceRefresh: True면 캐시 무시, KIND에서 재다운로드.

### `liveFilings(start: str | None = None, end: str | None = None, *, days: int | None = None, limit: int = 20, keyword: str | None = None, forms: list[str] | tuple[str, ...] | None = None, finalOnly: bool = False) -> pl.DataFrame`

OpenDART 기준 실시간 공시 목록 조회.

**Args:**

- start: 조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD). None이면 최근 days일.
- end: 조회 종료일. None이면 오늘.
- days: start/end 없을 때 최근 일수. None이면 기본값 적용.
- limit: 최대 반환 건수. 기본 20.
- keyword: 제목/회사명 키워드 필터.
- forms: 미사용 (DART는 forms 개념 없음).
- finalOnly: True면 최종보고서만 (정정 이전 제외).

```python
c = Company("005930")
c.liveFilings()                 # 최근 공시 20건
c.liveFilings(days=7)           # 최근 7일
c.liveFilings(keyword="배당")   # 키워드 필터
```

### `Company.market` (property)

시장 코드 (DART 제공자는 항상 KR).

```python
c = Company("005930")
c.market  # "KR"
```

### `network(view: str | None = None, *, hops: int = 1)`

관계 네트워크 (지분출자 + 그룹 계열사 지도).

**Args:**

- view: None이면 시각화(NetworkView), "members"/"edges"/"cycles"/"peers"이면 DataFrame.
- hops: peers/시각화 뷰에서 홉 수.

```python
c = Company("005930")
c.network()              # → NetworkView (.show()로 브라우저)
c.network().show()       # 브라우저 오픈
c.network("members")     # 같은 그룹 계열사 DataFrame
c.network("edges")       # 출자/지분 연결 DataFrame
c.network("cycles")      # 순환출자 경로 DataFrame
c.network("peers")       # 이 회사 중심 서브그래프 DataFrame
```

### `news(*, days: int = 30) -> pl.DataFrame`

최근 뉴스 수집.

**Args:**

- days: 최근 N일. 기본 30.

```python
c.news()           # 최근 30일
c.news(days=7)     # 최근 7일
```

### `Company.notes` (property)

K-IFRS 주석사항 접근자.

```python
c = Company("005930")
c.notes                # 주석사항 접근자
```

### `priority() -> int`

낮을수록 먼저 시도. DART=10 (기본 provider).

### `Company.profile` (property)

docs spine + finance/report merge layer -- 통합 프로필 접근자.

```python
c = Company("005930")
c.profile.sections         # 통합 sections
c.profile.show("BS")       # merge된 재무상태표
```

### `Company.rank` (property)

전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률).

```python
from dartlab.analysis.financial.insight import buildSnapshot
buildSnapshot()

c = Company("005930")
c.rank                    # RankInfo(삼성전자, 매출 2/2192, 섹터 2/467, large)
c.rank.revenueRank        # 2
c.rank.revenueRankInSector # 2
c.rank.sizeClass          # "large"
```

### `Company.ratioSeries` (property)

재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조).

```python
c = Company("005930")
series, years = c.ratioSeries
series["RATIO"]["roe"]  # [8.69, 13.20, 16.55, ...]
```

### `Company.ratios` (property)

재무비율 시계열 (분류/항목 x 기간 DataFrame).

```python
c = Company("005930")
c.ratios  # 분류 | 항목 | 2025Q3 | 2025Q2 | ...
```

### `Company.rawDocs` (property)

공시 문서 원본 parquet 전체 (가공 전).

```python
c = Company("005930")
c.rawDocs              # 삼성전자 공시 문서 원본
c.rawDocs.columns      # 컬럼 목록 확인
```

### `Company.rawFinance` (property)

재무제표 원본 parquet 전체 (가공 전).

```python
c = Company("005930")
c.rawFinance           # 삼성전자 재무제표 원본
c.rawFinance.columns   # 컬럼 목록 확인
```

### `Company.rawReport` (property)

정기보고서 원본 parquet 전체 (가공 전).

```python
c = Company("005930")
c.rawReport            # 삼성전자 정기보고서 원본
c.rawReport.columns    # 컬럼 목록 확인
```

### `readFiling(filing: Any, *, maxChars: int | None = None, sections: bool = False) -> dict[str, Any]`

접수번호 또는 liveFilings row로 공시 원문을 읽는다.

**Args:**

- filing: 접수번호(str) 또는 disclosure()/liveFilings() row.
- maxChars: 텍스트 최대 길이 (sections=False일 때만 적용).
- sections: True면 ZIP 기반 구조화된 섹션 목록 반환.

```python
c = Company("005930")
result = c.readFiling("20240315000123")
result = c.readFiling("20240315000123", sections=True)
```

### `research(*, sections: list[str] | None = None, includeMarket: bool = True)`

종합 기업분석 리포트 (재무 + 시장 + 공시 통합).

**Args:**

- sections: 포함할 섹션 리스트 (None이면 전체).
- includeMarket: 시장 데이터 포함 여부 (기본 True).

```python
c = Company("005930")
c.research()
c.research(sections=["financial", "risk"])
```

### `resolve(codeOrName: str) -> str | None`

종목코드 또는 회사명 → 종목코드 변환.

**Args:**

- codeOrName: 종목코드 ("005930") 또는 종목명 ("삼성전자").

### `Company.retrievalBlocks` (property)

원문 markdown 보존 retrieval block DataFrame.

```python
c = Company("005930")
c.retrievalBlocks          # 전체 retrieval 블록
```

### `review(section: str | None = None, layout = None, helper: bool | None = None)`

재무제표 구조화 보고서 — 14개 섹션 데이터 검토서.

**Args:**

- section: 섹션명 ("수익구조" 등). None이면 전체.
- layout: ReviewLayout 커스텀. None이면 기본.
- helper: True면 해석 힌트 텍스트 포함. None이면 자동.

```python
c.review()                        # 전체 검토서
c.review("수익구조")                # 특정 섹션
```

### `reviewer(section: str | None = None, layout = None, helper: bool | None = None, guide: str | None = None)`

AI 분석 보고서 — review() + 섹션별 AI 종합의견.

**Args:**

- section: 섹션명. None이면 전체.
- layout: ReviewLayout 커스텀.
- helper: True면 해석 힌트 포함.
- guide: AI에게 전달할 분석 관점 ("반도체 사이클 관점에서 평가해줘").

```python
c.reviewer()
c.reviewer("수익구조")
c.reviewer(guide="반도체 사이클 관점에서 평가해줘")
```

### `Company.sce` (property)

자본변동표 DataFrame (연결 기준).

### `Company.sceMatrix` (property)

자본변동표 연도별 매트릭스 (연결 기준).

```python
c = Company("005930")
matrix, years = c.sceMatrix
matrix["2024"]["net_income"]["retained_earnings"]
```

### `search(keyword: str) -> pl.DataFrame`

회사명 부분 검색 (KIND 목록 기준).

**Args:**

- keyword: 검색어 (부분 일치).

### `Company.sections` (property)

sections — docs + finance + report 통합 지도.

```python
c = Company("005930")
c.sections  # 전체 sections 지도
```

### `Company.sector` (property)

WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반).

```python
c = Company("005930")
c.sector              # SectorInfo(IT/반도체와반도체장비, conf=1.00, src=override)
c.sector.sector       # Sector.IT
c.sector.industryGroup  # IndustryGroup.SEMICONDUCTOR
```

### `Company.sectorParams` (property)

현재 종목의 섹터별 밸류에이션 파라미터.

```python
c = Company("005930")
c.sectorParams.perMultiple   # 15
c.sectorParams.discountRate  # 13.0
```

### `select(topic: str, indList: str | list[str] | None = None, colList: str | list[str] | None = None)`

show() 결과에서 행(indList) + 열(colList) 필터.

**Args:**

- topic: IS, BS, CF, CIS, SCE 또는 docs topic.
- indList: 행 필터. 한글 계정명/snakeId/항목명. 단일 str도 가능.
- colList: 열(기간) 필터. 단일 str도 가능.

```python
c.select("IS", ["매출액", "영업이익"])
c.select("IS", ["매출액"]).chart()
c.select("BS", ["자본총계"], ["2024", "2023"])
```

### `show(topic: str, block: int | None = None, *, period: str | list[str] | None = None, raw: bool = False) -> pl.DataFrame | None`

topic의 데이터를 반환.

**Args:**

- topic: topic 이름 (BS, IS, CF, dividend, companyOverview 등). c.topics로 전체 목록.
- block: blockOrder 인덱스. None이면 블록 목차 (블록 1개면 바로 데이터).
- period: 특정 기간 필터 ("2023", "2024Q2"). 리스트면 세로 뷰 (기간 × 항목).
- raw: True면 원본 그대로 (정제 없이).

```python
c = dartlab.Company("005930")
c.show("BS")                   # 재무상태표
c.show("IS", period="2023")    # 2023년 손익계산서
c.show("dividend")             # 배당
c.show("IS", period=["2022", "2023"])  # 세로 비교
```

### `simulation(*, scenarios: list[str] | None = None)`

경제 시나리오 시뮬레이션 (거시경제 충격 → 재무 영향).

**Args:**

- scenarios: 시뮬레이션할 시나리오 이름 리스트 (None이면 전체).

```python
c = Company("005930")
c.simulation()
c.simulation(scenarios=["금리인상", "경기침체"])
```

### `Company.sources` (property)

docs/finance/report 3개 source의 가용 현황 요약.

```python
c = Company("005930")
c.sources                  # 3행 DataFrame
```

### `status() -> pl.DataFrame`

로컬에 보유한 전체 종목 인덱스.

### `table(topic: str, subtopic: str | None = None, *, numeric: bool = False, period: str | None = None) -> Any`

subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱.

**Args:**

- topic: docs topic 이름
- subtopic: 파싱할 subtopic 이름 (None이면 첫 번째 subtopic)
- numeric: True이면 금액 문자열을 float로 변환
- period: 기간 필터 (예: "2024")

```python
c.table("employee")                    # 첫 번째 subtopic
c.table("employee", "직원현황")         # 특정 subtopic
c.table("employee", numeric=True)       # 숫자 변환
```

### `Company.timeseries` (property)

분기별 standalone 시계열 (연결 기준).

```python
c = Company("005930")
series, periods = c.timeseries
series["IS"]["sales"]  # 분기별 매출 시계열
```

### `Company.topics` (property)

topic별 요약 DataFrame -- 전체 데이터 지도.

```python
c = Company("005930")
c.topics                   # 전체 topic 요약
c.topics.filter(pl.col("source") == "finance")  # finance만
```

### `trace(topic: str, period: str | None = None) -> dict[str, Any] | None`

topic 데이터의 출처(docs/finance/report)와 선택 근거 추적.

**Args:**

- topic: topic 이름.
- period: 특정 기간. None이면 전체.

```python
c.trace("BS")           # 재무상태표 출처
c.trace("dividend")     # 배당 데이터 출처
```

### `update(*, categories: list[str] | None = None) -> dict[str, int]`

누락된 최신 공시를 증분 수집.

**Args:**

- categories: ["finance", "docs", "report"]. None이면 전체.

### `valuation(*, shares: int | None = None)`

종합 밸류에이션 (DCF + DDM + 상대가치).

**Args:**

- shares: 발행주식수 (None이면 profile에서 자동 조회).

```python
c = Company("005930")
c.valuation()
c.valuation(shares=5_969_782_550)
```

### `view(*, port: int = 8400) -> None`

브라우저에서 공시 뷰어를 엽니다.

**Args:**

- port: 로컬 서버 포트. 기본 8400.

```python
c = Company("005930")
c.view()
```

### `watch(topic: str | None = None) -> pl.DataFrame | None`

공시 변화 감지 — 중요도 스코어링 기반 변화 요약.

**Args:**

- topic: topic 이름. None이면 전체 중요도 순 요약.

```python
c.watch()                    # 전체 중요도 순
c.watch("riskManagement")    # 특정 topic
```

### `workforce(view: str | None = None) -> pl.DataFrame | None`

인력/급여 분석 (직원수, 평균급여, 근속연수).

**Args:**

- view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

```python
c = Company("005930")
c.workforce()            # 삼성전자 인력 현황
c.workforce("all")       # 전체 상장사
```
