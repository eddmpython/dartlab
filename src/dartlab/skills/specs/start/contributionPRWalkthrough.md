---
id: start.contributionPRWalkthrough
title: Contribution PR Walkthrough — 외부 기여자 sample PR
kind: curated
scope: builtin
status: drafted
category: start
purpose: 외부 OS 기여자 1 인칭 sample PR walkthrough — operation.contributionWorkflow 의 외부 진입 보조. 실제 PR diff sample + commit message + lint pass + CI gate 통과 흐름.
whenToUse:
  - 외부 기여
  - PR walkthrough
  - sample PR
  - contribution guide
  - first time contributor
inputs:
  - 기여자의 신규 skill 또는 fix 의도
outputs:
  - PR 작성 가이드
  - sample diff
toolRefs: []
knowledgeRefs:
  - operation.contributionWorkflow
  - operation.code
sourceRefs:
  - dartlab://skills/start.contributionPRWalkthrough
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
  - operation.contributionWorkflow
  - operation.code
  - operation.architecture
---

## sample PR 흐름

### 1. fork + clone

```bash
git clone https://github.com/<your>/dartlab
cd dartlab
uv sync
```

### 2. 신규 skill 작성

신규 spec은 `src/dartlab/skills/SCHEMA.md`의 4단계 절차를 따른다:
- `lintSkill` 강제 섹션 충족
- `capabilityRefs` 명시
- `readSkill/describeSkill` 검색 가능
- Skill OS 6 JSON 동기화 (capability 카탈로그는 docstring 라이브 빌드라 재생성 무관)

### 3. 변경 단위 commit

```bash
# CLAUDE.md 강행: git add -A / . 금지, git commit -o <명시 paths>
git add src/dartlab/skills/specs/recipes/macro/myNewRecipe.md
git commit -o src/dartlab/skills/specs/recipes/macro/myNewRecipe.md \
  -m "추가: recipes.macro.myNewRecipe — 새 매크로 recipe ..."
```

### 4. lint + test

```bash
uv run python -X utf8 tests/run.py preflight
# → 27 CI gate SSOT
```

### 5. PR submit

- title: 변경 단위 명확 ("추가:" / "수정:" / "정리:" prefix)
- body: Why + How to apply + 영향 범위
- linked issue (있으면)

## 강행 룰

1. master 브랜치만 (CLAUDE.md feedback_master_only).
2. 변경 단위 + commit -o (commit-self-change SSOT).
3. 자동 매핑 / docstring auto-sweep 도구 신설 금지.
4. graph 회귀 가드 (no_graph_regression 8 번째).

## 안티패턴

- `git add -A` 또는 `.` 사용.
- 자기 변경 외 다른 파일 commit.
- 새 브랜치 / worktree 사용.
- AI 모델명 / 자기참조 commit 메시지.

## 기본 검증

- PR diff 가 본 walkthrough 패턴 따름.
- CI 27 gate 통과.
- 외부 기여자 첫 PR 흐름 추적 (incidents.md 기록).
