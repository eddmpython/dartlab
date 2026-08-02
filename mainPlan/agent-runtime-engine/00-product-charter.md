# 00. Product Charter

## 1. 문제

현재 DartLab AI는 provider마다 다음 책임을 직접 구현한다.

- OAuth와 API key
- base URL과 model catalog
- completion과 tool-call 변환
- provider 선택과 model fallback
- streaming 흉내
- provider별 UI 설정

이 구조는 DartLab의 차별점인 Skill OS, 정식 engine, evidence보다 모델 gateway 유지보수에 더 많은 경계를 만든다. Codex adapter조차 agent session을 쓰지 않고 `codex exec`의 최종 text를 다시 잘라 stream한다.

사용자는 이미 Codex, Claude Code, Cline에 로그인해 있을 수 있다. DartLab이 다시 credential을 받고 모델 API를 흉내 내는 대신 설치된 agent에게 금융 작업대를 제공해야 한다.

## 2. 사용자 결과

### 첫 사용자

이미 agent CLI가 설치된 사용자는 DartLab을 열었을 때 다음을 경험한다.

1. 설치된 runtime과 실제 상태가 자동 탐색된다.
2. `DartLab 연결` 한 동작으로 공식 MCP 설정이 적용된다.
3. 회사명이나 질문을 입력한다.
4. agent가 Skill OS와 engine을 자율적으로 사용한다.
5. 답, evidence, artifact가 DartLab UI에 같은 계약으로 나타난다.
6. exact evidence를 열어 verified analysis loop를 완료한다.

### 신규 사용자

agent CLI가 없는 사용자는 다음을 경험한다.

1. OS와 설치 채널에 맞는 install plan을 본다.
2. 실행할 command, source, 권한, rollback 가능 여부를 확인한다.
3. 명시적으로 승인한다.
4. 설치 뒤 CLI가 소유한 login 화면으로 이동한다.
5. DartLab은 token을 읽지 않고 ready 여부만 다시 probe한다.

## 3. Outcome brief

```text
Primary goal ID: completeVerifiedAnalysisLoop
Supporting goal IDs: startFromRealQuestion, reachFirstEvidence, verifyAnalysisResult,
  retainAnalysisOutcome, protectResearchTrust, keepAnalysisResponsive, keepCapabilityParity
User and real subject: local desktop user asking about a real company, filing, market, industry or dataset
Observed loss transition: provider setup and one-shot completion prevent installed agents from using DartLab tools as agents
Baseline authority: current source audit plus local Codex, Claude Code and Cline protocol probes
Expected metric movement: ready runtime to verified analysis completion becomes possible without DartLab model credentials
Guardrails at risk: provider token boundary, shell/file permissions, transcript ownership, event backpressure, evidence identity
Complete vertical slice: discover -> connect MCP -> open native session -> call DartLab engine -> deliver -> resolve evidence
Automated evidence: fixture drivers, protocol captures, contract and UI behavior tests
Operator evidence: real installed CLI two-turn, resume, cancel, MCP and approval journey
Rollback: /api/ask compatibility switch to legacy provider until parity, no transcript migration
Exit decision: expand only when one runtime completes the full slice and all trust guards pass
```

## 4. 성공 조건

- DartLab production core와 UI에 direct model OAuth/API key 입력이 없다.
- core와 UI에 runtime ID 기반 기능 분기가 없다.
- runtime manifest에 model ID와 capability list가 없다.
- Codex, Claude, generic ACP가 persistent two-turn session을 통과한다.
- agent가 `ReadSkill` 또는 server instructions에서 시작해 DartLab engine을 실제 호출한다.
- provider native session ID로 resume한다.
- unknown event가 소실되지 않는다.
- DartLab은 provider transcript와 credential을 저장하지 않는다.
- UI evidence resolve까지 한 verified analysis loop가 완결된다.
- 설치 실패와 update 실패가 last-known-good runtime을 보존한다.

## 5. Non-goals

- 새로운 모델 API proxy
- provider token 추출 또는 subscription OAuth 재사용
- provider transcript directory reverse engineering
- 모델 ID 수기 catalog
- 고정 multi-agent graph
- agent별 prompt copy
- runtrol daemon 의존
- silent install, silent auth, 위험 권한 자동 승인
- public browser에서 local CLI를 직접 제어
- remote MCP connector의 Cloudflare와 auth 재구현
- provider 답변을 DartLab이 의미적으로 재작성

## 6. Product positioning

새 정체성은 Bring Your Agent다.

- agent CLI: reasoning, model, auth, conversation.
- DartLab: finance capability, evidence, reproducibility, artifact.
- Runtime Center: 설치와 연결 상태를 관리하는 local control surface.
- Analysis Capsule: transcript 없이 분석 상태를 runtime 간 전달하는 DartLab 자산.
