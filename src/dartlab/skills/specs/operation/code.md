---
id: operation.code
title: 코드 규칙
kind: curated
scope: builtin
status: observed
category: operation
purpose: 코드 규칙 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - 코드 규칙
  - code
  - 1. 네이밍 — camelCase 로 간다
  - 2. 독스트링 — 9 섹션으로 쓴다
  - AI 역할 — Guide 에 명시한다
  - Returns 작성 규칙 — 키 + 타입 + 단위를 명시한다
  - 3. CAPABILITIES — 단일 진실의 원천으로 간다
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
  - operation.contributionWorkflow
sourceRefs:
  - dartlab://skills/operation.code
procedure:
  - 1. 네이밍 — camelCase 로 간다 기준을 확인한다.
  - 2. 독스트링 — 9 섹션으로 쓴다 기준을 확인한다.
  - AI 역할 — Guide 에 명시한다 기준을 확인한다.
  - Returns 작성 규칙 — 키 + 타입 + 단위를 명시한다 기준을 확인한다.
  - 3. CAPABILITIES — 단일 진실의 원천으로 간다 기준을 확인한다.
  - 기존 코드의 네이밍 패턴을 따른다.
  - 0.10 부터 snake_case 절대금지 (식별자 + 파일명 모두). shim 없음.
  - '**최신 먼저 역순** — 데이터 정렬 기본값.'
  - '`AI role:` 또는 `AI 역할:` 로 시작하는 짧은 문장을 둔다.'
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
  - 코드 규칙 규칙 확인
  - code 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: code
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

- 1. 네이밍 — camelCase 로 간다 기준을 확인한다.
- 2. 독스트링 — 9 섹션으로 쓴다 기준을 확인한다.
- AI 역할 — Guide 에 명시한다 기준을 확인한다.
- Returns 작성 규칙 — 키 + 타입 + 단위를 명시한다 기준을 확인한다.
- 3. CAPABILITIES — 단일 진실의 원천으로 간다 기준을 확인한다.
- 0.10 부터 snake_case 절대금지. 모든 식별자 (함수·메서드·매개변수·모듈변수·**파일명**) camelCase. 클래스 PascalCase. 모듈 상수 ALL_CAPS.
- 매개변수명은 `core/naming/aliases.json` 표준 사전 준수 (의미 같으면 같은 이름 — AI 추론 단순화). 신규 의미는 PR 로 사전 추가 후 사용.
- 시그니처 단순화: 인자 5 개 초과 함수 → dataclass 묶기 권고.
- 파일명 (`.py`) 도 camelCase. pytest discovery 패턴: `test_*.py` + `test*.py` (둘 다 허용).
- **최신 먼저 역순** — 데이터 정렬 기본값.
- `AI role:` 또는 `AI 역할:` 로 시작하는 짧은 문장을 둔다.

## 12 룰 — 잘만든 라이브러리 구조 SSOT (P-트랙 박음)

dartlab 의 엔진·provider 모듈은 다음 12 룰 동시 만족 필수. 각 룰은 prose + 머신 게이트 동행 — 미준수 시 audit/lint 차단. baseline 모드에서 시작, P-phase 통과마다 strict 전환.

### 구조 룰 (7)

1. **Protocol 동일 surface** — 동일 도메인의 provider 는 동일 Protocol (`DocsProvider`/`FinanceProvider`/`FilingsProvider`/`CompanyProtocol`) 모두 isinstance + 시그니처 introspection 일치. 새 regulator 추가 = Protocol 구현체 1 개 drop-in. 현재 strict scope 는 `dart,edgar` 이며, `edinet` 은 API 통신 불가로 deferred.
   - 게이트: `tests/test_providerContract.py` · 정공법 (B) Protocol DIP.

2. **폴더 mirror** — 동일 도메인 sibling 폴더는 sub-folder set 동일. DART/EDGAR 는 `accessor/builder/parse/ops/docs/finance/openapi` 같은 골격을 맞춘다. EDINET 은 API 복구 전까지 placeholder 강제 대상이 아니다.
   - 게이트: `tests/audit/folderMirror.py --providers dart,edgar` · 정공법 (A) Hierarchy.

3. **LoC 임계** — 폴더화 vs 단일 .py 선택 규칙:
   | 도메인 합계 LoC | 형태 |
   |---|---|
   | ≤ 400 | 단일 `.py` (예 `dividend.py`) |
   | 401~800 | 폴더 + 1~2 sub-module |
   | > 800 | 폴더 + parser/pipeline/types 분할 |
   - 게이트: `tests/audit/folderSize.py` · 정공법 (A) Hierarchy. 임계값 외 폴더화 (50~300 LoC 폴더화 등) 자동 차단.

