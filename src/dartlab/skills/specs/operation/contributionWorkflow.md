---
id: operation.contributionWorkflow
title: 기여 작업 흐름과 커밋 규칙
kind: curated
scope: builtin
status: observed
category: operation
purpose: DartLab 변경 작업에서 코드 규칙, 검증 범위, 커밋 방식을 일관되게 적용한다.
whenToUse:
  - 기여 작업 흐름
  - 커밋 규칙
  - 코드 변경 전 운영 규칙 확인
  - 공개 산출물 작성 규칙
inputs:
  - 변경 목적
  - 변경 대상 파일
  - 검증 범위
outputs:
  - 적용한 운영 규칙
  - 검증 결과
  - 커밋 단위와 메시지
capabilityRefs: []
toolRefs:
  - git
  - test-lock
knowledgeRefs:
  - start.dartlabSkillOs
  - operation.code
  - operation.architecture
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.contributionWorkflow
procedure:
  - start.dartlabSkillOs에서 공식 Skill OS 진입점을 확인한다.
  - operation.code, operation.architecture, operation.testing 중 변경 범위에 맞는 규칙을 먼저 읽는다.
  - 변경은 한 논리 단위로 묶고, unrelated dirty worktree는 되돌리지 않는다.
  - 검증은 변경 범위에 맞게 최소 충분하게 실행하고 결과를 남긴다.
  - 커밋은 명시 경로만 포함하고 한국어 메시지로 남긴다.
requiredEvidence:
  - skillRef
  - testRef
  - gitDiffRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 변경 요약
  - 검증 명령과 결과
  - 커밋 메시지
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
    status: unsupported
    notes:
      - 저장소 파일 변경과 git 커밋은 로컬 작업환경에서 수행한다.
failureModes:
  - Skill OS 규칙 확인 없이 코드 변경을 시작함
  - 전체 add로 unrelated 변경을 커밋에 포함함
  - 검증 결과 없이 완료 처리함
  - 공개 산출물에 도구·모델·작성자 생성 표식을 남김
forbidden:
  - "`git add .` 또는 `git add -A` 로 넓게 staging하지 않는다."
  - unrelated 변경을 되돌리거나 같은 커밋에 섞지 않는다.
  - 커밋 메시지와 공개 문서에 assistant identity, 모델명, vendor명, generated-by 표식을 쓰지 않는다.
  - 실패한 검증을 통과한 것처럼 적지 않는다.
examples:
  - 코드 변경 전 operation.code와 operation.testing을 확인한다.
  - "문서 변경 커밋은 `문서: README Skill OS 안내 정리`처럼 범주와 내용을 함께 적는다."
source:
  type: skill_os
  format: markdown
lastUpdated: '2026-05-13'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 원칙

기여 작업은 Skill OS에서 시작한다. 저장소의 공식 규칙은 `start.dartlabSkillOs`를 통해 찾고, 변경 범위에 맞는 `operation.*` skill을 확인한 뒤 작업한다.

코드 변경은 기존 구조와 책임 경계를 우선한다. 새 abstraction은 중복이나 복잡도를 실제로 줄일 때만 추가하고, unrelated 정리 작업은 같은 변경에 섞지 않는다.

## 코드 규칙

- 식별자와 파일명은 기존 DartLab 규칙을 따른다. Python 함수·메서드·변수·파일명은 camelCase, 클래스는 PascalCase, 모듈 상수는 ALL_CAPS를 기본으로 한다.
- 공개 API, 대표 반환 형태, 오류·제한 동작은 Skill OS와 capability/docstring이 어긋나지 않게 유지한다.
- 계층 경계는 `operation.architecture`를 따른다. L2 엔진 간 직접 import, L1.5 sibling cross import, 표현/전송 helper의 비즈니스 로직 유입을 회귀로 본다.
- provider와 대용량 데이터 경로는 `operation.code`의 메모리-safe 룰을 따른다. eager cross-scan, full dataframe 기본 반환, baseline 증가를 새 코드에 만들지 않는다.

