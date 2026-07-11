# 자동 반영 + COEP 롤아웃 - pyproc 도입

> 릴리즈/CI 인프라 검토(pyproc 소스 + 소비 계약 + 헤더 재실측 기반) 산출.
> 실측 정정: `files.pythonhosted.org` GET(Origin 포함)은 `Access-Control-Allow-Origin: *` 를 준다(HEAD 가 축소보고). CORP 는 여전히 없음. 이로써 COEP `credentialless` 경로면 휠 문제가 거의 사라진다.

## 요약

- pyproc 을 **단일 정본 핀**에서 소비: `landing/package.json` 의 SHA 핀 github 의존(`"pyproc": "github:eddmpython/pyproc#<sha>"`), Vite 가 번들. Tier-1(Runtime/AsgiServer)에 COEP 안전한 same-origin 코드 + Tier-2 의 `processOs/worker.js` same-origin 요구를 동시 충족 + lockfile 재현성 + float 없음.
- 자동 반영 = 라이브 float 아니라 **주간 게이트 핀 범프 Action**: 최신 semver 태그 -> 불변 SHA 해소, 2계층 PYPROC 게이트 실행, 프로세스 OS 경로 안 건드리는 patch 범프만 auto-merge, 나머지는 사람 리뷰.
- crossOriginIsolated 는 **Tier-2 라우트에만** SW(coi 패턴)로 활성. `COEP: credentialless`(Chromium 전용 = Tier-2 브라우저셋) 선호 -> pythonhosted 휠 문제 대부분 소멸. require-corp 는 SW CORP 주입 폴백.
- kill-switch 2계층: 휠설치 실패 시 즉시 Tier-1 로 self-heal 하는 클라이언트 canary + 전역 off 커밋 플래그.

## D4 자동 반영

### 정본 핀 위치 (단일 진실)

`landing/package.json` -> `dependencies.pyproc` = `github:eddmpython/pyproc#<40자 SHA>`.

왜 이것인가(대안 대비):
- **.ts 상수/CDN URL**(오늘 `PYODIDE_CDN_ESM` 처럼): Tier-1 만 됨. `PyProc` 는 `new Worker(new URL("./worker.js", import.meta.url))` + SAB 사용, 계약상 worker 는 same-origin 필수 -> 크로스오리진 CDN 은 Tier-2 배달 불가. 두 핀(CDN 상수 + package dep)은 표류해 봇을 무력화.
- **손 벤더 사본**: 리뷰면 증가, 수동 sync, lockfile 무결성 없음.
- **package.json github SHA 의존**: Vite 가 `import.meta.url` 워커를 same-origin 해시 청크로 해소(Tier-2 해결), 번들 ESM 이 same-origin(COEP 안전, CORP 불요), `package-lock.json` 이 resolved+integrity 기록(재현), vision 정책의 "SHA 핀, float 없음" 정확 일치. pyproc 이 앱 셸(`build`)로 실려 기존 SW `SHELL_ASSETS` 자동 precache -> pyproc 용 SW 변경 불요.

pyodide 통일: 같은 `indexURL`(v0.27.5, `pyodideWorker.ts` 의 `PYODIDE_CDN_ESM`)을 pyproc 에 넘겨 pyproc·dartlab 이 한 런타임 공유.

> 3에이전트 수렴: 적대적 PM(R9 CDN 장애 + veto①)과 이 인프라 검토 둘 다 커널 라이브 CDN import 기각. 아키텍트가 제안한 Tier-1 CDN import 는 이 지점에서 뒤집혀 **package.json github 의존**으로 확정. 첫 Tier-1 PR 도 bare specifier `import {Runtime, AsgiServer} from "pyproc"` (Vite 번들), CDN URL 아님.

### 워크플로 (`.github/workflows/pyprocPinBump.yml`)

