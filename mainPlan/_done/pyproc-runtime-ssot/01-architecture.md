# 아키텍처 - dartlab 커널을 pyproc 위로

> 브라우저 런타임 아키텍트 검토(pyproc @v0.0.4 소스 + 우리 워커 직접 판독) 산출. 00 실측 위에서만 결정.
> 브리핑 대비 2개 중대 정정을 앞에 명시(D2 boot 금지, D6 체크포인트 비교체).

## 요약

pyproc 을 dartlab 소유의 얇은 **커널 seam** 뒤 2단계로 채택한다. Tier-1(지금): 워커의 이미 로드된 pyodide 를 pyproc `Runtime` 으로 감싸고 `/pyapi` 를 `AsgiServer` 로 라우팅. 전 브라우저, 격리 0, 회귀 0, 되돌릴 수 있는 PR 하나. Tier-2(나중, 게이트): `crossOriginIsolated` 뒤에서 프로세스 OS fork. 이건 pyproc worker 벤더링 + 0.27.5 에서 pyodide 스냅샷 지원 확인(미확인)이 필요. **`CheckpointGraph` 를 `ReactiveController` 로 즉시 교체하지 않는다**(분기 DAG vs 선형 타임라인, 다른 위상). FORMAT_CODE·OPFS·postMessage·패키지 매니페스트는 seam 위 dartlab 영구 소유.

## 결정

### D1 단계 (Verdict: Tier-1 먼저, Tier-2 프로세스 OS 는 crossOriginIsolated 게이트 뒤 나중. 직행 금지)

소스 확인된 격리 경계: `runtime.js`·`asgiServer.js`·`reactive.js`·`memoryCapability.js`·`terminal.js` 는 모듈 top-level 에 SAB/crossOriginIsolated 없음(reactive/memory 는 HEAPU8·스택포인터만, asgi 는 helper 문자열 + setGlobal/runAsync). `SharedArrayBuffer` 는 `pyProc.js` 에서만, JSPI 는 `syscallBridge.js` 메서드 안에서만.

- **Tier-1 = 격리 없이 도는 전부**: `Runtime`(우리 pyodide 채택), `AsgiServer`, 선택적 `ReactiveController`/`Terminal`. 전 브라우저. GitHub Pages 는 COOP/COEP 미발행이라 격리 의존 금지. 회귀 0 출하.
- **Tier-2 = `PyProc` 프로세스 OS 만**: 스냅샷-fork(SAB) + JSPI syscall. Chromium/Edge + crossOriginIsolated 전용, feature-detect, 단일워커 경로가 Firefox/Safari 영구 폴백.

직행하면 저위험 전브라우저 이득(ASGI superset)을 고위험 Chromium 전용 헤더의존 변경에 결박한다. 분리한다.

### D2 워커-부팅 (Verdict: (a)/(b)/(c) 다 아님. 공개 export `new Runtime(py)` 로 우리 pyodide 를 채택하고 pyproc `boot()` 는 절대 호출 안 함)

**소스 정정**: `boot(opts)` 는 `if (!globalThis.loadPyodide){스크립트 주입}; const py = await loadPyodide(...)`. `globalThis.loadPyodide` 프리셋(옵션 a)은 `document.createElement` 분기만 건너뛴다. `boot()` 는 여전히 `loadPyodide()` 를 불러 **두 번째 새 pyodide** 를 만든다. 우리 워커는 이미 완전 구성된 0.27.5 인터프리터(stdout/stderr hook·OPFS·marimo shim·matplotlibrc·interrupt buffer)를 소유하므로 두 번째를 띄우면 안 된다.

`Runtime` 은 top-level export 고 생성자는 `constructor(py){ this._py=py; this.memory=new MemoryCapability(py); this._micropip=null; }`. 따라서 `const rt = new Runtime(pyodide)` 로 우리 인스턴스를 감싼다. `boot()` 는 loadPyodide + optional loadPackage 뿐이라 우리에게 더 주는 게 없다. 이 경로는 pyodide 버전 불일치도 회피(pyproc `DEFAULT_INDEX` = v314.0.2 를 Tier-1 에서 절대 건드리지 않음).

