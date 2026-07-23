# DartLab Universe U0~U6

상태: U0 full census, U1 identity와 provenance, U2 capability execution kernel, U3 전수 catalog와 evidence graph, U4 하이브리드 검색과 불변 근거 팩, U5 runtime-only 3D projection과 semantic LOD, U6 GPU transport와 독립 3D 검수 GUI가 live gate를 통과했다. U4는 전체 블로그 AST와 기존 DART, EDGAR, 뉴스 content index를 검색하고, DART와 EDGAR capability를 실제 고정 입력으로 실행해 Arrow 결과와 영수증을 재생 검증한다. 손상된 upstream parquet 1건은 원본 상태를 숨기거나 외부 저장소를 수정하지 않고, 고정 raw authority와 historical transform을 사용한 Universe 전용 recovery receipt와 CAS로 복구했다. U6 GUI는 `/universe` 직접 주소와 loopback session token으로만 열리며 메뉴, 카드, 공개 버튼에는 연결되지 않았다. 답변 생성과 RAG, 영속 projection과 tile도 아직 없다.

이 디렉터리는 이전 Universe 실험을 전부 제거한 뒤 `mainPlan/dartlab-universe/`의 제품 계약에 맞춰 처음부터 다시 만든 데이터 엔진 경계다. 기존 `src/dartlab`, `ui`, `landing`, `blog`, `media`는 수정하지 않고 authority로 읽기만 한다.

## 현재 구현 범위

- `HF_REPO`, `HF_MEDIA_REPO`, 모든 `DATA_RELEASES[*].repo`의 동적 합집합
- private repo를 포함한 Hugging Face dataset revision, path, oid, byte, format 전수 census
- payload body 다운로드 0
- `dartlab.capabilities()`와 analysis, credit, industry, macro, quant, scan, story registry 병렬 census
- 블로그 post, companion, podcast 전수 parse
- 중앙 media catalog, HF object tree, 블로그 reference 양방향 reconciliation
- configured repo 누락, access denied, metadata 누락, 미분류 format, media 누락과 broken ref의 fail-closed G0
- canonical JSON과 같은 revision의 결정론적 snapshot digest
- 기존 시스템 보호 path byte digest 검사

## U1 구현 범위

- Unicode NFC, UTC, finite float 규칙을 가진 canonical JSON
- `du:v1:{kind}:{sha256}` logical ID와 revision-specific version ID
- DART corpCode와 SEC CIK를 법인 anchor로 분리한 identity ledger
- stockCode, ticker, 회사명은 validity를 가진 alias로 보존
- 동명이인, 교차상장, 합병, 분할 후보의 자동 merge 금지
- K-IFRS와 US-GAAP concept mapping basis 분리
- valid time과 known time을 동시에 거르는 PIT query
- correction, retraction, blog rewrite, revision-scoped row locator replay
- SHA-256 local CAS와 dirty worktree byte capture
- optimistic head, hash chain, append-only trigger를 가진 `control.sqlite`
- concurrent head, supersede, database corruption, CAS 누락과 digest mismatch 차단
- U0, identity collision, snapshot replay, temporal leakage, control integrity를 결합한 machine-readable G1

## U2 구현 범위

- runtime capability와 analysis, credit, industry, macro, quant, scan, story registry 합집합 전 후보 분류
- runtime에 누락된 analysis 22축을 `CALLABLE_UNMIRRORED`로 숨김 없이 보존
- runtime mirror에만 있고 actual registry에 없는 `scan.industry`, `scan.market`을 `MIRRORED_MISSING`으로 실행 차단
- preview, 내부 helper, Company-bound deferred surface를 explicit gap reason과 함께 실행에서 차단
- public dispatcher signature, registry module, 실제 axis implementation byte에 결박된 `SchemaDescriptor`
- `**kwargs`와 `Any`를 추측하지 않는 schema closure와 widening mutation 차단
- source byte digest가 바뀌면 descriptor를 `STALE`로 내리는 freshness 검증
- snapshot, target, visibility, budget, args, seed, idempotency 순서의 fail-closed admission
- 전용 subprocess worker와 HOME, TEMP, data, lineage, cache, output write redirect
- Python audit hook 기반 allowlist 밖 write, subprocess, socket 차단
- JSON canonical output과 DataFrame Arrow IPC output 분리
- timeout, cancel, transient retry, partial row, output byte budget 계약
- SQLite claim과 성공 receipt partial unique index를 사용한 durable idempotency
- CAS object 선commit 뒤 receipt transaction, crash orphan quarantine 복구
- 기존 simulator `AdmissionVerifier`를 통한 signed receipt tree 검증
- receiptVersion, kind, ruleId, ruleVersion, ruleHash, issuerExecutableHash exact schema descriptor
- allowlisted decoder digest, subject binding, parent role, seed, snapshot, assumption, asOf, vintage 검증
- 해석 불가 artifact를 `VERIFIED_ARTIFACT_UNINTERPRETED`로 닫고 execution과 graph 승격 차단

