<script lang="ts">
	/** P&L Sankey · 매출 → COGS / 영업이익 → SG&A / 순이익 흐름
	 *  pure SVG, no deps. dartlab editorial dark + brand color.
	 */

	interface Flow {
		from: string;
		to: string;
		value: number;
		tone?: 'brand' | 'good' | 'warn' | 'bad' | 'neutral';
	}

	interface Props {
		flows: Flow[];
		width?: number;
		height?: number;
	}

	let { flows = [], width = 720, height = 280 }: Props = $props();

	// 노드 자동 추출 + 레이어 결정
	type NodeInfo = { id: string; layer: number; value: number };
	const nodes = $derived.by(() => {
		const map = new Map<string, NodeInfo>();
		// 첫 from 은 layer 0, to 는 from layer + 1
		const layerOf: Record<string, number> = {};
		for (const f of flows) {
			if (!(f.from in layerOf)) layerOf[f.from] = 0;
			const tgtLayer = (layerOf[f.from] ?? 0) + 1;
			if (!(f.to in layerOf) || layerOf[f.to] < tgtLayer) layerOf[f.to] = tgtLayer;
		}
		// value: from 노드는 outflow 합, to 노드는 inflow 합
		const inflow: Record<string, number> = {};
		const outflow: Record<string, number> = {};
		for (const f of flows) {
			outflow[f.from] = (outflow[f.from] ?? 0) + f.value;
			inflow[f.to] = (inflow[f.to] ?? 0) + f.value;
		}
		const allIds = new Set<string>([...Object.keys(layerOf)]);
		for (const id of allIds) {
			map.set(id, {
				id,
				layer: layerOf[id] ?? 0,
				value: Math.max(inflow[id] ?? 0, outflow[id] ?? 0)
			});
		}
		return [...map.values()];
	});

	const layerCount = $derived(Math.max(...nodes.map((n) => n.layer), 0) + 1);
	const colW = $derived(width / Math.max(layerCount, 1));
	const nodeW = 14;
	const margin = 12;

	// 노드별 y 위치 · 동일 레이어 안에서 value 비례 stacking
	const nodePos = $derived.by(() => {
		const layers: Record<number, NodeInfo[]> = {};
		for (const n of nodes) (layers[n.layer] ??= []).push(n);
		const pos = new Map<string, { x: number; y: number; h: number }>();
		const usableH = height - margin * 2;
		for (const layer in layers) {
			const list = layers[layer].sort((a, b) => b.value - a.value);
			const total = list.reduce((s, n) => s + n.value, 0) || 1;
			let y = margin;
			for (const n of list) {
				const h = (n.value / total) * (usableH - (list.length - 1) * 6);
				pos.set(n.id, { x: Number(layer) * colW + 2, y, h });
				y += h + 6;
			}
		}
		return pos;
	});

	// flow path · bezier between nodes
	function flowPath(f: Flow) {
		const from = nodePos.get(f.from);
		const to = nodePos.get(f.to);
		if (!from || !to) return '';
		const fromNode = nodes.find((n) => n.id === f.from);
		const toNode = nodes.find((n) => n.id === f.to);
		if (!fromNode || !toNode) return '';

		const fromTotal = fromNode.value || 1;
		const toTotal = toNode.value || 1;
		const fh = (f.value / fromTotal) * from.h;
		const th = (f.value / toTotal) * to.h;

		// 단순 시작점: from 의 위에서부터 누적 (우선 평균선으로 구현)
		const fy = from.y + from.h / 2 - fh / 2;
		const ty = to.y + to.h / 2 - th / 2;
		const x1 = from.x + nodeW;
		const x2 = to.x;
		const cx = (x1 + x2) / 2;

		return `M ${x1} ${fy}
			C ${cx} ${fy}, ${cx} ${ty}, ${x2} ${ty}
			L ${x2} ${ty + th}
			C ${cx} ${ty + th}, ${cx} ${fy + fh}, ${x1} ${fy + fh}
			Z`;
	}

	const flowColor: Record<string, string> = {
		brand: 'var(--dl-orange)',
		good: 'var(--dl-good)',
		warn: 'var(--dl-warn)',
		bad: 'var(--dl-bad)',
		neutral: 'var(--dl-ink-faint)'
	};
</script>

<svg viewBox="0 0 {width} {height}" {width} {height} class="sankey">
	<!-- flows -->
	{#each flows as f}
		<path d={flowPath(f)} fill={flowColor[f.tone ?? 'brand']} fill-opacity="0.28" />
	{/each}

	<!-- nodes -->
	{#each nodes as n}
		{@const p = nodePos.get(n.id)}
		{#if p}
			<rect x={p.x} y={p.y} width={nodeW} height={p.h} rx="2" fill="var(--dl-ink-mute)" opacity="0.6" />
			<text
				x={n.layer === 0 ? p.x + nodeW + 6 : p.x - 6}
				y={p.y + p.h / 2}
				dominant-baseline="middle"
				text-anchor={n.layer === 0 ? 'start' : 'end'}
				font-size="11"
				font-family="var(--dl-font-ui)"
				fill="var(--dl-ink)"
				font-weight="500"
			>
				{n.id}
			</text>
		{/if}
	{/each}
</svg>

<style>
	.sankey { width: 100%; height: auto; max-width: 100%; }
</style>
