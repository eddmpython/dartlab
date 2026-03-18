# AI Engine — Provider 현황 및 유지보수 체크리스트

## Provider 목록 (7개)

| Provider | 파일 | 인증 | 기본 모델 | 안정성 |
|----------|------|------|----------|--------|
| `openai` | openai_compat.py | API Key | gpt-4o | **안정** — 공식 SDK |
| `claude` | claude.py | API Key / 프록시 | claude-sonnet-4-6 | **안정** — 공식 SDK |
| `ollama` | ollama.py | 없음 (localhost) | llama3.1 | **안정** — 로컬 |
| `custom` | openai_compat.py | API Key | gpt-4o | **안정** — OpenAI 호환 |
| `chatgpt` | oauthCodex.py | **OAuth PKCE** | gpt-5.4 | **취약** — 비공식 API |
| `codex` | codex.py | CLI 세션 | CLI config 또는 gpt-4.1 | **취약** — CLI 의존 |
| `claude-code` | claude_code.py | CLI 세션 | sonnet | **보류중** — OAuth 지원 전 비공개 |

---

## ChatGPT OAuth Provider — 핵심 리스크

### 왜 취약한가

`chatgpt` provider는 **OpenAI 비공식 내부 API** (`chatgpt.com/backend-api/codex/responses`)를 사용한다.
공식 OpenAI API (`api.openai.com`)가 아니므로 **예고 없이 변경/차단될 수 있다**.

### 정기 체크 항목

**1. 엔드포인트 변경**
- 현재: `https://chatgpt.com/backend-api/codex/responses`
- 파일: [oauthCodex.py](providers/oauthCodex.py) `CODEX_API_BASE`, `CODEX_RESPONSES_PATH`
- OpenAI가 URL 경로를 변경하면 즉시 404/403 발생
- 확인법: `dartlab status` 실행 → chatgpt available 확인

**2. OAuth 인증 파라미터**
- Client ID: `app_EMoamEEZ73f0CkXaXp7hrann` (Codex CLI에서 추출)
- 파일: [oauthToken.py](../oauthToken.py) `CHATGPT_CLIENT_ID`
- OpenAI가 client_id를 갱신하거나 revoke하면 로그인 불가
- 확인법: OAuth 로그인 시도 → "invalid_client" 에러 여부

**3. SSE 이벤트 타입**
- 현재 파싱하는 타입 3개:
  - `response.output_text.delta` — 텍스트 청크
  - `response.content_part.delta` — 컨텐츠 청크
  - `response.output_item.done` — 아이템 완료
- 파일: [oauthCodex.py](providers/oauthCodex.py) `stream()`, `_parse_sse_response()`
- OpenAI가 이벤트 스키마를 변경하면 응답이 빈 문자열로 돌아옴
- 확인법: 스트리밍 응답이 도착하는데 텍스트가 비어있으면 이벤트 타입 변경 의심

**4. 요청 헤더**
- `originator: codex_cli_rs` — Codex CLI 사칭
- `OpenAI-Beta: responses=experimental` — 실험 API 플래그
- 파일: [oauthCodex.py](providers/oauthCodex.py) `_build_headers()`
- 이 헤더 없이는 403 반환됨
- OpenAI가 originator 검증을 강화하면 차단됨

**5. 모델 목록**
- `AVAILABLE_MODELS` 리스트는 수동 관리
- 파일: [oauthCodex.py](providers/oauthCodex.py) `AVAILABLE_MODELS`
- 새 모델 출시/폐기 시 수동 업데이트 필요
- GPT-4 시리즈 (gpt-4, gpt-4-turbo 등)는 이미 제거됨

**6. 토큰 만료 정책**
- access_token: expires_in 기준 (현재 ~1시간)
- refresh_token: 만료 정책 불명 (OpenAI 미공개)
- 파일: [oauthToken.py](../oauthToken.py) `get_valid_token()`, `refresh_access_token()`
- refresh_token이 만료되면 재로그인 필요
- 확인법: 며칠 방치 후 요청 → 401 + refresh 실패 여부

### 브레이킹 체인지 대응 순서

1. 사용자가 "ChatGPT 안됨" 보고
2. `dartlab status` 로 available 확인
3. available=False → OAuth 로그인 재시도
4. 로그인 실패 → client_id 변경 확인 (opencode-openai-codex-auth 참조)
5. 로그인 성공인데 API 호출 실패 → 엔드포인트/헤더 변경 확인
6. API 호출 성공인데 응답 비어있음 → SSE 이벤트 타입 변경 확인

### 생태계 비교 — 누가 같은 API를 쓰는가

ChatGPT OAuth(`chatgpt.com/backend-api`)를 사용하는 프로젝트는 **전부 openai/codex CLI 역공학** 기반이다.

