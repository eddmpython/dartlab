# Skill SSOT 작성 규약

> 본 문서는 `src/dartlab/skills/specs/**/*.md` 에 새 skill 을 추가하거나 기존 skill 의 frontmatter 를 갱신할 때 참고하는 운영 가이드. Skill 은 운영자·사용자·사용자가 명시적으로 위임한 AI 가 관리하고 개발한다.
>
> **산출물 6 종** (spec 변경자가 필요한 파일을 명시적으로 patch):
> - `catalog.json` — 전체 검색 카탈로그 (frontmatter + bodyPreview). landing·wheel 소비 정본.
> - `agent.json` — `catalog.json` 의 byte-동일 legacy alias (실 리더 0 · 물리 dedup 운영자 결정 대기). *옛 `index.json` 별칭은 미생성·폐기.*
> - `mcp.json` — 외부 LLM (MCP) 용 경량 (5 핵심 필드 + nextSkills max 5).
> - `web.json` — 사람 (랜딩) 용 풍부 (humanIntro · visualRefs · bodyHuman).
> - `pyodide.json` — Pyodide 런타임 manifest.
> - `graph.json` — 257 노드 + 1337 엣지 + cycle/orphan/unreachable 메타.
>
> `llms.txt` · `sitemap.xml` 은 landing 정적 SEO 자산(동결·수동 관리) — 본 6 JSON·capability 빌더와 무관.
>
> **카탈로그 count 의미** — `catalog.json` meta 의 `skillCount`·카테고리 `count` 는 `listSkills()` 가 `_builtinSpecPaths()` 로 *발견한 spec* 수다. `specs/recipes/**` raw `.md` 파일 수보다 낮은 것이 정상 — `.archive/`(drafted/unverified persona 격리)·`README.md`·비-spec `.md` 는 발견에서 제외된다(예: recipes `count`=161 = raw 243 − 76 `.archive/` − 6 README/non-spec). **status 필터가 아니라 경로-발견 규칙**이라, raw 파일 수를 count 와 비교해 "드리프트"로 오독하지 말 것.

## 1. 5 카테고리 + 디렉토리

| 카테고리 | 위치 | 의미 |
|---|---|---|
| `start` | `specs/start/{name}.md` | 첫 진입 (DartLab Skill OS, install, catalog 사용) |
| `runtime` | `specs/runtime/{name}.md` | 실행 환경 (Pyodide, MCP, Web AI, Local Python) |
| `operation` | `specs/operation/{name}.md` | 운영 규칙 (philosophy, code, apiContract, architecture, testing) |
| `engines` | `specs/engines/{group}/SKILL.md` (기본) + `specs/engines/{group}/{axis}.md` (응용) | 엔진별 기본 사용법 + 응용 실행 스킬 |
| `recipes` | `specs/recipes/{persona}[/{domain}...]/{name}.md` | L1.5 이하 (core·gather/providers·scan/frame/synth/reference) 조합 실험장. 검증 통과 + 엔진 능가 → L2 엔진으로 흡수 |

엔진 응용 스킬의 `id` 는 `engines.{group}.{axis}` 형식 (예: `engines.analysis.cashflow`). 기본 스킬은 `engines.{group}` (예: `engines.company`).

Recipe id 는 `recipes.{persona}[.{domain}...].{name}` 형식 (≥3 parts, depth 가변). 디렉토리 경로 ↔ id 가 1:1. 같은 단어 반복 금지 — `recipes.fundamental.credit.deepDive` 는 OK, `recipes.fundamental.credit.creditDeepDive` 는 나쁜 예.

### 1.1 페르소나 트리 SSOT

recipes/ 는 *분석가 페르소나* 별로 분류된다. 외부 트렌드인 "AI 펀더멘털/센티먼트/뉴스/테크니컬 애널리스트" 가 추론으로 결론을 만드는 반면, dartlab 의 recipe 는 모두 *L1.5 이하 (core·gather/providers·scan/frame/synth/reference) 조합* 으로만 작성되어 raw 근거가 추적 가능하다. 페르소나는 메시지 라벨이지 코드 구조가 아니다 — engines/ 의 4 계층 import 룰은 페르소나 트리와 무관하게 그대로 강제된다.

