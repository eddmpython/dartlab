// 백테스트 체결 커널 · 변경 이유: 체결/비용/지표 의미(전략 추가와 분리, 03 §0.5.3).
// 체결 모델: 신호 t일 종가 확정 → t+1일 시가 체결(target 1봉 shift = look-ahead 구조적 불가).
// 거래정지(v=0/o=0) 봉은 체결 자동 이연. B&H = 같은 엔진에 target≡1 주입(공정 비교 코드 보장).
import { BT_PRESETS } from './presets';
import { evalRule, ruleWarmup, type StrategyRule } from './conditions';
import { BT_COSTS, BT_ENGINE_VERSION } from './types';
import type { BtCostsBp, BtStopConfig, BtPresetKey, BtResult, BtRunSpec, BtSplitMetrics, BtSpecInput, BtTrade, BtWarning, Candle } from './types';

interface Costs {
	comm: number;
	tax: number;
	slip: number;
}
const ZERO_COSTS: Costs = { comm: 0, tax: 0, slip: 0 };
const toCosts = (bp: BtCostsBp = BT_COSTS): Costs => ({ comm: bp.commissionBp / 1e4, tax: bp.sellTaxBp / 1e4, slip: bp.slippageBp / 1e4 });

interface PassOut {
	equity: (number | null)[];
	trades: BtTrade[];
	heldBars: number;
	deferredBars: number;
}

// 단일 패스 · target[i-1] 을 i 봉 시가에 적용 (1봉 shift). 4,000봉 < 1ms.
function runPass(candles: Candle[], target: Int8Array, startIdx: number, k: Costs, stop: BtStopConfig | null = null): PassOut {
	const n = candles.length;
	const equity: (number | null)[] = new Array(n).fill(null);
	const trades: BtTrade[] = [];
	let pos = 0;
	let cash = 100;
	let shares = 0;
	let entryCash = 0;
	let entryIdx = -1;
	let entryPx = 0;
	let heldBars = 0;
	let deferredBars = 0;
	let maePct = 0;
	let mfePct = 0;
	let stopPx: number | null = null;
	let takePx: number | null = null;
	equity[startIdx] = 100;
	for (let i = startIdx + 1; i < n; i++) {
		const b = candles[i];
		const want = target[i - 1];
		if (want !== pos) {
			if (b.v > 0 && b.o > 0) {
				if (want === 1) {
					const px = b.o * (1 + k.slip);
					entryPx = px * (1 + k.comm);
					entryCash = cash;
					shares = cash / entryPx;
					cash = 0;
					pos = 1;
					entryIdx = i;
					maePct = 0;
					mfePct = 0;
					stopPx = stop?.lossPct ? entryPx * (1 - stop.lossPct / 100) : null;
					takePx = stop?.gainPct ? entryPx * (1 + stop.gainPct / 100) : null;
				} else {
					const px = b.o * (1 - k.slip);
					const exitPx = px * (1 - k.comm - k.tax);
					cash = shares * exitPx;
					shares = 0;
					pos = 0;
					trades.push({
						entryT: candles[entryIdx].t,
						exitT: b.t,
						entryPx,
						exitPx,
						retPct: (cash / entryCash - 1) * 100,
						holdDays: i - entryIdx,
						open: false,
						exitReason: 'signal',
						entryDeferredBars: 0,
						maePct,
						mfePct
					});
				}
			} else {
				deferredBars++; // 신호 변경을 원했으나 거래정지(v=0/o=0) · 다음 거래가능 봉까지 이연(감사)
			}
		}
		// 손절/익절 인트라바(gated) · 진입 봉 다음부터(i>entryIdx): 같은 봉 진입+청산은 인트라바 순서 미지 → look-ahead 낙관 차단.
		// 갭 관통 시 stopPx/takePx 가 아닌 그 봉 시가로 체결(낙관 차단): 손절 min(stopPx,b.o)·익절 max(takePx,b.o). 보수: 손절 우선.
		if (pos === 1 && i > entryIdx && stopPx != null && b.l <= stopPx) {
			const exitPx = Math.min(stopPx, b.o) * (1 - k.slip) * (1 - k.comm - k.tax);
			cash = shares * exitPx; shares = 0; pos = 0;
			trades.push({ entryT: candles[entryIdx].t, exitT: b.t, entryPx, exitPx, retPct: (cash / entryCash - 1) * 100, holdDays: i - entryIdx, open: false, exitReason: 'stop', entryDeferredBars: 0, maePct, mfePct });
		} else if (pos === 1 && i > entryIdx && takePx != null && b.h >= takePx) {
			const exitPx = Math.max(takePx, b.o) * (1 - k.slip) * (1 - k.comm - k.tax);
			cash = shares * exitPx; shares = 0; pos = 0;
			trades.push({ entryT: candles[entryIdx].t, exitT: b.t, entryPx, exitPx, retPct: (cash / entryCash - 1) * 100, holdDays: i - entryIdx, open: false, exitReason: 'take', entryDeferredBars: 0, maePct, mfePct });
		}
		if (pos === 1) {
			heldBars++;
			const lowRet = (b.l / entryPx - 1) * 100;
			const highRet = (b.h / entryPx - 1) * 100;
			if (lowRet < maePct) maePct = lowRet;
			if (highRet > mfePct) mfePct = highRet;
		}
		equity[i] = cash + shares * b.c;
	}
	if (pos === 1) {
		// 미청산 · 마지막 종가에 가상 매도비용 차감 평가(finalMark convention)
		const last = candles[n - 1];
		const virtual = shares * last.c * (1 - k.slip) * (1 - k.comm - k.tax);
		trades.push({
			entryT: candles[entryIdx].t,
			exitT: null,
			entryPx,
			exitPx: null,
			retPct: (virtual / entryCash - 1) * 100,
			holdDays: n - 1 - entryIdx,
			open: true,
			exitReason: 'finalMark',
			entryDeferredBars: 0,
			maePct,
			mfePct
		});
	}
	// entryDeferredBars 는 진입-청산 분리 모델상 청산 시 역산이 어려워 0 (전체 deferredBars 로 감사 · 03 §0.5.4).
	return { equity, trades, heldBars, deferredBars };
}

