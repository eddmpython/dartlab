---
id: operation.coreloop
title: Core Loop — 자가개선 루프 운영 SSOT
kind: curated
scope: builtin
status: observed
category: operation
purpose: Core Loop — 자가개선 루프 운영 SSOT 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - Core Loop — 자가개선 루프 운영 SSOT
  - coreloop
  - 1. Legacy 5 Phase — O · P · R · F · A
  - 2. Phase O — 기록 인프라
  - legacy 구현 위치
  - 출력
  - v2 스키마
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
  - operation.agentAudit
sourceRefs:
  - dartlab://skills/operation.coreloop
procedure:
  - 1. Legacy 5 Phase — O · P · R · F · A 기준을 확인한다.
  - 2. Phase O — 기록 인프라 기준을 확인한다.
  - legacy 구현 위치 기준을 확인한다.
  - 출력 기준을 확인한다.
  - v2 스키마 기준을 확인한다.
  - 아래 경로는 old AI runtime 기준이며 새 AI/skills 경로의 production 표준이 아니다.
  - 새 구현 위치는 `src/dartlab/ai` 와 `src/dartlab/skills` 의 trace, verify, provider, MCP 계약을 따른다.
  - compatibility 코드가 필요하면 새 `AuditPacket`/`ImprovementCandidate` 스키마로 어댑트한다.
  - I/O 실패 조용 무시 (응답 경로 보호).
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
  - Core Loop — 자가개선 루프 운영 SSOT 규칙 확인
  - coreloop 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: coreloop
  format: markdown
lastUpdated: '2026-08-09'
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

- 1. Legacy 5 Phase — O · P · R · F · A 기준을 확인한다.
- 2. Phase O — 기록 인프라 기준을 확인한다.
- legacy 구현 위치 기준을 확인한다.
- 출력 기준을 확인한다.
- v2 스키마 기준을 확인한다.
- 아래 경로는 old AI runtime 기준이며 새 AI/skills 경로의 production 표준이 아니다.
- 새 구현 위치는 `src/dartlab/ai` 와 `src/dartlab/skills` 의 trace, verify, provider, MCP 계약을 따른다.
- compatibility 코드가 필요하면 새 `AuditPacket`/`ImprovementCandidate` 스키마로 어댑트한다.
- I/O 실패 조용 무시 (응답 경로 보호).

## 하위 사이클

신규 분석 skill 을 자율 발굴·검증·등재하는 6 단계 인큐베이션 사이클과 audit 회환 절차는 [operation.skillDevelopmentLoop](/skills/operation.skillDevelopmentLoop) 가 SSOT. coreloop 은 메타 흐름만 다루고, 사이클 본문은 그쪽에서 정의한다.

## audit runner 스크립트

표준 질문 세트를 배치 실행해 AI 응답을 저장하는 runner 3 종. 모두 `data/audit/ai/{YYYY-MM-DD}/` 또는 `data/dart/auditAi/` 에 원문 + trace 를 남긴다. 품질 P/T/C/V 판정은 자동 메트릭 없이 *사람이 직접 읽고* 한다.

| 스크립트 | 호출 경로 | 질문 소스 | SSOT 적합성 |
|---|---|---|---|
| `tests/ai/runners/serverAskAudit.py` | `POST /api/ask` (httpx) | 코드 내장 `QUESTIONS[]` | **SSOT 적합**. 서버 경유 → 미들웨어·직렬화·streaming·tool_choice 매핑 전부 통과. 실사용자 경로 동일 |
| `tests/ai/runners/aiAudit.py` | 인라인 `dartlab.ask()` (in-process) | 코드 내장 `_STANDARD_SET` 9 문항 | **참고용** — 서버 경유 마이그레이션 전까지. SSOT audit 결론으로 인용 금지 |
| `tests/ai/runners/auditAi.py` | 인라인 `dartlab.ask()` (in-process) | `data/dart/auditAi/questions.json` | **참고용** — `aiAudit.py` 와 동질, 질문 외부화 차이만. SSOT audit 결론으로 인용 금지 |

표준 절차: `serverAskAudit.py` 만 SSOT audit 결론으로. 인라인 runner 2 종은 (a) provider/네트워크 미설치 환경 빠른 sanity check (b) 서버 미기동 상태 회귀 비교 용도로만. 둘 다 trace 가 서버 미들웨어를 건너뛰어 `tool_choice`/streaming/직렬화 회귀를 잡지 못한다.

품질 등급 P/T/C/V 정의, 서버 기동 절차, C/V 발생 시 중단 기준은 `operation.agentAudit`에서 확인한다.

## audit 보조 스크립트

audit jsonl 후처리·판정 누적·playbook 저장 보조 스크립트. 모두 `data/audit/` 또는 KnowledgeDB 와 연동.

| 스크립트 | 역할 |
|---|---|
| `tests/ai/runners/readAiJudgments.py` | `data/audit/ai-judgment/*.jsonl` 의 P/T/C/V 판정 요약. PowerShell 출력 인코딩 우회용 Python UTF-8 reader. `--file` 옵션으로 특정 날짜만 |
| `tests/ai/runners/sanitize_audit.py` | `data/audit/ai-ask/*.jsonl` 민감정보 마스킹 — 공개 공유 (블로그·repo PR) 전 필수. `--mode hash\|drop\|mask\|check`. mask 모드는 종목명·이메일·URL 만 |
| `tests/ai/runners/quickQualityAudit.py` | 4 시나리오 × tool 다양성 + override 재호출 + pastInsight/sectorInsights 활용 체크. 인라인 `runAsk` 호출 (in-process) — 참고용, SSOT audit 결론으로 인용 금지 |
| `src/dartlab/skills/learnRecipe.py` | 검증된 코드 패턴 → KnowledgeDB `playbook` 테이블 (source="recipe") 수동 저장. HF push 시 자동 공유, 사용자 auto_pull 로 다운로드. `--list` / `--batch seed.json` / 단일 (질문, 코드) 인자 |
| `src/dartlab/skills/cleanup_knowledge_db.py` | W-D2 재설계 — 검증 게이트 없이 쌓인 오염 정리. `insights(source="live")` 전량 drop / `insights(source="audit")` 는 auditAnalysis md 실존만 이관 / `playbook` 은 `quality≥0.75 AND success_count≥5` 만 유지 / `executions` 는 `question_hash` 치환 + 최근 30 일 유지. 새 스키마 컬럼 `evidence_ref` + `quality_gate` 부착. `--confirm` 없으면 dry-run |
