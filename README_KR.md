<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>DART 전자공시 + EDGAR에서 하나의 회사 맵을 만든다</b></p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-120%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> · <a href="https://eddmpython.github.io/dartlab/blog/">블로그</a> · <a href="notebooks/marimo/">Marimo 노트북</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb">Colab에서 열기</a> · <a href="README.md">English</a> · <a href="https://buymeacoffee.com/eddmpython">후원</a>
</p>

<p>
<a href="https://huggingface.co/datasets/eddmpython/dartlab-data"><img src="https://img.shields.io/badge/Data-HuggingFace-ffd21e?style=for-the-badge&labelColor=050811&logo=huggingface&logoColor=white" alt="HuggingFace Data"></a>
</p>

</div>

> **참고:** DartLab은 활발히 개발 중이다. 버전 간 API가 바뀔 수 있으며, 문서가 최신 코드를 따라가지 못하는 경우가 있다.

## 설치

**Python 3.12+** 필요.

```bash
# 코어 — 재무제표, sections, Company
uv add dartlab

# pip으로 설치
pip install dartlab
```

### 선택적 확장

필요한 것만 설치한다:

```bash
uv add "dartlab[ai]"              # 웹 UI, 서버, 스트리밍 (FastAPI + uvicorn)
uv add "dartlab[llm]"             # LLM 분석 (OpenAI)
uv add "dartlab[charts]"          # Plotly 차트, 네트워크 그래프 (plotly + networkx + scipy)
uv add "dartlab[event]"           # 이벤트 스터디, 주가 데이터 (yfinance)
uv add "dartlab[mcp]"             # Claude Desktop / Code / Cursor용 MCP 서버
uv add "dartlab[channel]"         # 웹 UI + cloudflared 터널 공유
uv add "dartlab[channel-ngrok]"   # 웹 UI + ngrok 터널 공유
uv add "dartlab[channel-full]"    # 전체 채널 + Telegram / Slack / Discord 봇
uv add "dartlab[all]"             # 위 전부 (channel 봇 제외)
```

**자주 쓰는 조합:**

```bash
# 재무 분석 + AI 채팅
uv add "dartlab[ai,llm]"

# 전체 분석 — 차트, AI, LLM
uv add "dartlab[ai,llm,charts]"

# 팀과 분석 공유 (터널)
uv add "dartlab[channel]"
```

### 소스에서 설치

```bash
git clone https://github.com/eddmpython/dartlab.git
cd dartlab && uv pip install -e ".[all]"

# pip으로 설치
pip install -e ".[all]"
```

PyPI 배포는 코어가 안정적일 때만 한다. 최신 기능(감사, 예측, 밸류에이션 등 실험적 기능 포함)을 바로 쓰고 싶다면 git clone을 권장하지만, 간헐적 breaking change에 주의해야 한다.

### 데스크톱 앱 (Alpha)

설치 과정 없이 바로 실행할 수 있는 Windows 런처:

