// 랭킹 신호 · UniverseRow 에서 그 시점 랭킹 값 추출(가격/기술 팩터만, 17년 가격보존-clean).
// 재무 팩터 랭킹은 금지(상폐사 재무 13.9% = 생존편향, 05 §4). 단일종목 펀더게이트(W2)와 분리.

import type { RankSignalKey, UniverseRow } from './types';
import { RANK_SIGNAL_LABEL } from './types';

/** 신호 값(null=랭킹 제외). lowerBetter 신호는 부호 반전해 *항상 큰 값=상위분위*로 정규화. */
export function rankValue(row: UniverseRow, signal: RankSignalKey): number | null {
	let v: number | null;
	switch (signal) {
		case 'mom12_1':
			v = row.momMonthly;
			break;
		case 'lowVol':
			v = row.volMonthly6m;
			break;
		case 'high52w':
			v = row.high52wProx;
			break;
		case 'liquidity':
			v = row.turnover > 0 ? row.turnover : null;
			break;
		default:
			v = null;
	}
	if (v == null || !Number.isFinite(v)) return null;
	return RANK_SIGNAL_LABEL[signal].lowerBetter ? -v : v;
}

/** 그 리밸 시점 turnover 퍼센타일 임계 · PIT(절대 임계는 16년 인플레로 왜곡, 퍼센타일이 robust). */
function turnoverThreshold(rows: UniverseRow[], liquidityPctile: number): number {
	if (liquidityPctile <= 0) return 0;
	const ts = rows.map((r) => r.turnover).filter((t) => t > 0).sort((a, b) => a - b);
	if (!ts.length) return 0;
	const idx = Math.min(ts.length - 1, Math.floor(liquidityPctile * ts.length));
	return ts[idx];
}

/** 정렬 가능한 (code, value) 리스트 · value 큰 순(상위분위) 정렬은 호출부. null·저유동성 제외.
 *  ★유동성 컷 필수(실측): 없으면 penny-stock 인공물이 저분위를 폭발시킴(Q5 230배). U-G3. */
export function eligibleRanked(
	rows: UniverseRow[],
	signal: RankSignalKey,
	liquidityPctile: number
): { code: string; value: number }[] {
	const thr = turnoverThreshold(rows, liquidityPctile); // PIT 퍼센타일(그 리밸 시점)
	const out: { code: string; value: number }[] = [];
	for (const r of rows) {
		if (r.turnover < thr) continue; // 저유동성 컷
		const v = rankValue(r, signal);
		if (v == null) continue;
		out.push({ code: r.stockCode, value: v });
	}
	out.sort((a, b) => b.value - a.value); // 큰 값 = 상위분위(분위 1)
	return out;
}

/** NTILE 분위 배정 · 정렬된 리스트를 buckets 등분(상위=1). 동점 경계는 인덱스 기준(결정론). */
export function assignBuckets(ranked: { code: string; value: number }[], buckets: number): Map<string, number> {
	const n = ranked.length;
	const m = new Map<string, number>();
	if (n === 0) return m;
	for (let i = 0; i < n; i++) {
		// i=0(최상위)→bucket 1, i=n-1(최하위)→bucket=buckets
		const b = Math.min(buckets, Math.floor((i * buckets) / n) + 1);
		m.set(ranked[i].code, b);
	}
	return m;
}
