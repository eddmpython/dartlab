---
title: "Sections — 회사 맵"
---

# Sections — 회사 맵

DartLab에서 `sections`는 회사의 전체 지도다. 매 보고기간마다 제출되는 공시 문서를 topic(주제) 단위로 나누고, 기간축으로 나란히 정렬한 하나의 수평화 보드가 `sections`다. 개별 사업보고서를 하나씩 열어 볼 필요 없이, 모든 공시 섹션을 시간 순서대로 한눈에 비교할 수 있다.

## sections는 무엇인가

DART에 제출되는 사업보고서에는 I장 회사의 개요부터 XII장 상세표까지 수십 개의 섹션이 들어 있다. 문제는 이 보고서가 매 분기/연도마다 별도 파일로 존재한다는 것이다. 같은 주제("사업의 개요")가 2025년, 2024년, 2024Q3에 각각 흩어져 있다.

`sections`는 이 흩어진 원문을 **topic x period 매트릭스**로 재구성한다. 한 행은 하나의 주제-블록이고, 열은 기간이다. 텍스트든 테이블이든 원본 그대로 보존하면서, 시간축으로 정렬해 준다.

```python
import dartlab

c = dartlab.Company("005930")  # 삼성전자
c.sections
```

반환되는 DataFrame은 이런 형태다:

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ null         │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
```

## 핵심 컬럼

### 구조 컬럼

| 컬럼 | 설명 |
|---|---|
| `chapter` | 대분류 번호. I~XII까지 사업보고서 장(章) 구분 |
| `topic` | 표준 topic 식별자. `companyOverview`, `businessOverview`, `BS`, `IS`, `CF` 등 snakeCase로 통일된 이름 |
| `blockType` | `"text"` 또는 `"table"`. 같은 topic 안에 서술 블록과 테이블 블록이 섞여 있을 때 구분 |
| `blockOrder` | topic 내 블록 순서. 원본 문서에서의 등장 순서를 그대로 보존 |
| `textNodeType` | text 블록의 세부 유형: `"heading"` (섹션 제목) 또는 `"body"` (서술 본문). table에서는 null |
| `textLevel` | heading의 깊이 레벨 (1, 2, 3, ...). body와 table에서는 null |
| `textPath` | heading의 구조적 경로. 섹션 내 위치를 나타낸다 |

### 기간 컬럼

`2025Q4`, `2024Q4`, `2024Q3`, `2024Q2`, `2024Q1`, ... 형태의 컬럼이 이어진다. 최신 기간이 먼저 오고, 연간 보고서는 Q4로 표시된다.

- 각 셀에는 해당 기간의 원문 payload가 들어 있다
- text 블록이면 서술형 텍스트, table 블록이면 마크다운 테이블
- `null`이면 해당 기간에 데이터가 없는 것

## show(topic)으로 topic 열기

`sections` 전체를 탐색한 뒤, 특정 topic을 깊이 보고 싶을 때 `show()`를 쓴다.

```python
c.show("companyOverview")       # block 목차 DataFrame (block, type, source, preview)
c.show("companyOverview", 0)    # block 0의 실제 데이터 DataFrame
c.show("BS")                    # 재무상태표 (finance source)
```

`show()`는 항상 `sections` 위에서 동작하며, source 우선순위가 있다:

1. **finance** (BS, IS, CF, CIS, SCE) -- 숫자가 authoritative이므로 docs 텍스트보다 우선
2. **report** -- DART 정형 공시 데이터
3. **docs** -- 원본 서술형 텍스트/테이블

재무제표 topic은 finance 엔진이 계산한 정규화된 숫자 DataFrame을 반환한다. 서술형 topic은 원문 텍스트를 기간별로 정렬해서 돌려준다.

## trace(topic)로 출처 확인

어떤 source가 실제로 채택되었는지 확인하고 싶다면 `trace()`를 쓴다.

```python
c.trace("BS")               # finance source, 기간별 coverage
c.trace("companyOverview")  # docs source
```

반환 결과에는 다음 정보가 포함된다:

- 채택된 source (docs / finance / report)
- 기간별 데이터 존재 여부(coverage)
- chapter, label 등 메타데이터

## sections 필터링

`sections`는 Polars DataFrame이므로 Polars 문법으로 자유롭게 필터링할 수 있다.

```python
import polars as pl

# 특정 topic만
df = c.sections.filter(pl.col("topic") == "companyOverview")

# text 블록만
df = c.sections.filter(pl.col("blockType") == "text")

# table 블록만
df = c.sections.filter(pl.col("blockType") == "table")
```

`sections`에는 편의 메서드도 있다:

```python
c.sections.periods()    # 기간 목록 반환
c.sections.ordered()    # 최신 순 정렬
c.sections.coverage()   # topic별 기간 coverage 요약
```

## docs.sections vs sections

현재 `c.sections`와 `c.docs.sections`는 동일하다. 둘 다 pure docs source view를 가리킨다.

```python
c.sections              # 바로가기
c.docs.sections         # 명시적 경로 (동일)
```

`show(topic)`이 source 우선순위(finance > report > docs)를 적용해서 merge된 결과를 보여 주므로, 실사용에서는 `show()`를 쓰면 된다.

## EDGAR에서도 동일

미국 SEC EDGAR 기업도 같은 구조, 같은 API로 접근한다.

```python
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
us.show("BS")
```

topic 이름만 SEC form 기준이다. 10-K의 Item 1이면 `10-K::item1Business`, Item 7이면 `10-K::item7MDA` 식이다. 재무제표 topic(BS, IS, CF)은 DART와 동일한 이름을 쓴다.

## 다음 단계

- [빠른 시작](./quickstart) -- Company 생성부터 show()까지 한번에
- [API Overview](../api/overview) -- 전체 API 흐름
- [공시 텍스트 실전](../tutorials/06_disclosure) -- 서술형 공시 데이터 활용
- [EDGAR 튜토리얼](../tutorials/09_edgar) -- 미국 기업 분석
