# 01. 티어 아키텍처 — 4 티어 사다리와 AiPort 확장

상태: 구현 계약 PRD v0.2 (R1 전문가평가 반영: 계약 census 실측·TierBackend 누수 해소·AiAskInput 비파괴 마이그레이션·멀티턴 슬롯)
범위: `AiTier` 확장(`edge` 신설), `AiPort`의 `compose` 동사 추가(비파괴), 공개 어댑터 배선, 런타임 티어 선택·우아한 강등, capabilities 계약. 현재 UI runtime 계약을 기준으로 개정한다.

> ⚠ 본 문서의 모든 계약 인용은 `ui/packages/contracts/src/ai.ts` **실측**(2026-06)이다. R1 평가가 적발한 "계승 위장"(실은 breaking)을 제거하고, 실제 필드/메서드와 diff 를 명시한다.

---

## 0. 실측 계약 census (착수 전 ground-truth)

```ts
// ai.ts:5  (실측)
export type AiTier = 'advanced' | 'onDevice' | 'deterministic' | 'none';
// ai.ts:8  AiCapabilities { tier, streaming, toolCalling, localWorkspace, deterministicAnswers, providerLabel?, modelLabel?, upgradeHint? }
// ai.ts:150 AiAskInput { prompt; mode: AiModeId; code?: string; evidence?: EvidenceSelection[] }
// ai.ts:157 AiAskResult { text: string; refs: EvidenceRef[] }
// ai.ts:183 AiPort = { capabilities, ask, streamAsk, runTool, explainEvidence, listModes, setMode, getMode }  // 8 메서드
// registry.ts:22 OriginId = 'hf'|'hfRange'|'localApi'|'newsWorker'|'naverWorker'|'duckdbHf'|'govDev'  // aiEdge 없음
// createPublicRuntime.ts: get ai() { return notWiredYet('ai') }  // lazy getter, 미배선
```

본 PRD 가 *건드리는* 표면과 그 성격:

| 심볼 | 변경 | 파괴적? |
|---|---|---|
| `AiTier` | `+ 'edge'` | 비파괴(유니온 확장) |
| `AiCapabilities` | `+ available?`, `+ compose?`, `+ meteredBudget?` (기존 8필드 전부 유지) | 비파괴(옵셔널 추가) |
| `AiAskInput` | `+ scope?`, `+ context?`, `+ history?` (기존 `code?`·`evidence?` **유지**) | **비파괴**(§7) |
| `AiAskResult` | `+ tierUsed?`, `+ grounded?`, `+ limitations?` (기존 `text`·`refs` 유지) | 비파괴 |
| `AiPort` | `+ compose`, `+ streamCompose` (기존 8메서드 전부 구현 의무) | 표면 추가(§3·§8) |
| `OriginId` | `+ 'aiEdge'` + ORIGINS 항목 신설 | 비파괴(신설) |
| `get ai()` | getter 제거 → eager `publicAiPort(core)` | 내부(§8) |

---

## 1. 기준선과 §4 개정점

`02-runtime-ai-services §4` 공개 어댑터 원칙 중 **운영자 승인으로 개정하는 한 항**:

> 기존: "public adapter — server-side agent gateway 없음, secret 0, tier deterministic 기본 + onDevice 승급."
> 개정: "public adapter — tier 사다리 `deterministic → onDevice → edge`. `edge` = 우리 Cloudflare 워커의 stateless 단발 prompt→text 게이트. **클라이언트 secret 0 불변**(사용자 키·토큰 0). 워커는 budget 카운터(Durable Object)라는 *서버측 상태* 를 갖지만 클라이언트엔 안 보인다. 무거운 server-side agent gateway(5패스·tool-calling)는 여전히 금지 — tool-calling 은 `advanced` 전용."

이 개정은 착수 시 `02-runtime-ai-services §4` + 07 원장에 동반 entry. "이미 출시된 공개 AskDrawer(Tier0+WebGPU) 회귀 금지" 는 그대로 — edge 를 *얹는* 것이지 빼는 게 아니다.

---

