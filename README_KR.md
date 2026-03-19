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

## 왜 DartLab인가

기업 공시는 가장 풍부한 공개 정보다 — 재무제표, 리스크, 사업 전략, 지배구조, 보수, 그 이상. 하지만 지금까지 이 데이터에 접근하려면:

- **PDF 수동 읽기** — 사업보고서는 200페이지가 넘고, 프로그래밍으로 접근할 구조가 없다
- **파편화된 도구들** — 재무제표는 이 라이브러리, 텍스트는 저 라이브러리, EDGAR는 또 다른 도구. 서로 연결이 안 된다
- **시간축이 없다** — 데이터를 추출해도 같은 섹션을 5년치 비교하려면 매번 접착 코드를 짜야 한다
- **맥락의 단절** — 숫자를 설명하는 서술문이 없거나, 텍스트를 뒷받침하는 숫자가 없다

DartLab은 원본 공시에서 **하나의 통합 회사 맵**을 만든다. 텍스트, 테이블, 재무제표가 같은 topic × period 뼈대 위에 정렬된다. 파편이 아니라 전체 그림을 얻는다.

### 누구를 위한 도구인가

| 당신이... | DartLab이 주는 것 |
|---|---|
| **투자자 / 애널리스트** | 모든 공시 항목을 전 기간에 걸쳐 즉시 조회 — PDF 뒤질 필요 없음 |
| **퀀트 / 데이터 사이언티스트** | 2,700개+ 상장사의 정제된 DataFrame, 모델링에 바로 투입 |
| **개발자** | docs, finance, report API를 하나의 `Company` 객체로 통합 |
| **연구자** | 텍스트 + 재무 데이터가 결합된 표준화 기업 간 비교 데이터셋 |
| **AI 개발자** | LLM이 실제로 추론할 수 있는 구조화된 기업 맥락 |

### 이런 걸 할 수 있다

- "삼성전자가 2023→2024 사업 설명을 어떻게 바꿨지?" → `c.diff("businessOverview")`
- "Apple 최신 10-K 리스크 요인을 보여줘" → `us.show("10-K::item1ARiskFactors")`
- "상장사 중 부채비율이 가장 높은 곳은?" → `dartlab.debt("all")`
- "5년치 손익계산서를 비교하고 싶다" → `c.IS`
- "시장 전체 지배구조 현황은?" → `dartlab.governance()`

### 기존 도구와 뭐가 다른가

| | DartLab | 기존 도구들 |
|---|---|---|
| **범위** | 공시 전문 + 재무제표 + 정형 보고서 | 보통 이 중 하나만 |
| **구조** | 하나의 수평화 맵 (topic × period) | 플랫 출력, 시간축 정렬 없음 |
| **소스** | DART + EDGAR 같은 인터페이스 | 한국만 또는 미국만 |
| **데이터 출처** | `trace()`로 어떤 source가 선택됐는지 정확히 확인 | 블랙박스 |
| **AI 연동** | 구조화된 sections가 LLM 맥락에 바로 들어감 | 수동 프롬프트 엔지니어링 |

## DartLab은 무엇인가

DartLab은 공시 문서를 하나의 회사 맵으로 바꾸는 Python 라이브러리다. 한국 DART와 미국 EDGAR를 모두 지원한다.

핵심은 `sections`다. 사업보고서와 분기보고서의 섹션 구조를 기간축으로 수평화하고, 그 위에 더 강한 source를 올린다.

- **`docs`** — 섹션 구조, heading/body로 분리된 서술 텍스트, 테이블, 원문 증거층
- **`finance`** — 재무 숫자 authoritative source (BS, IS, CF) + 재무비율
- **`report`** — 정형 공시 API authoritative source (DART만 해당)

```python
import dartlab

c = dartlab.Company("005930")   # 삼성전자 (DART)
c.sections                      # 전체 회사 맵 (topic × period)
c.topics                        # topic 목록 (source, blocks, periods)
c.show("companyOverview")       # topic 하나 열기
c.show("IS", period=["2024Q4", "2023Q4"])  # 특정 기간 비교
c.BS                            # 재무상태표
c.ratios                        # 재무비율 시계열
c.insights                      # 7영역 등급 (A~F)

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("10-K::item1Business")
us.BS
us.ratios
```

## 설치

```bash
uv add dartlab
```

**데이터 설정 불필요.** `Company`를 처음 생성하면 필요한 데이터를 자동으로 다운로드한다. DART 데이터는 GitHub Releases에서, EDGAR 재무 데이터는 SEC API에서 직접 가져온다. 두 번째 실행부터는 로컬 캐시를 사용해 즉시 로드된다.

```
[dartlab] 005930 (DART 공시 문서 데이터) → 첫 사용: GitHub에서 자동 다운로드 중...
[dartlab] ✓ DART 공시 문서 데이터 다운로드 완료 (542KB)
[dartlab] 005930 (재무 숫자 데이터) → 첫 사용: GitHub에서 자동 다운로드 중...
[dartlab] ✓ 재무 숫자 데이터 다운로드 완료 (38KB)
```

AI 인터페이스:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## 바로 시작하기