## 검증 규칙

- 테스트는 변경 범위에 맞게 좁게 시작하고, shared behavior나 계층 경계를 건드리면 architecture/audit gate까지 넓힌다.
- 긴 테스트나 pytest 직접 실행이 필요한 경우 `tests/test-lock.sh`를 우선 사용한다.
- Guard Index 관련 회귀 작업은 `operation.testing`, `operation.code`, `operation.architecture`의 절차를 함께 적용한다.
- 실패한 검증은 숨기지 않는다. 기존 실패인지, 이번 변경으로 생긴 실패인지 구분해 기록한다.

## 커밋 규칙

- 커밋은 한 논리 단위로 나눈다. 기능 변경과 생성 산출물 동기화가 분리 가능한 경우 별도 커밋으로 둔다.
- staging은 명시 경로만 사용한다. 예: `git add README.md src/dartlab/skills/specs/operation/contributionWorkflow.md`.
- 전체 staging 명령 (`git add .`, `git add -A`)은 사용하지 않는다.
- 커밋 메시지는 한국어로 작성하고, 변경 범주와 내용을 함께 담는다. 예: `문서: Skill OS 운영 안내 추가`.
- 커밋 메시지와 공개 산출물에는 assistant identity, 모델명, vendor명, generated-by 표식을 남기지 않는다.
- push는 별도 요청이 있을 때만 수행한다.

## 공개 산출물 규칙

README, Skill OS, landing page, blog, JSON index는 사용자가 직접 읽는 공개 산출물이다. 표현은 주체 중립적으로 쓴다.

운영 실패나 폐기 이력은 필요한 경우에만 짧게 남긴다. 내부 사유, 방어적 문구, 도구 중심의 표현보다 현재 운영 원칙과 사용자가 따라야 할 절차를 먼저 적는다.

## PreToolUse hook validator 스크립트

`.claude/hooks/` 가 PreToolUse 시점에 호출하는 검증 스크립트. 룰 위반 시 hook 이 도구 실행 자체를 차단. 운영자↔AI 약속 (메모리·CLAUDE.md) 의 자동 강행 가드.

| 스크립트 | 룰 | 차단 시점 |
|---|---|---|
| `.claude/hooks/check_no_ai_markers.py` | 커밋 메시지 + staged 본문에 AI attribution 마커 (생성 주체 표식 · 협업 표식 등 — 패턴 SSOT 는 해당 스크립트 본문 `BANNED_PATTERNS` 리스트) 금지. 본 spec "공개 산출물 규칙" + [MEMORY.md "주체 중립"](file://C:/Users/MSI/.claude/projects/c--Users-MSI-OneDrive-Desktop-sideProject-dartlab/memory/MEMORY.md) 강행 | git commit |
| `.claude/hooks/validate_ask.py` | `AskUserQuestion` 4 지선다 안티패턴 차단. [CLAUDE.md "사용자 질문 방식"](file://./CLAUDE.md) — 객관식 선택지 = 결정 떠넘김 | `AskUserQuestion` 도구 호출 |
| `.claude/hooks/validate_plan.py` | `ExitPlanMode` 본문 형식 게이트. 영향 파일 / 영향 함수 / 테스트 매핑 / 롤백 4 섹션 + path ≥ 2 강행. 룰 SSOT `memory/conduct.md` 6절 + skill [plan-deep](file://./.claude/skills/plan-deep/SKILL.md) | `ExitPlanMode` 도구 호출 |
| `.claude/hooks/validate_stop_phrase.py` | Stop hook trigger phrase 가드 — 컷오프 / 4 지선다 안티패턴 차단 | Stop hook (응답 종료 시점) |

위반 시 hook 메시지에 룰 SSOT 경로 노출. 위반 회피로 hook 우회 (`--no-verify` 등) 금지 — 우회 시도 자체가 회귀로 카운트.
