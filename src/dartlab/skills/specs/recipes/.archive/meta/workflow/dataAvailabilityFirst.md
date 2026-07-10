---
id: recipes.meta.workflow.dataAvailabilityFirst
title: 데이터 가용성 우선 점검 (수집 전 확인 → 누락 시 gather/update)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 분석 시작 전 필요한 데이터 (finance/docs/report/price) 가 local 에 있는지 확인하고 누락 시 수집을 트리거하는 절차. emit_result 실패 사이클 예방. 트리거 — '데이터 있나 확인', '분석 전 데이터 점검', '수집 누락 체크'.
whenToUse:
  - 데이터 가용성
  - 데이터 있는지
  - 분석 전 확인
  - 데이터 수집
  - 누락 데이터
  - inspect dataset
  - schema 확인
linkedSkills:
  - engines.company
  - engines.gather
  - engines.data.foundation
toolRefs:
  - InspectDataset
  - EngineCall
requiredEvidence:
  - skillRef
  - datasetRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.evidenceCoverage"
visualGuidance:
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."

forbidden:
  - 분석 시작 후 데이터 누락 발견하고 추측으로 메우기 금지 — 시작 전 점검.
  - 결손 데이터 (None) 0 으로 채워서 분석 진행 금지.
  - 데이터 가용성 점검 결과 명시 없이 분석 결과 단정 금지.
  - InspectDataset 결과의 schema 확인 누락 금지.
failureModes:
  - 가용 토픽 list 만 보고 실제 데이터 결손 무시"
  - schema 변경 (snakeId 매핑) 시점 차이로 mapping 실패
  - update() / gather() 후 새 데이터 캐시 hit 못함
  - 일부 분기 결손 (DART late filing) 무시"
  - 데이터 가용성 점검 결과를 분석 본문에 누락
examples:
  - 분석 시작 전 토픽 / schema 점검
  - 결손 데이터 발견 시 gather 트리거
  - InspectDataset + schema 검증
  - 데이터 점검 → 분석 → 결과
lastUpdated: '2026-05-13'
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
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

topics = c.panel  # 가용 토픽 목록
# InspectDataset 으로 schema 확인
# 누락 시 c.update() 또는 c.gather('price') 호출
```

## 호출 동작

분석 의도 → 필요한 dataset 식별 → InspectDataset 으로 schema/최신 시점 확인 → 누락 시 update/gather 트리거.

1. 회사 진입
2. c.panel — 가용 토픽 목록
3. InspectDataset — 핵심 dataset 확인 (Company.show:code:BS 등)
4. (누락 시) c.update() — finance/docs/report 증분 수집
5. (가격 필요 시) c.gather("price") — KR/US 주가

## 대표 반환 형태

- `skillRef` 1 (data foundation)
- `datasetRef` 3+ (BS / IS / CF 또는 price / macro)
- 답변 본문: 가용 vs 누락 dataset 표

## 연계 절차

1. engines.company — 회사 진입 + topics 조회
2. engines.data.foundation — 데이터 기본기 확인
3. engines.gather — 누락 데이터 수집

## 기본 검증

- 가용 dataset / 누락 dataset 명시.
- schema (컬럼 + dtype + 최신 시점) 표시.
- update 호출은 비용 (네트워크) — 누락 명확할 때만.