Marimo 인터랙티브 노트북으로 실제 기업 데이터를 바로 탐색할 수 있다 — 코드 작성 불필요:

```bash
uv add dartlab marimo
marimo edit startMarimo/dartCompany.py    # 한국 기업 (DART)
marimo edit startMarimo/edgarCompany.py   # 미국 기업 (EDGAR)
```

또는 브라우저에서 [Colab 빠른 시작 노트북](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)을 연다.

## 빠른 시작

### Sections — 회사 맵

`sections`는 Polars DataFrame이다. 각 행이 공시 블록, 각 기간 컬럼이 원문 payload를 담는다. 최신 기간이 먼저 오고, 연간 보고서는 Q4로 표시된다.

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ null         │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
III     │ BS               │ table     │ null         │ —      │ —      │ —      │ (finance)
VII     │ dividend         │ table     │ null         │ —      │ —      │ —      │ (report)
```

텍스트 블록은 구조 메타데이터를 함께 담는다 — `textNodeType` (heading/body), `textLevel`, `textPath` — 섹션 제목과 서술 본문을 구분할 수 있다.

### Show, Trace, Diff

```python
c = dartlab.Company("005930")

# show — source 우선순위에 따라 topic을 연다
c.show("BS")                # → finance DataFrame
c.show("companyOverview")   # → sections 기반 텍스트 + 테이블
c.show("dividend")          # → report DataFrame (전 분기)

# 특정 기간 비교
c.show("IS", period=["2024Q4", "2023Q4"])

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

### 모듈 — 어떤 topic을 볼 수 있는가

DartLab은 6개 카테고리에 걸쳐 100개 이상의 모듈을 제공한다. CLI로 확인:

```bash
dartlab modules                      # 전체 모듈 목록
dartlab modules --category finance   # 카테고리 필터
dartlab modules --search dividend    # 키워드 검색
```

Python에서:

```python
c.topics    # 이 회사에서 사용 가능한 전체 topic 목록
```

카테고리: `finance` (재무제표, 비율), `report` (배당, 지배구조, 감사), `notes` (K-IFRS 주석), `disclosure` (서술형 텍스트), `analysis` (인사이트, 순위), `raw` (원본 parquet).

### 인사이트

```python
c.insights                      # 7영역 분석
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["매출 고성장 +8.3%", …]
c.insights.anomalies            # → 이상치, 위험 신호
```

7개 분석 영역: 성과, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회.

### 관계 네트워크

상장사 간 출자/지분 관계를 시각화한다 — 그룹 구조, 순환출자 탐지 포함:

```python
c = dartlab.Company("005930")

# 브라우저에서 인터랙티브 관계도
c.network().show()           # ego 뷰 (1홉)
c.network(hops=2).show()     # 2홉 이웃

# DataFrame 뷰
c.network("members")     # 같은 그룹 계열사
c.network("edges")       # 출자/지분 연결
c.network("cycles")      # 순환출자 경로
c.network("peers")       # ego 서브그래프

# 전체 시장 네트워크
dartlab.network().show()
```

브라우저 뷰는 다크/라이트 테마, 회사 검색, 그룹 필터, 지분율 툴팁, 클릭 하이라이트를 지원한다.

### 시장 전수 스캔

회사 하나를 보다가 바로 시장 전체로 넓혀서 같은 축을 스캔할 수 있다:

```python
c = dartlab.Company("005930")

# 개별 회사
c.governance()
c.workforce()
c.capital()
c.debt()

# 시장 요약
c.governance("market")   # 시장별 요약
c.governance("all")      # 전체 상장사 DataFrame

# 모듈 레벨 전체 스캔
dartlab.governance()
dartlab.workforce()
dartlab.capital()
dartlab.debt()
```

report + finance parquet를 결합해 지배구조, 인력/보수, 주주환원, 부채위험을 시장 전체 DataFrame으로 바로 뽑는다.

### EDGAR (미국)

동일한 `Company` 인터페이스, 다른 데이터 소스:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections (heading/body 분리)
us.show("10-K::item1Business")      # 사업 설명
us.show("10-K::item1ARiskFactors")  # 리스크 요인
us.BS                               # SEC XBRL 재무상태표
us.ratios                           # 동일한 47개 비율
us.diff("10-K::item7Mdna")          # MD&A 텍스트 변화
```

EDGAR sections도 DART와 동일한 텍스트 구조 메타데이터(heading/body 분리, textLevel, textPath)를 갖는다.

## OpenAPI — 원본 공공 API

원본 공시 API를 직접 다루고 싶을 때 source-native wrapper를 쓴다.

### OpenDart (한국)

```python
from dartlab import OpenDart

d = OpenDart()                                  # API 키 자동 탐색
d = OpenDart(["key1", "key2"])                  # 멀티 키 로테이션

d.search("카카오", listed=True)                  # 기업 검색
d.filings("삼성전자", "2024")                    # 공시 목록
d.company("삼성전자")                            # 기업 개황
d.finstate("삼성전자", 2024)                     # 재무제표
d.report("삼성전자", "배당", 2024)                # 56개 보고서 유형

