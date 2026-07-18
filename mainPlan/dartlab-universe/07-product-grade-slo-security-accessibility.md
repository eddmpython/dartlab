# 07. 제품급 SLO, 복구, 관측성, 보안, 접근성

## 1. 기준선과 측정 원칙

현재 관측 범위는 HF 77,757파일, 약 304.5GB, capability 226개, registry axis 147개, blog 275개, HF media 3,123개다. 숫자는 고정 용량 한계가 아니라 benchmark fixture를 만드는 현재 기준선이다.

모든 SLO는 다음 환경 정보를 receipt에 남긴다.

- OS와 browser/runtime version
- CPU model과 logical core
- RAM
- GPU와 VRAM
- network profile
- cold/warm cache
- source revision set
- object, edge, tile 수
- build mode

기기 정보를 기록하지 않은 성능 숫자는 release evidence로 인정하지 않는다.

## 2. 기준 기기

### 2.1 Local data engine 기준

- 8 logical core 이상 x86-64 또는 arm64
- RAM 16GB
- NVMe SSD
- 100Mbps network, RTT 30ms simulation 별도

### 2.2 Browser renderer 기준

- desktop RAM 16GB
- discrete GPU VRAM 8GB급 기준 기기 1대
- integrated GPU 기준 기기 1대
- 1920x1080, devicePixelRatio 1과 2
- Chromium WebGPU, Firefox/Safari 또는 WebGL2 fallback 대상

실제 모델명은 benchmark report에 기록한다. 문서 단계에서 특정 제조사 성능을 보장하지 않는다.

## 3. Data engine SLO

| operation | p50 | p95 | p99 | 제한 |
|---|---:|---:|---:|---|
| full HF metadata census | 30s | 60s | 90s | payload 전체 download 0, RSS 512MB 이하 |
| warm delta census | 2s | 5s | 10s | unchanged payload read 0 |
| C2 descriptor per structured file | 300ms | 2s | 10s | projection 또는 footer 우선, bounded byte read |
| C2 resume from checkpoint | 1s | 5s | 15s | completed descriptor 재처리 0 |
| exact ID lookup | 30ms | 100ms | 300ms | local catalog |
| object detail | 80ms | 300ms | 1s | evidence locator 포함 |
| structured query | 100ms | 500ms | 2s | bounded rows |
| bounded graph traversal | 100ms | 300ms | 1s | depth와 result budget 적용 |
| capability admission | 20ms | 100ms | 300ms | engine runtime 제외 |
| snapshot digest replay | 1s | 5s | 15s | 원문 download 제외 |

full census가 60초를 넘으면 먼저 HF metadata call, pagination, concurrency, memory profile을 개선한다. 바로 manifest bake로 도피하지 않는다.

G0 metadata census와 U3 C2 descriptor crawl은 같은 SLO가 아니다. C2 전체 wall time은 file format, remote range 지원, row metadata 유무에 좌우되므로 임의의 짧은 deadline을 약속하지 않는다. 대신 30초 이내 checkpoint, bounded inflight byte, 재시작 시 완료 항목 재처리 0, item별 terminal status 100%를 제품 gate로 삼는다.

## 4. Query와 RAG SLO

| operation | p50 | p95 | p99 |
|---|---:|---:|---:|
| exact/structured candidate | 100ms | 500ms | 2s |
| hybrid retrieval without model | 300ms | 1.5s | 4s |
| RetrievalEvidencePack G4E validation | 200ms | 1s | 3s |
| interactive engine job admission | 100ms | 300ms | 1s |
| answer first progress event | 500ms | 2s | 5s |

모델 latency와 외부 provider latency는 별도 span으로 분리한다. 전체 p95가 느려도 source, retrieval, engine, model 중 원인을 식별할 수 있어야 한다.

## 5. Scene와 renderer SLO

### 5.1 Projection compute

| operation | p50 | p95 | p99 | RSS |
|---|---:|---:|---:|---:|
| current full graph root projection | 10s | 30s | 60s | 2GB 이하 |
| prior ProjectionState runtime replay | 10s | 30s | 60s | 2GB 이하 |
| 1% graph delta incremental projection | 2s | 5s | 15s | 추가 1GB 이하 |
| semantic LOD and tile envelope compile | 3s | 10s | 30s | 2GB 이하 |

U5 fixture와 current full census metadata에서 이 값을 측정한다. prior runtime replay p95 30초 또는 incremental p95 5초를 넘으면 U5B Bake Decision을 연다. persistent ProjectionState를 먼저 만드는 것은 금지한다.

