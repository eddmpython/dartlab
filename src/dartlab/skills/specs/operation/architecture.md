---
id: operation.architecture
title: dartlab 아키텍처 — 전체 청사진
kind: curated
scope: builtin
status: observed
category: operation
purpose: dartlab 아키텍처 — 전체 청사진 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - dartlab 아키텍처 — 전체 청사진
  - architecture
  - 1. 레이어 — L0→L4 (L1.5와 L2.5 dataHub 포함) 구조로 간다
  - 2. 5 L2 분석엔진 — 두 소비자를 최고로 지원한다
  - 소비자별 차이
  - 3. 모듈 제공 패턴 — analysis 기준 (5 L2 엔진 동일)
  - 4. import 방향 — L0 ← L1 ← L1.5 ← L2 ← L2.5 dataHub ← L3 하향만 허용한다
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
sourceRefs:
  - dartlab://skills/operation.architecture
procedure:
  - 1. 레이어 — L0→L4 (L1.5와 L2.5 dataHub 포함) 구조로 간다 기준을 확인한다.
  - 2. 5 L2 분석엔진 — 두 소비자를 최고로 지원한다 기준을 확인한다.
  - 소비자별 차이 기준을 확인한다.
  - 3. 모듈 제공 패턴 — analysis 기준 (5 L2 엔진 동일) 기준을 확인한다.
  - 4. import 방향 — L0 ← L1 ← L1.5 ← L2 ← L2.5 dataHub ← L3 하향만 허용한다 기준을 확인한다.
  - data는 lower owner의 metadata와 공개 callable만 소비하고 simulate, story, AI를 역참조하지 않는다.
  - '**story 가 쓸 때** — L3 조합기로서 5 L2 분석엔진 + L1.5 4 형제 (scan/frame/synth/reference) 의 calc 결과를 블록으로 변환하여 보고서에 배치. 자체 해석·계산 0 — 모든 숫자는 하위 엔진 ref. story 가 단독으로 다중 결합 책임을 짊어져 L2 끼리 직접 import 가 만드는 순환참조를 차단.'
  - '**AI 가 쓸 때** — AI 가 주체. 엔진 결과를 의심하고, 원본 (`c.show`) 으로 검증하고, override 로 재계산.'
  - 엔진은 양쪽 모두에게 최고의 재료를 제공한다. 숫자와 근거를 투명하게 반환하여 story 는 배치하고 AI 는 검증할 수 있게.
  - calc 함수는 **독립 모듈** — 다른 calc 호출 가능하지만 순환 없음.
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
  - dartlab 아키텍처 — 전체 청사진 규칙 확인
  - architecture 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: architecture
  format: markdown
lastUpdated: '2026-07-22'
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

- 1. 레이어: L0→L4 (L1.5와 L2.5 dataHub 포함 7단) 구조로 간다 기준을 확인한다.
- 2. 5 L2 분석엔진 — 두 소비자를 최고로 지원한다 기준을 확인한다.
- 소비자별 차이 기준을 확인한다.
- 3. 모듈 제공 패턴 — analysis 기준 (5 L2 엔진 동일) 기준을 확인한다.
- 4. import 방향: L0 ← L1 ← L1.5 ← L2 ← L2.5 dataHub ← L3 하향만 허용한다 기준을 확인한다.
- **story 가 쓸 때** — L3 조합기로서 5 L2 분석엔진 + L1.5 4 형제 (scan/frame/synth/reference) 의 calc 결과를 블록으로 변환하여 보고서에 배치. 자체 해석·계산 0 — 모든 숫자는 하위 엔진 ref. story 가 단독으로 다중 결합 책임을 짊어져 L2 끼리 직접 import 가 만드는 순환참조를 차단.
- **AI 가 쓸 때** — AI 가 주체. 엔진 결과를 의심하고, 원본 (`c.show`) 으로 검증하고, override 로 재계산.
- 엔진은 양쪽 모두에게 최고의 재료를 제공한다. 숫자와 근거를 투명하게 반환하여 story 는 배치하고 AI 는 검증할 수 있게.
- calc 함수는 **독립 모듈** — 다른 calc 호출 가능하지만 순환 없음.

