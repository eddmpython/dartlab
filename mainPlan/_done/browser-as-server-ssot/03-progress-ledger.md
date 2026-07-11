# 03. Progress Ledger - 결정 원장·재개점

상태: **완료 (2026-07-11 배포 + 프로덕션 e2e 검증)**. Phase 0~2 구현·배포·검증 끝. Phase 3 폐기. `_done` 이관.

---

## 최종 완료 (2026-07-11): PyPI-native 피벗으로 배포

아래 "HF 공개 배포" 계획은 더 나은 방향으로 **대체됐다**. 운영자 결정: "허깅페이스로 하면 진입점이 다르니 단순화해서 본체 릴리즈에 맞추자". 그래서 별도 HF wheel 업로드 대신 **브라우저를 PyPI-native 로** 전환했다.

- **릴리즈**: dartlab **0.10.9 를 PyPI 에 발행**(webapi 포함). 첫 시도는 ci-full red 였는데 원인은 이 작업이 아니라 병렬 "거울 작업대" workstream 의 guard/census 재작업 미완(master CI red)이었다. pickRow 중첩헬퍼 `_pickRow` + guard baseline lazy-import 줄번호 동기화(381->382 등)로 census 복구 후 통과. 커밋 c0ddd6ae0.
- **스위치**: `pyodideWorker.ts` DARTLAB_WHEEL(HF URL) -> `micropip.install("dartlab")`. README·pyodide/README·loader.js 도 동일. 커밋 f58d3c3aa + 115593381. 진입점이 pip 과 통일되고 버전이 본체 릴리즈에 자동으로 맞는다(HF wheel URL·수동 포인터·3-way 드리프트 제거).
- **배포 + 프로덕션 검증**: master push -> deploy-landing success. 프로덕션 e2e: `eddmpython.github.io/dartlab/blog/what-is-dartlab` 의 `<LiveData spec="scan/growth">` 가 **전상장사 2,241행 중 20행 라이브 렌더**(browser 배지, 32.5s = 워커 부팅 + PyPI 에서 0.10.9 설치 + webapi + scan).
- **보너스**: browser-as-server(webapi)가 이 PyPI 릴리즈에 실려 함께 배포됐다. 별도 HF 업로드 게이트가 소멸.
- **발행 게이트**: `.github/scripts/pyodideSmoke.mjs` + `publish.yml` build 잡. 발행될 wheel 을 node-pyodide 로 `micropip.install` + import 검증. 실측 0.10.7 FAIL(msgspec)/0.10.9 PASS. auto-sync 를 켠 대가로 pyodide-깨는 릴리즈 차단. 커밋 55c5a9b07.
- **SW 캐시**: `isImmutableRuntimeAsset` 가 `files.pythonhosted.org` 를 cache-first 캐시(PyPI wheel 콜드스타트 회귀 없음). PyPI 는 같은 버전 재발행 없어 cache-first 정확. 옛 HF wheel(`isDartlabWheel`)은 dead code 로 잔존(무해).

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
- [x] **엔드투엔드 실측(로컬 0.10.9 wheel + landing dev)**: 블로그 story 01 `<LiveData spec="scan/growth">` -> 전상장사 2,241행 중 20행 라이브 렌더 + browser 배지(눈검수). 노트북(`/notebooks/post:what-is-dartlab`) 투영 마크다운셀 `@[data](scan/growth)` -> 20행 hydrate. typing-extensions 4.11 고정 -> fastapi 설치 막힘 버그를 e2e 로 발견, uninstall 후 재설치로 수정(pyodideWorker PYAPI_SETUP).
- [~] **HF 공개 배포(운영자 게이트, 턴키)**: **대체됨(위 "최종 완료" 참조)**. PyPI-native 로 전환해 별도 HF wheel 업로드가 불필요해졌다. dartlab 을 PyPI 에 발행하면 브라우저가 `micropip.install("dartlab")` 로 그 버전을 자동으로 받는다.

## Phase 2 (블로그·노트북 소비자, 2026-07-11 토론 수렴)

전문 에이전트 5 렌즈 토론(57 에이전트, 8 생존/9 탈락) 결과. 회의론자 정면 답: 빌드타임 스냅샷(CompanyFinancials)이 기본 우세. 라이브는 스냅샷이 원리적으로 불가능할 때만 이긴다 (①독자입력 파라미터 ②빌드셋 밖 ③scan 전유니버스 지금값). 그래서 회사글 고정 재무표=스냅샷, dartlab 이야기 횡단·파라미터=라이브.

- [x] **코어**: `landing/src/lib/pyapi/liveData.ts`(resolveEndpoint 계약검증 + fetchLive + renderLiveTable 이스케이프+tier배지 + hydrateLiveData). vitest 8건.
- [x] **노트북 어댑터**: richMarkdown `@[data]`(youtube·video·data 3형제) + MarkdownCell `$effect` hydrate. 코드셀엔 /pyapi 안 붙임(execute 경로 불가침, 직접 import).
- [x] **블로그 어댑터**: `LiveData.svelte`(CompanyFinancials 선례 동형). 첫 소비자 = story 01 `<LiveData spec="scan/growth">` (전상장사 2,241행, 빌드셋 불가). 고아 해소.
- [x] **한 번 저술, 두 표면**: `fromMarkdown.ts` 가 `<LiveData spec="X">` -> `@[data](X)` 투영 번역 + script 스캐폴드 제거. 블로그 mdsvex 컴포넌트가 노트북 richMarkdown 으로 자동 투영.
- [x] **계약 안전 3 중**: resolveEndpoint 런타임 null + liveData.test 빌드 + browserApi 404. 새 AST 게이트 불필요(토론 kill).
- [x] **tier 배지**: pyodideWorker.ts:393 이 x-dartlab-tier 주입 -> ld-tier 배지. G5 완료.

**폐기(토론 kill)**: Phase 3 노트북 사이드바 데이터 패널(코드셀=직접 import, 마크다운셀=@[data], 세 번째 방법은 덕지덕지) · DataFrameTable 재사용(읽기전용 임베드엔 renderLiveTable) · 블로그 ```data 펜스(두 번째 문법) · @[data] 전용 notebookContract AST 게이트(잉여).

## 완료 요약 (재개점 없음, _done)
- [x] **landing 배포**: master push -> deploy-landing success -> 프로덕션 라이브. UI 눈검수 = 프로덕션 e2e(story 01 라이브 표 20행).
- [x] **Phase 2 완료**: 블로그 story 01 + 노트북 @[data] + 코어 + 투영.
- [~] **Phase 3 폐기**: 노트북 사이드바 데이터 패널은 토론 kill(덕지덕지). @[data] 마크다운셀이 정답.
- [x] 가드: G1(async)·G5(tier 배지) 완료. G2·G3·G4 는 코어 유닛테스트·vitest·resolveEndpoint allowlist 로 충족. + 발행 게이트(pyodideSmoke) 추가.

## 열린 질문 (해소됨)

- ~~`browserApi.py` fastapi import 격리~~ -> 해소: `buildBrowserApi()` 안에서 fastapi lazy import. wheel(fastapi 제외) import 시점엔 안 당김. PYAPI_SETUP 이 첫 /pyapi 때 typing-extensions 올리고 fastapi 설치.
- ~~노트북/데이터 API 전역 공유 격리~~ -> 현 구현: /pyapi 는 노트북 execute 커널을 공유하되 라우트가 매번 `dartlab.Company(code)` 를 새로 만들어 셀 전역 오염과 분리. v1 충분.