**upstream 요청**: 생성자 private 필드(`_py`·`_micropip`)에 결합되지 않도록 문서화된 채택 경로 추가 (`boot({ pyodide })` 또는 static `Runtime.adopt(py)`). 저자에게 명시: `globalThis.loadPyodide` 프리셋은 두 번째 loadPyodide 호출을 못 막는다. 저자가 우리 사용자라 값싸지만, 공개 `new Runtime(py)` 로 오늘 Tier-1 출하 가능(대기 불요).

### D3 소비 (Verdict: Tier-1 = jsDelivr gh SHA/태그 핀, 서브모듈 직접 import. Tier-2 = pyproc src 벤더링)

- **Tier-1**: `import { Runtime } from ".../gh/eddmpython/pyproc@<pin>/src/runtime/runtime.js"` + `AsgiServer` from `.../src/capabilities/asgiServer.js`. 소스 확인 안전: `runtime.js` 는 memoryCapability·reactive·syscallBridge·asgiServer·terminal 만 정적 import 하고 **`pyProc.js` 는 안 함** -> CDN import 가 SAB 모듈을 안 끌어온다. **barrel `index.js` import 금지**(PyProc 재노출 -> pyProc.js fetch/eval). 핀은 **full 40자 SHA 권장**(태그 재부착이 바이트를 조용히 바꿈).
- **Tier-2**: `pyProc.js` 는 `new Worker(new URL("./worker.js", import.meta.url), {type:"module"})` 로 spawn. same-origin 필수 -> 크로스오리진 CDN 불가. `src/processOs/`(최소 pyProc.js + worker.js) 를 landing 빌드에 벤더링해 Vite 가 same-origin 워커 청크 emit. 이때는 핀된 `src/` 전체 벤더링(CDN Tier-1 + 벤더 Tier-2 혼용 대신 일관).

### D6 마이그레이션 + seam (Verdict: 둘 다 seam 뒤. ASGI 먼저 pyproc 전환(superset·폴백 플래그). CheckpointGraph 는 seam 뒤 손수 유지, ReactiveController 는 자료모델이 달라 연기)

ASGI 는 진짜 superset 교체. 우리 `_dl_dispatch` 는 `[status, bodyText]` 반환, pyproc `AsgiServer.serve(method,path,body,query)` 는 같은 scope 구성·같은 async-def 제약 + 진짜 헤더로 `{status,headers,body}` 반환. dartlab 은 `/pyapi` 접두 제거 + query 분리를 seam 위에서 유지(그건 dartlab 라우팅 지식이지 커널 지식 아님) 후 `enableAsgiServer({app:"_dl_app"})` 로 `serve()` 호출.

체크포인트는 drop-in 아님(소스 비교):
- **우리 `CheckpointGraph`**: content-addressed **분기 DAG**, 명명 문자열 id, `parentId` 체인, dedup, 노드별 stackPointer, 32bit 페이지해시. API `create(label)`/`restore(id)`/`list()`/`clear()` = 우리 postMessage 프로토콜과 정확히 일치.
- **pyproc `ReactiveController`**: **선형 인덱스 타임라인**(`base`+`deltas[]`, 정수 j), `restore(j,savedSP)`/`restoreLive(j,savedSP,{rehash})`, 외부화 스택포인터, 64bit 해시(충돌 2^-64), `saveBase`/`loadBase` OPFS. rehash-on-rollback 은 소스 주석상 2026-07-11 dartlab 에서 흡수. 하지만 명명 id·분기 없음(단일 선형 히스토리 가정).

즉시 교체하면 분기와 id 계약을 조용히 잃는다. 결론: seam 뒤에 `CheckpointGraph` 를 그대로 두고(Tier-1), `ReactiveController` 는 나중 플래그 게이트 실험(선형 시간여행 전용 또는 upstream 명명/분기 API 대기).

