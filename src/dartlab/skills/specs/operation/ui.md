---
id: operation.ui
title: UI 엔진 (L4 표현 계층)
kind: curated
scope: builtin
status: observed
category: operation
purpose: UI 엔진 (L4 표현 계층) 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - UI 엔진 (L4 표현 계층)
  - ui
  - 1. 한눈에 보기
  - 2. 디렉토리 구조
  - 3. 빌드
  - 4. 서버 연동 — `_ui_path.py::resolve_ui_build_dir()` 단일 함수로 경로 해석한다
  - UI 빌드 경로 해석 우선순위
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
  - operation.aiProductReplatform
sourceRefs:
  - dartlab://skills/operation.ui
  - dartlab://skills/operation.aiProductReplatform
procedure:
  - 1. 한눈에 보기 기준을 확인한다.
  - 2. 디렉토리 구조 기준을 확인한다.
  - 3. 빌드 기준을 확인한다.
  - 4. 서버 연동 — `_ui_path.py::resolve_ui_build_dir()` 단일 함수로 경로 해석한다 기준을 확인한다.
  - UI 빌드 경로 해석 우선순위 기준을 확인한다.
  - '`/assets/*` → `{UI_BUILD}/assets/`.'
  - 나머지 → `{UI_BUILD}/index.html` (SPA fallback).
  - '`ensure_ui_build()` — GitHub ZIP 다운로드 제거. wheel 설치 후 `index.html` 존재만 확인, 없으면 `--force-reinstall`.'
  - '`runner.rs` — `DARTLAB_UI_DIR` 환경변수를 서버 프로세스에 주입.'
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
  - UI 엔진 (L4 표현 계층) 규칙 확인
  - ui 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: ui
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

## AI 채팅 UI 계약

- AI 제품 바탕 교체의 상세 SSOT는 `operation.aiProductReplatform`이다. `operation.ui`는 UI 표현 계층 규칙만 보완한다.
- 공식 제품 경로는 `DartLab App → /api/ask stream → Agent Gateway → Agent Runtime → 설치형 agent CLI → DartLab MCP`다.
- UI 표면은 LibreChat식 conversation/message parts 모델을 따른다. DartLab 브랜드, workspace, evidence, artifact viewer는 유지하되 채팅 본문은 message parts만 렌더한다.
- UI와 엔진 사이의 공개 stream은 AG-UI compatible event allowlist만 허용한다. 내부 kernel trace는 Agent Gateway에서 public event로 변환하고, raw trace는 Evidence/journal에만 저장한다.
- 허용 public event는 `TEXT_MESSAGE_*`, `TOOL_CALL_*`, `STATE_*`, `ACTIVITY_*`, `RUN_FINISHED`, `RUN_ERROR`다. 이 목록 밖 이벤트가 채팅 UI로 직접 들어오면 계약 위반이다.
- local chat과 terminal ask는 공통 `AiPort`를 통해 `/api/ask` 또는 Agent Gateway를 사용한다. provider별 transport를 UI에 만들지 않는다.
- Runtime Center는 `/api/agent/*` adapter 하나로 설치 상태, MCP 상태, 명시적 digest 승인, runtime 선택을 제공한다. provider API key와 OAuth 입력란은 두지 않는다.
- 분석형 질문도 별도 고정 Graph나 Loop로 우회하지 않고 같은 Agent Runtime에 analysis capsule을 전달한다.
- 채팅 본문은 최종 답변, 짧은 activity 로그, 실제 코드/시각화 실행 카드, 실패 notice, source 요약만 렌더한다.
- raw prompt, raw tool args/result JSON, 내부 trace JSON, `Agent Trace`, `투명성` 박스는 채팅 본문에 렌더하지 않는다.
- Evidence 패널은 source refs, datasets, raw tool input/output, verification, artifact를 분리해서 보관한다.
- 서버 SSE의 `activity` 이벤트가 사용자용 진행 표면의 정규 계약이다. legacy `reference`, `inspect`, `execute`, `verify`, `tool_*` 이벤트는 activity/message parts로 변환만 하고 직접 카드로 노출하지 않는다.
- 내부 tool id는 채팅 본문에 snake_case로 노출하지 않는다. 기본 표시명은 `replaceAll("_", " ")`를 적용하고, activity 문구는 `search reference 실행함`, `read context 실행함`, `inspect dataset 실행함`, `run python 실행함`, `compile visual 실행함`, `verify 실행함` 형식을 사용한다.
- 진행 중에는 최근 6개 activity만 보이고, 완료 후에는 `명령어 N개 실행` 한 줄로 접는다.
- 빈 chunk, 검색-only, tool 실패 은폐, 정형 ref 없는 계산 답변은 성공 outcome으로 release하지 않는다.
- evidence chip을 렌더한 것만으로 verified를 기록하지 않는다. 사용자가 exact ref의 `근거 확인`을 실행하고 같은 outcome receipt가 200으로 검증된 뒤에만 Product Outcome을 승격한다.

