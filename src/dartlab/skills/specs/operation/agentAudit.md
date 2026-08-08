---
id: operation.agentAudit
title: Agent Audit — 답변 품질 회귀 측정 절차
kind: curated
scope: builtin
status: drafted
category: operation
purpose: DartLab 에이전트 답변 품질 회귀를 P/T/C/V 4단계로 측정하는 공개 운영 SSOT. 회귀 가드는 추적되는 audit와 CI로 자동화한다.
whenToUse:
  - agent audit
  - 에이전트 audit
  - 답변 품질 회귀
  - P/T/C/V
  - prompt verifier
inputs:
  - 답변 sample (jsonl)
  - audit 기준 (P/T/C/V)
outputs:
  - audit 결과 (pass/fail per dimension)
  - 회귀 신호 ledger
toolRefs: []
knowledgeRefs:
  - operation.coreloop
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/operation.agentAudit
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
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - operation.coreloop
  - runtime.workbenchEvidenceFlow
---

## P/T/C/V 4 단계

| 단계 | 검사 | pass 기준 |
|---|---|---|
| **P** (Prompt) | system prompt 변형 정합 | promptingPatterns 패턴 안 |
| **T** (Tool calls) | 도구 선택 + 순서 정합 | toolComposition 5 분류 안 |
| **C** (Compliance) | 강행 룰 (단위/dateRef/wrap) | 4 강행 요소 100% |
| **V** (Verifier) | evidence GATE + grounding | EvidenceGate pass + GroundingCheck score ≥ 0.8 |

## 절차

```bash
# 1. 답변 sample 수집 (production 무작위 100 건)
uv run python -X utf8 -m dartlab.audit.collect --n=100 --out=audit/samples.jsonl

# 2. P/T/C/V 4 차원 평가
uv run python -X utf8 -m dartlab.audit.run --in=audit/samples.jsonl --out=audit/report.json

# 3. 회귀 신호 ledger (전 cycle 대비)
uv run python -X utf8 -m dartlab.audit.compare --prev=audit/2026-05.json --curr=audit/2026-06.json
```

## 강행 룰

1. audit 실행 = 운영자 트리거 (cron 없음 — memory ai_audit 패턴 유지).
2. 4 차원 모두 측정 (선택적 dimension X).
3. ledger append-only (역사 보존).
4. 회귀 신호 발생 → 별 commit 으로 개별 fix.

## 안티패턴

- audit 자동 cron 도입 (운영자 결정 우회).
- 단일 dimension 만 평가 후 pass 단언.
- 회귀 신호 batch fix (개별 commit 강행).

## 기본 검증

- audit cycle 후 4 차원 모두 측정 결과 commit.
- 회귀 신호 ledger 변동 → fix commit 동행.
- memory ai_audit.md 의 절차와 본 spec 일관성 강행.