```yaml
name: pyproc pin bump (gated)
on:
  schedule: [{ cron: "0 0 * * 1" }]   # 월 09:00 KST, dependabot 케이던스 정렬
  workflow_dispatch: {}                # 저자 조기 강제
permissions: { contents: write, pull-requests: write }
concurrency: { group: pyproc-pin, cancel-in-progress: false }
jobs:
  resolve:        # 최신 태그->SHA 해소 + diff 로 tier2 분류 (pyprocResolvePin.mjs)
  gate-a:         # Tier-1, node-pyodide, 항상 (pyprocSmoke.mjs)
  gate-b:         # Tier-2, 실 Chromium+crossOriginIsolated, tier2||minor+ 일 때만 (pyprocForkSmoke.mjs)
  land:           # 봇 PR 생성. patch && !tier2 && gate-a green -> auto-merge, 아니면 리뷰 라벨
```

봇이 자기 PR 브랜치를 여는 것은 dependabot 과 같은 허용 경로(master 직접 안 건드림). CLAUDE.md master-only 는 사람 브랜치 금지지 봇 PR 아님.

### `pyprocResolvePin.mjs` 개요

1. `GET /repos/eddmpython/pyproc/tags` -> `^v\d+\.\d+\.\d+$` 필터 -> **semver 정렬** 최대(API 배열순 불신). `commit.sha` 해소(태그 payload 에 있음, `v0.0.4` -> `c0e7570...`).
2. 현재 SHA = `package.json` `dependencies.pyproc` 의 `#<sha>`.
3. `newer = latestSha !== currentSha`. 두 태그로 `bump`(patch/minor/major).
4. `GET .../compare/<cur>...<new>` -> `files[].filename`. `src/processOs/`·`syscallBridge.js`·`worker.js` 매치면 `tier2=true`. 4개 output emit.

### PYPROC 게이트 (2계층)

**GATE-A `pyprocSmoke.mjs`**(node-pyodide, 결정적, 항상). 대상 = 핀 pyproc x 현재 발행된 PyPI dartlab(프로덕션 현실: 브라우저가 micropip 로 auto-sync):

```
import { boot } from "pyproc";            # 핀 SHA, 정확한 번들 바이트
const rt = await boot({ indexURL: ".../v0.27.5/full/" });
assert (await rt.run("1+1")) === 2;                        # Runtime, 전 브라우저
await rt.install("micropip");
await rt.runAsync(`import micropip; await micropip.install("dartlab")`);  # PyPI 최신 = 프로덕션
const asgi = rt.enableAsgiServer();
await rt.runAsync(`import dartlab.webapi as w; app = w.buildBrowserApi()`);
await asgi.install();
assert (await asgi.serve("GET", "/health")).status === 200;   # 실제 dartlab 라우트를 pyproc 으로 서빙
const term = rt.enableTerminal(); await term.install();
assert (await term.push("2+3")).out.includes("5");            # Terminal REPL
```

**GATE-B `pyprocForkSmoke.mjs`**(Playwright headless Chromium, `tier2||bump!=patch` 일 때만). node 는 프로세스 OS 경로를 정직히 못 덮음(`PyProc` 는 Web Worker API + SAB + JSPI, 실 crossOriginIsolated Chromium 필요, worker_threads 아님):

```
// COOP:same-origin + COEP:require-corp 세팅하는 정적 서버로 build 서빙,
// headless chromium 에서 /notebook 열기(crossOriginIsolated===true) 후:
const kernel = new PyProc(); await kernel.boot(2, true);   // SAB 스냅샷-fork
assert (await kernel.map("lambda x: x*x", [2,3,4])) == [4,9,16];   // 병렬 fork
const sb = rt.enableSyscallBridge(); const info = await sb.install();
if (info.jspi) { /* subprocess canary */ } else { assert info.jspi === false; }  // graceful
```

### 케이던스 + auto-merge 정책

- **주간**(월, dependabot 정렬) + `workflow_dispatch`. pyproc 은 동일저자·저속(태그 4개). 일간=노이즈, 월간=런타임 의존엔 느림.
- **auto-merge 는 전부 참일 때만**: bump=**patch**, compare diff 가 `src/processOs/**`·`syscallBridge.js`·`worker.js` **무접촉**, GATE-A green(이 경우 GATE-B 설계상 skip). 그 외(minor/major, tier2 경로 변경)는 `pyproc-tier2-review` 라벨 + 저자 리뷰어 + GATE-B 필수. 근거: 프로세스 OS/JSPI 경로가 crossOriginIsolated 게이트·고블스트반경.

