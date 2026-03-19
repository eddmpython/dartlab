---
title: 빠른 시작
---

# 빠른 시작

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

DartLab의 현재 시작 흐름은 `sections -> show -> trace`다.

1. `Company`를 만든다
2. `sections`로 회사 맵을 본다
3. `show("topic")`으로 topic을 연다
4. `trace("topic")`으로 source를 확인한다

## 설치

```bash
uv add dartlab
```

AI 인터페이스까지 쓰려면:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## Company 생성

```python
import dartlab

# 한국: DART
c = dartlab.Company("005930")
c = dartlab.Company("삼성전자")

# 미국: EDGAR
us = dartlab.Company("AAPL")
```

## 먼저 `sections`를 본다

```python
c.sections
us.sections
```

`sections`는 회사의 canonical board다. 컬럼은 기간이고, row는 회사 문서에서 정렬된 topic 구조다.

중요한 구분:

- `c.sections`: 공개 company board
- `c.docs.sections`: pure docs source

## topic을 연다

```python
c.show("BS")
c.show("companyOverview")
c.show("audit")

us.show("BS")
us.show("10-K::item1Business")
```

`show(topic)`은 topic 하나를 실제 payload로 연다. 숫자 topic이면 `finance`가, 정형 공시 topic이면 `report`가, 서술/섹션 topic이면 `docs`가 기본 source가 된다.

## source를 추적한다

```python
c.trace("BS")
c.trace("companyOverview")
c.trace("audit")
```

`trace(topic)`은 그 topic이 왜 그 source에서 왔는지 설명한다.

확인하고 싶은 것은 보통 다음 세 가지다.

- 어떤 source가 선택됐는가
- 어떤 period가 실제로 채워졌는가
- raw docs / finance / report 중 무엇이 증거인가

## source namespace

필요하면 source를 직접 내려가서 볼 수 있다.

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

하지만 기본 경로는 여전히 `sections -> show -> trace`다.

## OpenAPI

공개 API를 직접 다루고 싶다면 source-native wrapper를 쓴다.

```python
from dartlab import OpenDart, OpenEdgar

d = OpenDart()
e = OpenEdgar()

e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

## 다음 단계

- [Sections 가이드](./sections) — sections 구조와 필터링 상세
- [API 개요](../api/overview) — 전체 API 흐름
- [공시 텍스트 실전](../tutorials/disclosure) — 텍스트/테이블 블록 활용
- [안정성 안내](../stability)