| 페르소나 | 위치 | 의미 | 현재 커버리지 |
|---|---|---|---|
| `fundamental` | `recipes/fundamental/{domain}/{name}.md` | 재무·가치평가·신용·자본배분·지배구조·공시 — 펀더멘털 분석가가 보는 모든 것 | valuation(damodaran 포함) · quality · credit · dividend · governance · disclosure (+ 미커버 산업 단계 등 추가 가능) |
| `macro` | `recipes/macro/{name}.md` | 거시·시클·금리·환율·유동성·시나리오 | 21 recipes |
| `technical` | `recipes/technical/{name}.md` | 가격·수익률·팩터·차트 (quant 엔진 부분 조합) | 미커버 → 1+ 예정 |
| `sentiment` | `recipes/sentiment/` | 투자심리·플로우·포지셔닝 | **미커버** (의도적 — placeholder README) |
| `news` | `recipes/news/` | 뉴스·공시 본문·외부 텍스트 | **미커버** (의도적 — placeholder README) |
| `meta` | `recipes/meta/{name}.md` | 페르소나가 아닌 *cross-cutting 작업 종류* — 보고서 합성·1차 스크리닝·테제 검증·사용 가이드 | report · screen · thesisKillChain · workflow |

페르소나 분류 룰:
- recipe 의 *주된 시점* (어떤 분석가가 사용할지) 으로 1차 분류. 펀더멘털 분석가의 *공시 이벤트 감시* = `fundamental/disclosure/eventRadar/`, 펀더멘털의 *이익의 질 forensics* = `fundamental/quality/forensics/`.
- 여러 페르소나가 동등하게 쓰는 결과물·필터·테제 검증 = `meta/`.
- "미커버" 페르소나 (sentiment·news) 는 빈 폴더 + README 로 *명시* — 있는 척 placeholder 채우지 않는다.

## 2. frontmatter 필드

### 필수 (검증 게이트)

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | `string` | 점-분리 (`category.name` 또는 `engines.group.axis`). 다른 곳에서 참조하는 표준 식별자. |
| `title` | `string` | 사람이 읽는 짧은 제목. 카드·헤더에 노출. |
| `category` | `start` \| `runtime` \| `operation` \| `engines` \| `recipes` | 카테고리 태그. |
| `purpose` | `string` | 1~2 문장. 이 skill 이 무엇을 하는지. 카드 미리보기·메타 디스크립션·llms.txt 에 직접 노출. |
| `whenToUse` | `string[]` | 어떤 질문/작업에 매칭되는 키워드. 검색·필터의 핵심. 비어있지 않게. |

### lint 강제 (게이트 통과 필수) — `src/dartlab/skills/registry.py::lintSkill`

| 필드 | 강제 조건 | 차단 |
|---|---|---|
| `runtimeCompatibility.pyodide` | `kind="curated"` skill 은 반드시 선언 | `_validateRuntimeCompatibility` 가 ValueError |
| `capabilityRefs[]` | 등록된 capability id 만 | `_validateCapabilityRefs:577-583` 가 ValueError |
| `id` 점 분리 | `category.name` 또는 `engines.group.axis` | `validateSkills.py` |
| `purpose` · `title` | 비어있지 않음 | `lintSkill:202-203` |
| (engines 카테고리) 본문 강제 섹션 4 종 | `## 공개 호출 방식` · `## 호출 동작` · `## 대표 반환 형태` · `## 기본 검증` | `_validateExecutionSkillContract` + `tests/audit/checkEngineSpecSchema.py` |

### Graph lint (phase 1 warn-only, phase 2-3 차단 예정) — `src/dartlab/skills/graphLint.py`