## U3 구현 범위

- HF file, blog, companion, media catalog, DART와 EDGAR identity, engine capability를 하나의 catalog로 결합
- 원본 payload 복제 없이 revision, locator, selector, content digest만 보존
- Parquet, Arrow IPC, JSON, JSONL, CSV와 기타 분류 형식의 bounded range descriptor
- schema fingerprint, row count 또는 명시적 unavailable reason, response digest의 terminal C2 계약
- SQLite lease, heartbeat, exact receipt, content-addressed receipt, 실패 attempt ledger를 가진 resume checkpoint
- 인증, transport와 parser 오류는 재시도하고 성공 receipt만 content cache로 승격
- catalog root와 descriptor set을 결박한 immutable snapshot, tombstone delta와 replay 검증
- 대형 snapshot을 중간 JSON tree 없이 계산하는 byte 동일 canonical streaming hash
- Arrow batch를 ephemeral DuckDB에 투영하고 visibility 교집합으로 exact resource와 object evidence pack 조회
- object, evidence, identity, alias, capability를 연결하는 typed relation taxonomy와 bounded graph traversal
- 알려지지 않은 endpoint, empty visibility, 미래 정보, 근거 누락, 가시성 누출을 fail-closed 차단
- 고정 revision 무결성과 지속 수집원의 HEAD freshness를 분리한 snapshot 계약
- 원본 `PARSE_ERROR`를 그대로 보존하면서 raw source object, historical transform source, derived CAS artifact를 결박하는 recovery receipt
- Git object OID와 실제 LFS payload SHA-256을 각각 검증하고, 전체 Parquet batch read와 schema, row, footer를 확인하는 fail-closed recovery validator
- repository HEAD가 바뀌어도 path, OID, byte size가 모두 같은 object만 현재 resource version에 재결박하는 SQLite recovery store
- descriptor set과 recovery set을 함께 결박한 catalog snapshot v3
- cold projection, lookup, object detail, graph traversal, snapshot replay의 p50, p95, p99 SLO receipt

## U4 구현 범위

- 비신뢰 질문 원문을 저장하지 않고 NFC search term, explicit identifier, SHA-256 digest로 축소하는 query 계약
- exact, structured, lexical, graph, contradiction 다섯 레인을 고정한 allowlist-only planner
- 질문 문장만으로 capability execution이나 외부 tool call을 만들 수 없는 UI-less runtime
- policy마다 resource, object, evidence provenance closure를 먼저 축소하는 visibility pre-filter
- DART corpCode, SEC CIK, 종목 코드, Universe ID, resource locator의 exact lookup
- object, source, resource kind와 subject, predicate, period, instant의 structured filtering
- 영속 index나 source payload 복제 없이 process-local metadata posting을 쓰는 한국어와 영어 lexical retrieval
- valid time, known time, visibility, node, edge, depth budget을 적용한 evidence graph traversal
- conflict group과 `CONTRADICTS` relation을 항상 별도 탐색하는 contradiction lane
- deterministic reciprocal-rank fusion과 lane별 score provenance
- 모든 현재 Markdown을 runtime에 다시 parse해 frontmatter, heading, paragraph, table, code, image, link, 외부 영상을 원래 path와 line, AST path에 결박하는 블로그 AST adapter
- 현재 41만 건 규모인 기존 DART, EDGAR, 뉴스 content index를 manifest resource에 결박하고 raw snippet 대신 digest와 source selector만 근거 팩에 넣는 content search adapter
- 별도 `CapabilityRequest`가 있을 때만 U2 admission, sandbox, CAS, receipt 경로로 검증된 엔진을 실행하고 execution ref를 근거 팩에 결박하는 capability adapter
- candidate와 contradictory evidence를 분리하고 locator, source revision, snapshot root, descriptor set, recovery set을 결박한 immutable `RetrievalEvidencePack`
- pack digest, query plan, visibility, source revision, locator, content digest, virtual evidence resolver, execution receipt, lane coverage를 모델 없이 재생하는 G4E validator
- query text의 prompt injection이 capability, subprocess, socket, 외부 tool call로 승격되지 않는 회귀 검증