## UI 런타임 데이터층 — 단일 작업대 SSOT + 공통배선

데이터층의 SSOT는 본 문서다. 캐시 정책 세부는 `runtime.cacheStrategy`가 있으면 그쪽을 교차 참조하되 중복 기술하지 않는다.

### 단일 작업대

- 모든 데이터 호출은 `data/fetch.request()` 한 진입점을 통과한다. source는 fetch·URL 문자열·자체 캐시 Map을 직접 갖지 않고, 무엇을(path)·어느 오리진에서(origin)·어떻게 캐시(cache)하는지만 선언한다.
- 오리진은 `data/origins` 레지스트리에 명명 항목으로만 추가한다(HF·range·CF 프록시·news/naver 워커·localApi·duckdbHf·landingJson).
- 캐시·dedup은 어댑터당 `RuntimeCache`·`RequestDedup` 단일 인스턴스를 코어가 만들어 주입한다. 전역 싱글턴은 두지 않는다.

### 공통배선 default

- 터미널과 공유 surface는 공개·로컬 공통배선을 기본으로 한다. 로컬은 명시적 로컬 전용이 아니면 공개 HF source를 재사용한다.
- 로컬 앱(dev)은 `:8400` 백엔드 없이 정적 HF로 떠야 정상이다. `/api`(localApi 오리진)는 라이브 provider·AI 스트림·공시뷰어 격자 같은 실제 로컬 전용 호출만 사용한다. 로컬 전용 호출은 `adapters/local/api` 게이트 한 곳에만 둔다.

### 신선도 캐시

- 캐시 TTL은 오리진별로 차등한다. 신선도 데이터(`recent.parquet`·naver fresh tail)는 짧은 TTL 또는 무 TTL을 쓰고, 일괄 캐시는 두지 않는다.

### 신규 추가 규칙

- 새 데이터 소스는 source에 `request()` 호출 한 함수로 추가한다. 새 오리진은 레지스트리 항목 1개, 새 로컬 엔드포인트는 api 게이트 카탈로그 1줄로 추가한다.
- source 안에서 raw fetch·직접 URL·`new Map` 캐시를 신설하지 않는다. `tests/audit/checkUiDataWiring`이 신규 위반을 차단한다(baseline 부채원장 대비 증가 0 강제).

## 실행 순서

- 1. 한눈에 보기 기준을 확인한다.
- 2. 디렉토리 구조 기준을 확인한다.
- 3. 빌드 기준을 확인한다.
- 4. 서버 연동 — `_ui_path.py::resolve_ui_build_dir()` 단일 함수로 경로 해석한다 기준을 확인한다.
- UI 빌드 경로 해석 우선순위 기준을 확인한다.
- `/assets/*` → `{UI_BUILD}/assets/`.
- 나머지 → `{UI_BUILD}/index.html` (SPA fallback).
- `ensure_ui_build()` — GitHub ZIP 다운로드 제거. wheel 설치 후 `index.html` 존재만 확인, 없으면 `--force-reinstall`.
- `runner.rs` — `DARTLAB_UI_DIR` 환경변수를 서버 프로세스에 주입.

