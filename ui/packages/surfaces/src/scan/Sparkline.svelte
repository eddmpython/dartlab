<script lang="ts">
	/** 미니 sparkline · pure SVG, no deps. mono color, smooth curve. */
	interface Props {
		data: (number | null | undefined)[];
		width?: number;
		height?: number;
		stroke?: string;
		fill?: string;
		showDots?: boolean;
		smooth?: boolean;
	}

	let {
		data = [],
		width = 120,
		height = 36,
		stroke = 'currentColor',
		fill = 'none',
		showDots = false,
		smooth = true
	}: Props = $props();

	const cleaned = $derived(data.map((v) => (typeof v === 'number' && Number.isFinite(v) ? v : null)));

	const stats = $derived.by(() => {
		const valid = cleaned.filter((v): v is number => v != null);
		if (valid.length === 0) return { min: 0, max: 1 };
		const min = Math.min(...valid);
		const max = Math.max(...valid);
		return { min, max: max === min ? min + 1 : max };
	});

	const pad = 2;
	const points = $derived.by(() => {
		const w = width - pad * 2;
		const h = height - pad * 2;
		const range = stats.max - stats.min;
		return cleaned.map((v, i) => {
			if (v == null) return null;
			const x = pad + (i / Math.max(cleaned.length - 1, 1)) * w;
			const y = pad + (1 - (v - stats.min) / range) * h;
			return [x, y] as [number, number];
		});
	});

	const path = $derived.by(() => {
		const valid = points.filter(
			(p): p is [number, number] =>
				p != null && Number.isFinite(p[0]) && Number.isFinite(p[1])
		);
		if (valid.length < 2) return '';
		if (!smooth || valid.length < 3) {
			return valid.map(([x, y], i) => (i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`)).join(' ');
		}
		// Catmull-Rom → Bézier (smooth)
		let d = `M ${valid[0][0]} ${valid[0][1]}`;
		for (let i = 0; i < valid.length - 1; i++) {
			const p0 = valid[i - 1] ?? valid[i];
			const p1 = valid[i];
			const p2 = valid[i + 1];
			const p3 = valid[i + 2] ?? p2;
			const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
			const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
			const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
			const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
			d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2[0]} ${p2[1]}`;
		}
		return d;
	});
</script>

<svg viewBox="0 0 {width} {height}" {width} {height} class="spark" role="img" aria-hidden="true">
	{#if path}
		<path d={path} {stroke} stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" {fill} />
		{#if showDots}
			{#each points as p}
				{#if p}
					<circle cx={p[0]} cy={p[1]} r="2" {fill} stroke="none" />
				{/if}
			{/each}
		{/if}
	{/if}
</svg>

<style>
	.spark { display: inline-block; vertical-align: middle; }
</style>
