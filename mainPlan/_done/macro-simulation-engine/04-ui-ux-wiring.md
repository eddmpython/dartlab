# 04 · UI/UX Wiring — 터미널 배선 (배선 잘해라)

> 원칙: 새 거대 surface 신설 금지(declutter). 방금 만든 거시 패널/다이얼로그를 *확장*한다. 차트는 MiniFinChart SSOT(손수 차트 0). 데이터는 `rt.macro` 단일 진입점. 푸시 전 스크린샷 전수 눈검수.

## §0. 현재 거시 표면 (확장 대상 — 실측)
- `terminal/panels/MacroRegimePanel.svelte` — 좌측 글랜스, 한국|미국 세로 2분할(국면·확신도·성장/물가·사분면·자산함의). `regime: RegimeQuadrantView`.
- `terminal/panels/MacroRegimeDialog.svelte` — 상세. 상단 2단(판정 + 국면 모델 합류) + 근거지표 2×2 차트(`finFsGrid mrCharts2` + MiniFinChart). KR/US 탭. `loadSeries=rt.macro.getSeries`.
- `terminal/lib/macroLens.ts` — 뷰모델 빌더(`buildRegimeView`·`buildMacroGlanceView`·`buildMacroEvidenceCards`). `terminal/panels/LeftRail.svelte` 가 조립.
- 차트 SSOT: `terminal/charts/MiniFinChart.svelte`(`card: FinCard`, `periods`, h). FinCard.series[].data=Num[](null=펜업), axis 'r', unit.

## §1. 뷰모델 — `macroLens.ts` 신규 (순수 함수, 테스트 동행)

```ts
// macro/sim/{kr,us}.json → 뷰모델. buildMacroEvidenceCards 와 같은 파일·패턴.
export interface MacroSimView {
  market: 'KR' | 'US';
  status: 'ok' | 'holdback';          // 표시 보류 시 holdback
  asOf: string; horizon: number;
  regimePath: RegimePathView | null;  // 국면경로(과거+미래 연속)
  fanCards: FinCard[];                // 변수 fan = MiniFinChart 카드(p5/p50/p95 라인)
  irf: IrfView | null;                // 충격반응 small-multiples
  scenarios: ScenarioPathView[];      // 조건부 경로(overlay)
  calibration: CalibrationBadge;      // coverage/CRPS/status
  honesty: { sampleN: number; seed: number; note: string; calibrated: boolean };
}
export function buildMacroSimView(sim: MacroSimFile, lang: Lang): MacroSimView
export function buildRegimePathSpark(rp): { history: Num[]; forward: Num[]; bandLo: Num[]; bandHi: Num[] }
```

- **fan → FinCard 매핑(신규 차트 0)**: 각 변수 fan 을 FinCard 로 — `series=[{name:'p95',data,tone:faint},{name:'p50',data,tone:solid},{name:'p5',data,tone:faint}]` + `history` 를 같은 라인 앞부분에 이어 붙임(현재 시점 기준 과거 실선 / 미래 3라인). MiniFinChart 가 이미 다중 라인·null 펜업 지원 → **밴드를 3라인으로 표현**(p5/p50/p95). 음영 밴드 fill 은 Phase 2 차트 확장(아래 §5).
- holdback(미보정·미수렴)이면 fanCards=[] + "표본/보정 부족·표시 보류" 카드 1장(기존 mrEmpty 패턴).

## §2. 좌측 패널 (MacroRegimePanel) — 미래 1줄 추가

한국|미국 각 칸 *맨 아래*에 **국면경로 미니 1줄**(빈 공간 채움 + 미래 축 완결):

```
한국    수축 38%        미국    둔화 51%
성장↓ 물가→            성장→ 물가↑
역실적 장세            후기 확장
주식↓ 채권↓ …          주식↑ 채권→ …
6M 수축 31%↗  ← 신규    6M 수축 22%↘  ← 신규
```

- `mrColPath` 클래스 1줄: `{T('6M 수축','6M rec')} {p}%` + 추세 화살표(현재 대비 ↗/↘/→). tone = bucketTone(p)(>0.5 tDn, 0.3~0.5 tWarn, <0.3 tNeu) — 기존 톤 클래스 재사용, 새 색 0.
- holdback 시 줄 생략(거짓확신 금지). 데이터는 `regimeView` 옆에 `simView` 를 LeftRail 에서 같이 derived → panel 에 `regimePath6m` prop 1개만 추가(패널은 sim 전체 모름·얇게).

## §3. 다이얼로그 (MacroRegimeDialog) — "전망 시뮬레이션" 섹션 추가

기존 `mrBody`: [상단 2단 판정+모델] → [근거지표 2×2] 사이/뒤에 **새 섹션 3블록**(세로, 스크롤 없이 한 화면 — 기존 무스크롤 규율 유지):

