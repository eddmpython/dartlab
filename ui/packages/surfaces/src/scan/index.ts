// scan surface 공개 표면 (§8.1 · 작업면 한 폴더, index.ts 하나가 공개 API).
// 데이터 탐색기·SQL 노트북·스크리너 · landing /scan 라우트(컴포지션 루트)가 마운트. DuckDB-WASM 은 셸이
// provideScanDuckDb 로 주입(seam, SvelteKit/Vite 결합 절제). 숫자 포맷은 @dartlab/ui-format 공유패키지 경유(복사 제거 완료). Sparkline 은 scan canonical + ./scan/viz 얇은 subpath 노출(landing 복사 제거 완료).
// 외부 실소비(routes/scan·companyLive·scanRuntime.worker) import 로 검증된 심볼만 공개.

// ── 컴포넌트 ──
export { default as Grid } from './Grid.svelte';
export { default as ColumnGroupBar } from './ColumnGroupBar.svelte';
export { default as PresetModal } from './PresetModal.svelte';
export { default as CellTooltip } from './CellTooltip.svelte';
export { default as Distribution } from './Distribution.svelte';
export { default as InsightsFeed } from './InsightsFeed.svelte';
export { default as SavedSets } from './SavedSets.svelte';
export { default as Detail } from './Detail.svelte';
export { default as DataExplorer } from './DataExplorer.svelte';
// 유니버스 백테스터(terminal-strategy-lab 간판① · 전종목 크로스섹셔널, scan 의 자연 종착).
export { default as UniverseBacktester } from './universe/UniverseBacktester.svelte';

// ── duckdb 쿼리 엔진 + seam ──
export {
	ensureDuckDb,
	loadCompanyChanges,
	provideScanDuckDb,
	type DartDb,
	type CompanyChange,
	type PriceMetrics,
	type ValuationMetrics,
	type DbState
} from './duckSql';
export { loadFinanceLiteRuntime, loadCompanyFinanceLitePeriods } from './financeLiteRuntime';

// ── 페이로드·메트릭·프리셋·타입 ──
export { encodeScanPayload, decodeScanPayload } from './url';
export { DEFAULT_COLUMNS, METRICS_BY_KEY, PINNED_COLUMNS, type MetricGroup } from './metrics';
export { PRESETS_BY_ID, type Preset, type RuntimeLoader } from './presets';
export type { SavedColumnSet, ScanNode, FilterCond, SortKey } from './types';

// ── DART(KR) + EDGAR(US) 동시 조회 ──
// 무차원(비율·등급)만 시장을 가로질러 비교한다. 절대금액·상대지표는 시장 안에서만.
export { loadEdgarNodes } from './edgarNodes';
export {
	MARKET_CURRENCY,
	MARKET_LABEL,
	cellApplicability,
	crossMarketComparable,
	inScope,
	nodeMarket,
	percentilesByMarket,
	sortAllowed,
	sortBlockedReason,
	US_FIELDS,
	type Market,
	type MarketScope
} from './marketScope';

// ── 판정격자 · 조건 x 종목 3-state (PASS/FAIL/UNKNOWN) 판정의 SSOT ──
export { default as VerdictRibbon } from './VerdictRibbon.svelte';
export {
	buildFunnel,
	buildVerdictGrid,
	condLabel,
	coverageStats,
	evalVerdict,
	hasValue,
	nearMiss,
	normalizeNumeric,
	relaxThreshold,
	type CoverageStat,
	type FunnelStep,
	type RowVerdict,
	type Verdict,
	type VerdictGrid
} from './verdict';