**seam 위 dartlab 영구 소유(비마이그레이션)**: `FORMAT_CODE`, OPFS `mountNativeFS`+`syncWorkspace`, 전체 postMessage 프로토콜, 패키지 매니페스트, marimo+matplotlib AGG shim, dartlab/fastapi lazy install. seam 은 pyproc 흡수가능 3프리미티브(raw exec·ASGI dispatch·checkpoint store)만 감싼다.

**롤백**: 단일 불린 플래그(`PYPROC_ASGI`, 기본 off) 가 arm 별 impl 선택. off = 오늘 `_dl_dispatch` 바이트 동일, 데이터 마이그레이션 0(체크포인트는 세션 인메모리). PR 전체 롤백 = seam 파일 2개 삭제 + `case 'pyapi'` 한 블록 revert.

## 목표 아키텍처

```
Page (SvelteKit, GitHub Pages)
  │  postMessage 프로토콜 (dartlab 소유: execute/pyapi/checkpoint/workspace/
  │                        package/completion/docstring/variable)
  └─ Service Worker  ->  fetch('/pyapi/*')  (dartlab 소유 browser-as-server 배선)
──────────────────────────────────────────────────────────────────────────
Web Worker (pyodideWorker.ts, dartlab 소유)
  • FORMAT_CODE 결과 렌더        │ seam 위, dartlab 소유 (비마이그레이션)
  • OPFS mount + syncWorkspace   │
  • 패키지 매니페스트 / dartlab install │
  • marimo + matplotlib shim     │
  • /pyapi 접두제거 + query 분리  │ (dartlab 라우팅, ASGI seam 위)
  ┌──────────── KERNEL SEAM (dartlab 정의 인터페이스) ────────────┐
  │  KernelRuntime -- impl: HandRolled(오늘) | Pyproc(new Runtime(py)) │
  └──────────────────────────────────────────────────────────────┘
──────────────────────────────────────────────────────────────────────────
pyproc @<pin> (pyproc 소유)
  Tier-1 (전 브라우저, 격리 없음): Runtime, AsgiServer, [ReactiveController]
  Tier-2 (Chromium/Edge + crossOriginIsolated): PyProc fork + SyscallBridge(JSPI)
──────────────────────────────────────────────────────────────────────────
Pyodide 0.27.5 (한 인스턴스, dartlab 워커가 로드, 채택하되 재부팅 안 함)
```

커널 seam 인터페이스 (TypeScript, dartlab 정의):

```ts
export interface AsgiKernel {
  install(appVar: string): Promise<void>;                 // pyproc: enableAsgiServer({app}).install()
  serve(method: string, path: string, body: string | null, query: string):
    Promise<{ status: number; headers: Record<string, string>; body: string }>;
}

export interface CheckpointKernel {                        // dartlab CheckpointInfo shape 보존
  create(label: string): CheckpointInfo;
  restore(id: string): { id: string; pagesWritten: number; bytesWritten: number };
  list(): CheckpointInfo[];
  clear(): void;
}

export interface KernelRuntime {                           // 워커 init 당 1회 구성
  run(code: string): unknown;
  runAsync(code: string): Promise<unknown>;
  setGlobal(name: string, value: unknown): void;
  readonly asgi: AsgiKernel;
  readonly checkpoints: CheckpointKernel;
}
```

impl 2개: `HandRolledRuntime`(현 inline `_dl_dispatch`/`PYAPI_SETUP` + `CheckpointGraph` 위임), `PyprocRuntime`(`new Runtime(pyodide)` + `enableAsgiServer`; 체크포인트는 Tier-1 에서 `CheckpointGraph` 위임, 나중 `ReactiveController` 어댑터 선택). 플래그로 선택.

## Tier-1 첫 PR (최소 되돌림)

ASGI arm 만. 체크포인트는 seam 인터페이스 뒤로 옮기되 손수 impl 무변경(무동작변경). 파일별:

