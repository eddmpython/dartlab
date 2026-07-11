# PRD - dartlab 커널 pyproc 이관 (단계·영향·게이트·롤백·이중평가)

> 종합 SSOT. 00 실측 + 01 아키텍처 + 02 자동반영 + 03 리스크 + 전문 에이전트 3인(브라우저 아키텍트·릴리즈 인프라·적대적 PM) 토론 수렴. 작성 2026-07-12.
> plan_deep_gate 준수: 이 문서만 보고 재조사 없이 구현 가능한 완전 설계.

## 0. 결정 + 단계

**결정**: pyproc 을 dartlab 소유 커널 seam 뒤에서 단계 채택. 라이브 커널 즉시 삭제 안 함. package.json SHA 핀(Vite 번들 same-origin) 소비. crossOriginIsolated 는 별도 승인 프로젝트로 격리.

**3에이전트 수렴점**:
- Tier-1(Runtime+AsgiServer, 격리 없음, 전 브라우저) 먼저, Tier-2(프로세스 OS fork) 별도.
- pyproc `boot()` 호출 금지 -> `new Runtime(pyodide)` 로 우리 인스턴스 채택(두 번째 pyodide 방지).
- CheckpointGraph 즉시 교체 금지(분기 DAG vs 선형 타임라인, 자료모델 상이).
- 커널 라이브 CDN import 기각 -> package.json github SHA 의존(적대 R9 + 인프라 Tier-2 same-origin 합의).
- 격리는 통합 PR 에 얹지 않음. R1(휠 붕괴)·R2(Firefox/Safari 상실) 별도 해결·실측 후에만.

| 단계 | 내용 | 게이트 | 프로덕션 접촉 |
|---|---|---|---|
| **P0 선증명** | throwaway 하네스에서 pyproc parity 실측(ASGI·체크포인트 골든 diff) | 골든 diff clean | 없음(tests/_attempts) |
| **P1 seam(플래그 off)** | 커널 seam + PyprocAsgi 추가, 기본 손수 경로 | GATE-A green + 격리없음 assertion | landing/src(커밋만, push 운영자 승인) |
| **P2 flip+soak** | 운영자 승인 후 플래그 on, 손수 경로 1릴리즈 잔존 | capability probe 폴백 확인 | 운영자 push 후 |
| **P3 자동반영** | pyprocPinBump.yml 주간 게이트 핀 범프 | GATE-A + 봇 PR | .github(봇 PR) |
| **P4 Tier-2(별도 PRD)** | 프로세스 OS fork + crossOriginIsolated | GATE-B Chromium + R1 실측 | **HARD NO-GO 현재** |

## 1. 영향 파일/함수

### P0 (tests/_attempts/pyprocKernel/, gitignored)
- `harness.mjs` (신규): node-pyodide 로 `new Runtime(py)` 채택 -> dartlab micropip 설치 -> `enableAsgiServer` 로 13 라우트 dispatch. **이미 00 §6 에서 /health·/openapi 실증됨** -> 여기선 전 라우트 골든 응답 캡처.
- `asgiParity.mjs` (신규): pyproc `AsgiServer.serve` vs 현 `_dl_dispatch` 응답 바이트 diff(status·body·헤더). R4 가드.
- `checkpointParity.mjs` (신규): `ReactiveController.restore` vs `CheckpointGraph.restore` 를 기존 체크포인트 시나리오로 diff. R5 가드. **결과가 분기 필요를 확정하면 upstream 요청 3 발동.**