// 순수 헬퍼(mdd·mddWindowOf·riskRatios·benchmarkStats·endRet·cagr)는 base-independent ·
// portfolio.ts combo equity 가 재호출(03 §3 runPortfolioBacktest). export 는 additive(동작 무변경).
export function mdd(equity: (number | null)[]): number {
	let peak = -Infinity;
	let worst = 0;
	for (const e of equity) {
		if (e == null) continue;
		if (e > peak) peak = e;
		else if (peak > 0) worst = Math.min(worst, (e / peak - 1) * 100);
	}
	return worst;
}

// 최대 낙폭 창 · 피크·저점·회복(피크 재돌파) 인덱스 + 최장 수면 거래일. 에쿼티 페인 음영·KPI 용.
export function mddWindowOf(equity: (number | null)[]): { peakIdx: number; troughIdx: number; recoverIdx: number | null; days: number } | null {
	let peakIdx = -1;
	let peak = -Infinity;
	let worst = 0;
	let wPeak = -1;
	let wTrough = -1;
	for (let i = 0; i < equity.length; i++) {
		const e = equity[i];
		if (e == null) continue;
		if (e > peak) { peak = e; peakIdx = i; }
		else if (peak > 0) {
			const dd = (e / peak - 1) * 100;
			if (dd < worst) { worst = dd; wPeak = peakIdx; wTrough = i; }
		}
	}
	if (wPeak < 0) return null;
	let recoverIdx: number | null = null;
	const ref = equity[wPeak]!;
	for (let i = wTrough + 1; i < equity.length; i++) {
		const e = equity[i];
		if (e != null && e >= ref) { recoverIdx = i; break; }
	}
	let last = equity.length - 1;
	while (last > wPeak && equity[last] == null) last--;
	return { peakIdx: wPeak, troughIdx: wTrough, recoverIdx, days: (recoverIdx ?? last) - wPeak };
}

// 일수익률 기반 연환산 Sharpe(rf=0)·Sortino · 표본 < 60봉이면 null (소표본 거짓말 차단).
export function riskRatios(equity: (number | null)[]): { sharpe: number | null; sortino: number | null } {
	const rets: number[] = [];
	let prev: number | null = null;
	for (const e of equity) {
		if (e == null) continue;
		if (prev != null && prev > 0) rets.push(e / prev - 1);
		prev = e;
	}
	if (rets.length < 60) return { sharpe: null, sortino: null };
	const mean = rets.reduce((a, r) => a + r, 0) / rets.length;
	const varAll = rets.reduce((a, r) => a + (r - mean) * (r - mean), 0) / rets.length;
	const downs = rets.filter((r) => r < 0);
	const varDown = downs.length ? downs.reduce((a, r) => a + r * r, 0) / rets.length : 0;
	const ann = Math.sqrt(252);
	const sharpe = varAll > 0 ? (mean / Math.sqrt(varAll)) * ann : null;
	const sortino = varDown > 0 ? (mean / Math.sqrt(varDown)) * ann : null;
	return { sharpe, sortino };
}