### 5.2 네트워크와 메모리

- 초기 shell와 L0 manifest 압축 5MB 이하
- 단일 scene tile 압축 2MB 이하
- 동시 inflight tile 8개 이하, device profile별 조정
- browser heap steady state 1GB 이하
- GPU memory target 1.5GB 이하
- budget 초과 시 LOD와 label 밀도 하향, crash 0

### 5.3 frame과 interaction

기준 desktop release gate:

- visible proxy 250,000개와 aggregate edge 100,000개에서 median 60fps, p95 frame 25ms 이하
- point-only stress 1,000,000개에서 30fps 이상
- pointer picking p95 100ms 이하
- camera input to visual response p95 50ms 이하
- main-thread long task p95 50ms 이하
- parent-child LOD transition blank frame 0
- 30분 연속 탐색 heap 증가율 5% 이하

integrated GPU와 WebGL2 fallback은 동일 기능을 유지하되 profile별 visible budget을 낮출 수 있다. 어떤 budget을 썼는지 UI와 telemetry가 안다.

## 6. 신뢰성과 복구

### 6.1 source 장애

| 장애 | 동작 |
|---|---|
| HF repo unavailable | pinned snapshot의 locator와 stale 상태 표시, 새 snapshot 발행 금지 |
| private repo access denied | public scope만 분리 가능, full scope G0 실패 |
| 일부 file corrupt | resource CORRUPT, affected query partial, 전체 성공 금지 |
| capability runtime failure | receipt FAILED, source fact 유지 |
| blog parse failure | post resource 유지, STRUCTURED 미달 |

### 6.2 snapshot 손상

- root digest 재검증
- source revision 존재 확인
- identity ledger와 schema version compatibility 확인
- invalid snapshot은 active pointer로 승격 금지
- 이전 verified snapshot으로 즉시 rollback
- switch는 새 snapshot 완전 검증 후 atomic pointer 교체
- inflight query는 시작 snapshot으로 끝냄

U0부터 U7 attempts의 active snapshot pointer는 process-local이다. U8 stable product의 active snapshot은 `control.sqlite`에 승인된 append-only control record로 전환하며 이전 verified head를 보존한다. ProjectionState는 이전 snapshot에서 결정론적으로 runtime replay하는 것이 기본이다. replay가 SLO를 넘고 U5B 승인까지 받은 경우에만 별도 `APPROVED_DERIVED` ProjectionState pointer를 둘 수 있으며 knowledge snapshot pointer와 분리한다.

### 6.3 scene 장애

- tile digest mismatch는 폐기 후 1회 재요청
- child tile 실패 시 parent proxy 유지
- WebGPU device loss 시 buffer 재생성과 camera/selection 복구
- renderer crash 시 semantic tree mode 유지
- stale scene은 snapshot mismatch banner와 interaction 제한

## 7. 관측성

### 7.1 span

```text
universe.census.source
universe.census.reconcile
universe.identity.resolve
universe.query.plan
universe.query.structured
universe.query.lexical
universe.query.graph
universe.query.semantic
universe.execution.admit
universe.execution.run
universe.evidence.verify
universe.scene.project
universe.scene.tile
universe.renderer.frame
universe.renderer.pick
```

### 7.2 metric

- discovered, registered, failed, unresolved by source
- C0부터 C5 coverage
- broken refs와 orphan count
- identity conflict와 false merge review count
- query latency와 result count by lane
- capability admission, success, partial, timeout, cancel
- evidence coverage와 citation precision
- tile request, bytes, cache hit, decode time
- frame time, dropped frames, GPU memory, device loss
- public/private serialization rejection

### 7.3 log 금지

- HF token
- API key
- private repo path in public log
- raw filing/body 전체
- full prompt와 private context
- local absolute secret path

debug detail은 local restricted sink에만 두고 public message는 safe error code를 쓴다.

## 8. 보안

### 8.1 secret

- HF token과 provider key는 server/local process에만 존재
- browser bundle, scene payload, snapshot public JSON에 포함 금지
- config object 직렬화 전 allowlist
- error traceback의 header와 URL query redact

### 8.2 권한

모든 query, traversal, execution, evidence fetch에 visibility scope를 선적용한다. 결과를 만든 뒤 private를 제거하는 post-filter 방식은 금지한다.

```text
authorize -> plan -> retrieve -> execute -> serialize
```

cache key에도 visibility scope와 identity를 포함한다. public과 private result가 같은 cache entry를 공유하지 않는다.

### 8.3 engine sandbox

