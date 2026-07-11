# pyproc 도입 - 검증된 사실 (실측 원장)

> 이 문서는 추측이 아니라 실제 측정·소스판독·엔드투엔드 실행으로 확인된 것만 담는다.
> 설계(01)·자동업데이트(02)·리스크(03)·PRD(04)는 전부 이 사실 위에서만 결정한다.
> 측정일: 2026-07-11.

---

## 1. pyproc 정체 + 소비 정책 (소스·API 확인)

- **정체**: `github.com/eddmpython/pyproc` @ `v0.0.4` (dartlab 과 동일 저자). 자기기술 = "브라우저 파이썬 프로세스 OS", codaro/dartlab/xlpod 가 공유하는 웹 파이썬 런타임의 단일 진실(SSOT). 순수 ESM, 빌드 단계 없음.
- **배포처**: npm·PyPI 에 **없음**(PyPI `pyproc` 는 무관한 인도네시아 조달 도구). GitHub 만.
- **소비 방법**: SHA 핀 github 의존(`"pyproc": "github:eddmpython/pyproc#<sha>"`) 또는 jsDelivr gh CDN(`https://cdn.jsdelivr.net/gh/eddmpython/pyproc@v0.0.4/index.js`). 태그 `v0.0.1`~`v0.0.4` 존재(GitHub API 로 기계 판독 가능).
- **정책(vision.md)**: 기본 브랜치 float **금지**. 버전 핀 고정 소비만(재현성·안전). 따라서 "자동 반영"은 라이브 float 이 아니라 **게이트 통과 후 핀 범프**여야 한다.

## 2. pyproc API 표면 (index.d.ts + 소스 확인)

- `boot(opts) -> Runtime`: `run`/`runAsync`/`install`/`loadPackages`/`setGlobal`.
- Runtime 능력 opt-in:
  - `enableAsgiServer()` -> `AsgiServer.install()` / `serve(method, path, body, query)`. asgiServer.js 주석: **"browserAsServer 흡수, 2026-07-11"**. 엔드포인트 `async def` 강제(우리 실측과 동일).
  - `enableReactive()` -> `ReactiveController`: 완전 힙해시 체크포인트 체인 + `restore`/`timeTravel`.
  - `enableSyscallBridge()` -> `input()` / `urllib`(동기 XHR) / `subprocess`.
  - `enableTerminal()` -> `Terminal`(InteractiveConsole REPL).
- `PyProc` 클래스 = 프로세스 OS: `boot(N)` 스냅샷-fork N 워커(~184ms vs 콜드 ~2.8s = **15.4배**), `map(fn, args)` = 진짜 멀티코어(N 독립 GIL).

## 3. 격리(crossOriginIsolated) 요구 - 기능별 매핑 (소스 grep 확인)

- `SharedArrayBuffer` 는 **오직** `src/processOs/pyProc.js`(fork 스냅샷 + interrupt SAB)에서만 사용.
- `JSPI`(WebAssembly.Suspending)는 **오직** `src/capabilities/syscallBridge.js` 의 async input·subprocess 에서만(동기 input·urllib 은 비 JSPI 폴백 있음).
- `runtime.js`·`asgiServer.js`·`terminal.js`·`reactive.js`·`memoryCapability.js` 에는 SharedArrayBuffer/crossOriginIsolated 사용 **없음**(주석에만 지원 타깃 표기).
- **결론**: `Runtime` + `AsgiServer` + `Terminal` + 동기 syscall 은 **모든 브라우저에서 격리 없이** 동작. 오직 프로세스 OS fork + JSPI 기능만 Chromium/Edge + crossOriginIsolated(COOP: same-origin, COEP: require-corp) 필요.

## 4. COEP 리스크 - 크로스오리진 헤더 실측 (`curl -I`)

| 소스 | CORP | CORS(ACAO) | COEP require-corp 하 |
|---|---|---|---|
| jsdelivr (pyodide `.mjs` + pyproc) | `cross-origin` | `*` | **안전** |
| files.pythonhosted.org (PyPI 휠, micropip 설치처) | **없음** | **없음** | **차단 위험** |
| huggingface.co resolve (parquet 데이터) | 없음 | `*` | cors-mode fetch 는 통과 |

- **핵심 리스크**: COEP 를 켜면 `micropip.install` 의 휠 다운로드(files.pythonhosted.org)가 막힐 수 있다. 완화 = Service Worker 가 통과 응답에 `Cross-Origin-Resource-Policy: cross-origin` 을 주입(coi-serviceworker 방식). 우리는 이미 SW(`landing/src/service-worker.ts`)가 있다.
- GitHub Pages 는 응답 헤더를 직접 못 준다 -> crossOriginIsolated 는 SW 헤더 주입으로만 가능.

## 5. 부팅 토폴로지 - 워커 호환성 (소스 확인)

- `boot()`(단일 Runtime) + `PyProc._makeSnapshot()`(부모)은 `document.createElement("script")` + UMD `pyodide.js` 사용 -> **메인스레드 전용**.
- `src/processOs/worker.js`(fork 되는 프로세스 워커)는 `import(mjs) + loadPyodide` + `_loadSnapshot` fast-fork + interruptSab -> **워커 안전**.
- 우리 커널은 pyodide 를 **워커 안**에서 돌린다(`pyodideWorker.ts`, `import(pyodide.mjs)`). `boot()`는 `globalThis.loadPyodide` 가 이미 정의돼 있으면 document 분기를 건너뛴다.
- process-OS worker.js 는 same-origin 필수(`new Worker(new URL("./worker.js", import.meta.url))`) -> 순수 크로스오리진 CDN 불가, 빌드에 벤더링해야 함.

## 6. Tier-1 엔드투엔드 실증 (node-pyodide 실제 실행, exit 0)

스크립트: pyproc `asgiServer.js` 의 `HELPER` 를 **verbatim** 주입 -> dartlab 실제 FastAPI 앱(`dartlab.webapi.buildBrowserApi()`)을 dispatch.

```
[2] dartlab+fastapi installed 16.0s
[3] app built + pyproc HELPER injected 18.9s
[routes] count= 13
  GET /health, GET /scan/{axis}, GET /company/{code}/panel/{topic}, ... (13개)
[openapi] status 200 bodylen 6553
[route] /health -> 200 bodylen 30 head: {"ok":true,"version":"0.10.9"}
[DONE] 19.0s
```

- **증명된 것**: pyproc 의 AsgiServer dispatch 프리미티브가 우리 browser-as-server FastAPI 를 **그대로 서빙**한다. 격리 불필요(node-pyodide 는 crossOriginIsolated 아님). 즉 Tier-1 은 실재한다.

## 7. 우리 통합 표면 (pyodideWorker.ts 판독)

- **pyproc 이 흡수 가능**: pyodide boot(171-174), 손수 만든 ASGI dispatch `_dl_dispatch`(PYAPI_SETUP 100-143) -> `AsgiServer`, heap 스냅샷 `CheckpointGraph` -> `ReactiveController`+`MemoryCapability`, interrupt buffer.
- **dartlab 이 계속 소유(seam 위)**: postMessage 프로토콜(execute/pyapi/checkpoint/workspace/package/completion/docstring/variable), OPFS 워크스페이스 영속, 패키지 매니페스트, 결과 포매팅 `FORMAT_CODE`(pandas/polars/matplotlib/plotly/marimo), marimo·matplotlib shim, SW `/pyapi` 배선.
