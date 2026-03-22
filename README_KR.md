<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>공시 문서에서 하나의 회사 맵을 만든다 — DART + EDGAR</b></p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-115%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> · <a href="https://eddmpython.github.io/dartlab/blog/">블로그</a> · <a href="startMarimo/">Marimo 노트북</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb">Colab에서 열기</a> · <a href="README.md">English</a> · <a href="https://buymeacoffee.com/eddmpython">후원</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

## 설치

```bash
uv add dartlab
```

**설정 불필요.** `Company`를 생성하면 필요한 데이터를 자동으로 다운로드한다. DART 데이터는 GitHub Releases에서, EDGAR 데이터는 SEC API에서 가져온다. 두 번째 실행부터는 로컬 캐시로 즉시 로드된다.

## 빠른 시작

```python
import dartlab

c = dartlab.Company("005930")   # 삼성전자 (DART)
c.sections                      # 전체 회사 맵 (topic × period)
c.show("overview")              # topic 하나 열기
c.BS                            # 재무상태표
c.ratios                        # 재무비율 시계열
c.insights                      # 7영역 등급 (A~F)

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("business")
us.BS
us.ratios
```

## DartLab은 무엇인가

DartLab은 공시 문서를 하나의 회사 맵으로 바꾸는 Python 라이브러리다. 한국 DART와 미국 EDGAR를 모두 지원한다.

핵심은 `sections`다. 사업보고서와 분기보고서의 섹션 구조를 기간축으로 수평화하고, 그 위에 더 강한 source를 올린다.

- **`docs`** — 섹션 구조, heading/body로 분리된 서술 텍스트, 테이블, 원문 증거층
- **`finance`** — 재무 숫자 authoritative source (BS, IS, CF) + 재무비율
- **`report`** — 정형 공시 API authoritative source (DART만 해당)

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
III     │ BS               │ table     │ null         │ —      │ —      │ —      │ (finance)
VII     │ dividend         │ table     │ null         │ —      │ —      │ —      │ (report)
```

### 핵심 원칙

1. **Sections First** — 회사는 여러 parser 결과의 모음이 아니라, 기간축 위에 정렬된 하나의 공시 맵이다
2. **Source-Aware** — `finance`나 `report`가 더 authoritative하면 자동으로 대체한다. `trace()`로 어떤 source가 채택됐는지 확인
3. **텍스트 구조** — 서술 텍스트는 heading/body로 분리되고, 레벨과 경로 메타데이터를 갖는다. DART와 EDGAR 모두 동일
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

### 재무제표와 재무비율

```python
c.BS                    # 재무상태표 (계정 × period, 최신 먼저)
c.IS                    # 손익계산서
c.CF                    # 현금흐름표
c.ratios                # 재무비율 시계열 DataFrame (6개 카테고리 × period)
c.finance.ratios        # 최신 단일 시점 RatioResult
c.finance.ratioSeries   # 비율 시계열 across years
c.finance.timeseries    # 원본 계정 시계열
```

재무비율은 6개 카테고리를 포괄한다: 수익성, 안정성, 성장성, 효율성, 현금흐름, 밸류에이션.

### 인사이트

```python
c.insights                      # 7영역 분석
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["매출 고성장 +8.3%", …]
c.insights.anomalies            # → 이상치, 위험 신호
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

### 차트 & 시각화

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

### 관계 네트워크

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

### 시장 전수 스캔

```python
c = dartlab.Company("005930")

# 개별 회사 → 시장 전체
c.governance()           # 개별 회사
c.governance("all")      # 전체 상장사 DataFrame
dartlab.governance()     # 모듈 레벨 스캔
dartlab.workforce()
dartlab.capital()
dartlab.debt()
```

## EDGAR (미국)

동일한 `Company` 인터페이스, 다른 데이터 소스:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections (heading/body 분리)
us.show("business")                 # 사업 설명
us.show("10-K::item1ARiskFactors")  # 리스크 요인
us.BS                               # SEC XBRL 재무상태표
us.ratios                           # 동일한 47개 비율
us.diff("10-K::item7Mdna")          # MD&A 텍스트 변화
```

## AI 분석

DartLab은 구조화된 기업 데이터를 LLM에 전달하는 AI 분석 레이어를 내장하고 있다. 질문에 따라 관련 데이터를 자동으로 선택한다.

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
```

5개 provider 지원: `oauth-codex` (ChatGPT 구독), `codex` (Codex CLI), `ollama` (로컬, 무료), `openai` (API 키), `custom` (OpenAI 호환).

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

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (미국)

```python
from dartlab import OpenEdgar

e = OpenEdgar()
e.search("Apple")
e.filings("AAPL", forms=["10-K", "10-Q"])
e.companyFactsJson("AAPL")
```

## 데이터

**설정 불필요.** `Company`를 생성하면 해당 종목의 데이터를 자동으로 다운로드한다. DART 데이터는 GitHub Releases에서, EDGAR 데이터는 SEC API에서 가져온다.

| 데이터셋 | 규모 | 출처 |
|----------|------|------|
| DART docs | 320+ 기업 (수집 중) | 한국 공시 텍스트 + 테이블 |
| DART finance | 2,700+ 기업 | XBRL 재무제표 |
| DART report | 2,700+ 기업 | 정형 공시 API |
| EDGAR | 주문형 | SEC XBRL + 10-K/10-Q (자동 수집) |

## 바로 시작하기

### Marimo 노트북

```bash
uv add dartlab marimo
marimo edit startMarimo/dartCompany.py    # 한국 기업 (DART)
marimo edit startMarimo/edgarCompany.py   # 미국 기업 (EDGAR)
marimo edit startMarimo/aiAnalysis.py     # AI 분석 예시
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

[DartLab 블로그](https://eddmpython.github.io/dartlab/blog/)는 실전 공시 분석 주제를 다룬다 — 재무제표 읽는 법, 공시 패턴 해석, 리스크 신호 포착 등. 3개 카테고리 115편 이상:

- **공시 제도** — DART/EDGAR 공시의 구조와 작동 원리
- **보고서 읽기** — 감사보고서, 잠정실적, 재작성 등 실전 가이드
- **재무 해석** — 재무제표, 비율, 공시 신호 해석

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, ratios, insights) |
| **Beta** | EDGAR Company, OpenDart, OpenEdgar, Server API, MCP 서버 |
| **Experimental** | AI 도구, export |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 기여

이 프로젝트는 엔진 변경 전에 실험으로 먼저 검증하는 방식을 선호한다. parser나 mapping을 바꾸고 싶다면 먼저 실험으로 확인한 뒤 엔진에 반영하는 흐름이 맞다.

## 라이선스

MIT
