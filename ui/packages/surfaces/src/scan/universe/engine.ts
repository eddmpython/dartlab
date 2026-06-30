// 유니버스 크로스섹셔널 백테스트 엔진 · 매 리밸 전종목 랭킹 → 분위 보유 → 재랭킹. holdings 회계.
// terminal-strategy-lab 05 §2. 단일종목 runPass(candles-aligned) 비공유 · 순수 equity 헬퍼 6종만 재사용.
// ★U-G1 이중실행 밴드: unknown 폐지를 0손실(낙관)/−100%(보수) 2회 → 밴드=진짜 unknown 의존도.
//   합병/코드변경 = last-close(0, 밴드 제외). decisionYm<fillYm 불변(look-ahead 차단).

import { mdd, riskRatios, endRet } from '../../terminal/lib/backtest';
import { eligibleRanked, assignBuckets } from './ranking';
import type { UniverseBtResult, UniverseRow, UniverseRun, UniverseSpec } from './types';

type Outcome = { v: number } | 'merger' | 'unknown'; // 한 종목의 그 기간 결과
type Mode = 'optimistic' | 'conservative';

/** null forward(중간 리밸의 미관측 다음달) = 폐지 → 사유별. retFwd 있으면 그대로. */
function outcomeOf(row: UniverseRow, rebalance: 'M' | 'Q'): Outcome {
	const fwd = rebalance === 'M' ? row.retFwd1m : row.retFwd3m;
	if (fwd != null && Number.isFinite(fwd)) return { v: fwd };
	return row.delistReason === 'unknown' ? 'unknown' : 'merger'; // merger/codeChange/edge = last-close
}

function applyOutcome(o: Outcome, mode: Mode): number {
	if (o === 'merger') return 0; // last-close(밴드 제외)
	if (o === 'unknown') return mode === 'conservative' ? -1 : 0; // ★이중실행 분기
	return o.v;
}

function meanReturn(outcomes: Outcome[], mode: Mode): number {
	if (!outcomes.length) return 0;
	let s = 0;
	for (const o of outcomes) s += applyOutcome(o, mode);
	return s / outcomes.length;
}

/** 리밸 ym 축 · 윈도 내 정렬 unique ym, M=매월·Q=3개월 간격. */
function rebalanceAxis(allYms: string[], spec: UniverseSpec): string[] {
	const inWin = allYms.filter((y) => y >= spec.windowFrom && y <= spec.windowTo).sort();
	if (spec.rebalance === 'M') return inWin;
	return inWin.filter((_, i) => i % 3 === 0); // 분기(3개월) · retFwd3m 정렬
}

/** 한 청산가정(mode) NAV 회계 · 분위별·EW. perPeriodBuckets/perPeriodEW 는 양 모드 공유(선정 동일). */
function runMode(
	ymAxis: string[],
	perPeriodBuckets: Outcome[][][], // [period][bucket][member]
	perPeriodEW: Outcome[][], // [period][member]
	buckets: number,
	mode: Mode
): UniverseRun {
	const navByBucket: Record<number, number[]> = {};
	for (let b = 1; b <= buckets; b++) navByBucket[b] = [100];
	const ewBench: number[] = [100];
	for (let i = 0; i < ymAxis.length - 1; i++) {
		for (let b = 1; b <= buckets; b++) {
			const r = meanReturn(perPeriodBuckets[i]?.[b - 1] ?? [], mode);
			navByBucket[b].push(navByBucket[b][i] * (1 + r));
		}
		ewBench.push(ewBench[i] * (1 + meanReturn(perPeriodEW[i] ?? [], mode)));
	}
	const top = navByBucket[1];
	const bottom = navByBucket[buckets];
	const spread = top.map((v, i) => v - bottom[i]);
	const topRet = endRet(top);
	return {
		navByBucket,
		ewBench,
		spread,
		metrics: {
			topRetPct: topRet,
			topMddPct: mdd(top),
			topSharpe: riskRatios(top).sharpe,
			spreadEndPct: spread[spread.length - 1] ?? 0,
			avgTurnover: 0 // runUniverse 에서 채움(선정 공유)
		}
	};
}

