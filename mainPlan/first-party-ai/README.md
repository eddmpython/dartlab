# DartLab First-Party AI: 자체 작성·분석 엔진 SSOT PRD Index

> 2026-08-02 재정합 포인터: local `advanced` provider와 direct model credential 경계는 [agent-runtime-engine](../agent-runtime-engine/)이 대체한다. 본 계획의 public deterministic/on-device compose 후보는 유지하되 Cloudflare edge model 전제는 구현 착수 전에 다시 검증한다. 상세 경계의 정본은 [agent-runtime-engine/01-current-state-audit.md](../agent-runtime-engine/01-current-state-audit.md)다.

상태: 비전 + 구현 착수 PRD v0.2 (2026-06-22, 데이터 작업대 SSOT 위에 *DartLab 자신이* 글을 쓰고 분석하는 1급 AI 레인을 공개/로컬 공통배선으로 정착. 5분야 전문가 R1 평가 반영: 계약 census 실측·TierBackend 누수 해소·verifyGrounded fact-typed·budget=Durable Object·관측성 신설)
범위: 터미널·리포트·캐러셀(신규)·블로그·랜딩의 "AI 가 대신 써줄 수 있는 문구"와 "바로 묻는 분석"을, **하나의 AI 포트(`runtime.ai`)** 로 일원화한다. 퍼블릭에서는 Cloudflare Workers AI 무료티어(우리 워커·API 키 0)를 1차 경로로 쓰고, WebGPU 온디바이스로 폴백하며, 결정론 Q&A 가 바닥을 받친다. 로컬은 기존 ask 엔진(`advanced`)을 그대로 재사용한다.

구현 착수 기준은 [06-scope-phasing-guardrails.md](06-scope-phasing-guardrails.md) 의 phase gate 가 우선한다. 비전과 구현이 충돌하면 06 의 phase·가드·롤백을 따른다.

---

## 한 줄 결정

**DartLab First-Party AI 는 새 챗봇 UI 가 아니라, `runtime.ai` 단일 포트 뒤에 결정론 → 온디바이스 → 엣지 → 로컬 4 티어를 사다리로 세운 *작성·분석 generation 코어* 다. 모든 surface 는 `ai.ask`(분석) / `ai.compose`(작성) 두 동사만 부르고, 어느 티어가 답했는지·무엇에 근거했는지는 포트가 책임진다.**

```text
surface (terminal · report · carousel · blog · landing)
  -> runtime.ai.ask / runtime.ai.compose          (동사 2개)
    -> Grounding SSOT (결정론 분석능력: 숫자·근거·asOf 생성)
    -> Tier ladder
         deterministic   결정론 Q&A (LLM 0, 환각 0, 항상)
         onDevice        WebGPU @mlc-ai/web-llm 1~3B (서버 0·secret 0)
         edge            Cloudflare Workers AI 8B (우리 워커·키 0·무료티어)  ← 신설
         advanced        로컬 ask 엔진 (full tool-calling, 내 데이터)
```

---

## 무엇을 만드나 (Section A)

1. **Grounding SSOT (`runtime/src/ai/analysis/`)**: viewer 에 갇혀 있던 결정론 분석능력(`classifyIntent`·`financeSignals`·`ratioSeries`·`won`/`fmtAmt1` 포맷터·`CellFacet`)을 surface 비종속 순수 모듈로 끌어올린다. 입력 = runtime 데이터 포트, 출력 = `GroundingPack{facts(합성키+분모정의+renderedForms), derivedFacts, evidence, asOf, dataVersion, limitations}`. **모든 티어가 이 하나를 근거로 쓰고, `verifyGrounded` 가 fact-typed 로 숫자 환각을 막는다.**
2. **공개 AiPort 배선 (단계-7 "ask 추출")**: 현재 `notWiredYet('ai')` 인 public adapter 의 `AiPort` 를 실배선한다. 결정론 기본 + WebGPU 승급은 기존 설계대로, **여기에 `edge` 티어를 추가**한다.
3. **Edge 워커 (`infra/workers/aiEdge`)**: Workers AI 바인딩(`[ai] binding="AI"`, 키 불요)으로 `/ai/compose`·`/ai/ask`(SSE)·`/ai/health`. 예산 방어 4겹 = **Durable Object 원자 카운터**(reserve/settle) + **CF 429 ground-truth 차단** + CF native Rate Limiting·Turnstile + **Workers Paid spend cap**. 데이터 프록시와 비용·남용 격리를 위해 별도 워커.
4. **자동 감지·자동 배선**: 별도 `deploy-ai-edge.yml`(deploy-landing 오염 금지)이 `CLOUDFLARE_API_TOKEN` 있을 때만 워커 배포(자동설치, idempotent). 런타임은 `originConfigured('aiEdge')` + `/ai/health` 로 "이미 켜져있으면 그대로", 없으면 WebGPU 폴백.
5. **관측성**: 워커가 강등율·stray 거부율·5xx·neuron 소비를 CF Analytics Engine/siteSignals 로 집계 → `monitorPipeline.py` 동형 게이트로 운영자 알림. budget 만성소진·환각 급증을 맹목으로 안 둠.
6. **compose 레인(작성)**: `ai.compose(template, scope, context)` 로 리포트 섹션 해설·캐러셀 카피·블로그 보조 문구를 생성. **빌드타임 baked(정적 surface 기본·문장 캐시·asOf 무효화) / 런타임 live(인터랙티브) 2 본성**을 같은 포트로. 신경험 간판 = 터미널 selection-grounded ask.

