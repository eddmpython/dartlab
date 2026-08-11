---
id: operation.skillDevelopmentLoop
title: Skill 개발 루프 — 자율 인큐베이션 + audit 회환
kind: curated
scope: builtin
status: unverified
category: operation
purpose: AI 가 분석 빈칸을 발굴해 신규 skill 초안을 만들고 같은 세션에서 자가 실행으로 검증해 정식 등재까지 가는 6 단계 사이클과, 운영 중 audit 결과를 엔진 skill 또는 docstring 개선으로 되돌리는 회환 절차를 합쳐 한 곳에서 관리한다. 트리거 — 신규 분석 skill 만들자 / 분석 빈칸 메우기 / audit 결과 반영.
whenToUse:
  - 신규 분석 skill 후보 발굴
  - Company/gather/scan 원천 데이터로 빈칸 메우기
  - skill 초안을 직접 써보고 품질 검증
  - 인큐베이팅 skill 을 정식 specs/ 로 승격
  - 분석 skill 의 ground-truth 비교
  - skill incubation
  - skill 개발 사이클
  - 엔진 조합으로 새 분석 만들기
  - 엔진에 없는 분석을 응용
  - audit 결과를 skills 에 반영
  - 독스트링 보강 후보 찾기
inputs:
  - 사용자 질문 또는 분석 빈칸 후보 (자유형 슬러그 또는 자동 발굴)
  - audit 결과
  - ground-truth 종목 3 개 (성공 / 실패 / 위기 또는 등가 케이스)
outputs:
  - incubating skill markdown (.dartlab/skills/incubating/{id}.md)
  - selfRun 결과 표 (3 케이스 × evidence)
  - graduate 결정 (정식 specs/ 등재 또는 회귀)
  - docstring improvement candidate
  - curated SkillSpec candidate
capabilityRefs:
  - Company
  - Company.analysis
  - Company.panel
  - Company.credit
  - Company.quant
  - gather
  - scan
  - macro
  - quant
toolRefs:
  - ReadSkill
  - GetSkillBody
  - ReadCapability
  - CreateUserSkill
  - EngineCall
  - RunPython
  - SaveArtifact
  - RunWorkbench
  - InspectDataset
  - CompileVisual
knowledgeRefs:
  - operation.extendSkills
  - operation.coreloop
  - operation.opsAsSkills
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/operation.skillDevelopmentLoop
procedure:
  - gapSpot — 전 카테고리 dartlab.skills.search() 로 유사 skill 부재 확인 후 ReadCapability + ReadSkill 로 Company/gather/scan 노출 데이터 빈칸 식별. 후보 5~8 개 nominate (axis 명 / 사용 데이터 / 가설).
  - dataSanityCheck — protoSkill 작성 *전* 에 사용할 capability 를 1 종목 (대형 안정형) 으로 EngineCall 우선 호출해 실제 반환 형태와 시계열 길이를 본다. EngineCall surface 가 없을 때만 RunPython fallback 으로 확인한다. 가정 어긋나면 후보 폐기 또는 신호 정의 재설계.
  - protoSkill — 후보 1 개 선택. `CreateUserSkill` 로 .dartlab/skills/incubating/user.{slug}.md 초안을 작성한다. requiredEvidence[] 에 ground-truth 3 케이스 명시. 엔진에 있는 기능은 toolRefs/본문에서 EngineCall 우선, RunPython 은 fallback/폴백 절차로 분리한다.
  - selfRun — 같은 세션에서 ReadSkill 로 재로드 후 capabilityRefs 를 EngineCall 로 먼저 3 케이스 전부 실행한다. 보조 결합·L1.5 helper·미등록 실험 경로만 RunPython fallback 으로 실행한다. 출력 ref + 정량 결과 누적. 종목 동시 로드 ≤ 2 (메모리 안전).
  - redTeam — RunWorkbench 의 CRITIQUE 패스로 (a) 반대 가설 (b) 누락 데이터/edge case (c) 다른 axis 와 중복성 점검. 통과 못하면 protoSkill 재집필 1 회 회귀.
  - graduate — 통과 시 specs/{category}/{slug}.md 로 이동 + 필요시 facade axis 등록 + 모듈 코드 작성 + 산출물 동기화 + 운영자 ack 1 줄. engines.{scan|gather|analysis|quant|macro}.* 응용 skill 은 lint 가 facade 호출 예시를 강제하므로 코드 작업 동반.
  - auditFeedback — 운영 중 같은 skill 이 audit P 반복 또는 docstring 보강 후보 적발 시, public API 자체가 새 축을 요구할 정도로 반복되면 docstring Guide/AIContract 또는 공식 엔진 axis 로 승격, 관련 SkillSpec 의 공개 호출 방식과 대표 반환 형태를 같은 변경에서 갱신.
