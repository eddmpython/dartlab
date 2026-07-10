---
id: engines.company.disclosureEvent
title: Company Disclosure Event
category: engines
kind: curated
status: observed
purpose: Company.filings 응용 — 이벤트 timestamp + 본문 abstract.
sourceRefs:
  - dartlab://skills/engines.company.disclosureEvent
knowledgeRefs:
  - engines.company
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
whenToUse:
  - Company.filings 응용
  - 이벤트 timestamp + 본문 abstract
---

## 절차

- 공시 목록의 접수일, 제목, 유형을 확인한다.
- 가능한 경우 경량 본문 조회로 제목 기준 판단을 보강한다.
- 본문 미조회 상태에서는 제목 기준 우선순위라고 명시한다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")
events = c.filings()
print(events)  # timestamp + 본문 abstract
```


- `c = dartlab.Company("005930")`
- `c.panel()`
- `c.panel("BS")`
- `c.index()`
- `c.trace()`

## 호출 동작

- 종목코드 또는 ticker를 target으로 고정하고 재무, 공시, 가격, 하위 엔진 호출의 단일 진입점을 제공한다. 무인자 호출은 사용 가능한 topic/axis 가이드를 반환한다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- Company 객체 메서드는 topic별 DataFrame, dict, 또는 하위 엔진 결과를 반환한다. 핵심 식별자는 stockCode/ticker, companyName, period, topic, source, value, unit이다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.
