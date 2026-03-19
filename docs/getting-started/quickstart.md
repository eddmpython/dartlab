---
title: 빠른 시작
---

# 빠른 시작

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

DartLab에서 하나의 회사를 여는 데 필요한 것은 `c.sections` 하나다. 나머지(`show`, `trace`, `diff`, `BS`, `ratios`)는 전부 sections 위의 뷰다.

## 설치

```bash
uv add dartlab
```

AI 인터페이스까지 쓰려면:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## sections = 회사 전체

```python
import dartlab

c = dartlab.Company("005930")  # 삼성전자
c.sections
```

`sections`는 Polars DataFrame이다. 모든 공시 섹션이 topic × period 매트릭스로 들어 있다.

```
chapter │ topic            │ blockType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ "…"    │ "…"    │ "…"    │
```

이것만으로 회사의 전체 공시 구조가 보인다. topic 목록, 기간 범위, 텍스트/테이블 구분 전부 여기에 있다.

```python
c.topics              # topic 요약 DataFrame (source, blocks, periods)
c.sections.periods()  # 기간 목록
c.sections.ordered()  # 최신 순 정렬
```

## sections 위의 뷰

sections 전체를 볼 필요 없이, topic 하나만 열고 싶을 때:

```python
c.show("companyOverview")       # 블록 목차
c.show("companyOverview", 0)    # 블록 0 실제 데이터
c.show("BS")                    # 재무상태표 (finance source)
c.show("dividend")              # 배당 (report source)
```

텍스트가 언제 바뀌었는지:

```python
c.diff()                                    # 전체 변경률
c.diff("businessOverview")                  # topic 이력
c.diff("businessOverview", "2024", "2025")  # 줄 단위 비교
```

어떤 source가 채택됐는지:

```python
c.trace("BS")               # finance source
c.trace("companyOverview")  # docs source
```

## 재무제표와 비율

재무제표도 sections 위의 finance 뷰다:

```python
c.BS                    # 재무상태표 (최신 먼저)
c.IS                    # 손익계산서
c.CF                    # 현금흐름표
c.ratios                # 재무비율 시계열 DataFrame
c.finance.ratios        # 최신 단일 시점 RatioResult
c.finance.ratioSeries   # 비율 시계열 (raw)
```

## 인사이트

7개 영역(성과, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회)의 등급 분석:

```python
c.insights                      # 7영역 분석
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["매출 고성장 +8.3%", …]
c.insights.anomalies            # → 이상치, 위험 신호
```

## EDGAR도 동일

```python
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
us.BS
us.ratios
```

같은 `sections`, 같은 `show`, 같은 `diff`. topic 이름만 SEC form 기준이다.

## source namespace

더 깊게 내려가야 할 때:

```python
c.docs.sections          # pure docs source
c.finance.BS             # finance 엔진 직접
c.report.extract("배당")  # report 엔진 직접
```

하지만 대부분의 분석은 `c.sections`와 `c.show()` 두 개면 충분하다.

## 다음 단계

- [Sections 가이드](./sections) — sections 구조, 컬럼, 필터링 상세
- [API 개요](../api/overview) — 전체 API 흐름
- [공시 텍스트 실전](../tutorials/disclosure) — 텍스트/테이블 블록 활용
- [안정성 안내](../stability)