| 필드 | 검증 | 정책 |
|---|---|---|
| `knowledgeRefs[]` · `sourceRefs[]` · `toolRefs[]` · `datasetRefs[]` | id 가 listSkills 셋에 존재 | phase 1 warn / phase 2 신규 차단 |
| `successors[]` · `predecessors[]` | 양방향 일관성 | phase 2 부터 |
| `linkedSkills[]` cycle | 3+ 노드 SCC | phase 2 부터 |
| in-degree 0 + entry 아님 | `isLeafNode: true` 명시 권장 | warn-only |

### 권장 (`/skills/[id]` 페이지가 명시 섹션으로 렌더)

| 필드 | 타입 | 페이지 렌더 위치 |
|---|---|---|
| `procedure` | `string[]` | 우측 상단 `<ProcedureStepper>` numbered card stepper. **빈 배열이면 섹션 자체가 안 뜬다 — 채우면 절차감이 강해진다.** |
| `examples` | `string[]` | `<UsageExamples>` — 어떤 질문일 때 이 skill 을 쓰는지. |
| `expectedOutputs` | `string[]` | `<EvidenceChecklist title="기대 결과" kicker="출력">`. |
| `requiredEvidence` | `string[]` | 좌측 메타 카드의 chip 배열. 답변에 묶어야 할 evidence 종류. |
| `failureModes` | `string[]` | `<DoNotDo>` 의 "흔한 실패" 블록. |
| `forbidden` | `string[]` | `<DoNotDo>` 의 "절대 금지" 블록. |
| `runtimeCompatibility` | `Record<env, {status, notes?, limitations?}>` | `<RuntimeMatrix>` 5 환경 표. |
| `inputs` / `outputs` | `string[]` | 구조화된 입출력. 좌측 메타 카드. |
| `capabilityRefs` / `apiRefs` / `toolRefs` | `string[]` | 코드 원천. |
| `knowledgeRefs` | `string[]` | 다른 skill id (예: `engines.company`) — **참조용** (읽으면 도움). 클릭 가능한 chip 으로 링크. |
| `linkedSkills` | `string[]` | 다른 skill id — **실행 절차의 일부** (recipe 가 순서대로 거치는 step). `knowledgeRefs` 와 의미 분리. `kind: recipe` 에서 핵심. |
| `predecessors` / `successors` | `string[]` | 작업 흐름 path — 이전/다음 단계. graph 산출물을 갱신할 때 양방향 정합성 유지. recipe 외 sub-spec 의 진입 path 명시. |
| `audiences` | `dict[str, str]` | 본문 주체별 분기 — `llm` / `agent` / `human` 키 → 짧은 한글 설명. mcp.json/web.json 수동 갱신 시 매핑. |
| `isLeafNode` | `bool` | True 면 *의도적 leaf* — orphan warn 면제. |
| `entryHint` | `bool` | True 면 진입 노드 — graph 시각화에서 강조. |
| `graphTier` · `cluster` | `string` | graph 시각화 그룹화 키 (선택). 기본 cluster = engines.{group} 또는 category. |
| `humanIntro` | `string` | 사람용 도입 1~2 문단 — web.json 수동 갱신 시 `bodyHuman` 또는 별도 필드로 노출. |
| `sourceRefs` | `string[]` | `dartlab://skills/{id}` 형식의 표준 출처. |
| `status` | `observed` \| `unverified` \| `archived` | 검증 상태. 카드 배지. |
| `lastUpdated` | `YYYY-MM-DD` | 본문 변경 날짜. 운영자 수동 갱신. |

### 옵셔널 (사람용 슬롯)

| 필드 | 타입 | 의미 |
|---|---|---|
| `image` | `string` | 헤더 커버 이미지. `landing/static/skills/{id}/cover.{png,webp,svg}` 패턴. 없으면 카테고리별 placeholder. |
| `humanIntro` | `string` | 도입 1~2 문단 (사람용 톤). 페이지에서만 노출, AI 인덱싱 우선순위 낮음. |

## 3. 본문 구조

frontmatter 아래 본문은 mdsvex 가 렌더한다. Shiki 코드 하이라이트 + 카테고리 색상 (start blue · runtime purple · operation green · engines orange) 적용됨. `./assets/foo.png` 상대경로는 `/skills/assets/foo.png` 으로 자동 변환.

