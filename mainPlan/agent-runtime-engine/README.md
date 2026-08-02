# Agent Runtime Engine

상태: 답변 품질 commit·FY 근거·timeout/cancel·재시작 복구를 포함한 local GUI verified journey 실증 완료, 주간 운영 관찰 중 (2026-08-02)

Primary goal ID: `completeVerifiedAnalysisLoop`

Supporting goal IDs: `startFromRealQuestion`, `reachFirstEvidence`, `verifyAnalysisResult`, `retainAnalysisOutcome`, `protectResearchTrust`, `keepAnalysisResponsive`, `keepCapabilityParity`

범위: DartLab 로컬 AI의 직접 OAuth, API key, 정적 model/provider gateway를 제거하고 사용자의 PC에 설치된 Codex, Claude Code, Cline과 향후 ACP 호환 CLI를 구조화된 agent runtime으로 사용한다. 금융 capability, Skill OS, evidence, artifact, product session contract는 DartLab `src`가 소유한다.

runtrol은 실행 의존성이 아니다. 별도 daemon, git submodule, shared package를 추가하지 않는다. runtrol에서 검증된 process supervision, runtime discovery, provider-owned session, opaque event 원칙만 DartLab 설계로 흡수한다.

## 한 줄 결정

**DartLab은 모델 provider를 호스팅하지 않는다. 설치된 agent CLI가 인증, 모델, native session, transcript를 소유하고, DartLab은 MCP로 금융 능력을 제공하며 UI와 CLI에는 provider-neutral Agent Runtime 계약만 공개한다.**

## 목표 구조

```text
DartLab local UI / dartlab ask
  -> DartLab Agent Session API
    -> src/dartlab/ai/runtime
      -> Codex app-server driver
      -> Claude stream-json driver
      -> generic ACP driver -> Cline
        -> provider-owned authentication and native session

installed agent CLI
  -> dartlab mcp --profile agent
    -> Skill OS -> ReadCapability -> EngineCall / RunPython
    -> evidence -> artifact -> Analysis Capsule
```

## 두 제품 모드

### External agent mode

사용자가 Codex, Claude Code, Cline terminal 또는 IDE에서 직접 일한다. DartLab은 공식 CLI 명령으로 MCP만 연결한다. 대화 UI와 session은 agent 제품이 소유한다.

### Embedded agent mode

사용자가 DartLab local UI에서 대화한다. DartLab runtime이 설치된 CLI의 documented structured protocol을 열고 native session을 제어한다. text-only one-shot CLI는 이 모드에 들어오지 못한다.

## 포트폴리오 경계

- `first-party-ai`: public deterministic/on-device compose와 surface 글쓰기만 남긴다. direct edge model과 local provider tier는 본 계획과 재정합한다.
- `ai-workbench-connector`: remote public evidence connector를 소유한다. local agent profile과 tool schema는 공유하되 remote auth와 Cloudflare gateway는 별도다.
- 기존 `src/dartlab/ai/agent.py`: migration 동안 compatibility facade, 최종적으로 session bridge가 된다.
- `src/dartlab/ai/providers/`: migration 종료 후 삭제 대상이다.

## 문서 지도

1. [00-product-charter.md](00-product-charter.md): 사용자 문제, 성공 조건, non-goals, outcome brief.
2. [01-current-state-audit.md](01-current-state-audit.md): 현재 hardcoding과 실제 CLI surface, runtrol 흡수 범위.
3. [02-runtime-architecture.md](02-runtime-architecture.md): package, contracts, drivers, process, events, session ownership.
4. [03-bootstrap-install-security.md](03-bootstrap-install-security.md): discovery, install, auth, MCP profile, sandbox, update와 rollback.
5. [04-api-cli-ui-contract.md](04-api-cli-ui-contract.md): server endpoints, CLI, UI state, generated contracts, Analysis Capsule.
6. [05-migration-validation-rollback.md](05-migration-validation-rollback.md): 단계별 구현, 영향 파일과 심볼, tests, deletion, rollback, 평가.
7. [06-progress-ledger.md](06-progress-ledger.md): 실측 기준선, 결정, NEXT.

## 구현 의존 순서

```text
dartlab-north-star Phase 0 contract
  -> tests/_attempts/agentRuntime three-runtime proof
    -> runtime contracts and process supervisor
      -> Codex + Claude + ACP drivers
        -> agent MCP profile and bootstrap
          -> session API and compatibility /api/ask
            -> Runtime Center UI
              -> direct provider deletion
```

구현 착수 시 최신 CLI surface를 다시 probe한다. 이 계획에 기록된 2026-08-02 버전은 재현 기준선이지 영구 capability 선언이 아니다.