### 3a. 국면경로 (과거→미래 연속 SVG)
- 기존 Hamilton band SVG(`bandPoly`, 과거 24분기)를 *연장* — 현재 시점에 세로 경계선, 좌측=실선(과거 smoothedProbs), 우측=밴드(forward p + lo/hi 음영). 0~1 고정축. 1줄 캡션 "6개월 뒤 수축확률 31% (밴드 22~41%)".
- 시각문법: 과거 실선 / 미래 중앙 실선 + 상하 점선(또는 옅은 fill). 경계선 = "지금".

### 3b. 변수 팬차트 (2×2, MiniFinChart)
- `finFsGrid mrCharts2`(기존 2×2 그리드 재사용)에 fanCards. 각 카드 = 변수 1개: 과거 실선 + 미래 p50 실선 + p5/p95 옅은 라인. 카드 헤더 = 변수 라벨 + 단위 + asOf.
- 호버 = 각 h 의 p5/p50/p95 수치(MiniFinChart 호버 재사용).

### 3c. 충격반응 (IRF small-multiples)
- 충격 1개(기본 "정책금리 +100bp") 선택 → 변수별 반응 미니라인(2×2 또는 가로 스파크). 부호충돌 변수는 ⚠ 마커.
- 충격 토글(2~3 프리셋: 금리·신용·환율) = 작은 chip 버튼(기존 mrTab 패턴).

### 3d. 시나리오 overlay (선택)
- 시나리오 chip(금리인하 사이클 등) on → 3b 팬차트에 조건부 p50 점선 overlay(baseline 대비 delta 가시). "조건부 가정" 배지.

### 3e. 정직 footer (강제)
- 기존 `mrFoot` 확장: `표본 N=420 · seed 20260624 · BVAR(lag6,minnesota) · 보정: 80%밴드 coverage 0.79 · scenario≠forecast` + MACRO_ATTRIBUTION.
- calibration.status='uncalibrated' 면 섹션 헤더에 "미보정·참고용" 배지 + 팬 흐리게(opacity).

## §4. 데이터 배선 (단일 진입점)
- `rt.macro.getSim(market)` 신규 포트 → origins `macroSim` origin → `macro/sim/{kr,us}.json`(03 §4). `getSeries` 와 동형, 직접 fetch·URL·자체 캐시 금지.
- LeftRail: `macroSim = $derived(...)` 로 패널(§2 1줄)·다이얼로그(§3) 동시 공급. 다이얼로그 열릴 때만 무거운 fan 로드(lazy) — 패널 1줄은 regimePath 만(경량).
- 결정론: JSON 이 precompute(seed 고정)라 렌더는 순수 — 같은 JSON 같은 화면.

## §5. 차트 확장 결정 (음영 밴드)
- **v1**: 밴드 = p5/p50/p95 3라인(MiniFinChart 기존 기능, 신규 0). 충분히 읽힘.
- **Phase 2(선택)**: MiniFinChart 에 `band?: {lo,hi,tone}` 옵션 1개 추가(두 series 사이 area fill). 이건 *재무그래프 SSOT 변경*이라 신중 — MiniFinChart 소비처 전수 회귀(`reference_financial_graph_ssot`) + 스크린샷 눈검수 후에만. v1에서 미루는 게 정공(declutter).

## §6. 시각 일관성·눈검수 게이트
- 색·배경: 기존 터미널 토큰(`--dl-bg-base`·tone 클래스). 새 색 0. 팬 밴드 색 = 변수 라인 톤의 옅은 변형(투명도만).
- 푸시 전: KR/US × (패널 1줄 + 다이얼로그 3섹션) 스크린샷 전수 + 운영자 눈검수(`feedback_ui_rules` ★). 정량 PASS 가 디자인 디테일 못 본다.
- 공개 터미널 무중단: 미배선/미완 섹션은 커밋하되 *피처 게이트*(sim JSON 없으면 섹션 자체 미렌더) — 로컬 프리뷰 격리, 완결 단위만 push.

## §7. UI 영향 파일 요약
- `terminal/lib/macroLens.ts` — buildMacroSimView 등 + `macroLens.test.ts` 신규 테스트.
- `terminal/lib/types.ts` — MacroSimFile 타입.
- `terminal/panels/MacroRegimePanel.svelte` — mrColPath 1줄 + prop 1개.
- `terminal/panels/MacroRegimeDialog.svelte` — 전망 섹션 3a~3e.
- `terminal/panels/LeftRail.svelte` — macroSim derived + getSim 배선.
- `terminal/terminal.css` — mrColPath·전망 섹션·연속 band SVG 스타일(기존 토큰).
- runtime `data/origins`·`rt.macro` — macroSim origin/포트.
- contracts `macro.ts` — MacroSimFile 계약(필요 시).
