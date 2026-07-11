# 03. Progress Ledger - 결정 원장·재개점

상태: 진행 v0.1 (2026-07-11)

---

## 결정

- **2026-07-11 채택 결정**: codaro browser-as-server 를 dartlab 에 접목. 3발명 중 이것만(소켓 브리지·힙 스냅샷은 dartlab 전제와 불합). 근거 = 엔드투엔드 실측 PASS(`tests/_attempts/browserAsServer/`).
- **아키텍처 확정**: 한 pyodide 커널, 두 인터페이스(노트북 postMessage execute + 데이터 fetch/SW/ASGI). 노트북 워커 대체 아님. 근거 = /exec HTTP 8ms(오버헤드 무시) + 노트북 스트리밍/위젯은 HTTP 부적합.
- **콜드스타트 판정**: fastapi 추가 1.6s(실측). lazy+precache+프리워밍으로 은닉. dartlab 10.3s 는 커널 공유라 기존 프리워밍이 커버.

## 실측 근거 (tests/_attempts/browserAsServer, gitignore 로컬)

- GET /pyapi/panel/005930 -> 200 shape[36,43]. GET /pyapi/scan/growth -> 200 rows 2241. (SW 엔드투엔드)
- POST /pyapi/exec -> 200, 8~9ms.
- 콜드: pyodide 3.7s + fastapi 1.6s + dartlab 10.3s = 18.4s.
- async def 강제(sync 는 can't start new thread). 직접 ASGI dispatch(httpx 우회, 0.27.5 검증).

## 진행 (2026-07-11)

- [x] **Phase 0 완료**: `src/dartlab/webapi/browserApi.py`(async 데이터 라우터 SSOT, fastapi lazy). `pyodideWorker.ts` ensureServer + case 'pyapi'. workerEngine.serveApi + executionEngine.PyApiResponse 인터페이스. 커밋 189836a57(dartlab) + fce0d3e1a(landing).
- [x] **Phase 1 완료**: `service-worker.ts` /pyapi/* 라우팅 + `pyapi/pyapiBridge.ts`(SW relay) + +layout.svelte onMount 설치. 사이트 전역에서 fetch('/pyapi/*') 가능(블로그·노트북 포함).
- [x] **G1 게이트**: `tests/audit/browserApiAsync.py`(AST, async 강제) + `tests/webapi/test_browserApi.py`(3건).
- [x] **검증**: webapi 포함 로컬 wheel 로 브라우저 실측 health·panel·scan 200. landing build + vitest 145 통과.

## NEXT (세션 재개점)

- [ ] **wheel 재배포(게이트)**: 배포된 0.10.8 엔 dartlab.webapi 가 없다. 0.10.9 patch + HF 업로드 + pyodideWorker.ts 포인터 bump 후에야 프로덕션 /pyapi 가 산다. 운영자 push 단어 필요(0.10.8 배포와 동형).
- [ ] **landing push**: Phase 0~1 배선은 commit 됨, UI 라 운영자 승인 대기.
- [ ] **Phase 2**: dartlab 이야기 LiveTable(마크다운 `@[data](company/005930/panel/IS)` 확장, richMarkdown 임베드 계열). 라이브 표.
- [ ] **Phase 3**: 노트북 데이터 패널(사이드바에서 /pyapi 호출).
- [ ] 가드 G2~G5(한 커널·회귀·계약·tierUsed).

## 열린 질문

- `browserApi.py` 를 dartlab wheel 에 넣을 때 fastapi import 를 어떻게 격리하나(wheel 은 fastapi 제외). -> 라우터 정의를 fastapi lazy import 로 함수 안에서, 또는 순수 핸들러 + 워커가 fastapi 라우팅 조립.
- 노트북과 데이터 API 가 전역을 공유할 때 격리(셀이 만든 c 를 API 가 보면 편의지만 오염 위험). v1 은 분리 네임스페이스 권장.
