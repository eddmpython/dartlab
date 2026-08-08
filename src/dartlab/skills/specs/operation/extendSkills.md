---
id: operation.extendSkills
title: Skill 확장과 공식 승격 규칙
kind: curated
scope: builtin
status: unverified
category: operation
purpose: 새 분석법, 운영 규칙, 외부 LLM 사용법을 Skills 체계에 추가하고 official 수준으로 승격하는 기준을 정한다.
whenToUse:
  - 새 skill을 추가할 때
  - 운영 규칙을 operation skill로 흡수할 때
  - user skill을 curated skill로 승격할 때
  - 반복 audit 결과를 docstring 또는 SkillSpec에 반영할 때
inputs:
  - 새 절차
  - sourceRef
  - audit result
  - 사용자 확인
outputs:
  - user skill
  - curated skill
  - docstring improvement
  - official promotion decision
toolRefs:
  - ReadSkill
  - GetSkillBody
  - ReadCapability
  - CreateUserSkill
  - EngineCall
  - RunPython
  - SaveArtifact
knowledgeRefs:
  - operation.contributionWorkflow
sourceRefs:
  - dartlab://skills/operation.opsAsSkills
  - dartlab://skills/operation.code
  - dartlab://skills/operation.coreloop
requiredEvidence:
  - sourceRef
  - auditResult
  - userConfirmed
  - executionRef
expectedOutputs:
  - 확장 위치 결정
  - 승격 가능 여부
  - 검증 체크리스트
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
failureModes:
  - 한 번 쓴 질문별 runner를 skill로 고정
  - 검증 없이 official 상태 부여
  - docstring에 있어야 할 API 능력을 SkillSpec에 중복
  - 로컬 user skill 을 official skill 처럼 답변하거나 산출물에 섞음
  - sourceRef 없는 운영 규칙 추가
forbidden:
  - final answer template 저장
  - API schema 복사
  - 사용자 확인 없는 official 승격
  - CreateUserSkill 없이 `.dartlab/skills` user skill 파일을 임의 경로에 작성
  - local user skill 작성 요청을 `src/dartlab/skills/specs` 공식 스펙 변경으로 처리
examples:
  - 새 운영 규칙을 operation skill로 추가하기
  - 반복 분석 절차를 curated skill로 승격하기
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: '2026-08-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 절차

- 새 내용이 엔진 API 능력이면 docstring/capability로 보강한다.
- 새 내용이 여러 엔진을 조합하는 분석 절차면 curated skill 후보로 둔다.
- 새 내용이 테스트, 릴리즈, 문서, UI, 데이터 같은 운영 규칙이면 operation skill로 둔다.
- 프로젝트별 실험은 `.dartlab/skills/**/*.md` user skill로 시작한다.
- 사용자가 "내 스킬을 만들어 넣고 싶다"는 의도를 보이면 `CreateUserSkill` 로 `.dartlab/skills` 아래에만 `kind/scope/category: user`, `status: drafted` 초안을 작성한다. 공식 `src/dartlab/skills/specs` 는 건드리지 않는다.
- 신규 분석 skill 을 자율 발굴·검증으로 만드는 6 단계 사이클과 audit 회환은 [operation.skillDevelopmentLoop](/skills/operation.skillDevelopmentLoop) 가 SSOT (gapSpot → dataSanityCheck → protoSkill → selfRun → redTeam → graduate → auditFeedback). 본 skill 은 graduate 단계의 *승격 규칙* 만 정의한다.
- official 승격은 구조 lint, 서버 audit P, 사용자 확인이 모두 있을 때만 허용한다.
- 승격 후에도 SkillSpec은 schema를 복사하지 않고 capabilityRefs와 sourceRefs로 원천을 연결한다.

## 로컬 user skill 작성 규칙

- 로컬 user skill 은 `CreateUserSkill` 로 만든다. 저장 위치는 `.dartlab/skills/{user.slug}.md` 또는 `.dartlab/skills/incubating/{user.slug}.md` 이며, 공식 산출물 동기화 대상이 아니다.
- `capabilityRefs` 가 있으면 본문과 `toolRefs` 에서 `EngineCall` 을 먼저 둔다. `RunPython` 은 여러 EngineCall 결과 결합, L1.5 helper 확인, 표 정리 같은 `fallback` 절차로만 쓴다.
- `visualRefs` 는 `status: observed` 인 `engines.viz.*` 만 허용한다. 검증되지 않은 viz skill 은 `visualGuidance` 에 후보로도 공식처럼 적지 않는다.
- `ReadSkill(includeUser=true)` 로 검색·사용하되, 답변에서는 `trustTier: localUserDraft` 로 취급한다. 공식 승격 전에는 사용자 로컬 지침이지 DartLab builtin 계약이 아니다.
- official 로 승격하려면 user skill 본문, selfRun 결과, redTeam 결과, 운영자 ack 를 모아 별도 변경으로 `src/dartlab/skills/specs/{category}/` 에 작성하고 산출물을 동기화한다.

## Trigger phrase 작성 규칙

`purpose:` 마지막 문장은 **trigger phrase** — 사용자가 자연어로 어떻게 부를지 1~3 가지 명시.

형식 (em dash `—` 사용 — colon 사용하면 YAML mid-value mapping 으로 해석돼 ScannerError):
```
purpose: ...절차 설명. 트리거 — '오늘 아침', '야간 공시 정리', 'morning note'.
```

