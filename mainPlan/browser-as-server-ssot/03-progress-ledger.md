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

## wheel 0.10.9 (2026-07-11)

- [x] pyproject 0.10.9 bump + CHANGELOG [0.10.9] Added(dartlab.webapi).
- [x] `uv build --wheel` -> dist/dartlab-0.10.9-py3-none-any.whl(21.4MB, webapi 2파일 포함 확인).
- [x] 브라우저 실측(로컬 서빙 0.10.9): health 200 version=0.10.9 + panel 200 + scan 200 shape[2241,8]. dispatch 로직은 pyodideWorker PYAPI_SETUP 동일.
- [ ] **HF 공개 배포(운영자 게이트)**: `pyodide/dartlab-0.10.9-...whl` 업로드는 공개 배포 표면이라 auto-mode 분류기가 차단(2026-07-11). 운영자 명시 발행 단어("올려"/"발간해") 필요. **이 배포 전엔 pyodideWorker.ts 포인터·README 를 0.10.9 로 올리지 않는다**(올리면 wheel 404). 배포+포인터+README+push 는 한 묶음.

## Phase 2 (블로그·노트북 소비자, 2026-07-11 토론 수렴)

전문 에이전트 5 렌즈 토론(57 에이전트, 8 생존/9 탈락) 결과. 회의론자 정면 답: 빌드타임 스냅샷(CompanyFinancials)이 기본 우세. 라이브는 스냅샷이 원리적으로 불가능할 때만 이긴다 (①독자입력 파라미터 ②빌드셋 밖 ③scan 전유니버스 지금값). 그래서 회사글 고정 재무표=스냅샷, dartlab 이야기 횡단·파라미터=라이브.

- [x] **코어**: `landing/src/lib/pyapi/liveData.ts`(resolveEndpoint 계약검증 + fetchLive + renderLiveTable 이스케이프+tier배지 + hydrateLiveData). vitest 8건.
- [x] **노트북 어댑터**: richMarkdown `@[data]`(youtube·video·data 3형제) + MarkdownCell `$effect` hydrate. 코드셀엔 /pyapi 안 붙임(execute 경로 불가침, 직접 import).
- [x] **블로그 어댑터**: `LiveData.svelte`(CompanyFinancials 선례 동형). 첫 소비자 = story 01 `<LiveData spec="scan/growth">` (전상장사 2,241행, 빌드셋 불가). 고아 해소.
- [x] **한 번 저술, 두 표면**: `fromMarkdown.ts` 가 `<LiveData spec="X">` -> `@[data](X)` 투영 번역 + script 스캐폴드 제거. 블로그 mdsvex 컴포넌트가 노트북 richMarkdown 으로 자동 투영.
- [x] **계약 안전 3 중**: resolveEndpoint 런타임 null + liveData.test 빌드 + browserApi 404. 새 AST 게이트 불필요(토론 kill).
- [x] **tier 배지**: pyodideWorker.ts:393 이 x-dartlab-tier 주입 -> ld-tier 배지. G5 완료.

**폐기(토론 kill)**: Phase 3 노트북 사이드바 데이터 패널(코드셀=직접 import, 마크다운셀=@[data], 세 번째 방법은 덕지덕지) · DataFrameTable 재사용(읽기전용 임베드엔 renderLiveTable) · 블로그 ```data 펜스(두 번째 문법) · @[data] 전용 notebookContract AST 게이트(잉여).

## NEXT (세션 재개점)
- [ ] **landing push**: Phase 0~2 배선 전부 commit 됨, UI 라 운영자 승인("올려/발간해") 대기. wheel 배포와 한 묶음.
- [x] **Phase 2 완료**: 위 참조. 블로그 story 01 + 노트북 @[data] + 코어 + 투영.
- [~] **Phase 3 폐기**: 노트북 사이드바 데이터 패널은 토론 kill(덕지덕지). @[data] 마크다운셀이 정답.
- [ ] 가드: G1(async) 완료. G5(tier 배지) 완료. G2(한 커널)·G3(노트북 회귀)·G4(계약 무증가)는 코어 유닛테스트·vitest 회귀·resolveEndpoint allowlist 로 충족.

## 열린 질문

- `browserApi.py` 를 dartlab wheel 에 넣을 때 fastapi import 를 어떻게 격리하나(wheel 은 fastapi 제외). -> 라우터 정의를 fastapi lazy import 로 함수 안에서, 또는 순수 핸들러 + 워커가 fastapi 라우팅 조립.
- 노트북과 데이터 API 가 전역을 공유할 때 격리(셀이 만든 c 를 API 가 보면 편의지만 오염 위험). v1 은 분리 네임스페이스 권장.