4. **`__init__.py` thin** — 함수/클래스 정의 0 + 본문 노드 화이트리스트 (docstring · import · `__all__` 대입 · DI register call). 로직이 들어가면 즉시 `.py` 분리.
   - 게이트: `tests/audit/initThin.py` (AST 기반). LoC 임계는 ruff `format` 의 magic-trailing-comma 와 충돌하므로 두지 않는다. 본질은 "로직 0" 강제.

5. **`_*.py` 0** — generic helper 파일명 (`_helpers.py`/`_utils.py`/`_*.py`) 폐지. helper 는 사용처 안으로 흡수하거나 도메인 명시 이름 (예: `_filings.py` → `filingsCatalog.py`).
   - 게이트: `tests/audit/lint_camelcase_ast.py --no-underscore-modules` · 정공법 (A) Hierarchy + 사용처 흡수.

6. **Docstring** — 9 섹션 full 표준 (`operation.docstringStandard` SSOT) 준수. 사람용 8 (`Capabilities`/`Args`/`Returns`/`Example`/`Guide`/`SeeAlso`/`Requires`/`AIContext`) + LLM Specifications 1 (안에 `AntiPatterns`/`OutputSchema`/`Prerequisites`/`Freshness`/`Dataflow`/`TargetMarkets` 6 sub-keys) = 9 섹션.
   - **최소 strict 게이트** — `Sig`/`Args`/`Example`/`Raises` (또는 `Returns` 대체) 4 섹션 부재 시 차단 (`tests/audit/docstring4Section.py` + `tests/audit/lint_camelcase_ast.py --docstring-strict`). nine-section full migration 은 후속 트랙 (P-F6~F11 minimum 4-섹션 strict 만 우선 적용).

7. **테스트 mirror** — `src/dartlab/providers/X/Y.py` ↔ `tests/providers/X/test_Y.py` 1:1 슬롯. 새 src 파일 = 테스트 자동 슬롯. 누락 시 차단.
   - 게이트: `tests/test_structureMirror.py`.

### 메모리-safe 룰 (4)

8. **`fetchX()` full-df 금지** — provider 의 collection 반환 메서드는 `limit: int = 100` keyword 의무. cross-company 질문은 slim index 경유만.
   - 게이트: `tests/audit/limitDefault.py` · 정공법 (B) Protocol DIP + (C) 호출 inversion.

