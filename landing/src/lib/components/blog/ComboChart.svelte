<script lang="ts">
	interface DataPoint {
		year: string;
		[key: string]: string | number | null;
	}

	interface Props {
		data: DataPoint[];
		title?: string;
		unit?: string;
		lineKeys?: string[];
		barKeys?: string[];
		lineColors?: string[];
		barColors?: string[];
		height?: number;
		dualAxis?: boolean;
	}

	let {
		data = [],
		title = '',
		unit = '억원',
		lineKeys = [],
		barKeys = [],
		lineColors = ['#22c55e'],
		barColors = ['#3b82f6', '#f59e0b', '#ef4444'],
		height = 340,
		dualAxis = true
	}: Props = $props();

	const W = 720;
	const PAD = { top: 30, right: 70, bottom: 65, left: 70 };
	const plotW = W - PAD.left - PAD.right;
	const plotH = height - PAD.top - PAD.bottom;

	// 라인 값 (좌축)
	const lineVals = $derived(
		data.flatMap((d) => lineKeys.map((k) => d[k] as number).filter((v) => v != null))
	);
	// 막대 값 (우축 or 동일축)
	const barVals = $derived(
		data.flatMap((d) => barKeys.map((k) => d[k] as number).filter((v) => v != null))
	);

	// 좌축 스케일 (라인)
	const lMin = $derived(lineVals.length > 0 ? Math.min(...lineVals, 0) : 0);
	const lMax = $derived(lineVals.length > 0 ? Math.max(...lineVals, 0) : 1);
	const lPad = $derived((lMax - lMin) * 0.12 || 1);
	const lyMin = $derived(lMin < 0 ? lMin - lPad : 0);
	const lyMax = $derived(lMax + lPad);

	// 우축 스케일 (막대) · dualAxis일 때만 별도
	const allVals = $derived([...lineVals, ...barVals]);
	const rMin = $derived(dualAxis && barVals.length > 0 ? Math.min(...barVals, 0) : Math.min(...allVals, 0));
	const rMax = $derived(dualAxis && barVals.length > 0 ? Math.max(...barVals, 0) : Math.max(...allVals, 0));
	const rPad = $derived((rMax - rMin) * 0.15 || 1);
	const ryMin = $derived(rMin < 0 ? rMin - rPad : Math.min(0, rMin));
	const ryMax = $derived(rMax + rPad);

	function xCenter(i: number): number {
		const gap = plotW / data.length;
		return PAD.left + i * gap + gap / 2;
	}
	// 좌축 Y (라인)
	function yL(v: number): number {
		return PAD.top + (1 - (v - lyMin) / (lyMax - lyMin)) * plotH;
	}
	// 우축 Y (막대)
	function yR(v: number): number {
		if (!dualAxis) return yL(v);
		return PAD.top + (1 - (v - ryMin) / (ryMax - ryMin)) * plotH;
	}

	const zeroYR = $derived(ryMin <= 0 && ryMax >= 0 ? yR(0) : null);
	const barGroupW = $derived(Math.min((plotW / data.length) * 0.65, 70));
	const singleBarW = $derived(barKeys.length > 0 ? barGroupW / barKeys.length : 0);

	function fmt(v: number): string {
		if (Math.abs(v) >= 1e4) return (v / 1e4).toFixed(1) + '조';
		if (Math.abs(v) >= 1) return v.toLocaleString('ko-KR');
		return v.toFixed(1);
	}

	const lTicks = $derived(Array.from({ length: 5 }, (_, i) => lyMin + ((lyMax - lyMin) * i) / 4));
	const rTicks = $derived(Array.from({ length: 5 }, (_, i) => ryMin + ((ryMax - ryMin) * i) / 4));

	let hoverIdx = $state<number | null>(null);

	// legend 위치 계산
	const totalLegendItems = $derived(lineKeys.length + barKeys.length);
	const legendW = $derived(totalLegendItems * 120);
	const legendStartX = $derived((W - legendW) / 2);
</script>

