<script lang="ts">
	/**
	 * 5축 SVG 레이더 차트 · Simply Wall St Snowflake 스타일.
	 *
	 * axes: 5개 축 배열 [{label, value(0~100), benchmark(0~100)?}]
	 * value = 이 회사 점수 (빨강 실선)
	 * benchmark = 업종 중앙값 (회색 반투명 영역)
	 */
	interface Axis {
		label: string;
		value: number;
		benchmark?: number;
	}

	interface Props {
		axes: Axis[];
		size?: number;
	}

	let { axes, size = 120 }: Props = $props();

	const cx = $derived(size / 2);
	const cy = $derived(size / 2);
	const maxR = $derived(size / 2 - 16);
	const N = $derived(axes.length || 5);

	function polarX(i: number, r: number): number {
		const angle = (Math.PI * 2 * i) / N - Math.PI / 2;
		return cx + r * Math.cos(angle);
	}
	function polarY(i: number, r: number): number {
		const angle = (Math.PI * 2 * i) / N - Math.PI / 2;
		return cy + r * Math.sin(angle);
	}
	// 라벨 정렬 · 스포크 다수(10+)일 때 겹침 완화: 우측은 start(밖으로), 좌측은 end, 상·하는 middle.
	function anchorFor(i: number): 'start' | 'middle' | 'end' {
		const c = Math.cos((Math.PI * 2 * i) / N - Math.PI / 2);
		return c > 0.3 ? 'start' : c < -0.3 ? 'end' : 'middle';
	}

	// Grid rings (20%, 40%, 60%, 80%, 100%)
	let rings = $derived([0.2, 0.4, 0.6, 0.8, 1.0].map((p) => p * maxR));

	// Polygon path from values (0~100 → 0~maxR)
	function polygonPath(values: number[]): string {
		return values
			.map((v, i) => {
				const r = (Math.min(100, Math.max(0, v)) / 100) * maxR;
				const x = polarX(i, r);
				const y = polarY(i, r);
				return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
			})
			.join(' ') + ' Z';
	}

	let companyPath = $derived(polygonPath(axes.map((a) => a.value)));
	let benchmarkPath = $derived(
		axes.some((a) => a.benchmark != null)
			? polygonPath(axes.map((a) => a.benchmark ?? 50))
			: ''
	);
</script>

<svg width={size} height={size} viewBox="0 0 {size} {size}" class="radar">
	<!-- Grid rings -->
	{#each rings as r}
		<polygon
			points={Array.from({ length: N }, (_, i) => `${polarX(i, r).toFixed(1)},${polarY(i, r).toFixed(1)}`).join(' ')}
			fill="none"
			stroke="rgba(148,163,184,0.15)"
			stroke-width="0.5"
		/>
	{/each}

	<!-- Axis lines -->
	{#each axes as _, i}
		<line
			x1={cx}
			y1={cy}
			x2={polarX(i, maxR)}
			y2={polarY(i, maxR)}
			stroke="rgba(148,163,184,0.12)"
			stroke-width="0.5"
		/>
	{/each}

	<!-- Benchmark area (업종 중앙값) -->
	{#if benchmarkPath}
		<path d={benchmarkPath} fill="rgba(148,163,184,0.1)" stroke="rgba(148,163,184,0.3)" stroke-width="0.8" />
	{/if}

	<!-- Company area -->
	<path
		d={companyPath}
		fill="rgba(234,70,71,0.2)"
		stroke="var(--color-dl-primary)"
		stroke-width="1.5"
	/>

	<!-- Dots on company polygon -->
	{#each axes as a, i}
		{@const r = (Math.min(100, Math.max(0, a.value)) / 100) * maxR}
		<circle cx={polarX(i, r)} cy={polarY(i, r)} r="2.5" fill="var(--color-dl-primary)" />
	{/each}

	<!-- Axis labels -->
	{#each axes as a, i}
		{@const lx = polarX(i, maxR + 11)}
		{@const ly = polarY(i, maxR + 11)}
		<text
			x={lx}
			y={ly}
			text-anchor={anchorFor(i)}
			dominant-baseline="central"
			class="radar-label"
		>{a.label}</text>
	{/each}
</svg>

<style>
	.radar {
		display: block;
		overflow: visible; /* 스포크 라벨이 viewBox 밖으로 나가도 클립되지 않게(겹침 완화 anchor-flip 보완) */
	}
	.radar-label {
		fill: var(--color-dl-text-muted);
		font-size: 9px;
		font-weight: 500;
	}
</style>
