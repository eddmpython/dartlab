# 01. Architecture - 한 커널, 두 인터페이스

상태: 상세 설계 v0.1 (2026-07-11)
범위: 배선 구조, 영향 파일·심볼, async 강제·의존, 결과 일관성, 인터럽트.

---

## 1. 현재 구조 (조사 실증)

- 노트북 실행: 페이지 -> `executionStore` -> `WorkerEngine`(`workerEngine.ts:9`, postMessage `call(cmd,args)`) -> `pyodideWorker.ts`(웹워커, `case 'execute'`/'warm'/'getCompletions'/... 15 메시지).
- `ExecutionEngine` 인터페이스(`executionEngine.ts:36`): initialize·warm?·execute(code)->CellOutput + 완성·변수·파일.
- 데이터(터미널): `ui/.../runtime/src/data/fetch` -> `data/origins` -> HF 직독. 무거운/라이브 = :8400 FastAPI.
- SW: `landing/src/service-worker.ts` (SvelteKit, shell precache + pyodide/wheel on-demand 캐시).

## 2. 목표 구조

```text
[노트북·블로그 실행셀]                    [데이터 API 소비자(터미널·글·외부)]
  executionStore.execute(code)              fetch('/pyapi/company/005930/panel/IS')
       |                                          |
  WorkerEngine.call('execute')             Service Worker (/pyapi/* 가로채기)
       |                                          |  postMessage -> 컨트롤 페이지
       |                                     WorkerEngine.serveApi(method, path, body)
       |                                          |  call('pyapi', ...)
       +--------------------+---------------------+
                            |  (한 pyodide 워커, 한 인터프리터)
                     pyodideWorker.ts
                       case 'execute' -> 셀 코드 exec (기존 불변)
                       case 'pyapi'   -> FastAPI app(scope, receive, send)  (신설)
                            |
                     dartlab (wheel 0.10.8)
```

핵심: `execute` 와 `pyapi` 가 **같은 워커의 같은 파이썬 전역**을 공유한다. 셀에서 만든 상태를 API 가 볼 수 있고(필요 시), 콜드스타트·메모리가 1배다.

## 3. 신설/수정 (영향 파일·심볼)

| 구분 | 경로 | 내용 |
|---|---|---|
| 수정 | `landing/src/lib/notebook/engine/pyodideWorker.ts` | `ensureServer()`(fastapi+dartlab 로드 + ASGI 앱 build, lazy), `case 'pyapi'`(dispatch: scope/receive/send 직접 호출, httpx 우회). async 엔드포인트만. |
| 수정 | `landing/src/lib/notebook/engine/executionEngine.ts` | 인터페이스에 `serveApi?(method, path, body): Promise<{status, headers, body}>` 추가. |
| 수정 | `landing/src/lib/notebook/engine/workerEngine.ts` | `serveApi` 구현 = `call('pyapi', {method, path, body})`. |
| 신설 | `landing/src/lib/server/pyapiBridge.ts` | 페이지 측 브리지: SW message('pyapi') 수신 -> 공유 WorkerEngine.serveApi -> port.postMessage. 단일 진입(덕지덕지 방지). |
| 수정 | `landing/src/service-worker.ts` | `/pyapi/*` fetch 가로채 컨트롤 페이지로 relay(codaro serve-sw.js 패턴). shell/데이터 캐시 로직 불변. |
| 신설 | `src/dartlab/server/browserApi.py` | 브라우저 서빙용 async 데이터 라우터(panel·select·analysis·scan·credit·story). 기존 라우터의 async 미러 최소셋. wheel 에 포함(현 fastapi 는 emscripten 제외라 서버 모듈은 브라우저 wheel 밖 -> 이 라우터만 순수 모듈로 분리해 pyodide 에서 fastapi 위에 마운트). |

원칙(덕지덕지 금지): 새 표면 컴포넌트가 티어를 고르지 않는다. `pyapiBridge` 하나가 SW<->워커 relay 를 소유한다. 데이터 엔드포인트는 dartlab 공개계약(엔진명)의 async 노출일 뿐, 새 계약을 만들지 않는다.

## 4. async 강제 (make-or-break)

sync `def` 엔드포인트는 Starlette 가 `anyio.to_thread` 로 돌려 pyodide 에서 `can't start new thread`. 그러므로 `browserApi.py` 의 모든 엔드포인트는 `async def`. dartlab 호출 자체는 동기(panel 등)라 async 함수 안에서 직접 부른다(그 함수가 이벤트 루프에서 돌아 스레드 안 씀). 게이트: `browserApi.py` 에 sync `def` 엔드포인트가 없음을 AST 로 검사(Phase 2 가드).

## 5. 의존·설치

- fastapi + starlette(순수휠) + pydantic-core(pyodide 0.27.5 lockfile wasm) micropip.
- dartlab pyproject 의 fastapi 는 `sys_platform != 'emscripten'` 제외 유지(서버 전체는 브라우저 wheel 밖). 브라우저는 `browserApi.py`(순수 모듈, dartlab wheel 에 포함) 를 fastapi 위에 얹는다. fastapi 는 워커가 lazy micropip.
- 콜드스타트: fastapi 설치 1.6s(실측). `ensureServer` 는 첫 `/pyapi` 요청 때만 부른다(노트북 전용 사용자는 fastapi 비용 0).

## 6. 결과 일관성 계약

- 응답 포맷은 :8400 FastAPI 와 동일 JSON(같은 dartlab 직렬화 경유). 브라우저 서빙과 :8400 서빙이 같은 스키마.
- tierUsed: 응답 헤더 `X-Dartlab-Tier: browser|local` 로 어디서 왔는지 표면화. 조용한 차이 금지.
- 노트북 execute 결과 포맷(`_normalizeResult`)은 불변. browser-as-server 는 그 경로를 안 건드린다.

## 7. 인터럽트·수명

- 데이터 API 요청은 단발 request/response. 인터럽트는 노트북 execute 의 몫(기존 Worker.terminate 재기동)이고 API 요청엔 타임아웃만.
- SSE/장수명 연결은 v1 범위 밖([02] Phase 4 이후). WebSocket 업그레이드는 SW fetch 로 불가 -> 필요 시 SSE/롱폴.
