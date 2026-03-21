# AI Engine Development Guide

## Source Of Truth

- 데이터 source-of-truth: [`src/dartlab/core/registry.py`](C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src/dartlab/core/registry.py)
- AI capability source-of-truth: [`src/dartlab/core/capabilities.py`](C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src/dartlab/core/capabilities.py)

## 현재 구조 원칙

- `core.analyze()`가 AI 오케스트레이션의 단일 진입점이다.
- `tools/registry.py`는 capability 정의를 runtime에 바인딩하는 레이어다.
- `server/streaming.py`, `mcp/__init__.py`, UI SSE client는 capability 결과를 소비하는 adapter다.
- Svelte UI는 source-of-truth가 아니라 render sink다.

## 패키지 구조

- `runtime/`
  - `core.py`: 오케스트레이터
  - `events.py`: canonical/legacy 이벤트 계약
  - `pipeline.py`: pre-compute pipeline
  - `standalone.py`: public ask/chat bridge
  - `validation.py`: 숫자 검증
- `conversation/`
  - `dialogue.py`, `history.py`, `intent.py`, `focus.py`, `prompts.py`
- `context/`
  - `builder.py`: structured context build
  - `snapshot.py`: headline snapshot
  - `company_adapter.py`: facade mismatch adapter
- `tools/`
  - `registry.py`: tool/capability binding
  - `runtime.py`: tool execution runtime
  - `plugin.py`: external tool plugin bridge
  - `coding.py`: coding runtime bridge
- `providers/support/`
  - `codex_cli.py`, `cli_setup.py`, `ollama_setup.py`, `oauth_token.py`
  - provider 구현이 직접 쓰는 CLI/OAuth 보조 계층

루트 shim 모듈(`core.py`, `tools_registry.py`, `dialogue.py` 등)은 제거되었다. 새 코드는 반드시 하위 패키지 경로(`runtime/`, `conversation/`, `context/`, `tools/`, `providers/support/`)를 직접 import한다.

## UI Action 계약

- canonical payload는 `UiAction`이다.
- render payload는 `ViewSpec` + `WidgetSpec` schema를 기준으로 한다.
- widget id(`chart`, `comparison`, `insight_dashboard`, `table`)는 UI widget registry에 등록된 것만 사용한다.
- 허용 action:
  - `navigate`
  - `render`
  - `update`
  - `toast`
- canonical SSE UI 이벤트는 `ui_action` 하나만 유지한다.
- Svelte 측 AI bridge/helper는 `src/dartlab/ui/src/lib/ai/`에 둔다. `App.svelte`는 provider/profile 동기화와 stream wiring만 연결하는 shell로 유지한다.

## Provider Surface

- 공식 GPT 구독 계정 경로는 두 개다.
  - `codex`: Codex CLI 로그인 기반
  - `oauth-codex`: ChatGPT OAuth 직접 연결 기반
- 공개 provider surface는 `codex`, `oauth-codex`, `openai`, `ollama`, `custom`만 유지한다.
- `claude` provider는 public surface에서 제거되었다. 남은 Claude 관련 코드는 legacy/internal 용도로만 취급한다.
- provider alias(`chatgpt`, `chatgpt-oauth`)는 더 이상 공개/호환 surface에 두지 않는다.
- ask/CLI/server/UI는 같은 provider 문자열을 공유해야 하며, 새 GPT 경로를 추가할 때는 이 문서와 `core/ai/providers.py`, `server/api/ai.py`, `ui/src/App.svelte`, `cli/context.py`를 같이 갱신한다.

## Shared Profile

- AI 설정 source-of-truth는 `~/.dartlab/ai_profile.json`과 공통 secret store다.
- `dartlab.llm.configure()`는 메모리 전용 setter가 아니라 shared profile writer다.
- profile schema는 `defaultProvider + roles(analysis, summary, coding, ui_control)` 구조다.
- UI는 provider/model을 localStorage에 저장하지 않고 `/api/ai/profile`과 `/api/ai/profile/events`를 통해 동기화한다.
- API key는 profile JSON에 저장하지 않고 secret store에만 저장한다.
- OAuth 토큰도 legacy `oauth_token.json` 대신 공통 secret store로 이동한다.
- Ollama preload/probe는 선택 provider가 `ollama`일 때만 적극적으로 수행한다. 다른 provider가 선택된 상태에서는 상태 조회도 lazy probe가 기본이다.

## Company Adapter 원칙

- AI 레이어는 `company.ratios` 같은 facade surface를 직접 신뢰하지 않는다.
- headline ratio / ratio series는 [`company_adapter.py`](C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src/dartlab/engines/ai/company_adapter.py)로만 접근한다.
- facade와 엔진 surface mismatch를 발견하면 AI 코드 곳곳에서 분기하지 말고 adapter에 흡수한다.