## D5 COEP 롤아웃

crossOriginIsolated 는 **Tier-2 라우트에만**(예 `/notebook`, `/terminal`), 사이트 전역 금지(격리는 document 전역, 마케팅 페이지 require-corp 는 임베드/이미지 파손 위험).

### SW 변경 (`landing/src/service-worker.ts`)

1. 게이트 `coiWanted(url)` = `COI_ENABLED && (path 가 Tier-2 라우트로 시작)`.
2. `req.mode === 'navigate'` 분기에서 `coiWanted` 면 `fetch(req)` 후 격리 헤더 추가한 `Response(res.body, {status, statusText, headers})` 재구성:
   - `Cross-Origin-Opener-Policy: same-origin`
   - `Cross-Origin-Embedder-Policy: credentialless`(주, Chromium 전용 = Tier-2 셋) 또는 `require-corp`(폴백, 상수 하나 flip).
   coi-serviceworker 메커니즘: 브라우저가 SW 합성 navigation 헤더를 서버발신처럼 존중 -> crossOriginIsolated true. SW 가 페이지 제어해야 하므로 첫 활성 시 `clients.claim()` + 1회 reload.
3. same-origin 서브리소스(번들 JS/CSS/pyproc 워커 청크)는 암묵 COEP 허용 -> 할 일 없음. pyproc same-origin 번들(D4)이 중요한 이유.

### `files.pythonhosted.org` 완화

재실측(Origin 포함 GET): pythonhosted 휠 GET = `ACAO: *`, **CORP 없음**. jsdelivr = CORP cross-origin + ACAO *. HF = ACAO *(CORP 없음).

- **`COEP: credentialless`(주)**: 크로스오리진 no-cors 서브리소스가 CORP 없이 로드(credential-less fetch). 휠·jsdelivr·HF 전부 무개입 로드. Chromium 전용성이 Tier-2 와 완벽 일치.
- **`COEP: require-corp`(폴백)**: micropip 휠 GET 은 cors-mode 고 pythonhosted `ACAO:*` 가 cors 리소스 COEP 를 이미 충족 -> 자력 통과. 벨트+멜빵으로 SW 가 이미 `files.pythonhosted.org` 를 intercept(`isImmutableRuntimeAsset`) -> 그 분기에서 `CORP: cross-origin` 추가한 Response 재구성. SW 자체 cors fetch 는 body 읽음(ACAO * 확인, non-opaque) -> 페이지 fetch mode 무관 결정적 주입.
- **jsdelivr·HF 는 SW 작업 불요**: jsdelivr 는 이미 CORP, HF 는 ACAO * + dartlab 이 parquet 을 cors 로 fetch(CORS 가 COEP 충족) -> "HF Range 절대 intercept 안 함" 불변식 유지. 테스트 1항: HF 302 -> xet CDN **최종 hop** 이 격리하 ACAO 유지 확인(오늘 cors parquet 되므로 반드시).

### 실브라우저 테스트 매트릭스

| 브라우저 | crossOriginIsolated | dartlab 휠설치 | 셀 | Tier-2 fork/map | 기대 |
|---|---|---|---|---|---|
| Chromium/Edge(격리) | true | pass(credentialless/CORP주입) | pass | pass(SAB) | 완전 Tier-2 |
| Chromium+JSPI | true | pass | pass | +subprocess | Tier-2+JSPI |
| Firefox | false | pass | pass | 불가 -> Tier-1 | graceful |
| Safari | false | pass | pass | Tier-1 | graceful |
| Chromium, COI OFF(kill) | false | pass | pass | Tier-1 | graceful |

JS 런타임 게이팅: `crossOriginIsolated && ("Suspending" in WebAssembly) && (typeof SharedArrayBuffer !== "undefined")` feature-detect 로 Tier-2/Tier-1 선택. user-agent 추정 금지.

