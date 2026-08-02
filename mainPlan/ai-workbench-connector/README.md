# DartLab AI Workbench Connector PRD Index

> 2026-08-02 경계 포인터: 본 계획은 remote public evidence connector를 소유한다. installed local agent의 discovery, auth, session, MCP bootstrap은 [agent-runtime-engine](../agent-runtime-engine/)이 소유한다. canonical evidence와 tool identity는 `src/dartlab` 정본을 함께 소비하고 별도 schema를 만들지 않는다.

상태: 비전 + 구현 착수 PRD v0.2 (2026-06-17, 제품 전략 · Cloudflare/MCP 아키텍처 · 보안/프라이버시 · AI 생태계 상호운용성 4 렌즈 토론 후 작성, 구현 계약 보강)
범위: DartLab 을 특정 챗봇에 종속된 기능이 아니라, 외부 AI 들이 공시 · 재무 · 워치리스트 · viewer/terminal 상태를 안전하게 조회하는 **AI-native evidence workbench layer** 로 만든다. ChatGPT 는 1차 배포 채널이지만 제품 코어가 아니다.

구현 착수 기준은 [08-implementation-plan.md](08-implementation-plan.md) 가 우선한다. 비전 문서와 구현 문서가 충돌하면 `08` 의 tool 계약, data source map, phase gate 를 따른다.

---

## 한 줄 결정

**DartLab AI Workbench Connector 는 모델을 제공하지 않는다. DartLab 은 검증 가능한 공시·재무·워크벤치 근거와 deep link 를 제공하고, 사용자의 AI 가 그 근거를 해석한다.**

```text
ChatGPT / Claude / Gemini / 임의 에이전트
  -> DartLab Connector adapter
    -> DartLab Canonical Tool Contract
      -> Cloudflare Worker Gateway
        -> Public Evidence Plane / User Context Plane / Link-State Plane
          -> HF parquet · 기존 hfProxy · D1/KV/R2 · viewer/terminal deep link
```

이 PRD 의 핵심은 "DartLab 챗봇"이 아니다. 핵심은 **AI 가 믿고 읽는 DartLab 근거 서버**다. 사용자는 이미 결제한 AI 에 질문하고, DartLab 은 답변 생성 비용을 지는 대신 정확한 데이터 조각, 출처, 화면 상태, viewer/terminal 링크를 반환한다.

---

## 핵심 결정 요약

- **제품 정체성 = evidence workbench connector.** 종목 추천 챗봇, 뉴스 요약 챗봇, 투자 조언 AI 가 아니다. DartLab 의 차별점은 공시 원문 근거, 재무 패널, 워치리스트 델타, viewer anchor, terminal state deep link 다.
- **MCP-first, OpenAPI-compatible.** 내부 표준은 `DartLab Canonical Tool Contract`, 1차 노출은 remote MCP `/mcp`, 동시 노출은 REST/OpenAPI `/openapi.json` + `/api/v1/tools/*`. ChatGPT/Claude/Gemini/LangChain/LlamaIndex/기타 에이전트는 adapter 다.
- **Cloudflare Workers 기존 라인 재사용.** 새 서버 후보 탐색이 아니라 현재 `infra/workers/{hfProxy,questionCollector,siteSignals}` 패턴 위에 `infra/workers/dartlabConnector` 를 추가한다. 초기에는 단일 Worker + 내부 모듈 분리, 규모가 커지면 plane 별 Worker 분리.
- **Public Evidence Plane 과 User Context Plane 완전 분리.** 공개 공시/재무/회사 검색은 익명·캐시 가능. 워치리스트·최근 방문·개인 terminal state 는 OAuth scope 필수, 사용자별 ACL, no-store 기본.
- **응답은 문장이 아니라 Evidence Pack.** 모든 tool response 는 `requestId`, `asOf`, `data`, `evidence[]`, `freshness`, `links`, `limitations` envelope 를 갖는다. AI 는 이 evidence pack 을 해석할 뿐, DartLab 은 근거 추적을 맡는다.
- **외부 AI 에 범용 실행 도구 금지.** public connector 에 `RunPython`, 임의 SQL, 임의 파일 읽기 같은 범용 도구를 열지 않는다. 내부 DartLab 엔진을 사용하더라도 외부에는 read-only, schema-validated, 목적별 tool 만 노출한다.
- **Deep link 가 제품 차별점.** AI 답변에서 끝나면 흔한 요약봇이다. 답변 → viewer 근거 → terminal 분석으로 돌아와야 DartLab 이 워크벤치가 된다.
- **투자 조언 금지.** 매수/매도/보유, 목표주가 단정, 수익률 보장, 개인 투자성향 기반 추천은 범위 밖. 허용 범위는 공시 변화, 재무 수치 근거, 동종 비교 데이터, 리스크 항목, viewer 근거 링크다.

---

## 문서 지도

1. [00-product-vision.md](00-product-vision.md): 제품 정의, 사용자, 차별화, 성공/실패 기준, 왜 챗봇이 아닌 connector 인가.
2. [01-ecosystem-interop.md](01-ecosystem-interop.md): MCP-first/OpenAPI-compatible 근거, ChatGPT/Claude/Gemini/agent framework 별 adapter 원칙.
3. [02-neutral-tool-contract.md](02-neutral-tool-contract.md): Canonical Tool Contract, Evidence Pack envelope, resources/prompts, tool 목록과 금지 tool.
4. [03-cloudflare-worker-architecture.md](03-cloudflare-worker-architecture.md): `infra/workers/dartlabConnector` 배치, endpoint, data plane, 기존 Worker 재사용, deployment 원칙.
5. [04-state-and-deeplink.md](04-state-and-deeplink.md): public/private state, viewer/terminal link, stateId 스키마, TTL/권한/재현성.
6. [05-auth-privacy-security.md](05-auth-privacy-security.md): OAuth scope, secret 관리, prompt injection, rate limit, 투자 조언 리스크, logging.
7. [06-evaluation-phasing-kill-list.md](06-evaluation-phasing-kill-list.md): 수용 기준, eval, Phase, KILL/DEFER, 출시 차단 게이트.
8. [07-progress-ledger.md](07-progress-ledger.md): 토론 수렴 기록, 결정 원장, NEXT.
9. [08-implementation-plan.md](08-implementation-plan.md): tool 별 AC, data source map, endpoint/schema, OAuth gate, eval fixture, rollout.

---

## 설계 원칙

1. **AI 를 호스팅하지 않는다.** 사용자의 AI 가 답변한다. DartLab 은 데이터·근거·링크를 제공한다.
2. **ChatGPT 전용으로 닫지 않는다.** ChatGPT App 은 첫 배포 채널일 수 있으나, core contract 는 MCP + OpenAPI-compatible 이어야 한다.
3. **공개와 개인을 섞지 않는다.** 공개 tool 은 절대 사용자 워치리스트나 개인 state 를 읽지 않는다.
4. **원문 전체 투척 금지.** 질문에 필요한 근거 조각만 반환하고, 모든 외부 본문은 untrusted content 로 표시한다.
5. **viewer/terminal 로 돌아오게 한다.** DartLab 의 독립 가치는 AI 답변이 아니라 검증 가능한 근거 화면이다.
6. **추천하지 않는다.** evidenceOnly, notInvestmentAdvice, asOfDate, dataLimitations 를 tool response 의 1급 필드로 둔다.
7. **무료/저비용은 Cloudflare 로 시작한다.** 단 "영구 무료 운영"을 제품 약속으로 쓰지 않는다. 초기 검증은 Workers/D1/KV/R2 free tier 에 맞추되 quota·abuse·OAuth 운영 비용을 인정한다.
