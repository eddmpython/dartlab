---
id: runtime.mcp
title: MCP
kind: curated
scope: builtin
status: observed
category: runtime
purpose: MCP 실행 환경의 제약, 시작 절차, 검증 기준을 Skill OS에서 확인한다.
whenToUse:
  - MCP
  - mcp
  - 1. 한눈에 보기
  - 2. 설치 — `.mcp.json` 에 dartlab 서버를 등록한다
  - 자동 설치 (프로젝트 루트에서)
  - 수동 설정 (`.mcp.json`)
  - 3. 실행 경로
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
  - ReadSkill
  - ReadCapability
  - EngineCall
  - RunPython
knowledgeRefs:
  - start.dartlabSkillOs
sourceRefs:
  - dartlab://skills/runtime.mcp
procedure:
  - 1. 한눈에 보기 기준을 확인한다.
  - 2. 설치 — `.mcp.json` 에 dartlab 서버를 등록한다 기준을 확인한다.
  - 자동 설치 (프로젝트 루트에서) 기준을 확인한다.
  - 수동 설정 (`.mcp.json`) 기준을 확인한다.
  - 3. 실행 경로 기준을 확인한다.
  - 상한 5 인스턴스 · TTL 10 분 (`_CACHE_MAX` · `_CACHE_TTL`).
  - LRU 정책. 새 종목 로드 시 가장 오래된 항목 제거.
  - Company 로딩 자체가 수초 걸리므로 같은 종목 반복 질의에 유효.
  - '`ask` · `Company` · `setup` · `collect` · `config` 등 비분석 API.'
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
  - MCP 규칙 확인
  - mcp 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: mcp
  format: markdown
lastUpdated: '2026-08-01'
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

- 1. 한눈에 보기 기준을 확인한다.
- 2. 설치 — `.mcp.json` 에 dartlab 서버를 등록한다 기준을 확인한다.
- 자동 설치 (프로젝트 루트에서) 기준을 확인한다.
- 수동 설정 (`.mcp.json`) 기준을 확인한다.
- 3. 실행 경로 기준을 확인한다.
- 상한 5 인스턴스 · TTL 10 분 (`_CACHE_MAX` · `_CACHE_TTL`).
- LRU 정책. 새 종목 로드 시 가장 오래된 항목 제거.
- Company 로딩 자체가 수초 걸리므로 같은 종목 반복 질의에 유효.
- `ask` · `Company` · `setup` · `collect` · `config` 등 비분석 API.

## 엔진 흡수 contract — MCP 표면이 dartlab 엔진을 어떻게 따라가는가

dartlab 엔진/Skill OS 가 진화해도 MCP 표면이 자동으로 따라가도록 설계된 자동 채널과,
사람이 손대야 하는 수동 touchpoint, 그리고 회귀 가드의 위치를 한곳에 정리한다.

### 자동 채널 — 엔진 변경하면 MCP 코드 손대지 않아도 자동 반영

| 채널 | 어떻게 자동인가 |
|---|---|
| `EngineCall` | capability 카탈로그에 등재된 canonical `dartlab.*` verb·`Company.*` 메서드를 `{apiRef, args}` 로 호출. provider static/class method와 하위호환 helper는 카탈로그에서 제외 |
| `RunPython` | EngineCall 결과의 다단 결합·랭킹·Polars 가공 채널. 단일 dartlab 공개 API 호출을 우회하는 용도가 아님 |
| `ReadCapability` | `reference/capability.loadCapabilities()` 라이브 카탈로그 색인. `engineCallable=true`만 EngineCall 실행 권한이고 false는 공개 문서 참조 전용 |
| `ReadSkill` | `skills/specs/**` 의 모든 skill markdown 자동 색인 (process-lifetime 캐시) |
| `prompts/list` & `prompts/get` | Skill OS 의 `kind: recipe` 카테고리를 prompt 로 자동 노출. arguments 는 skill `inputs` frontmatter 에서 derive |
| `dartlab://skills/{id}` resources | Skill OS 에서 런타임 derive |

### 도구 설계 원칙 — verb=SSOT, 손코딩 도구는 thin 위임

데이터 verb(`compare`·`scan`·`gather`·`Company.*`)는 위 자동 채널(EngineCall·RunPython)로 손코딩 0
에 노출된다. 따라서 새 비교/분석 능력을 위해 손코딩 도구를 또 만들 이유가 거의 없다.

