// 다전략 포트폴리오 백테스트 · 단일종목 위 N전략(≤3) 동시 실행 + 동일가중 고정 조합.
// 변경 이유: 다전략 캔버스(terminal-strategy-lab 01 §3). runBacktest/runPass/presets 무수정 ·
//   각 슬롯 = 기존 runBacktest 1회 호출, combo = equity 가중합에 순수 헬퍼(engine.ts) 재호출.
// 정직(01 §1.3): 한 run 의 모든 전략은 동일 candles·windowBars → 동일 startIdx·전부 non-null·
//   시작 100(워밍업 차이는 flat target=0, null 아님) → combo[i]=Σ wₛ·eqₛ[i] 는
//   "고정가중 보유합성(리밸런싱 없음)"의 정확한 표현.
// combo 는 체결 개념 0(가중 산술합) → 거래 KPI(승률·PF·노출·거래표·CSV) N.A.(01 §1.2) ·
//   UI 에서 명시적 "·". equity 메트릭(수익·MDD·Sharpe·Calmar·vs B&H)만 산출.
import { benchmarkStats, cagr, endRet, mdd, mddWindowOf, riskRatios, runBacktest, runBacktestRule } from './engine';
import type { StrategyRule } from './conditions';
import type { BtCostsBp, BtStopConfig, BtPresetKey, BtResult, BtSpecInput, Candle } from './types';

export interface StrategySlot {
	id: string;
	preset: BtPresetKey;
	params: Record<string, number>;
	color: string;
	label: string;
	rule?: StrategyRule; // 있으면 조건 빌더(커스텀·rule 프리셋) 경로 · preset 무시(전문가급 패널)
}

// combo 는 거래가 없다 → equity 기반 메트릭만(거래 KPI 는 UI 에서 명시적 "·", 01 §1.2).
export interface ComboMetrics {
	retPct: number;
	cagrPct: number | null; // windowBars < 252 → null
	mddPct: number;
	mddDays: number | null;
	sharpe: number | null; // 표본 < 60봉 → null
	sortino: number | null;
	calmar: number | null; // cagr / |mdd| · 낙폭 대비 수익(둘 중 하나 null 이면 null)
	beta: number | null;
	alphaPct: number | null;
	infoRatio: number | null;
}

export interface ComboResult {
	equity: (number | null)[]; // candles 길이, [startIdx]=100, 창 밖/결측 = null
	bhEquity: (number | null)[]; // 공통 B&H(동일비용) · 모든 슬롯 동일
	metrics: ComboMetrics;
	mddWindow: { peakIdx: number; troughIdx: number; recoverIdx: number | null } | null;
	weightsLabel: 'equal'; // 동일가중 · 자유가중은 P3(과거 곡선 보고 정하면 곡선맞춤, 04 §2.3)
}

export interface PortfolioBtResult {
	slots: { id: string; result: BtResult }[]; // 유효(non-null) 슬롯만 · runBacktest null(워밍업 부족)은 제외
	combo: ComboResult | null; // 유효 슬롯 ≥ 2 일 때만(단일은 조합 의미 없음)
	startIdx: number;
	bhEquity: (number | null)[]; // 공통 B&H(첫 유효 슬롯) · 공유 절대축 draw·strip 헤드라인용
}

/**
 * 다전략 포트폴리오 백테스트(N ≤ 3 권장). 각 슬롯은 기존 runBacktest 를 1회 호출(엔진 무수정) ·
 * N=1 경로는 단일 슬롯 result 가 현 runBacktest 와 byte 동일(회귀 0). combo 는 동일가중 가중합.
 * look-ahead 차단은 candles 절단(displaySeries)이 N전략에 구조적 상속(01 §2.2).
 */
export function runPortfolioBacktest(
	candles: Candle[],
	slots: StrategySlot[],
	opts: {
		windowBars: number;
		withCosts: boolean;
		costsBp?: BtCostsBp;
		spec?: BtSpecInput;
		oosSplit?: number;
		gate?: (number | null)[] | null; // 펀더게이트 PIT 시계열 · rule 슬롯의 fundGate 조건 소비(W2). 전 슬롯 공유(같은 종목).
		stop?: BtStopConfig | null; // 손절/익절(S2) · 전 슬롯 공유(opts 통과로 runBacktest 가 소비).
	}
): PortfolioBtResult {
	const computed = slots
		.map((s) => ({
			id: s.id,
			result: s.rule ? runBacktestRule(candles, s.rule, opts, opts.gate ?? null) : runBacktest(candles, s.preset, s.params, opts)
		}))
		.filter((x): x is { id: string; result: BtResult } => x.result != null);

	if (computed.length === 0) return { slots: [], combo: null, startIdx: 0, bhEquity: [] };

	const startIdx = computed[0].result.startIdx; // 동일 candles·windowBars → 전 슬롯 동일(검증: combo 루프 null 가드)
	const bhEquity = computed[0].result.bhEquity; // B&H 동일비용 · 슬롯 무관 공통
	const n = candles.length;
	const windowBars = n - startIdx;

	let combo: ComboResult | null = null;
	if (computed.length >= 2) {
		const w = 1 / computed.length;
		const equity: (number | null)[] = new Array(n).fill(null);
		for (let i = startIdx; i < n; i++) {
			let sum = 0;
			let ok = true;
			for (const c of computed) {
				const e = c.result.equity[i];
				if (e == null) { ok = false; break; } // 슬롯 startIdx 불일치 방어 · 한 슬롯이라도 결측이면 그 봉 combo null
				sum += w * e;
			}
			equity[i] = ok ? sum : null;
		}
		const retPct = endRet(equity);
		const ddWin = mddWindowOf(equity);
		const ratios = riskRatios(equity);
		const ben = benchmarkStats(equity, bhEquity);
		const mddPct = mdd(equity);
		const cagrPct = cagr(retPct, windowBars);
		const calmar = cagrPct != null && mddPct < 0 ? cagrPct / Math.abs(mddPct) : null;
		combo = {
			equity,
			bhEquity,
			metrics: {
				retPct,
				cagrPct,
				mddPct,
				mddDays: ddWin ? ddWin.days : null,
				sharpe: ratios.sharpe,
				sortino: ratios.sortino,
				calmar,
				beta: ben.beta,
				alphaPct: ben.alphaPct,
				infoRatio: ben.infoRatio
			},
			mddWindow: ddWin ? { peakIdx: ddWin.peakIdx, troughIdx: ddWin.troughIdx, recoverIdx: ddWin.recoverIdx } : null,
			weightsLabel: 'equal'
		};
	}

	return { slots: computed, combo, startIdx, bhEquity };
}