/** 유니버스 백테스트 · 패널 전체 행 + spec → 이중실행 밴드 결과. */
export function runUniverse(rows: UniverseRow[], spec: UniverseSpec): UniverseBtResult {
	// ym → 그 달 행들(code→row) 인덱스
	const byYm = new Map<string, Map<string, UniverseRow>>();
	for (const r of rows) {
		if (!byYm.has(r.ym)) byYm.set(r.ym, new Map());
		byYm.get(r.ym)!.set(r.stockCode, r);
	}
	const ymAxis = rebalanceAxis([...byYm.keys()], spec);
	if (ymAxis.length < 4) {
		return blankResult(ymAxis); // 표본 부족
	}

	const perPeriodBuckets: Outcome[][][] = [];
	const perPeriodEW: Outcome[][] = [];
	const rebalances: UniverseBtResult['rebalances'] = [];
	const unknownExitCodes = new Set<string>();
	const mergerExitCodes = new Set<string>();
	let prevTop: Set<string> | null = null;
	let turnoverSum = 0;
	let turnoverN = 0;

	for (let i = 0; i < ymAxis.length - 1; i++) {
		const decisionYm = ymAxis[i];
		const fillYm = ymAxis[i + 1]; // decisionYm < fillYm 불변
		const rowMap = byYm.get(decisionYm)!;
		const rowsAt = [...rowMap.values()];
		const ranked = eligibleRanked(rowsAt, spec.rankSignal, spec.liquidityPctile);
		const bucketOf = assignBuckets(ranked, spec.buckets);

		const bucketOutcomes: Outcome[][] = Array.from({ length: spec.buckets }, () => []);
		const ewOutcomes: Outcome[] = [];
		const bucketCodes: { bucket: number; codes: string[] }[] = Array.from({ length: spec.buckets }, (_, b) => ({
			bucket: b + 1,
			codes: []
		}));
		let mergerExits = 0;
		let unknownExits = 0;
		for (const { code } of ranked) {
			const row = rowMap.get(code)!;
			const o = outcomeOf(row, spec.rebalance);
			const b = bucketOf.get(code)!;
			bucketOutcomes[b - 1].push(o);
			bucketCodes[b - 1].codes.push(code);
			ewOutcomes.push(o);
			// outcomeOf 는 null forward(=exit) 일 때만 merger/unknown 반환 → 그대로 카운트(중간 리밸이라 none-edge 없음).
			if (o === 'unknown') {
				unknownExits++;
				unknownExitCodes.add(code);
			} else if (o === 'merger') {
				mergerExits++;
				mergerExitCodes.add(code);
			}
		}
		perPeriodBuckets.push(bucketOutcomes);
		perPeriodEW.push(ewOutcomes);

		const top = new Set(bucketCodes[0].codes);
		if (prevTop && top.size) {
			let changed = 0;
			for (const c of top) if (!prevTop.has(c)) changed++;
			turnoverSum += changed / top.size;
			turnoverN++;
		}
		prevTop = top;

		rebalances.push({
			ym: decisionYm,
			decisionYm,
			fillYm,
			byBucket: bucketCodes,
			turnover: turnoverN ? turnoverSum / turnoverN : 0,
			nEligible: ranked.length,
			mergerExits,
			unknownExits
		});
	}

	const avgTurnover = turnoverN ? turnoverSum / turnoverN : 0;
	const optimistic = runMode(ymAxis, perPeriodBuckets, perPeriodEW, spec.buckets, 'optimistic');
	const conservative = runMode(ymAxis, perPeriodBuckets, perPeriodEW, spec.buckets, 'conservative');
	optimistic.metrics.avgTurnover = avgTurnover;
	conservative.metrics.avgTurnover = avgTurnover;

	const optTop = optimistic.navByBucket[1];
	const consTop = conservative.navByBucket[1];
	const unknownDependence = Math.abs((optTop[optTop.length - 1] ?? 100) - (consTop[consTop.length - 1] ?? 100));

	return {
		ymAxis,
		optimistic,
		conservative,
		unknownDependence,
		headlineSuppressed: unknownDependence > 30, // U-G1 ④
		rebalances,
		status: 'ok',
		nUnknownExits: unknownExitCodes.size,
		nMergerExits: mergerExitCodes.size
	};
}

function blankResult(ymAxis: string[]): UniverseBtResult {
	const empty: UniverseRun = {
		navByBucket: {},
		ewBench: [],
		spread: [],
		metrics: { topRetPct: 0, topMddPct: 0, topSharpe: null, spreadEndPct: 0, avgTurnover: 0 }
	};
	return {
		ymAxis,
		optimistic: empty,
		conservative: empty,
		unknownDependence: 0,
		headlineSuppressed: false,
		rebalances: [],
		status: 'invalid',
		nUnknownExits: 0,
		nMergerExits: 0
	};
}