- **verb = SSOT** — 라이브러리 verb 가 단일 진실원. 같은 능력을 MCP 도구가 재구현하지 않는다.
- **손코딩 도구 = thin 오케스트레이터만** — `PeerCompareN`·`DCFValuation` 처럼 *단일 verb 로 표현 못 하는*
  다단 가공(percentile rank·dCR/industry badge·시나리오)만 손코딩한다. 데이터 추출은 verb 또는 단일
  헬퍼(`ai/tools/companyMetrics.companyMetrics`)에 위임한다.
- **자동 generator 금지** — 도구/skill 산출물을 capability 에서 자동 생성하는 도구를 만들지 않는다(운영자
  수기 자산 덮어쓰기 회귀). 자동성은 *런타임 디스패치*(EngineCall)로 얻지 *코드 생성*으로 얻지 않는다.
- **커버리지 경계** — `compare` 재무 셀 모드는 KR 전용(native acode). cross-market(KR+US) 재무가 필요한
  도구는 finance 파사드(`companyMetrics`)를 쓴다 — 순수성 위해 US 커버리지를 희생하지 않는다.

가드: `tests/ai/test_engine_call_reachability.py`(verb 자동경로 lock) ·
`tests/audit/test_aiToolsSingleExtraction.py`(재무 추출 단일점 — facade 추출은 `companyMetrics.py` 한 곳만).

### 수동 touchpoint — 엔진 surface 변경 시 사람이 손대야 함

| 위치 | 언제 |
|---|---|
| `ai/tools/registry._SPECS` / `CANONICAL_V2` | AI tool 정의와 MCP에 공개할 canonical 부분집합 추가/제거 |
| `ai/tools/types.ToolSpec` 의 4 hint | 새 도구의 readOnly/destructive/idempotent/openWorld 분류 |
| `mcp/protocol.mcpAdvertisedToolNames` | `ask + CANONICAL_V2` 광고·실행 allowlist. schema 누락은 fail-closed |
| `ai/tools/registry._LEGACY_NAME_MAP` | Python 내부 호환 alias. MCP 실행 권한은 부여하지 않음 |
| `dartlab/__init__._LAZY_ATTRS` (PEP 562) | 새 top-level `dartlab.X` 모듈 추가 시 등록 |
| `ai/tools/runpythonGuard` import/attribute/path allowlist | RunPython 분석 표면을 추가하거나 차단할 때 |

### Silent drift — 조용히 깨질 수 있는 채널 (가드 1 종)

- **새 Skill OS 카테고리** — `prompts/list` 는 `kind == "recipe"` 로 hardcode 필터. `playbook/`, `scenario/` 같은 새 카테고리 도입 시 prompts 에서 누락되며 외부 LLM 이 알아챌 수 없음.
  - **가드**: `tests/test_mcp.py::test_recipe_skills_all_exposed_as_prompts` invariant. recipe 파일 set ↔ `_recipeSkillsForPrompts()` 반환 set 일치 검증. 이 테스트가 fail 하면 `_recipeSkillsForPrompts()` 의 필터를 새 카테고리 포함하도록 갱신.

### 큰 변화 시 점검 (체크리스트)

엔진 surface 가 큰 폭으로 바뀔 때 (새 엔진 추가 / 기존 엔진 폐기 / 새 Skill OS 카테고리 도입 / capability docstring 표준 개편) 다음을 확인한다.

1. `DARTLAB_TEST_LOCKED=1 pytest tests/mcp/test_mcp.py -q`와 관련 파일별 pytest: 흡수 표면 회귀.
2. 새 카테고리가 들어왔다면 `_recipeSkillsForPrompts()` 의 `kind` 필터 확장 여부 결정.
3. 새 top-level 모듈이라면 `dartlab/__init__._LAZY_ATTRS` 등록 + RunPython 안에서 import 가능한지 확인.
4. capability 추가/변경 = docstring 만 작성. 카탈로그는 `loadCapabilities()` 가 docstring 소스에서 **라이브 빌드**(첫 조회 1 회 캐시)라 재생성·커밋 단계 없음 — 사본이 없어 drift 불가. (옛 `_generated.py` 커밋 + 재생성 단계 + `--check` 게이트는 폐기.)
5. canonical tool 추가/제거 시 `ToolSpec` 의 4 hint 채움 + `tests/test_mcp.py::test_mcp_advertised_tools_carry_annotations` 갱신.
6. **도그푸드 verification**: `uv run python -X utf8 tests/ai/runners/mcp_dogfood_probe.py` 실행. advertised happy path와 non-advertised fail-closed 경계를 함께 확인한다.