### 3.1. engine skill — 강제 섹션 (lint 게이트)

`category: engines` 인 skill 은 `dartlab.skills.registry` 의 `_validateExecutionSkillContract` 와 `tests/audit/checkEngineSpecSchema.py` 가 다음 4 개 섹션 제목을 본문에서 강제한다. 빠지면 `validateSkills.py` · registry lint · CI `lint` 게이트 어느 한 곳에서 `ValueError` 또는 exit 2 로 실패.

- `## 공개 호출 방식` — Python 코드블록. 사용자가 그대로 복사해 실행할 수 있는 호출 예 (모듈 callable / Company-bound / 클래스 직접 패턴).
- `## 호출 동작` — 입력 / 출력 / 에러 동작 산문. 어떤 인자를 받고 어떤 결과를 어떻게 반환하는지. axis/method 디스패치 룰.
- `## 대표 반환 형태` — 표 또는 구조 텍스트로 반환 DataFrame / dict 구조 (컬럼·dtype) 명시.
- `## 기본 검증` — 변경 시 동기화 약속·실패 표시 경로 (None / 빈 DataFrame / flags / Exception 어느 경로로 결손을 표현).

추가로 권장 (강제 아님):
- `## 엔진 역할` — 본문 도입 1~2 문단.
- `## evidence 기준` — `requiredEvidence[]` 의 각 항목 의미.
- `## 기본 실행 순서` — 사용 절차 numbered list.
- axis/method 표 — 가능하면 `## 전체 축/메서드 목록` 또는 동등한 헤딩 아래 표로 (예: gather/SKILL.md). 권장이며 lint 차단은 아님.

엔진 skill 은 **tool card** 로 유지한다. 즉, 어떤 질문에서 이 엔진을 쓰는지, 공개 호출이 무엇인지, 반환값과 evidence 가 어떤 성격인지까지만 명확히 한다. 축별 상세 컬럼·함수 schema·오류 세부는 capability/docstring 을 원천으로 연결하고, 여러 엔진을 엮어 결론·반례·모니터링을 만드는 분석 절차는 recipe skill 로 둔다. 축별 engine sub-spec 이 base skill + capability/docstring 참조로 충분한 경우에는 새 분석 논리를 그 안에 복제하지 않는다.

### 3.2. recipe skill — 본문 5 단 분석 구조 (권장)

`category: recipes` 인 skill 은 *여러 engine 을 조합하는 깊은 분석 절차* 다. 단순 출력 형태 (mermaid 한 개, 표 한 개) 만 명세하지 말고, 답변 본문이 그대로 5 단 구조로 작성되도록 다음 섹션을 채운다. 시스템 프롬프트의 분석 답변 5 단 (결론/근거/메커니즘/반례·한계/후속 모니터링) 과 1:1 매핑.

강제 (registry 검증): `## 연계 절차` 1 개 — 다른 skill 연결 단계.

권장 (본문 깊이 표준):

- `## 공개 호출 방식` — Python 코드블록. 사용자가 복사 실행 가능한 호출 예. *5 단 답안 산출* 가능한 구조여야 한다.
- `## 호출 동작` — 5 단 분석 구조로 다음 sub-heading 강제:
    - `### 1. 결론 도출` — 어떤 정량 한 문장 결론을 산출하는지 (예: "회사 X 의 신용 충격 민감도 = β 1.8 ± 0.3").
    - `### 2. 핵심 근거 수집` — 어떤 ref (skillRef/sourceRef/executionRef) 3 개 이상을 모으는지. 출처 + 수치 + 시점 명시.
    - `### 3. 메커니즘 분석` — 인과 경로 (mermaid graph LR 또는 단계별 bullet). 노드에 *수치 임계* 부착 권장.
    - `### 4. 반례·한계` — 결론이 깨지는 조건 / 데이터 noise / 측정 보수성.
    - `### 5. 후속 모니터링` — 다음 turn 에 추적할 지표 + 임계값 2~3 개.