원칙:
- 자연어 phrase (한국어 위주, 영문 보조 OK), 사용자가 채팅에 칠 만한 표현.
- 기존 `whenToUse:` array 와 *중복 OK* — `whenToUse` 는 검색 인덱스, `purpose` 끝 문장은 LLM 이 skill 카탈로그를 펼침 시 매칭하는 자연어.
- 1~3 개 — 너무 많으면 LLM 이 false positive 매칭. 가장 자주 칠 표현부터.
- 동의어 그룹 (예: "재무제표 비교 / 회사 비교 / 두 종목 차이") 은 같은 trigger 안에 묶어서.

이유:
- LLM 이 `ReadSkill` 검색 결과를 펼쳐볼 때 `purpose` 본문이 가장 먼저 보이고, 자연어 phrase 매칭이 단어 array (`whenToUse`) 보다 우선 hit.
- whenToUse 는 grep-style 인덱스이고, purpose trigger 는 LLM 의 의도 매칭에 직접 들어간다.

SCHEMA 변경 없음 — `purpose:` 본문 끝에 한 문장 추가만. `lastUpdated` 는 갱신.

신규 cadence recipe (dailyMorningNote · catalystCalendar · thesisTracker) 도 같은 규칙으로 작성.

## Skill 확장 보조 CLI

신규 엔진·axis·recipe 추가는 사용자가 선택한 작업 범위에 맞춰 보조 CLI 로 스켈레톤을 만든 뒤, 운영자·사용자·사용자가 명시적으로 위임한 AI 가 SkillSpec 과 산출물을 함께 정리한다.

```bash
# 새 엔진 (engines.{name})
uv run python -X utf8 src/dartlab/skills/addEngine.py myEngine \
    --title "My Engine" \
    --purpose "myEngine 엔진은 ..."

# 기존 엔진 안 axis sub-spec 추가 (engines.{group}.{axis})
uv run python -X utf8 src/dartlab/skills/addAxis.py {group} {axis} \
    --title "..." --purpose "..."
```

`addEngine.py` 가 준비하는 스켈레톤:

- `src/dartlab/{name}/__init__.py` 스켈레톤 + `__all__`
- `src/dartlab/skills/specs/engines/{name}/SKILL.md` frontmatter 5 필수 + 3 강제 섹션 placeholder

`addAxis.py` (`addEngine.py` 의 축소판 — 새 엔진이 아니라 *기존 엔진 안의 응용 결* 결정) 가 준비하는 스켈레톤:

- `src/dartlab/skills/specs/engines/{group}/{axis}.md` frontmatter + 3 강제 섹션 placeholder

후속 정리 항목:

1. `src/dartlab/__init__.py` re-export
2. `pyproject.toml [tool.importlinter]` contract 추가
3. `operation.architecture` L2 계층 표 1 줄
4. SKILL.md 3 강제 섹션 본문 채우기

`--dry-run`으로 미리 본다. axis, recipe, operation, start, runtime sub-spec은 `src/dartlab/skills/SCHEMA.md`의 수동 4단계 절차를 따른다.

## 신규 frontmatter 필드 8 종 (Skill Graph 모델)

`SkillSpec` 에 다음 필드 추가됨 (모두 default 값, backward-compatible):

| 필드 | 타입 | 의미 |
|---|---|---|
| `predecessors` | `list[str]` | 본 skill 호출 전 거쳐야 할 skill id (역방향 successors) |
| `successors` | `list[str]` | 본 skill 후 자연 호출 후속 skill id (linkedSkills 의 의미 분리) |
| `audiences` | `dict[str, str]` | `{"llm": "...", "agent": "...", "human": "..."}` 주체별 한 줄 도입 |
| `isLeafNode` | `bool` | true 면 의도적 leaf — orphan lint 면제 |
| `entryHint` | `bool` | true 면 외부 LLM 첫 진입 후보 — MCP `start.*` 외 보강 |
| `graphTier` | `str` | L0~L4 계층 hint — 그래프 클러스터링 색상 |
| `cluster` | `str` | 자동 도출 외 수동 그룹핑 (e.g. `gather.history`) |
| `humanIntro` | `str` | 사람용 본문 도입 1~2 문단 (랜딩 페이지 상단 별도 영역) |

작성 가이드:

- `successors[]` · `predecessors[]` 는 *recipe* 의 linkedSkills 와 다르다 — recipe step 흐름이 아닌 일반 skill 간 후속 관계.
- `audiences[]` 3 키는 본문 directive (`:::for-llm` · `:::for-agent` · `:::for-human` · `:::end`) 와 함께 3 인덱스 분기 (mcp.json · agent.json · web.json) 에 사용.
- `isLeafNode: true` 는 자연스러운 종점 (e.g. `engines.gather.collect` 단순 호출) 만 — orphan 분류와 구분.

## 3 주체 인덱스 산출물

Skill 산출물은 운영자·사용자·사용자가 명시적으로 위임한 AI 가 spec 변경 의도에 맞춰 갱신한다.

| 산출물 | 대상 | 크기 (skill 당) |
|---|---|---|
| `catalog.json` | 전체 카탈로그 (landing·wheel 정본) | ~500 토큰 |
| `agent.json` | `catalog.json` byte-동일 legacy alias (실 리더 0) | ~500 토큰 |
| `mcp.json` | 외부 LLM (MCP first hop) | < 300 토큰 |
| `web.json` | 사람 (랜딩) | ~1500 토큰 + humanIntro |
| `pyodide.json` | 브라우저 Pyodide | ~400 토큰 |
| `graph.json` | 그래프 시각화 (`/skills/graph`) | nodes + edges + cycles + orphans |

산출물 동기화의 commit 분리 여부는 `operation.contributionWorkflow`의 논리 단위 원칙을 따른다.

