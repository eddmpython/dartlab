---
id: recipes.README
title: Recipes — 페르소나 트리 인덱스
purpose: dartlab recipes/ 트리 진입점. 페르소나별 분류와 분류 룰 SSOT 안내.
category: recipes
kind: curated
status: curated
whenToUse:
  - recipes 트리 시작점
  - 페르소나 분류 룰 확인
  - 새 recipe 어디에 두는지
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
---

# Recipes — 페르소나 트리

dartlab recipes/ 는 *L1.5 이하 (core · gather/providers · scan/frame/synth/reference) 조합* 으로만 작성되는 분석 절차 모음이다. L2 엔진 호출 금지 — 검증 통과 + 엔진 능가 시 L2 엔진으로 흡수가 유일한 승격 경로.

## AI 페르소나 vs dartlab 근거 트리

외부 트렌드는 "AI 펀더멘털/센티먼트/뉴스/테크니컬 애널리스트" 가 *추론으로 결론을 만드는* 방식. dartlab recipe 는 모든 입력이 L1.5 이하 raw 조합이라 결론의 모든 숫자·날짜·문장이 1차 출처로 추적된다.

```
recipes/
├── fundamental/    펀더멘털 — 재무·가치평가·신용·자본배분·지배구조·공시
│   ├── valuation/{damodaran/}
│   ├── quality/{forensics/}
│   ├── credit/
│   ├── dividend/
│   ├── governance/
│   └── disclosure/{eventRadar/}
├── macro/          매크로 — 거시·시클·금리·환율·유동성
├── technical/      테크니컬 — 가격·수익률·팩터·차트
├── sentiment/      센티먼트 — 미커버 (placeholder)
├── news/           뉴스 — 미커버 (placeholder)
└── meta/           cross-cutting (페르소나 아님)
    ├── report/         다중 페르소나 결과 합성 형태
    ├── screen/         1차 스크리닝 필터
    ├── thesisKillChain/ 테제 검증 워크플로
    └── workflow/        사용 가이드·데이터 가용성 등
```

## 분류 룰 (SCHEMA.md §1.1 SSOT)

1. recipe 의 *주된 사용자 시점* 으로 1차 분류 — 펀더멘털 분석가가 *공시 이벤트 감시* 하면 `fundamental/disclosure/eventRadar/`.
2. 여러 페르소나가 동등하게 쓰는 결과물·필터·테제 검증 = `meta/`.
3. "미커버" 페르소나 (sentiment·news) 는 빈 폴더 + README 로 *명시*. 있는 척 placeholder recipe 채우지 않는다.

## id 형식

`recipes.{persona}[.{domain}...].{name}` (≥3 parts, depth 가변). 디렉토리 경로 ↔ id 1:1.

- `recipes.fundamental.dividend.thesis` (4 parts — persona + domain + name)
- `recipes.fundamental.valuation.damodaran.fcffDcf` (5 parts — persona + domain + subdomain + name)
- `recipes.macro.sixActs` (3 parts — persona 가 곧 분야인 경우)
- `recipes.meta.report.dailyMorningNote` (4 parts — meta + 종류 + name)

## `.archive/` 격리 정책 (2026-05-26 T4)

`drafted` / `unverified` status 의 recipe 는 `recipes/.archive/` 하위에 페르소나 디렉토리 구조 그대로 격리한다. 사용자 노출 (index/agent/mcp/web/pyodide/graph.json 6 종 + landing `/skills`) 차단.

- **격리 메커니즘**: `src/dartlab/skills/registry.py::_builtinSpecPaths` 가 `.archive/` 폴더 path 를 필터링 — `listSkills` cascade 에서 invisible.
- **격리 진입**: `uv run python -X utf8 src/dartlab/skills/recipePromote.py archive --dry-run` 후 batch 검토 → 본 실행.
- **승격 (복원)**: 역방향 git mv 1 회 — `git mv recipes/.archive/{path} recipes/{path}` + status frontmatter `tested|verified` 변경 + 6 JSON 동기화 (운영자 수동, `feedback_no_skill_json_auto_build` 강행).
- **현재 격리 76 건** (2026-05-26): drafted 25 + unverified 51. 페르소나 분포: fundamental/credit 10 · disclosure 6 · dividend 5 · governance 5 · quality 10 · valuation 7 · macro 8 · meta/report 6 · meta/screen 9 · meta/workflow 2 · quant 1 · sentiment 1 · technical 6.

배경 (`memory/engineering.md` 10절 강행): drafted/unverified 가 카탈로그 220 의 35% 차지하면 *검증 안 된 recipe 가 사용자 표면을 오염*. 6-stage lifecycle (drafted → unverified → tested → verified → curated) 의 `tested` 미달은 표면 X — `.archive/` 격리가 정공.

## engines/ 와의 직교성

| 축 | 설명 |
|---|---|
| `engines/` | 4 계층 import 룰 (L0~L4) 에 따른 코드 구조. SDK 사용법 SSOT. 페르소나 트리 *없음*. |
| `recipes/` | 페르소나 트리. L1.5 이하 조합만 작성. 코드 구조 영향 0. |

engines 는 *검증되어 박힌 능력*, recipes 는 *L1.5 이하 조합 실험장*. 두 축은 서로 독립.
