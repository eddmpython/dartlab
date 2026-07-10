---
id: recipes.fundamental.credit.creditRatingMigration
title: Credit Rating Migration — 신용등급 변동 추적
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: KR 신용평가 3 사 (NICE/KIS/한신평) 신용등급 변동 추적 + dCR rating delta 비교. 등급 하향 = 진짜 신호 (lag 큼 그러나 강도 강). **status=drafted — 신용평가 3 사 API 인프라 선결**. 트리거 — '신용등급 변동', 'rating migration', '등급 하향', 'rating downgrade', 'dCR rating delta'.
whenToUse:
  - credit rating migration
  - 신용등급 변동
  - rating downgrade
  - rating upgrade
  - dCR rating
linkedSkills:
  - engines.credit
  - engines.scan
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - engines.viz.tableBackedChart
gap:
  primary:
    - credit
    - scan
testUniverse:
  market: KR
  stockCodes:
    - "005930"
  asOfPolicy: latest
falsifier:
  description: 등급 하향 후 30d 회사채 spread reaction 0 = market efficient + signal lag 없음 = recipe 가치 약.
  pythonCheck: |
    assert avg_spread_reaction_30d >= 0
expectedNovelty:
  - ratingNice
  - ratingKis
  - ratingDcr
  - migrationDelta
forbidden:
  - 단일 평가사 등급 변동 = 절대 신호 X — 3 사 합의 권장.
  - dCR vs 외부 rating divergence 단방향 해석 X (모델 차이 + 정보 가용성 차이).
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: limited
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
---

## 공개 호출 방식

```python
import dartlab
c = dartlab.Company("005930")
dcr = c.credit().get("rating")
# external rating 3 사 (NICE/KIS/한신평) — 별 endpoint
```

## 호출 동작

3 사 rating + dCR rating + 직전 12 개월 migration history + delta.

## 대표 반환 형태

dict — `ratingNice + ratingKis + ratingHankyung + ratingDcr + migration12m + consensusDelta`.

## 연계 절차

1. 본 recipe → rating migration 추적.
2. 하향 cluster (3 사 중 2 사 하향) → spread widening 사전 detection.
3. dCR vs external divergence → forensics 검토.