# 편의 프록시
s = d("삼성전자")
s.finance(2024)
s.report("배당", 2024)
s.filings("2024")
```

### OpenEdgar (미국)

```python
from dartlab import OpenEdgar

e = OpenEdgar()

e.search("Apple")                               # 종목 검색
e.company("AAPL")                               # 기업 정보
e.filings("AAPL", forms=["10-K", "10-Q"])       # 공시 목록
e.companyFactsJson("AAPL")                      # XBRL 팩트
e.companyConceptJson("AAPL", "us-gaap", "Revenue")  # 단일 태그 시계열
```

이 계층은 원본 surface를 최대한 왜곡하지 않으면서, 저장 parquet은 DartLab runtime과 호환되게 맞춘다.

## MCP — AI 어시스턴트 연동

DartLab은 [MCP](https://modelcontextprotocol.io/) 서버를 내장하고 있다. Claude Desktop, Cursor 등 MCP 호환 AI 어시스턴트에 직접 연결하면, DartLab의 전체 분석 엔진을 AI가 도구로 호출할 수 있다.

```bash
uv add "dartlab[mcp]"
```

### Claude Desktop

Claude Desktop 설정 파일(`claude_desktop_config.json`)에 추가:

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

### AI가 할 수 있는 것

연결하면 AI 어시스턴트가 다음을 수행할 수 있다:

- **기업 검색** — "삼성전자 찾아줘" → `search_company` 호출
- **공시 항목 조회** — "삼성전자 사업개요 보여줘" → `show_topic` 호출
- **기간 비교** — "2024년과 2023년 재무제표 비교해줘" → `get_timeseries` 호출
- **비율 계산** — "부채비율 계산해줘" → `calculate_ratios` 호출
- **등급 평가** — "이 회사 종합 등급은?" → `get_insights` 호출
- **교차 시장 분석** — DART(한국)과 EDGAR(미국) 기업 모두 지원

45개 이상의 도구가 MCP 브릿지를 통해 자동으로 사용 가능하다. AI는 원문이 아닌 구조화된 기업 데이터를 받으므로 정확하고 근거 있는 답변을 할 수 있다.

### CLI

```bash
dartlab mcp    # MCP stdio 서버 시작
```

## 핵심 개념

### 1. Sections First

`sections`가 뼈대다. 회사는 여러 parser 결과의 모음이 아니라, 기간축 위에 정렬된 하나의 공시 맵으로 설명된다.

### 2. Source-Aware Company

`Company`는 raw source wrapper가 아니다. 같은 topic에서 `finance`나 `report`가 더 authoritative하면 자동으로 대체한다. `trace()`로 어떤 source가 채택됐는지 확인할 수 있다.

### 3. 텍스트 구조

서술 텍스트는 flat string이 아니다. heading/body로 분리되고, 레벨과 경로 메타데이터를 갖는다. 한국어 DART와 영문 EDGAR 공시 모두 동일한 구조를 제공한다.

### 4. Raw Access

더 깊게 내려가야 할 때는 source namespace를 직접 쓴다.

```python
c.docs.sections          # pure docs 수평화
c.finance.BS             # finance 엔진 직접
c.report.extract("배당")  # report 엔진 직접
```

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, ratios, insights) |
| **Beta** | EDGAR Company, OpenDart, OpenEdgar, Server API |
| **Experimental** | AI 도구, export |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 데이터

DartLab은 GitHub Releases로 사전 구축 데이터셋을 제공한다. 데이터는 새 공시가 수집될 때마다 지속 업데이트된다.

| 데이터셋 | 규모 | 출처 |
|----------|------|------|
| DART docs | 260+ 기업 | 한국 공시 텍스트 + 테이블 |
| DART finance | 2,700+ 기업 | XBRL 재무제표 |
| DART report | 2,700+ 기업 | 정형 공시 API |
| EDGAR docs | 970+ 기업 | 10-K/10-Q sections |
| EDGAR finance | 주문형 | SEC XBRL facts (SEC API 자동 수집) |

```python
# 전체 다운로드 (선택사항 — 전 종목 일괄 다운로드)
from dartlab.core.dataLoader import downloadAll
downloadAll("docs")       # DART 공시 문서
downloadAll("finance")    # DART 재무제표
downloadAll("report")     # DART 정형 보고서
```

## 문서

문서는 지속적으로 업데이트 중이다.

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview

### 블로그

[DartLab 블로그](https://eddmpython.github.io/dartlab/blog/)는 실전 공시 분석 주제를 다룬다 — 재무제표 읽는 법, 공시 패턴 해석, 리스크 신호 포착 등. 3개 카테고리 115편 이상:

- **공시 제도** — DART/EDGAR 공시의 구조와 작동 원리
- **보고서 읽기** — 감사보고서, 잠정실적, 재작성 등 실전 가이드
- **재무 해석** — 재무제표, 비율, 공시 신호 해석

## 기여

이 프로젝트는 엔진 변경 전에 실험으로 먼저 검증하는 방식을 선호한다. parser나 mapping을 바꾸고 싶다면 먼저 실험으로 확인한 뒤 엔진에 반영하는 흐름이 맞다.

## 라이선스

MIT