// 벤치마크(B&H) 상대 통계 · 베타·연환산 알파·정보비율. 같은 인덱스에서 둘 다 유효한 일수익률 쌍만.
// 서술적(단일창) 지표라 표본이 받침(§0.5.9-C). 표본 < 60봉 → 전부 null(소표본 거짓말 차단, riskRatios 와 동일 하한).
export function benchmarkStats(stratEq: (number | null)[], bhEq: (number | null)[]): { beta: number | null; alphaPct: number | null; infoRatio: number | null } {
	const s: number[] = [];
	const b: number[] = [];
	let ps: number | null = null;
	let pb: number | null = null;
	for (let i = 0; i < stratEq.length; i++) {
		const es = stratEq[i];
		const eb = bhEq[i];
		if (es != null && eb != null) {
			if (ps != null && pb != null && ps > 0 && pb > 0) { s.push(es / ps - 1); b.push(eb / pb - 1); }
			ps = es;
			pb = eb;
		} else { ps = es ?? ps; pb = eb ?? pb; }
	}
	if (s.length < 60) return { beta: null, alphaPct: null, infoRatio: null };
	const n = s.length;
	const ms = s.reduce((a, x) => a + x, 0) / n;
	const mb = b.reduce((a, x) => a + x, 0) / n;
	let cov = 0;
	let varb = 0;
	for (let i = 0; i < n; i++) { cov += (s[i] - ms) * (b[i] - mb); varb += (b[i] - mb) * (b[i] - mb); }
	const beta = varb > 0 ? cov / varb : null;
	const alphaPct = beta != null ? (ms - beta * mb) * 252 * 100 : null;
	// 정보비율 · 액티브 일수익률(전략 − B&H) 평균 / 표준편차 × √252
	const act = s.map((x, i) => x - b[i]);
	const ma = act.reduce((a, x) => a + x, 0) / n;
	const va = act.reduce((a, x) => a + (x - ma) * (x - ma), 0) / n;
	const infoRatio = va > 0 ? (ma / Math.sqrt(va)) * Math.sqrt(252) : null;
	return { beta, alphaPct, infoRatio };
}

export function endRet(equity: (number | null)[]): number {
	for (let i = equity.length - 1; i >= 0; i--) if (equity[i] != null) return (equity[i]! / 100 - 1) * 100;
	return 0;
}

export function cagr(retPct: number, windowBars: number): number | null {
	if (windowBars < 252) return null;
	return (Math.pow(1 + retPct / 100, 252 / windowBars) - 1) * 100;
}

// 무수정주가 분할 의심 · 전봉 종가/당봉 시가 비가 정수배(상대 ±2%) & ≥1.5배.
function findSplitSuspect(candles: Candle[], startIdx: number): string | null {
	for (let i = Math.max(1, startIdx + 1); i < candles.length; i++) {
		const prev = candles[i - 1].c;
		const o = candles[i].o;
		if (!(prev > 0) || !(o > 0)) continue;
		const r = prev / o;
		const rr = r >= 1 ? r : 1 / r;
		const near = Math.round(rr);
		if (rr >= 1.5 && near >= 2 && Math.abs(rr - near) / near < 0.02) return candles[i].t;
	}
	return null;
}

// reconcile/무결성 가드(03 §0.5.4) · single-array 모델이라 trade↔equity 분기는 구조적 불가지만,
// 데이터 손상(o=0·c=0·entryCash=0)이 만드는 NaN/Infinity 를 차단. 위반 시 status=invalid → UI 지표 미노출.
function reconcileOk(equity: (number | null)[], trades: BtTrade[], retPct: number): boolean {
	if (!Number.isFinite(retPct)) return false;
	for (const e of equity) if (e != null && !Number.isFinite(e)) return false;
	for (const t of trades) if (!Number.isFinite(t.retPct) || (t.exitPx != null && !Number.isFinite(t.exitPx))) return false;
	return true;
}