## 2. AiTier 확장 — 그리고 advanced 는 사다리 밖

```ts
export type AiTier = 'advanced' | 'edge' | 'onDevice' | 'deterministic' | 'none';
```

| 티어 | 모델 | streaming | toolCalling | 다턴 | 사다리 멤버? | 공개 |
|---|---|---|---|---|---|---|
| deterministic | —(계산) | n/a | no | no | ✅(바닥) | 항상 |
| onDevice | web-llm 1~3B | yes | no | no(v0) | ✅ | WebGPU 기기 |
| edge | Workers AI 8B | yes | no | **no(v0 단발)** | ✅ | 워커 배포 시 |
| advanced | 로컬 provider | yes | **yes** | yes | ❌(§5) | — |

> **R1 BLOCKER 해소 — advanced 는 단발 텍스트 사다리의 멤버가 아니다.** advanced(로컬 ask 엔진)는 tool-calling·다턴·AG-UI 15종 이벤트(`TOOL_CALL_START`·`VIEW_SPEC`…)를 발행한다. 이를 단발 텍스트 백엔드 추상에 욱여넣지 않는다. advanced 는 사다리 *위* 에서 *먼저* 선택되어 기존 `streamAsk`(Ask 엔진) 경로로 직결되고, edge/onDevice/deterministic 만 단발 텍스트 사다리(§5)를 이룬다.
>
> **R1 일관성 정정 — edge 는 v0 에서 단발**(다턴 아님). 02 §3 엔드포인트·05 K3 과 일치. 다턴 edge 는 DEFER(05 §2).

---

## 3. compose 동사 + 열린 템플릿

`ask`(질문→답)와 `compose`(템플릿+톤→카피)는 입력 형태가 달라 typed sibling 동사로 둔다. **단 자주 늘어나는 것(템플릿)은 계약을 안 건드리게 연다.**

```ts
export interface AiPort {
  // 기존 8 메서드 — public adapter 가 전부 구현(§8 conformance) —
  compose(input: AiComposeInput): Promise<AiComposeResult>;
  streamCompose(input: AiComposeInput): AsyncIterable<AiStreamEvent>;  // ⭐ R2 유연성 해소: streamAsk 와 동일 청크 모델
}

export type ComposeTemplateId = string;
// ⭐ R2 유연성 해소: 브랜디드(코드 선례 0) 아님. 열린 `string` + analysis/compose/templates.ts 레지스트리 키 존재로 런타임 검증.
// 철학은 Storage 와 같다(키는 열고, 전역 union 은 닫음 — 02-runtime §8). 단 메커니즘은 다르다:
// Storage=템플릿 리터럴 타입, 여기=런타임 레지스트리 검증. "철학적 동형"이지 타입 동형 아님. 새 카피자리 = templates.ts 한 파일, contracts 불변.

export interface AiComposeInput {
  template: ComposeTemplateId;
  scope: 'report' | 'carousel' | 'blog' | 'landing' | 'terminal';
  evidence?: EvidenceSelection[];   // ⭐ GroundingRef 폐기 — 실존 EvidenceSelection 재사용(ai.ts)
  context?: { code?: string; period?: string; sectionKey?: string };
  tone?: 'neutral' | 'reader-first';
  maxTokens?: number;               // 온디바이스 4096 캡·neuron 예산 보호
  determinismFloor?: boolean;       // LLM 불가 시 결정론 템플릿 문장으로라도
}

export interface AiComposeResult {
  text: string;
  refs: EvidenceRef[];
  tierUsed: AiTier;                 // 답한 티어 명시(§6)
  grounded: boolean;                // 숫자 사후검증(03 §5)
  limitations?: string;
}
```

**동사 수를 늘리지 않는 이유 명시(R1 유연성 응답)**: 내부 `generate()` 코어는 verb 무관 단일(§5)이지만, *포트 표면* 은 `ask`/`compose` 두 typed 동사를 유지한다 — 입력 타입이 verb 별로 다르기 때문(ask=질문, compose=템플릿). 자주 늘어나는 축은 verb 가 아니라 *템플릿* 이고, 그건 `ComposeTemplateId` 를 열어 흡수한다. 3번째 verb 는 드물고 그때만 계약 개정. (Storage 가 "키는 열고 전역 union 은 닫은" 것과 같은 균형.)

