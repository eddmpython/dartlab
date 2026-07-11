# Browser As Server SSOT - 브라우저 안 dartlab FastAPI 실행 런타임

상태: PRD v0.1 (2026-07-11). 검증 기반 = `tests/_attempts/browserAsServer/` 엔드투엔드 실측 PASS.
범위: dartlab 의 실제 FastAPI 서버 코드를 브라우저 pyodide 안에서 돌려, 페이지가 표준 `fetch('/pyapi/*')`
로 dartlab API 를 부르게 한다. 백엔드(:8400) 없이. 노트북 워커와 한 커널을 공유한다.

> 형제 프로젝트 codaro 의 `codaro-anywhere/10-browser-as-server.md` 발명을 dartlab 에 접목.
> 접목 검토 3발명 중 이것만 dartlab 에 맞았고 실측 통과했다(다른 둘은 로컬 엔진 전제라 불가).

---

## 한 줄 결정

**"로컬 서버 = TCP 소켓이 아니라 ASGI 인터페이스"다. dartlab 의 FastAPI 를 pyodide 워커 안에서
돌리고, Service Worker 가 페이지 fetch 를 그 앱으로 넘긴다. 실행 SSOT 는 pyodide 커널 하나이고,
노트북(postMessage execute)과 데이터 API(fetch -> SW -> ASGI dispatch)가 그 한 커널을 공유한다.
browser-as-server 는 노트북 워커를 대체하지 않는다. 데이터 API / 터미널 백엔드 SSOT 로 얹힌다.**

```text
페이지 fetch('/pyapi/company/005930/panel')
  -> Service Worker (fetch 가로채기)
    -> 컨트롤 페이지 -> WorkerEngine.serveApi(method, path, body)
      -> pyodideWorker (기존 커널) -> FastAPI app(scope, receive, send)  (소켓 0)
      -> dartlab.Company(...).panel(...)
    -> Response(status, headers, body)
  -> 페이지가 진짜 HTTP 응답 수신 (:8400 과 같은 계약)
```

---

## 검증된 사실 (착수 근거, tests/_attempts/browserAsServer)

- **엔드투엔드 PASS**: 페이지 `fetch('/pyapi/panel/005930')` -> SW -> 브라우저 FastAPI -> dartlab -> 200, 실제 shape [36,43]. `/pyapi/scan/growth` -> 200 rows 2241.
- **HTTP 오버헤드 = 8ms**: `/pyapi/exec`(임의 코드 HTTP 왕복) 8~9ms. postMessage 대비 무시 수준. 인터페이스 교체 자체는 무비용.
- **콜드스타트 = 18.4s**: pyodide 3.7s + fastapi 1.6s + dartlab wheel 10.3s. **fastapi 는 1.6초만 추가**. dartlab 10.3s 는 노트북과 동일(이미 프리워밍 대상).
- **필수 제약**: 엔드포인트 `async def` 강제. sync `def` 는 Starlette 가 스레드풀 -> pyodide `can't start new thread`.
- **의존**: fastapi/starlette(순수 파이썬) + pydantic-core(pyodide 0.27.5 lockfile 에 wasm 휠 실재) micropip. dartlab pyproject 의 fastapi 는 `sys_platform != 'emscripten'` 제외라 브라우저 wheel 엔 없음, 별도 install.

## 무엇을 만드나

1. **pyodide 워커 안 dartlab FastAPI** - `pyodideWorker.ts` 에 'pyapi' 메시지 핸들러 추가. 워커가 fastapi+dartlab 을 로드하고 ASGI 앱을 직접 호출(scope/receive/send, httpx·소켓 0). 기존 execute 커널과 같은 인터프리터.
2. **WorkerEngine.serveApi** - `executionEngine.ts` 인터페이스에 `serveApi?(method, path, body)` 추가. WorkerEngine 이 'pyapi' 로 라우팅.
3. **landing Service Worker /pyapi 라우팅** - `service-worker.ts` 가 `/pyapi/*` fetch 를 가로채 컨트롤 페이지 -> WorkerEngine 으로 relay.
4. **dartlab 서버 async 데이터 라우터** - dartlab 의 순수 데이터 엔드포인트(panel·select·analysis·scan·credit·story)를 async 로 브라우저 번들에 노출. heavy/live/SSE 제외.

## 무엇을 잠그나 (재론 금지)

5. **노트북 워커 대체 금지.** execute·스트리밍·위젯·15 메서드는 postMessage 유지. browser-as-server 는 얹히는 데이터 API 이지 노트북 실행 경로가 아니다.
6. **heavy/live 는 브라우저 서빙 대상 아님.** gather(라이브 수집·스레드)·threading·SSE 장수명·데스크톱은 pyodide 원리적 불가. :8400 또는 로컬 티어 전속.
7. **두 커널 금지.** FastAPI 는 노트북과 별도 pyodide 를 띄우지 않는다. 한 워커 커널을 공유(콜드스타트·메모리 2배 방지).

## 문서 지도

1. [00-product-vision.md](00-product-vision.md) - 문제, 왜 dartlab 에 맞나, 성공/실패 기준, codaro 3발명 중 채택 근거.
2. [01-architecture.md](01-architecture.md) - 한 커널 두 인터페이스, 워커/SW/서버 배선, 영향 파일·심볼, async 강제·의존.
3. [02-phasing-and-wiring.md](02-phasing-and-wiring.md) - Phase 0~4, dartlab 이야기·노트북 배선 순서, 콜드스타트 완화, 게이트·롤백·이중 평가.
4. [03-progress-ledger.md](03-progress-ledger.md) - 결정 원장·세션 간 재개(NEXT).

## 한계 표기 원칙

1. 새 발명 최소화. FastAPI·SW·pyodide·ASGI 전부 기성. 새로운 건 조합(한 커널에 두 인터페이스)뿐.
2. tierUsed 표면화. 데이터가 브라우저 FastAPI 에서 왔는지 :8400 에서 왔는지 UI 가 숨기지 않는다.
3. "무료" 조건 = 정적 호스팅 + 사용자 브라우저 컴퓨트. 서버 비용 0.
4. 브라우저 상한 정직하게. 데이터 계산은 polars WASM 바닥(노트북과 동일). 서빙 자체만 런타임급.