<div class="chart-wrap">
	{#if title}
		<div class="chart-title">{title}</div>
	{/if}
	<svg viewBox="0 0 {W} {height}" xmlns="http://www.w3.org/2000/svg">
		<!-- 좌축 grid + labels -->
		{#each lTicks as tick}
			<line x1={PAD.left} y1={yL(tick)} x2={W - PAD.right} y2={yL(tick)} stroke="#1e293b" stroke-width="0.5" />
			<text x={PAD.left - 8} y={yL(tick) + 4} text-anchor="end" fill="#64748b" font-size="10">{fmt(tick)}</text>
		{/each}

		<!-- 우축 labels (dualAxis) -->
		{#if dualAxis && barKeys.length > 0}
			{#each rTicks as tick}
				<text x={W - PAD.right + 8} y={yR(tick) + 4} text-anchor="start" fill="#64748b" font-size="10">{fmt(tick)}</text>
			{/each}
		{/if}

		<!-- 좌축 라벨 -->
		{#if lineKeys.length > 0}
			<text x={12} y={PAD.top + plotH / 2} text-anchor="middle" fill={lineColors[0]} font-size="10"
				transform="rotate(-90, 12, {PAD.top + plotH / 2})">매출 ({unit})</text>
		{/if}
		<!-- 우축 라벨 -->
		{#if dualAxis && barKeys.length > 0}
			<text x={W - 10} y={PAD.top + plotH / 2} text-anchor="middle" fill={barColors[0]} font-size="10"
				transform="rotate(90, {W - 10}, {PAD.top + plotH / 2})">이익 ({unit})</text>
		{/if}

		<!-- zero line (우축 기준) -->
		{#if zeroYR != null}
			<line x1={PAD.left} y1={zeroYR} x2={W - PAD.right} y2={zeroYR} stroke="#475569" stroke-width="1" stroke-dasharray="4,3" />
		{/if}

		<!-- 막대 (우축 스케일) -->
		{#each data as d, i}
			{#each barKeys as bk, bi}
				{@const val = d[bk] as number | null}
				{#if val != null}
					{@const bx = xCenter(i) - barGroupW / 2 + bi * singleBarW + 1}
					{@const baseY = zeroYR ?? yR(0)}
					{@const byTop = val >= 0 ? yR(val) : baseY}
					{@const bh = Math.abs(yR(val) - baseY)}
					<rect
						x={bx} y={byTop} width={singleBarW - 2} height={Math.max(bh, 1)}
						rx="2" fill={barColors[bi % barColors.length]}
						opacity={hoverIdx === i ? 1 : 0.75}
					/>
				{/if}
			{/each}
		{/each}

		<!-- 라인 (좌축 스케일) -->
		{#each lineKeys as lk, li}
			{@const pts = data.map((d, i) => {
				const val = d[lk] as number | null;
				return val != null ? `${xCenter(i)},${yL(val)}` : null;
			}).filter(Boolean)}
			<polyline points={pts.join(' ')} fill="none" stroke={lineColors[li % lineColors.length]}
				stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
			{#each data as d, i}
				{#if d[lk] != null}
					<circle cx={xCenter(i)} cy={yL(d[lk] as number)} r={hoverIdx === i ? 5 : 3.5}
						fill={lineColors[li % lineColors.length]} />
				{/if}
			{/each}
		{/each}

		<!-- x labels -->
		{#each data as d, i}
			<text x={xCenter(i)} y={PAD.top + plotH + 20} text-anchor="middle" fill="#94a3b8" font-size="12">{d.year}</text>
		{/each}

		<!-- hover zones -->
		{#each data as _, i}
			{@const gap = plotW / data.length}
			<rect x={PAD.left + i * gap} y={PAD.top} width={gap} height={plotH}
				fill="transparent"
				onmouseenter={() => (hoverIdx = i)} onmouseleave={() => (hoverIdx = null)} />
		{/each}

		<!-- tooltip -->
		{#if hoverIdx != null}
			{@const d = data[hoverIdx]}
			{@const allK = [...lineKeys, ...barKeys]}
			{@const tw = 160}
			{@const th = allK.length * 18 + 24}
			{@const tx = Math.min(Math.max(xCenter(hoverIdx) - tw / 2, PAD.left), W - PAD.right - tw)}
			<rect x={tx} y={PAD.top} width={tw} height={th} rx="6"
				fill="#0f172a" fill-opacity="0.95" stroke="#334155" />
			<text x={tx + tw / 2} y={PAD.top + 14} text-anchor="middle"
				fill="#f1f5f9" font-size="11" font-weight="bold">{d.year}</text>
			{#each allK as k, ki}
				{@const isLine = lineKeys.includes(k)}
				{@const color = isLine ? lineColors[lineKeys.indexOf(k)] : barColors[barKeys.indexOf(k)]}
				<text x={tx + tw / 2} y={PAD.top + 14 + (ki + 1) * 18} text-anchor="middle"
					fill={color} font-size="11">
					{k}: {d[k] != null ? fmt(d[k] as number) : '·'}
				</text>
			{/each}
		{/if}

		<!-- legend (X축 아래) -->
		{#each lineKeys as k, i}
			<line x1={legendStartX + i * 120} y1={height - 15} x2={legendStartX + i * 120 + 16} y2={height - 15}
				stroke={lineColors[i]} stroke-width="2.5" />
			<circle cx={legendStartX + i * 120 + 8} cy={height - 15} r="3" fill={lineColors[i]} />
			<text x={legendStartX + i * 120 + 20} y={height - 11} fill="#94a3b8" font-size="11">{k} (좌)</text>
		{/each}
		{#each barKeys as k, i}
			<rect x={legendStartX + (lineKeys.length + i) * 120} y={height - 20} width="12" height="10" rx="2"
				fill={barColors[i % barColors.length]} />
			<text x={legendStartX + (lineKeys.length + i) * 120 + 16} y={height - 11} fill="#94a3b8" font-size="11">{k} (우)</text>
		{/each}
	</svg>
</div>

<style>
	.chart-wrap {
		margin: 1.5rem 0;
		padding: 1rem;
		background: #0a0e1a;
		border: 1px solid #1e293b;
		border-radius: 12px;
		overflow-x: auto;
	}
	.chart-title {
		color: #f1f5f9;
		font-size: 0.95rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		padding-left: 0.5rem;
	}
	svg {
		width: 100%;
		max-width: 720px;
		height: auto;
		font-family: -apple-system, 'Segoe UI', sans-serif;
	}
</style>