`AiAskResult` 도 `tierUsed?`·`grounded?`·`limitations?` 옵셔널 추가(비파괴).

---

## 4. capabilities 계약 (실측 기반 확장)

```ts
export interface AiCapabilities {
  // 기존 8필드 전부 유지 (실측 ai.ts:8)
  tier: AiTier; streaming: boolean; toolCalling: boolean; localWorkspace: boolean;
  deterministicAnswers: boolean; providerLabel?: string; modelLabel?: string; upgradeHint?: string;
  // 본 PRD 추가(옵셔널, 비파괴)
  compose?: boolean;                     // compose 동사 가용 (deterministic 이상 true)
  meteredBudget?: AiMeteredBudget;       // ⭐ edge 한정 아님 — 어느 metered 티어든 (R1 유연성 MINOR)
}
// ⭐ R2 유연성 해소: `available?: AiTier[]` 제거(YAGNI). 강등 가시화는 `tier`(최고 가용) vs 응답의 `tierUsed`
//   두 스칼라 차이로 충분(배지 "edge 한도 → 온디바이스로 답함"). 배열이 실수요가 생기면 그때 추가.

export interface AiMeteredBudget {
  tier: AiTier;                          // 어느 티어의 예산인가
  remaining: 'high' | 'low' | 'exhausted';  // ⭐ 정확한 수 숨김 (R1 운영 B6: 정찰 차단)
  resetAt: string;
}
```

강등 가시화는 `tier`(최고 가용) vs 응답의 `tierUsed`(실제 답한 티어) 차이로 표현 — 별도 배열 불요. surface 는 이 둘을 *표시* 에만 쓰고 *분기 코드* 로 안 쓴다(02 §1 계승; 06 §2 TS 가드가 surface 의 `tier`/`tierUsed` 분기 사용을 차단). `meteredBudget.remaining` 은 버킷으로만 노출해 공격자 정찰을 막는다(02 §6·§9).

---

## 5. generation 코어 — 일원화 + 누수 없는 추상

```text
ai.ask(input)  ─┐ buildPrompt
                ├─> Grounding SSOT(03) → GroundingPack{facts, evidence, asOf, limitations}
ai.compose(in) ─┘        │
        ┌────────────────┴─ advanced 가용 & 요청이 tool-calling/다턴? ─ yes ─> 기존 streamAsk(Ask 엔진) [사다리 밖]
        │                                                              no
        v
   generate(groundedPrompt, ladder)              ladder = [edge, onDevice, deterministic] (단발 텍스트만)
        try ladder[i].isAvailable() → generate → 런타임에러(429/device-lost/timeout) → i+1
        deterministic 은 항상 성공(바닥)
        v
   postCheck: verifyGrounded(text, facts)        (03 §5)
        v
   { text, refs, tierUsed, grounded, limitations }
```

```ts
// ⭐ R1 BLOCKER 해소: 반환을 청크 union 으로 일반화 (string 으로 안 좁힘 → 미래 tool-calling API 수용)
export type GenChunk =
  | { type: 'text'; delta: string }
  | { type: 'tool'; name: string; args: unknown }    // 미래 tool-calling 텍스트 API 대비(현재 미발행)
  | { type: 'done'; tierUsed: AiTier };

export interface TierBackend {
  readonly tier: AiTier;                 // 'edge' | 'onDevice' | 'deterministic' (단발 텍스트만)
  readonly rank: number;                 // ⭐ 사다리 순서를 데이터로 (R1 유연성: union 순서 의존 제거)
  isAvailable(): Promise<boolean>;       // edge=health+budget, onDevice=webgpuUsable, det=true
  generate(prompt: GroundedPrompt, opts: GenOpts): AsyncIterable<GenChunk>;
}
```