// equity 하위슬라이스 [fromIdx..toIdx] 의 재기준 성과 · base-independent 헬퍼 재사용(03 §0.5.9-A).
function splitMetrics(equity: (number | null)[], fromIdx: number, toIdx: number, tradeCount: number): BtSplitMetrics {
	let first: number | null = null;
	let last: number | null = null;
	for (let i = fromIdx; i <= toIdx; i++) {
		const e = equity[i];
		if (e == null) continue;
		if (first == null) first = e;
		last = e;
	}
	const sub = equity.slice(fromIdx, toIdx + 1);
	const retPct = first != null && last != null && first > 0 ? (last / first - 1) * 100 : 0;
	return { retPct, sharpe: riskRatios(sub).sharpe, mddPct: mdd(sub), tradeCount, bars: toIdx - fromIdx };
}

// OOS 학습/검증 분할 · 고정 전략을 split 지점 전후로 나눠 성과 산출(walk-forward 아님, §0.5.9-A).
function computeOos(
	equity: (number | null)[],
	trades: BtTrade[],
	candles: Candle[],
	startIdx: number,
	n: number,
	frac: number
): { splitIdx: number; splitT: string; train: BtSplitMetrics; test: BtSplitMetrics } | null {
	if (!(frac > 0 && frac < 1)) return null;
	const splitIdx = startIdx + Math.floor((n - 1 - startIdx) * frac);
	if (splitIdx <= startIdx || splitIdx >= n - 1) return null;
	const splitT = candles[splitIdx].t;
	const trainCount = trades.filter((t) => t.entryT <= splitT).length;
	const testCount = trades.filter((t) => t.entryT > splitT).length;
	return {
		splitIdx,
		splitT,
		train: splitMetrics(equity, startIdx, splitIdx, trainCount),
		test: splitMetrics(equity, splitIdx, n - 1, testCount)
	};
}

/** 백테스트 실행 · 전략(선택 비용)·전략(비용 OFF, 비용드래그용)·B&H(동일 비용) 3패스. null = candles 부족. */
interface StrategyForSpec { id: BtPresetKey | 'custom'; params: Record<string, number> }
type BtOpts = { windowBars: number; withCosts: boolean; costsBp?: BtCostsBp; spec?: BtSpecInput; oosSplit?: number; stop?: BtStopConfig | null };

/** 6 레거시 프리셋(종가 신호) 경로 · 기존 계약 무변경. */
export function runBacktest(candles: Candle[], preset: BtPresetKey, params: Record<string, number>, opts: BtOpts): BtResult | null {
	const def = BT_PRESETS.find((d) => d.key === preset);
	if (!def) return null;
	if (candles.length < def.warmup(params) + 5) return null;
	// 신호는 전체 이력로 계산(워밍업 자동 확보), 체결·평가는 평가창 안에서만.
	return runBacktestCore(candles, def.signal(candles.map((c) => c.c), params), opts, { id: preset, params });
}

/** 조건 빌더 룰(커스텀 조립 + OHLCV rule 프리셋) 경로 · target 을 evalRule 로 산출(전문가급 패널).
 *  gate = 펀더게이트 PIT 시계열(있으면 fundGate 조건 소비, 공시 전 봉 진입차단 · look-ahead 0, W2 간판②). */
export function runBacktestRule(
	candles: Candle[],
	rule: StrategyRule,
	opts: BtOpts,
	gate: (number | null)[] | null = null
): BtResult | null {
	if (candles.length < ruleWarmup(rule) + 5) return null;
	return runBacktestCore(candles, evalRule(candles, rule, gate).target, opts, { id: 'custom', params: {} });
}