- **[DartLab.exe 다운로드](https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe)** — [dartlab-desktop](https://github.com/eddmpython/dartlab-desktop) 릴리즈
- [DartLab 랜딩 페이지](https://eddmpython.github.io/dartlab/)에서도 다운로드 가능

원클릭 실행 — Python, 터미널, 패키지 관리자 모두 불필요. 웹 UI와 내장 Python 런타임이 번들되어 있다.

> **Alpha** — 동작하지만 불완전. Windows 전용 `.exe` 런처. macOS/Linux는 아직 미지원.

---

**설정 불필요.** `Company`를 생성하면 필요한 데이터를 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동으로 다운로드한다. EDGAR 데이터는 SEC API에서 가져온다. 두 번째 실행부터는 로컬 캐시로 즉시 로드된다.

## 빠른 시작

```python
import dartlab

c = dartlab.Company("005930")   # 삼성전자 (DART)
c.sections                      # 전체 회사 맵 (topic × period)
c.show("overview")              # topic 하나 열기
c.BS                            # 재무상태표
c.ratios                        # 재무비율 시계열
c.insights                      # 7영역 등급 (A~F)
c.filings()                     # 공시 문서 목록

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("business")
us.BS
us.ratios

# 코드 없이 자연어로 질문
dartlab.ask("삼성전자 재무건전성 분석해줘")
```

## DartLab은 무엇인가

DartLab은 사업보고서의 **숫자**(재무제표)와 **텍스트**(사업 개요, 리스크, 감사보고서)를 모두 분석하는 Python 라이브러리다. 한국(DART), 미국(EDGAR)을 지원하고, 일본(EDINET)은 연구 중이다.

모든 회사는 다른 방식으로 공시한다. 같은 "매출액"이 `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`로 표기되고, 한글명도 "매출", "수익", "영업수익", "매출액합계" 등 수십 가지 변형이 있다. 섹션 제목도 회사, 연도, 업종마다 다르다. 두 회사를 수작업으로 비교하려면 몇 시간의 재정렬이 필요하다.

DartLab은 두 가지 표준화 엔진으로 이 문제를 해결한다.

### 계정 표준화

재무제표는 XBRL을 쓰지만, 계정 ID는 회사마다 다르다. DartLab은 4단계 파이프라인으로 이를 정규화한다:

```
원본 XBRL account_id
  → 1단계: 접두사 제거 (ifrs-full_, dart_, ifrs_, ifrs-smes_)
  → 2단계: 영문 ID 동의어 (59개 규칙)
           예) NetIncome, Profit, NetProfit → ProfitLoss
  → 3단계: 한글명 동의어 (104개 규칙)
           예) 매출, 수익, 영업수익, 매출액합계 → 매출액
  → 4단계: 학습된 매핑 테이블 (34,249개 엔트리)
           AccountMapper가 표준 snakeId로 변환
  → 결과: revenue, operatingIncome, totalAssets, …
```

실제로 세 회사의 같은 "매출액" 계정이 원본에서 어떻게 다른지:

```
Before (원본 XBRL):                        After (표준화):
회사        account_id          account_nm   →  snakeId    label
삼성전자    ifrs-full_Revenue   수익(매출액)  →  revenue    매출액
SK하이닉스  dart_Revenue        매출액       →  revenue    매출액
LG에너지    Revenue             매출         →  revenue    매출액
```

모든 회사의 모든 계정이 동일한 `snakeId`로 수렴한다. 회사 간 비교가 수작업 없이 가능하다.

매핑 테이블은 전체 상장사의 ~97%를 커버한다. 나머지 예외(신규 XBRL 분류체계, 비표준 공시)는 원본 ID를 보존한 채 그대로 통과한다.

### 섹션 수평화

사업보고서에는 구조화된 섹션(사업 개요, 리스크, 배당 정책 등)이 있지만, 섹션 제목이 회사·연도·업종마다 다르다. DartLab은 모든 섹션을 **topic × period** 격자로 정규화한다:

```
                    2025Q4    2024Q4    2024Q3    2023Q4    …
companyOverview       ✓         ✓         ✓         ✓
businessOverview      ✓         ✓         ✓         ✓
productService        ✓         ✓         ✓         ✓
salesOrder            ✓         ✓         —         ✓
employee              ✓         ✓         ✓         ✓
dividend              ✓         ✓         ✓         ✓
audit                 ✓         ✓         ✓         ✓
…                    (98개 canonical topics)
```

같은 내용의 섹션이 회사마다 다른 제목으로 등장한다:

```
Before (원본 섹션 제목):                     After (canonical topic):
삼성전자    "II. 사업의 내용"                → businessOverview
현대차      "II. 사업의 내용 [자동차부문]"    → businessOverview
카카오      "2. 사업의 내용"                 → businessOverview
```

매핑 파이프라인: **텍스트 정규화**(업종 접두사, 번호, 구두점 제거) → **545개 하드코딩 매핑** → **73개 regex 패턴** → canonical topic 할당. 전체 상장사 대비 ~95%+ 매핑률을 달성한다.

격자의 각 셀에는 heading/body로 분리된 원문, 테이블, 증거가 들어 있다. "작년 대비 올해 리스크 기술이 어떻게 바뀌었는지"를 `diff()` 한 줄로 비교할 수 있다.

### Company — 통합된 회사 맵

`Company`는 모든 것이 합쳐지는 지점이다. `sections`(docs에서 온 텍스트 구조)를 spine으로 두고, 그 위에 더 강한 데이터 소스를 올린다:

```
레이어        제공하는 것                       우선순위
─────────────────────────────────────────────────────────
docs          섹션 텍스트, 테이블, 증거           기본 spine
finance       BS, IS, CF, 비율, 시계열           숫자 topic 대체
report        28개 정형 API (DART 전용)          정형 topic 채움
─────────────────────────────────────────────────────────
profile       통합 뷰 (사용자 기본값)             최상위
```

- **`docs`**는 서술 텍스트를 담당한다 — 사업 개요, 리스크, 감사 의견
- **`finance`**는 숫자가 더 강한 곳을 대체한다 — BS, IS, CF가 authoritative DataFrame이 된다
- **`report`**는 DART 전용 정형 데이터를 채운다 — 배당 정책, 임원 보수, 지배구조 상세

네 가지 namespace로 다른 관점을 제공한다:

```python
c.docs.sections     # 순수 텍스트 소스 (sections spine)
c.finance.BS        # authoritative 재무제표
c.report.extract()  # 정형 DART API 데이터
c.profile.sections  # 통합 뷰 — 사용자가 보는 기본값
```

`c.sections`는 통합 뷰다. `c.trace("BS")`로 어떤 소스가 왜 채택됐는지 확인한다.

### 핵심 원칙

1. **Sections First** — 회사는 여러 parser 결과의 모음이 아니라, 기간축 위에 정렬된 하나의 공시 맵이다
2. **Source-Aware** — `finance`나 `report`가 더 authoritative하면 자동으로 대체한다. `trace()`로 어떤 source가 채택됐는지 확인
3. **텍스트 + 숫자** — 서술 텍스트(heading/body + 메타데이터)와 재무 숫자(표준화된 계정)가 같은 구조에 공존한다
4. **Raw Access** — 더 깊게: `c.docs.sections`, `c.finance.BS`, `c.report.extract("배당")`

## 기능

### Show, Trace, Diff

```python
c = dartlab.Company("005930")

# show — source 우선순위에 따라 topic을 연다
c.show("BS")                # → finance DataFrame
c.show("overview")          # → sections 기반 텍스트 + 테이블
c.show("dividend")          # → report DataFrame (전 분기)
c.show("IS", period=["2024Q4", "2023Q4"])  # 특정 기간 비교

# trace — docs/finance/report 중 어떤 source가 채택됐는지
c.trace("BS")               # → {"primarySource": "finance", ...}

# diff — 기간 간 텍스트 변화 감지 (3가지 모드)
c.diff()                                    # 전체 요약
c.diff("businessOverview")                  # topic 이력
c.diff("businessOverview", "2024", "2025")  # 줄 단위 diff
```

실제 출력 예시:

```
>>> c.show("businessOverview")
shape: (12, 5)
┌───────────┬──────────┬──────────────────────────────┬──────────────────────────────┐
│ blockType │ nodeType │ 2024                         │ 2023                         │
├───────────┼──────────┼──────────────────────────────┼──────────────────────────────┤
│ text      │ heading  │ 1. 산업의 특성                │ 1. 산업의 특성                │
│ text      │ body     │ 반도체 산업은 기술 집약적 …   │ 반도체 산업은 기술 집약적 …    │
│ table     │ null     │ DataFrame(5×3)               │ DataFrame(5×3)               │
└───────────┴──────────┴──────────────────────────────┴──────────────────────────────┘

>>> c.diff("businessOverview", "2023", "2024")
┌──────────┬─────────────────────────────────────────────┐
│ status   │ text                                        │
├──────────┼─────────────────────────────────────────────┤
│ added    │ AI 반도체 수요 급증에 따른 HBM 매출 확대 …   │
│ modified │ 매출액 258.9조원 → 300.9조원                 │
│ removed  │ 반도체 부문 수익성 악화 우려 …               │
└──────────┴─────────────────────────────────────────────┘
```

### 재무제표와 재무비율

```python
c.BS                    # 재무상태표 (계정 × period, 최신 먼저)
c.IS                    # 손익계산서
c.CF                    # 현금흐름표
c.ratios                # 재무비율 시계열 DataFrame (6개 카테고리 × period)
c.finance.ratioSeries   # 비율 시계열 across years
c.finance.timeseries    # 원본 계정 시계열
c.annual                # 연간 시계열
c.filings()             # 공시 문서 목록 (Tier 1 Stable)
```

모든 계정은 4단계 표준화 파이프라인을 거친다 — 삼성전자의 `revenue`와 LG의 `revenue`는 같은 `snakeId`다. 재무비율은 6개 카테고리를 포괄한다: 수익성, 안정성, 성장성, 효율성, 현금흐름, 밸류에이션.

### 인사이트 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
c.insights                      # 7영역 분석
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["매출 고성장 +8.3%", …]
c.insights.anomalies            # → 이상치, 위험 신호

# 부도·부정 예측 스코어카드 — 6개 모델
c.insights.distress             # Altman Z-Score, Beneish M-Score, Ohlson O-Score,
                                # Merton Distance-to-Default, Piotroski F-Score, Sloan Ratio
```

### 밸류에이션, 예측 & 시뮬레이션

```python
dartlab.valuation("005930")           # DCF + DDM + 상대가치 밸류에이션
dartlab.forecast("005930")            # 매출 예측 (4소스 앙상블)
dartlab.simulation("005930")          # 시나리오 시뮬레이션 (매크로 프리셋)

# Company 메서드로도 사용 가능
c.valuation()
c.forecast(horizon=3)
c.simulation(scenarios=["adverse", "rate_hike"])
```

통화 자동 감지 — DART 기업은 KRW, EDGAR 기업은 USD.

### 감사 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
dartlab.audit("005930")               # 11개 감사 Red Flag 탐지기

# Benford's Law (숫자 분포), 감사인 교체 (PCAOB AS 3101),
# 계속기업 (ISA 570), 내부통제 (SOX 302/404),
# 수익의 질 (Dechow & Dichev), Merton 부도확률, ...
```

### 시장 인텔리전스 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
dartlab.digest()                      # 시장 전체 공시 변화 다이제스트
dartlab.digest(sector="반도체")        # 섹터 필터
dartlab.groupHealth()                 # 그룹 건전성: 네트워크 × 재무비율
```

### 모듈

DartLab은 6개 카테고리에 걸쳐 100개 이상의 모듈을 제공한다:

```bash
dartlab modules                      # 전체 모듈 목록
dartlab modules --category finance   # 카테고리 필터
dartlab modules --search dividend    # 키워드 검색
```

```python
c.topics    # 이 회사에서 사용 가능한 전체 topic 목록
```

카테고리: `finance` (재무제표, 비율), `report` (배당, 지배구조, 감사), `notes` (K-IFRS 주석), `disclosure` (서술형 텍스트), `analysis` (인사이트, 순위), `raw` (원본 parquet).

### 차트 & 시각화 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
c = dartlab.Company("005930")

# 한 줄 Plotly 차트
dartlab.chart.revenue(c).show()          # 매출 + 영업이익률 콤보
dartlab.chart.cashflow(c).show()         # 영업/투자/재무 CF
dartlab.chart.dividend(c).show()         # DPS + 배당수익률 + 배당성향
dartlab.chart.profitability(c).show()    # ROE, 영업이익률, 순이익률

# 자동 감지 — 사용 가능한 모든 차트 스펙
specs = dartlab.chart.auto_chart(c)
dartlab.chart.chart_from_spec(specs[0]).show()

# 범용 차트 (아무 DataFrame 가능)
dartlab.chart.line(c.dividend, y=["dps"])
dartlab.chart.bar(df, x="year", y=["revenue", "operating_income"], stacked=True)
```

데이터 가공 + 텍스트 분석 도구:

```python
dartlab.table.yoy_change(c.dividend, value_cols=["dps"])       # YoY% 컬럼 추가
dartlab.table.format_korean(c.BS, unit="백만원")                # 1.2조원, 350억원
dartlab.table.summary_stats(c.dividend, value_cols=["dps"])     # mean/CAGR/trend
dartlab.text.extract_keywords(narrative)                        # 빈도 기반 키워드
dartlab.text.sentiment_indicators(narrative)                     # 긍정/부정/리스크
```

차트 의존성 설치: `uv add "dartlab[charts]"`

### 관계 네트워크 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
c = dartlab.Company("005930")

# 브라우저에서 인터랙티브 관계도
c.network().show()           # ego 뷰 (1홉)
c.network(hops=2).show()     # 2홉 이웃

# DataFrame 뷰
c.network("members")     # 같은 그룹 계열사
c.network("edges")       # 출자/지분 연결
c.network("cycles")      # 순환출자 경로

# 전체 시장 네트워크
dartlab.network().show()
```

### 시장 전수 스캔 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
c = dartlab.Company("005930")

# 개별 회사 → 시장 전체
c.governance()           # 개별 회사
c.governance("all")      # 전체 상장사 DataFrame
dartlab.governance()     # 모듈 레벨 스캔
dartlab.workforce()
dartlab.capital()
dartlab.debt()

# 스크리닝 & 벤치마크
dartlab.screen()         # 멀티팩터 스크리닝
dartlab.benchmark()      # 동종업체 비교
dartlab.signal()         # 공시 변화 감지 시그널
```

### 시장 데이터 수집 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

Gather 엔진은 모든 시장 데이터를 **Polars DataFrame 시계열**로 반환한다. 모든 요청은 자동 fallback 체인, circuit breaker 격리, TTL 캐시를 거친다. 동기 시그니처 — 내부적으로 async 병렬 실행.

```python
import dartlab

# OHLCV 시계열 — 수정주가, 1회 요청으로 6000거래일+
dartlab.price("005930")                         # KR: 기본 1년, Polars DataFrame
dartlab.price("005930", start="2015-01-01")     # 기간 지정
dartlab.price("AAPL", market="US")              # US: Yahoo Finance chart API
dartlab.price("005930", snapshot=True)          # opt-in: 현재가 스냅샷

# 수급 시계열 (KR 전용)
dartlab.flow("005930")                          # DataFrame (date, foreignNet, institutionNet, ...)

# 거시 지표 — 전체 wide DataFrame
dartlab.macro()                                 # KR 12개 지표 (CPI, 금리, 환율, 생산, ...)
dartlab.macro("US")                             # US 25개 지표 (GDP, CPI, 연방기금, S&P500, ...)
dartlab.macro("CPI")                            # 단일 지표 (자동 KR 감지)
dartlab.macro("FEDFUNDS")                       # 단일 지표 (자동 US 감지)

# 컨센서스, 뉴스
dartlab.consensus("005930")                     # 목표가 + 투자의견
dartlab.news("삼성전자")                         # Google News RSS → DataFrame
```

**데이터 수집 방식 — 걱정하지 마라, 안전하다:**

| 소스 | 데이터 | 방식 |
|------|--------|------|
| 네이버 차트 API | KR OHLCV (수정주가) | `fchart.stock.naver.com` — 종목당 1회 요청, 최대 6000일 |
| Yahoo Finance v8 | US/글로벌 OHLCV | `query2.finance.yahoo.com/v8/finance/chart` — 공개 차트 API |
| ECOS (한국은행) | KR 거시 지표 | 공식 API, 사용자 본인의 키 사용 |
| FRED (세인트루이스 연방준비) | US 거시 지표 | 공식 API, 사용자 본인의 키 사용 |
| 네이버 모바일 API | 컨센서스, 수급, 업종 PER | `m.stock.naver.com/api` — JSON 엔드포인트 |
| FMP | US 히스토리 fallback | Financial Modeling Prep API (선택) |

**안전 인프라:**

- **Rate limiting** — 도메인별 RPM 제한 (네이버 30, ECOS 30, FRED 120) + async 큐
- **Circuit breaker** — 연속 3회 실패 → 해당 소스 60초 비활성화, half-open 재시도
- **Fallback 체인** — KR: naver → yahoo_direct → yahoo / US: yahoo_direct → fmp → yahoo
- **Stale-while-revalidate** — 실패 시 캐시된 데이터 반환, `log.warning`으로 경고
- **User-Agent 로테이션** — 요청마다 랜덤화
- **조용한 실패 없음** — 모든 API 에러는 warning 레벨로 기록, 절대 삼키지 않음
- **스크래핑 없음** — 모든 소스가 공개 API 또는 공식 데이터 엔드포인트

### 국가간 비교 분석 (beta)

> **Beta** — API가 변경될 수 있다. [stability](docs/stability.md) 참고.

```python
c = dartlab.Company("005930")

# 공시 키워드 빈도 추이
c.keywordTrend(keyword="AI")          # topic × period × keyword 빈도
c.keywordTrend()                      # 54개 내장 키워드 전체

# 뉴스 수집
c.news()                              # 최근 30일
dartlab.news("AAPL", market="US")     # 미국 기업 뉴스

# 글로벌 피어 매핑 (WICS → GICS 섹터)
dartlab.crossBorderPeers("005930")    # → ["AAPL", "MSFT", "NVDA", "TSM", "AVGO"]

# 환율 변환 (FRED 기반)
from dartlab.engines.common.finance import getExchangeRate, convertValue
getExchangeRate("KRW")                # KRW/USD 환율
convertValue(1_000_000, "KRW", "USD") # → ~730.0

# 감사의견 다국가 정규화 (한/영/일 → 통일 코드)
from dartlab.engines.common.audit import normalizeAuditOpinion
normalizeAuditOpinion("적정")          # → "unqualified"
normalizeAuditOpinion("Qualified")     # → "qualified"
```

공시 불일치 탐지는 `c.insights` 안에서 자동 실행된다 — 텍스트 변화와 재무 건전성 간 불일치를 감지한다 (예: 리스크 서술 급증인데 재무는 안정적).

### 내보내기 (experimental)

> **Experimental** — 호환성 깨지는 변경 가능. 프로덕션 사용 비권장.

```bash
dartlab excel "005930" -o samsung.xlsx
```

설치: `uv add "dartlab[ai]"` (Excel 내보내기는 AI extras에 포함).

### 플러그인

```python
dartlab.plugins()               # 로드된 플러그인 목록
dartlab.reload_plugins()        # 플러그인 재스캔
```

플러그인으로 커스텀 데이터 소스, 도구, 분석 엔진을 확장할 수 있다. `dartlab plugin create --help`로 스캐폴딩.

## EDGAR (미국)

동일한 `Company` 인터페이스, 동일한 계정 표준화 파이프라인, 다른 데이터 소스. EDGAR 데이터는 SEC API에서 자동 수집된다 — 사전 다운로드 불필요:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections (heading/body 분리)
us.show("business")                 # 사업 설명
us.show("10-K::item1ARiskFactors")  # 리스크 요인
us.BS                               # SEC XBRL 재무상태표
us.ratios                           # 동일한 47개 비율
us.diff("10-K::item7Mdna")          # MD&A 텍스트 변화
us.insights                         # 7영역 등급 (A~F)

# analyst 함수 — USD 자동 감지
dartlab.valuation("AAPL")           # DCF + DDM + 상대 밸류에이션 (USD)
dartlab.forecast("AAPL")            # 매출 예측 (USD)
dartlab.simulation("AAPL")          # 시나리오 시뮬레이션 (US 매크로 프리셋)
```

인터페이스가 동일하다 — 같은 메서드, 같은 구조:

```python
# Korea (DART)                          # US (EDGAR)
c = dartlab.Company("005930")           c = dartlab.Company("AAPL")
c.sections                              c.sections
c.show("businessOverview")              c.show("business")
c.BS                                    c.BS
c.ratios                                c.ratios
c.diff("businessOverview")              c.diff("10-K::item7Mdna")
c.insights.grades()                     c.insights.grades()
```

### DART vs EDGAR 네임스페이스 차이

|               | DART           | EDGAR          |
|---------------|:--------------:|:--------------:|
| `docs`        | ✓              | ✓              |
| `finance`     | ✓              | ✓              |
| `report`      | ✓ (28개 API 타입) | ✗ (해당 없음) |
| `profile`     | ✓              | ✓              |

DART는 28개 정형 공시 API가 있는 `report` 네임스페이스가 있다 (배당, 지배구조, 임원 보상 등). SEC는 공시 구조가 다르므로 EDGAR에는 해당 없음.

**EDGAR topic 네이밍**: `{formType}::{itemId}` 형식. 단축 별칭도 사용 가능:

```python
us.show("10-K::item1Business")     # 전체 형식
us.show("business")                # 단축 별칭
us.show("risk")                    # → 10-K::item1ARiskFactors
us.show("mdna")                    # → 10-K::item7Mdna
```

## AI 분석

> **Tip:** 코드를 모르거나 자연어를 선호한다면 `dartlab.ask()`를 사용하세요. AI 비서가 데이터 다운로드부터 분석까지 모든 것을 처리합니다.

DartLab은 구조화된 기업 데이터를 LLM에 전달하는 AI 분석 레이어를 내장하고 있다. **코드 없이** 자연어로 질문하면 DartLab이 모든 것을 처리한다: 데이터 선택, 컨텍스트 조립, 답변 스트리밍.

```bash
# 터미널 한 줄 — Python 코드 필요 없음
dartlab ask "삼성전자 재무건전성 분석해줘"
```

DartLab이 데이터를 구조화하고, 관련 컨텍스트(재무제표, 인사이트, 섹터 벤치마크)를 선택해서 LLM에 전달한다:

```
$ dartlab ask "삼성전자 재무건전성 분석해줘"

삼성전자의 재무건전성은 A등급입니다.

▸ 부채비율 31.8% — 업종 평균(45.2%) 대비 양호
▸ 유동비율 258.6% — 200% 안전 기준 상회
▸ 이자보상배수 22.1배 — 이자 부담 매우 낮음

`최근 7일 수주공시 알려줘`, `이번 주 삼성전자 공시 뭐 있었어` 같은 실시간 공시목록 질문은 `OpenDART API 키`를 사용한다. UI Settings에서 프로젝트 `.env` 기준으로 저장/검증/삭제할 수 있다.
▸ ROE 회복세: 1.6% → 10.2% (4분기 연속 개선)

[데이터 출처: 2024Q4 사업보고서, dartlab insights 엔진]
```

2-Tier 아키텍처로 기본 분석은 어떤 provider에서든 동작하고, tool-calling provider(OpenAI, Claude)는 대화 중 추가 데이터를 요청해 더 깊이 분석할 수 있다.

### Python API

```python
import dartlab

# 스트리밍 출력 + 전체 텍스트 반환
answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

# provider + model 지정
answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

# 데이터 필터링
answer = dartlab.ask("삼성전자 핵심 포인트", include=["BS", "IS"])

# 분석 패턴
answer = dartlab.ask("삼성전자 분석", pattern="financial")

# 에이전트 모드 — LLM이 도구를 선택하여 심화 분석
answer = dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
```

### CLI

```bash
# provider 설정
dartlab setup              # 전체 provider 목록
dartlab setup ollama       # 로컬 LLM (무료)
dartlab setup openai       # OpenAI API

# 상태 확인
dartlab status             # 전체 provider (테이블 뷰)
dartlab status --cost      # 누적 토큰/비용 통계

# 질문 (스트리밍 기본값)
dartlab ask "삼성전자 재무건전성 분석해줘"
dartlab ask "AAPL risk analysis" -p ollama
dartlab ask --continue "배당 추세는?"

# 보고서 자동 생성
dartlab report "삼성전자" -o report.md

# 웹 UI
dartlab                    # 브라우저 UI 실행
dartlab --help             # 전체 명령어 확인
```

<details>
<summary>전체 CLI 명령어 (16개)</summary>

| 분류 | 명령어 | 설명 |
|------|--------|------|
| 데이터 | `show` | topic 열기 |
| 데이터 | `search` | 종목 검색 |
| 데이터 | `statement` | BS / IS / CF / SCE 출력 |
| 데이터 | `sections` | 원본 docs sections |
| 데이터 | `profile` | 회사 인덱스, facts |
| 데이터 | `modules` | 사용 가능 모듈 목록 |
| AI | `ask` | 자연어 질문 |
| AI | `report` | 분석 보고서 자동 생성 |
| 내보내기 | `excel` | Excel 내보내기 (experimental) |
| 수집 | `collect` | 데이터 다운로드 / 갱신 / 배치 수집 |
| 수집 | `collect --check` | 새 공시 감지 (freshness 체크) |
| 수집 | `collect --incremental` | 누락 공시만 증분 수집 |
| 서버 | `ai` | 웹 UI 실행 (localhost:8400) |
| 서버 | `share` | 터널 공유 (ngrok / cloudflared) |
| 서버 | `status` | Provider 연결 상태 |
| 서버 | `setup` | Provider 설정 마법사 |
| MCP | `mcp` | MCP stdio 서버 실행 |
| 플러그인 | `plugin` | 플러그인 생성 / 관리 |

</details>

### Provider

| Provider | 인증 | 비용 | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT 구독 (Plus/Team/Enterprise) | 구독에 포함 | Yes |
| `codex` | Codex CLI 로컬 설치 | 무료 (Codex 세션 사용) | Yes |
| `ollama` | 로컬 설치, 계정 불필요 | 무료 | 모델에 따라 다름 |
| `openai` | API 키 (`OPENAI_API_KEY`) | 토큰당 과금 | Yes |
| `custom` | OpenAI 호환 엔드포인트 | 다양 | 다양 |

**Claude provider가 없는 이유:** Anthropic은 OAuth 기반 접근을 제공하지 않는다. OAuth 없이는 사용자가 기존 구독으로 인증할 방법이 없어서 API 키를 직접 입력하게 해야 하는데, 이는 DartLab의 마찰 없는 설계에 맞지 않는다. Anthropic이 향후 OAuth를 지원하면 Claude provider를 추가할 예정이다. 현재 Claude는 **MCP**로 사용 가능 — Claude Desktop, Claude Code, Cursor에서 DartLab의 60개 도구를 직접 호출할 수 있다.

**`oauth-codex`**가 권장 provider다 — ChatGPT 구독이 있으면 API 키 없이 바로 작동한다. `dartlab setup oauth-codex`로 인증.

**웹 UI (`dartlab`)** 는 브라우저 기반 대화형 분석 인터페이스를 실행한다. 이 기능은 현재 **실험적** 단계로, 시각화와 협업 기능의 범위와 UX를 검토 중이다.

AI 의존성 설치: `uv add "dartlab[ai]"`

### 프로젝트 설정 (`.dartlab.yml`)

```yaml
company: 005930         # 기본 종목
provider: openai        # 기본 LLM provider
model: gpt-4o           # 기본 모델
verbose: false
```

## MCP — AI 어시스턴트 연동

DartLab은 [MCP](https://modelcontextprotocol.io/) 서버를 내장하고 있다. 60개 도구 (글로벌 16 + 기업별 44)를 Claude Desktop, Claude Code, Cursor 등 MCP 호환 클라이언트에 노출한다.

```bash
uv add "dartlab[mcp]"
```

### Claude Desktop

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add dartlab -- uv run dartlab mcp
```

또는 `~/.claude/settings.json`에 추가:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Cursor

`.cursor/mcp.json`에 Claude Desktop과 동일한 형식으로 추가.

### 사용 가능한 기능

연결하면 AI 어시스턴트가 다음을 수행할 수 있다:

- **검색** — 이름이나 코드로 기업 찾기 (`search_company`)
- **공시 조회** — 임의 topic의 공시 데이터 열기 (`show_topic`, `list_topics`, `diff_topic`)
- **재무** — BS, IS, CF, 재무비율 (`get_financial_statements`, `get_ratios`)
- **분석** — 인사이트, 섹터 순위, 밸류에이션 (`get_insight`, `get_ranking`)
- **EDGAR** — 미국 기업도 동일한 도구로 지원 (`stock_code: "AAPL"`)

플랫폼별 설정 자동 생성:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

## OpenAPI — 원본 공공 API

원본 공시 API를 직접 다루고 싶을 때 source-native wrapper를 쓴다.

### OpenDart (한국)

> **참고:** `Company`는 API 키가 **필요 없다** — 사전 구축 데이터셋으로 동작한다.
> `OpenDart`는 DART 원본 API를 직접 사용하므로 [opendart.fss.or.kr](https://opendart.fss.or.kr) 에서 API 키가 필요하다 (무료).
> 전체 시장 최근 공시목록을 AI가 직접 찾는 기능도 이 키를 사용하며, UI Settings에서 `OpenDART API 키`를 관리할 수 있다.

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (미국)

> **API 키 불필요.** SEC EDGAR는 공공 API다 — 등록 없이 사용 가능.

```python
from dartlab import OpenEdgar

e = OpenEdgar()
e.search("Apple")
e.filings("AAPL", forms=["10-K", "10-Q"])
e.companyFactsJson("AAPL")
```

## 데이터

**설정 불필요.** `Company`를 생성하면 해당 종목의 데이터를 자동으로 다운로드한다.

| 데이터셋 | 규모 | 출처 |
|----------|------|------|
| DART docs | 320+ 기업 | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/docs) |
| DART finance | 2,700+ 기업 | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/finance) |
| DART report | 2,700+ 기업 | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/report) |
| EDGAR | 주문형 | SEC API (자동 수집) |