| 프로젝트 | 언어 | Client ID | 모델 목록 | refresh 실패 처리 | 토큰 저장 |
|----------|------|-----------|----------|------------------|----------|
| **openai/codex** (공식) | Rust | 하드코딩 | `/models` 동적 + 5분 캐시 | 4가지 분류 | 파일/키링/메모리 3중 |
| **opencode plugin** | TS | 동일 복제 | 사용자 설정 의존 | 단순 throw | 프레임워크 위임 |
| **ai-sdk-provider** | TS | 동일 복제 | 3개 하드코딩 | 단순 throw | codex auth.json 재사용 |
| **dartlab** (현재) | Python | 동일 복제 | 13개 하드코딩 | None 반환 | `~/.dartlab/oauth_token.json` |

**공통 특징:**
- Client ID `app_EMoamEEZ73f0CkXaXp7hrann` 전원 동일 (OpenAI public OAuth client)
- `originator: codex_cli_rs` 헤더 전원 동일
- OpenAI가 이 값들을 바꾸면 **전부 동시에 깨짐**

**openai/codex만의 차별점 (dartlab에 없는 것):**
1. Token Exchange — OAuth 토큰 → `api.openai.com` 호환 API Key 변환
2. Device Code Flow — headless 환경 (서버, SSH) 인증 지원
3. 모델 목록 동적 조회 — `/models` 엔드포인트 + 캐시 + bundled fallback
4. Keyring 저장 — OS 키체인 (macOS Keychain, Windows Credential Manager)
5. refresh 실패 4단계 분류 — expired / reused / revoked / other
6. WebSocket SSE 이중 지원

**참고: opencode와 oh-my-opencode(현 oh-my-openagent)는 ChatGPT OAuth를 사용하지 않는다.**
- opencode: GitHub Copilot API 인증 (다른 시스템)
- oh-my-openagent: MCP 서버 표준 OAuth 2.0 + PKCE (플러그인)

### 추적 대상 레포지토리

변경사항 감지를 위해 다음 레포를 추적한다.

| 레포 | 추적 이유 | Watch 대상 |
|------|----------|-----------|
| **openai/codex** | canonical 구현. Client ID, 엔드포인트, 헤더의 원본 | `codex-rs/core/src/auth.rs`, `model_provider_info.rs` |
| **numman-ali/opencode-openai-codex-auth** | 빠른 변경 반영 (TS라 읽기 쉬움) | `lib/auth/`, `lib/constants.ts` |
| **ben-vargas/ai-sdk-provider-chatgpt-oauth** | Vercel AI SDK 호환 참조 | `src/auth/` |

### 향후 개선 후보 (codex에서 가져올 수 있는 것)

1. **모델 목록 동적 조회** — `chatgpt.com/backend-api/codex/models` 호출 + JSON 캐시
2. **refresh 실패 분류** — expired/reused/revoked 구분하여 사용자에게 구체적 안내
3. **Token Exchange** — OAuth → API Key 변환으로 `api.openai.com` 호환 (듀얼 엔드포인트)

---

## Codex CLI Provider — 리스크

### 왜 취약한가

`codex` provider는 OpenAI `codex` CLI 바이너리를 subprocess로 호출한다.
CLI의 JSONL 출력 포맷이 변경되면 파싱 실패.

### 현재 동작

- `~/.codex/config.toml`의 model 설정을 우선 흡수
- `codex --help`, `codex exec --help`를 읽어 command/sandbox capability를 동적 감지
- 일반 질의는 `read-only`, 코드 수정 의도는 `workspace-write` sandbox 우선
- 별도 `run_codex_task` tool로 다른 provider에서도 Codex CLI 코드 작업 위임 가능

### 체크 항목

- CLI 출력 포맷: `item.completed.item.agent_message.text` 경로
- CLI 플래그: `--json`, `--sandbox ...`, `--model ...`, `--skip-git-repo-check`
- CLI 설치: `npm install -g @openai/codex`
- 파일: [codex.py](providers/codex.py)

---

## Claude Code CLI Provider — 보류중

### 현재 상태

VSCode 환경에서 `CLAUDECODE` 환경변수가 설정되어 SDK fallback 모드로 진입하지만,
SDK fallback에서 API key 추출(`claude auth status --json`)이 또 subprocess를 호출하는 순환 문제.

### 알려진 이슈

- 테스트 31/32 pass, `test_complete_timeout` 1개 fail
- VSCode 내에서 CLI 호출이 hang되는 케이스 (중첩 세션)
- `_probe_cli()` 8초 타임아웃으로 hang 감지 후 SDK 전환
- 파일: [claude_code.py](providers/claude_code.py)

---

## 안정 Provider — 특이사항 없음

### openai / custom (openai_compat.py)
- 공식 `openai` Python SDK 사용
- 버전 업데이트 시 SDK breaking change만 주의
- tool calling 지원

### claude (claude.py)
- 공식 `anthropic` Python SDK + OpenAI 프록시 이중 모드
- base_url 있으면 OpenAI 호환, 없으면 Anthropic 네이티브

### ollama (ollama.py)
- localhost:11434 OpenAI 호환 엔드포인트
- `preload()`, `get_installed_models()`, `complete_json()` 추가 기능
- tool calling 지원 (v0.3.0+)

---

## 마지막 점검일

- 2026-03-10: ChatGPT OAuth 정상 동작 확인 (gpt-5.4)
- 2026-03-10: Claude Code 보류 (VSCode 환경이슈)