- `ladder` 는 하드코딩 분기가 아니라 **`TierBackend[]` 레지스트리를 `rank` 내림차순 정렬** 한 것. 지역별 edge·2차 모델은 *배열 원소 추가* = 데이터 변경(R1 유연성 BLOCKER 해소).
- **"새 단발 API = TierBackend 1파일"** 은 참(edge 급). **tool-calling 좋은 API**(Claude/GPT function-calling)는 두 길: ① 단발 모드로만 쓰면 `GenChunk` text 백엔드 1파일, ② full agent 로 쓰면 `advanced` 경로(Ask 엔진)에 provider 추가 — 사다리 밖. R1 이 적발한 "1파일" 과장을 이렇게 정정한다.
- `advanced` 는 `TierBackend` 가 **아니다**(별도 경로). 이로써 "ask/compose 가 같은 generate 코어로 수렴" 은 *단발 티어* 한정 참, advanced 는 명시적으로 예외임을 표로 못박는다.
- **⭐ 청크 어댑팅 지점(R2 유연성 MAJOR 해소).** `GenChunk` 는 `generate.ts` *내부* 통화다. surface 는 `GenChunk` 를 모른다 — `generate.ts` **출구에서 `GenChunk{text}` → `AiStreamEvent`(TEXT_MESSAGE_CONTENT/RUN_FINISHED) 로 어댑팅** 한다. advanced 는 처음부터 `streamAsk`(AiStreamEvent) 직결. 따라서 `streamAsk`·`streamCompose` 둘 다 **surface 에 `AsyncIterable<AiStreamEvent>` 단일 청크 모델만 노출** → "surface 는 동사 2개만, 청크 1종만 안다"(00 §8). 미래 `GenChunk{tool}` 발행 시 verifyGrounded·어댑터 동반 확장(03 §5 한계 절).

---

## 6. 티어 선택·우아한 강등 (스트림 안전)

선택(공개): `capabilities().tier` = 레지스트리에서 `isAvailable()` 통과한 최고 `rank`.
```text
edge configured(VITE_DARTLAB_AI_PROXY) & health ok & budget≠exhausted → edge(rank 30)
else webgpuUsable()                                                    → onDevice(rank 20)
else                                                                    → deterministic(rank 10)
```

**스트림 강등의 안전 규칙(R1 아키텍처/운영 해소):**
1. **첫 토큰 전 티어 확정.** `isAvailable()` 를 스트림 시작 *전* 평가하고, 그 요청은 그 티어로 끝까지. 스트림 *도중* 조용한 티어 전환 금지(부분 텍스트 + 재시작 혼란 차단).
2. **스트림 중 백엔드 사망**(워커 die·device-lost)은 **부분 출력 폐기 + "끊김" 표시**, onDevice 재시작은 *명시적 사용자 액션* 으로(자동 이중답 금지). `tierUsed` 는 단일 값 유지.
3. **전체 타임아웃 예산**(예 8s) — `isAvailable` 프로브 누적이 폭주하지 않게. 초과 시 즉시 deterministic.
4. **강등은 조용하지 않다.** `tierUsed < capabilities().tier` 면 UI 가 사유 한 줄("무료 한도 — 온디바이스로 답함" / "이 기기 WebGPU 미지원 — 결정론 답"). [[feedback_terminal_hf_ssot_local_compute]] "stale 을 fresh 처럼 안 보임" 동형.

로컬 어댑터: provider 설정 시 advanced(기존 Ask 엔진), 미설정 시 공개 사다리(edge/onDevice/deterministic) 재사용 — 공통배선.

---

## 7. AiAskInput — 비파괴 마이그레이션 (R1 BLOCKER 해소)

실측 `AiAskInput = {prompt, mode, code?, evidence?: EvidenceSelection[]}`. 본 PRD 는 이를 **대체하지 않고 옵셔널로 보강**:

```ts
export interface AiAskInput {
  prompt: string;
  mode: AiModeId;
  code?: string;                       // 유지
  evidence?: EvidenceSelection[];      // 유지 — viewer 기존 호출부 무손상
  // 본 PRD 추가(전부 옵셔널)
  scope?: 'viewer' | 'terminal' | 'report';
  context?: { period?: string };       // code 는 위 필드 재사용, selection 은 evidence 재사용
  history?: ChatTurn[];                // ⭐ R2 아키텍처 해소: viewer 가 *이미* 멀티턴 → v0 실배선(슬롯 아님). ChatTurn 은 contracts 로 승격(§8)
}
```

- `scope` 를 **필수로 만들지 않는다** — 기존 호출부(viewer streamAsk)가 컴파일 안 깨짐. 미지정 시 어댑터가 `mode`/`code` 로 추론.
- `selection` 신규 필드를 안 만들고 **기존 `evidence: EvidenceSelection[]` 를 selection 근거로 그대로 사용** — `GroundingRef` 유령 타입 제거(R1 유연성/데이터 적발).
- **`history?` 는 v0 실배선(R2 아키텍처 MAJOR 해소).** viewer 는 실코드(`webllm.ts routeChat(history, evidence)`·`ChatTurn`·`buildChatMessages`·`AskDrawer.svelte`)로 *이미* 멀티턴을 서빙 중이다. 이관 시 `history?` 가 미사용이면 viewer 멀티턴이 *회귀* 한다(03 §8 "바이트 동일" 게이트 위반). 따라서 `history?` 는 슬롯이 아니라 **viewer 이관과 동시에 v0 배선**한다. `ChatTurn` 타입을 viewer-local 에서 `contracts/ai.ts` 로 승격(§8 영향파일).
- 사상: `streamAsk` + `history?`/`evidence`. history *보관* 은 surface 상태(Storage `ask.*` 키), 포트는 무상태 전달(턴 배열을 매 호출 실어 보냄). 06 Phase 1 게이트에 "멀티턴 턴 누적 동작 스냅샷" 추가.
- compose 는 단발 작성이라 `history` 없음(의도된 비대칭).

---

## 8. 영향 파일 (구현 시)

| 파일 | 변경 |
|---|---|
| `ui/packages/contracts/src/ai.ts` | `AiTier+'edge'`; `AiAskInput +scope?/context?/history?`(비파괴); `AiAskResult +tierUsed?/grounded?/limitations?`; `compose`/`streamCompose(→AiStreamEvent)`; `AiCapabilities +compose?/meteredBudget?`(available 없음); `GenChunk`(내부)·`ComposeTemplateId`(열린 string)·`AiComposeInput/Result`; **`ChatTurn` 승격**(viewer-local→contracts) |
| `ui/packages/runtime/src/ai/` (신규) | `generate.ts`·`backends/{edge,onDevice,deterministic}.ts`(TierBackend)·`analysis/`(03) |
| `…/adapters/public/createPublicRuntime.ts` | `get ai()` getter 제거 → eager `publicAiPort(core)`; **단 webgpu/health 프로브는 lazy(첫 호출)** — 부팅 경로 오염 금지(R1 아키텍처) |
| `…/adapters/local/sources/aiSource.ts` | 8 메서드 유지 + `compose`/`streamCompose` 구현; provider 무설정 시 공개 사다리 재사용 |
| `…/adapters/test/createFakeRuntime.ts` | `compose`/`streamCompose` fake 구현(conformance) |
| `…/data/origins/registry.ts` | `OriginId +'aiEdge'` + ORIGINS 항목 신설(throw 게이트 해제), `configured:()=>Boolean(AI_PROXY)` |
| `02-runtime-ai-services.md §4` | edge 티어 개정 entry |

**conformance(R1 BLOCKER 해소)**: `AiPort` 의 *전 10 메서드*(기존 8 + compose 2)를 public/local/test 가 구현하거나 02-runtime §3.6 "명시적 unavailable 구조화 반환"(throw 아님)으로 처리. `runTool`/`setMode` 등 비-생성 메서드의 public 거동을 §8 census 에 명시: public 은 `runTool`→unavailable, `listModes`→['chat'] 등 결정론 반환. 06 conformance test 가 10 메서드 전부 검사.
