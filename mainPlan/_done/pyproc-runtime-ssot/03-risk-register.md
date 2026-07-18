# 리스크 원장 + go/no-go - pyproc 도입

> 적대적 검토(전문 에이전트, pyproc @v0.0.4 소스 직접 판독 기반) 산출. 00 실측과 함께 착수 전제.
> 블스트반경 x 확률 순.

## 판정

- **Tier-1(Runtime + AsgiServer, 격리 없음) = 조건부 GO.** 단 벤더링 + SHA 핀 + 플래그 off 기본 + throwaway 선증명 + kill-switch 전제.
- **라이브 GitHub Pages 노트북에 crossOriginIsolated(COOP/COEP) = HARD NO-GO.** R1(휠 설치 붕괴)이 별도로 해결·실측되기 전까지. Tier-2 는 별도 승인 프로젝트.
- **근시 사용자 가시 이득 ~ 0** (Tier-1 은 이미 되는 코드의 통합이지 새 기능 아님). fork 병렬(진짜 새 능력)은 위험 클러스터와 같은 동작이라 지금 태우지 않는다.

## 2026-07-12 실측 갱신 (GATE-B, 격리 Chromium)

봉인 핵심 리스크 R1·R2 가 실브라우저 실측으로 판정됐다(`.github/scripts/pyprocForkSmoke.mjs`, Playwright headless Chromium + COOP/COEP credentialless):

- **R1 (COEP 가 micropip 휠 설치를 깬다) -> 해소.** COEP **`credentialless`** 하에서 micropip 이 dartlab 휠(files.pythonhosted.org)을 정상 설치(`wheelInstall: OK`, dartlab 0.10.9 import). require-corp 가 아니라 credentialless 를 쓰면 크로스오리진 no-cors 서브리소스가 CORP 없이 로드되므로 휠이 안 막힌다. **격리 이동 기각의 근거가 사라졌다.**
- **R2 (Firefox/Safari 상실) -> feature-detect 로 격리(완화 가능).** credentialless 는 Chromium/Edge 전용이라, COI 주입을 credentialless 지원 브라우저로만 게이트하면 Firefox/Safari 는 오늘 그대로(Tier-1) 유지된다.
- **fork 실동작 확인**: `PyProc.boot(2)` 스냅샷-fork 2워커/~330ms + `map` 병렬 결과 정확(`[332833500, 2664667000]`).
- **부수 발견(pyproc 버그)**: pyproc v0.0.4 기본 indexURL 이 `v314.0.2`(부재)라 스냅샷 버전 불일치로 fork 가 깨진다. 소비자는 `PyProc({ indexURL })`·`boot({ indexURL })`로 우리 pyodide(0.27.5)를 반드시 넘겨야 한다(upstream 보고 사안).

**갱신된 판정**: P4 봉인의 make-or-break(R1)가 실측 해소돼 **P4 는 봉인 해제**. 다만 라이브 전체 노트북 페이지 COEP 는 서브리소스(web-llm·transformers·차트 등) 광범위 검증 + fork 소비자(병렬 scan 등) + kill-switch 가 남아, 라이브 flip 은 여전히 scoped 후속. GATE-B 가 이후 fork 경로를 CI 로 지킨다.

## 리스크 (R1~R9)

