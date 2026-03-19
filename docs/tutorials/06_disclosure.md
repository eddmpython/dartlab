---
title: "6. Disclosure Text"
---

# 6. 공시 텍스트 — sections로 읽는 서술형 공시

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb)

숫자 뒤에 숨겨진 텍스트를 읽는다. DartLab은 모든 공시 텍스트를 `sections`로 수평화한다. 사업보고서의 모든 섹션이 topic × period 매트릭스로 정리되어 있어서, 어떤 주제든 기간별로 나란히 비교할 수 있다.

---

## 준비

```python
import dartlab
import polars as pl

c = dartlab.Company("005930")
```

---

## sections로 전체 구조 보기

```python
c.sections
```

`sections`는 회사의 전체 공시 지도다. 모든 섹션이 topic × period 매트릭스로 수평화되어 있다. `blockType` 컬럼으로 텍스트와 테이블을 구분하고, `blockOrder`로 원본 순서를 보존한다.

```
│ chapter │ topic            │ blockType │ blockOrder │ 2024   │ 2023   │ ...
│ I       │ companyOverview  │ text      │ 0          │ 서술문 │ 서술문 │
│ I       │ companyOverview  │ table     │ 1          │ 테이블 │ 테이블 │
│ II      │ businessOverview │ text      │ 0          │ 서술문 │ 서술문 │
```

---

## topic 목록 확인

```python
c.topics
```

주요 topic 예시:

| topic | 설명 |
|-------|------|
| `companyOverview` | 회사의 개요 |
| `businessOverview` | 사업의 내용 |
| `riskFactors` | 위험 관리 |
| `mdna` | 경영진단 및 분석의견 |
| `salesOrder` | 매출·수주 현황 |
| `rawMaterial` | 원재료 현황 |
| `segments` | 사업부문 |
| `companyHistory` | 회사 연혁 |

회사마다 보유한 topic이 다르다. `c.topics`로 해당 종목에서 사용 가능한 전체 목록을 확인한다.

---

## show()로 topic 열기

`show()`는 sections에서 해당 topic을 꺼내 블록 단위로 보여준다.

```python
# 블록 목차 — 어떤 블록이 있는지 확인
c.show("businessOverview")
```

목차에서 블록 번호를 확인한 뒤, 원하는 블록을 꺼낸다.

```python
# 블록 0: 텍스트 DataFrame (기간별 원문)
c.show("businessOverview", 0)

# 블록 1: 테이블 DataFrame (항목 × 기간 매트릭스)
c.show("businessOverview", 1)
```

텍스트 블록은 기간별 원문 컬럼이 나란히 나오고, 테이블 블록은 항목명 × 기간 형태의 수평화된 DataFrame을 반환한다.

---

## Polars로 sections 필터링

sections는 Polars DataFrame이므로 자유롭게 필터할 수 있다.

```python
# 특정 topic의 텍스트 블록만
text_rows = c.sections.filter(
    (pl.col("topic") == "businessOverview") & (pl.col("blockType") == "text")
)

# 특정 topic의 테이블 블록만
table_rows = c.sections.filter(
    (pl.col("topic") == "businessOverview") & (pl.col("blockType") == "table")
)

# 특정 기간의 원문 읽기
row = c.sections.filter(
    (pl.col("topic") == "companyOverview") & (pl.col("blockType") == "text")
)
print(row["2024"][0])  # 2024년 텍스트
```

---

## 기간별 탐색

```python
# 사용 가능한 기간 목록
c.sections.periods()

# 최신 순 정렬
c.sections.ordered()
```

`periods()`는 해당 회사에 수록된 전체 기간 리스트를 반환한다. `ordered()`는 최신 기간이 먼저 오도록 컬럼을 재정렬한다.

---

## diff()로 변경 감지

두 기간 사이의 텍스트 변화를 추적한다. 공시 텍스트가 어느 해에 크게 바뀌었는지 한눈에 파악할 수 있다.

```python
# 전체 topic별 변경률 요약
c.diff()

# 특정 topic의 기간별 변경 이력
c.diff("businessOverview")

# 두 기간 사이 라인 단위 상세 비교
c.diff("businessOverview", "2023", "2024")
```

> 변경률이 높은 해에는 사업 구조 변경, 신사업 진출, 위험 요인 추가 등이 있을 수 있다. `diff()`로 변화 지점을 먼저 잡고, `show()`로 해당 기간의 원문을 읽는 것이 효율적인 분석 흐름이다.

---

## source namespace로 더 깊게

`c.sections`는 merged view다. 원본 데이터에 더 깊이 접근하려면 `c.docs` namespace를 사용한다.

```python
# pure docs source view (finance/report 병합 전)
c.docs.sections

# 원문 block retrieval (검색·AI용)
c.docs.retrievalBlocks

# LLM context slice
c.docs.contextSlices

# K-IFRS 주석
c.docs.notes
```

---

## 실전 예: 위험 요인 변화 추적

위험 요인은 매년 업데이트되므로, 변경 지점을 추적하면 새로운 리스크를 빠르게 발견할 수 있다.

```python
# 위험 요인 블록 목차
c.show("riskFactors")

# 텍스트 블록 열기
c.show("riskFactors", 0)

# 연도별 변경률 확인
c.diff("riskFactors")

# 2023→2024 상세 비교
c.diff("riskFactors", "2023", "2024")
```

---

## 출처 추적

어떤 topic의 데이터가 어디서 왔는지 확인한다.

```python
c.trace("businessOverview")
```

`trace()`는 해당 topic의 source(docs/finance/report), 기간 수, 텍스트·테이블 유무 등 메타데이터를 반환한다.

---

## 다음 단계

- [Sections 가이드](../getting-started/sections) — sections 구조 상세
- [7. 고급 분석](./advanced) — K-IFRS 주석, 유형자산, 관계기업
- [8. 기업 간 비교](./cross-company) — 섹터, 인사이트, 순위