- `## 대표 반환 형태` — 표 또는 구조 텍스트로 반환 dict / DataFrame 구조 명시.
- `## 연계 절차` — 다른 skill 로 이어지는 단계 (linkedSkills 와 정합).
- `## 기본 검증` — 검증 게이트.

#### recipe 실행 라우팅 계약

Recipe 는 RunPython 스크립트 모음이 아니라 **엔진 호출 오케스트레이션** 이다. 공개 API 또는 engine capability 가 이미 존재하면 `toolRefs[]` 와 본문 절차에서 `EngineCall` 을 우선한다.

- **EngineCall 우선** — `Company.panel`, `Company.trace`, `Company.disclosure`, `scan.*`, `gather.*`, `analysis.*`, `quant.*`, `credit.*`, `macro.*`, `viz.*` 처럼 capability 에 등록된 실행은 EngineCall 로 호출하도록 쓴다.
- **RunPython fallback** — 엔진 결과를 합치거나, L1/L1.5 helper 를 직접 호출해야 하거나, 아직 EngineCall surface 가 없는 실험 경로일 때만 보조 코드블록으로 둔다. 이 경우 본문에 "RunPython fallback" 또는 "RunPython 폴백" 을 명시한다.
- **계산 소유권** — recipe 안 Python 은 glue code 다. 엔진에 있는 계산을 recipe 코드에 다시 구현하지 않는다.
- **근거 보존** — EngineCall 결과의 `tableRef` / `valueRef` / `dateRef` / `sourceRef` 를 우선 사용하고, fallback 코드도 `emit_result(...)` 로 같은 evidence 를 남긴다.
- **도구 순서** — 둘 다 필요하면 `toolRefs: [EngineCall, RunPython]` 순서로 적는다.

#### recipe 시각화 선택 계약

Recipe 는 최종 금융 분석 답변을 만드는 절차이지만 모든 recipe 가 차트를 가져야 하는 것은 아니다. `visualGuidance[]` 는 차트를 의무화하는 필드가 아니라, 이 recipe 에서 시각 산출물을 만들지 말지와 만든다면 어떤 viz skill 을 쓸지 결정하는 선택 계약이다.

`visualGuidance[]` 를 쓰는 경우:

- **visualRefs 와 정합** — 실제로 사용할 `engines.viz.*` skill 을 `visualRefs[]` 에 명시한다.
- **primary visual** — 어떤 chartType 또는 diagram 을 우선할지 (`table-backed chart`, `price-chart`, `balance-structure-trend`, `cashflow-signed-matrix`, `peer-matrix`, `heatmap`, `waterfall`, `Mermaid graph LR` 등).
- **evidence gate** — 어떤 `tableRef` / `evidenceBinding` / 원문 ref 가 있을 때만 emit 할지.
- **fallback** — 데이터가 부족하면 차트를 만들지 않고 어떤 표나 coverage note 로 낮출지.
- **answer placement** — 결론 KPI, 구조 차트, 메커니즘 diagram, falsifier 표 중 어디에 배치할지.

시각화는 **observed viz skill 우선** 이다. `status: observed` 이고 evidenceBinding 계약이 명확한 `engines.viz.*` 만 `visualRefs[]` 에 넣는다. `unverified` 시각화는 recipe 의 공식 visualRef 가 아니라 본문 한계 또는 후속 후보로만 언급한다. 재무 원표 기반 recipe 는 우선 `engines.viz.financialStructureCharts`, `engines.viz.balanceStructureTrend`, `engines.viz.cashflowWaterfall`, `engines.viz.evidenceCoverage`, `engines.viz.mermaidDiagram` 중 데이터와 직접 맞는 것만 연결한다.

`visualGuidance[]` 를 비워두는 경우:

- 사용법/API 안내처럼 차트가 답변 품질을 높이지 않는 recipe.
- 공시 원문 근거 확인처럼 원문 문장·목록·표가 우선이고 차트가 장식이 될 위험이 큰 recipe.
- 아직 대응되는 `engines.viz.*` skill 또는 ChartRenderer chartType 이 없는 recipe.

금지:

