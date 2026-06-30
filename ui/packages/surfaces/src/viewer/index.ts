// viewer surface 공개 표면 (§8.1 · 작업면 한 폴더, index.ts 하나가 공개 API).
// 셸(landing /viewer route·terminal hosts·lab/viewer-*·CompanyQuickSearch·dev AskDrawer)이 소비하는
// 컴포넌트 + 데이터레이어 심볼만 공개. 내부 부품(CellContent·FinanceStatementPane·AskDrawer 본진 등)은
// 비공개 · 트리 내부 상대 import 로만 접근. 모든 export 는 외부 실소비 import 로 검증된 심볼.
// 정량재무제표 raw 행은 셸이 provideFinanceRows 로 주입(financeQuery seam · 차트 hyparquet 캐시 공유, DuckDB 제거).

// ── 컴포넌트 (외부 소비: route·terminal hosts·lab) ──
export { default as ViewerStudio } from './components/ViewerStudio.svelte';
export { default as FinanceDialog } from './components/FinanceDialog.svelte';
export { default as PanelMatrix } from './components/PanelMatrix.svelte';
export { default as PanelTocTree } from './components/PanelTocTree.svelte';
export { default as TimelineRibbon } from './components/TimelineRibbon.svelte';
export { default as CommandPalette } from './components/CommandPalette.svelte';
export { default as CompanySearch } from './components/CompanySearch.svelte';
export { default as ComparisonMatrix } from './components/ComparisonMatrix.svelte';
export { default as GiscusPanel } from './components/GiscusPanel.svelte';

// ── 데이터레이어 (브라우저 parquet read·검색·재무·비교·AI 보조) ──
export { loadPanelBundle } from './lib/panelLoad';
export type { PanelBundle, PanelRow, PanelTocResponse } from './lib/types';
export { loadCompanies, resolveCompanies, type Co } from './lib/companyNames';
export { plainText, search, buildIndexChunked, type SearchHit, type SearchIndex } from './lib/searchIndex';
export { buildEvidencePack, highlightParts, type EvidenceItem } from './lib/searchEvidence';
export { loadIntentModel, queryScope, type IntentModel } from './lib/queryCanon';
export { composeAnswer } from './lib/answerCompose';
export { loadCompanyFinanceSignals } from './lib/financeAsk';
export { translateAnswer, translatorSupported, TARGET_LANGS, type TargetLang } from './lib/translate';
export { deriveActions, executeAction, type ViewerAction, type ViewerApi } from './lib/viewerActions';
export {
	DEFAULT_MODEL_ID,
	isKnownModel,
	isModelCached,
	routeChat,
	stripEcho,
	warmEngine,
	webgpuUsable,
	webgpuAvailable,
	WEBLLM_MODELS,
	narrateSignals,
	type AskEvidence,
	type ChatTurn,
	type Provider
} from './lib/webllm';
export { detectOllama } from './lib/ollama';
export { analyzeViewport, financeSignals, type FinanceSignal, type CellFacet } from './lib/diff';
export { buildCompareBoard, commonPeriods } from './lib/compare';
export { normalizeCompareTargets } from './lib/compare/targets';
export { scanDeepRowsChunked, type DeepSearchRow } from './lib/deepSearch';
export { checkBrowserAiAvailability, runBrowserAiPrompt, type BrowserAiStatus } from './lib/browserAi';
export { analyzeEvidencePack, attachBrowserAiText, type ViewerAnalysis } from './lib/viewerAnalyst';
export { marketForCode } from './lib/dartUrl';
export { panelToCsv, financeToExcel, downloadText, downloadBlob } from './lib/dataExport';
// table-export · ExportPort 다리(셸이 publicExportPort.exportShared 로 주입) + 선택 스토어 타입.
export {
	createSelectionStore,
	deriveWorkbookInput,
	exportInputToWorkbookBytes,
	type SelectionStore,
	type SheetSelection,
	type ExportMode
} from './lib/export/selection.svelte';
export { buildWorkbook, type SheetInput } from './lib/xlsx';
export { loadFinanceStatement, financeAvailability, provideFinanceRows } from './lib/finance/financeQuery';
export { type RawFinanceRow } from './lib/finance/financePivot';
export { KIND_LABELS, type FinanceKind, type FinanceScope, type FinanceStatement } from './lib/finance/types';