### P1 (커널 seam)
- `landing/package.json` (편집): `dependencies.pyproc = "github:eddmpython/pyproc#<40자 SHA>"`. 정본 핀 단일 출처. `package-lock.json` integrity 동반.
- `landing/src/lib/notebook/engine/kernel/runtime.ts` (신규): `KernelRuntime`·`AsgiKernel`·`CheckpointKernel` 인터페이스(01 §seam). `HandRolledRuntime`(현 inline 위임) + `PyprocRuntime`(`new Runtime(pyodide)` + `enableAsgiServer({app:"_dl_app"})`). 플래그 `USE_PYPROC_ASGI=false`.
- `landing/src/lib/notebook/engine/kernel/asgiSeam.ts` (신규): `HandRolledAsgi`(현 `PYAPI_SETUP`+`_dl_dispatch` verbatim 이동) + `PyprocAsgi`(pyproc import, `_dl_app` 만 빌드). fastapi/typing-extensions lazy-install 공유.
- `landing/src/lib/notebook/engine/kernel/checkpointSeam.ts` (신규): `CheckpointKernel` 어댑터로 기존 `CheckpointGraph` 위임(무동작변경). P4 에서 ReactiveController 어댑터 선택지.
- `landing/src/lib/notebook/engine/pyodideWorker.ts` (편집 ~30줄): init 에서 플래그로 `kernel` 구성. `case 'pyapi'`: `ensureServer()`+inline dispatch -> `kernel.asgi.install()`+`kernel.asgi.serve()`(접두제거·query 분리는 seam 위 유지). `case 'createCheckpoint'/'restoreCheckpoint'/...`: `kernel.checkpoints.*` 위임. FORMAT_CODE·OPFS·패키지·shim·그 외 case 무변경.

### P3 (자동반영)
- `.github/workflows/pyprocPinBump.yml` (신규): 02 §워크플로. 주간 cron + dispatch, resolve/gate-a/gate-b/land.
- `.github/scripts/pyprocResolvePin.mjs` (신규): semver 태그->SHA + compare diff 로 tier2 분류.
- `.github/scripts/pyprocApplyPin.mjs` (신규): package.json 핀 교체 + `npm install`.
- `.github/scripts/pyprocSmoke.mjs` (신규): GATE-A(02 §게이트). node-pyodide, pyodideSmoke 와 형제(단일목적 유지).

### P4 (별도 PRD, 현재 미착수)
- `landing/src/service-worker.ts` (편집): coi 주입(COOP/COEP credentialless) Tier-2 라우트 한정 + pythonhosted CORP 폴백.
- pyproc `src/processOs/` 벤더 번들(Vite same-origin 워커 청크).
- `.github/scripts/pyprocForkSmoke.mjs`: GATE-B(Playwright Chromium 격리).

## 2. 테스트·게이트

- **P0 게이트**: asgiParity·checkpointParity 골든 diff clean(현 프로덕션 동작이 오라클). 미통과면 P1 착수 금지(적대 veto②).
- **P1 게이트(GATE-A)**: node-pyodide 로 boot+`run("1+1")`+micropip dartlab+`AsgiServer.serve("GET","/health")==200`+Terminal REPL. **격리없음 assertion**: `crossOriginIsolated===false` 에서도 휠 설치·셀 통과(적대 veto④). **lint 가드**: 노트북 경로에서 `process-os`/`worker` 진입점 import 금지.
- **P1 회귀**: 플래그 off 경로가 현 `_dl_dispatch` 와 바이트 동일(기본 무변경 증명).
- **P3 게이트**: pyprocPinBump 가 GATE-A 통과분만 봇 PR, patch+non-tier2 만 auto-merge. 기존 pyodideSmoke(태그 push, 미발행 wheel)와 트리거·산출물 달라 이중게이트 아님(02 §조합).
- **P4 게이트(GATE-B)**: Playwright headless Chromium(COOP/COEP 세팅) 에서 `PyProc.boot(N,true)` fork + `map` + JSPI subprocess canary + 폴백. node 불가 영역.

## 3. 롤백·kill-switch

