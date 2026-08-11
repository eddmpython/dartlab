---
id: runtime.promptingPatterns
title: Prompting Patterns — 6 막 인과 + axis 카탈로그
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: dartlab 답변 prompt 패턴 카탈로그 — 6 막 인과 (회사분석 한정), recipe 카탈로그 호출 시 prompt 변형, untrusted wrap 가이드, evidence GATE 통과 강행 prompt. agent.py system prompt 의 변형 SSOT.
whenToUse:
  - prompting patterns
  - 6 막 인과
  - prompt 변형
  - system prompt
  - 답변 패턴
inputs:
  - 사용자 질문 분류
  - recipe / engine axis
outputs:
  - prompt 변형 (회사분석 / 매크로 / 횡단)
toolRefs: []
knowledgeRefs:
  - runtime.workbenchEvidenceFlow
  - engines.story
sourceRefs:
  - dartlab://skills/runtime.promptingPatterns
requiredEvidence:
  - skillRef
  - executionRef
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
  - engines.story
  - runtime.workbenchEvidenceFlow
  - runtime.untrustedContent
---

## 분류

### 1. 회사분석 — 6 막 인과 (engines.story)

회사 단위 답변 한정. 모든 질문에 6 막을 강제하지 않는다. 회사분석 의도 (`Company.panel` / `Company.analysis`) 와 `engines.story` / `operation.sixActsAnalysis` 경로에서만 적용한다.

```
1막 — 산업 위치 (engines.industry.peers + supplyChain)
2막 — 재무 현황 (engines.analysis 22 axis)
3막 — 이익품질 (engines.analysis.forensics)
4막 — 자금조달 (engines.credit + altman)
5막 — 종합평가 (piotroski + qmj + valuation)
6막 — 시장분석 (engines.quant + scan)
```

### 2. 매크로 — axis 가이드 우선

`dartlab.macro()` 가이드 12 axis 먼저 → 사용자 의도 매칭 axis 선택 → 단위/dateRef 강행.

### 3. 횡단 (scan) — universe 정의 강행

universe 명시 (default KOSPI200 / 사용자 보유 list) → 횡단 axis 결과 정렬 → top N 인용.

### 4. recipe 호출 — 카탈로그 SSOT 인용

recipe id (`recipes.macro.qualityMacroBeta` 등) 명시 호출 → 결과의 `## 연계 절차` 다음 단계 자동 제안.

## 강행 prompt 요소

모든 prompt 변형에 다음 4 요소 강행:

1. **단위 명시** (% / bp / index / 원).
2. **dateRef** (YYYY-MM-DD 또는 YYYY-MM).
3. **evidence GATE** (skillRef / tableRef / valueRef 묶음).
4. **untrusted wrap** (외부 본문 시 sentinel 마커).

## 안티패턴

- 모든 질문 6 막 강제 (회사분석 외 trigger 금지).
- "최신" 단어 사용 시 dateRef 누락 (search dataAsOf stale 회귀).
- recipe 호출 결과 dump (`## 연계 절차` 무시 회귀).

## 기본 검증

본 spec 패턴 변경 시 agent.py system prompt 동시 갱신 (단일 SSOT 강행).
