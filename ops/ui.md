# UI 패리티 규칙 (Svelte ↔ VSCode 확장)

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