- **P1/P2**: 플래그 `USE_PYPROC_ASGI` 기본 off. 손수 `_dl_dispatch`+`CheckpointGraph` **in-tree 잔존**, 플래그 on 후 최소 1릴리즈 삭제 금지(적대 veto⑤). 체크포인트는 세션 인메모리라 마이그레이션 0.
- **capability probe**: `Runtime`/`AsgiServer` init 또는 첫 휠설치 실패 시 legacy 자동 폴백 + 한 줄 진단. 조용한 죽은 커널 금지.
- **핀 롤백**: package.json 의존이라 revert 한 커밋(CDN·upstream 조율 불요, 적대 R8/R9).
- **PR 전체 롤백**: seam 신규 파일 삭제 + `case 'pyapi'` 한 블록 revert.
- **P4 격리 kill-switch(2계층)**: 클라이언트 canary(휠설치 실패 시 즉시 Tier-1 self-heal) + 전역 `coi-killswitch.json`(no-store, 1배포).

## 4. 전문 개발자 이중 평가

- **강점**: seam 이 깨끗하고 ASGI 는 superset 이 node-pyodide 로 실증됨(00 §6, /health 200). 체크포인트 비교체 판단이 자료모델 실측(분기 DAG vs 선형)에 근거 -> 조용한 correctness 회귀(R5) 사전 차단. package.json 핀 > CDN(same-origin + lockfile integrity + Tier-2 워커 동시 충족).
- **함정 회피**: pyproc `boot()` 의 두 번째 pyodide 인스턴스 트랩을 `new Runtime(py)` 채택으로 우회(소스 정정). barrel `index.js` 대신 서브모듈 import 로 SAB 모듈 미유입.
- **잔여 우려**: (a) ~~0.27.5 스냅샷 지원 미확인~~ **해소 (2026-07-12 spike 실측: `makeMemorySnapshot` + `_loadSnapshot` SUPPORTED, 20MB 스냅샷 fork 자식 실행 확인)**. P4 fork 의 pyodide 전제는 성립. (b) pre-1.0 pyproc churn -> patch-only auto-merge + GATE-A 의존. (c) node 가 Tier-2 못 덮음 -> GATE-B 필수. (d) index.d.ts 손유지 -> 타입 표류 가능, 우리측 가드가 유일 방어(R6).

## 5. PM 이중 평가 + go/no-go

- **가치 정직**: P1~P2 근시 사용자 가시 이득 ~ 0(이미 되는 커널 통합). 정당화 = 장기 SSOT(codaro/dartlab/xlpod 커널 1벌 공유, 한 곳 수정) + P4 fork 병렬(전종목 scan 등 진짜 새 능력)의 토대. 이 순서가 라이브 노트북을 보호(플래그 off·throwaway 선증명·격리 분리).
- **속도 조절**: P4(Tier-2)에 지금 투자 금지. 0.27.5 스냅샷 spike + COEP 실측(R1) 전까지 별도 PRD 로 봉인. 통합(P1~P3)과 능력(P4)은 같은 움직임 아니게 분리.
- **go/no-go**:
  - **GO**: P0(parity 선증명) -> P1(seam, 플래그 off). 지금 착수 가능. 단 P1 은 landing/src 변경이라 **커밋까지 자율, push/배포는 운영자 승인**(UI push 게이트).
  - **조건부 GO**: P2(flip) = P0 골든 diff clean + 운영자 리뷰 후. P3(자동반영) = P2 안정 후.
  - **HARD NO-GO(현재)**: P4 격리. R1(COEP 휠 붕괴) 별도 실측 + Firefox/Safari 폴백 + 운영자 승인 전까지.
- **veto 조건(프로덕션 커널 접촉 전 전부 참, 03 §veto)**: 벤더/핀 소비·라이브 CDN 0, ASGI+체크포인트 골든 패리티, 워커 안 Runtime 시연, 격리없음 증명 + import 가드, 플래그 기본 off + 손수 경로 1릴리즈 잔존.

## NEXT

1. **운영자 승인 게이트**: 이 PRD 로 P0 착수 승인 요청.
2. 승인 시 P0 하네스(tests/_attempts/pyprocKernel) parity 실측 -> P1 seam PR(플래그 off, 커밋만) -> 운영자 눈검수·push 승인 -> P2 flip -> P3 자동반영.
3. P4 는 0.27.5 스냅샷 spike 결과 + COEP 실측 후 별도 PRD 로 재기획.