### 3단계 데이터 파이프라인

```
dartlab.Company("005930")
  │
  ├─ 1. 로컬 캐시 ────── 이미 있으면 즉시 반환 (instant)
  │
  ├─ 2. HuggingFace ──── 자동 다운로드 (수 초, 키 불필요)
  │
  └─ 3. DART API ──────── API 키로 직접 수집 (키 필요)
```

HuggingFace에 없는 기업은 DART에서 직접 수집한다 — API 키가 필요하다:

```bash
dartlab setup dart-key
```

### Freshness — 자동 업데이트 감지

3-Layer freshness 시스템으로 로컬 데이터를 최신 상태로 유지한다:

| Layer | 방식 | 비용 |
|-------|------|------|
| L1 | HTTP HEAD → HuggingFace ETag 비교 | ~0.5초, 수백 바이트 |
| L2 | 로컬 파일 나이 (90일 TTL 폴백) | 즉시 (로컬) |
| L3 | DART API → `rcept_no` diff (API 키 필요) | API 1회, ~1초 |

`Company`를 열면 새 공시가 있는지 자동으로 확인한다:

```python
c = dartlab.Company("005930")
# [dartlab] ⚠ 005930 — 새 공시 2건 발견 (사업보고서 (2024.12))
#   • 증분 수집: dartlab collect --incremental 005930
#   • 또는 Python: c.update()

c.update()  # 누락된 공시만 증분 수집
```