## 7단 계층 SSOT (L0 → L4): P-CORE B 정리 결과 반영

| Layer | 구성 | 역할 |
|---|---|---|
| L0 | `core` | L0 primitive 만: logger·env·types·memory·polarsUtil·formatting·constants·protocols·naming·utils·cache·di·credentials·dualAccess·palette·**accounts**·**ratios** + DIP Protocol (disclosureFetcher·gatherProvider·financeDocAccessor·listingResolver). 상위 import 금지. **`accounts`** = 계정 정규화 단일 SSOT (DART 12단계 + EDGAR tag + 라벨 cascade + snakeId alias). **`ratios`** = DART/EDGAR가 같은 정규화 시계열에 적용하는 순수 재무비율 공식 SSOT. 두 provider가 공유해야 하는 데이터 기반 primitive만 L0에 둔다. |
| **L1 (ETL 스테이지 분할)** | `gather` · `providers` | **gather = Extract** (모든 외부 네트워크 fetch → raw: DART OpenAPI·EDGAR/SEC client·키풀·submissions/facts/docs/bulk/universe/FTS). **providers = Transform(raw→parquet build) + Load(parquet→DataFrame read)** — HTTP 클라이언트 import 0 ([tests/architecture/test_providers_no_network.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_providers_no_network.py) 강제). core 만 import, **gather ↛ providers 상호 import 금지**. EDINET 은 별도 제3 규제기관(API 통신 불가). |
| **L1.5 (가공 4 형제)** | `scan` · `frame` · `synth` · `reference` | raw 생산 0, 책임 분리 가공기. core·L1 만 import. **4 형제끼리 cross import 금지** ([tests/architecture/test_l15_no_cross_import.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_l15_no_cross_import.py) 강제). 책임: scan=횡단면 (한 metric × 다수 회사), frame=raw 결합 (panel/시계열 view — `disclosureDiff` 등 동일 회사 N-1 vs N 보고서 sentence-level diff 포함), synth=분석 후처리·매칭·시나리오, reference=정적 JSON 룩업+매핑 엔진 |
| **L2 분석엔진 (5)** | `analysis` · `credit` · `macro` · `quant` · `industry` | 단일 도메인 분석. core·L1.5 만 import. L1 직접 import 는 L1.5 에 없는 raw 가 필요할 때만 예외. **다른 L2 직접 import 금지** (도메인 격리 + 순환참조 방지) |
| **L2.5 데이터 플랫폼** | `dataHub` | L1, L1.5, L2 owner의 metadata와 공개 callable을 자동 발견해 catalog, bounded query, typed projection, PIT gate, lineage를 제공. source와 계산을 복제하지 않는다. `simulate`, `story`, `ai` 역참조 금지 |
| **L3 조합기와 시뮬레이터** | `story` · `simulate` | story는 하위 결과를 보고서로 조합한다. simulate는 `dataHub` snapshot을 소비해 조건부 경로를 계산한다. 둘 다 dataHub보다 위에 있고 dataHub가 이들을 import하지 않는다 |
| L4 소비자 | `ai` · `mcp` | dartlab 라이브러리 직접 호출 — AI 자율 추론 + tool 사용 (ai) · 외부 LLM 진입 (mcp). 엔진 결과를 의심·검증·재계산 |
| 표현/전송 헬퍼 (sink) | `viz` · `cli` · `server` · `channel` · `pipeline` | 비즈니스 로직 0 — 모든 계층 결과를 다른 매체로 표현/조합. viz=차트·excel·html 렌더, cli=CLI wrapper, server=HTTP host, channel=외부 공유, **pipeline=수집 오케스트레이션**(gather fetch + providers build + HF upload 합법 조합 — 흩어진 sync 스크립트의 in-library SSOT, `dartlab sync`·`python -m dartlab.pipeline`). import 룰은 L4 와 동일(모든 하위 OK)이지만 책임 분리. sink 자격은 `SINK_HELPERS`+`PRIMARY_PACKAGES` 등록(`test_pipeline_sink`)으로 강제 |

