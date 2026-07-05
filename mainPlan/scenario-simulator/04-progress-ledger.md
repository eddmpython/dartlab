# 04. Progress Ledger

상태: PRD v0.3 (2026-06-13 12-에이전트 워크플로 심화 — 지수 차트 완전 명세 + 시뮬 backbone/데이터배선 코드-그라운드 재설계 + 적대검증 반영) + ★2026-06-20 9인 전문가 패널 uplift(아래 §0)
범위: 현재 확정 결정, 미작성/정정 갭, NEXT 시퀀스, 구현 전 체크리스트

---

## 0. ★2026-06-20 9인 전문가 패널 uplift — 세 축 planScore 95 도달

**목표**: 각 분야 전문가 + UI/UX 전문가 관점으로 플랜을 *시각화 직관성·분석 전문성·예측 전문성* 95점까지 개선(운영자 지시). **결과: 세 축 모두 planScore 95 도달 확정**(설계 완전성 — 04 §4 #11 systemScore[빌드]와 분리, 코드부재≠감점).

| 축 | 시작 | 최종 | 핵심 닫힘 |
|---|---|---|---|
| 시각화직관성 | 66 | **95** | 시각 인코딩 SSOT(05 §10, 기존 HonestyFooter 3단·AuditStrip 1:1 확장)·레이아웃 와이어프레임(05 §0.5, TerminalSurface:370-376 colL 교체 코드근거)·ReportDock 거처(05 §8.1=StrategyDock fill 일반화)·Bridge Waterfall 시각 문법(08 §3.4)·초보 학습성 3종(05 §11·§12: 상태 카피·온보딩 ladder·TermGloss·disclosure-level) |
| 분석전문성 | 79 | **95** | Driver Coverage Census(02 §2C, 11-driver 실측 coverage% 명시 정량)·회계품질 leaf-binding(09 §0 7~8행+03 §5 producer 매트릭스+01 §5b quality.baseline)·base margin 정규화/COGS tier(02 §3.8)·checkValuationCoherence(01 §6.3, terminal-g·value-destructive·(d)영구초과수익 moat)·PeerSelection 회귀-조정+DoF 가드(03 §6.3)·라이프사이클 dispatch(01 §5b) |
| 예측전문성 | 82 | **95** | G16 Calibration 게이트(03 §4.4: coverage[over/under 대칭]·PIT·CRPS·skill+baseline 명명+pooled-only)·mc.distribution 측정 비모수 분포(01 §5b: regime-σ·empirical-quantile·cone 검증)·forensic→fan σ 하방 비대칭 전파(02 §3.7 FQ2)·DSR/PBO admission(09 §10.3)·driver 공분산 fan(02 §3.11)·coverage drift 2채널 decay(02 §2B.2)·look-ahead 3표면 assert(02 §2B.11) |

**과정**: 진단(9인 패널: 시각/분석/예측 각 3인)→23항 우선순위 백로그(3-Wave: A 문구즉시·B 사양게이트·C write-end 의존)→구현(6 문서-소유 에이전트 병렬, 569 insertions·충돌 0)→적대 재평가(94·95·94)→잔여 설계 갭 7건 외과 보강→확정 재평가(95·95·95).

**규율**: 전 개선 **honestySafe=true**(검증 척추 강화 또는 중립)·**새 파일 0**(기존 9문서 내 절/소절/표 행 신설만)·**새 패널/슬라이더/색 0**(기존 자산·토큰 재사용 = "깎아서 강함")·**코드 정본**(에이전트가 백로그 오류 코드 대비 정정: `cfoToNi`→`cfToNi`·`EnvironmentSnapshot` macroRegime 부재·`listing()` asOf 부재). 미구현부는 전부 design/졸업 AC/write-end 라이브 후 active 한계 라벨.

**잔여(=systemScore 빌드, planScore 갭 아님)**: 95 도달은 *설계*다 — 실제 구현(렌더러 2개·gate.py·ReportDock·mc.distribution·quality.baseline 노드·recordForecast write-end)은 09 §10 빌드티켓·_attempts 졸업 게이트 경유. write-end 라이브+held-out 데모(acceptance threshold) 후 design→proven 전환.

### 0b. ★2라운드 16-분야 천장 추진 + 시그니처 현실 점검 (2026-06-20, 운영자 "억지로 넘기지 마라")

1라운드(9인) 95 확정 후 16-분야 신규 패널(접근성·모션·현지화·거시정합·신용·K-IFRS·베이지안·시계열·MLOps·tail risk·행동재무·규제관할·문서무결성·적대)이 *원본 9인 미발견* 60항 천장 백로그를 도출, **6 에이전트 병렬 적용(+327 insertions, 전부 honestySafe·declutterSafe = 새 파일/패널/색 0)**. 진짜 새 차원: 검증 척추의 **비시각 전달**(aria 0건→missing≠0이 스크린리더에 도달)·**자본시장법 관할**(US식만→한국 발간 primary)·**warnings fail-open→fail-closed**·**cpi silent-drop**·**ES tail**·**baseline planScore SSOT 봉합**.

★**그러나 "천장 98/99 도달"은 주장하지 않는다(검증 가드).** 천장 재평가 9 검증자 중 세션 한도로 **1명(접근성)만 실행** → 99 아닌 **97 + 미해결 갭 3건**(SC 1.4.11 대비 기준배경 3중 드리프트·200% reflow AC 부재·08 a11y 포인터 의존). ⟹ 2라운드는 *플랜 내용을 진짜 개선*했으나 **천장 도달은 미검증**이고, **시그니처 지위는 §8b conditional-signature(61) 그대로**다. 상세 부정적 검토·시그니처 판정 = **00 §8c**(데이터-부재 벽·commodity 규율·미빌드 검증루프 3 구조위협 / planScore↑≠시그니처↑ / 패널-uplift 중단·최소 검증척추 빌드로 재정박 권고). 교훈: PRD 점수를 시그니처 proxy로 쓰는 확신오정렬 차단.

---

> ⚠ v0.1 폐기 박제: 이전 04는 "초기 아키텍처 = story 동격 L3 `scenarioWorkbench`, 공개 verb `dartlab.scenario`(미결)"을 현재 결정으로 들고 있었다. **01 §3이 이를 코드로 기각**했다(story=순수 렌더러라 동거 불가, `scenario` 명사형은 `macro.scenarios`/`ScenarioOverlay` 충돌). 본 v0.2가 정본.

---

## 1. 현재 확정 결정 (v0.2)

1. 제품은 주가 예측기가 아니라 **조건부 손익-주가 시뮬레이터 + 재생(Play) 미래 리플레이**. scenario≠forecast.
2. **엔진 거처 = 새 L2.5 독립 묶음 `src/dartlab/simulate/`** (드라이버 DAG + 엣지 transfer 소유, leaf 계산은 L2 SSOT 호출). story 동급 L3 기각, 신규 L2 기각(L2↔L2 cross 금지). `L2_PEERS` 미소속이라 analysis+macro+quant 동시 결합 합법. → 01.
3. **공개 verb = `dartlab.simulate(...)` / `Company.simulate(...)`**, `mode=whatif|replay|walkforward`·`universe`(횡단면=scan 위임) 흡수. `scenario` 명사형 verb 기각. → 01 §3.
4. **AI = 노드 평행 `.det`/`.ai` 슬롯.** 목적=보완(약한 노드를 grounding 통과 AI로 교체→결론 개선), 경합(평행 보존+Brier 사후채점)=그 보완이 진짜인지 검증하는 안전장치. 블렌딩 금지. AI 코드=`ai/tools/lens.py`(no-graph-regression). → 01 §6.
5. **driver 수렴/확장 = DriverRegistry**(카드+6게이트 입장, pooled-panel transfer). factor-zoo 규율(다중검정·OOS·차원붕괴·민감도 가지치기·decay). → 02 §2B.
6. **중심 산출물 = Play 미래 리플레이**(기존 터미널 replay 상태기계 미래방향 대칭 확장). 미래 캔버스 개방(EOD "여백 0"은 live 모드 한정). → 05(미작성).
7. **가치평가 = simulate(mode="whatif")의 정적 단면.** 적정주가=조건부 범위+reverseDCF 닻(단일 목표가·rating 금지). 신용=solvency 뷰(같은 단면의 지급능력 렌즈). 보고서=story 렌더, 발간=`story/publisher.py`. → 08·09 §4.
8. **시뮬레이터-앵커 = 정합화 원리.** "모든 시뮬 숫자=하나의 SSOT leaf"가 DCF 5중·회귀 4중·축 이중화를 구조적으로 청산. 실행은 외과적·census 단조·byte-identical·무중단(빅뱅 금지). → 09.
9. 결손은 0 대체 금지(missing/blocked/partial). 결과는 ref+quality gate status+provenance. look-ahead 차단(t종가→t+1시가). 단일 base 금지(bear/base/bull).
10. **v0.3 심화(12-에이전트 워크플로, 코드 그라운드)** 4 정정 박제:
    - **노드 차원폭발 차단 = 3중 좌표 (driverId, scenarioId, periodKey).** rev.path = 시나리오당 1노드, 연도·분기는 `NodeValue.vector`가 흡수 → 노드 수 O(driver×branch)≈24(폭발 아님). 01 §5.
    - **데이터 추가 = exogenousAxes 1줄(수동) → 전 과정 자동(driverPrefit→admission→decay).** if 상한 = 검증된 축 수(6~8), 시리즈 수와 독립(Stock-Watson). 02 §2B.7~2B.9.
    - **치명 신규 ① models HF 배포 경로 0건** — pre-fit 적합이 `~/.dartlab/`(ephemeral)에만 저장돼 cron 켜도 소비처 영구 None. DATA_RELEASES 'models' 1줄 + `data/models/` 리다이렉트 + `_uploadModels`가 전체 배선의 load-bearing. 02 §2B.5.
    - **치명 신규 ② scanMacroBeta firm-level t-stat 수학적 부재** (연간 N=3, df=N−k≤−1). "N~13 기술"이 한 단계 더 낙관 → firmRefine은 t-stat 게이트 *계산 금지*(pooled에서만 valid), leave-last-k hitrate만. 01 §1 #7·02 §2B.1·§2B.9. **★:205 버그 수정 제안 `*=`도 틀림**(평균경로 소실) — per-year 성장계수 cumprod, 단 kill-test로 '기존이 버그'임 먼저 증명. 01 §12.

---

## 2. 작성 문서 + 상태

| 문서 | 상태 | 비고 |
|---|---|---|
| README | ✅ v0.2 | 문서지도·L2.5 정정 (06 v0.3 반영 1줄 갱신 필요) |
| 00-product-prd | ⏳ v0.1 잔재 | §6 5-pane 화면 토폴로지 → ✅ v0.4 정정 박스 적용(terminal-host 흡수, 별도 셸 0); 잔여 = §5 "Scenario Workbench" 제품명 sync |
| 01-engine-architecture | ✅ v0.3 | §5 노드 3중좌표·§6 NodeValue/실행기/gate/grounding·§12 byte-parity+:205 수식정정·§13b 격자구조·§1 #7(scanMacroBeta N=3) 심화 |
| 02-assumption-method | ✅ v0.3 | mode enum 본문 통일(replay/walkforward/whatif)·§2B.7 end-to-end 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models HF 배포 갭(치명) |
| 03-validation-ai-review | ✅ v0.3 | §9.3 발간 게이팅 반영(헤더 정본)·fatal① lint 빌드 정합(§4 #9) |
| 04-progress-ledger | ✅ v0.3 (본 문서) | — |
| 08-valuation-report | ✅ v0.4 | 가치평가 융합·발간 계약(코어 졸업 후)·fatal① lint 빌드 정합(발간표면 한정) |
| 09-architecture-consolidation | ✅ v0.3 | 부채 원장·앵커·신용 뷰·Phase 시퀀스·§10 4 fatal 빌드티켓(①✅ 빌드·배선) |
| 05-play-future-replay | ✅ v0.3 | ★중심 산출물. fan-band None구간 끊기·byte-parity 범위 명시 |
| 07-integration-roadmap | ✅ v0.3 | **cross-category 브리지로 전환**(차트 suite ⟶ 시뮬 단방향 시퀀싱·공유 DNA·미래마커 이관) |
| → 06/10/11 **분리** | ✅ 이동 | **`../_done/terminal-chart-suite/`로 git mv**(06→01 차트·11→02 레일·10→03 백테스팅). 번호 공백(00-05/07-09) 유지=cross-ref 안정. 상세 = suite README·07 브리지·§4(14) |

---

## 3. ★워크스페이스 변동 (이 세션 중 실측 — 중요)

mainPlan UI 플랫폼 리팩토링이 **이 세션 동안** 단계-4b~5-2b로 진척(git log 오늘). 핵심:
- **터미널 전체 이동**: `landing/src/lib/terminal/` → **`ui/packages/surfaces/src/terminal/`**(commit `ff9099ba0` "data/→lib/ git mv"). `landing`엔 `terminal-shell/{routeLoad,terminalShell}.ts`만 잔존.
- **결과**: PRD의 모든 `landing/.../terminal/...` UI 경로 stale. 새 SSOT = `ui/packages/surfaces/src/terminal/`(charts/PriceChart.svelte·chartState.svelte.ts 실재) + 포트 `ui/packages/contracts` + 런타임 `ui/packages/runtime`. 엔진 경로(`src/dartlab/*`)는 불변.
- **함의**: PRD가 "mainPlan 이후 착수"라며 가정한 post-refactor 토폴로지가 *조기 도래*. 05(Play)·06(지수)는 새 토폴로지로 재기반 필수. `chartState.svelte.ts` 실재 확인 → README "replay 상태기계 재사용" 옳음, 08 "부재" 정정 대상.
- ui/apps/local SvelteKit 앱 신설(단계-5), createLocalRuntime AiPort SSE 배선(단계-5-2b) — 로컬 고급 엔진 경로 진행 중.
- **★v0.3 워크플로 코드-그라운드 확정**: 정본 = `ui/packages/surfaces/src/terminal/charts/PriceChart.svelte`(klinecharts 1051줄). `ChartCtl`은 PriceChart **내부** 생성(`new ChartCtl` 1곳, setContext 0건) → CenterStack은 ctl 모름 ⟹ 06 v0.2 "ctl.subject 분기"는 컴파일 불가, 정정=CenterStack-local `$state`(06 §2.5). soft-swap은 실재하나 *회사 전환 전용*. replay 상태기계는 *과거 backward-only*(미래 sim.play 필드 신설 필요). 미래여백 0은 *무조건 적용*(05 §2 live 분기 신설 필요). PricePort 실제 메서드 = initial/older/loaded/govCandles/govRecent(PRD `indexInitial` 발명 폐기). `ui/shared/chart/PriceChart.svelte`는 별개 SVG 컴포넌트(혼동 금지).

---

## 4. NEXT — PRD 닫기 체크리스트 (v0.3 갱신)

### ✅ 완료 (v0.2→v0.3)
1. ~~05-play-future-replay.md~~ ✅ — ★중심 산출물 작성(v0.3 fan-band None구간 끊기 포함).
2. ~~06-index-chart.md~~ ✅ — v0.3 전면 대체(subject 소유권 seam·IndexPort catalog/search/series·US 부재 가드). **→ 2026-06-14 `_done/terminal-chart-suite/01-price-index-chart.md`로 분리(§4 #14).**
3. ~~07-integration-roadmap.md~~ ✅ — 시퀀스·의존성·Phase.
4. ~~02 mode enum 통일~~ ✅ — 본문 §2.3·§3.1 → `replay/walkforward/whatif` SSOT 단일.
5. ~~01 §1/§5/§6/§12/§13b 심화~~ ✅ — v0.3 워크플로(노드 3중좌표·NodeValue/실행기/gate·byte-parity·격자·N=3 #7).
6. ~~02 §2B 심화~~ ✅ — §2B.7 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models 배포 갭.
7. ~~06 OQ12(US 지수)~~ ✅ — 운영자 결정=FRED 채택, 종가 라인 subject로 06 v0.4 통합. FRED 데이터 라이브 실측(SP500/NASDAQ/다우/VIX 4종)·종가전용 지표 3분기 매트릭스·candleStyle 격리. 잔여=구현만.

### 🔨 엔진 착수 — L2.5 `simulate/` (P1 ①② 완료 후 다음, execution-ready scope 2026-06-14)
> ⚠ **이건 대형 engine-add — 신선한 집중 + dartlabGuard 선행 필수**(master-red 교훈: 아키텍처 변경 rush 금지). `.claude/skills/engine-add` 절차 동반.

✅ **개념검증 + foundation 졸업 완료(2026-06-14)** — ★layer subtlety 는 **§10 born-clean 으로 해소**(아래 "1." 의 a/b/c 고민 불필요): simulate/ 는 *소비처 0 신생, 기존 simulation.py 무접촉* → transfer 는 L2.5 에 새로 태어나고(synth L1.5 상수만 forward import) legacy `_applyMacroShock` 잔존(§4 move 는 L2→L2.5 역방향이라 *회피*, BC 위임은 성숙 후 별도). 
  - `_attempts/scenarioSimulate/` 개념검증 PASS(born-clean DAG·transfer byte-identical·buildProforma leaf·결정론).
  - **본진 `src/dartlab/simulate/` 졸업**: `sheet.py`(NodeValue/DriverNode/DriverSheet+computeInputsHash+buildOrder Kahn+evaluateSheet, lens 심볼 부재=invariant-1) + `transfer.py`(transferMacroToFundamentals/transferRevenuePath). LAYER_OF simulate:2.5 등록(indexer.py+test_import_direction.py, downward-only). 검증: dartlabGuard exit 0·22 테스트·9섹션 docstring·born-clean.
  - ✅ **deterministic core 졸업(2026-06-14, `096e84c43`)**: `registry.py`(buildSnapshot read-once + 4 노드 _fnMacroPath/_fnRevPath/_fnProforma/_fnDcf — ★dcf=proforma FCF 기반 FCFF 폴백, `calcDFV` 아님[calcDFV 는 외부 proforma 무시 → scenario-coherence 깨짐]) + `run.py`(runScenario→SimulationResult+NodeAudit). 4노드 DAG end-to-end·32 테스트·dartlabGuard exit 0·결정론.
  - ✅ **공개 verb 졸업(2026-06-14, `ac3905fd9`)**: `simulate/entry.py`(톱레벨 `dartlab.simulate(code, *, scenario, horizon, asOf)` thin wrapper, KR 전용 가드=market!='KR', 9섹션) + `Company.simulate(...)` 메서드 + `__init__.py` lazy map+`__all__`+callable-module 충돌 패치(서브패키지=verb 동명) + `rules.py` FROZEN_PROVIDER_COMPANY_SURFACE 등록. **EngineCall 자동등록**(allowlist=라이브 capability 카탈로그 from `__all__`+Company public methods, 별도 파일 0). 결정론 subset(scenario/horizon/asOf)만 — drivers/lens/mode 는 인자조차 미추가(inert stub=clutter, 후속 phase). 검증: dartlabGuard exit 0·apiContractAudit exit 0(docstring+annotation 충족, contract dir repo-wide 미존재)·test_verb 4 passed·실호출 005930 adverse<baseline.
  - **다음 phase**: lens 보조(`ai/tools/lens.py`, 비결정론 평행 보완·no-graph-regression) · drivers/mode 인자(다중 드라이버 override + whatif/replay/walkforward) · Play 미래리플레이(05) · DriverRegistry 수렴(pooled-panel transfer) · US 프리셋(KR 가드 해제 선결) · (선택)import-linter pyproject contract entry.

**1. (해소됨 — born-clean) transfer 외과 추출 (01 §4) 의 layer subtlety 기록 보존**:
- `_applyMacroShock`(`simulation.py:180-235`) → `simulate/transfer.py::transferMacroToFundamentals`(rename) 이사.
- 실측 호출/proxy: `_applyMacroShock` 호출자 = `_simMonteCarlo.py:184`·`_simScenario.py:199`(둘 다 함수내부 lazy proxy `_simMonteCarlo.py:36-38`·`_simScenario.py:35-38`) + `__init__.py:27` re-export. (`_simHistorical` proxy 는 `_extractBaseMetrics`/`_extractVolatility` 용이지 `_applyMacroShock` 아님.)
- **★발견(PRD 미기재)**: 호출자 `_simScenario`/`_simMonteCarlo` 가 **L2**(`analysis/forecast`)인데 transfer 를 simulate/(**L2.5**)로 옮기면 **L2→L2.5 역방향 import = layer 위반**(viz→providers DIP 위반과 동류, F1.7 재발). ⟹ transfer 단독 이사로는 부족 — 옵션: (a) `simulation/` 시뮬 서브시스템 전체를 simulate/ 로 이주(큰 이동) / (b) DI Protocol(transfer 를 L0 protocol+L2.5 register, L2 가 get) / (c) 01 의 "묶음이 leaf 호출" 의미를 재확인(simulate 가 _simScenario 를 *호출*하지 _simScenario 가 transfer 를 호출 안 하게 재배선). **착수 전 01 §3~§5 재정독 + 호출방향 확정 필수** — 안 하면 architecture-l0-l15 FAIL.
- 부수: proxy 4 dissolve(no_import_evasion 부채 청산), import-linter contract(`pyproject.toml`)+`test_l2_no_cross_import`(L2_PEERS)+`test_l15_entry_rule` 에 simulate L2.5 등록, byte-identical 검증.

**2. 이후**: DriverNode/DriverSheet(`simulate/sheet.py`) + 위상정렬 실행기 + gate/grounding(01 §6) → AI lens(`ai/tools/lens.py`, no-graph-regression) → Play(05). 공개 verb `dartlab.simulate(...)`(01 §3).

### ⏳ 남은 정합성 (v0.1 잔재 + lint 범위)
7. ✅ **00 v0.2 동기화(2026-06-14)** — §2 본문 "Scenario Workbench" → `simulate` 치환, §7.2 #9 비범위에 simulate=L2.5 합법성 예외 1줄 추가. §5 "Valuation Report + Credit View = simulate 발간 단면" 은 v0.2 정정 헤더가 이미 정본 우선으로 커버(본문 전면개정은 선택, 미실시). 정정 헤더 + 본문 잔재 치환으로 doc정합 닫음.
8. ✅ **03 §9.3 발간 게이팅(2026-06-14)** — 03 v0.2 정정 헤더(line 7)가 이미 "발간 모드는 코어 SimulationResult 실측 확정 후를 본진 승격 기준에 추가"로 정본 커버. 08 §11 우선순위 역전 가드 반영 완료(헤더 정본).
9. ✅ **fatal① T1 금지어 lint 신설·CI배선 완료(2026-06-14)** — `tests/audit/valuationPublishLint.py`(+test) 발간 표면(`reportType: simulation` 마크다운) 한정 스캔, `tests/run.py:140` GATES lint 체인·green no-op·6 unit PASS. leaf 3파일(priceImplied·_valuationOther·pricetarget)은 `_isSimulationReport`가 `.py` 영원히 미스캔(옛 "2/3파일" src-스캔 모델 무효 — 발간 누출은 §2.3 어댑터가 drop). 잔여=T2 발간 표면(Phase 6). 03/07/08/09 "lint 미존재" 서술 stale 정정 동반.
10. **README 1줄** — 06 v0.3 반영(완료) + 06 문서지도 갱신(완료).
11. ★**빌드티켓 천장(09 §10)** — fatal① T1 ✅·Phase 0 ✅. 잔여 천장 = fatal②(forwardTest recordForecast write·models HF)/fatal③(gate/ledger/admission/lens)/fatal④(US threading) = **SYSTEM(미빌드 코드) 천장이지 PLAN 결함 0** — 설계는 09 §10 에 파일·시그니처·테스트게이트·phase 까지 execution-ready 로 닫혀 있고, 미빌드는 *코드 부재*지 *설계 미결*이 아니다(채점규칙: 코드부재≠감점). ★**planScore SSOT = §0(세 축 planScore 95)가 정본**(2026-06-20 R12 봉합 — 직전 "planScore=100" 표기는 본 항 1곳에만 있던 SSOT 분열이라 §0 로 강등): 본 항은 그 95의 *빌드측 근거*다 — fatal①~④ = SYSTEM 천장, PLAN 결함 0(설계는 execution-ready). systemScore=빌드 진행률(현 fatal① 1/4). **한 문서 한 점수**(100 vs 95 모순 제거) — planScore 정본은 §0, 본 항은 systemScore 분리 근거. 두 축 혼동 금지.
12. ★**타사 개념 흡수 토론 반영(2026-06-14, 경쟁 6서비스)** — 12 agent 토론+적대검증으로 흡수후보 9종 판정: 5종(A3·A6·A8·A9 already + A5 honesty 위반 reject)·4종 **absorb-as-defer**(새 기능 0, 한계 라벨/defer-게이트로만). PRD 반영 완료: A1 preset 출처 라벨+미검증 warning 시나리오-레벨 전파(02 §2.3, **졸업 AC**) / A2 임의충격 UX defer(02 §2B.3, 01 §4 already-have 명기) / A4 라이브 레버 = dirty recompute+S_T 격자 선결 defer(05 §4) / A6 fan band σ provenance 실선/점선 시각 규율(01 §5b·05 §3) / A7 공개 Brier 리더보드 write-end 후 defer(03 §9.3) / A5 점확률 발간 금지 가드(02 §2.3). 시그니처 판정=**conditional-signature(합의 61, KEEP 조건부)** — 00 §경쟁 지형·시그니처 박제. 잔여 졸업 AC = A1 warning 전파 실배선(write-end dead chain 동일 선결).
13. ★**A4 라이브 레버 졸업 의존** — live 레버(드래그→즉시 재렌더)는 lens/drivers phase(`_dirtyClosure` dirty recompute 01 §6.2·§13b-1 + Sobol S_T 격자 OQ11) 의존으로 deferred. 그 전엔 landing=사전 동결 격자 lookup·격자 밖 토글="로컬 재계산 필요" 한계 라벨(05 §4).
14. ★**차트 suite 분리 완료(2026-06-14, 운영자 go)** — 현재/과거 차트 3 컴포넌트(06 지수→01 차트·11 레일→02·10 백테스팅→03)를 **`mainPlan/_done/terminal-chart-suite/`로 git mv**(이력 보존). 절단면=**시간축**(현재/과거=suite, 미래=시뮬). **단방향 의존**(suite ⟶ 시뮬 05 Play, 역참조 0 — 시뮬-앵커 사상 동형). 07 = cross-category 브리지로 전환(시퀀스·공유 DNA·미래마커 이관). 시뮬 번호 공백(00-05/07-09) 유지=cross-ref churn 0. 갱신 동반: scenario-simulator README 문서지도·07·00:상태박스·05:37/48 형제참조·suite README 신설·terminal-chart-suite H1 renumber+참조규약. **이유=셋이 시뮬 미완 게이트(write-end·admission)에 인질로 안 잡히고 독립 출시 가능**(분리의 핵심 이득). 메모리 포인터 갱신 동반(시뮬+백테스팅+이벤트레일+terminal-improvement 경계). ⚠ `project_terminal_improvement` 경계 노트("지수/이벤트레일=scenario-simulator")가 stale→terminal-chart-suite로 정정 필요.

---

## 5. Open Questions (v0.2 — v0.1 미결 close 후 잔여)

> v0.1 OQ1(verb 위치)·계층 결정은 01 §3이 close. **2026-06-14 완성도 검토(구현자 시뮬레이션)로 OQ2~13 대부분 resolve-now 결정**(아래 ✅, 코드/1차원리 근거)·OQ11=데모 명세 확정(🔬)·OQ1=거시 AR/VAR 데모/빌드 의존(천장). 잔여 진짜 미결은 데모-보정 *값*뿐(규칙·설계는 결정됨).

1. 거시 미래경로 예측(AR/VAR) — 부재 확정(01 §9). 별도 _attempts 라운드 시점(데모/빌드 의존 천장, 09 §10 잔여).
2. ✅ **결정(rule)**: pooled 풀 경계 = **IndustryGroup(sub-sector) 기본 → pooled-N<60 이면 부모 WICS-11 Sector 승격 → 여전히 <60 이면 DEFAULT_ELASTICITY+warnings**. 근거: macro-β 식별 DoF≈time-DoF T(Moulton, §2B.1)라 풀 *폭*은 β t-stat 못 높임(기업이질성 정밀도만); SECTOR_ELASTICITY 이미 sub-sector grain(35키), `_resolveSectorKey`(_valuationHelpers.py:55) 가 industryGroup.name→2층 구조 보유(새 코드 0). **데모 필수 = 경계 임계값만**(IG풀 vs 승격이 leave-last-k=4 OOS partial-R²로 갈리는 지점). 02 §2B.1/§2B.11.
3. ✅ **결정(아키텍처)**: AI lens 노출 = **fork/큰-gap 노드만**. '전 근거 나열'은 결정론 provenance/refs(run.py NodeAudit 전 노드)가 이미 충족 — AI 의견은 약한-det fork 의 DisagreementLedger 로만 표면. 노출 *수준*은 비용/환각/원칙(불변2)으로 결정(데이터 무관); 데모는 FORK_THR/grounding 임계 *값*만 보정. 01 §6.4.
4. ✅ **결정**: `universe=` 횡단면 UI = 기존 **ScreenerModal** 흡수(새 셸/라우트/둘째차트 0). 노출랭킹=ScreenerModal 리스트+노출-스코어 컬럼(scan 위임), 행클릭=기존 onPick(code)→PriceChart subject+단일사 full DAG(01 §13c). 정본=07 시퀀스 4 + 00 §6.4(옛 '06/07' 라우팅 정정 — 06 은 무관).
5. ✅ **결정(빌드 의존 순서)**: (1) ReportDock valuation 단일모드 먼저(08 §5 YAGNI) → (2) P7 졸업(extractChsFeatures 가 proformaStatement 수신, 본체 0줄, 09 §4.3 — 현 `chsFeatures.py:18` 미수신) → (3) credit mode(09 Phase 5). credit mode 를 P7 전에 켜면 actual-only dead 탭. 정본=09 §4.5.

### v0.3 신규 잔여 (워크플로 심화)

6. ✅ **결정**: driverPrefit = **주간 dataPrebuild FULL 경로**(일 cron `0 17 * * 0`)에 한 step(증분 prebuild-scan 아님). driverDecay(forwardTest persistence/G5)는 별도 분기 cron 유지. 근거: scanMacroBeta 가 **연간 컬럼만**(macroBeta.py:113)+pooled-β DoF≈연간 time-DoF라 분기 공시는 연간 design matrix 거의 불변 → 증분 재적합=같은 (XtX) 재계산 낭비+churn. dataPrebuild.yml 에 prebuild-scan+prebuild-full 이미 존재라 full 편입=새 cron 0(prefit=design-matrix 주기 vs decay=outcome-vintage 주기). 02 §2B.7.
7. ✅ **결정**: tier 는 axis 에서 **파생**(저장 안 함): `tier='core' if card.axis in {6 exogenousAxes 문자열값} else 'exploratory'`. 운영자 수동=카드별 override 플래그만(기본 빈값). 근거: `ExogenousIndicator`(exogenousAxes.py:34)에 axis 있으나 tier 필드 없음; 척추 6축=그 6 문자열값, 뉴스·customs 미등록(candidate)→core/exploratory 가 axis 와 1:1. 저장 tier=axis 동어반복+drift. ⚠ `EXOGENOUS_AXES` 명명 상수 없음 — 6 문자열리터럴 또는 파생집합(`{ind.axis for ind in indicators}`, exogenousAxes.py:461) 참조. 02 §2B.3.
8. ✅ **결정**: mc.distribution `deps=(proformaId,)` — proforma 노드의 **FCF 벡터(`NodeValue.vector`)** 에 의존(leaf 아님). mean path=proformaNv.vector(단일 SSOT), noise σ=snapshot elasticity. 벡터화 noise 만(buildProforma 재호출 0 — `_simMonteCarlo.py:203-211` cumprod=OOM 없음). **`NodeValue.frozenInputs` 확장 불필요**(mc 는 proforma mean vector+σ 소비, macro 분포 파라미터 아님 — '직접계산 vs deps' 이분법 해소). byte-parity 제외(RNG), 분포통계 ±ε 만. 01 §5b.
9. ✅ **완료(close)**: :205 cumprod 전환 완료(09 P1, `ad112b171` cumprod + `fe9e66c0a` seed isolation). kill-test `test_horizon_widens_cone` 가 옛 cone-일정 버그 증명 후 전환. §4 P1 ②·§6 체크리스트 [x] 와 중복 — open 목록서 닫음.
10. ✅ **결정**: groundingCheck(b) 수치 범위 출처 = **snapshot 실측 base metrics ± 고정 tol**(`snapshot.baseRevenue/baseMargin`, registry.py:188 실측 키)을 단일 규칙으로. 약한 det 자체분포 금지(순환). `AssumptionLedgerRow`(코드 0건) 제거. ledger-row 없는 노드: (b) 기권→fork(det-분포 폴백 아님)=abstention-over-circular. gate.py 설계 계약으로 박음(데이터 무관). 01 §6.3.
11. 🔬 **데모 명세 확정(데이터 의존, 실험 닫음)**: Sobol S_T 컷오프 — 표본=척추 6섹터×2사=12 + 토글 8~10; 추정기=Saltelli/Sobol N_base=1024(≤12,288 결정론 DAG eval, 벡터화); 타깃=dcf perShare+terminalRevenue; **판정=컷오프 재정의 'top-6 토글 누적 S_T≥0.9'**(k≤6 보장, 고정 0.05 폐기); robustness=seed×3+bootstrap CI+cross-firm Kendall τ(τ 불안정 시 글로벌 컷오프 기각, per-firm top-6 폴백). 근거: src 에 variance-Sobol 부재(sensitivityAnalysis=OAT tornado), S_T 는 입력분포×출력비선형 의존이라 a priori 결정 불가. 02 §2B.11·01 §13b.
12. **(close — 운영자 결정=FRED 채택)** ★US 지수(SP500/NASDAQ/다우/VIX) = **FRED 종가 라인 subject로 06 통합 확정**. 운영자 결정 '미국 지수는 FRED 고려' 반영. 로컬 `data/macro/fred/observations.parquet` 실측으로 4종 라이브 확정(SP500 2609행 2016~·NASDAQCOM 14440행 1971~·DJIA 2609행 2016~·VIXCLS 9508행 1990~) — '데이터 전무(grep 0건)' 정정(grep은 ui 코드 미배선이지 데이터 부재 아님). KR=OHLCV 캔들 / US=종가(o=h=l=c, v=0) degenerate candle + `candleStyle='area'`. 새 차트·포트 0(IndexRef.market 분기 + 변환 1함수). 종가전용 제약=캔들·ATR·KDJ·CCI·WR·DMI·ICHI·AO·CR·VP 불가(06 §4.2), MA/RSI/MACD/BOLL 등 close-기반만 정상. 06 §3.2~§3.6·§6. **잔여=구현만**(데이터 선결 0). 표면 선호 1건(macroSource srcCache 공유 vs 소스 독립, 06 §7 OQ2).
13. ✅ **결정(경로, 실행 후속)**: 별도 `indexCompares: IndexRef[]` 슬롯(compares 의 IndexRef 확장 *기각*). 근거: `ctl.compares` 는 `{code,name}[]`(chartState:97)라 IndexRef 재구성 불가, compares 확장은 N사 compare 경로 회귀. indexCompares=가산적·회귀 0. 실행=06-subject 후 별트랙(US 벤치마크는 forward-fill 캘린더 정렬 선행). 06 §7.

---

## 6. 구현 전 체크리스트

- [x] main memory 포인터 (project 메모리 — 본 세션 추가 예정)
- [x] 엔진 거처 L2.5 simulate 확정·근거 기록 (01)
- [x] driver 수렴/확장 메커니즘 (02 §2B)
- [x] AI 보완/경합 + no-graph-regression (01 §6)
- [x] 가치평가·신용 = simulate 뷰 (08·09 §4)
- [x] 부채 원장 + 외과 시퀀스 (09)
- [x] **MC seed kill-test 선결 (P1) — ①② 완료(2026-06-14)**
  - ✅ **① MC 시드 전역오염 격리**(commit `fe9e66c0a`): `_simMonteCarlo.py`·`pricetarget.py` 의 전역 `random.seed`/`random.gauss` → 로컬 `rng = random.Random(seed)` 인스턴스. **동일 seed→동일 Mersenne 시퀀스라 동작 무변경**, 전역 RNG 오염만 제거. ★spec 의 numpy PCG64 대신 stdlib `random.Random` 채택 — 동작 무변경·`외부 의존성 제로`(pyodide 안전) 보존·jumpable streams 는 simulate 엔진이 필요할 때 재방문. test_simulation 29 PASS.
  - ✅ **② MC 호라이즌 cone 누적**(commit `ad112b171`): `:205` 내부 루프가 `simRev`/`simMargin` 을 매년 덮어써 마지막 해 노이즈만 반영(호라이즌 무관 cone 일정 = 버그). fix = 연도별 성장계수 cumprod(`cumRevFactor*=1+revNoise`) + margin 가산 random-walk(`cumMarginNoise+=`), mean path 보존. **kill-test `test_horizon_widens_cone`**: 옛 코드 FAIL(cv h=1 0.2251 ≈ h=3 0.2228 = 버그 증명) → cumprod 후 PASS(cone 확대). 전체 30 MC PASS(정성 회귀 0). 옛 `*=` 단순수정은 평균경로 소실이라 기각. 운영자 가시 기록 = kill-test + 커밋.
- [ ] 05/06/07 작성 + 00/02/03 v0.2 동기화 (NEXT §4)
- [ ] 워크스페이스 새 토폴로지(ui/packages/surfaces) 반영 (05/06)
- [ ] 착수 = mainPlan 완료 후 (조기 진척 중 — 의존성 07에서 확정) + 운영자 go


## 2026-07-05 : 06 "현재" 축 탑재 (운영자 합의)

- 신규 문서 06-engine-readings-and-sweep.md: 전 하위 엔진 데이터를 한곳에서 모아 출처·성격별
  판독(표면 카탈로그 자동 전수 등재, 선별 0) → 전량 봉인(issueReadings, issueMacro 동형) →
  주간 채점(G16 정합 수축 성적표) → 가정 sweep(상황 가정=명명 프리셋 소비, 결합 가정=
  AssumptionLedgerRow 규율 첫 적용, 선정=강건성 median, 가정도 봉인·채점).
- 00 §8b conditional-signature 의 "검증 루프 미완"을 채우는 조각. 09 §10 fatal②(forward-test
  write 끝단)를 주간 전종목 규모로 실장.
- 토론 이력(v0.1~v0.6.1)·P0 실측·갭 원장 = ../weekly-uplift-shortlist/ (아카이브 전환).
- 원칙 확정 반영: 개별 데이터 작업대 폐기(dossier df41ee60e), 호출계약은 엔진 소유 verb 로만.