9. **Eager cross-scan 금지** (scan 엔진 자체는 허용) — 차단 표적은 **런타임 (providers/) 안 eager 전 회사 일괄 적재**. 즉 `pl.read_parquet("data/.../*.parquet")` 또는 `pl.scan_parquet("*.parquet").collect()` (engine 미지정 = eager) 패턴만 grep 차단. 다음 3 가지는 허용:
   - **빌더 (scan/builder/)** — prebuild 단계 cross-scan 은 본직. `whitelist_paths: [scan/builder/, industry/build/]`.
   - **Streaming engine 명시** — `.collect(engine="streaming")` 또는 `.sink_parquet(path)` (disk-spill, O(batch) 메모리).
   - **Slim index 경유** — 런타임은 `data/{provider}/scan/docsIndex.parquet` (section_content 제외 메타) 만 scan. content 가 필요하면 stockCode 단위 회사별 lazy 로드.
   - inline 화이트리스트: `# polars-streaming-unsupported: pivot|over|asof` 주석 — streaming 엔진 미지원 연산 의도 마킹 (M0/M3).
   - 게이트: `tests/test_no_raw_cross_scan.py` — eager collect 패턴 + 화이트리스트 외 raw glob scan 검출.
   - **M-track 4 층 패턴** (2026-05-12 도입):
     1. **Streaming engine 일괄** (M2): 142 collect 중 ~100 곳을 `.collect(engine="streaming")` 명시. dataLoader 진입점 + providers/dart + providers/edgar + scan/builder + industry/build + quant + analysis + macro + gather + scan/* 전 sub-folder.
     2. **DuckDB hybrid** (M6, 후속): cross-company × complex aggregation 은 SQL 위임 (Arrow zero-copy).
     3. **Allocator 검증** (M7, 진단 후속): Windows mimalloc 실측 결과 기반 jemalloc 검토. 실측 캡처 — `tests/cli/showPolarsBuild.py` (`uv run python -X utf8 tests/cli/showPolarsBuild.py`) → `polars.show_versions()` 본문 + platform · python · cpu count · `POLARS_MAX_THREADS` / `POLARS_ALLOCATOR` 환경변수 + mimalloc 추정 hint (Polars 1.0+ default). stdout 만, md 산출 안 함 (md 작성 금지 룰).
     4. **함수 단위 가드** (M4/M5): `@withMemoryBudget(limitMb=N)` 데코레이터 (`MemoryBudgetExceeded`) + `OomTripwire` background watcher (EMERGENCY 초과 시 graceful `os._exit(137)`). Company `__enter__` 자동 시동.

10. **`iterX()` + `fetchX(limit=)` 쌍** — collection 반환 provider 메서드는 iterator family 동행. 사용자가 streaming/limited 둘 다 고를 수 있게.
    - 게이트: `tests/test_provider_iter_pairs.py`.

11. **Company context manager** — `with Company(c) as c:` 종료 시 BoundedCache evict + RSS 회수. Polars 네이티브 힙 (gc 회수 불가) 누수 차단.
    - 게이트: `tests/test_company_context.py` · 정공법 (D) Facade + (C) lifecycle inversion.

### 호출계약 룰 (1)

12. **호출계약 = 사용 · 일관·통일 · 추정가능** — 공개 표면 (facade 메서드 · `__all__` · Protocol surface) 은 세 조건 동시 만족. 위반은 "추가" 가 아니라 "정리" 대상.
    1. **사용** — 실제 consumer (코드 · CLI · server · test) 가 있어야 한다. 안 쓰는 public 은 많아 봐야 무의미 → 제거. 호출계약 등록(동결)은 *사용되는* surface 에만.
    2. **일관·통일** — 동일 도메인 내 명명 · 시그니처 · 반환형 통일. 같은 일을 하는 변종을 다중 메서드로 쪼개기 금지 (예: `topicRaw`/`topicTables`/`topicLazy`/`topicLong` → `topic(*, format=, lazy=)` 단일화). cross-provider (dart/edgar) 표면 대칭 (rule 1 Protocol 과 동행).
    3. **추정가능** — 사용자가 이름·동작·인자를 예측할 수 있어야 한다. 비대칭 alias · 도메인마다 다른 명명 · 예측 불가 surface 금지.
    - 신규 public = 사용처 동반 + 3 조건 준수 + `api.companyFacadeFrozenSurface` contract review. 미사용·중복변종·비대칭 surface 는 등록(동결)이 아니라 제거/통합.
    - 게이트: `api.companyFacadeFrozenSurface` (review 없는 신규 surface 차단) + [후속: 미사용 public 검출 · 도메인 명명 일관성 lint].

### 적용 범위

- providers/ (`dart,edgar`) 우선. `edinet` 은 API 통신 불가 deferred provider 로 strict scope 에서 제외.
- L2 6 엔진 (analysis/credit/macro/quant/industry/scan) — F-트랙 재개 시 11 룰 inherit.
- L3 story · L1.5 scan/search · L1 gather · L0 core 도 동일 적용 (단계적).

### 회귀 가드

각 룰의 게이트는 `tests/audit/_baselines/*.json` 에 현 위반 항목 기록. P-phase 통과마다 baseline 축소. 최종적으로 모든 baseline JSON 의 `sum(values) == 0` 시점에 strict 전환 완료 = "더 안 건드릴" 상태.

### Baseline Ledger

baseline JSON 은 면죄부가 아니라 부채 원장이다. 각 audit 은 기존 위반을 `known` 으로 고정하고, 신규 위반은 fail 로 처리한다.

- 대표 원장은 `tests/audit/_baselines/dartlabGuard.json` 이다.
- 신규 violation 0 이 PR 기준이다.
- baseline count 증가 0 이 PR 기준이다.
- 해결된 violation 은 같은 변경에서 baseline 을 shrink 한다.
- deferred 항목은 사유, owner, 복구 조건을 기록한다.
- `edinet` 은 API 통신 불가로 provider strict scope 에서 제외된 deferred 예시다. API 복구 전까지 placeholder 폴더나 protocol symmetry 를 강제하지 않는다.

baseline 증가, deferred 사유 누락, 해결된 위반의 baseline 미축소는 모두 품질 회귀다.

## Skill OS frontmatter 8 신규 필드 (Skill Graph)

`src/dartlab/skills/specs/**/*.md` frontmatter 에 다음 필드가 정식 등록됨 (전부 default 값 있어 기존 257 spec 무탈, 점진 마이그레이션):

| 필드 | 타입 | default | 의미 |
|---|---|---|---|
| `predecessors` | `list[str]` | `[]` | 본 skill 호출 전 거쳐야 할 skill id (역방향 successors) |
| `successors` | `list[str]` | `[]` | 본 skill 후 자연 호출 후속 skill id (recipe step 과 무관) |
| `audiences` | `dict[str, str]` | `{}` | `{"llm": "...", "agent": "...", "human": "..."}` 주체별 1 줄 |
| `isLeafNode` | `bool` | `False` | 의도적 leaf — orphan lint 면제 |
| `entryHint` | `bool` | `False` | 외부 LLM 첫 진입 후보 (MCP `start.*` 외 보강) |
| `graphTier` | `str \| None` | `None` | L0~L4 계층 hint — 그래프 클러스터 색상 |
| `cluster` | `str \| None` | `None` | 수동 그룹핑 (e.g. `gather.history`). 미명시 시 자동 도출 |
| `humanIntro` | `str \| None` | `None` | 사람용 본문 도입 1~2 문단 (랜딩 페이지 상단 별도 영역) |

작성 가이드:

- **`successors[]` vs `linkedSkills[]`** — `linkedSkills` 는 recipe step 흐름 (순서 의미), `successors` 는 일반 skill 간 자연스러운 후속 관계 (순서 X).
- **`predecessors[]`** — A 의 successors 에 B 있으면 B 의 predecessors 에 A 자동 추론 권장. `validateBidirectional` (warn-only) 가 형제 간 대칭 검증.
- **`audiences[]` 3 키** — `llm` / `agent` / `human` 키 (다른 키 무시). 본문 directive 마커 (`:::for-llm` · `:::for-agent` · `:::for-human` · `:::end`) 와 함께 3 인덱스 분기 (mcp.json · agent.json · web.json) 에 사용.
- **`isLeafNode: true`** — 자연 종점 (e.g. `engines.gather.collect` 단순 호출) 만. orphan (out-degree 0 + in-degree 0) 과 구분 — `isLeafNode` 는 *intentional* 마킹.
- **`entryHint: true`** — 외부 LLM 이 `start.dartlabSkillOs` 외 직접 진입해도 무방한 skill. MCP first-hop fetch 시 nextSkills 후보로 가중치.
- **`humanIntro`** — 1~2 문단 (200~400 자). 사람이 처음 만나는 영역 — 코드/자료 들어가기 전 맥락. 상위 50 hot spec 우선 마이그레이션.

## 본문 directive 마커 — 3 주체 분기

```markdown
:::for-llm
외부 LLM 용 짧은 도입 — < 200 토큰. 사실 + 호출 시그니처만.
:::end