import 정책 (P-CORE B 정리 결과):

1. **상하 단방향 절대 강제**: `L0 ← L1 ← L1.5 ← L2 ← L2.5 dataHub ← L3 ← L4` (CI lint와 DataHub purity audit로 강제).
2. **L1 cross import 금지 (ETL 단방향)**: gather ↛ providers AND providers ↛ gather ([tests/architecture/test_l1_no_cross_import.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_l1_no_cross_import.py)). 두 L1 의 통신 채널은 셋뿐 — **(a) 디스크 raw artifact, (b) core DIP Protocol seam** (`core.dartClient`/`dartBuild`/`edgarClient`/`edgarBuild` — gather/providers 가 import 시점에 register, 소비자는 core 경유로 위임 호출), **(c) sink-layer orchestration** (`pipeline`·`cli`·`.github/scripts/sync/*` — gather fetch + providers build + HF upload 조합). 정본은 in-library **`dartlab.pipeline`**(L4 sink, `runStage`/`runPipeline`) — 로컬 `dartlab sync` 와 CI `python -m dartlab.pipeline` 가 동일 SSOT 호출. 옛 `.github/scripts/sync/*` 는 점진적으로 그 stage 로 흡수 — **edgar/allFilings/dartZip/edgarPanel·macro 는 in-library 흡수 완료(스크립트 = thin shim·로직 중복 0), 잔여 dart/news 는 전환기 stage 가 동형 호출(`runScript`)**. providers build 가 gather fetch 를 트리거해야 하면 core seam 으로 위임(예: `convertQuarterlyToParquets` zip 부재 시 `core.edgarClient.downloadQuarterlyDataset`). 정공이지 우회 아님.
3. **L1.5 4 형제 cross import 금지**: scan ↛ frame ↛ synth ↛ reference ([tests/architecture/test_l15_no_cross_import.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_l15_no_cross_import.py)). core 잡동사니화 재발 방지.
4. **L1.5 진입 룰**: 새 모듈 추가 시 ≥ 2 분석엔진이 같은 형태로 사용해야 함 ([tests/architecture/test_l15_entry_rule.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_l15_entry_rule.py)). 1 개만 쓰면 그 분석엔진 owner.
5. **core L0 only**: core/ 가 상위 계층 import 금지 ([tests/architecture/test_core_l0_only.py](https://github.com/eddmpython/dartlab/blob/master/tests/architecture/test_core_l0_only.py)). di.py 만 lazy import 예외.
6. **양방향 cycle 절대금지**: `tests/audit/cycleScan.py` CI 강제 (양방향 2-cycle + 3+ 모듈 cycle 검출).
7. story 가 다중 L2 소비 책임 잔존 (조합기) — 그러나 단방향 sibling import 도 도메인적 자연 의존이면 허용.
8. **별도빌드 금지**: 모든 외부 데이터 수집과 빌드는 owner SSOT를 경유한다. 수집은 `gather`, provider transform/load는 `providers`, 횡단 prebuild는 `scan`, orchestration은 `pipeline`이 소유한다. `dataHub`는 이 로직을 재구현하지 않고 catalog와 query로 연합한다. `.github/scripts/{sync,meta}/*`도 owner 공개 함수에 위임한다.

### DartLab DataHub 경계

- 각 L1, L1.5, L2 owner는 자기 package의 `dataProduct.py`에 plain metadata mapping만 선언한다. lower owner가 `dartlab.dataHub`를 import하면 계층 역전이다.
- `dataHub`는 중앙 엔진 이름 목록을 소유하지 않는다. owner provider를 발견해 registry와 callable asset을 derived catalog로 만든다.
- public axis는 `catalog`, `query` 둘뿐이다. factor, records, graph, narrative, resource는 query projection이다.
- `dataHub`는 source owner나 계산 owner가 아니다. 직접 parquet reader, Company loop, simulate, story, AI import를 금지한다.
- `simulate`는 `dataHub`를 소비할 수 있고 data snapshot, contract hash, lineage, receipt를 결과에 보존한다. 반대 방향은 금지한다.
- private, nested, bulk resource 정책과 전체 query row, byte, time, asset, subject 예산은 dataHub 실행 경계에서 fail-closed로 적용한다.

### L0~L1.5 완료 게이트 (2026-05-13)

L0~L1.5 는 "정리했다" 가 아니라 다음 gate 가 모두 통과해야 완료다.

- `tests/architecture/*` 는 repo root 의 실제 `src/dartlab` 를 검사한다. 빈 경로 통과 금지.
- `tests/architecture/test_core_l0_only.py` — core 의 상위 계층 import 0.
- `tests/architecture/test_l1_no_cross_import.py` — gather/providers module-level cross import 0.
- `tests/architecture/test_l15_no_cross_import.py` — scan/frame/synth/reference sibling import 0.
- `tests/architecture/test_import_direction.py::test_l0_l15_import_direction_strict` — L0~L1.5 가 상위 계층을 직접 import 하지 않는다.
- `tests/audit/cycleScan.py --strict-toplevel` — top-level package cycle 0.
- provider strict scope 는 `dart,edgar` 이다. `edinet` 은 API 통신 불가 상태라 복구 전까지 deferred provider 로 제외한다.

### Guard Index architecture 수집 항목

Guard Index 는 기존 architecture pytest, import-linter, audit scripts 를 같은 graph 로 묶는 공식 실행 표면이다. 현재 v1 은 stdlib AST index 와 기존 audit wrapper 로 구성하며, 최소한 다음 항목을 전수 수집한다.

- module path, layer, owner
- import graph
- L1 cross import
- L1.5 sibling import
- core upper import
- public re-export surface
- provider folder mirror
- tests mirror
- stable API manifest

`tests/architecture/*`, `pyproject [tool.importlinter]`, `tests/audit/*Gate.py` 는 같은 architecture graph 를 바라보는 방향으로 유지한다. L0~L1.5 완료 확인은 다음 명령을 기본 entry 로 쓴다.

```bash
python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar
```

### 5 L2 분석엔진 도메인 격리

| Engine | 담당 질문 | 범위 |
|---|---|---|
| `analysis` | 이 회사는 무엇으로 돈을 벌고, 어떻게 남기고, 지금 가격이 어느 정도인가 | 단일 기업 재무제표 22 축 |
| `credit` | 이 회사가 부도 날 가능성·재무 건전성은 | 단일 기업 dCR 등급 + 7 축 |
| `macro` | 시장·경제 환경은 어느 국면이고 다음 시나리오는 | 시장 레벨 6 막 인과 |
| `quant` | 가격·팩터·전략의 정량 신호와 백테스트는 | 가격·수급·공시 텍스트·포트폴리오 |
| `industry` | 이 종목이 밸류체인 어느 공정·peer 그룹에 속하는가 | 산업 분류 + 공정 매핑 + lifecycle |

### L2 단방향 의존성 그래프 (허용 + 추적)

| 화살표 | SSOT 위치 | 사용 사례 |
|---|---|---|
| analysis → industry | industry.Sector / SectorParams | 재무 분석이 산업 분류·peer 사용 |
| analysis → macro | macro.scenario / riskPremiums | proforma·forecast 가 ERP·시나리오 탄성 사용 |
| credit → industry | industry.Sector | chsFeatures 가 산업별 default rate 보정 |
| macro → credit | credit.crisisDetector / excessBondPremium / creditCycle | crisis 감지가 spread 사용 |

**금지**: 위 화살표의 역방향 import (양방향 cycle). `tests/audit/cycleScan.py` CI 강제.

분석엔진 ↔ 분석엔진 cycle 발생 시 해소 패턴 4 가지:
1. 호출자 inversion (호출 측이 결과 미리 전달)
2. 공통 logic 을 core/calcs 강등 (외부 L2 의존 0 + 순수 함수 + ≥ 2 엔진 사용)
3. story 위임 (조합 책임)
4. importlib 동적 호출 (cycleScan 의 AST 검사 우회 — analysis ↔ credit 잔존 cycle 에 적용)

> **동적 import 가드 (debt-honesty P1-7)** — 위 pattern-4 importlib 는 정적 AST 가드를 우회한다(설계상). `test_l2_no_cross_import`·`test_l15_no_cross_import` 의 `*_no_new_dynamic_cross_import` 가 `import_module("dartlab.X")` 문자열 import 를 탐지해 baseline(`_baselines/l2DynamicImport.json`·`l15DynamicImport.json`) 대비 *신규* 동적 cross 만 차단한다(ratchet). L2 baseline 5 = 위 sanctioned cycle-break(analysis→macro §172 + credit→macro·analysis pattern-4). **L1.5 baseline 3(synth→frame/scan)은 sanctioned 아닌 추적 부채** — pattern-4 는 L2 전용이라 L1.5 형제 cross 엔 sanction 이 없다. 해소 = 호출자 inversion(L2 가 sector params·scan 데이터를 synth 에 주입).

### 명명 alias 금지 (operation.philosophy §5)

- "6 분석 엔진" 표현 금지 — 5 L2 분석엔진 + L3 조합기 (story) 분리 명시.
- "매퍼 엔진" 단독 표현 금지 (industry) — `L2 분석엔진 (산업 매퍼)` 형식.
- scan 을 "L2" 라고 부르지 않는다 — `L1.5` (전체 횡단).
- story 를 "분석 엔진" 또는 "L2" 와 평탄화하지 않는다 — `L3 조합기` 명시.

## Provider Protocol 동일 surface (3-provider mirror)

P-트랙 박음: dart/edgar/edinet 3 provider 는 동일 Protocol contract 만족. 새 regulator (SGX, FSA 등) = Protocol 구현체 drop-in.

### Protocol 4 + CompanyProtocol 확장

| Protocol | 책임 | 핵심 메서드 |
|---|---|---|
| `DocsProvider` | 공시 본문 + 섹션 메타 | `fetchFiling(stockCode, *, period)`, `listSections(...)`, `iterSections(...)` |
| `FinanceProvider` | XBRL / 재무제표 정규화 | `fetchStatements(stockCode, *, period, kind="annual", limit=100)`, `listAccounts(...)`, `iterAccounts(...)` |
| `FilingsProvider` | 공시 검색·메타 | `search(query, *, market=None, limit=20)`, `iterSearch(...)` |
| `MemorySafeProvider` | 메모리-safe surface (공통) | `cleanupCache() -> int`, `memorySnapshot() -> dict` |
| `CompanyProtocol` 확장 | lifecycle | `__enter__()`, `__exit__()` 추가 |

### 폴더 mirror 골격 (dart 기준, edgar/edinet 동일 정렬)

```
providers/{dart,edgar,edinet}/
├── __init__.py        # __all__ + Company facade re-export
├── company.py         # Company 진입점 (CompanyProtocol 구현)
├── accessor/          # docsAccessor · financeAccessor · profileAccessor · reportAccessor
├── builder/           # filingsCatalog · financeStatementBuilder · scanAggregator · dataDispatcher
├── parse/             # viewerPageExtractor · tableHorizontalizer · diffEvaluator
├── ops/               # calendar · insiderTrades
├── docs/              # 공시 본문 파싱 (DocsProvider 구현)
├── finance/           # XBRL 정규화 (FinanceProvider 구현)
├── openapi/           # raw HTTP client
├── report/            # 정형 report (옵션)
├── filings/           # 공시 검색·메타 (FilingsProvider 구현)
└── search/            # 도메인 검색 (옵션)
```

누락 폴더는 placeholder `__init__.py` 만 (Protocol satisfaction 위해). edinet 처럼 일부 폴더 미보유 가능 — 단, 노출 surface 는 Protocol contract 만족 (stub + NotImplementedError 명시).

### 메모리-safe surface

cross-company query 는 raw parquet lazy scan 금지. 모든 provider 가 `data/{provider}/scan/docsIndex.parquet` 슬림 인덱스 빌드 + `Scan.docsSections(market=..., limit=...)` 단일 API 노출. Company facade 는 context manager — `with Company(c) as c:` 종료 시 BoundedCache evict 자동.

상세는 `operation.code` "11 룰" 섹션 참조.

### providers 레이어 god 격차 분해 트랙 (debt-honesty P3-1 — 위임·점진)

- **측정**: providers 76.7K줄(raw)/61.9K(유효) = frame 대비 **~82배** (dart 하위만 49.9K). 목표 = 레이어간 ≤10배.
- **근인**: providers 가 panel/finance/search 데이터 owner 라 로직이 집중. 14 sub-namespace 로 자연 분기.
- **분해 순서**(재구현 아닌 *위치 이동* — HF 경로·consume seam 불변 전제): ① search(~7K) → frame/synth 또는 빌드레이어 ② panel pivot → frame ③ finance pivot → synth. Company facade frozen surface(`checkProviderCompanyFrozenSurface`)·CompanyProtocol 보존이 불변 가드.
- **추적**: `tests/audit/moduleSizeAudit.py --max-ratio N` 으로 격차 측정 (현재 미배선 advisory — strict 배선은 legit provider 증가까지 차단해 노이즈라 점진 도입). 실행은 frontend-refactor-loop·company-analysis-report 백로그 위임. 본 PRD 는 *순서·측정* 박제만.

Skill 은 운영자·사용자·사용자가 명시적으로 위임한 AI 가 관리하고 개발한다. 산출물 6 종은 spec 변경 의도에 맞춰 같은 변경 단위에서 명시적으로 갱신한다.

| 산출물 | 대상 | 결 |
|---|---|---|
| `src/dartlab/skills/catalog.json` | 전체 검색 카탈로그 (landing·wheel 정본) | frontmatter + body preview 1500 자 |
| `src/dartlab/skills/agent.json` | `catalog.json` byte-동일 legacy alias (실 리더 0) | dedup 운영자 결정 대기 |
| `src/dartlab/skills/mcp.json` | 외부 LLM (MCP first hop) | < 300 토큰 + nextSkills max 5 |
| `src/dartlab/skills/web.json` | 사람 (랜딩) | humanIntro + visualRefs + bodyHuman directive 분리 |
| `src/dartlab/skills/pyodide.json` | 브라우저 Pyodide | 경량 lookup |
| `src/dartlab/skills/graph.json` | 그래프 시각화 (`/skills/graph`) | nodes 257 + edges 1337 + cycles + orphans + unreachable |

`graph.json` 은 `dartlab.skills.graph.buildSkillGraph(specs)` 직렬화 형태와 정합해야 한다. 진단 결과 (cycle/orphan/unreachable) 는 `dartlab.skills.graphLint` 가 `listSkills` 1 회 warn-only 로 노출 (env `DARTLAB_SKILL_GRAPH_LINT=0` 으로 silence). phase 1 (warn) → phase 2 (신규/수정 차단, env `DARTLAB_SKILL_GRAPH_LINT_STRICT=1`) → phase 3 (전수 차단).

본문 directive 마커 (3 주체 분기):

```markdown
:::for-llm
외부 LLM 용 짧은 도입. < 200 토큰.
:::end

:::for-agent
내부 AI 엔진 용 절차·예시.
:::end

:::for-human
사람 용 상세 설명·맥락·시각자료.
:::end
```

마커 없는 본문은 3 주체 모두에게 동일 노출 (fallback). 상세: `operation.code` "frontmatter 8 신규 필드" 섹션 + [.claude/skills/skill-os-add/SKILL.md](file://./.claude/skills/skill-os-add/SKILL.md).