U4 query engine과 G4E 계약은 fixture와 live 전체 corpus golden query, 품질, leakage, latency gate를 통과했다. U5와 U6는 이 검증된 snapshot을 하나의 결정적 3D 우주와 GPU runtime으로 변환한다.

## U5 구현 범위

- source가 아니라 의미 family와 stable hash shard를 쓰는 하나의 전체 Universe community hierarchy
- 오른손 Y-up, root half extent 1,000,000 Q, round-half-even 정수 좌표
- 64 Q 안전 슬롯과 ID-derived 3D jitter를 사용한 결정적 충돌 회피
- 이전 ProjectionState 좌표 pin, community retained, split, merge, retired lineage
- L0 root, L1 family, L2 cluster, L3 object, L4 resource, L5 row와 evidence 지연 해소 경로
- object, kind, source, epistemic, verification, period, statement, evidence, relation type과 direction 100% 보존 assertion
- 2MB 이하 deterministic MessagePack runtime tile과 scene, snapshot, visibility, generation envelope 결박
- tile content digest, parent advertisement, stale binding, selected object, z=0 평면 붕괴의 fail-closed 검증
- current full graph 30초, prior replay 30초, two-snapshot 1% delta 5초, RSS 2GB machine threshold
- 동일 입력 좌표 digest equality, normalized displacement p95 2% 이하, cluster continuity 98% 이상
- `EPHEMERAL` ProjectionState만 허용하고 승인 없는 coordinate map과 tile 영속화 0

U5 live 판정은 `%LOCALAPPDATA%/DartLab/universe/control/u5/latest.json`의 digest 결박 report가 정본이다. report는 좌표나 tile payload를 저장하지 않는다.

## U6 구현 범위

- U5 SceneTile을 고정 stride node 28 bytes, edge 32 bytes의 GPU binary bundle로 변환
- WebGPU renderer와 validation scope, 실제 frame pixel probe, 실패 시 WebGL2 자동 전환
- 전체 우주에서 L2 은하계 overview를 streaming하고 선택한 은하계의 L3 실제 객체로 drill-down
- 회전, 확대, 키보드 이동, 노드 선택, 상위와 전체 복귀, 이름과 관계 표시 제어
- 320px부터 desktop까지 재배치되는 full-screen 3D GUI와 dark, light theme 대응
- 원본 ID와 locator는 보존하면서 화면에는 사람 친화적인 한국어 family와 resource 이름을 제공하는 display adapter
- manifest, source tile digest, binary record digest, metadata cardinality와 child tile closure 전수 검증
- loopback host allowlist, fragment session token, constant-time 비교, no-store와 strict CSP
- 외부 asset 0, 직접 route 연결 1, route 밖 공개 진입 링크와 버튼 0
- U5 full projection observer를 사용해 U5와 U6가 같은 in-memory snapshot과 projection을 원자적으로 검증
- `EPHEMERAL` transport만 허용하고 승인 없는 GPU payload, coordinate map과 tile 영속화 0

U6 live 판정은 `%LOCALAPPDATA%/DartLab/universe/control/u6/latest.json`의 digest 결박 report가 정본이다. U6 gate는 동일 실행의 U5 report도 `%LOCALAPPDATA%/DartLab/universe/control/u5/latest.json`에 원자적으로 갱신한다.

