# VSCode Extension

dartlab의 1순위 UI surface. AI 채팅 + 프로바이더 연결 + MCP 자동 등록.

| 항목 | 내용 |
|------|------|
| 레이어 | L4 (표현) |
| 경로 | `vscode/` (루트 레벨, 독립 패키지) |
| 배포 | VS Marketplace (`vsce-*` 태그 → GitHub Actions) |
| 아키텍처 | Svelte webview ↔ postMessage ↔ extension host ↔ stdio JSON Lines ↔ `dartlab chat --stdio` |
| PyPI 의존 | stdio.py 변경 시 dartlab PyPI도 같이 배포해야 다른 PC에서 동작 |

## 버전 규칙

- **0.2.x** — 끝자리만 올린다 (0.2.0 → 0.2.1 → 0.2.2 → ...)
- `vscode/package.json`의 `version` 필드가 진실의 원천
- 태그: `vsce-{버전}` (예: `vsce-0.2.1`)
- CHANGELOG: `vscode/CHANGELOG.md`

## 배포 절차

1. `vscode/package.json` version 올리기 (끝자리)
2. `vscode/CHANGELOG.md` 작성
3. 커밋 + 푸시
4. `git tag vsce-{버전}` + `git push origin vsce-{버전}`
5. GitHub Actions가 webview 빌드 → extension 빌드 → vsce publish
6. **stdio.py 변경이 포함됐으면 dartlab PyPI도 함께 배포** (v* 태그)
7. Actions 결과까지 확인 완료가 배포의 마지막 단계

## 아키텍처

```
┌─ VSCode Extension Host (TS/Node)
│  ├─ extension.ts          활성화, MCP 자동 등록
│  ├─ bridge/
│  │  ├─ stdioProxy.ts      child process 관리, fallback chain, healthcheck
│  │  └─ messageProtocol.ts webview ↔ extension host 메시지 타입
│  ├─ providers/
│  │  ├─ chatWebviewBase.ts webview 셋업 + 메시지 라우팅
│  │  ├─ chatPanelManager.ts 에디터 탭 패널
│  │  └─ sidebarViewProvider.ts 사이드바 세션 목록
│  └─ commands/             커맨드 등록
│
├─ Webview UI (Svelte + TS)
│  ├─ lib/components/
│  │  ├─ ChatPanel.svelte   대화 관리 + 웰컴 화면
│  │  ├─ ChatHeader.svelte  상태 + 프로바이더 드롭다운
│  │  ├─ ChatInput.svelte   입력 + 슬래시 커맨드
│  │  └─ MessageBubble.svelte 메시지 렌더링
│  ├─ lib/api/
│  │  ├─ client.ts          postMessage API
│  │  └─ sseHandler.ts      JSON 이벤트 → 메시지 업데이트
│  └─ lib/chart/            차트 컴포넌트
│
└─ Python Backend (child process)
   └─ src/dartlab/cli/stdio.py  JSON Lines 프로토콜
```

## stdio 프로토콜

```
→ {"type":"ping"}                        ← {"event":"pong","data":{}}
→ {"type":"status"}                      ← {"event":"status","data":{provider, model, ready, providers[]}}
→ {"type":"setProvider","provider":"..."}
   ├─ API 키 있음                         ← {"event":"providerChanged","data":{...}}
   ├─ API 키 없음                         ← {"event":"needCredential","data":{provider, signupUrl}}
   └─ OAuth provider                      ← {"event":"oauthStart","data":{authUrl, provider}}
                                          ← {"event":"providerChanged","data":{...}}  (로그인 완료 후)
→ {"type":"oauthPasteToken","tokenJson":"..."}
                                          ← {"event":"providerChanged","data":{...}}
→ {"id":"1","type":"ask","question":"..."}
   ← {"id":"1","event":"meta","data":{company, stockCode}}
   ← {"id":"1","event":"chunk","data":{text}} × N
   ← {"id":"1","event":"done","data":{}}
→ {"type":"exit"}
```

## 프로바이더 연결 원칙

provider 선택하면 바로 연결까지 끝나야 한다. 추가 설정 페이지 없음.

| provider 종류 | 플로우 |
|--------------|--------|
| API 키 (Gemini, Groq 등) | 선택 → signupUrl 브라우저 → InputBox 키 입력 → 저장 → 연결 |
| OAuth (ChatGPT) | 선택 → 브라우저 PKCE 로그인 → callback → 토큰 저장 → 연결 |
| OAuth 토큰 입력 (방화벽) | "토큰 입력" → InputBox에 JSON 붙여넣기 → 저장 → 연결 |
| 로컬 (Ollama) | 선택 → 바로 연결 |

연결 완료 시 "연결 완료" 메시지 표시.

## spawn fallback chain

extension이 dartlab 프로세스를 찾는 순서:
1. `pythonPath` 설정 (있으면)
2. `uv run python -X utf8 -m dartlab chat --stdio`
3. `python -m dartlab chat --stdio`
4. `python3 -m dartlab chat --stdio`
5. `dartlab chat --stdio`

성공한 후보를 기억해서 다음 재시작 때 먼저 시도.

## 빌드 + 검증

```bash
cd vscode && npm run verify    # esbuild → vite → vitest → tsc → vscode-test
cd vscode && npm run build     # extension만
cd ui/vscode && npm run build  # webview만
```

## 에러 메시지 원칙

- UI에서 `dartlab.setup(...)` 같은 CLI 명령을 안내하지 않는다
- `_sanitizeErrorForUi()`가 stdio 레이어에서 CLI 안내를 제거
- 인증 에러 시 provider 변경을 UI에서 직접 제안

## MCP 자동 등록

extension 활성화 시 `.mcp.json` + `.vscode/mcp.json`에 dartlab MCP 서버 자동 등록.
Claude Code, Copilot 등에서 `@dartlab` 도구를 바로 사용 가능.

## 관련 코드

| 경로 | 역할 |
|------|------|
| `vscode/src/` | TypeScript extension |
| `ui/vscode/src/` | Svelte webview |
| `src/dartlab/cli/stdio.py` | Python backend 프로토콜 |
| `src/dartlab/guide/providers.py` | provider 카탈로그 |
| `src/dartlab/guide/credentials.py` | 자격증명 관리 |
| `src/dartlab/ai/providers/support/oauth_token.py` | OAuth 토큰 관리 |