```bash
# CLI freshness 체크
dartlab collect --check 005930         # 단일 종목
dartlab collect --check                # 전체 로컬 종목 스캔 (7일)

# 증분 수집 — 누락된 공시만
dartlab collect --incremental 005930   # 단일 종목
dartlab collect --incremental          # 새 공시 있는 전체 종목
```

### 배치 수집 (DART API)

```bash
dartlab collect --batch                    # 전체 상장, 미수집만
dartlab collect --batch -c finance 005930  # 특정 카테고리 + 종목
dartlab collect --batch --mode all         # 전체 재수집
```

## 바로 시작하기

### Marimo 노트북

> 데이터는 첫 사용 시 자동 다운로드된다. DART에서 직접 수집하지 않는 한 별도 설정 불필요.

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/dartCompany.py    # 한국 기업 (DART)
marimo edit notebooks/marimo/edgarCompany.py   # 미국 기업 (EDGAR)
marimo edit notebooks/marimo/aiAnalysis.py     # AI 분석 예시
```

### Colab 튜토리얼

| 노트북 | 주제 |
|---|---|
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb) | **빠른 시작** — sections, show, trace, diff |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial_statements.ipynb) | **재무제표** — BS, IS, CF |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb) | **재무비율** — 47개 비율 |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb) | **공시 텍스트** — sections, 텍스트 파싱 |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb) | **EDGAR** — 미국 SEC 공시 |

## 문서

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview

### 블로그

[DartLab 블로그](https://eddmpython.github.io/dartlab/blog/)는 실전 공시 분석 주제를 다룬다 — 재무제표 읽는 법, 공시 패턴 해석, 리스크 신호 포착 등. 3개 카테고리 120편 이상:

- **공시 제도** — DART/EDGAR 공시의 구조와 작동 원리
- **보고서 읽기** — 감사보고서, 잠정실적, 재작성 등 실전 가이드
- **재무 해석** — 재무제표, 비율, 공시 신호 해석

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR 파워유저 (SCE, notes, cadence, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text 도구, ask/chat, OpenDart, OpenEdgar, Server API, MCP, CLI 서브커맨드 |
| **Experimental** | AI 도구 호출, export |
| **Alpha** | Desktop App (Windows .exe) — 동작하지만 불완전, Sections Viewer — 수평화된 공시 뷰어, 아직 체계 미완성 |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 기여

이 프로젝트는 **엔진 변경 전에 실험으로 먼저 검증**하는 방식을 선호한다.

- **실험 폴더**: `experiments/XXX_camelCaseName/` — 각 파일은 독립 실행 가능해야 하고, docstring에 실제 결과가 포함되어야 한다
- **데이터 기여** (`accountMappings.json`, `sectionMappings.json` 등): 실험 증거가 있을 때만 수용 — 수작업 일괄 수정 불가
- 한국어/영어 이슈와 PR 모두 환영

## 라이선스

MIT
