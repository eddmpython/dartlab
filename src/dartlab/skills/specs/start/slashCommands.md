---
id: start.slashCommands
title: Slash Commands — VSCode plugin 진입점 카탈로그
kind: curated
scope: builtin
status: drafted
category: start
purpose: dartlab slash command 진입점 카탈로그 — `/오늘아침` `/실적예고` `/논거점검` `/스크린` 등 외부 LLM 호환 진입점. VSCode extension / 호환 plugin 측 구현 사양.
whenToUse:
  - slash command
  - VSCode plugin
  - 진입점
  - command palette
inputs:
  - 사용자 slash command
outputs:
  - 매칭 recipe / engine axis 호출
toolRefs: []
knowledgeRefs:
  - start.dartlabSkillOs
sourceRefs:
  - dartlab://skills/start.slashCommands
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: limited
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - start.dartlabSkillOs
---

## 진입점 카탈로그

| 명령 | 매핑 | 설명 |
|---|---|---|
| `/오늘아침` | recipes.meta.report.dailyMorningNote | 일일 시황 1 페이지 |
| `/실적예고` | recipes.meta.report.catalystCalendar | 30/90 일 이벤트 |
| `/논거점검` | recipes.meta.report.thesisTracker | thesis falsifier 게이트 |
| `/스크린` | recipes.meta.screen.* 4 종 menu | screen 5 활성 menu |
| `/회사분석` | engines.company + 6 막 | 단일 회사 deep dive |
| `/매크로` | engines.macro 12 axis menu | 매크로 axis 선택 |
| `/시나리오` | engines.macro.scenarios | 시나리오 카탈로그 |
| `/portfolio` | recipes.quant.portfolio.* | 포트폴리오 구성 |

## 구현 사양

```python
# 호환 plugin 측 매핑 (예시)
SLASH_COMMANDS = {
    "/오늘아침": ("recipe", "recipes.meta.report.dailyMorningNote"),
    "/실적예고": ("recipe", "recipes.meta.report.catalystCalendar"),
    "/논거점검": ("recipe", "recipes.meta.report.thesisTracker"),
    # ...
}

def handle_slash(cmd: str) -> dict:
    type_, target = SLASH_COMMANDS.get(cmd, (None, None))
    if type_ == "recipe":
        return dartlab.ask(target)
    elif type_ == "engine":
        return dartlab.ask(target)
```

## 강행 룰

1. command 추가 → 본 spec 동시 갱신.
2. command → skill mapping 1:1 강행 (1 command 다중 skill X).
3. 사용자 input parsing → injection 차단 (untrusted wrap).

## 기본 검증

- 모든 command 의 mapping target 이 listSkills 안 존재.
- command name camelCase 또는 한글 (단순 명사).