| # | 리스크 | 심각도/확률 | 요지·완화 |
|---|---|---|---|
| **R1** | 격리 시 COEP 가 micropip 휠 설치를 깬다 | 치명/중~고 (격리 시) | files.pythonhosted.org 가 CORP·CORS 둘 다 없음(00 §4). `COEP:require-corp` 하 dartlab+deps 휠 fetch 실패 -> 죽은 커널. pyproc 은 여기 무관, 순전히 dartlab SW 문제. 완화(credentialless·SW CORP 주입·휠 프리벤더)는 전부 Chromium 한정/추가작업. **이 리스크만으로 지금 격리 이동 기각.** |
| **R2** | 격리 시 브라우저 지원 회귀 | 치명(비-Chromium)/확실 (격리 시) | pyproc 헤더 명시 = Chromium/Edge 전용, Firefox/Safari 미지원. 지금 노트북은 전 브라우저. 격리 요구 순간 Firefox/Safari 사용자 제품 상실. **호재**: `SharedArrayBuffer` 는 pyProc.js 메서드 안에서만 할당(모듈 로드 시 아님) -> Tier-1 import 만으론 SAB 잠금 안 걸림. seam 은 실재하나 무방비(미래 `PyProc.spawn` 호출이 탭을 격리요구로 끌 수 있음). |
| **R3** | 워커-부팅 토폴로지 불일치 (실측) | 중/고 | `boot()` 는 `document.createElement` 사용 = 메인스레드 요구. 우리 노트북은 **워커 안** pyodide -> `boot()` 워커에서 사용 불가. 우회(워커-로드 pyodide 를 `new Runtime(py)` 로 감쌈)는 되지만 이는 재배선이지 드롭인 아님. "browser-as-server 흡수"해도 SW+워커 배선은 여전히 dartlab 소유. 통합량이 광고보다 작다. |
| **R4** | ASGI dispatch 가 우리 것보다 좁다 (의미 회귀) | 중 | asgiServer.js 는 얇은 dispatcher: 헤더 `content-type: application/json` 하드코딩, 전 엔드포인트 `async def` 강제, 비스트리밍 단일 body, lifespan·multipart 없음. dartlab 앱이 sync 라우트·비 JSON·스트리밍·lifespan 쓰면 조용히 회귀. **골든 응답 diff 선행 필수.** |
| **R5** | 체크포인트/리액티브 의미 표류 vs CheckpointGraph | 중, 미묘 correctness | `ReactiveController` = 페이지 해시 델타 + 선형/시간여행 복원(`restoreLive({rehash})` 탈출구). 우리 CheckpointGraph 가 분기·명명노드·OPFS 영속 그래프 의존하면 엔진 교체가 관측동작 변경. 스모크는 통과하고 실세션에서 실패하는 류. **기존 체크포인트 시나리오를 골든 테스트로.** |
| **R6** | 단일저자 bus-factor + 미발행 수기유지 계약 | 중, 구조적 | dartlab·pyproc·요청 동일인. npm/PyPI 미발행, 외부 사용자·2차 리뷰어 없음. index.d.ts "빌드 없이 손으로 유지" -> 타입이 .js 와 조용히 표류 가능. 실격은 아니나(우리가 통제) pyproc 에 독립 테스트 표면이 없음 -> **모든 회귀 가드는 dartlab 측에.** |
| **R7** | 매일 바뀌는 0.0.x 추적 결합세 | 중, 상시 | 태그 4개 + 오늘 push. SHA 핀은 옳으나 매일 움직이는 의존은 상시 범프 압력 + 매 범프가 R3/R4/R5 재유발. 1회 마이그레이션이 아니라 상시 재검증 의무. 가드 = **핀 고정·동결, 이름있는 테스트된 필요에만 범프**("새 태그 났으니" 금지). |
| **R8** | 자동업데이트발 breaking change | 낮음(규율 시)/치명(무규율 시) | SHA 핀·벤더링으로 완화. 잔여는 인적("고치려고 @main 지목"). 가드 = **파일 벤더링**(라이브 CDN import 아님) -> 업데이트가 리뷰가능 PR 이지 런타임 기습 아님. |
| **R9** | jsDelivr/CDN 장애 vs 벤더링 | 낮음/고 | 커널을 라이브 CDN import 하면 jsDelivr 장애가 노트북 다운. 완화 = **7개 소스 파일 벤더링**(순수 ESM, 빌드없음, 소형). 커널을 라이브 CDN 의존시킬 이유 없음. |

## ROI 정직

- **지금(Tier-1)**: 이미 되는 커널의 통합(유지보수 이득, capability 아님). ASGI 흡수도 R3/R4 때문에 부분 삭제. **사용자 가시 이득 ~ 0.**
- **나중(Tier-2)**: 스냅샷-fork(184ms) + N-GIL 멀티코어. 진짜 새 능력이나 crossOriginIsolated 게이트 = R1+R2+coi-hack. 가치 실재하나 헤더 못주는 호스트 위 프로덕션 위험 클러스터. **별도 승인 프로젝트로, 통합 PR 에 얹지 않는다.**

## veto 조건 (프로덕션 커널 접촉 전 전부 참이어야)

1. pyproc 소스 **레포에 벤더링** + SHA 핀. 커널 라이브 CDN import 0, float 태그 0 (R7/R8/R9).
2. ASGI 경로 골든응답 패리티(R4) + 체크포인트/복원 패리티(R5), 현 동작을 오라클로 증명.
3. 워커 안 `Runtime` 구성 엔드투엔드 시연. 메인스레드 전용 `boot()` 는 프로덕션 경로에 절대 없음(R3).
4. 프로덕션 경로 격리없음 증명: `crossOriginIsolated === false` 에서도 부팅·휠설치 되는 테스트 + 노트북 경로에서 `process-os`/`worker` 진입점 import 금지 lint 가드(R1/R2).
5. 플래그 기본 **off**. 손수 커널은 플래그 on 후 최소 1릴리즈 동안 in-tree 잔존(삭제 금지).

## kill-switch / 롤백

- 단일 런타임 플래그(`kernel: "pyproc" | "legacy"`), 기본 legacy, 재배포 없이 전환(쿼리파람/설정).
- 구 CheckpointGraph + browser-as-server 코드 **보존**, pyproc 이 플래그 뒤에서 프로덕션 soak 할 때까지 삭제 금지.
- 부팅 capability probe: `Runtime`/`AsgiServer` init 또는 첫 휠설치 실패 시 legacy 자동 폴백 + 한 줄 진단. 조용한 죽은 커널 금지.
- 벤더 핀이라 롤백 = 폴더 git revert 하나(CDN·upstream 조율 불요).

## 다른 두 렌즈 과열 가드

- **브라우저 아키텍트**: fork 병렬에 매료돼 "좋은 부분 풀려고" 격리 주장 -> R1/R2 직격. asgiServer 흡수를 깨끗한 코드 삭제로 오신(실제론 async·JSON·비스트리밍 한정). 가드 = 격리는 별도 승인 프로젝트 + 휠설치 완화 실측 + Firefox/Safari 폴백 선행. 통합 PR 에 헤더 변경 금지.
- **릴리즈 인프라**: 깨끗한 의존 원해 "jsDelivr import + 태그 핀" 또는 매일 바뀌는 0.0.x auto-bump/Dependabot -> R7/R8/R9. 우리 테스트 green 을 패리티 증명으로 오인(pyproc 독립 테스트 표면 없음, R4/R5 는 유닛 CI 가 놓침). 가드 = 벤더 소스만(라이브 CDN·auto-bump 금지), 핀 동결, 머지는 **행동 골든 diff** 게이트.
