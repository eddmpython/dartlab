# 진행 원장 - pyproc Runtime SSOT

> 결정·근거·세션 재개(NEXT) 원장. 상세 설계는 01~04, 실측은 00.

## 2026-07-11 세션 1 (기획 착수)

### 한 일
- **실측 3종 완료** (00-verified-facts SSOT):
  1. COEP 헤더 실측(`curl -I`): jsdelivr 안전, files.pythonhosted.org CORP/CORS 없음(휠 설치 차단 위험), HF cors-only.
  2. pyproc 소스 판독: 격리 요구 기능별 매핑(Runtime/AsgiServer/Terminal 격리 불요, fork+JSPI 만 필요), 부팅 토폴로지(boot() 메인스레드 / worker.js 워커안전), 소비 정책(SHA 핀, float 금지).
  3. **Tier-1 엔드투엔드 실증**(node-pyodide, exit 0): pyproc AsgiServer HELPER 가 dartlab FastAPI 를 dispatch -> `/health` 200 `{"ok":true,"version":"0.10.9"}`, 13 라우트, `/openapi.json` 200.
- mainPlan 폴더 생성: README + 00-verified-facts.
- 앞서 정리: pyodide 0.27.2 -> 0.27.5 버전 통일(loader.js·pyodide README·블로그 08), 커밋+push(39a85e483).

### 확정된 결정
- **D-STAGE**: Tier-1(격리 불요, 전 브라우저) 먼저 -> Tier-2(Chromium fork) 점진. 근거 = 격리 요구가 기능별로 갈리고 Tier-1 이 회귀 0 으로 실증됨.
- **D-NO-DELETE**: 라이브 커널 즉시 삭제 금지. seam 뒤 폴백 강등 후 게이트 통과 시 삭제.
- **D-AUTOUPDATE-SHAPE**: 자동 반영 = float 아님(pyproc 정책). 게이트 통과 후 핀 범프.

### 열린 질문 (에이전트 토론 대기)
- 워커-부팅 해법: `globalThis.loadPyodide` 프리셋 vs pyproc 에 워커안전 boot upstream 요청 vs 메인스레드-부모 토폴로지 재구성.
- seam 인터페이스 정확한 시그니처 + 마이그레이션 순서(dispatch·checkpoint 교체 vs 폴백 병존).
- 자동업데이트 워크플로 구체(핀 위치·cadence·auto-merge 정책) + pyproc 게이트 정의.
- COEP 롤아웃 SW 변경 상세 + pythonhosted CORP 완화 + 실브라우저 테스트 매트릭스.
- 리스크 원장 + go/no-go + veto 조건 + kill-switch.

### 에이전트 토론 수렴 (3인 완료)
- **브라우저 아키텍트**: 2개 소스 정정 -> (1) `boot()` 금지, `new Runtime(py)` 로 우리 pyodide 채택(두 번째 인스턴스 방지 + 버전 불일치 회피). (2) CheckpointGraph(분기 DAG) vs ReactiveController(선형) 비교체, 체크포인트 seam 뒤 손수 유지. ASGI 만 superset 교체. seam 인터페이스·Tier-1 첫 PR·upstream 요청 4 확정.
- **릴리즈 인프라**: 정본 핀 = `landing/package.json` github SHA 의존(Vite 번들 same-origin, Tier-1+Tier-2 동시 충족). 주간 게이트 핀 범프 Action(resolve/gate-a/gate-b/land). COEP 는 Tier-2 라우트 한정 credentialless(휠 문제 소멸) + require-corp 폴백. pythonhosted GET 은 ACAO * 있음(재실측 정정).
- **적대 PM**: Tier-1 조건부 GO(벤더·핀·플래그 off·throwaway 선증명·kill-switch), 라이브 Pages 격리 HARD NO-GO(R1 휠 붕괴 실측 전). R1~R9 + veto 5조건.
- **수렴**: 커널 라이브 CDN import 기각(적대 R9 + 인프라 Tier-2) -> package.json github 의존으로 확정(아키텍트 CDN 제안 뒤집힘).

