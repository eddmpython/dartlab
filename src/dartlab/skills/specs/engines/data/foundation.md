---
id: engines.data.foundation
title: 데이터 엔진 기본기
kind: curated
scope: builtin
status: unverified
category: engines
purpose: 응용 분석 skill이 시작 전에 참조할 Company, gather, scan 데이터 엔진의 기본 선택 순서와 evidence 계약을 정의한다.
whenToUse:
  - 응용 분석 skill을 만들기 전에 데이터 확보 순서를 정할 때
  - Company, gather, scan 중 어떤 데이터 엔진을 먼저 써야 하는지 판단할 때
  - 단일 종목, 원자료 수집, 횡단 비교를 한 질문 안에서 조합해야 할 때
capabilityRefs:
  - Company
  - Company.index
  - Company.panel
  - Company.trace
  - gather
  - scan
knowledgeRefs:
  - engines.company
  - engines.gather
  - engines.scan
toolRefs:
  - search_reference
  - EngineCall
  - RunPython
datasetRefs:
  - dart.finance
  - dart.docs
  - market.price
  - market.flow
  - macro.raw
requiredEvidence:
  - target
  - universe
  - provider
  - topic
  - metric
  - period
  - latestAsOf
  - table
  - rank
  - executionRef
  - sourceRef
expectedOutputs:
  - data-engine routing decision
  - source table refs
  - data availability and freshness note
  - downstream analysis handoff plan
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
    notes:
      - Web AI는 snapshot과 provider 접근 범위 안에서 Company/gather/scan을 조합한다.
  pyodide:
    status: limited
    dataSources:
      - HuggingFace dartlab-data snapshot
      - packaged scan finance-lite snapshot
    limitations:
      - live EDGAR, 외부 market provider, full scan 축은 서버와 coverage가 다를 수 있다.
failureModes:
  - 데이터 가능 여부 확인 없이 analysis, credit, story부터 실행
  - 단일 종목 질문에 scan만 쓰고 Company 원자료를 확인하지 않음
  - 최신 원자료 질문에 gather latestAsOf를 남기지 않음
  - 횡단 비교에서 universe와 rank 기준을 숨김
  - 실행 ref는 만들었지만 claim refs를 연결하지 않아 Workbench 검산 실패
  - scan finance-lite의 부분 계정 커버리지를 단일 기업 재무제표 전체로 오해
forbidden:
  - 공개 호출 방식, 대표 반환 형태, 오류/제한 동작을 skill과 불일치한 채 방치하지 않는다.
  - source table 없이 응용 엔진 결론을 먼저 만들지 않는다.
  - 후보·상위·랭킹 산출물은 입력/유니버스, 필터, 계산식/지표, 결과 evidence table 없이 완료하지 않는다.
  - Company, gather, scan 결과를 서로 같은 의미의 데이터로 합치지 않는다.
examples:
  - 종목 분석은 Company로 target/topic을 확정하고, 필요한 최신 시장 데이터만 gather로 보강한다.
  - 후보 발굴은 scan으로 universe/rank를 만들고, 남은 후보만 Company로 원자료를 확인한다.
  - 시장 급변 질문은 gather로 price/news 최신성을 확인하고 scan 또는 Company로 영향 대상을 좁힌다.
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-02"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 기본 판단

- 단일 종목의 재무, 공시, 사업, 하위 엔진 라우팅은 `Company`가 먼저다. scan prebuild는 peer 위치, universe ranking, Company 원자료 부재 시의 보조 경로다.
- 최신 주가, 수급, 뉴스, 거시 원자료처럼 외부 데이터 신선도가 핵심이면 `gather`가 먼저다.
- 후보 발굴, 순위, peer 위치, 시장 전체 분포가 핵심이면 `scan`이 먼저다.
- 질문이 섞여 있으면 `Company`로 target을 고정하고, `gather`로 최신 raw data를 보강하고, `scan`으로 상대 위치를 확인한다.

## 응용 Skill 작성 시작점

- 응용 skill은 먼저 `knowledgeRefs`의 `engines.company`, `engines.gather`, `engines.scan`을 참조한다.
- 단일 엔진의 기본 사용법은 각 엔진의 `SKILL.md`를 본다. capability/docstring은 스킬의 공개 호출과 반환 설명을 검산하는 원천 자료다.
- 응용 skill은 이 skill의 requiredEvidence 중 자기 질문에 필요한 항목을 줄이지 말고 구체화한다.
- 응용 skill은 source table ref를 만든 뒤 analysis, credit, quant, macro, story, viz로 넘긴다.

## 절차

- 질문을 단일 종목, 원자료 최신성, 횡단 비교 중 어디에 속하는지 분류한다.
- 필요한 경우 세 경로를 조합하되, 각 경로의 evidence 이름을 분리한다.
- Company 경로는 target, topic, source, period를 남긴다.
- gather 경로는 provider, latestAsOf, metric, table을 남긴다.
- scan 경로는 universe, metric, period, rank, table을 남긴다.
- table/value/date ref를 만든 뒤에는 최종 답변의 material claim마다 해당 ref를 직접 연결한다. evidence refs 전체 목록만 제출하는 것은 숫자 claim 근거가 아니다.
- 후보·상위·랭킹 산출물은 입력/유니버스, 필터, 계산식/지표, 결과 evidence table이 있어야 재현 가능한 데이터 결론으로 취급한다.
- 최종 답변 전에 데이터 한계와 후속 분석 엔진으로 넘긴 근거 ref를 확인한다.

## 공개 호출 방식

```python
import dartlab

dartlab.gather("price", "005930")          # 최신 raw data 보강 (provider·latestAsOf)
dartlab.scan("fields")                       # universe·rank 위치 (횡단 비교)
dartlab.Company("005930").panel("IS")        # 단일 종목 원자료 (항목 x 기간 격자)
```

## 호출 동작

- Company, gather, scan이 사용할 원자료 위치와 freshness를 확인한다. 분석 결론보다 source table과 latestAsOf를 먼저 만든다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- dataset/table ref 또는 DataFrame을 반환한다. 핵심 컬럼은 provider, dataset, entity, period/date, metric, value, latestAsOf다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.