function runBacktestCore(candles: Candle[], target: Int8Array, opts: BtOpts, specStrat: StrategyForSpec): BtResult | null {
	const n = candles.length;
	const startIdx = Math.max(0, n - Math.max(2, opts.windowBars));
	const windowBars = n - startIdx;
	const full = toCosts(opts.costsBp);
	const costs = opts.withCosts ? full : ZERO_COSTS;

	const strat = runPass(candles, target, startIdx, costs, opts.stop ?? null);
	const stratOn = opts.withCosts ? strat : runPass(candles, target, startIdx, full, opts.stop ?? null);
	const stratOff = opts.withCosts ? runPass(candles, target, startIdx, ZERO_COSTS, opts.stop ?? null) : strat;
	const hold = new Int8Array(n).fill(1);
	const bhPass = runPass(candles, hold, startIdx, costs);

	const retPct = endRet(strat.equity);
	const closedAndOpen = strat.trades;
	// 승률·손익비는 실현(청산) 거래만 · 미청산 finalMark 의 평가손익이 분자/분모를 오염하지 않게(거래표엔 미청산 행 유지).
	const closed = closedAndOpen.filter((t) => !t.open);
	const wins = closed.filter((t) => t.retPct > 0);
	const losses = closed.filter((t) => t.retPct < 0);
	const gainSum = wins.reduce((a, t) => a + t.retPct, 0);
	const lossSum = Math.abs(losses.reduce((a, t) => a + t.retPct, 0));
	const ddWin = mddWindowOf(strat.equity);
	const ratios = riskRatios(strat.equity);
	const bhRatios = riskRatios(bhPass.equity);
	const ben = benchmarkStats(strat.equity, bhPass.equity);

	const warnings: BtWarning[] = [];
	if (closedAndOpen.length < 10) warnings.push({ kind: 'fewTrades' });
	if (windowBars < 120) warnings.push({ kind: 'shortRange' });
	const splitDate = findSplitSuspect(candles, startIdx);
	if (splitDate) warnings.push({ kind: 'splitSuspect', date: splitDate });
	if (!opts.withCosts) warnings.push({ kind: 'costsOff' });

	const bhRet = endRet(bhPass.equity);
	const fullBp = opts.costsBp ?? BT_COSTS;
	const runSpec: BtRunSpec | undefined = opts.spec
		? {
				engineVersion: BT_ENGINE_VERSION,
				symbol: { code: opts.spec.code, name: opts.spec.name, market: opts.spec.market },
				dataSource: opts.spec.dataSource ?? 'gov/prices',
				dataAsOf: candles[n - 1].t,
				adjusted: opts.spec.adjusted ?? false,
				dividend: 'excluded',
				range: { from: candles[startIdx].t, to: candles[n - 1].t, bars: windowBars },
				strategy: { id: specStrat.id, params: specStrat.params },
				costs: { enabled: opts.withCosts, commissionBp: fullBp.commissionBp, sellTaxBp: fullBp.sellTaxBp, slippageBp: fullBp.slippageBp },
				benchmark: { kind: 'buyAndHold', sameCosts: true }
			}
		: undefined;
	const status: 'ok' | 'invalid' = reconcileOk(strat.equity, closedAndOpen, retPct) ? 'ok' : 'invalid';
	return {
		status,
		startIdx,
		equity: strat.equity,
		bhEquity: bhPass.equity,
		trades: closedAndOpen,
		metrics: {
			retPct,
			cagrPct: cagr(retPct, windowBars),
			mddPct: mdd(strat.equity),
			mddDays: ddWin ? ddWin.days : null,
			sharpe: ratios.sharpe,
			sortino: ratios.sortino,
			winRatePct: closed.length ? (wins.length / closed.length) * 100 : null,
			profitFactor: lossSum > 0 ? gainSum / lossSum : null,
			tradeCount: closedAndOpen.length,
			avgTradePct: closedAndOpen.length ? closedAndOpen.reduce((a, t) => a + t.retPct, 0) / closedAndOpen.length : null,
			bestTradePct: closedAndOpen.length ? Math.max(...closedAndOpen.map((t) => t.retPct)) : null,
			worstTradePct: closedAndOpen.length ? Math.min(...closedAndOpen.map((t) => t.retPct)) : null,
			avgHoldDays: closedAndOpen.length ? closedAndOpen.reduce((a, t) => a + t.holdDays, 0) / closedAndOpen.length : null,
			exposurePct: (strat.heldBars / Math.max(1, windowBars - 1)) * 100,
			costDragPct: endRet(stratOn.equity) - endRet(stratOff.equity),
			beta: ben.beta,
			alphaPct: ben.alphaPct,
			infoRatio: ben.infoRatio
		},
		bh: { retPct: bhRet, cagrPct: cagr(bhRet, windowBars), mddPct: mdd(bhPass.equity), sharpe: bhRatios.sharpe },
		mddWindow: ddWin ? { peakIdx: ddWin.peakIdx, troughIdx: ddWin.troughIdx, recoverIdx: ddWin.recoverIdx } : null,
		deferredBars: strat.deferredBars,
		warnings,
		runSpec,
		oos: opts.oosSplit ? computeOos(strat.equity, closedAndOpen, candles, startIdx, n, opts.oosSplit) : null
	};
}
