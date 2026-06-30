// 백테스트 도메인 compat barrel · 기존 7 importer 무수정(03 §0.5.3). 분할: types(계약)·presets(전략)·engine(체결).
export { BT_COSTS, BT_ENGINE_VERSION } from './types';
export type {
	BtPresetKey,
	BtParamDef,
	BtPresetDef,
	BtCostsBp,
	BtStopConfig,
	BtTrade,
	BtWarning,
	BtMetrics,
	BtRunSpec,
	BtResult,
	BtSpecInput,
	BtFullRef
} from './types';
export { BT_PRESETS } from './presets';
export { runBacktest, runBacktestRule } from './engine';
// 순수 equity 헬퍼 · 유니버스 백테스터(scan/universe) 공유(05 §1: 헬퍼 6종만 재사용, candles-aligned 엔진은 비공유).
export { mdd, mddWindowOf, riskRatios, benchmarkStats, endRet, cagr } from './engine';
export { runPortfolioBacktest } from './portfolio';
export type { StrategySlot, ComboMetrics, ComboResult, PortfolioBtResult } from './portfolio';
// 대기 프리플라이트 · 전략 0개일 때 실행 전 B&H 기준선·데이터품질·비용 계산(중앙 하단 BacktestPreflight).
export { backtestPreflight } from './preflight';
export type { BtPreflight } from './preflight';
// 조건 빌더(전문가급 커스텀 패널) · 지표 카탈로그·룰 프리셋·평가.
export { SERIES_CATALOG, RULE_PRESETS, OP_LABEL, evalRule, evalCondition, ruleWarmup, FAMILY_LABEL, FAMILY_ORDER } from './conditions';
export type { SeriesKey, SeriesDef, Op, Condition, StrategyRule, RulePreset, RuleEval } from './conditions';
export type { PresetFamily } from './types';
// 펀더게이트(W2 간판②) · PIT 시계열 빌더 + 룰 게이트 사용 가드.
export { buildGateSeries, ruleUsesGate } from './gate';
export type { GateRow } from './gate';