requiredEvidence:
  - skillRef
  - capabilityRef
  - auditResult
  - groundTruthCases
  - selfRunResultTable
  - redTeamCheck
  - executionRef
  - sourceRef
expectedOutputs:
  - 빈칸 후보 표 (gapSpot 결과)
  - incubating skill 본문
  - selfRun 결과 표 (3 케이스 × evidence)
  - redTeam 통과 여부 + 사유
  - graduate 최종 위치
  - audit 회환 후보 (docstring or 엔진 skill 보강)
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
    notes:
      - selfRun 단계의 EngineCall/RunPython 은 server/localPython 환경 필요. webAi 단독으로는 protoSkill 작성까지만 가능.
  pyodide:
    status: limited
    limitations:
      - live API 가 필요한 조합을 서버 audit 없이 official 로 승격하지 않는다.
      - 일부 capability (대량 parquet, MCP) 미지원으로 selfRun 부분 실행만 가능.
failureModes:
  - ground-truth 케이스 없이 selfRun 통과시킴 (정성 평가 회귀)
  - incubating skill 을 selfRun 없이 바로 specs/ 로 등재
  - 1 종목으로만 검증 (3 케이스 강행규칙 위반)
  - 엔진 capability 가 있는데 recipe 본문이 RunPython 코드만 유도함
  - RunPython fallback 을 주 호출 경로처럼 써서 engine evidence refs 를 잃음
  - unverified viz skill 을 visualRefs 에 넣어 공식 시각화처럼 노출함
  - CreateUserSkill 로 만든 local user skill 을 builtin/official skill 처럼 답변함
  - redTeam 회귀 횟수 누적 없이 무한 재집필
  - 동일 axis 가 이미 analysis/scan/quant 에 존재함을 점검 안 함
  - 한 질문에 맞춘 runner 를 skill 로 고정
  - 공개 API 변경 후 관련 skill 을 갱신하지 않음
  - 자동 metric 만 보고 official 승격
forbidden:
  - 운영자 ack 없이 graduate 실행
  - specs/ 디렉터리에 검증 미통과 skill 직접 쓰기
  - local user skill 요청을 공식 specs/ 변경으로 처리
  - 엔진에 이미 있는 계산을 recipe RunPython 코드에 재구현
  - observed 가 아닌 viz skill 을 공식 visualRefs 로 연결
  - selfRun 결과를 외부 본문으로 인용 (sourceType=external 마커 누락)
  - 종목 3 개 동시 메모리 로드 (`operation.performanceProfile` 메모리 안전 위반)
  - 질문별 실행 코드 저장
  - 답변 템플릿 저장
  - skill 과 공개 API 호출/반환 설명 불일치 방치
examples:
  - 분석 axis 빈칸 메우자 — gapSpot 후보 표 + dataSanityCheck → protoSkill 1 개 선정
  - flowAnomaly skill 만들어보자 — protoSkill → selfRun (005930/047810/138930) → redTeam → graduate ack 대기
  - audit 에서 실패한 질문을 skill 또는 docstring 개선으로 반영해줘 — auditFeedback 단계만 실행
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-17"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 무엇을 하나

DartLab 의 analysis 엔진은 25 axis 로 *재무 인과* 영역을 두텁게 덮고 있지만, Company/gather/scan 이 노출하는 원천 데이터 (가격·수급·뉴스·컨센서스·내부자거래·배당이벤트·공시텍스트·거시지표) 의 *시장신호·이벤트추적·시계열 누적* 관점은 빈칸이 많다. 또 운영 중 audit 결과가 *공개 API 의 새 축을 요구* 하는 신호로 누적될 때가 있다.

이 skill 은 두 흐름을 한 곳에서 다룬다:
1. **인큐베이션 사이클 (gapSpot → graduate)** — 사용자 의도에 따라 AI 가 보조하는 6 단계로 신규 분석 skill 을 발굴·검증·등재.
2. **audit 회환 (auditFeedback)** — 운영 중 audit P 반복 또는 docstring 갭 적발 시 엔진 skill·docstring 으로 환류.

