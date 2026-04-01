# UI 엔진 (L4 표현 계층)

> dartlab의 모든 시각 인터페이스를 관리한다.

## 한 눈에 보기

| 항목 | 설명 |
|------|------|
| **레이어** | L4 — 표현 (L3 AI 위) |
| **Surface** | Svelte SPA (`ui/`) + VSCode 확장 (`vscode/`) |
| **패리티 원칙** | VSCode 확장이 선행, Svelte가 따라감 |
| **SPA 서빙** | `dartlab share` → FastAPI가 `ui/build/` 정적 서빙 |
| **확장 배포** | VS Marketplace (독립 패키지) |
| **공유 코드** | markdown renderer, SSE handler, contentSplitter (TS↔JS 분기) |

## 디렉토리 구조

```
ui/                        ← Svelte SPA (루트 레벨)
├── src/                   ← Svelte 컴포넌트 + 라이브러리
├── widget/                ← 임베드 위젯 (IIFE 빌드)
├── build/                 ← 빌드 출력 (gitignore)
├── package.json
├── vite.config.js
└── vite.widget.config.js

vscode/                    ← VSCode 확장 (루트 레벨, 독립 배포)
├── src/                   ← TypeScript 확장 코드
├── webview/               ← 사이드바 Svelte UI
│   └── src/lib/           ← markdown/, api/, components/
├── dist/                  ← 빌드 출력
└── package.json           ← marketplace manifest
```

## 빌드

```bash
# Svelte SPA
cd ui && npm install && npm run build

# VSCode 확장
cd vscode && npm install && npm run build

# 위젯 (임베드용)
cd ui && npm run build:widget
```

## 서버 연동

`src/dartlab/server/web.py`가 `ui/build/`를 정적 서빙한다.
- `/assets/*` → `ui/build/assets/`
- 나머지 → `ui/build/index.html` (SPA fallback)
- 환경변수 `DARTLAB_UI_DIR`로 빌드 경로 오버라이드 가능

## 패리티 규칙

> **원칙: Svelte UI는 VSCode 확장을 따라간다.**
> VSCode 확장에 있는 기능은 Svelte에도 있어야 하고, VSCode에 없는 기능은 Svelte에서 숨긴다.

## 기능 대조표

| 기능 | VSCode 확장 | Svelte UI | 상태 |
|------|------------|-----------|------|
| AI 채팅 | chat panel | Chat 뷰 | **동기** |
| 대화 관리 (목록/생성/삭제/이름변경) | sidebar | Sidebar | **동기** |
| 대화 검색 | sidebar 필터 | SearchModal | **동기** |
| 스트리밍 응답 | SSE | SSE | **동기** |
| Provider/Model 선택 | 드롭다운 | 설정 패널 | **동기** |
| Slash 명령어 | /new, /clear, /model 등 | — | Svelte 미구현 |
| 상태표시줄 | 하단 서버 상태 | 상단 연결 상태 | **동기** |
| 공시뷰어 (Viewer) | — | 숨김 | VSCode 미구현 |
| 대시보드 (Dashboard) | — | 숨김 | VSCode 미구현 |
| Room 협업 | — | 활성 | Svelte 전용 (서버 기능) |
| Data Explorer (우측 패널) | — | 활성 | Svelte 전용 (서버 기능) |
| Excel 내보내기 | — | 활성 | Svelte 전용 (서버 기능) |
| 종목 검색 (Ctrl+K) | — | SearchModal | Svelte 전용 |

> Room, Data Explorer, Excel 내보내기는 서버 연동 전용 기능이므로 VSCode에 없어도 유지.
> Viewer/Dashboard는 VSCode에 동일 기능 추가 후 Svelte에서 복원.

## 숨김 처리 위치

| 항목 | 파일 | 처리 |
|------|------|------|
| Viewer/Dashboard 상단 탭 | `App.svelte:535-553` | 주석 |
| 모바일 하단 탭 | `App.svelte:742-756` | 주석 |
| 키보드 단축키 2/3 | `App.svelte:430-431` | 주석 |
| ActivityBar items | `ActivityBar.svelte:25-28` | 주석 |
| SearchModal 액션 | `SearchModal.svelte:30` | 주석 |
| App.svelte 콜백 | `App.svelte:799-800` | 주석 |

> 모든 TODO 주석에 "VSCode 확장에 동일 기능 추가 후 복원" 표기.

## 복원 절차

1. VSCode 확장에 해당 기능(예: Viewer) 구현 완료
2. 위 숨김 처리 위치의 주석 해제
3. 이 대조표 갱신
4. 양쪽 surface 동작 확인

## 신규 기능 추가 시

1. **VSCode 확장에 먼저 (또는 동시에) 구현**
2. Svelte UI에 반영
3. 이 대조표에 행 추가
