---
id: engines.industry.supplyChain
title: Industry — 밸류체인 그래프 (supplyChain)
category: engines
kind: curated
scope: builtin
status: observed
purpose: 산업 내 공정 단계 (stage) 와 stream 분류 (upstream/midstream/downstream) 의 SSOT — 산업 매핑 데이터 (taxonomy.json + nodes.json) 의 공정 순서 + 상하류 위치를 코드·답변에서 동일 어휘로 인용.
whenToUse:
  - 밸류체인
  - supply chain
  - 공정 단계
  - upstream / midstream / downstream
  - 상류·중류·하류
  - 산업 지도
  - 전공정 / 후공정 / 장비
  - stream 분류
sourceRefs:
  - dartlab://skills/engines.industry.supplyChain
capabilityRefs:
  - industry
knowledgeRefs:
  - engines.industry
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
linkedSkills:
  - engines.industry
  - engines.viz
---

## 엔진 역할

`industry` 엔진의 *밸류체인 구조* sub-axis. 한 산업의 공정 단계 (stage) 와 stream 분류 (upstream/midstream/downstream) 를 단일 어휘로 정의한다. 본 spec 의 stage·stream enum 이 industryBadge.stream / `Company.industry().stage` 의 SSOT.

## 공개 호출 방식

```python
import dartlab

# 1. 산업 내 공정 단계 + 종목
nodes = dartlab.industry("semiconductor")
# → DataFrame: 공정 · 공정명 · 종목코드 · 종목명 · 역할 · 위치

# 2. stage 필터
fab_only = dartlab.industry("semiconductor", stage="fab")

# 3. 단일 종목 stage + stream (자동 부착)
c = dartlab.Company("005930")
badge = c.panel("IS").data.industryBadge
badge.stage      # "fab"
badge.stream     # "midstream"
```

## 호출 동작

1. `dartlab.industry(industryId)` → 공정 단계 (`공정` 컬럼) + 산업 내 stream 위치 (`위치` 컬럼) 동시 노출.
2. `Company.industry()` → 단일 종목의 `stage` (공정 ID) + `stageLabel` (한글 공정명) 반환. industryBadge 는 `stream` 도 추가 (upstream/midstream/downstream).
3. stage 와 stream 의 관계 — *stream 은 stage 의 grouping*. 예: 반도체 (`semiconductor`) 에서 `equipment`/`material`/`design` = upstream, `fab` = midstream, `oSat`/`module` = downstream.
4. 매칭 신뢰도 (`confidence`) 가 0.5 미만이면 stage·stream 도 신뢰 한계 명시.

## 대표 반환 형태

```text
dartlab.industry("semiconductor")
→ DataFrame
   공정 : str               # stage ID (fab / oSat / equipment / design / material / module)
   공정명 : str             # 한글 공정명 (전공정 / 후공정 / 장비 / ...)
   종목코드 : str
   종목명 : str
   역할 : str
   위치 : str               # upstream / midstream / downstream
```

```text
Company("005930").industry()
→ dict
   stage : str              # 공정 ID
   stageName : str          # 한글 공정명
   role : str               # 역할 (제조 / 설계 / 장비 공급 / ...)
   stream : str             # upstream / midstream / downstream
```

## stream enum 정의

| stream | 의미 | 반도체 예시 stage | 자동차 예시 stage |
|---|---|---|---|
| **upstream** | 원료·장비·설계 | equipment / material / design | 부품 / 소재 |
| **midstream** | 핵심 제조 | fab | 완성차 조립 |
| **downstream** | 가공·조립·유통 | oSat / module | 판매·정비 |

stream 분류 SSOT 는 `nodes.json` 의 `위치` 컬럼 — 운영자 수동 갱신 (taxonomyOps 참조).

## 기본 실행 순서

1. **단일 종목 stage / stream** — `industryBadge.stage` + `industryBadge.stream` 그대로 인용.
2. **산업 전체 stage 표** — `dartlab.industry(industryId)` 의 `공정` · `위치` 컬럼.
3. **특정 stage peer 추출** — `dartlab.industry(industryId, stage="...")`.
4. **시각화** — `engines.viz.peerMatrix` 가 stage × peer 격자 양식 표준.

## 기본 검증

- `위치` 컬럼 값이 enum (upstream/midstream/downstream) 안.
- stage ID 가 산업별 정의된 enum 안 (반도체 6 종 / 자동차 5 종 / ...).
- 같은 종목의 stage·stream 매칭 일관성 — `Company.industry()` ↔ `industryBadge` 동일.

본 spec 은 공개 실행 문서다. stream/stage enum 또는 컬럼명이 변경되면 본 파일을 같은 변경에서 갱신한다.

## 관련

- [engines.industry](/skills/engines.industry) — base SKILL
- [engines.industry.peers](/skills/engines.industry.peers) — 같은 stage peer 추출
- [engines.industry.taxonomyOps](/skills/engines.industry.taxonomyOps) — taxonomy.json/nodes.json 운영자 갱신 절차
- [engines.viz.peerMatrix](/skills/engines.viz.peerMatrix) — stage × peer 격자 표준
