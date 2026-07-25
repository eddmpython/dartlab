---
id: engines.story.companyCausal
title: Story Company Causal — 6 막 인과
category: engines
kind: curated
status: observed
purpose: 회사 6 막 (배경/사이클/실적/구조/전망/리스크) 인과 chain — story.show 응용.
sourceRefs:
  - dartlab://skills/engines.story.companyCausal
knowledgeRefs:
  - engines.story
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
  - 회사 6 막 인과 chain
  - 배경/사이클/실적/구조/전망/리스크
  - story.show 응용
---

## 절차

- 기업 식별과 사용 가능한 Company topic을 확인한다.
- macro, scan 또는 industry 맥락이 필요한지 reference에서 확인한다.
- Company.analysis와 원본 panel 결과를 실행해 수치 근거를 만든다.
- 판단 claim은 대상, 기간, metric, value ref에 묶는다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")
# 6 막 인과 chain — 배경/사이클/실적/구조/전망/리스크
story_df = c.story(reportType="companyCausal")
print(story_df.summaryCard)
```


- `c = dartlab.Company("005930")`
- `c.story()`
- `dartlab.story(c)`

## 호출 동작

- analysis, credit, macro, scan, quant 결과를 thesis/evidence/risk/limit 구조로 조립한다. 숫자 계산은 하위 엔진 결과 ref에 묶는다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- report dict 또는 block list를 반환한다. 핵심 키는 thesis, evidenceBlocks, riskBlocks, limits, sourceRefs다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.
