# 05. Play — 미래 리플레이 (★중심 산출물)

상태: PRD v0.4 (2026-06-20 9인 패널 백로그 — 시각 인코딩 SSOT·레이아웃 와이어프레임·ReportDock 거처·초보 학습성·상태 카피 매트릭스 / 2026-06-20 16인 교차분야 천장 백로그 — 접근성 규약(WCAG 2.2 AA·SC 1.1.1/1.3.1/1.4.11/1.4.13/2.1.1)·모션 kinetics(fan reveal 계약·프레임 예산·스크럽 인터럽트·모션 토큰 SSOT)·한글 금융 현지화(KRW number-render SSOT·KR/EN 병기 패리티)·설명적 내러티브(first-read 위계·persistent annotation·reveal 비트) 추가)
범위: 재생버튼으로 미래가 시간순 펼쳐지는 퍼포먼스 뷰. 미래 캔버스 개방·다중분기 동시재생·if 토글 실시간·근거 인벤토리·결정론 재현·graceful degradation + **§0.5 레이아웃 와이어프레임·§1.1 Play 컨트롤·§1.2 cross-panel highlight·§6.1 Assumption Ledger 밀도표·§8.1 ReportDock 거처 SSOT·§10 시각 인코딩 SSOT·§11 상태 카피 매트릭스·§12 초보 학습성 3종**.
UI 토폴로지: **`ui/packages/surfaces/src/terminal/`**(이 세션 중 `landing/src/lib/terminal/`에서 이동, 04 §3). 포트=`ui/packages/contracts`, 런타임=`ui/packages/runtime`.

---

## 0. 결론

**Play는 시뮬레이터의 정점 산출물이다 — 보조 차트가 아니라 심오한 최강 뷰.** 재생버튼을 누르면 시간이 미래로 흐르고, 예측된 주가·사건·지표·재무가 시간순으로 펼쳐지는 *퍼포먼스* 자체가 결과물이다. 핵심 통찰: **과거 replay = "이미 존재하는 시계열을 idx까지만 보여주기" / 미래 replay = "사전 계산된 결정론 path를 t까지만 보여주기" — 메커니즘 동일.** 따라서 새 재생 엔진 0 — 기존 터미널 replay 상태기계의 미래 방향 대칭 확장 + 결정론 산출물 *드러내기*(매 프레임 재계산 아님).

두 불변(01 §0): **(1) AI 없이도 결정론 재생** — path는 순수함수 DAG가 사전계산, Play는 드러내기만. **(2) AI 보완** — 약한 노드를 grounding 통과 의견으로 채워 더 나은 path(경합=검증). Play 위 모든 픽셀이 검증 엔진(buildProforma/monteCarloForecast/forwardTest)·정전 기법(fan chart/GMA/CIB)에 1:1 대응, 지어낸 것 0.

---

## 0.5 레이아웃 와이어프레임 (실재 컴포넌트 1:1 매핑 — 발명 0)

> **★거처 그라운드(코드 실측):** TerminalSurface(`ui/packages/surfaces/src/terminal/TerminalSurface.svelte:370-379`)는 12-col 3컬럼 `colL`/`colC`/`colR`. **colL 은 이미 조건부 교체 선례 보유** — backtest 모드면 `<StrategyDock fill>`, 아니면 `<LeftRail>`(`:372-376`). colC=`<CenterStack>`(PriceChart 호스트), colR=`<RightStack>`. ChartRibbon·HonestyFooter·MacroPathRail 모두 실재. 아래 그리드는 *새 셸 0* — 이 실재 셀에 sim 산출물을 흡수하는 배치도다. 신규 셀은 `[신규]`, 기존 표면 흡수는 `[흡수]` 라벨. 시선 순서 번호 ①~⑥ = (①GO 검색→②Sim/Live 모드 토글→③Play transport→④fan band→⑤if 인셋→⑥ReportDock 근거).

**(A) live/replay baseline (현 터미널 — sim.on=false):**

```
┌─ colL (3/12) ──────┬─ colC (6/12) ─────────────────────┬─ colR (3/12) ──┐
│ LeftRail [기존]    │ CenterStack [기존]                │ RightStack     │
│  · 매크로/스크리너 │  ┌ ChartRibbon [기존] ───────────┐ │  [기존]        │
│  · ① GO 검색 입구  │  │ 기간·TF·캔들·밴드·VS·리플레이 │ │  · 공시/재무   │
│  · 공시검색(⌘⇧F)   │  └───────────────────────────────┘ │  · 우측 공시행 │
│                    │  PriceChart [기존]                │   (suite/02    │
│                    │   · 과거 캔들 (live: 미래 여백 0) │    highlight)  │
│                    │   · replay 진입 시 idx까지 절단   │                │
│                    │  HonestyFooter [기존, 도크 footer] │                │
└────────────────────┴───────────────────────────────────┴────────────────┘
```

**(B) simulate 모드 (sim.on=true — StrategyDock `fill` 선례 재사용):**

```
┌─ colL (3/12) ──────────┬─ colC (6/12) ─────────────────────────┬─ colR (3/12) ──┐
│ ReportDock(sim) [흡수] │ CenterStack [기존]                    │ RightStack     │
│  StrategyDock 일반화    │  ┌ ChartRibbon [기존+sim 분기 1개] ──┐ │  [기존]        │
│  (mode='sim', R5)       │  │ ② [Live│Sim] 세그 토글 (langSwitch│ │  · 공시/재무   │
│  · ⑥ 근거 인벤토리 탭   │  │   패턴) · ③ Play transport bar    │ │   (단면 동기)  │
│   (evidence ledger,§6)  │  │   t 스크럽·⏮·속도 400/150ms       │ │                │
│  · Assumption Ledger    │  └───────────────────────────────────┘ │                │
│   (정렬·status,§6)      │  PriceChart [기존, sim 모드]          │                │
│  · status 카피(§7)      │   · asOf 경계 수직 실선 (§2 범례)     │                │
│                         │   · ④ fan band 좌→우 reveal (§3.1)    │                │
│  ┌ if 인셋 토글 ───────────┐ (⑤ 차트 좌상단 collapsible 오버레이│                │
│  │ AssumptionLedger if 토글│  = colL 미점유, §4·05 §0.5)         │                │
│  └─────────────────────────┘                                    │                │
│                         │  HonestyFooter [기존, sim 스탬프]     │                │
└─────────────────────────┴───────────────────────────────────────┴────────────────┘
```

**최소 확정(코드 선례 근거):**
- **미래 캔버스 = colC 중앙 `PriceChart` 점유**(둘째 차트 인스턴스 0, §1·§8). sim.on 일 때만 xAxis 가 asOf+horizon 까지 패딩(§2).
- **if 토글 인셋 = 차트 좌상단 collapsible 오버레이**(차트-스코프, colL region 미점유 = colL 좌패널 규칙 회피, 05 §0.5·§4). 좌패널은 ReportDock(sim) 이 차지하므로 if 토글을 colL 에 또 두면 충돌·중복.
- **ReportDock 위치 = colL 전체 교체**(StrategyDock `fill` 선례, §1·§8 R5 확정). RightStack 대신 colL 인 이유 = backtest 모드가 *이미* colL 을 `fill` 로 교체하는 코드 선례(`TerminalSurface.svelte:372-376`)라 학습비용 0·시각 정합. (R5 가 코드 근거로 이 결정을 박는다.)

## 0.6 first-read 초점 위계 (설명적 내러티브 VIZ — 화면당 '5초 초점' 1개, 새 요소 0)

> **★규약(새 요소·새 색·새 패널 0 — 기존 요소 간 *시각 무게* 우선순위만):** §0.5 의 시선 순서 ①~⑥은 **UI 컨트롤 동선**(모드 토글→transport→band→인셋→ReportDock)이지 *데이터 스토리* 위계가 아니다. 첫 시선(first-read)에 무엇이 데이터로 가장 먼저 읽혀야 하는지를 각 핵심 화면마다 **단 1개**의 '5초 초점' SSOT 로 박는다. 초점 요소만 위치/크기 채널 우선권(§10.4), 나머지 context 는 디밍(§5 occlusion 동일 메커니즘 차용 — 새 디밍 토큰 발명 0, 불투명 35% dim 재사용).

| 핵심 화면 | 5초 초점(데이터 스토리 SSOT) | 시각 무게 우선권 | context 디밍 대상 |
|---|---|---|---|
| **Play 캔버스(§2·§3)** | P50 중심선 대비 **reverseDCF 닻 갭**(08 §2 닻 1:1) — "시장이 이미 박은 가정 vs P50" | 닻 수평선 + P50 선 위치/대비 우선, fan band 경계는 다음 위계 | 미검증 σ fan(점선 약 fade, §3.1)·격자선·범례 |
| **bridge waterfall(08 §3.4)** | **착지 바**(당기 영업이익/가치 = "결과가 어디 착지했나") | 착지 바 크기·위치 우선 | 부유 driver 바는 context(클릭/hover 시만 강조, §1.2) |
| **Assumption Ledger(§6.1)** | **헤더 status 분포 stacked bar**(§6.1 이미 존재 — "이 시나리오가 얼마나 fact 기반인가") 를 최상단 시선목표로 승격 | 헤더 stacked bar 1줄을 표 머리 시각 앵커로 | S_T 미니막대·dumbbell 은 행 단위 context |