- 데이터 row 없이 임의 차트 생성.
- 결손값을 0 으로 채워 구조 변화처럼 보이게 하는 chart.
- 표가 더 적합한 단일값을 장식 chart 로 승격.
- 차트가 답변 문단 하나를 직접 뒷받침하지 않는데 본문 chart 로 노출.
- `visualRefs[]` 없이 `visualGuidance[]` 만 적어 AI 가 실제 실행 스킬을 찾지 못하게 하는 상태.

### 3.3. 그 외 카테고리 (start · runtime · operation) — 권장 섹션

강제 섹션 없음. 자유로운 본문 구조. 권장:
- `## 절차` 또는 `## 무엇을 하나` — 본문 도입.
- `## 공개 호출 방식` (있으면) — 코드블록.
- `## 다음 단계` — 관련 skill 링크 (반드시 절대 path `/skills/{id}` 형식).

### 3.3. 내부 링크는 절대 path

skill 사이 링크는 항상 `[title](/skills/{id})` 절대 path 로 박는다. relative path (`(SKILL)`, `(../start/quickStart)`) 는 prerender 시 `/skills/SKILL` 같은 잘못된 URL 로 해석되어 빌드 실패.

본문 헤더 (`h1`/`h2`/`h3`) 는 `/skills/[id]` 페이지의 좌측 TOC 자동 추출 대상.

## 4. 새 skill 추가 절차

1. 카테고리 결정 (5 개 중 하나).
2. `src/dartlab/skills/specs/{category}/{name}.md` 생성. 엔진 응용은 `specs/engines/{group}/{axis}.md`, recipe 는 `specs/recipes/{domain}/{name}.md`.
3. 위 §2 의 필수 필드 5 개 + 권장 필드 채우기. `procedure[]` · `examples[]` 비워두기보다 1~2 개라도 채우기 (페이지 풍부도).
4. 본문 산문 작성 (§3 권장 구조).
5. 산출물 동기화: 변경 내용이 노출 표면에 영향을 주면 `catalog.json` · `agent.json` · `mcp.json` · `web.json` · `pyodide.json` · `graph.json` 중 필요한 파일을 명시적으로 patch.
6. 검증: `uv run python -X utf8 src/dartlab/skills/validateSkills.py src/dartlab/skills/specs/{category}/{name}.md`.
7. 랜딩 산출물을 바꿨으면 `cd landing; npm run build`.

## 5. 이미지 자산

- 위치: `landing/static/skills/{id}/cover.{ext}` — 랜딩 정적 자산 (PyPI 패키지와 분리). frontmatter `image:` 가 이 경로를 가리킨다 (예: `/skills/engines.company/cover.png`).
- 본문 안 이미지: 마크다운 `![alt](./assets/foo.png)` → 빌드 시 `/skills/assets/foo.png` 으로 변환 ([landing/svelte.config.js](landing/svelte.config.js) `rehypeBaseUrl`).
- 본문에서 사용하는 자산은 `landing/static/skills/assets/` 평면 폴더에 평면 파일명으로 (`syncSkillAssets.js` 가 향후 추가될 수 있음 — 그 전까진 운영자 직접 복사).

## 6. 검증 게이트

`src/dartlab/skills/validateSkills.py` 가 신규/수정된 .md 만 검사 (CI 에서 `git diff --name-only` 로 변경 파일 추출 후 인자 전달). 174 개 기존 파일에 일괄 강제하지 않는다.

검증 항목:
- frontmatter 존재.
- 필수 필드 5 개 (id·title·category·purpose·whenToUse) 비어있지 않음.
- `category` 가 5 카테고리 안.
- `id` 점 포함.

## 7. 관리 원칙

- Skill 본문은 capability/docstring 과 분리된 SSOT 로 작성한다.
- 174 개 본문 변환 또는 마이그레이션은 운영자 페이스로 점진 진행한다.
- frontmatter schema 새 필드는 [landing/src/lib/skills/catalog.ts](landing/src/lib/skills/catalog.ts) 의 `SkillDoc` 인터페이스와 함께 동기화한다.
- 카테고리는 5 개 (start/runtime/operation/engines/recipes) 를 유지한다.