### 확정 결정 추가
- **D-CONSUME**: package.json github SHA 핀(Vite 번들), 커널 CDN import 0.
- **D-ADOPT**: `new Runtime(pyodide)` 채택, pyproc `boot()` 프로덕션 경로 금지.
- **D-CHECKPOINT**: CheckpointGraph 유지, ReactiveController 는 P4 실험(자료모델 상이).
- **D-COEP**: Tier-2 라우트 한정, credentialless 우선. 사이트 전역·라이브 노트북 격리 현재 NO-GO.

### 문서 완성 (2026-07-12)
- 00 실측·01 아키텍처·02 자동반영·03 리스크·04 PRD(5섹션)·README·06 원장 전부 작성.

## 2026-07-12 세션 2 (P0 실증 + P1 빌드, 승인 "지어")

### P0 골든 파리티 PASS (node-pyodide 실측)
- pyproc AsgiServer(asgiServer.js HELPER verbatim) vs 현 `_dl_dispatch`, 4라우트 바이트 동일:
  `/health` 200/30B, `/openapi.json` 200/6553B, `/company/005930/industry` 200/767B, 404경로 404/22B.
- 데이터 fetch 라우트(panel/finance)는 node-pyodide 가 dartlab 동기 HF fetch(`run_sync(pyfetch)`) 불가라 제외(실브라우저는 동일 `_dl_app` 경유라 파리티 따라옴). dispatch 래퍼 파리티 확정. **R4 해소.**

### P1 커널 seam 빌드 (플래그 off, 커밋 a1f13c74a + lock bae12a7c6, push 보류)
- 신규 `kernel/asgiSeam.ts`: `AsgiKernel` + `HandRolledAsgi`(현 `_dl_dispatch` verbatim) + `PyprocAsgi`(`new Runtime(py)`+`enableAsgiServer`, `pyproc/runtime` 동적 import).
- 신규 `kernel/pyprocRuntime.d.ts`: pyproc/runtime 앰비언트 타입.
- `pyodideWorker.ts`: `PYAPI_SETUP`/`ensureServer` 제거 -> seam 위임. `USE_PYPROC_ASGI=false` 기본(오늘과 바이트 동일). `globals.set` 타입 보강.
- `landing/package.json`: pyproc `git+https` SHA 핀(c0e7570).
- **검증**: 타입체크 내 코드 0에러(richMarkdown 은 기존 debt) · node 가 `pyproc/runtime` `Runtime` export 해소 · esbuild 가 동적 import 번들(22.3kb, SAB 미유입) · P0 파리티.

### 열린 항목
- **CI ssh->https**: npm 이 lock `resolved` 를 `git+ssh` 로 정규화(package.json 은 https 명시해도). CI `npm ci` 전에 `git config --global url."https://github.com/".insteadOf ssh://git@github.com/` 필요(landing build + pyprocPinBump). P1 push/P3 전제.
- **richMarkdown.ts 기존 debt**: marked `renderer.link` 타입 에러(HEAD 커밋, @[data] 계열, pyproc 무관). 별건.

### NEXT (세션 재개 지점)
1. **운영자 push 승인 대기**: P1 은 landing/src(UI 게이트)라 커밋만 완료. "푸시해"/"올려" 시 (CI ssh->https 선처리 포함) push.
2. push 후 P2: 운영자 눈검수 + `USE_PYPROC_ASGI=true` flip(실브라우저 노트북 /pyapi 동작 + capability probe 폴백 확인). 손수 경로 1릴리즈 잔존.
3. P3: `pyprocPinBump.yml` + `pyprocResolvePin/ApplyPin/Smoke.mjs` 작성(자동반영, ssh->https 포함).
4. P4(Tier-2 격리)는 0.27.5 스냅샷 spike + COEP 실측 후 별도 PRD.