1. **`landing/src/lib/notebook/engine/kernel/asgiSeam.ts` (신규)**: `AsgiKernel` 인터페이스; `HandRolledAsgi` = 현 `PYAPI_SETUP` + `_dl_dispatch` verbatim 이동, `install()`/`serve()` 노출; `PyprocAsgi` = 핀 CDN 에서 `Runtime`/`AsgiServer` import, `new Runtime(pyodide)`, `enableAsgiServer({app:"_dl_app"})`, `_dl_app` 만 빌드하는 preamble. 둘 다 dartlab fastapi/typing-extensions lazy-install 공유.
2. **`landing/src/lib/notebook/engine/kernel/pin.ts` (신규)**: `PYPROC_PIN`(40자 SHA) + 서브모듈 import URL 2개. 핀 단일 출처.
3. **`pyodideWorker.ts` (편집, ~15줄)**: `case 'pyapi'` 의 `ensureServer()` + inline `_dl_dispatch` 호출을 `await asgiKernel.install()` + `await asgiKernel.serve(...)` 로 교체(접두제거·query 분리는 seam 위 유지). init 에서 플래그로 `asgiKernel` 구성: `const USE_PYPROC_ASGI = false`(기본 손수). 그 외 무변경.

가산·게이트. 기본 경로 오늘과 바이트 동일. 플래그 flip 으로 pyproc 실행/롤백. revert = 신규 2파일 + `case` 편집 삭제.

## upstream 요청 (pyproc 저자 = 우리 사용자)

1. **채택-기존 런타임**: `boot({ pyodide })` 또는 `Runtime.adopt(py)` (로드된 인터프리터 감싸고 loadPyodide 생략). "globalThis.loadPyodide 프리셋은 두 번째 loadPyodide 를 못 막는다" 명시.
2. **pyodide 버전 계약**: `DEFAULT_INDEX` 가 v314.0.2 핀인데 dartlab 은 0.27.5. Runtime/AsgiServer/ReactiveController 지원 pyodide 범위 문서화(전부 안정 API: runPython·runPythonAsync·globals.set·_module.HEAPU8·_emscripten_stack_get_current/restore). `PyProc._makeSnapshot`(makeMemorySnapshot) + worker `_loadSnapshot` 지원 버전 floor 확인 -> Tier-2 버전 하한.
3. **명명/분기 체크포인트**: `ReactiveController` 에 문자열 라벨 + 비선형(부모상대) 복원 추가, 또는 "의도적 단일 선형"임을 문서화(그럼 분기는 CheckpointGraph 유지). D6 체크포인트 arm 을 풀어줌.
4. **Tier-2 same-origin 워커**: `worker.js` 벤더링 계약 확인 + per-worker `indexURL`(이미 `msg.indexURL`)을 `PyProc({ indexURL })` 1급 옵션화 -> 벤더 pyodide 핀 가능.

## 미해결 리스크 (Tier-2 관련)

- **0.27.5 스냅샷 지원(Tier-2 blocker)**: fast-fork 는 `makeMemorySnapshot()` + `_loadSnapshot` 의존. pyproc 은 v314 타깃. 0.27.5 안정 노출 미확인. 아니면 15.4배 spawn 이 우리 pyodide 에선 버전 범프 전까지 성립 안 함. spike 필요.
- **GitHub Pages COOP/COEP(Tier-2 blocker)**: 정적 Pages 헤더 불가 -> 프로세스 OS·JSPI 는 현 호스트에 SW 헤더주입 shim 없이 배포 불가. Tier-1 은 불요. 호스팅 미해결.
- **ReactiveController 의미 갭**: 선형 누적델타 복원은 단일 히스토리 가정. 노트북이 분기(복원 후 발산) 쓰나 = 제품 결정. upstream 요청 3의 필수/선택을 가름.
- **핀 churn / npm-PyPI provenance 없음**: jsDelivr gh SHA 핀은 태그 이상의 lockfile 무결성 없음 -> full SHA 핀 + 핀된 서브모듈 clean import CI 체크(pyproc 은 우리에게 테스트 미제공).
- **AsgiServer 헤더/동작 패리티**: pyproc helper 는 항상 `content-type: application/json` + 계산 content-length, 우리 `_dl_dispatch` 는 최소 헤더 + `x-dartlab-tier:browser`. superset 같으나 다른 content-type·정확한 응답헤더 의존 엔드포인트는 flip 전 패리티 패스.