:::for-agent
내부 AI 엔진 (dartlab.ask) 용 절차·예시. 호출 패턴 + 출력 검증.
:::end

:::for-human
사람 용 상세 설명·맥락·시각자료. 톤 풍부, 인과 서술 가능.
:::end
```

마커 외 본문은 3 주체 모두에게 fallback 노출. `_splitDirectives()` (`src/dartlab/skills/compiler.py`) 가 regex 추출. 마커 누락 spec 은 모두에게 동일 본문 — backward-compatible.

## Skill OS 산출물 6 종

Skill은 운영자, 사용자, 사용자가 명시적으로 위임한 에이전트가 관리한다. spec 소스를 변경하면 `src/dartlab/skills/SCHEMA.md`에 따라 산출물 6종을 명시적으로 동기화하고, commit 단위는 `operation.contributionWorkflow`를 따른다.

| 산출물 | 대상 | 결 |
|---|---|---|
| `catalog.json` | 전체 카탈로그 (landing·wheel 정본) | frontmatter + bodyPreview 1500 자 |
| `agent.json` | `catalog.json` byte-동일 legacy alias (실 리더 0) | dedup 운영자 결정 대기 |
| `mcp.json` | 외부 LLM | < 300 토큰 + nextSkills max 5 |
| `web.json` | 사람 (랜딩) | humanIntro + visualRefs + bodyHuman |
| `pyodide.json` | Pyodide | 경량 lookup |
| `graph.json` | `/skills/graph` 시각화 | nodes + edges + cycles + orphans + unreachable |