책임 경계:
- [operation.extendSkills](/skills/operation.extendSkills) — *승격 규칙* SSOT. user → curated, official 조건. 본 skill 의 graduate 단계가 호출.
- [operation.coreloop](/skills/operation.coreloop) — 자가개선 루프 *전체* SSOT (AuditPacket/ImprovementCandidate 메타). 본 skill 은 그 하위 한 사이클.

세 skill 은 중복 규칙 금지 — 본 skill 은 *사이클 + 회환*, extendSkills 는 *규칙*, coreloop 은 *메타*.

## 6 단계 인큐베이션 사이클

```
gapSpot → dataSanityCheck → protoSkill → selfRun → redTeam → graduate
                              (.dartlab/skills/incubating/)         (specs/{category}/)
```

### 1. gapSpot

- `dartlab.skills.search(축_명사구)` 를 *전 카테고리* 로 호출해 유사 skill 부재 확인. operation/runtime 까지 검색 (한 카테고리만 보면 중복 회귀).
- ReadCapability 로 Company/gather/scan 의 노출 데이터 인벤토리 확인.
- 후보 5~8 개를 표로 nominate. 각 후보는 `(axis 명 / 사용 데이터 / 가설 한 줄)`.
- 후보 1 개 선택은 운영자 발화 또는 AI 자체 판단 (위험 낮은 것부터).

### 2. dataSanityCheck

- protoSkill 작성 *전* 에 사용할 capability 를 1 종목 (대형 안정형, 예: 005930) 으로 호출해 *실제 반환 형태와 시계열 길이* 를 본다.
- 실행 우선순위는 `EngineCall` → `RunPython fallback` 이다. `Company.panel`, `Company.trace`, `Company.filings`, `scan.*`, `gather.*`, `analysis.*`, `quant.*`, `credit.*`, `macro.*`, `viz.*` 처럼 엔진 surface 가 있으면 EngineCall 로 호출한다.
- RunPython 은 엔진 결과를 결합하거나 L1/L1.5 helper 를 직접 호출해야 하는 경우에만 보조로 쓴다. 이때 protoSkill 본문에 "RunPython fallback" 또는 "RunPython 폴백" 을 명시한다.
- 검사 항목 — 행 수, 컬럼 존재, None/NaN 비율, 기간 범위, attr 이름 (dataclass docstring 으로 검산).
- 가정과 어긋나면 후보 폐기 또는 신호 정의 재설계 (예: 시계열이 5 거래일뿐이면 σ 통계 가정 폐기 → 절대값/임계 비교로 재정의).
- 이 단계가 빠지면 protoSkill 가정 오류가 selfRun 단계에서 적발돼 회귀 비용이 1 회 늘어난다 (실제 인큐베이션 회귀 사례에서 확립).

### 3. protoSkill

- SCHEMA.md `## 1. 5 카테고리` 표에 따라 카테고리 결정. 신규 axis 가 *signal/event* 영역이면 `engines.scan.{slug}` 또는 `engines.analysis.eventBased.{slug}`. 여러 엔진을 묶어 답변 품질을 높이는 절차면 `recipes.{domain}.{slug}`.
- 초안 markdown 은 `CreateUserSkill` 로 `.dartlab/skills/incubating/user.{slug}.md` 에 저장한다. 이 로컬 user skill 은 공식 산출물 동기화 대상이 아니며 `trustTier: localUserDraft` 로 취급한다.
- frontmatter 필수 5 개 (id·title·category·purpose·whenToUse) 채우고 `requiredEvidence[]` 에 ground-truth 3 케이스 명시 — 예: 005930 (성공), 047810 (위기), 138930 (저평가).
- 본문 강제 섹션 (engine skill 인 경우): `## 공개 호출 방식`, `## 호출 동작`, `## 대표 반환 형태`.
- recipe skill 은 tool card 가 아니다. 엔진 호출은 `linkedSkills`/`capabilityRefs`/`toolRefs` 에서 EngineCall 로 드러내고, RunPython 은 fallback code block 으로 분리한다.
- 시각화가 답변 품질을 높이면 `visualRefs[]` 와 `visualGuidance[]` 를 같이 둔다. 단, 공식 visualRef 는 `status: observed` 인 `engines.viz.*` 만 사용한다. 재무 원표 기반이면 `engines.viz.financialStructureCharts` / `engines.viz.balanceStructureTrend` / `engines.viz.cashflowWaterfall` / `engines.viz.evidenceCoverage` / `engines.viz.mermaidDiagram` 중 실제 근거와 맞는 것만 고른다.

