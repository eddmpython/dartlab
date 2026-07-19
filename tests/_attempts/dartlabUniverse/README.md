# DartLab Universe U0~U2

상태: U0 full census, U1 identity와 provenance, U2 capability execution kernel gate 구현. 3D, UI, route, 공개 버튼, RAG, 영속 index는 아직 없다.

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

## 정본 명령

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/census.py --all --strict --format json
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

## 다음 gate

다음 단계는 U3 전체 catalog와 evidence graph다. 기존 runtime 승격, 독립 3D harness, UI 연결, 공개 route는 각각 후속 gate와 운영자 확인 전까지 금지한다.