### kill-switch (즉시)

GitHub Pages 는 서버상태 즉시 flip 불가 -> 2계층:
- **클라이언트 canary(즉시, 사용자별)**: Tier-2 부팅 시 휠설치 canary. 실패 시 즉시 (1) SW 에 이 클라이언트 COEP 주입 중단 postMessage, (2) `localStorage.coiDisabled=1`, (3) Tier-1 로 1회 reload. 배포 없이 수초 self-heal.
- **전역 플래그(1배포, ~1-2분)**: SW 가 `activate` 에 same-origin `coi-killswitch.json`(`cache:'no-store'`) 읽음. `{disabled:true}` 면 전 신규세션 `COI_ENABLED=false`. 커밋 상수 = 빌드 기본, JSON = 런타임 오버라이드.

## 기존 게이트와 조합 (이중게이트·레이스 없음)

- **pyodideSmoke.mjs(publish.yml)**: dartlab **태그 push** 시. 대상 = 미발행 dartlab wheel(`emfs:/`) + pyodide. 릴리즈 게이트. 무변경.
- **PYPROC GATE-A(pyprocPinBump.yml)**: **schedule** 시. 대상 = 핀 pyproc x 이미 발행된 PyPI dartlab. 다른 트리거·다른 산출물 -> 이중게이트 아님. 같은 node-pyodide harness 재사용하되 형제 스크립트(pyodideSmoke 는 wheel 게이트 단일목적 유지).
- **PyPI auto-sync**: 순 런타임(노트북 열 때 `micropip.install("dartlab")` 최신). GATE-A 가 그 최신 설치(잡 시작 시 1회 해소, PR body 기록) -> 프로덕션 미러. 도중 dartlab 릴리즈여도 게이트가 N-1/N 봄(둘 다 유효, micropip 은 런타임에 늘 최신) -> lock/race 없음.
- **Dependabot**: pip-only 로 좁혀짐(`4fe3a31f7`). pyproc 은 github-URL 의존, dependabot 이 여기서 스케줄 범프 안 함 -> 핀 범프 Action 이 pyproc 핀 **유일** 소유자. 겹침·경합 없음.

## 미해결 리스크

- **node 가 Tier-2 를 못 덮음**: `PyProc` 는 Web Worker API -> GATE-A 는 fork/JSPI 검증 불가. GATE-B(Playwright Chromium+헤더) 가 프로세스 OS 경로 변경에 필수. GATE-B flaky 시 patch-only auto-merge 는 Tier-1 안전 범프는 착지시키나 tier2 회귀가 분류기 누락 시 샐 수 있음. 완화: 분류기 err-open(알려진 안전셋 밖 `src/` 변경 = tier2 취급).
- **pythonhosted 헤더 불일치**(HEAD vs GET ACAO 상이): credentialless 가 우회, require-corp 폴백의 SW CORP 주입이 hedge. pythonhosted 가 GET ACAO 도 떨구면 cors-mode micropip 이 COEP 무관하게 실패 -> require-corp 하 SW-intercept 가 기본이어야(선택 아님).
- **HF xet 최종 hop 격리하**: 302 타깃이 cors parquet COEP 용 ACAO 유지해야. 테스트 매트릭스에서 확인(오늘 되지만 서명 URL CDN 헤더 표류는 라이브 리스크).
- **crossOriginIsolated 1-reload UX**: 첫 Tier-2 방문이 격리 획득에 reload 필요 -> "격리 런타임 준비 중" 상태 표시(flash 금지).
- **pre-1.0 semver**: 0.0.x 범프는 기술적으로 전부 breaking. patch-only auto-merge 는 GATE-A 의 Tier-1 파손 포착에 의존. 동일저자·저속 동안 수용, pyproc 1.0 에 auto-merge 폭 재검.
- **번들러 워커 emit**: Tier-2 same-origin 워커가 Vite 의 `new URL("./worker.js", import.meta.url)` same-origin 청크 emit 에 의존. 빌드설정 회귀가 조용히 fork 파손 -> emit 워커 same-origin 빌드 assertion 추가.