### 4. selfRun

- 새로 저장한 incubating user skill 을 `ReadSkill(includeUser=true)` 로 다시 로드 (검증 — 같은 세션에서 검색 매칭되는지).
- capabilityRefs 의 각 API 를 EngineCall 로 먼저 호출, 보조 계산은 RunPython fallback 으로 실행한다.
- EngineCall 결과의 `tableRef` / `valueRef` / `dateRef` / `sourceRef` 를 selfRun 표의 1차 근거로 둔다. fallback 코드도 `emit_result(...)` 로 같은 ref 형태를 남긴다.
- 3 케이스를 *순차* 실행 (`operation.performanceProfile` 메모리 안전: 동시 로드 ≤ 2).
- 결과 표: `(케이스 / 입력 / 출력 / evidence ref)` 4 열. 각 행은 1~2 줄.

### 5. redTeam

- RunWorkbench 의 CRITIQUE 모드 또는 명시 검토 프롬프트로:
  1. **반대 가설** — 같은 데이터로 정반대 결론이 나오는 시나리오 가능한가?
  2. **누락 데이터 / edge case** — 분기 결손, IPO 1 년 미만, 해외 dual listing 등에서 동작 보장되는가?
  3. **중복성** — 이미 analysis/scan/quant 의 어느 axis 와 90% 이상 겹치는가?
- 셋 다 통과해야 5 단계 완료. 하나라도 실패면 protoSkill 재집필 1 회 회귀.
- 회귀 카운트는 incubating skill frontmatter 의 `lastUpdated` + 본문 끝 `<!-- redTeamRetry: N -->` 주석으로 추적. 3 회 초과 시 폐기.

### 6. graduate

- 운영자에게 다음 4 가지를 한 응답에 보여준다:
  1. selfRun 결과 표 (3 케이스 × evidence)
  2. redTeam 통과 사유
  3. incubating skill 본문 요약 (frontmatter + 본문 핵심 3 줄)
  4. 정식 등재 위치 제안 (`specs/{category}/{slug}.md`)
- 운영자 ack 1 줄: `ok` 또는 `reject` 와 사유.
- engines.{scan|gather|analysis|quant|macro}.* 응용 skill 은 lint 가 *facade 호출 예시* 를 강제 — graduate 가 자동으로 *facade axis 등록 + 모듈 구현* 코드 작업 동반. 코드 작업이 무거우면 local user skill 로 incubating 에 머무르며 별도 PR 로 분리.
- `ok` + 코드 작업 동반 가능 시:
  - `.dartlab/skills/incubating/user.{slug}.md` 내용을 검증 후 `src/dartlab/skills/specs/{category}/{slug}.md` 로 공식 스펙 작성
  - facade `_AXIS_REGISTRY` 등록 + 모듈 작성 (예: `src/dartlab/scan/{slug}.py`)
  - `uv run python -X utf8 src/dartlab/skills/validateSkills.py src/dartlab/skills/specs/{category}/{slug}.md`
  - 산출물 6 종 중 노출 표면에 영향을 받는 파일을 명시적으로 동기화
- `reject` 사유 시: incubating 에 머무르며 회귀 카운트 +1.

## 7 단계 — auditFeedback (운영 회환)

운영 중 누적된 신호:
- 같은 skill 이 서버 경유 `/api/ask` audit 에서 P (pass) 를 반복 → `auditP` 후보.
- public API 자체가 새 축을 요구할 정도로 반복 → docstring Guide/AIContract 또는 공식 엔진 axis 로 승격.
- official 승격은 *구조 lint + 서버 audit P + 운영자 확인* 셋 모두 만족할 때만.

승격 시 관련 SkillSpec 의 *공개 호출 방식* 과 *대표 반환 형태* 를 같은 변경에서 갱신해야 코드↔skill 동기화 룰을 지킨다.

### 7 단계 실행 스크립트 (Phase P/F/R/V)

`auditFeedback` 자동화는 `data/audit/candidates/{YYYY-MM-DD}-candidates.json` 을 입력으로 받는 4 개 스크립트로 분리된다. 운영자가 cron 트리거 없이 명시 호출.

