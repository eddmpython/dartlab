---
title: API Overview
---

# API Overview

DartLab의 현재 공개 Company 흐름은 `sections -> show(topic) -> trace(topic)` 이다.

핵심은 parser 목록이 아니라 회사 맵이다. 먼저 `sections`로 회사 구조를 보고, 필요한 topic을 열고, 마지막에 그 값이 `docs`, `finance`, `report` 중 어디에서 왔는지 확인한다.

## Company 생성

```python
import dartlab

# DART
c = dartlab.Company("005930")
c = dartlab.Company("삼성전자")

# EDGAR
us = dartlab.Company("AAPL")
```

## 현재 공개 surface

```python
c.sections
c.show("BS")
c.trace("companyOverview")
```

- `c.sections`: 공개 company board
- `c.show(topic)`: topic payload 반환
- `c.trace(topic)`: source provenance 반환

## sections

`sections`는 회사의 canonical map이다. Polars DataFrame으로, 각 행이 공시 블록이고 기간 컬럼이 원문을 담는다.

```python
c.sections                  # topic × period 매트릭스
c.sections.periods()        # 사용 가능한 기간 목록
c.sections.ordered()        # 최신 순 정렬
c.topics                    # topic 요약 DataFrame (source, blocks, periods)
```

핵심 컬럼:

| 컬럼 | 설명 |
|------|------|
| `chapter` | 대분류 (I~XII) |
| `topic` | 표준 topic snakeId |
| `blockType` | "text" 또는 "table" |
| `blockOrder` | topic 내 순서 |
| `textNodeType` | text 블록 세부 유형: "heading" 또는 "body" |
| `textLevel` | heading 깊이 레벨 |
| `textPath` | heading 구조적 경로 |
| 기간 컬럼 | `2025Q4`, `2024Q4`, `2024Q3` 등 — 원문 payload |

이 board의 의도는 다음과 같다.

- 공시를 세로 문서가 아니라 기간축 위의 회사 맵으로 본다
- 같은 topic을 여러 기간에 걸쳐 바로 비교한다
- AI GUI와 Python이 같은 구조를 공유한다

pure docs source가 필요하면 `c.docs.sections`를 쓴다.

자세한 구조는 [Sections 가이드](../getting-started/sections)를 본다.

## show(topic)

```python
c.show("BS")
c.show("companyOverview")
c.show("audit")

us.show("BS")
us.show("10-K::item1Business")
```

`show(topic)`은 topic 하나를 연다.

대략적인 source 우선순위는 다음과 같다.

- 재무 숫자: `finance`
- 정형 공시: `report`
- 서술형/섹션/원문 구조: `docs`

즉 `Company`는 raw source wrapper가 아니라 source-aware merged company object다.

## trace(topic)

```python
c.trace("BS")
c.trace("dividend")
c.trace("companyOverview")
```

`trace(topic)`은 같은 topic에서 실제로 어떤 source가 채택됐는지 설명한다.

보통 여기서 확인하는 정보는:

- 선택 source
- provenance
- fallback 여부
- period coverage

## diff()

`diff()`는 기간 간 텍스트 변화를 감지한다.

```python
c.diff()                                # 전체 topic별 변경률
c.diff("businessOverview")              # 기간별 변경 이력
c.diff("businessOverview", "2023", "2024")  # 라인 단위 비교
```

변경률이 높은 해에는 사업 구조 변경, 신사업 진출, 위험 요인 추가가 있을 수 있다.

## source namespace

더 깊게 내려가야 할 때는 source namespace를 직접 쓴다.

```python
# DART
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices
c.finance.BS
c.report.audit

# EDGAR
us.docs.sections
us.finance.BS
```

## OpenAPI

`Company`와 별도로 public API wrapper도 제공한다.

```python
from dartlab import OpenDart, OpenEdgar

d = OpenDart()
e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

원칙은 이렇다.

- 외부 인터페이스는 source-native
- 저장 포맷은 DartLab runtime과 호환
- derived `Company` layer는 별도 책임

## 안정성

- DART core `Company`는 stable 중심
- EDGAR는 더 낮은 안정성 tier
자세한 기준은 [안정성 안내](../stability)를 본다.
