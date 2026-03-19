<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>공시 섹션에서 하나의 회사 맵을 만든다</b></p>

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

DartLab은 공시 문서를 하나의 회사 맵으로 바꾸는 Python 라이브러리다.

핵심은 `sections`다. 사업보고서와 분기보고서의 섹션 구조를 먼저 기간축으로 수평화하고, 그 위에 더 강한 source를 올린다.

- `docs`: 섹션 구조, 서술 텍스트, detail block, 원문 증거층
- `finance`: 재무 숫자 authoritative source
- `report`: 정형 공시 API authoritative source
- `profile`: 같은 spine 위에서 merge된 최종 company layer

공개 기본 흐름은 단순하다.

```python
import dartlab

c = dartlab.Company("005930")

c.sections
c.show("companyOverview")
c.trace("BS")
```

## 왜 지금 구조가 중요한가

예전 공시 도구는 parser가 늘어날수록 진입점도 늘어나고, 회사 전체 구조를 한 번에 설명하기 어려워졌다.

DartLab은 그 방향을 버리고 다음으로 정리하고 있다.

- 하나의 `Company`
- 하나의 canonical `sections` 맵
- 하나의 `show / trace` 소비 경로
- 같은 구조를 Python, 문서, AI GUI가 함께 소비

최근 성능과 품질 개선도 대부분 이 구조 단순화에 맞춰져 있다.

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

```python
import dartlab

# 한국: DART
c = dartlab.Company("005930")

c.sections                  # canonical company map (topic × period 매트릭스)
c.show("BS")                # topic 하나 열기 (finance source)
c.show("companyOverview")   # sections 기반 공시 payload
c.trace("BS")               # 선택된 source와 provenance
c.diff("businessOverview")  # 기간 간 텍스트 변화 감지

# 미국: EDGAR
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
```

`sections`는 Polars DataFrame이다. 각 행이 공시 블록, 각 기간 컬럼이 원문 payload를 담는다.

```
chapter │ topic            │ blockType │ 2025  │ 2024  │ 2024Q3 │ …
I       │ companyOverview  │ text      │ "…"   │ "…"   │ "…"    │
I       │ companyOverview  │ table     │ "…"   │ "…"   │ null   │
II      │ businessOverview │ text      │ "…"   │ "…"   │ "…"    │
```

핵심 구분은 이렇다.

- `c.sections`: 공개 company board (topic × period)
- `c.show(topic)`: topic 하나를 source 우선순위에 따라 연다
- `c.trace(topic)`: `docs / finance / report` 중 어떤 source가 채택됐는지 설명
- `c.diff(topic)`: 기간 간 텍스트 변화를 추적

## OpenAPI

원본 공공 API를 직접 다루고 싶다면 source-native wrapper를 쓴다.

```python
from dartlab import OpenDart, OpenEdgar

d = OpenDart()
e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

이 계층은 원본 surface를 최대한 왜곡하지 않고, 저장 parquet만 DartLab runtime과 호환되게 맞춘다.

## 핵심 개념

### 1. Sections First

`sections`가 뼈대다. 회사는 더 이상 여러 parser 결과의 모음이 아니라, 기간축 위에 정렬된 하나의 공시 맵으로 설명된다.

### 2. Source-Aware Company

`Company`는 raw source wrapper가 아니다. 같은 topic에서 `finance`나 `report`가 더 authoritative하면 그것이 docs를 대체한다.

### 3. AI-Ready Structure

앞으로의 AI GUI도 별도 스키마를 만드는 것이 아니라, 같은 `sections -> show -> trace` 구조를 그대로 소비한다.

### 4. Raw Access

더 깊게 내려가야 할 때는 source namespace를 직접 쓰면 된다.

```python
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices
c.finance.BS
c.report.audit
```

## 안정성

- DART core `Company` 흐름이 안정성 중심이다
- EDGAR는 빠르게 좋아지고 있지만 아직 더 낮은 안정성 tier다
- 공개 메시지는 `sections -> show -> trace`를 기준으로 간다
자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 문서

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview
- 블로그: https://eddmpython.github.io/dartlab/blog/

## 데이터

DartLab은 중앙 config로 데이터 릴리즈를 관리하고, source별 저장 포맷은 runtime loader와 호환되도록 고정한다.

현재 공개 릴리즈:

- DART docs
- DART finance
- DART report
- EDGAR docs
- EDGAR finance

## 기여

이 프로젝트는 엔진 변경 전에 실험으로 먼저 검증하는 방식을 선호한다. parser나 mapping을 바꾸고 싶다면 먼저 실험으로 확인한 뒤 엔진에 반영하는 흐름이 맞다.

## 라이선스

MIT