- **초점 1개 규율**: 화면당 초점은 *정확히 1개* — 둘 이상이면 위계 붕괴(전부 강조=아무것도 강조 아님, §10.4 chartjunk·`feedback_always_check_clutter`). 초점 외 요소는 상태 인코딩(§10.1 status)을 유지하되 *시각 무게*만 낮춘다(정보 제거 아님 — 디밍은 opacity floor 로 인접 객체와 ≥3:1 유지, §10.4 SC 1.4.11 행).
- **non-VIZ 동치**: 초점은 시각 위계지 *유일 채널* 아님 — 비시각(SR) 사용자에게는 §10.1 SR 채널(aria-live·근거표)이 동일 우선순위 정보를 평문으로 전달(초점=눈, 근거표=귀, 둘 다 닻 갭/착지/status 분포를 1순위로).

---

## 1. 기존 replay 상태기계 대칭 확장 (코드 실측 선행)

**선결 실측**: `ui/packages/surfaces/src/terminal/charts/chartState.svelte.ts`의 replay 상태(`replay`/`replayStep`/`replayStepBack`/`replayRestart`·`replayMs 400|150`, project_terminal_round3_overhaul에서 정비됨)가 미래 방향 확장 가능한지 Read로 확정. 실재 확인됨(파일 새 토폴로지에 존재) → replay 상태기계와 **동형(同型)인 미래 방향 상태기계를 신설**하되, 재생 컨트롤 UI·타이머 루프·렌더 파이프는 **공유** — 별도 차트 인스턴스 0, 새 재생 엔진 0(README "replay 재사용"의 정밀 의미).

상태 확장(conservative 최소주의 + ambitious 명세 병합 — 01 §6 sim 상태):
```typescript
sim.play = { on, t, len, ms:400|150 }   // t=0 → asOf, t=len → horizon 끝
playStep()      // t++ 미래 전진, 예측 캔들·이벤트·지표·재무 펼침
playStepBack()  // t-- 미래 되감기(자동재생 정지)
playRestart()   // t=0(asOf 복귀)
playExit()      // sim.on=false, 미래 캔버스 닫고 live 차트 복원
```
Play/일시정지/속도(400/150ms)/스크럽(t 드래그)/⏮ = 기존 replay 컨트롤 재사용. `mode:"live"|"simulate"` 전환(차트 모드 토글, 둘째 차트 금지).

**불변식(상호배타):** replay(과거)·sim.play(미래)는 `mode:live|simulate` 로 상호배타 — `replay.on`·`sim.play.on` 동시 true 금지(전환 시 진입 측이 상대 `.on=false` 보장).

**불변식(스크럽 인터럽트 — user-input-wins, 모션 kinetics):** 사용자 입력(스크럽 t 드래그·`playStepBack`·`playRestart`) 발화 시 **자동재생 즉시 정지 + 진행 중 reveal fade·펄스 즉시 종료(잔류 0)** — in-flight 애니메이션이 t 와 어긋난 유령 프레임을 남기지 않는다. 스크럽 중 fan band reveal 은 t 에 *즉시 동기*(fade 없이 hard-set, §3.1 이산 점프의 단일 스텝 적용), pulse 는 suppress(§10.3). **관성 금지**: t 드래그에 momentum/spring 0 — 금융 시점은 근사값이 아니라 정확값이라 드래그 release 시 한 봉으로 정착(MOTION.md overshoot 0 원칙 §10.5 정합). 이 불변식이 §1.1 스크럽·되감기 컨트롤의 시간축 정합을 닫는다.

### 1.1 Play 컨트롤 인체공학 (R20 — ChartRibbon 세그 토글 + transport, 코드 근거)

**코드 근거(실측):** `ChartRibbon.svelte`는 이미 `seg`/`seg on` radiogroup 세그먼트 패턴(`:80-83` PERIODS/TFS/CANDLES/YMODES)과 `lang` 기반 `T(kr,en)` 토글(`:39`), `onReplay`/`subject`/`hasBand` props(`:31,34,38`), `ctl.showBand` 밴드 토글(`:87`)을 보유. 따라서 sim 모드 컨트롤은 **신규 발명이 아니라 기존 세그 패턴 1개 추가 + props 1분기**다.

- **[Live│Sim] 모드 세그 토글 1개**: `ChartRibbon` 에 `langSwitch`/`seg` 패턴 재사용한 세그먼트 라디오 1개 추가(`enterReplay`/`onReplay` 와 **별도** — replay=과거 idx 절단, sim=미래 캔버스 개방, §1 상호배타 불변과 1:1). `subject:'index'` 처럼 새 분기 추가가 아닌 *모드* 축이라 기존 `subject` 와 직교.
  - **★세그 토글 radiogroup 정상화(코드 선례 결함 수정 후 재사용 — SC 1.3.1/4.1.2):** ChartRibbon `seg` 패턴은 `role=radiogroup` 래퍼에 자식이 `<button>` 일 뿐 **자식에 `role=radio`·`aria-checked` 가 없다**(코드 실측 — SR 에 "깨진 그룹"으로 읽힘). 새 [Live│Sim] 세그를 그대로 복제하면 결함이 전파되므로, 신규 세그는 **`role=radio`+`aria-checked={selected}`+그룹 `aria-label='재생 모드'`** 로 정상화한 뒤 재사용한다(기존 ChartRibbon seg 도 같은 정상화를 권장 — 코드 선례 결함을 복제 금지). Live/Sim 모드 전환은 **색(amber)뿐 아니라** `aria-current`/`aria-label='시뮬레이션 모드 — 가정 구간'` 으로 입력수단 무관 announce(§10.1 SR 채널, 색 단독 의존 금지).
