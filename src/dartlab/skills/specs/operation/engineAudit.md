---
id: operation.engineAudit
title: Engine Audit — 엔진 기능 점검 규격
kind: curated
scope: builtin
status: observed
category: operation
purpose: Engine Audit — 엔진 기능 점검 규격 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - Engine Audit — 엔진 기능 점검 규격
  - engineAudit
  - 1. 목적 — 엔진 end-to-end 통로를 점검한다
  - 2. 점검 범위 — 체크리스트로 간다
  - Company facade
  - panel · select
  - analysis (L2)
inputs:
  - 작업 목적
  - 대상 엔진 또는 실행 환경
  - 검증 범위
outputs:
  - selected skill
  - capability/docstring handoff
  - verification gate
capabilityRefs: []
toolRefs:
  - search_reference
knowledgeRefs:
  - start.dartlabSkillOs
sourceRefs:
  - dartlab://skills/operation.engineAudit
procedure:
  - 1. 목적 — 엔진 end-to-end 통로를 점검한다 기준을 확인한다.
  - 2. 점검 범위 — 체크리스트로 간다 기준을 확인한다.
  - Company facade 기준을 확인한다.
  - panel · select 기준을 확인한다.
  - analysis (L2) 기준을 확인한다.
  - Company 생성 → panel · select · analysis · credit · scan · story · macro · gather · quant 전체 통로 작동 확인.
  - 주요 종목 (KR + US) 에서 반환값이 기대 형식인지.
  - 새 기능 추가·데이터 갱신·리팩토링 후 회귀 감지.
  - AI audit 전에 선행 점검 (엔진 깨진 채 AI 돌리면 무의미).
requiredEvidence:
  - skillRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 작업 경로
  - 확인한 근거
  - 검증 결과
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
    status: supported
    notes: []
failureModes:
  - Skill OS 검색 없이 과거 문서 경로를 직접 찾음
  - API schema를 skill 본문에 중복해 docstring/capability와 어긋남
  - 검증 게이트 없이 변경 또는 답변을 완료 처리함
forbidden:
  - 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다.
  - 공개 호출 방식, 대표 반환 형태, 오류/제한 동작을 skill과 불일치한 채 방치하지 않는다.
examples:
  - Engine Audit — 엔진 기능 점검 규격 규칙 확인
  - engineAudit 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: engineAudit
  format: markdown
lastUpdated: '2026-05-03'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## Skill OS 흡수 규칙

- 이 skill이 공식 진입점이다. 삭제된 운영 문서 경로를 다시 안내하지 않는다.
- 공개 호출 방식과 대표 반환 형태는 skill에서 확인하고, 세부 필드는 capability/docstring으로 검산한다.
- 분석이나 변경 결과는 ref, 실행 로그, 테스트 결과로 검증한다.

## 실행 순서

- 1. 목적 — 엔진 end-to-end 통로를 점검한다 기준을 확인한다.
- 2. 점검 범위 — 체크리스트로 간다 기준을 확인한다.
- Company facade 기준을 확인한다.
- panel · select 기준을 확인한다.
- analysis (L2) 기준을 확인한다.
- Company 생성 → panel · select · analysis · credit · scan · story · macro · gather · quant 전체 통로 작동 확인.
- 주요 종목 (KR + US) 에서 반환값이 기대 형식인지.
- 새 기능 추가·데이터 갱신·리팩토링 후 회귀 감지.
- AI audit 전에 선행 점검 (엔진 깨진 채 AI 돌리면 무의미).
- AI 답변 품질 audit은 자동 점수로 통과 처리하지 않는다. `/api/ask` 서버 경유 원문 답변, refs, events, meta를 저장한 뒤 사람이 직접 읽어 P/F와 root cause를 기록한다.
- 실패 root cause는 `skillSearch`, `generatedSpecSearch`, `planEvidence`, `engineCall`, `runPython`, `verifyAnswer`, `composeAnswer`, `publicEvent/UI` 중 하나로 귀속한다.
- 직접 원문 review 전에는 “품질 통과” 또는 “완료”를 주장하지 않는다.

## 실행 스크립트

| 스크립트 | 역할 |
|---|---|
| `tests/ai/runners/engineAudit.py` | dartlab 엔진 end-to-end 기능 점검 batch runner. `--stock 005930` 단일, `--quick` 핵심만, 인자 없으면 전체 종목. 결과 `data/audit/engine/{YYYY-MM-DD}/{stockCode}.json` + `report.md`. AI audit 선행 점검용 — 엔진 깨진 채 AI 돌리면 무의미 |


