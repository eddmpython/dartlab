<script lang="ts">
	/**
	 * 분포 패널 · 현재 정렬 컬럼의 30 bin 히스토그램.
	 *
	 *  - bin click → 그 구간 회사를 그리드에서 highlight (양방향)
	 *  - 산업 필터 시 산업 평균 line 추가 표시
	 *  - 통계량 (mean / median / p10 / p90) 표시
	 *  - 로그 스케일 toggle (MetricDef.distribution 기본값 자동)
	 */
	import { binNumeric, findBinIndex } from './binning';
	import type { DistributionData } from './binning';
	import { METRICS_BY_KEY } from './metrics';
	import type { ScanNode } from './types';
	import { fmtKrw } from '@dartlab/ui-format/krw';
	import { fmtPct, fmtMul } from '@dartlab/ui-format/pct';

	interface Props {
		nodes: ScanNode[];
		filteredNodes: ScanNode[];
		metricKey: string;
		sortDir?: 'asc' | 'desc';
		highlightBin: { x0: number; x1: number } | null;
		onBinHover: (bin: { x0: number; x1: number } | null) => void;
		onCompanyClick?: (id: string) => void;
	}

	let { nodes, filteredNodes, metricKey, sortDir = 'desc', highlightBin, onBinHover, onCompanyClick }: Props = $props();

	let metric = $derived(METRICS_BY_KEY[metricKey]);
	let scale = $state<'linear' | 'log'>('linear');

	// metric 바뀌면 권장 스케일 따라가기
	$effect(() => {
		scale = metric?.distribution || 'linear';
	});

	let dist = $derived.by<DistributionData>(() => {
		if (!metric || metric.type !== 'number') {
			return {
				bins: [],
				min: 0,
				max: 0,
				count: 0,
				scale: 'linear',
				mean: 0,
				median: 0,
				p10: 0,
				p90: 0
			};
		}
		return binNumeric(
			nodes.map((n) => (n as Record<string, unknown>)[metricKey] as number | null | undefined),
			scale
		);
	});

	// 현재 필터된 회사들의 평균 (bin 위에 line 으로)
	let filteredMean = $derived.by(() => {
		if (!metric || metric.type !== 'number' || filteredNodes.length === 0) return null;
		const valid: number[] = [];
		for (const n of filteredNodes) {
			const v = (n as Record<string, unknown>)[metricKey];
			if (typeof v === 'number' && Number.isFinite(v)) {
				if (scale === 'log' && v <= 0) continue;
				valid.push(v);
			}
		}
		if (valid.length === 0) return null;
		return valid.reduce((s, v) => s + v, 0) / valid.length;
	});

	let filteredMeanBin = $derived(filteredMean !== null ? findBinIndex(dist, filteredMean) : -1);
	let p10Bin = $derived(findBinIndex(dist, dist.p10));
	let p90Bin = $derived(findBinIndex(dist, dist.p90));
	let valueStats = $derived.by(() => {
		if (!metric || metric.type !== 'number') return { valid: 0, missing: nodes.length, unique: 0, activeBins: 0 };
		const values = nodes
			.map((n) => (n as Record<string, unknown>)[metricKey])
			.filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
		const unique = new Set(values.map((v) => v.toFixed(6))).size;
		const activeBins = dist.bins.filter((b) => b.count > 0).length;
		return { valid: values.length, missing: nodes.length - values.length, unique, activeBins };
	});
	let histogramUsable = $derived(
		dist.count >= 20 &&
			valueStats.unique >= 4 &&
			valueStats.activeBins >= 3 &&
			Number.isFinite(dist.p10) &&
			Number.isFinite(dist.p90) &&
			Math.abs(dist.p90 - dist.p10) > 1e-9
	);

	// TOP / BOTTOM 5 회사 (현재 컬럼 기준)
	let ranked = $derived.by(() => {
		if (!metric || metric.type !== 'number') return { top: [], bottom: [] };
		const list = filteredNodes
			.map((n) => {
				const v = (n as Record<string, unknown>)[metricKey];
				return typeof v === 'number' && Number.isFinite(v) ? { n, v } : null;
			})
			.filter((x): x is { n: ScanNode; v: number } => x !== null);
		if (list.length === 0) return { top: [], bottom: [] };
		const desc = list.slice().sort((a, b) => b.v - a.v);
		const asc = list.slice().sort((a, b) => a.v - b.v);
		const goodFirst = sortDir === 'desc' || metric.higherBetter !== false;
		return {
			top: (goodFirst ? desc : asc).slice(0, 5),
			bottom: (goodFirst ? asc : desc).slice(0, 5)
		};
	});

	const W = 280;
	const H = 140;
	const PAD_T = 8;
	const PAD_B = 18;

	let maxCount = $derived(dist.bins.length === 0 ? 0 : Math.max(...dist.bins.map((b) => b.count)));
	let barWidth = $derived(dist.bins.length === 0 ? 0 : (W - 16) / dist.bins.length - 1);

	function fmtVal(v: number): string {
		if (!metric) return String(v);
		if (metric.unit === '억원') return fmtWonAsEok(v);
		if (metric.unit === '원') return fmtKrw(v);
		if (metric.unit === '%' || metric.unit === '%p') return fmtPct(v);
		if (metric.unit === '배') return fmtMul(v, 1);
		if (metric.unit === '명') return Math.round(v).toLocaleString('ko-KR') + '명';
		if (metric.unit === '위') return Math.round(v) + '위';
		if (metric.unit === '건') return Math.round(v) + '건';
		return v.toLocaleString('ko-KR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function fmtWonAsEok(v: number): string {
		const eok = v / 1e8;
		const abs = Math.abs(eok);
		const maximumFractionDigits = abs >= 100 ? 0 : 1;
		return `${eok.toLocaleString('ko-KR', { maximumFractionDigits })}억원`;
	}

	function isBinHighlighted(b: { x0: number; x1: number }): boolean {
		if (!highlightBin) return false;
		return b.x0 === highlightBin.x0 && b.x1 === highlightBin.x1;
	}

	function handleBinEnter(b: { x0: number; x1: number }) {
		onBinHover({ x0: b.x0, x1: b.x1 });
	}
	function handleBinLeave() {
		onBinHover(null);
	}
</script>

<div class="dist">
	<div class="dist-head">
		<div class="dist-title">
			<span class="d-mlbl">분포</span>
			<span class="d-mname">{metric?.label ?? metricKey}</span>
			{#if metric?.unit}<span class="d-munit">({metric.unit})</span>{/if}
		</div>
		{#if metric?.type === 'number'}
			<button
				type="button"
				class="scale-toggle"
				class:active={scale === 'log'}
				onclick={() => (scale = scale === 'log' ? 'linear' : 'log')}
				title="로그 스케일 toggle"
			>
				log
			</button>
		{/if}
	</div>

	{#if metric?.type !== 'number'}
		<div class="dist-empty">숫자 메트릭만 분포 표시 ({metric?.label ?? metricKey} 은 텍스트/등급)</div>
	{:else if dist.count === 0}
		<div class="dist-empty">데이터 없음</div>
	{:else}
		{#if histogramUsable}
		<svg viewBox="0 0 {W} {H}" class="dist-svg" role="img" aria-label="히스토그램">
			<!-- bars -->
			{#each dist.bins as b, i (i)}
				{@const h = maxCount === 0 ? 0 : ((H - PAD_T - PAD_B) * b.count) / maxCount}
				{@const x = 8 + i * (barWidth + 1)}
				{@const y = H - PAD_B - h}
				<rect
					{x}
					{y}
					width={barWidth}
					height={h}
					class="bar"
					class:highlighted={isBinHighlighted(b)}
					onmouseenter={() => handleBinEnter(b)}
					onmouseleave={handleBinLeave}
					role="presentation"
				></rect>
				<!-- 투명 hit area (얇은 bar 도 hover 잘 잡힘) -->
				<rect
					{x}
					y={PAD_T}
					width={barWidth + 1}
					height={H - PAD_T - PAD_B}
					class="hit"
					onmouseenter={() => handleBinEnter(b)}
					onmouseleave={handleBinLeave}
				></rect>
			{/each}
			<!-- p10 / p90 vertical lines -->
			{#if p10Bin >= 0}
				{@const lx = 8 + p10Bin * (barWidth + 1) + barWidth / 2}
				<line x1={lx} x2={lx} y1={PAD_T} y2={H - PAD_B} class="quantile-line p10" />
				<text x={lx + 2} y={PAD_T + 7} class="quantile-label" text-anchor="start">p10</text>
			{/if}
			{#if p90Bin >= 0}
				{@const lx = 8 + p90Bin * (barWidth + 1) + barWidth / 2}
				<line x1={lx} x2={lx} y1={PAD_T} y2={H - PAD_B} class="quantile-line p90" />
				<text x={lx - 2} y={PAD_T + 7} class="quantile-label" text-anchor="end">p90</text>
			{/if}
			<!-- 필터된 평균 line -->
			{#if filteredMeanBin >= 0 && filteredNodes.length < nodes.length}
				{@const lx = 8 + filteredMeanBin * (barWidth + 1) + barWidth / 2}
				<line x1={lx} x2={lx} y1={PAD_T} y2={H - PAD_B} class="mean-line" />
				<text x={lx} y={PAD_T + 4} class="mean-label" text-anchor="middle">필터 평균</text>
			{/if}
			<!-- baseline -->
			<line x1="0" x2={W} y1={H - PAD_B} y2={H - PAD_B} class="axis" />
		</svg>
		{:else}
			<div class="dist-summary">
				<div class="summary-title">분포 대신 랭킹 표시</div>
				<div class="summary-desc">값이 비어 있거나 한 구간에 몰려 히스토그램 해석이 어렵습니다.</div>
				<div class="summary-grid">
					<span>유효값</span><strong>{valueStats.valid.toLocaleString('ko-KR')}</strong>
					<span>결측</span><strong>{valueStats.missing.toLocaleString('ko-KR')}</strong>
					<span>고유값</span><strong>{valueStats.unique.toLocaleString('ko-KR')}</strong>
				</div>
			</div>
		{/if}

		<div class="stats">
			<div class="stat">
				<span class="s-lbl">전체 평균</span>
				<span class="s-val">{fmtVal(dist.mean)}</span>
			</div>
			<div class="stat">
				<span class="s-lbl">중앙값</span>
				<span class="s-val">{fmtVal(dist.median)}</span>
			</div>
			<div class="stat">
				<span class="s-lbl">p10</span>
				<span class="s-val">{fmtVal(dist.p10)}</span>
			</div>
			<div class="stat">
				<span class="s-lbl">p90</span>
				<span class="s-val">{fmtVal(dist.p90)}</span>
			</div>
			{#if filteredMean !== null && filteredNodes.length < nodes.length}
				<div class="stat highlight">
					<span class="s-lbl">필터 평균</span>
					<span class="s-val">{fmtVal(filteredMean)}</span>
				</div>
				<div class="stat highlight">
					<span class="s-lbl">필터 사</span>
					<span class="s-val">{filteredNodes.length.toLocaleString('ko-KR')}</span>
				</div>
			{/if}
		</div>

		{#if histogramUsable}
			<div class="range">
				<span>{fmtVal(dist.min)}</span>
				<span>{fmtVal(dist.max)}</span>
			</div>
		{/if}

		<!-- TOP / BOTTOM 5 회사 -->
		{#if ranked.top.length > 0}
			<div class="ranked-grid">
				<div class="ranked-col">
					<div class="ranked-title">TOP 5 ({metric?.higherBetter === false ? '낮은 순' : '높은 순'})</div>
					<ul class="ranked-list">
						{#each ranked.top as r (r.n.id)}
							<button
								type="button"
								class="ranked-item top"
								onclick={() => onCompanyClick?.(r.n.id)}
								title="{r.n.label} ({r.n.id}) · 클릭 시 디테일"
							>
								<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
								<span class="r-label">{r.n.label}</span>
								<span class="r-val">{fmtVal(r.v)}</span>
							</button>
						{/each}
					</ul>
				</div>
				<div class="ranked-col">
					<div class="ranked-title">BOTTOM 5</div>
					<ul class="ranked-list">
						{#each ranked.bottom as r (r.n.id)}
							<button
								type="button"
								class="ranked-item bottom"
								onclick={() => onCompanyClick?.(r.n.id)}
								title="{r.n.label} ({r.n.id}) · 클릭 시 디테일"
							>
								<span class="r-dot" style:background={(r.n.color as string) || '#475569'}></span>
								<span class="r-label">{r.n.label}</span>
								<span class="r-val">{fmtVal(r.v)}</span>
							</button>
						{/each}
					</ul>
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.dist {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 12px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		font-size: 11px;
		height: 100%;
		overflow: hidden;
	}
	.dist-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.dist-title {
		display: flex;
		align-items: baseline;
		gap: 6px;
	}
	.d-mlbl {
		font-size: 10px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.d-mname {
		font-weight: 600;
		color: #f1f5f9;
		font-size: 12px;
	}
	.d-munit {
		font-size: 10px;
		color: #64748b;
	}
	.scale-toggle {
		font-size: 10px;
		padding: 2px 8px;
		background: #0a0e18;
		border: 1px solid #1e2433;
		border-radius: 3px;
		color: #94a3b8;
		font-family: monospace;
		cursor: pointer;
	}
	.scale-toggle.active {
		background: rgba(var(--amber-rgb), 0.1);
		border-color: rgba(var(--amber-rgb), 0.4);
		color: var(--amber);
	}

	.dist-empty {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #475569;
		font-size: 11px;
		text-align: center;
		padding: 20px 8px;
	}
	.dist-summary {
		padding: 12px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #0a0e18;
	}
	.summary-title {
		font-size: 12px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.summary-desc {
		margin-top: 4px;
		font-size: 10px;
		line-height: 1.4;
		color: #64748b;
	}
	.summary-grid {
		margin-top: 10px;
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 4px 10px;
		font-family: monospace;
		font-size: 10px;
	}
	.summary-grid span {
		color: #64748b;
	}
	.summary-grid strong {
		color: #cbd5e1;
		font-weight: 700;
	}

	.dist-svg {
		width: 100%;
		height: auto;
	}
	.bar {
		fill: #475569;
		transition: fill 0.1s;
	}
	.bar.highlighted {
		fill: var(--amber);
	}
	.hit {
		fill: transparent;
		cursor: crosshair;
	}
	.hit:hover + .bar,
	.hit:hover {
		cursor: crosshair;
	}
	.mean-line {
		stroke: var(--amber);
		stroke-width: 1.5;
		stroke-dasharray: 2 2;
	}
	.mean-label {
		fill: var(--amber);
		font-size: 8px;
		font-family: monospace;
	}
	.quantile-line {
		stroke-width: 1;
		stroke-dasharray: 1 2;
	}
	.quantile-line.p10 {
		stroke: #ef4444;
		opacity: 0.5;
	}
	.quantile-line.p90 {
		stroke: #22c55e;
		opacity: 0.5;
	}
	.quantile-label {
		fill: #64748b;
		font-size: 7px;
		font-family: monospace;
		opacity: 0.7;
	}
	.axis {
		stroke: #1e2433;
		stroke-width: 1;
	}

	.stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 4px 12px;
	}
	.stat {
		display: flex;
		justify-content: space-between;
		font-family: monospace;
		font-size: 10px;
	}
	.s-lbl {
		color: #64748b;
	}
	.s-val {
		color: #cbd5e1;
		font-weight: 500;
	}
	.stat.highlight .s-val {
		color: var(--amber);
	}

	.range {
		display: flex;
		justify-content: space-between;
		font-family: monospace;
		font-size: 9px;
		color: #475569;
		padding: 0 8px;
	}

	.ranked-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px solid #1e2433;
	}
	.ranked-col {
		min-width: 0;
	}
	.ranked-title {
		font-size: 9px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: 4px;
	}
	.ranked-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.ranked-item {
		display: grid;
		grid-template-columns: 5px minmax(0, 1fr) max-content;
		align-items: center;
		gap: 5px;
		padding: 3px 4px;
		background: transparent;
		border: none;
		border-radius: 3px;
		cursor: pointer;
		text-align: left;
		font-family: inherit;
		color: inherit;
		width: 100%;
	}
	.ranked-item:hover {
		background: rgba(var(--amber-rgb), 0.08);
	}
	.ranked-item.top:hover {
		background: rgba(34, 197, 94, 0.06);
	}
	.ranked-item.bottom:hover {
		background: rgba(239, 68, 68, 0.06);
	}
	.r-dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.r-label {
		flex: 1;
		font-size: 10px;
		color: #cbd5e1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.r-val {
		font-family: monospace;
		font-size: 9px;
		color: #94a3b8;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.ranked-item.top .r-val {
		color: #22c55e;
	}
	.ranked-item.bottom .r-val {
		color: #ef4444;
	}
</style>