- **Play transport bar**: t 스크럽 = 차트 폭 타임라인(좌=asOf 마커 t=0, 우=horizon 끝 마커 t=len, §2 범례와 동일 경계). ⏮(playRestart)·일시정지·속도(400/150ms = chartState `replayMs 400|150` 재사용, `chartState.svelte.ts:110`). 스크럽 = `sim.play.t` 드래그(playStep/playStepBack 재사용, §1).
- **모드 색 구분(시각 가드)**: `simulate` 일 때 transport·세그 active 를 **amber(#fb923c)** — 과거 replay 는 중립 톤. amber = HonestyFooter Tier3 active 경고색(`HonestyFooter.svelte:110,121`)·"미검증·가정 구간" 의미색 재사용(§10 status 표 hypothesis/active 행과 정합). 무지개 금지.
- **스크럽 중 fan band reveal 좌→우**: t 가 0→len 전진하며 fan band 가 asOf 경계부터 오른쪽으로 채워짐(§3.1 fan reveal). 되감기(playStepBack)는 reveal 역방향.
- **★prefers-reduced-motion 대체(접근성 — 새 토큰 0, `@media` 1블록 규약화):** Play 자동재생(400/150ms)·fan reveal(§3.1)·200ms 펄스(§10.3)·코치마크 슬라이드인(§12.1)이 전부 motion 인데 현 터미널 charts 는 `prefers-reduced-motion` 대체가 **0건(코드 실측)**. 규약 1줄로 닫는다 — `prefers-reduced-motion: reduce` 면 **① fan reveal·펄스·슬라이드인은 애니메이션 없이 즉시 최종 상태 점프**(이산 점프라 최종 봉만 hard-set, §3.1 메커니즘과 동형 — RAF 제거 불필요) **② Play 자동재생은 기본 일시정지 + 수동 스텝(playStep) 우선**(자동 setInterval 대신 사용자 명시 클릭). 200ms 펄스(§10.3)는 이미 1회·반복 금지라 reduce 시 *생략*만(대체 모션 불필요).

**★ChartRibbon 분기 최소성 검증(코드 근거 서술 — 졸업 AC):** "props 1개 추가로 끝나는가"를 졸업 데모에서 코드로 확인한다. 현 props(`onReplay`·`subject`·`hasBand`·`lang`·`ctl`)에 **sim 분기 1개**(`mode:'live'|'sim'` + `onModeToggle`)를 더하는 선에서 닫히는지 — 닫히지 않고 ChartRibbon 내부에 sim 전용 상태기계·둘째 차트 인스턴스가 번지면 §8 "새 차트 인스턴스 0" 위반이므로 그 경계를 코드로 박는다(잠정값: 데모서 props delta 측정·재보정).

### 1.2 cross-panel 하이라이트 버스 (R20 — 단일 highlightId, 인과 단정 금지)

운영자 "과거 근거 + 미래 예측 근거 나열·연결"(§6)의 *연결* 채널. **단일 `highlightId` bus**는 nodeId 3중 좌표(`driverId@scenarioId#periodKey`, 01 §5·§6.1 `f"{driverId}@{scenarioId}#{periodKey}"`)를 재사용한다. 현재 공시 이벤트 레일의 점 클릭, 스크롤, focus pulse 동기 패턴과 같은 문법으로 sim 3면(DriverGraph 엣지·fan band 선·ReportDock 행)을 연결한다.

**양방향 매핑(점등 = 연결 표시지 인과 화살표 아님):**

| 발화 면 | highlightId 키 | 점등 대상(양방향) |
|---|---|---|
| DriverGraph 엣지 클릭 | `driverId@scenarioId#all` | fan band 해당 분기 path 굵기↑ + ReportDock evidence ledger 행 |
| fan band 선 hover | 동 nodeId(slice periodKey) | DriverGraph 상류 driver 엣지 + ReportDock 근거 행 |
| ReportDock evidence 행 클릭 | 행의 nodeId | DriverGraph 엣지 + fan band 구간 |

- **인코딩 = §10 cross-highlight 행 SSOT**(선택=시안 외곽+굵기 / 연관=시안 디밍 / 비연관=불투명35% dim / 펄스 1회 200ms). 색은 시안 #22d3ee 1곳만(focus).
- **★nodeId 키 정합 1회 검증 = 졸업 AC**: 세 면이 같은 `driverId@scenarioId#periodKey` 문자열을 쓰는지 데모서 1회 cross-check(키 drift 시 점등이 엉뚱한 행을 가리킴). 키 SSOT = 01 §6.1 `DriverNode.nodeId`.
- **인과 단정 가드**: 점등은 "이 driver 와 이 band/행이 *같은 노드*" 라는 *연결* 표시일 뿐, "driver→가격 상승" 같은 화살표·호재/악재 단정 아님(03 look-ahead·인과 혼합 금지, 00 §7 인과 시간순 가드). 부호 표시는 §10 부호색 규율(중립 톤)을 따른다.

---

## 2. 미래 캔버스 개방 (운영자 명시: live는 여백 0, sim은 연다)

"우측 미래 여백 0" 불변식은 **`mode:"live"` 한정**으로 명시 변경. `sim.on`일 때만 klinecharts xAxis를 `asOf + horizon`까지 패딩. 미래 봉 = candle 아닌 **fan band polyline**(`nextTradingDateOnOrAfter` 트레이딩데이 snapping 재사용 — suite/02 이벤트레일과 공유). Play → t가 0→len 전진하며 미래 path가 왼쪽→오른쪽 채워짐.

**★future-band 렌더 계약(plan 갭 — '재생 파이프 공유'의 정확한 경계):** 기존 `valBand`(PriceChart.svelte:523-534)는 `createOverlay('priceLine')` 수평 3선(시간불변)이라 미래 fan band(다점 시변)에 *재사용 불가* — 새 multi-point figure 필요. replay 는 `fullSeries().slice(0,idx)`(:279-307)로 *기존* 시리즈를 자르지만 미래는 자를 소스가 없다 → **컨트롤/타이머만 공유, data·band 렌더는 신규**(klinecharts `applyNewData` 미래-timestamp 행 또는 별도 overlay 레이어 + 미래 `replayCutT` + None-구간 끊기). §1 '동형 신설·엔진 공유' 경계의 렌더 측 정밀화.

**미래 구간 시각 구분(시각 가드, 03 §10·08 §7):** 미래 봉 점선·반투명, 배경 톤 구분, "가정 구간" 워터마크, 상시 "가정 하의 가상 경로 · 투자권유 아님 · [conf:30]". fan chart 단일선 거부, 단일 path 강조 금지(항상 밴드/다중분기).

### 2.1 미래 캔버스 축·범례 (VIZ — asOf 경계·fan 범례·y축)

미래 캔버스는 "어디부터 가정인가·밴드가 무엇인가"를 축과 범례로 못박는다(점추정 오독 차단):

- **asOf 경계 = 수직 실선 + 라벨**: live 캔들과 sim fan 의 경계에 `asOf` 수직 실선(`--dl-line-strong #2a3142` 보다 진한 의미선) + "asOf YYYY-MM-DD · 여기부터 가정 구간" 라벨. 좌=실현(fact), 우=가정(hypothesis) — §10 status 채널 전환점. Play t=0 마커가 이 선 위.
- **fan 범례(점추정 아님 캡션 상존)**: 'P50 중심 · P25–P75 / P5–P95 백분위 밴드' 범례 + 하단 캡션 **"백분위 밴드 (점추정 아님)"** 상시. 단일선 강조 금지(§2 fan chart 단일선 거부 재확인). σ provenance 가 미검증(`elasticity_prior_unvalidated`)이면 점선·회색 근사 fan(§3.1 σ provenance 규율·§10 estimate/hypothesis 채널). **fan 캡션·범례 카피 = `T(kr,en)` 결정론 슬롯**(§11 KR/EN 병기 패리티·HonestyFooter `T(kr,en)` 패턴, AI 번역 0 — kr "백분위 밴드 (점추정 아님)" / en "Percentile band (not a point estimate)" 쌍 fill-in). `lang===en` 일 때만 en 슬롯 노출(§10.4 라벨 number-render SSOT).
- **y축 단위·기준 수평선**: y축 단위(원/주, 또는 지수 pt) 명시 + asOf 종가 수평 기준선(`--dl-line`, dim) 1개. y축 "0 시작" 강제 아님(가격 path 는 비율 변화가 본질) — 단 기준선이 닻 역할. 기준선 외 격자선 최소(chartjunk 금지, §10 채널 예산).
- **★essential 그래픽 외곽선 ≥3:1(SC 1.4.11 — 새 색 0):** asOf 경계선·fan 경계선·해치 테두리 같은 *essential* 그래픽은 fill 대비가 1.4:1 이어도 **테두리/외곽선을 ≥3:1 토큰**으로(신규 색 발명 0 — 기존 `--dl-ink #c8cfdb`(배경 `#0a0e15` 대비 ~6:1 계열) 외곽 재사용). 비연관 35% dim(§10.3) 후에도 인접 객체와 ≥3:1 유지를 opacity floor 로 보장(§10.4 SC 1.4.11 행이 SSOT). 대비 기준점 배경 토큰 = 실코드 `--dl-bg-base #0a0e15`/`--dl-bg-raised #0e141f`(§10.4 — README 의 `#050811` 은 정정 대상, 대비 계산 SSOT 불일치 회피).

---

## 3. 펼쳐지는 5갈래 (시간순 동기, 전부 결정론)

**★reveal 내러티브 비트(정상상태 — 설명적 내러티브 VIZ, 새 메커니즘 0):** Play reveal 이 *메커니즘 시간*(t=0→len)으로만 규율되면 매 재생이 '시간 흐름'이지 '이야기 전개'가 아니다. transport t 진행을 **분기/마일스톤 노드**에서 의미 비트로 끊고, 통과 시 §3.6 persistent annotation 을 활성화한다 — 비트 어휘 = **닻 고정(asOf·reverseDCF 닻 등장) → 긴장(fan band 벌어짐) → 분기 발산(branch 노드 통과) → so-what 착지(horizon 끝 P50 vs 닻 갭)**. 이 비트 정의는 §12.1 온보딩 ladder(L0 닻→L1 fan→L2 토글→L3 3분기)의 **정상상태 SSOT 재사용**(1회용 온보딩과 *같은 비트 어휘*, 중복 정의 금지 — 온보딩 = 비트의 안내된 첫 통과, 정상 재생 = 같은 비트의 자유 통과). 비트 사이는 transport 가 그냥 흐르고(메커니즘 시간), 비트 노드에서만 annotation 이 의미를 얹는다 — 산문 환각 0(§3.6 결정론 슬롯).

1. **예측 주가**: `monteCarloForecast` P50 중심선 + P5/25/75/95 fan chart(미래로 갈수록 벌어짐). seed=로컬 `random.Random(seed)`(09 P1, **stdlib·pyodide 안전 — numpy PCG64 아님**; MC는 분포통계 패리티 ±ε — byte 재현은 결정론 경로 한정, 01 §12). ⚠ **현재 `simulate/` 코어엔 mc.distribution 노드가 없다**(레거시 `monteCarloForecast`는 별개 경로, 01 §5b) — Play의 fan chart는 MC 노드가 simulate DAG에 합류한 *후*에 결정론 path로 드러난다. **결손 구간**: `NodeValue.vector`가 원소별 None을 허용(01 §6.1, missing≠0 불변) → fan band는 None 구간을 **0으로 잇지 않고 끊어** 그린다(데이터 부재를 0 추정으로 위장 금지). **★fan-chart 출력 shape 핀(plan 갭)**: `SimulationResult`(run.py)는 revenuePath/marginPath/fcfPath/dcfPerShare 만 — *일별 가격 path·가격 백분위 밴드 부재*, 레거시 `monteCarloForecast` 백분위도 **펀더멘털**(rev/OI/FCF)이지 가격 아님. ⟹ mc.distribution 노드는 **펀더멘털 분포(rev/OI/FCF P5~P95) emit** + Play 가격 밴드는 *결정론 매핑*(시나리오별 perShare → asOf 가격 anchor × 성장계수 path)으로 파생; `SimulationResult` 에 `pricePath:{p5..p95}, freq, dates` frozen 필드 추가(01 §5b mc.distribution + 09 §10 빌드티켓 동반). 노드 빌드는 진짜 천장이나 *shape·매핑 규칙*은 지금 박음. **★fan band σ provenance 시각 규율(A6 흡수, 01 §5b 미러)**: σ가 pooled-OOS residual(검증)이면 **실선 fan**, elasticity prior(`elasticity_prior_unvalidated`, 미검증)이면 **점선·회색 근사 fan** — LucaNet/Causal의 매끈한 단일 fan과 명확히 가르는 디테일(cosmetic 가우시안 폭 = 통계적 연극 방지). **★가격 path 의미 라벨(R21 — fair-value path ≠ tradable return)**: Play 가격 밴드는 valuation perShare(frictionless DCF, `_fnDcf` proforma-FCFF 직접할인, 01 §5a)에서 파생한 **'fair-value path, not a tradable backtest return'** — 비용·슬리피지 *무관* 내재가치 시각화다. fee/slip ON tradable 수익률은 **walk-forward 모드(suite/03 백테스팅·03 §4)뿐** — Play 의 whatif/replay 가격 밴드와 *분리* 표기(혼동 시 "예상 수익률 N%" 약속으로 오독, 08 §7 RISK 표). 캡션 = "내재가치 경로 · 거래비용 미반영 · 실현수익 아님". 다중분기 중첩 밴드에는 **'branches share macro shock — not independent paths'** 라벨(같은 거시 충격을 공유하므로 독립 표본 평균/확률곱 금지, §5).
2. **예측 사건**: 정기보고서 캘린더(결정론적 알려진 미래 날짜) + 가정 이벤트 점선. **뉴스·shock은 미래에 안 찍음**(데이터 부재·예측 아님 — 구조적 한계). suite/02 이벤트레일의 미래 공시 마커가 여기로 흡수(07 의존성).
3. **예측 지표·지수**: ECON 오버레이 미래 연장 = preset 거시 경로(가정 라벨). 지수 subject(suite/01)면 지수 자체 미래 재생(가정 경로).
4. **예측 재무 IS/BS/CF**: t가 분기 노드 통과 시 하단 ReportDock에 `buildProforma` 투영 분기 펼침, bridge waterfall 시간순 갱신(08 §3.2).
5. **예측 신용(09 §4 solvency 뷰)**: 같은 분기 단면에서 survival curve·dCR 등급 궤적이 함께 전진(opt-in).

### 3.1 fan reveal 모션 계약 (모션 kinetics — §0.5·§1.1·§5 dangling `(§3.1)` ref 의 실제 거처)

> **★현 3곳(§0.5 (B) 그리드 '④ fan band 좌→우 reveal (§3.1)'·§1.1 '스크럽 중 fan band reveal 좌→우'·§2.1 σ provenance)의 dangling `(§3.1)` 참조가 가리키는 실제 계약을 이 절이 닫는다.** 메커니즘은 코드 보존(아래 ①), 한계 경계는 시간축으로(②~④).

- **① reveal = 봉 단위 이산 점프(매끈 tween 거부 — 코드 메커니즘 보존):** replay 가 `setInterval(replayStep, replayMs 400|150)` 로 *이산* 전진하는 현 메커니즘을 sim.play 가 그대로 차용한다 — **새 RAF 루프 0·연속 tween 0**. 한 tick = 한 봉 추가(이산), byte-결정론 보존(같은 specKey·seed → 같은 프레임열). fan band 가 매끈하게 흐르는 *연속 애니메이션*은 거부(중간 보간 프레임이 실재하지 않는 가상 값을 그림 — 시각 가드).
- **② 시간축 경계 — asOf+1..t 만 렌더(미래 미리보기 금지):** reveal 중 fan band 는 `asOf+1 .. t` 구간만 그려지고 `t+1 .. len` 은 **미렌더**(아직 도달 안 한 미래를 미리 보여주지 않음 — Play 의 '시간이 흐른다' 메타포 무결성, replay 가 idx 이후를 안 보이는 것과 동형). t 가 전진하며 우측으로 한 봉씩 채워짐.
- **③ band 폭 = 데이터(폭 보간 금지):** fan band 의 세로 폭(백분위 간격)은 *데이터 산출값*이지 reveal 진행에 따라 width 를 보간하지 않는다 — opacity 0→1 **fade-in 만** 장식(§10.5 모션 토큰 ≤120ms). 폭을 시간에 따라 키우면 불확실성 크기를 연출로 왜곡(통계적 연극 방지, §2.1 σ provenance 규율 정합).
- **④ 되감기 = 이산 역순:** `playStepBack` 은 reveal 역방향으로 *한 봉씩 제거*(이산, fade-out 대칭) — momentum/관성 0(§1 스크럽 인터럽트 불변식 user-input-wins 정합).

### 3.6 persistent annotation layer (설명적 내러티브 VIZ — 새 패널·새 색 0, 결정론 슬롯)

> **★§5 다중분기·§3.2 reveal 비트의 in-chart 설명층.** NYT/FT 식 직접 라벨링을 결정론 슬롯로 — 새 패널·새 색·AI 산문 0. annotation 은 §6 슬롯 규율(status 키 fill-in)을 차트 위에서 재사용한다.

- **① 분기 발산 지점 고정 캡션:** 분기가 갈라지는 결정론 슬롯(예: 금리 결정 분기)에 in-chart 캡션 **"{driver} 가정에서 분기"**(AI 산문 금지 — status·driverId 키 fill-in, §6 결정론 내러티브 슬롯). 위치는 §6 슬롯 규율 재사용(새 슬롯 발명 0).
- **② focal annotation lede 상존:** 미래 캔버스에 한 줄 lede = **"P50 중심 vs 현재가 닻 갭"**(§0.6 Play 5초 초점과 1:1, reverseDCF 닻 08 §2). 항상 보임(focal — 첫 시선이 닻 갭으로 떨어지게).
- **③ leader line 없는 직접 라벨(화살표 금지):** annotation 은 대상 옆 **직접 라벨**(leader line·화살표 0) — 화살표는 인과 방향 단정으로 오독(§1.2 인과 단정 가드 정합, "driver→가격" 화살표 금지). 직접 라벨은 *연결*만 표시.
- **④ highlight bus 와 직교(유일 채널 아님):** §1.2 highlightId bus 의 점등은 *추가* 강조지 annotation 의 유일 채널이 아니다 — annotation 은 상존(상시 설명), highlight 는 상호작용 시 일시 강조(§10.3 펄스 1회). 둘이 같은 nodeId 를 공유(§1.2 키 SSOT).
- **⑤ 밀도 = §12.3 densityLevel 종속:** annotation 밀도는 disclosure-level 토글에 종속 — **L1 = focal 1개**(닻 갭 lede 만), **L3 = 전 의미 지점**(분기·마일스톤 전부 캡션). 표면마다 따로 안 둠(§12.3 단일 토글 동기).

### 3.7 canvas essential meaning = off-canvas 텍스트 동치 강제 (접근성 SC 1.1.1 — 새 컴포넌트 0)

> **★코드 실측: fan band·waterfall·asOf 경계·missing 해치가 전부 `<canvas>`**(PriceChart klinecharts·08 §3.4 waterfall SVG/CSS, 그러나 klinecharts 오버레이는 canvas)**라 SR(스크린리더)에 불가시(SC 1.1.1) — 상태 인코딩(§10.1 status·해치·점선) *전체*가 비시각 사용자에게 부재한다.** 새 SR 전용 컴포넌트를 만들지 않고 *이미 존재하는 DOM 표*를 텍스트 동치로 SSOT 명문화한다.

- **fan band 텍스트 동치 = 기존 ReportDock evidence ledger(§6.1) 의 DOM 표** — P5/P25/P50/P75/P95 수치표가 SR 에 동일 정보를 제공함을 SSOT 로 박는다(새 표 0, §6.1 ledger 재사용). 차트가 못 읽혀도 우측 근거표가 같은 백분위를 평문으로 가짐.
- **차트 컨테이너 `role=img` + `aria-label`** 1줄: "asOf 이후 가정 구간 백분위 밴드, 상세 수치는 우측 근거표" — canvas 를 단일 이미지로 SR 에 노출하고 상세는 DOM 표로 위임(SC 1.1.1 만족). waterfall(08 §3.4)도 동일 패턴 — 컨테이너 `role=img`+aria-label, 상세는 §6.1 ledger/08 블록3 표.
- **missing·근사 인코딩의 비시각 동치:** 해치(missing)·점선(미검증)은 canvas 에서 SR 불가 → §6.1 ledger 의 status 칩 텍스트(§10.1 SR 채널·§11 카피)가 동일 의미를 평문으로 전달(시각 어휘 ↔ 텍스트 어휘 1:1).

---

## 4. if 토글 실시간 연동 (증분 재계산)

차트-스코프 인셋(05 §0.5, colL region rule 회피)에 AssumptionLedger if 토글. 토글 → `assumptionSet` 변경 → 결정론 gate 재판정 → usable 가지 path 재계산 → fan band·이벤트·재무 ReportDock 즉시 갱신.

**속도(01 §13b)**: 노드 `inputsHash` dirty recompute — 토글 1개 변경 시 하류 sub-DAG만 재계산(전체 아님). landing=사전 동결 격자 lookup(재계산 0·즉시) / 로컬=Python 증분. 디바운스만 하면 인터랙티브(순수함수). 드라이버 클릭 → DriverGraph 엣지 하이라이트 + 미래 구간 강조(§1.2 cross-panel highlightId bus = suite/02[전 11] 동기 패턴 재사용, 인코딩 SSOT §10.3).

> **★A4 흡수(Causal/FinChat 편집가능 드라이버셀 + 라이브 레버, absorb-as-defer):** "레버 드래그→fan 즉시 재렌더"는 이 §4의 제품 요구지만 신규 발명 0이며 **두 미구현 엔진 선결**을 명시 후속 라벨로 단다 — ⓐ dirty recompute `_dirtyClosure`(01 §6.2·§13b-1, 현 `evaluateSheet`는 항상 전체 재평가) + ⓑ Sobol S_T 가지치기(04 §5 OQ11 = 데모-의존 잠정값, k≤6은 proven bound 아닌 design target). 즉시 재렌더는 (1) landing = 01 §13b 사전 동결 격자 lookup(재계산 0, **격자축 = top-6 누적 S_T≥0.9 토글만**) (2) 로컬 = Python 증분 — 둘 다 퍼블릭 서버0 floor, 격자 밖 토글은 "로컬 Python 재계산 필요" 한계 라벨. 레버 = **차트-스코프 인셋 AssumptionLedger 토글**이지 자유 슬라이더 무더기 금지(Causal 무제한 편집셀 복제 = if-폭발 = `feedback_always_check_clutter` 위반). 레버 입력 = `AssumptionLedgerRow`(user source) 생성으로 단위·기간·falsifier 강제 — 단 이 *사용자-입력* row는 grounding-check(b) 순환에서 제거된 *AI-grounding* row와 구분된다(01 §6.3 OQ10의 "AssumptionLedgerRow 코드 0건 제거"는 약한-det 자체분포 순환 차단이지 사용자 입력 ledger 부정 아님). 결과는 항상 fan band(단일 path 강조 금지)·결손 None 끊김(0 대체 금지). **reject 경계 = 사용자 토글만 합법, "dartlab이 이 가정 쓰라" 개인화 추천 금지**(08 §7 Advisers Act 가드).

---

## 5. 다중 분기 동시 재생 + 결정론 재현

- **단일 분기**: P50 중심선 + fan band(seed 고정).
- **다중 분기**(`sim.branches[]`, ≤3 — 09 §13 OOM 상한): baseline/adverse/severe 동시 전진(색상 구분 P50 3선 + 반투명 밴드 중첩). 분기 갈라지는 시점(예: 금리 결정 분기)에서 부채처럼 벌어짐. 트리 노드=RunSpec, 부모 분기말 BS 상속.
  - **분기 색 = categorical 분기 팔레트**(AuditStrip RUN_COLORS distinct hue, §10 채널 예산): baseline=blue #5b9bf0 / adverse=orange #fb923c / severe=purple #a78bfa(또는 등록 순). 시안 #22d3ee 는 focus 전용이라 분기색에서 제외(focus 와 분기 혼동 방지). 녹/적은 §10 부호색 규율상 호재/악재 단정 회피로 분기 식별색에 미사용.
  - **★occlusion 회피(VIZ — 3밴드 중첩 가독성)**: 3 분기 fan 밴드 fill 중첩은 색 진흙탕(muddy alpha)이 된다 → **(중첩 모드 기본)** hover/focus 한 분기만 밴드 **fill**, 나머지는 **외곽선(P50 선 + 밴드 경계선)만** 표시(focus+context). **(small-multiples 토글 1개)** = 분기별 미니 패널 3개 **공유 y축**(축 정렬로 폭 비교 가능). 두 모드는 §0.5 if 인셋 옆 토글 1개(새 패널 더미 0). focus 분기 = §1.2 highlightId bus 와 연동(시안 외곽).
  - **★프레임 예산 + degradation(모션 kinetics — worst-case 침묵 메움):** worst-case = **3분기 동시 reveal + cross-highlight pulse@150ms(2.5×)**. 시간 예산 = 한 reveal step 전체 렌더가 *다음 `setInterval` tick 전*(150ms@2.5×) 완료(§10.4 시간 예산 행이 SSOT, 졸업 데모 AC). 예산 초과 시 degradation: **① occlusion 강제 focus-only**(중첩 fill 제거, 외곽선만) **② pulse 는 자동재생 중 suppress**(스크럽·hover 같은 명시 상호작용에만 — MOTION.md §3.6 '모두 펄스면 아무것도 펄스 아님'의 시간축 적용) **③ small-multiples 는 3 독립 캔버스로 예산 분산**(한 캔버스 3밴드 합성 부하를 3 캔버스로 나눔). 예산은 잠정값(졸업 데모서 실측 재보정).
- **결정론 재현**: 같은 `ScenarioSpec`(assumptionSet `on` 상태 + MC seed + asOf + branch) → 바이트 단위 같은 재생. 현 결정론 코어는 **난수 0**이라 seed 없이도 노드별 inputsHash byte-identical(MC seed는 mc.distribution 노드 합류 후 적용, 로컬 `random.Random(seed)`, numpy/PCG64 아님). `sim.specKey`=직렬화 키, URL `?sim=` 공유(08 §8 — 단 브라우저는 사전계산 path 드러내기, RNG 미사용). 두 번 눌러도 같은 미래.

**★격자 직렬화 계약(01 §13b.6 보강):** (i) `gridArtifact` TS 인터페이스 = `{specKey → {candles:{p5..p95:number[]}, fanBand, events:SimEvent[], macro:number[], report, credit}}`(SimSeries/FanBand/SimEvent 타입, candles freq); (ii) `specKey = serialize(branchId, sorted(toggleState), mcSeed, asOf)` 결정론 — float round·sorted keys 정규화(01 §6 `_normalize` 미러, TS/Python byte-parity 골든); (iii) `sim.play.t(0..len)` → gridArtifact 시간-인덱스 매핑. 격자 *스키마*는 지금 박음(OQ11 의 k≤6 축 선택은 데모 의존, 분리).

---

## 6. 근거 인벤토리 + 결정론 내러티브 (완전성 ADD)

운영자 "과거 근거 + 미래 수십~수백 예측 근거 나열·연결" — DriverGraph 엣지 하이라이트만으로는 "연결"만 되고 "나열"이 빠진다. 보강:
- **근거 인벤토리 뷰**: ReportDock 한 탭으로 `evidence ledger`(과거 fact ref + 미래 driver, 출처/asOf/provenance 컬럼, DriverGraph 엣지 cross-link). 수백 근거를 표로 나열, 토글 상태 표시.
- **결정론 내러티브 슬롯**(story 재활용 금지 — AI 산문 환각 차단): "X 가정 → Y 분기 영업이익 Z원(ref) → 목표가 W(ref)" 식 fill-in 결정론 템플릿(scan 결정론 서사 패턴). AI 생성 산문 금지, 결정론 슬롯만.

### 6.1 Assumption Ledger = 정렬가능 밀도표 + 인라인 시각화 (VIZ)

근거 "나열"을 가독 있게 — 00 §5.2 Assumption Ledger 컬럼(가정/driver/base→scenario/range/ref/falsifier/status)을 ReportDock 한 표로 *밀도 있게* 펼치되, 표 안에 미니 시각화를 인라인(별도 차트 패널 0 = 깎아서 강함):

- **기본 정렬 = S_T 내림차순**(민감도 큰 가정 위 — Sobol S_T, 02 §2B.4-C). 클릭 정렬 = status·driver·base→scenario delta 도 가능.
- **status 색칩**: 각 행 좌측 status 칩(§10 status 표 SSOT 색 — fact=불투명 실선·hypothesis=점선 회색·blocked=적색·missing=해치 'missing(0아님)' 칩). status 가 표의 1열.
- **base→scenario dumbbell**: base value ●——● scenario value 한 칸 dumbbell(이동 방향·폭 = 가정 강도). 부호는 §10 부호색 규율(증가=시안 계열·감소=중립 회색, 호재/악재 단정 금지). **값 표기 = §10.4 number-render SSOT**(KRW 금액 = `fmtKRW` 조/억+천단위 콤마, 배수/비율 = `tabular-nums`).
- **S_T 미니막대**: 정렬 키인 S_T 를 행 끝 가로 미니막대(표 안 sparkline, chartjunk 0).
- **falsifier 부재 = 적색 ⚠**: falsifier 컬럼 비면 적색 ⚠(03 G13 Falsifier 미충족 시각화) — "반증 없는 가정" 즉시 눈에. 03 §6.2 reverseDCF 닻 충돌도 같은 행 표시.
- **헤더 status 분포 stacked bar**: 표 헤더에 전 행 status 분포 1줄 stacked bar(fact/estimate/hypothesis/missing/blocked 비율) — "이 시나리오가 얼마나 fact 기반인가" 한눈. 08 §6 체크리스트 #7(결손=결손) 시각 동기화. (§0.6 first-read 초점 — ledger 화면의 5초 초점 SSOT 로 승격.)
- **★시맨틱 table 강제(접근성 SC 1.3.1 — 코드 선례 결함 수정):** ledger·gate·provenance 표는 `<div>` 그리드가 아니라 **시맨틱 `<table>` + `scope=col`/`scope=row` + `<caption>`** 로 구현(현 13개 차트 컴포넌트 `scope=col` **0건**, 코드 실측 — 행/열 의미가 SR 에 도달 안 함). caption = ledger 의 시나리오·asOf 1줄 요약(canvas 차트의 텍스트 동치 역할도 겸, §3.7). status 칩(§10.1)·S_T·dumbbell 셀은 각각 `aria-label` 로 값+단위 평문 노출(시각 인코딩 ↔ SR 텍스트 1:1).
- **★한글 dense 셀 타이포(현지화 — 11px floor 정합, 새 규약 발명 0):** 11px floor 에서 한글 글리프가 영문보다 세로 점유가 커 한글 가정 라벨이 잘리고 어절 무시 줄바꿈이 난다 → 기존 BacktestStrip `tabular-nums`·line-height 규약을 ledger 에 명시 상속: **숫자 셀 = `font-variant-numeric:tabular-nums`**(dumbbell·S_T 자릿수 정렬 흔들림 제거), **한글 라벨 = `word-break:keep-all`(어절 보존) + `line-height≥1.4`**(11px floor 한글 가독), 1행 초과 시 **§12.3 L1 축약 ellipsis**(어절 보존 — 글자 중간 끊김 금지). 영문 라벨은 기존대로.

---

## 7. Graceful degradation (완전성 ADD — 데이터 공백 종목)

시뮬레이션 불가/부분가능 종목의 명세(03 §6 가드):
- 신규상장사(과거 시계열 < 회귀 최소 nObs) → pooled-panel 섹터 transfer 폴백(02 §2B.1), 그래도 부족하면 **Play 버튼 비활성 + 사유 표시**("시계열 부족 — 시뮬 불가").
- 분기 결측·정정공시로 BS 항등식 과거 미닫힘 → buildProforma 상속 체인 붕괴 시 blocked status, 결과 미생성.
- walk-forward 모드: Play는 whatif/replay 시각화, **walk-forward는 ReportDock 리포트-only**(시간축 애니메이션 아님 — 명시 결정).

---

## 8. 거처·계약

- **UI**: `ui/packages/surfaces/src/terminal/charts/`(PriceChart `subject`/`sim` 모드, chartState 확장). ReportDock 셸(08 §5, valuation→sim mode). 새 패널·차트 인스턴스 0.
- **엔진**: Play는 `dartlab.simulate(mode="replay"|"whatif", ...)` 결과(`SimulationResult`)를 시간축으로 드러냄. 계산은 L2.5 simulate(01), UI는 드러내기만.
- **선결**: 09 Phase 0 MC seed kill-test(결정론 재현 척추) → simulate 코어 졸업 → Play UI. mainPlan 완료(터미널 ui/packages 정착) 후.

### 8.1 ★ReportDock 거처 SSOT 확정 (R5 — 08·00 이 포인터로 참조)

> **결정(코드 선례 근거): ReportDock = StrategyDock 패턴 일반화, simulate 진입 시 colL 좌패널(LeftRail) 전체 교체.** RightStack 새 탭이 아니다.

- **코드 grep 결과**: `StrategyDock.svelte`는 `fill` props 로 **좌패널 전체 차지**(`:19` "true = 좌측 패널 전체 차지·폭 100%·리사이즈/접기 없음")가 실재하고, `TerminalSurface.svelte:370-376` 이 `colL` 을 backtest 모드면 `<StrategyDock fill>`, 아니면 `<LeftRail>` 로 **이미 조건부 교체**한다. **`ReportDock` 컴포넌트는 현재 부재**(grep 0) — 신설 대상. 즉 "좌패널 전체 교체" 동선은 *발명이 아니라 backtest 선례 복제*라 학습비용 0.
- **거처 = colL 좌패널 교체(RightStack 탭 아님)**: 같은 `TerminalSurface.svelte:370` colL 분기에 sim 모드 한 갈래 추가 — backtest 면 `<StrategyDock fill>`, sim 이면 `<ReportDock mode='sim' fill>`, 아니면 `<LeftRail>`. RightStack(colR)은 단일기업 공시/재무 컨텍스트 유지(시각 정합·기존 멘탈모델 보존). §0.5 (B) 그리드가 이 배치.
- **형태 = StrategyDock 일반화 `mode='backtest'|'sim'|'valuation'`**: 신규 별도 셸이 아니라 StrategyDock 의 `fill`/`onClose`/접힘 스파인(`:131`) 골격을 `mode` union 으로 일반화한 **공통 도크 셸**. backtest=백테스트 조작 패널, sim=Play 근거 인벤토리+Assumption Ledger(§6·§6.1)+status 카피(§7), valuation=정적 보고서 12블록(08 §3.2). 08 §5 "ReportDock=valuation 단일 모드로 시작" 과 정합 — **valuation 단일모드 → backtest/sim 탭 증설 동선**: 08 §5 가 valuation 모드를 먼저 ship(엔진 졸업 순서), 본 05 가 sim 모드를, suite/03 이 backtest 모드를 같은 `mode` union 에 증설(YAGNI 회피 = 각 엔진 졸업 시 해당 mode 추가, 추상화 선투자 금지).
- **★일반화 vs 신규 셸 판정(잠정 — 졸업 데모서 확정)**: StrategyDock `fill` 골격이 sim/valuation 콘텐츠를 *덕지덕지 없이* 담으면 일반화(권장), backtest 전용 상태(BT_PRESETS·RULE_PRESETS·rule 편집기)가 sim 에 죽은 무게로 끌려오면 공통 셸(`ReportDock`)을 새로 빼고 StrategyDock 이 그것을 `mode='backtest'` 로 소비. **둘 중 선택은 데모서 colL 콘텐츠 3종의 공유 골격 비율 측정 후 확정**(`feedback_always_check_clutter`: 공유 70%↑면 일반화, 미만이면 신규 셸). 어느 쪽이든 colL 교체·`fill`·`onClose` 계약은 불변.

(이 §8.1 이 ReportDock 거처 SSOT — 08 §5·00 §6 은 "결정 = 05 §8.1" 포인터로만 참조, 결정 본문 중복 금지.)

---

## 9. 왜 심오하면서 정공법인가

운영자의 미래 리플레이 퍼포먼스(Play·일시정지·속도·스크럽·다중분기·if 토글 실시간·결정론 재현)를 *완전히* 구현하되 새 재생 엔진 0 — 기존 replay 와 동형인 미래 상태기계(sim.play 1객체 + play* 4메서드) 신설, 재생 엔진(타이머·렌더·컨트롤)은 공유 + 결정론 산출물 드러내기. 화려한 모든 픽셀이 검증 엔진·정전 기법에 1:1 대응. **"강함은 쌓아서 아니라 깎아서."**

---

## 10. 시각 인코딩 SSOT (상태 표 — VIZ-1, 05·08·00 §6 단일 참조원)

> **이 §10 이 시각 인코딩 단일 SSOT다.** Play fan band·Assumption Ledger(§6.1)·ReportDock 12블록(08 §3.2)·DriverGraph 점등(§1.2) 의 *모든* status 인코딩이 이 표를 참조한다(컴포넌트마다 색 재발명 금지). 기존 컴포넌트(HonestyFooter 3단·AuditStrip bad=적색)의 **확장**이지 새 체계가 아니다 — 1:1 정합을 아래 명시.

### 10.1 status × redundant 3채널 매핑 (색 + 선종/형태 + SR 텍스트, 단일 채널 의존 금지)

각 status 는 **색 + 선종/형태 + 비시각(SR) 텍스트** **3채널**로 표현(색맹·인쇄·저대비 *그리고 스크린리더* robust, 색 단독·시각 단독 금지). 색은 *의미색만*(시안=focus 1곳·적색=blocked·amber=미검증 — 무지개 금지). **3번째 SR 채널이 §10 "robust" 주장을 비시각 사용자에게도 진실로 만든다**(canvas SR 불가시는 §3.7 텍스트 동치로 별도 해결):

| status | 색 (CSS var) | 선종/형태 | 불투명 | 배지/캡션 | 비시각(SR) 채널 | 0 보간 |
|---|---|---|---|---|---|---|
| **fact / usable** | `--dl-ink #c8cfdb`(중립 잉크) | 실선 | 100% | 없음(기본=신뢰) | `role=img`/`aria-label` 생략(기본=신뢰, 노이즈 회피) | — |
| **estimate** | `--dl-ink` dim | 실선 | 85% | (옵션) ⟨est⟩ | `aria-label='추정값'` | — |
| **hypothesis (AI)** | 회색 `#9aa`(=#8b94a3 계열) | **점선** | — | 우상단 **⟨hyp⟩ 배지** | `aria-label='가설(AI), 미검증'` | — |
| **missing** | — (렌더 안 함) | **구간 끊김 + 45° 해치 플레이스홀더** | — | **'결손' 캡션 + 'missing(0아님)' 칩** | `role=img aria-label='결손, 0 아님'`(§11 카피 재사용) | **절대 금지** |
| **blocked** | 적색 `--dn #f0616f` 외곽 | **빗금 + 잠금 아이콘** | — | 'blocked' | `aria-label='차단됨'`(§11 카피 재사용) | — |
| **partial** | 중립 | **점선 외곽** | 60% | 'partial' | `aria-label='부분 계산됨'`(§11 카피) | — |
| **usableWithGaps** | 약한 부분만 amber `#fb923c` | 실선 + 약부분 점선 | — | **'신뢰도 낮음' 라벨 상시** | `aria-label='일부 근거 빠짐, 신뢰도 낮음'`(§11 카피) | — |
| **rejected** | dim | **취소선 / 미표시** | — | 'rejected' | `aria-label='가정으로 결과 불가'`(§11 카피) | — |

- **SR 채널 = §11 한국어 평어 카피 재사용(중복 0)**: aria-label 카피는 새로 쓰지 않고 §11 상태 카피 매트릭스의 한 줄 제목을 *키 fill-in* 으로 가져온다(결정론 슬롯, §6) — 시각 라벨과 SR 라벨이 같은 SSOT 라 drift 0. blocked='차단됨'·missing='결손, 0 아님' 등.
- **★status 전환 = `aria-live=polite` announce(§10.2 HonestyFooter region 승격):** status 가 바뀔 때(예: if 토글로 usable→blocked) HonestyFooter 영역을 `aria-live=polite` region 으로 승격해 1줄 announce — 비시각 사용자가 status 전환을 *놓치지 않게*(시각 칩 색 변화의 SR 동치). 폭주 방지로 `polite`(즉시 끼어들지 않음)·전환 시 1회만.
- **missing 0 보간 절대금지**: fan band·ledger·bridge 어디서도 None 구간을 0 으로 잇지 않는다(01 §6.1 `NodeValue.vector` 원소별 None, missing≠0 불변 시각 강제). 끊김 + 해치 = "여기 데이터 없음"의 시각 어휘.
- **focus(cross-highlight) 색은 status 와 직교**: 시안 #22d3ee 는 *선택 상태*(focus)지 status 아님 — status 가 hypothesis(회색 점선)여도 focus 면 시안 외곽이 덧입혀짐(§10.3).

### 10.2 기존 컴포넌트 1:1 정합 (재발명 아닌 확장)

| 본 §10 status | 기존 컴포넌트 대응 (코드) |
|---|---|
| fact/estimate 스탬프 상존 | **HonestyFooter Tier1** 명세 스탬프(`HonestyFooter.svelte:82-88` '체결 t+1 시가'·'비용 반영'·'기준일' — 닫기불가 상존) |
| usableWithGaps / partial 구조한계 | **HonestyFooter Tier2** 구조한계(`:70-72` N≥2 사후선택 상존) |
| hypothesis(AI)·usableWithGaps active | **HonestyFooter Tier3** active amber 경고(`:110,121` `--amber`, 발동 시만) |
| blocked | **AuditStrip bad=적색**(`AuditStrip.svelte:46,48` `.bad`·비적정 카운트 `:37`) + `--dn #f0616f` |
| 방법론 on-demand | HonestyFooter ⓘ 방법론(`:88` Bloomberg 패턴 on-demand) — status 칩 hover 시 §12 TermGloss 연동 |
| status 전환 announce(SR) | **HonestyFooter 영역 = `aria-live=polite` region 승격**(§10.1 3채널 SR 행) — 현 터미널 `aria-live` 0건·`role=status` 0건(코드 실측)이라 status 전환이 SR 에 무성(無聲). HonestyFooter 가 이미 status 스탬프 상존 영역이라 *새 region 신설 0* — 기존 영역에 `aria-live` 속성만 부여 |

'초록 축포 금지'(HonestyFooter 규율) 계승: 시나리오가 우위(up)여도 success 색 `--up #34d399` 은 dim 처리, 단정 톤 금지(§10.4 부호색).

### 10.3 cross-highlight 인코딩 (§1.2 highlightId bus 시각 SSOT)

| highlight 상태 | 인코딩 |
|---|---|
| **선택(focus)** | 시안 #22d3ee 외곽 + 선 굵기↑ |
| **연관(linked)** | 시안 디밍(저채도 시안) |
| **비연관(unrelated)** | 불투명 35% dim |
| **전이 펄스** | 1회 200ms 펄스(반복 금지 — 주의 분산 방지). `prefers-reduced-motion: reduce` 면 펄스 *생략*(§1.1 reduced-motion 규약 — 1회·반복 금지라 대체 모션 불필요) |

### 10.4 채널 예산 (어떤 시각 채널이 무엇을 독점하나 — chartjunk 금지)

강한 시각은 채널을 *덜* 쓴다(깎아서 강함). 채널별 단일 책임 고정:

- **위치(position) = 정량 독점**: x=시간·y=값. 위치를 장식에 쓰지 않음(가장 정확한 채널을 데이터 전용).
- **색(color) = categorical 분기 + 의미 status 만**: 분기 식별(RUN_COLORS distinct hue, §5) + status 의미색(시안 focus·적색 blocked·amber 미검증). 그 외 색 금지(그라데이션 장식·무지개 범례 금지).
- **형태/선종 = 상태 표현**: 실선/점선/해치/취소선 = §10.1 status. 색과 redundant(2채널).
- **라벨(text) = 값·단위·ref**: 숫자에 단위·ref 동반(01 §2.5 '단위없는 숫자 invalid'). 장식 텍스트 금지.
  - **★KRW number-render SSOT(현지화 — 새 formatter 0, 혼용 차단):** 큰 KRW 금액 = **`engine.ts fmtKRW`(조/억 + 천단위 콤마)** 가 SSOT. `helpers.ts fmtAbbr`(T/B/M/K)는 **KRW 표면 금지**(코드 실측 — 두 formatter 가 공존하나 한 화면에 조/억 ↔ T/B/M/K 혼용은 오독). 비율/배수/주가 = `tabular-nums`(자릿수 정렬). **`lang===en` 모드에서만** fmtAbbr(T/B/M/K) 분기 허용. 08 §3.4 bridge delta·§6.1 dumbbell·waterfall 값 표기 = 이 행을 포인터 참조(번역값은 §11 KR/EN 슬롯, 숫자 포맷은 이 SSOT).
- **★비텍스트 대비 ≥3:1(SC 1.4.11 — 새 색 0):** essential 그래픽(§6.1 S_T 미니막대·해치 테두리·fan 경계선·dumbbell·asOf 경계)은 fill 이 1.4:1 이어도 **테두리/외곽선을 ≥3:1 토큰**으로(기존 `--dl-ink #c8cfdb` ~6:1 계열 외곽 재사용, 신규 색 0). 35% dim(§10.3 비연관)은 opacity floor 로 dim 후에도 인접 객체와 ≥3:1 유지. **대비 기준점 배경 토큰 = 실코드 `--dl-bg-base #0a0e15`/`--dl-bg-raised #0e141f`**(README 의 `#050811` 은 정정 대상 — 대비 계산 SSOT 가 실배경과 어긋나면 ≥3:1 판정이 거짓이 됨, §2.1 정합).
- **★시간 예산(모션 kinetics — chartjunk 의 시간축):** 시각 채널이 공간 예산을 쓰듯 *시간* 예산도 명시 — 한 reveal step(§3.1) 전체 렌더가 **다음 `setInterval` tick 전 완료**(worst-case 150ms@2.5×, §5 3분기 동시 reveal+pulse). 초과 시 §5 degradation(occlusion focus-only·자동재생 중 pulse suppress·small-multiples 3 캔버스 분산). 예산은 잠정값(졸업 데모 AC 재보정).
- **★부호색 규율(인과 단정 가드)**: 실현(과거) 수익은 기존 `--up #34d399`/`--dn #f0616f`(녹/적) 관례 유지 가능. 그러나 **시나리오 투영/bridge delta 는 호재/악재 단정 회피 — 중립 톤으로 *부호만***(증가=시안 계열 #22d3ee·감소=중립 회색 `#8b94a3`), 녹/적 '좋다/나쁘다' 금지. 미래 path 의 상승을 녹색 축포로 칠하면 "오른다" 단정으로 오독(00 §3 조건부 언어·08 §7 "예상 수익률 약속" 가드).
- **chartjunk 금지**: 격자선 최소(§2.1 기준선 외)·3D·그림자·불필요 범례 금지.

### 10.5 모션 토큰 (시간축 인코딩 SSOT — 새 색/패널 0, 표 행만)

> **★§10 이 *시각* 인코딩 SSOT 이듯 본 §10.5 가 *모션*(시간축) 인코딩 SSOT 다.** §3.1 reveal·§1.1 reduced-motion·§5 프레임 예산·§10.3 펄스가 모두 이 표를 참조한다(컴포넌트마다 timing 재발명 금지). 모션도 가드 대상 — 상승을 spring/bounce/녹색 펄스로 칠하면 "오른다" 단정이라(00 §3·§10.4 부호색 1:1).

| 모션 토큰 | 값 | 이징 | 규율(시각 가드) |
|---|---|---|---|
| **전이 펄스** | 200ms **1회**(§10.3, 반복 금지) | ease-out | 주의 분산 방지·reduce 시 생략(§1.1) |
| **reveal step fade-in**(§3.1) | ≤120ms | ease-out | `setInterval` 간격(400/150ms)보다 짧아 다음 tick 전 정착(이산 점프 보존, width 보간 0) |
| **미검증 σ fan fade-in**(§2.1·§3.1) | reveal step 보다 *느리고 약하게* | ease-out | **신뢰도 = 모션 강도**(미검증=점선 + 더 느린/약한 fade, 기존 opacity 재사용 — 검증 fan 보다 시각·시간 약하게) |
| **linear/overshoot/bounce/spring** | **금지** | — | 상승을 축포·반동으로 칠하면 "오른다" 단정(§10.4 부호색)·금융 시점은 정확값(§1 관성 0) |
| **녹색 펄스(success 축포)** | **금지** | — | '초록 축포 금지'(HonestyFooter 규율 §10.2) 시간축 적용 |

- **★sns/remotion MOTION.md 정합 1줄:** 터미널 Play 모션은 Remotion(쇼츠) 토큰과 **독립**(표면별 timing 값은 다름)이나 **원칙은 공유** — linear 금지·overshoot 0·축포 금지. *토큰 값은 표면별, 규율은 단일* (Remotion 의 BGM 덕킹·Lottie 타이밍을 터미널이 복제하지 않되, 시각 가드 어휘는 한 결).

---

## 11. 상태별 사용자향 카피 매트릭스 (R14 — 03 §2 Gate Matrix 가 포인터 참조)

> **이 §11 이 status→사용자 카피 SSOT다.** 03 §2 Gate Matrix(G0~G15)의 실패 상태(rejected/blocked/usableWithGaps/partial)는 *기계 라벨*이고, 본 §11 이 그 라벨을 **초보 평어 카피**로 번역하는 단일 표다(03 §2 는 "사용자 카피 = 05 §11" 포인터). 백로그가 지정한 '§7 상태별 카피'는 §7(Graceful degradation) 충돌 회피로 본 §11 에 둔다 — 의미·범위 동일. 톤 불변: **"고장이 아니라 조건 미충족"**.

| status | 아이콘 | 한 줄 제목(초보 평어, KR) | EN 한 줄 제목(병기) | 사유 | 복구 안내 | 톤(고장 아님) |
|---|---|---|---|---|---|---|
| **blocked** | 🔒 | "이 종목은 아직 시뮬레이션할 수 없어요" | "This stock can't be simulated yet" | "상장 후 데이터가 회귀 최소 기간보다 짧습니다"(또는 BS 항등식 과거 미닫힘) | "더 긴 이력이 쌓이면 자동으로 가능해집니다" | "제품 결함이 아니라 *근거 보존* 규칙입니다 — 없는 데이터를 지어내지 않습니다" |
| **rejected** | ⛔ | "이 가정으로는 결과를 낼 수 없어요" | "These assumptions can't produce a result" | "필수 입력(종목/기간/통화) 또는 결손 0 대체 금지 규칙에 걸렸습니다" | "가정 X 를 채우거나 horizon 을 조정하면 풀립니다" | "차단은 *입력 가드*가 작동한 정상 동작입니다" |
| **usableWithGaps** | ⚠ | "결과는 나왔지만 일부 근거가 빠졌어요" | "Result is ready, but some evidence is missing" | "일부 driver 의 ref/검증이 비어 신뢰도가 낮습니다" | "약한 부분(배지 표시)에 가정/근거를 더하면 올라갑니다" | "부분 결과를 *숨기지 않고* 약한 곳을 드러냅니다" |
| **partial** | ◐ | "절반만 시뮬레이션됐어요" | "Only part was simulated" | "일부 분기/노드만 계산되고 나머지는 데이터 부재입니다" | "결손 분기 데이터가 채워지면 완전해집니다" | "빈 곳을 0 으로 메우는 대신 *부분* 으로 표기합니다" |
| **missing** | ▢ | "이 구간은 데이터가 없어요" | "No data for this range" | "해당 기간/항목 공시가 존재하지 않습니다" | "공시가 올라오면 자동 반영됩니다" | "**'missing(0 아님)'** 칩 — 0 으로 위장하지 않습니다(§10.1)" |

- **usableWithGaps = 부분 결과 + 약한부분 배지 + '일부 근거 빠져 신뢰도 낮음' 상시 라벨**(§10.1 행과 정합, HonestyFooter Tier3 amber 연동).
- **missing 셀 = 'missing(0 아님)' 칩**(§10.1 해치 + 본 카피) — fan band·ledger·bridge 공통.
- 카피는 **결정론 슬롯**(§6 내러티브 슬롯 규율) — AI 산문 아님, status 키→고정 문구 fill-in.
- **★KR/EN 병기 패리티(현지화 — 카피 = `Bilingual{kr,en}` 결정론 슬롯):** 카피 타입 = `Bilingual{kr,en}`(AI 번역 0 — 사람 KR/EN 쌍 fill-in). HonestyFooter `T(kr,en)` 병기 계약을 sim 카피가 *KR-only* 로 깨지 않게 — `lang===en` 이면 EN 열 노출. §10.1 SR(aria-label) 채널도 같은 `Bilingual` 슬롯에서 lang 분기(시각 라벨 ↔ SR 라벨 ↔ 언어가 한 SSOT). 사유/복구/톤도 동일 `Bilingual` 슬롯 확장(표 가독상 EN 제목만 병기 노출, 나머지는 lang 분기 fill-in).

---

## 12. 초보 학습성 3종 (R7 — 새 패널 0·정적 콘텐츠 + tooltip 레이어)

> 깊이를 낮추지 않고 *진입로*를 연다. 새 패널·새 차트 0 — 정적 온보딩 콘텐츠 + tooltip 데이터 계약 + 기존 접기/펼치기 규율 재사용("깎아서 강함").

### 12.1 First-Run Onboarding Ladder (단계별 노출 — 한 번에 다 안 보임)

| 단계 | 트리거 | 노출 컴포넌트 | 카피 | CTA |
|---|---|---|---|---|
| **L0 빈상태** | sim 첫 진입(이력 0) | 차트 + 단일 CTA | "**예측이 아닙니다.** 켜는 가정 하에서 미래가 어떻게 펼쳐질 수 있는지 보여줍니다(scenario ≠ forecast)." | **[미래 재생]** 1버튼 |
| **L1 baseline fan** | L0 CTA 클릭 | baseline fan band **만** + 코치마크 | "P50 중심선 + 백분위 밴드. 단일 목표가가 아니라 *범위* 입니다(§2.1)." | 코치마크 "다음 →" |
| **L2 가정 1개 토글** | L1 다음 | 가정 1개 토글 슬라이드인 + Before/After | "가정 1개를 켜보세요. 켜기 전/후 fan 이 어떻게 바뀌는지 비교합니다." | [가정 켜기] → Before/After |
| **L3 bear/base/bull + 닻** | L2 다음 | 3분기 동시(§5) + reverseDCF 닻 카드 | "3 시나리오와, *현재가가 이미 요구하는* 성장률(reverseDCF 닻, 08 §2)을 함께 봅니다 — '얼마 오를까'가 아니라 '시장이 박은 가정이 그럴듯한가'." | 닻 카드 펼침 |

- 각 단계는 *정적* 코치마크/슬라이드인(상태 1개 `onboardStep`), 완료 후 dismiss·재방문 시 skip. 새 패널 0.
- **★카피 = `Bilingual{kr,en}` 결정론 슬롯(§11 KR/EN 병기):** 각 단계 카피(L0 "scenario ≠ forecast" 등)는 `Bilingual{kr,en}` 쌍 fill-in — `lang===en` 분기(AI 번역 0). §2.1 fan 캡션·§12.2 TermGloss 와 같은 슬롯 SSOT(HonestyFooter `T(kr,en)` 계승).
- **★코치마크 모션 = reduced-motion 대체(§1.1):** 코치마크 슬라이드인은 `prefers-reduced-motion: reduce` 면 즉시 최종 위치로 점프(애니메이션 0, §1.1·§10.5 모션 토큰).

### 12.2 TermGloss 데이터 계약 (용어 tooltip — 첫 등장 1회 inline 펼침, 키보드 도달 강제)

각 표면 용어에 tooltip 데이터 계약 `{oneLineDef, example, whyMatters}` 강제. example = **이 회사 실제 숫자**(추상 정의 아님 — grounding). ledger 헤더·gate 칩·status 칩 hover 시 §10/§11 과 연동. 첫 등장 1회 inline 펼침(이후 hover only).

- **★키보드 도달 강제(접근성 SC 1.4.13/2.1.1 — `title=` 의존 배제):** 코드 실측상 터미널은 `title=` 225곳·`aria-describedby` 0곳 — `title` 속성은 **키보드 포커스로 안 뜨고(SC 2.1.1 위반)·SR 읽기 불안정·hover 만 트리거(SC 1.4.13 위반)**. TermGloss 는 `title=` 에 의존하지 **않고** 키보드 도달 팝오버로: **① focus + hover 둘 다 트리거**(키보드 사용자 도달) **② ESC dismiss** **③ hoverable persistent**(팝오버로 포인터 이동 가능, 즉시 사라짐 금지 — SC 1.4.13). **첫 등장 inline 펼침을 1차 채널로 승격**(hover/focus 보조 — 입력수단 무관 도달).
- **★status 칩은 hover 의존 금지:** status 칩(§10.1)은 hover 로만 의미가 뜨면 키보드·터치·SR 에 도달 못함 → **§11 카피를 상시 표시 또는 `aria-label` 로 박아** 입력수단 무관 도달(§10.1 SR 채널 행과 1:1). `title` 속성 의존을 SSOT 에서 명시 배제.

```typescript
interface TermGloss {
  term: string;
  oneLineDef: Bilingual;        // {kr,en} 결정론 슬롯 (§11 KR/EN 병기, AI 번역 0)
  example: string;              // 이 회사 실측 — 언어 무관(숫자라 KR/EN 동일)
  whyMatters: Bilingual;        // {kr,en} 결정론 슬롯
}
interface Bilingual { kr: string; en: string; }   // lang 분기 fill-in (§11)
```

> **★현지화 정정(코드-진실):** TermGloss `oneLineDef`/`whyMatters` 는 `Bilingual{kr,en}`(설명 산문이라 언어별 쌍 필요), **`example` 만 string 유지**(이 회사 실측 *숫자*라 언어 무관 — 억지 번역 0). HonestyFooter `T(kr,en)` 병기 계약을 TermGloss 가 KR-only 로 깨지 않게.

**필수 해설 ≥15개**(잠정 목록 — 졸업 데모서 표면 용어 전수 재보정):
reverseDCF · implied growth · P10/P50/P90 · fan band · DSO · CFO/NI · terminal value · WACC · falsifier · S_T(민감도) · base→scenario · usableWithGaps · look-ahead · vintage(asOf/availableAt) · hypothesis(AI 숫자) · bridge(waterfall) · reinvestment rate. (≥15 충족, 표면 신설 용어는 등록 강제.)

### 12.3 disclosure-level (밀도 토글 1개 — 기존 접기/펼치기 재사용)

ledger·bridge·12블록에 L1축약/L2/L3전개 3단. **기본 = L1**(초보 진입 부담↓), '밀도 높이기' 토글 **1개**로 L3 전개. 기존 접기/펼치기 규율(StrategyDock 접힘 스파인 `:131`·HonestyFooter ⓘ 방법론 on-demand) 재사용 = 새 메커니즘 0.

- L1 = 핵심 1줄(예: ledger 행 = 가정+status+delta), L2 = +ref/range, L3 = +falsifier/provenance/S_T 전개.
- 토글 1개(`densityLevel`)가 전 표면 동기 — 표면마다 따로 안 둠(깎아서 강함). 디폴트 L1 = §11 초보 카피와 한 결.