| Phase | 스크립트 | 책임 | dry-run / confirm |
|---|---|---|---|
| **P** (Pattern) | `src/dartlab/skills/extract_skill_candidates.py` | audit ai-ask jsonl 스캔 → 동일 `(category_hash, tool_sequence_hash)` N 회 이상 성공 반복 = docstring Guide append 초안 생성. `data/audit/candidates/{YYYY-MM-DD}-candidates.json` + draft md 산출. `--sanitize` 시 question 원문 제외 (공개 공유용). `--include-audit-analysis` 시 `auditAnalysis/*.md` 의 "엔진 개선" bullet 도 후보 풀로 편입 | dry-run 기본 (산출물만), `--sanitize` 별도 |
| **V** (Verify) | `src/dartlab/skills/verify_candidate.py` | candidate 의 예시 질문을 `POST /api/ask` 로 재질의해 동일 tool sequence 재현 확인. 재현 실패 시 promote 중단. 서버 off 시 skip + WARN | 단일 모드 (조회만) |
| **R** (Raise) | `src/dartlab/skills/promote_skill.py` | candidate → docstring `Guide` append PR. `--confirm` 미지정 시 diff 만 출력. `--confirm --pr-draft` 시 git 브랜치 + `gh pr create --draft`. **auto-merge 금지** (`gh pr merge --auto` 호출 안 함, 3 중 방어 1 차) | dry-run 기본, `--confirm` 필요 |
| **F** (Feedback) | `src/dartlab/skills/refine_skill.py` | 실패 신호 (error 필드 / chunk_len 낮음 / extreme_flags / override 후 재발) 집계 → docstring `Caveats` 섹션 추가 PR | dry-run 기본, `--confirm` 필요 |
| (helper) | `src/dartlab/skills/_axis_slug.py` | 한글 축명 → ASCII slug 매핑 (`KOREAN_AXIS_SLUG`). PR 브랜치 규칙 `skill/docstring-{engine}-{axis-slug}-{YYYYMMDD}` 에 사용. promote/refine 양쪽 import. **단독 실행 모듈 아님** | n/a |
| (helper) | `src/dartlab/skills/_parse_audit_analysis.py` | `auditAnalysis/*.md` (사람 수동 작성) 의 "엔진 개선" 섹션 bullet 추출. Phase P 의 `--include-audit-analysis` 모드 helper. **단독 실행 모듈 아님** | n/a |
| **A** (Axis) | `src/dartlab/skills/propose_axis.py` | Phase R merge 이력 + Phase F counterexample 누적 → 엔진 axis 승격 proposal.md 생성. **엔진 코드는 건드리지 않음 — 사람 판단이 주**. 게이트 (AND): Phase R merge 3+ / counterexample 2+ / 첫 R merge 30 일+ | 단일 모드 (proposal.md 생성만) |

브랜치 네이밍 룰 (helper 강행): `skill/docstring-{engine}-{axis-slug}-{YYYYMMDD}` — 한글 축명은 반드시 `_axis_slug.to_slug()` 경유. 신규 엔진·축 추가 시 `KOREAN_AXIS_SLUG` 에 동일 변경 단위에서 보강.

## ground-truth 케이스 정책

- 3 케이스는 가능하면 *알려진 대표 사례* — DartLab 기존 분석/뉴스에서 진단이 명확한 종목.
  - 성공: 005930 (삼성전자) — 대형 안정형
  - 위기: 047810 (한국항공우주) 또는 동등 위기 사례
  - 저평가/턴어라운드: 138930 (BNK금융지주) 또는 동등
- 케이스 set 은 incubating skill frontmatter 에 명시 + 향후 동일 skill 의 backtest 시 재사용.
- 3 케이스 모두 *방향성 일치* 면 통과. 1 개라도 반대 진단이면 redTeam 재진입.

## 트리거

- 자유형 발화: "신규 분석 skill 만들자", "분석 빈칸 메우기", "효과적인 skill 굳히기", "audit 결과 반영해줘".
- slash command: `/skill-incubate {gap_slug?}` (선택) — 인자 있으면 gapSpot 생략하고 protoSkill 부터 시작.

## 다음 단계

- [operation.extendSkills](/skills/operation.extendSkills) — graduate 단계의 승격 규칙
- [runtime.workbenchEvidenceFlow](/skills/runtime.workbenchEvidenceFlow) — selfRun/redTeam 의 GATE 검증 메커니즘
- [operation.opsAsSkills](/skills/operation.opsAsSkills) — graduate 후 docstring/SkillSpec 정합성
