# Agent Runtime 아키텍처

Agent Runtime의 정본은 `src/dartlab/ai/runtime/`이다. 공급자별 모델 API 통합 대신 설치형 CLI 프로토콜을 어댑터로 두고, DartLab 계약과 품질 판정은 런타임 공통 계층이 소유한다.

## 경계

```text
manifest와 discovery
  -> 준비 상태와 기본 런타임 선택
  -> 네이티브 CLI driver와 session binding
  -> 읽기 전용 DartLab MCP
  -> 정규화 AgentEvent
  -> answer quality와 evidence commit
  -> public Agent event gateway
  -> CLI와 local GUI
```

- `manifests/*.toml`은 실행 파일 후보, 버전 확인, 인증 확인, 로그인 명령, 프로토콜 지원 여부를 선언한다.
- `registry.py`와 `discovery.py`는 매니페스트를 읽어 설치와 인증 상태를 판정한다. 인증 명령의 원문 출력은 공개 상태에 포함하지 않는다.
- `engine.py`는 기본 런타임 선택, 대화와 네이티브 세션 결속, 취소, 재개, 근거 수집을 소유한다.
- driver는 Codex app server, Claude stream JSON, ACP 차이를 `AgentEvent`로 정규화한다.
- `agent.py`는 답변 후보를 품질 판정 전까지 보류하고, 필요하면 같은 네이티브 세션과 outcome에서 한 번 보완한다.
- 후보 판정과 최종 판정은 각각 `verify` 이벤트로 남긴다. 최종 판정이 실패하면 답변 chunk를 공개하지 않고 실패 `done`으로 종료한다.
- `agentGateway.py`는 공개 이벤트 allowlist만 SSE로 투영한다. 실행마다 `RUN_ERROR`는 최대 한 번, `RUN_FINISHED`는 정확히 한 번 발행한다.

## 도구와 권한

설치형 에이전트에는 `agent` MCP profile만 연결한다. 이 profile은 Skill OS 조회와 정식 엔진 읽기 호출만 광고한다. 임의 Python 실행, 파일 저장, 데이터 변경 도구는 광고하지 않는다. Claude driver도 명시적 읽기 전용 도구 목록만 허용하며 일반 shell이나 도구 검색 우회를 열지 않는다.

설치와 MCP 연결은 명령 배열과 digest를 먼저 제시한 뒤 정확한 digest 승인에서만 실행한다. shell 문자열을 조립하지 않는다. 로그인은 공식 CLI 명령을 사용자에게 제시한다.

## 근거 무결성

`EngineCall` 결과는 canonical tool name, tool call ID, source identity, 기간과 값을 보존한다. 연간 손익과 현금흐름은 분기 합계, 연간 재무상태는 4분기 말 snapshot으로 만든다. 로컬 계산 결과는 canonical upstream lineage가 있을 때만 최종 근거로 인정한다.

품질 실패 시 첫 답변의 근거는 candidate로 격리한다. 보완 답변이 통과한 경우에만 최종 evidence store에 commit한다.
Python ask와 CLI는 실패 `done`을 빈 문자열이나 종료코드 0으로 낮추지 않는다.
