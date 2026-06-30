<script lang="ts">
	interface DataPoint {
		year: string;
		[key: string]: string | number | null;
	}

	interface Props {
		data: DataPoint[];
		title?: string;
		unit?: string;
		keys?: string[];
		colors?: string[];
		height?: number;
	}

	let {
		data = [],
		title = '',
		unit = '억원',
		keys = [],
		colors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
		height = 300
	}: Props = $props();

	// 자동으로 keys 추출 (year 제외 숫자 필드)
	const resolvedKeys = $derived(
		keys.length > 0
			? keys
			: Object.keys(data[0] || {}).filter(
					(k) => k !== 'year' && typeof data[0]?.[k] === 'number'
				)
	);

	const W = 700;
	const PAD = { top: 40, right: 20, bottom: 50, left: 70 };
	const plotW = W - PAD.left - PAD.right;
	const plotH = height - PAD.top - PAD.bottom;

	// min/max 계산
	const allVals = $derived(
		data.flatMap((d) => resolvedKeys.map((k) => d[k] as number).filter((v) => v != null))
	);
	const rawMin = $derived(Math.min(...allVals));
	const rawMax = $derived(Math.max(...allVals));
	const padding = $derived((rawMax - rawMin) * 0.1 || Math.abs(rawMax) * 0.1 || 1);
	const yMin = $derived(rawMin < 0 ? rawMin - padding : Math.min(0, rawMin));
	const yMax = $derived(rawMax + padding);

	function x(i: number): number {
		return PAD.left + (i / Math.max(data.length - 1, 1)) * plotW;
	}
	function y(v: number): number {
		return PAD.top + (1 - (v - yMin) / (yMax - yMin)) * plotH;
	}

	function fmt(v: number): string {
		if (Math.abs(v) >= 1e4) return (v / 1e4).toFixed(1) + '조';
		if (Math.abs(v) >= 1) return v.toLocaleString('ko-KR');
		return v.toFixed(1);
	}

	function pathD(key: string): string {
		const pts = data
			.map((d, i) => {
				const val = d[key] as number | null;
				if (typeof val !== 'number' || !Number.isFinite(val)) return null;
				return `${x(i)},${y(val)}`;
			})
			.filter(Boolean);
		if (pts.length < 2) return '';
		return 'M' + pts.join('L');
	}

	// 0선 위치
	const zeroY = $derived(yMin <= 0 && yMax >= 0 ? y(0) : null);

	// Y축 눈금 (5개)
	const yTicks = $derived(
		Array.from({ length: 5 }, (_, i) => yMin + ((yMax - yMin) * i) / 4)
	);

	// hover
	let hoverIdx = $state<number | null>(null);
</script>

<div class="chart-wrap">
	{#if title}
		<div class="chart-title">{title}</div>
	{/if}
	<svg viewBox="0 0 {W} {height}" xmlns="http://www.w3.org/2000/svg">
		<!-- grid -->
		{#each yTicks as tick}
			<line
				x1={PAD.left}
				y1={y(tick)}
				x2={W - PAD.right}
				y2={y(tick)}
				stroke="#1e293b"
				stroke-width="0.5"
			/>
			<text x={PAD.left - 8} y={y(tick) + 4} text-anchor="end" fill="#64748b" font-size="11"
				>{fmt(tick)}</text
			>
		{/each}

		<!-- zero line -->
		{#if zeroY != null}
			<line
				x1={PAD.left}
				y1={zeroY}
				x2={W - PAD.right}
				y2={zeroY}
				stroke="#475569"
				stroke-width="1"
				stroke-dasharray="4,3"
			/>
		{/if}

		<!-- x labels -->
		{#each data as d, i}
			<text x={x(i)} y={height - 10} text-anchor="middle" fill="#94a3b8" font-size="12"
				>{d.year}</text
			>
		{/each}

		<!-- lines -->
		{#each resolvedKeys as key, ki}
			{@const linePath = pathD(key)}
			{#if linePath}
				<path d={linePath} fill="none" stroke={colors[ki % colors.length]} stroke-width="2.5" />
			{/if}
			{#each data as d, i}
				{#if d[key] != null}
					<circle
						cx={x(i)}
						cy={y(d[key] as number)}
						r={hoverIdx === i ? 5 : 3.5}
						fill={colors[ki % colors.length]}
					/>
				{/if}
			{/each}
		{/each}

		<!-- hover zones -->
		{#each data as _, i}
			<rect
				x={x(i) - plotW / data.length / 2}
				y={PAD.top}
				width={plotW / data.length}
				height={plotH}
				fill="transparent"
				onmouseenter={() => (hoverIdx = i)}
				onmouseleave={() => (hoverIdx = null)}
			/>
		{/each}

		<!-- tooltip -->
		{#if hoverIdx != null}
			{@const d = data[hoverIdx]}
			<rect
				x={x(hoverIdx) - 60}
				y={PAD.top - 5}
				width="120"
				height={resolvedKeys.length * 18 + 22}
				rx="6"
				fill="#0f172a"
				fill-opacity="0.95"
				stroke="#334155"
			/>
			<text
				x={x(hoverIdx)}
				y={PAD.top + 12}
				text-anchor="middle"
				fill="#f1f5f9"
				font-size="11"
				font-weight="bold">{d.year}</text
			>
			{#each resolvedKeys as key, ki}
				<text
					x={x(hoverIdx)}
					y={PAD.top + 12 + (ki + 1) * 18}
					text-anchor="middle"
					fill={colors[ki % colors.length]}
					font-size="11"
				>
					{key}: {d[key] != null ? fmt(d[key] as number) : '·'}{unit === '억원' ? '' : unit}
				</text>
			{/each}
		{/if}

		<!-- legend -->
		{#each resolvedKeys as key, ki}
			<rect
				x={PAD.left + ki * 100}
				y={height - 28}
				width="12"
				height="12"
				rx="2"
				fill={colors[ki % colors.length]}
			/>
			<text
				x={PAD.left + ki * 100 + 16}
				y={height - 18}
				fill="#94a3b8"
				font-size="11">{key}</text
			>
		{/each}

		<!-- unit -->
		<text x={PAD.left} y={PAD.top - 12} fill="#64748b" font-size="10">({unit})</text>
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
		max-width: 700px;
		height: auto;
		font-family: -apple-system, 'Segoe UI', sans-serif;
	}
</style>