- allowlisted public capability만 실행
- arbitrary Python expression 금지
- args schema와 size limit
- 모든 engine을 worker process로 격리하고 `DARTLAB_DATA_DIR`, `DARTLAB_LINEAGE_DIR`, `HOME`, `XDG_CACHE_HOME`, `TEMP`, `TMP`를 workerRoot 아래로 재지정
- Python audit hook과 write allowlist로 workerRoot 밖 쓰기, rename, delete, subprocess, socket event를 기본 차단
- native library 또는 subprocess가 필요한 engine은 OS filesystem sandbox가 입증될 때까지 실행 불가
- 실행 전후 repo, 기존 `data/`, lineage와 user 보호 경로 digest 변화 0
- filesystem root와 capability별 network egress 제한
- timeout, cancel, resource limit
- output schema와 size 검증
- rate limit by user, capability, source

### 8.4 untrusted content

- Markdown, HTML, transcript는 instruction이 아닌 data
- HTML sanitizer와 URL scheme allowlist
- prompt injection corpus test
- model-generated tool args는 schema와 policy 재검증
- model은 canonical graph write 권한 없음

## 9. PII와 라이선스

### 9.1 PII

공시의 임원명 등 합법 공개 정보도 무제한 프로파일링 대상으로 확장하지 않는다. object kind별 최소 수집, purpose, retention, visibility를 기록한다. private 뉴스와 local artifact의 개인 식별 가능 text는 public RAG와 scene에서 제외한다.

### 9.2 라이선스

resource별 다음을 저장한다.

```text
licenseId
licenseUrl
sourceTermsRef
allowedUses
attribution
redistribution
derivativePolicy
unknownReason
reviewedAt
```

license unknown media는 public scene preview와 model context에 넣지 않는다. 외부 YouTube는 원본을 복제하지 않고 ID와 링크, 허용된 metadata만 다룬다.

## 10. 접근성

3D는 접근성 면제 구역이 아니다.

### 10.1 동등한 의미 tree

모든 visible/selected scene object는 virtualized semantic tree와 동기화한다.

- object label과 kind
- epistemic class text
- relation count와 주요 relation
- evidence count
- expand/collapse
- source original 열기

screen reader 사용자는 3D canvas 없이 같은 search, drill-down, evidence 기능을 쓴다.

### 10.2 keyboard

- Tab으로 search, filter, tree, detail 이동
- arrow key로 sibling과 parent/child 이동
- Enter로 object 열기
- Escape로 현재 mode 종료
- shortcut help 제공
- focus가 canvas 안에 갇히지 않음

### 10.3 motion과 시각

- `prefers-reduced-motion`이면 fly animation, particle motion, auto orbit 제거
- transition 없이 camera target 이동 선택 가능
- 상태를 색만으로 전달 금지
- contrast 기준 충족
- 200% zoom에서 panel과 label overflow 0
- low vision을 위한 label scale과 high contrast mode

### 10.4 3D 불가 환경

- WebGPU/WebGL2 실패 시 semantic explorer 자동 제공
- 검색, 관계, evidence, original link 기능 완전성 100%
- 3D 전용으로만 가능한 검증 작업 0

## 11. 장애 예산과 운영 판정

내부 release candidate 기준:

- catalog/query availability 99.9% local session 기준
- data corruption 허용 0
- private leakage 허용 0
- ID collision 허용 0
- evidence 없는 verified statement 허용 0
- renderer crash-free session 99.5% 이상
- device loss recovery 성공 100% test fixture

availability가 높아도 corruption, leakage, evidence 위반은 즉시 release blocker다.

## 12. 검증 도구

- Python: pytest, hypothesis, tracemalloc 또는 psutil, DuckDB profile
- source replay: pinned HF revision fixture
- contract: JSON Schema validation and mutation test
- browser: Playwright, PerformanceObserver, browser tracing
- GPU: renderer benchmark scene, device-loss simulation 가능 범위
- accessibility: axe, keyboard script, screen-reader manual checklist
- security: prompt injection corpus, serialization leakage test, dependency audit

## 13. G7 인수 기준

- 모든 SLO 측정에 환경과 source revision 기록
- full HF metadata census p95 60초, payload 전체 download 0, RSS 512MB 이하
- query p95 목표 충족
- renderer release scene 목표 충족
- snapshot rollback과 atomic switch test 통과
- private leakage와 secret log 0
- prompt injection tool escalation 0
- keyboard, semantic tree, reduced motion, non-color state 모두 통과
- 3D 없는 동등 기능 100%
- 30분 renderer memory 증가 5% 이하