## 무엇을 잠그나 (Section B)

7. **한계 표기 원칙 코드화**: 숫자는 Grounding SSOT 만 생성하고 모델은 *서술만*(생성된 숫자 사후 검증), 외부 본문 untrusted-wrap, "어느 티어가 답했는지" provenance 표면화, "영구 무료" 약속 금지. `operation.ui` AI 레인 절 + 기계 가드.
8. **경계 박제**: 이 PRD 는 `ai-workbench-connector`(외부 AI 에게 근거를 *내주는* 아웃바운드)와 **반대 방향**(DartLab 이 *직접* 쓰고 분석하는 인바운드). 두 워커·두 정체성을 섞지 않는다([05](05-killlist-and-non-goals.md)).

---

## 문서 지도

1. [00-product-vision.md](00-product-vision.md): 무엇을·누구를 위해·왜 "또 다른 챗봇"이 아니라 surface 전반의 작성·분석 레인인가. 커넥터와의 경계. 성공/실패 기준.
2. [01-tier-architecture.md](01-tier-architecture.md): 4 티어 사다리, `AiPort` 확장(`edge` 신설·`compose` 동사), 공개 배선, 런타임 티어 선택·우아한 강등, capabilities 계약.
3. [02-edge-ai-cloudflare.md](02-edge-ai-cloudflare.md): Workers AI 무료티어 통합, `aiEdge` 워커·바인딩·라우트, 자동 프로비저닝, neuron 예산·남용 방어, 프라이버시, 비용 명시.
4. [03-analysis-capability-ssot.md](03-analysis-capability-ssot.md): Grounding SSOT 추출·계약, 티어 공통 근거 재사용, 숫자 환각 가드, untrusted-wrap.
5. [04-surface-wiring.md](04-surface-wiring.md): viewer·terminal·report·carousel·blog 별 ask/compose 소비, baked vs live, compose 템플릿 계약.
6. [05-killlist-and-non-goals.md](05-killlist-and-non-goals.md): 안 하는 것(투자조언·surface env 분기·온디바이스 장문·영구무료 claim·graph 회귀·커넥터 혼입).
7. [06-scope-phasing-guardrails.md](06-scope-phasing-guardrails.md): phase·가드레일·롤백·테스트 매트릭스·개발자+PM 이중 평가.
8. [07-specialist-review.md](07-specialist-review.md): 5 분야(아키텍처·데이터·유연성·혁신성·운영성) 전문가 평가 라운드·점수·수렴(≥90 게이트).
9. [08-progress-ledger.md](08-progress-ledger.md): 결정 원장·세션 간 재개·NEXT.

---

## 한계 표기 원칙 (전 문서 관통)

1. **새 발명 최소화.** Grounding 은 viewer 의 결정론 분석을 *끌어올린* 것, AiPort 는 *이미 정의된* 계약을 *배선*하는 것. 신설은 `edge` 티어와 `compose` 동사뿐.
2. **숫자는 결정론, 서술만 모델.** 모든 수치는 Grounding SSOT 가 만들고 LLM 은 문장만 짠다. 출력 숫자는 facts 대조 사후검증으로 환각을 막는다.
3. **티어는 명시적으로 표면화.** 어느 티어가 답했는지(`tierUsed`)와 근거(`evidence[]`)를 답변과 함께 보인다. 강등(edge→onDevice→deterministic)은 조용히 하지 않는다.
4. **퍼블릭 무료는 한계가 있다.** Cloudflare 무료티어 = 10,000 neurons/day. 예산 서킷브레이커로 보호하고 "무제한 무료 AI" 로 포지셔닝하지 않는다.
5. **프라이버시 분기 명시.** baked·onDevice = 디바이스 밖으로 아무것도 안 나감. edge = 프롬프트+근거가 우리 워커로 감(PII 0·근거만). 사용자에게 구분해 알린다.
6. **투자 조언 금지.** 매수/매도/목표주가/수익률 보장 = 범위 밖. 공시 변화·재무 근거·동종 비교·리스크 서술까지.
7. **커넥터가 아니다.** 외부 AI 노출(MCP/OpenAPI)은 `ai-workbench-connector` 의 일. 본 PRD 는 DartLab 1인칭 작성·분석.
