# 01. Metric Authority and Privacy

## 1. 현재 기준선

2026-08-02 현재 권위 있는 `weeklyVerifiedAnalysisLoops` 값은 없다.

| 현재 자산 | 실제로 재는 것 | 북극성 사용 여부 |
|---|---|---|
| `infra/workers/siteSignals` | path별 pageView, dwell, scroll, CTA 등 익명 counter | 방향성 진단만 |
| `tests/audit/aiMetricsDigest.py` | local trace의 turn, first chunk, elapsed, tool 빈도 | runtime 성능 진단만 |
| `src/dartlab/server/agentMetrics.py` | chat-native와 workbench 분기 비율 | 회귀 진단만 |
| mainPlan progress ledger | 구현 진척 | 제품 결과가 아님 |
| pytest와 CI | 계약과 회귀 | release evidence, 사용자 사용량 아님 |

기존 숫자를 이름만 바꿔 북극성으로 승격하지 않는다.

## 2. 두 권위 평면

### Semantic authority

`src/dartlab/productOutcome/`가 한 분석 loop의 의미를 판정한다.

- state transition 유효성
- canonical subject 존재
- contract engine result 존재
- evidence와 artifact identity
- delivered, verified, retained 전이
- duplicate와 test traffic 제외

semantic authority는 로컬이다. 질문, evidence payload, 회사 코드, native session ID를 외부로 보내지 않는다.

### Count authority

Phase 0~2의 count authority는 로컬 outcome store와 release acceptance뿐이다.

- 운영자는 local scorecard로 전이 손실과 guardrail을 본다.
- CI는 deterministic acceptance가 정확히 한 completion을 만드는지 검증한다.
- 실제 CLI 계정이 필요한 claim은 operator evidence로만 인정한다.
- 전역 사용자 성장 수치는 표시하지 않는다.

원격 aggregate count는 별도 사용자 계정이나 검증 가능한 admission 계약이 생기기 전까지 DEFER다. 익명 endpoint에 random token을 보내는 것만으로는 누구나 분자를 부풀릴 수 있어 권위가 없다.

## 3. Local outcome store

저장 위치 제안은 `~/.dartlab/product-outcomes.sqlite3`다. provider transcript, AI memory, CLI history와 분리한다.

### `analysisOutcomes`

| 필드 | 의미 |
|---|---|
| `outcomeId` | random 128-bit ID, primary key |
| `schemaVersion` | migration version |
| `origin` | `user`, `test`, `operator` |
| `surface` | `localUi`, `cli`, `mcpHost`, `python` |
| `state` | started부터 retained까지 단조 전이 |
| `subjectKind` | company, filing, market, industry, macro, dataset |
| `subjectLocalRef` | local-only canonical ref |
| `startedAt`, `updatedAt` | UTC |
| `releaseId` | DartLab package/build identity |
| `capsuleId` | structured analysis capsule pointer |
| `failureCode` | 안정된 실패 코드, 성공 시 null |

### `analysisOutcomeEvidence`

- `outcomeId`
- `refId`
- `kind`
- `sourceType`
- `asOf`
- `resolvedAt`
- `artifactReceipt`

본문, prompt, answer, secret, provider transcript는 저장하지 않는다. evidence payload는 기존 artifact/evidence store가 소유하고 outcome store는 pointer와 receipt만 가진다.

모든 전이는 SQLite transaction 하나로 receipt와 같이 기록한다. process crash 후 partial state를 완료로 승격하지 않는다.

## 4. Scorecard

scorecard는 독립 KPI 나열이 아니라 인과 순서로 읽는다.

| 신호 | 계산 | 질문 |
|---|---|---|
| started | distinct user outcomes | 실제 분석 의도가 시작됐나 |
| scoped conversion | scoped / started | DartLab이 질문을 real subject에 붙였나 |
| grounded conversion | grounded / scoped | 정식 엔진이 근거를 만들었나 |
| delivered conversion | delivered / grounded | 근거가 사용자 결과로 도착했나 |
| verified conversion | verified / delivered | 사용자가 exact evidence를 확인했나 |
| retained conversion | retained / verified matured 28-day cohort | 결과가 다시 쓰였나 |
| first evidence | `timeToFirstEvidenceMs` 분포 | 첫 가치가 얼마나 빨랐나 |
| guardrails | trust, responsiveness, parity gates | 숫자를 의사결정에 써도 되나 |

최근 retained cohort는 28일이 완전히 지난 outcome만 분모로 쓴다. 열린 window를 실패로 세지 않는다.

판정은 다음 네 개다.

- `expand`: primary target과 모든 guardrail이 green.
- `improve`: target은 미달하지만 trust breach가 없음.
- `repair`: privacy, evidence, process, safety, responsiveness guardrail 중 하나가 실패.
- `revert`: 변경이 primary 전이를 악화시키고 즉시 안전한 복구가 가능.

데이터가 없으면 `noData`다. 0을 성공이나 실패로 해석하지 않는다.

## 5. 미래 원격 집계 조건

다음 조건을 모두 충족하는 별도 PRD가 승인되기 전에는 원격 북극성 집계를 만들지 않는다.

1. 명시적 opt-in과 삭제 표면.
2. 위조와 중복을 제한하는 admission authority.
3. raw question, subject, evidence, path, provider, model, token을 받지 않는 closed schema.
4. coarse day, random cycle digest, release ID만 유지.
5. retention과 key rotation, deletion, concentration guardrail.
6. siteSignals와 별도 binding과 별도 disclosure.
7. 익명 directional count를 authoritative numerator로 승격하지 않는 기계 가드.

현 단계에서 원격 수집을 만들지 않는 것은 기능 회피가 아니라 권위 없는 숫자로 제품을 운영하지 않기 위한 설계 결정이다.
