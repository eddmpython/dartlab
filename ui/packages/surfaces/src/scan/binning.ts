/**
 * Scan Studio 분포 패널 binning · 30 bin 히스토그램.
 *
 * mergedNodes (ecosystem + parquet 합본) 의 한 컬럼을 30 bin 으로 압축.
 * frontend bin (JS) 만 사용 · 2,664 회사 × 단일 컬럼 ≈ 2ms.
 *
 * log 스케일 옵션: 시총·매출처럼 long-tail 분포에 권장 (MetricDef.distribution).
 */

export interface Bin {
	x0: number;
	x1: number;
	count: number;
	values: number[]; // bin 안의 raw 값 (sample, outlier 표시용 · 최대 10)
}

export interface DistributionData {
	bins: Bin[];
	min: number;
	max: number;
	count: number;
	scale: 'linear' | 'log';
	mean: number;
	median: number;
	p10: number;
	p90: number;
}

const BIN_COUNT = 30;

function quantile(sorted: number[], p: number): number {
	if (sorted.length === 0) return 0;
	const idx = Math.min(sorted.length - 1, Math.max(0, Math.floor(p * (sorted.length - 1))));
	return sorted[idx];
}

/** 한 컬럼의 분포 · bins + 통계량 (mean/median/p10/p90). */
export function binNumeric(
	values: (number | null | undefined)[],
	scale: 'linear' | 'log' = 'linear'
): DistributionData {
	const valid: number[] = [];
	for (const v of values) {
		if (typeof v === 'number' && Number.isFinite(v)) {
			if (scale === 'log' && v <= 0) continue; // log 스케일에서는 양수만
			valid.push(v);
		}
	}
	if (valid.length === 0) {
		return {
			bins: [],
			min: 0,
			max: 0,
			count: 0,
			scale,
			mean: 0,
			median: 0,
			p10: 0,
			p90: 0
		};
	}
	const sorted = valid.slice().sort((a, b) => a - b);
	const min = sorted[0];
	const max = sorted[sorted.length - 1];
	const mean = valid.reduce((s, v) => s + v, 0) / valid.length;
	const median = quantile(sorted, 0.5);
	const p10 = quantile(sorted, 0.1);
	const p90 = quantile(sorted, 0.9);

	const bins: Bin[] = [];
	if (max <= min) {
		// 모든 값 동일 · 단일 bin
		bins.push({ x0: min, x1: max, count: valid.length, values: valid.slice(0, 10) });
		return { bins, min, max, count: valid.length, scale, mean, median, p10, p90 };
	}

	if (scale === 'log') {
		const lmin = Math.log10(min);
		const lmax = Math.log10(max);
		const step = (lmax - lmin) / BIN_COUNT;
		for (let i = 0; i < BIN_COUNT; i++) {
			const lx0 = lmin + i * step;
			const lx1 = i === BIN_COUNT - 1 ? lmax : lmin + (i + 1) * step;
			bins.push({
				x0: Math.pow(10, lx0),
				x1: Math.pow(10, lx1),
				count: 0,
				values: []
			});
		}
		for (const v of valid) {
			const idx = Math.min(
				BIN_COUNT - 1,
				Math.floor(((Math.log10(v) - lmin) / (lmax - lmin)) * BIN_COUNT)
			);
			bins[idx].count += 1;
			if (bins[idx].values.length < 10) bins[idx].values.push(v);
		}
	} else {
		const step = (max - min) / BIN_COUNT;
		for (let i = 0; i < BIN_COUNT; i++) {
			bins.push({
				x0: min + i * step,
				x1: i === BIN_COUNT - 1 ? max : min + (i + 1) * step,
				count: 0,
				values: []
			});
		}
		for (const v of valid) {
			const idx = Math.min(
				BIN_COUNT - 1,
				Math.floor(((v - min) / (max - min)) * BIN_COUNT)
			);
			bins[idx].count += 1;
			if (bins[idx].values.length < 10) bins[idx].values.push(v);
		}
	}

	return { bins, min, max, count: valid.length, scale, mean, median, p10, p90 };
}

/** 한 회사 값이 분포에서 어느 bin 인지. */
export function findBinIndex(dist: DistributionData, value: number | null | undefined): number {
	if (typeof value !== 'number' || !Number.isFinite(value) || dist.bins.length === 0) return -1;
	if (dist.scale === 'log' && value <= 0) return -1;
	if (dist.scale === 'log') {
		const lmin = Math.log10(dist.min);
		const lmax = Math.log10(dist.max);
		if (lmax <= lmin) return 0;
		return Math.min(
			dist.bins.length - 1,
			Math.max(0, Math.floor(((Math.log10(value) - lmin) / (lmax - lmin)) * dist.bins.length))
		);
	}
	if (dist.max <= dist.min) return 0;
	return Math.min(
		dist.bins.length - 1,
		Math.max(0, Math.floor(((value - dist.min) / (dist.max - dist.min)) * dist.bins.length))
	);
}
