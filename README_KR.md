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
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> · <a href="README.md">English</a> · <a href="https://buymeacoffee.com/eddmpython">후원</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

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
c.show("companyOverview")       # topic 하나 열기
c.BS                            # 재무상태표
c.ratios                        # 47개 재무비율
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

AI 인터페이스:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

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
c.show("dividend")          # → report DataFrame

# trace — docs/finance/report 중 어떤 source가 채택됐는지
c.trace("BS")               # → {"primarySource": "finance", ...}

# diff — 기간 간 텍스트 변화 감지 (3가지 모드)
c.diff()                                    # 전체 요약
c.diff("businessOverview")                  # topic 이력
c.diff("businessOverview", "2024", "2025")  # 줄 단위 diff
```

### 재무제표와 재무비율

```python
c.BS                    # 재무상태표 (계정 × 연도)
c.IS                    # 손익계산서
c.CF                    # 현금흐름표
c.finance.ratios        # 47개 비율 (ROE, 부채비율, 마진, …)
c.finance.ratioSeries   # 비율 시계열
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

7개 분석 영역: 성과, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회.

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

## 문서

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview
- 블로그: https://eddmpython.github.io/dartlab/blog/

## 데이터

DartLab은 GitHub Releases로 사전 구축 데이터셋을 제공한다.

| 데이터셋 | 규모 | 출처 |
|----------|------|------|
| DART docs | 260+ 기업 | 한국 공시 텍스트 + 테이블 |
| DART finance | 2,700+ 기업 | XBRL 재무제표 |
| DART report | 2,700+ 기업 | 정형 공시 API |
| EDGAR docs | 970+ 기업 | 10-K/10-Q sections |
| EDGAR finance | 970+ 기업 | SEC XBRL facts |

## 기여

이 프로젝트는 엔진 변경 전에 실험으로 먼저 검증하는 방식을 선호한다. parser나 mapping을 바꾸고 싶다면 먼저 실험으로 확인한 뒤 엔진에 반영하는 흐름이 맞다.

## 라이선스

MIT