## 정본 명령

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/census.py --all --strict --format json
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u5Gate --strict
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u6Gate --strict
```

명령은 token을 출력하지 않으며 canonical JSON만 stdout에 쓴다. 결과를 보존하려면 shell redirect나 CI artifact를 사용한다. repo 안에 census 산출물을 bake하지 않는다.

## 2026-07-18 live 인수 기록

아래 값은 제품 상수가 아니라 당시 live authority 관측값이다.

| 항목 | 관측값 |
|---|---:|
| configured HF repo | 4 |
| HF file | 77,875 |
| HF byte | 307,065,890,133 |
| runtime capability | 226 |
| registry record | 141 |
| blog post | 275 |
| companion | 353 |
| media object | 3,120 |
| podcast | 13 |
| terminal coverage | 100% |
| payload body read | 0 |
| wall clock | 36.95초 |
| Python peak memory | 184,231,482 bytes |
| G0 | PASS |

관측 snapshot digest는 `49673d54447f56ca7b67539ab88e90366275f8f13cd965e15a5eb8aecb17108e`다. 다음 실행은 설정과 remote revision을 다시 읽으므로 개수와 digest가 자동으로 달라질 수 있다.

## 2026-07-18 U1 identity 인수 기록

| authority | entity | alias | listing alias | source SHA-256 |
|---|---:|---:|---:|---|
| OpenDART corpCode | 118,508 | 240,013 | 3,977 | `afbba6621121beea97fefcf1999e957c9d1faf0b2c4eab751727aa49ad09020b` |
| SEC ticker and CIK | 8,023 | 18,460 | 10,436 | `4eac70ff311ca08a01cf3989fdc021ce4164287354e2ecdcfd7cfc35c629f55d` |

총 126,531개 법인 identity의 canonical collision, source 내부 duplicate, DART와 EDGAR 사이 ID collision은 모두 0이다. 숫자는 현재 local authority byte의 관측값이며 상수가 아니다.

live G1은 private HF G0, 현재 Git source 600개 이상, DART와 EDGAR local authority, dirty byte의 임시 CAS 복원을 하나의 snapshot으로 묶는다. `NONREPLAYABLE`, 잘못된 control head, 다른 snapshot의 replay report, 미래 정보 leakage, false merge가 하나라도 있으면 통과하지 않는다.

최종 live G1 관측:

| 항목 | 관측값 |
|---|---|
| HF file | 77,875 |
| HF byte | 307,066,041,763 |
| Git source input | 675 |
| dirty and local CAS object | 54개, 15,449,111 bytes |
| replayability | `LOCAL_CAPTURED` |
| U0 snapshot digest | `4f8e75ab58d73d1852bc31177993018128aa5009120daced70ddb681e0d6e52a` |
| Universe snapshot ID | `du:v1:snapshot:e758250139d9ef1a8dd6cadb98cf1c375bfeb01161f44d1e308bf6977e963900` |
| G1 digest | `e0ed03dbdbc4dc7846109f425eb0a869e054cd348e76645a3ddbc35d18ce8e28` |
| G1 | PASS |

U1은 아직 verified statement를 admission하지 않으므로 live statement contract 분모는 `NOT_APPLICABLE`이다. 이를 100%로 위장하지 않는다. Statement와 evidence validator 자체는 positive, mutation, future leakage, correction, retraction fixture로 검증한다.

## 2026-07-19 U2 live G2 인수 기록

아래 수치는 현재 live runtime과 registry source에서 다시 계산한 관측값이며 제품 상수가 아니다.

| 항목 | 관측값 |
|---|---:|
| discovered capability candidate | 260 |
| classified candidate | 260 |
| eligible callable | 147 |
| validated SchemaDescriptor | 147 |
| blocked eligible | 0 |
| invented axis | 0 |
| catalog coverage | 100% |
| execution readiness | 100% |
| capability census digest | `ae9cc4fd72a7a87c7470245882c31aae029a2ddf6b4ef032b32da1778cfa268a` |
| capability registry digest | `8a8288773737c2331f1005a6ec71e8112d4a836ec229541917b1d72be72bde24` |
| G2 digest | `7392533efe6e3d86671f229d15062fe986807f75a6af200200aa3c42f72a324c` |
| G2 | PASS |

비네트워크 Universe 회귀 81개와 dirty source를 다시 capture한 live G1이 함께 통과했다. U2 mutation에는 fake axis, registry drift, schema widening, source drift, invalid args, snapshot mismatch, ambient secret 제거, timeout, cancel, retry, concurrent idempotency, partial Arrow와 JSON output, 보호 경로 write, subprocess, output schema mismatch, CAS orphan이 포함된다. Simulator mutation에는 unknown issuer, broken parent chain, missing artifact, unknown schema, stale decoder, artifact schema version, subject mismatch, parent role mismatch, missing seed, snapshot mismatch, vintage와 step contract mismatch, `OBSERVED` leakage가 포함된다.

## 2026-07-19 U3 live 인수 기록

아래 값은 `eddmpython/dartlab-data@a5139face25d8ef4abf60112c601c922d81bec14`를 포함한 네 저장소의 고정 revision 관측값이다. 상류 HEAD가 전진해도 이 snapshot은 같은 commit SHA로 재생되며, 다음 수집이 delta를 만든다.

| 항목 | 관측값 |
|---|---:|
| HF candidate와 terminal descriptor | 78,034 |
| HF discovered byte | 310,962,703,798 |
| eligible descriptor | 74,260 |
| directly described eligible | 74,259 |
| recovered eligible | 1 |
| explicit unsupported | 3,774 |
| parse error | 1 |
| full catalog resource | 211,771 |
| catalog object | 211,771 |
| catalog evidence | 211,771 |
| identity entity | 126,531 |
| typed relation | 291,061 |
| catalog, object evidence, relation coverage | 100% |
| schema와 row contract coverage | 100% |
| source payload copy | 0 |
| recovery receipt | 1 |
| cold catalog projection | 17.013초 |
| exact lookup p99 | 7.191ms |
| object evidence detail p99 | 19.857ms |
| 3-hop graph traversal p99 | 0.027ms |
| snapshot replay | 3.946초 |
| snapshot replay SLO | PASS |
| pinned revision validation | PASS |
| source freshness | CURRENT |
| U3 integrated gate | PASS |

손상된 정본은 `eddmpython/dartlab-data/dart/docs/024950.parquet` 4,777,778 bytes다. 파일은 시작 magic `PAR1`은 있지만 terminal footer magic이 없으며 원본 descriptor는 계속 `PARSE_ERROR/INVALID_PARQUET_FOOTER`로 남는다. target Git object OID는 `bf34d862b95469a76ff807717885dd08abdafd76`, LFS payload SHA-256은 `ef01e197ac634261e711ed8f8a62feb5b5d8556e605937534471f513ce3e77f6`다.

복구 입력은 `eddmpython/dartlab-dart-original@46c49eb22615b22b2947a5afee01257a554411a5`의 `docs/024950.tar`다. Git object OID `b154fed12616ce56cd423e8593e6006a5b7489b4`, payload SHA-256 `16d26ad0c4160a30a0afa203c40a29b8e7f0c59d4db3625bf25daba5a8c81aa2`를 모두 검증한다. 변환은 git commit `3cf27ba98a20511e2c8803c0061e6509d06a9f89`의 `zipCollector.py`, `zipDocsXml.py`, `xmlAdapter.py` byte와 현재 recovery recipe byte를 digest로 결박한다.

실제 recovery artifact는 44개 receipt, 751행, 44 row group, nonempty `section_content_mixed` 585행이다. CAS ref는 `cas:sha256:d13124eca1481c52d8a09aa485eafa1cb38b1d6a893162903873fcacddf71734`, transform source digest는 `8d63d89b81180b4dbaa36c03cc2c4c09642336e44fb0482bcc5d9998f79fb6c3`, recovery ID는 `du:v1:recovery:89970828c4101172ed862a723a80cbc3e17eaf6396bcf1ac86a696f30fe8fd9a`다. artifact나 receipt는 repo에 bake하지 않고 기본 local control-plane `%LOCALAPPDATA%/DartLab/universe/control/recovery-v1`에 둔다. sibling arrow나 과거 parquet로 대체하지 않았으며 외부 Hugging Face 파일도 수정하지 않았다.

최종 catalog snapshot ID는 `du:v1:catalog-snapshot:6536c8cd72062c2cbc5f898ce733a3fb118d441cb8beb7b6ab4ecc836aa9a0cc`, recovery set digest는 `6427735a73053110b7f1bb4fd77d4e29a653ac650a6901c3fbb769073f1811da`다.

정본 명령:

```powershell
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u3Recovery
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u3C2 --strict
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u3Gate --strict
```

## 2026-07-22 U4 live 인수 기록

아래 값은 네 HF 저장소의 현재 고정 revision, 현재 로컬 블로그, 현재 content index를 하나의 catalog snapshot으로 결박한 관측값이다. 상류 HEAD가 바뀌면 C2와 U3를 다시 통과하기 전까지 U4가 닫히도록 한다.

| 항목 | 관측값 |
|---|---:|
| U3 upstream | PASS |
| blog post | 279 |
| blog AST block | 55,984 |
| blog image | 1,858 |
| external video | 14 |
| stale blog resource | 0 |
| content index artifact | 12 |
| fixture golden query | PASS |
| live golden query | PASS |
| live recall@20 | 100% |
| exact recall@1 | 100% |
| G4E validation | 100% |
| private leakage | 0 |
| hybrid retrieval p95 | 710.247ms |
| DART source universe | 2,727 |
| DART returned company | 2,685 |
| DART row coverage | 98.460% |
| DART numeric period value | 10,960 |
| EDGAR source universe | 6,007 |
| EDGAR returned company | 4,529 |
| EDGAR row coverage | 75.395% |
| EDGAR numeric period value | 44,710 |
| capability canary | PASS |
| U4 integrated gate | PASS |

DART canary는 4개 입력 340,478,422 bytes를, EDGAR canary는 9,998개 입력 523,944,157 bytes를 실행 경계에 결박했다. 두 시장 모두 Arrow magic, execution ref, durable receipt replay, G4E 검증을 통과했다. U4 catalog snapshot ID는 `du:v1:catalog-snapshot:c093714d26a4a891d0121619b800315ee147fb833c9e6e5071aa43542491701e`다.

정본 명령:

```powershell
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u4Gate --strict
```

## 2026-07-22 U5와 U6 live 인수 기록

U5와 U6는 한 프로세스에서 같은 in-memory projection을 공유해 검증했다. 작업공간 source가 동시에 전진해도 두 gate 사이의 snapshot이 갈라지지 않는다.

| 항목 | 관측값 |
|---|---:|
| catalog object | 212,394 |
| typed relation | 292,315 |
| community | 1,813 |
| scene tile | 1,818 |
| full projection | 22.034초 |
| projection replay | 21.684초 |
| 1% incremental | 1.914초 |
| coordinate determinism | 100% |
| meaning preservation | 100% |
| peak RSS | 1,809,506,304 bytes |
| max source tile | 1,085,085 bytes |
| encoded GPU payload | 95,232,159 bytes |
| full GPU tile encode | 3.984초 |
| initial GUI payload | 1,265,150 bytes |
| max GPU bundle | 426,894 bytes |
| tile, source, record, metadata, child closure coverage | 100% |
| label coverage | 100% |
| raw locator label | 0 |
| external GUI asset | 0 |
| public surface reference | 0 |
| public route와 button | 0 |
| persistent projection과 GPU artifact | 0 |
| G5A와 U5B | PASS |
| G6 | PASS |

catalog snapshot ID는 `du:v1:catalog-snapshot:f375e0e1130b87ca05316e50c426a21784c7100f2986c1300244a8bcb844619c`, projection state ID는 `du:v1:projection-state:67930ff500e76216b1d420346e53a22a5331b37e139cc46ef344b5f571b48d68`다. U5 report digest는 `a8927941f7f08ebbef66c47e29da704d96cce1a9d70a0d327b21bb513de035eb`, U6 report digest는 `cd3873e91c5e5be9c9448ce2ba88290da35dd77ab051c610500e9861a1d5fe71`다.

## 2026-07-23 직접 화면 route 승인

운영자 승인에 따라 `/universe` 고정 화면 route만 연결했다. 홈, 메뉴, 카드, sitemap에는 진입 링크를 만들지 않는다. 화면은 GPU bundle을 저장하거나 공개 저장소에 복사하지 않고, U6 loopback runtime이 세션마다 만든 일회성 tile을 fragment token과 고정 Origin CORS로 읽는다.

로컬 landing route로 직접 확인:

```powershell
# terminal 1
npm run dev -w landing

# terminal 2
uv run python -X utf8 -m tests._attempts.dartlabUniverse.u6Harness --live --route-url http://127.0.0.1:5173/universe --open
```

배포된 route로 직접 확인할 때는 두 번째 명령의 `--route-url`만 `https://eddmpython.github.io/dartlab/universe`로 바꾼다. 데이터는 계속 loopback에서만 제공되고 session token은 URL fragment 안에만 존재한다.

## 다음 gate

질문을 은하계에 던지는 기능은 U4 근거 팩을 U6 선택 scope에 결박하는 별도 U7 RAG gate로 설계한다. 현재 U6의 데이터와 렌더링 정본은 변경하지 않으며, 공개 진입 버튼은 운영자의 별도 승인 전까지 금지한다.
