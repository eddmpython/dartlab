<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import {
		forceSimulation,
		forceManyBody,
		forceCollide,
		forceCenter,
		forceLink,
		forceX,
		forceY
	} from 'd3-force';

	interface CompanyNode {
		id: string;
		label: string;
		stage: string;
		stageName?: string;
		role?: string;
		stream?: string;
		revenue: number;
		size: number;
		color: string;
		roe?: number | null;
		opMargin?: number | null;
		debtRatio?: number | null;
		[k: string]: any;
	}

	interface CompanyEdge {
		source: string;
		target: string;
		type: string;
		amount: number | null;
		ratio: number | null;
		product?: string;
		confidence?: number;
		[k: string]: any;
	}

	interface Props {
		nodes: CompanyNode[];
		links: CompanyEdge[];
		onNodeClick?: (n: CompanyNode | null) => void;
	}

	let { nodes, links, onNodeClick }: Props = $props();

	let container: HTMLDivElement | null = $state(null);
	let w = $state(1200);
	let h = $state(800);
	let simNodes: any[] = $state([]);
	let simLinks: any[] = $state([]);
	let hovered: string | null = $state(null);
	let selectedId: string | null = $state(null);
	let zoom = $state(1);
	let panX = $state(0);
	let panY = $state(0);
	let isDragging = $state(false);
	let lastMouse = { x: 0, y: 0 };
	let simulation: any = null;
	let builtSig = '';

	function nodeRadius(n: CompanyNode): number {
		// 매출(원 단위) → 4~22px
		const eok = (n.revenue || 0) / 1e8;
		return Math.max(4, Math.min(22, 3 + Math.log2(Math.max(1, eok / 100) + 1)));
	}

	function edgeWidth(e: any): number {
		if (e.amount) return Math.max(1.4, Math.min(5, 0.8 + Math.log10(e.amount + 1) * 0.6));
		return 1.4;
	}

	function dataSig(): string {
		return `${nodes.length}|${links.length}|${nodes
			.map((n) => n.id)
			.slice(0, 5)
			.join(',')}`;
	}

	function build() {
		if (!container || nodes.length === 0) {
			simNodes = [];
			simLinks = [];
			return;
		}
		const rect = container.getBoundingClientRect();
		w = rect.width || 1200;
		h = rect.height || 800;

		// stage별 그룹 중심점 (cluster force 대용)
		const stageKeys = [...new Set(nodes.map((n) => n.stage))];
		const cols = Math.ceil(Math.sqrt(stageKeys.length));
		const stageCenters = new Map<string, { x: number; y: number }>();
		stageKeys.forEach((k, i) => {
			const col = i % cols;
			const row = Math.floor(i / cols);
			stageCenters.set(k, {
				x: (w * (col + 0.5)) / cols,
				y: (h * (row + 0.5)) / Math.ceil(stageKeys.length / cols)
			});
		});

		simNodes = nodes.map((n) => {
			const c = stageCenters.get(n.stage) || { x: w / 2, y: h / 2 };
			return {
				...n,
				r: nodeRadius(n),
				x: c.x + (Math.random() - 0.5) * 80,
				y: c.y + (Math.random() - 0.5) * 80
			};
		});

		const byId = new Map(simNodes.map((n: any) => [n.id, n]));
		simLinks = links
			.filter((l) => byId.has(l.source) && byId.has(l.target))
			.map((l) => ({ ...l }));

		simulation?.stop();
		simulation = forceSimulation(simNodes)
			.force(
				'charge',
				forceManyBody<any>()
					.strength((d: any) => -d.r * 8)
					.distanceMax(220)
			)
			.force(
				'collide',
				forceCollide<any>()
					.radius((d: any) => d.r + 3)
					.strength(0.95)
					.iterations(3)
			)
			.force(
				'x',
				forceX<any>((d: any) => stageCenters.get(d.stage)?.x ?? w / 2).strength(0.18)
			)
			.force(
				'y',
				forceY<any>((d: any) => stageCenters.get(d.stage)?.y ?? h / 2).strength(0.22)
			)
			.force('center', forceCenter(w / 2, h / 2).strength(0.01))
			.force(
				'link',
				forceLink<any, any>(simLinks)
					.id((d: any) => d.id)
					.distance((l: any) => 30 + (l.amount ? 5 : 15))
					.strength(0.04)
			)
			.alphaDecay(0.025)
			.on('tick', () => {
				simNodes = [...simNodes];
				simLinks = [...simLinks];
			});
	}

	onMount(() => {
		build();
		builtSig = dataSig();
		const ro = new ResizeObserver(() => {
			if (!container) return;
			const rect = container.getBoundingClientRect();
			if (Math.abs(rect.width - w) > 4 || Math.abs(rect.height - h) > 4) {
				w = rect.width;
				h = rect.height;
				simulation?.alpha(0.3).restart();
			}
		});
		if (container) ro.observe(container);
		return () => {
			ro.disconnect();
			simulation?.stop();
		};
	});

	onDestroy(() => simulation?.stop());

	$effect(() => {
		if (!container) return;
		const sig = dataSig();
		if (sig !== builtSig) {
			build();
			builtSig = sig;
		}
	});

	// 색 동기화 · nodes prop 의 color 만 바뀌면 위치/시뮬 유지하고 색만 갱신
	$effect(() => {
		const colorById = new Map<string, string>();
		for (const n of nodes) colorById.set(n.id, n.color);
		let changed = false;
		for (const sn of simNodes) {
			const c = colorById.get(sn.id);
			if (c && sn.color !== c) {
				sn.color = c;
				changed = true;
			}
		}
		if (changed) simNodes = [...simNodes];
	});

	function isConnected(nodeId: string): boolean {
		if (!hovered) return true;
		if (nodeId === hovered) return true;
		return simLinks.some(
			(l: any) =>
				(l.source.id === hovered && l.target.id === nodeId) ||
				(l.target.id === hovered && l.source.id === nodeId)
		);
	}

	function edgeConnected(l: any): boolean {
		if (!hovered) return true;
		return l.source.id === hovered || l.target.id === hovered;
	}

	function handleClick(n: any) {
		selectedId = n.id;
		onNodeClick?.(n);
	}

	function onWheel(e: WheelEvent) {
		e.preventDefault();
		const delta = e.deltaY > 0 ? 0.9 : 1.1;
		const newZoom = Math.max(0.3, Math.min(5, zoom * delta));
		// 마우스 위치 기준 줌
		const rect = container!.getBoundingClientRect();
		const mx = e.clientX - rect.left;
		const my = e.clientY - rect.top;
		panX = mx - (mx - panX) * (newZoom / zoom);
		panY = my - (my - panY) * (newZoom / zoom);
		zoom = newZoom;
	}

	function onMouseDown(e: MouseEvent) {
		if ((e.target as Element).closest('.node')) return;
		isDragging = true;
		lastMouse = { x: e.clientX, y: e.clientY };
	}

	// 노드 드래그
	let dragNode: any = $state(null);
	let dragMoved = $state(false);

	function onNodeMouseDown(e: MouseEvent, n: any) {
		e.stopPropagation();
		dragNode = n;
		dragMoved = false;
		n.fx = n.x;
		n.fy = n.y;
	}

	function onNodeDoubleClick(n: any) {
		n.fx = null;
		n.fy = null;
		simulation?.alpha(0.3).restart();
	}

	function onMouseMove(e: MouseEvent) {
		if (dragNode && container) {
			dragMoved = true;
			const rect = container.getBoundingClientRect();
			const mx = (e.clientX - rect.left - panX) / zoom;
			const my = (e.clientY - rect.top - panY) / zoom;
			dragNode.fx = mx;
			dragNode.fy = my;
			dragNode.x = mx;
			dragNode.y = my;
			simulation?.alpha(0.3).restart();
			simNodes = [...simNodes];
			return;
		}
		if (!isDragging) return;
		panX += e.clientX - lastMouse.x;
		panY += e.clientY - lastMouse.y;
		lastMouse = { x: e.clientX, y: e.clientY };
	}

	function onMouseUp() {
		if (dragNode && !dragMoved) {
			// 간단 클릭으로 취급 (handleClick 은 원래 <g onclick> 에 위임)
			dragNode.fx = null;
			dragNode.fy = null;
		}
		dragNode = null;
		isDragging = false;
	}

	function resetView() {
		zoom = 1;
		panX = 0;
		panY = 0;
	}
</script>

<svelte:window onmousemove={onMouseMove} onmouseup={onMouseUp} />

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	bind:this={container}
	class="drilldown-container"
	onwheel={onWheel}
	onmousedown={onMouseDown}
	role="application"
	aria-label="산업 내부 지도"
>
	<svg width={w} height={h}>
		<defs>
			<filter id="dd-glow" x="-50%" y="-50%" width="200%" height="200%">
				<feGaussianBlur stdDeviation="1.5" result="blur" />
				<feMerge>
					<feMergeNode in="blur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
		</defs>

		<g transform="translate({panX},{panY}) scale({zoom})">
			<!-- 엣지 -->
			<g class="edges">
				{#each simLinks as l, i (i)}
					{@const sx = l.source.x ?? 0}
					{@const sy = l.source.y ?? 0}
					{@const tx = l.target.x ?? 0}
					{@const ty = l.target.y ?? 0}
					<line
						x1={sx}
						y1={sy}
						x2={tx}
						y2={ty}
						stroke={l.amount ? '#fbbf24' : '#ec4899'}
						stroke-width={edgeWidth(l)}
						stroke-linecap="round"
						opacity={edgeConnected(l) ? (hovered ? 0.95 : 0.55) : 0.08}
					/>
				{/each}
			</g>

			<!-- 노드 -->
			<g class="nodes">
				{#each simNodes as n (n.id)}
					{@const stroke = n.stream === 'upstream'
						? '#8b5cf6'
						: n.stream === 'downstream'
							? '#f97316'
							: '#f8fafc'}
					<g
						class="node"
						class:dim={!isConnected(n.id)}
						class:selected={selectedId === n.id}
						class:fixed={n.fx != null}
						transform="translate({n.x ?? 0},{n.y ?? 0})"
						onmouseenter={() => (hovered = n.id)}
						onmouseleave={() => (hovered = null)}
						onmousedown={(e: MouseEvent) => onNodeMouseDown(e, n)}
						onclick={() => !dragMoved && handleClick(n)}
						ondblclick={() => onNodeDoubleClick(n)}
						role="button"
						tabindex="0"
						onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && handleClick(n)}
					>
						{#if selectedId === n.id || hovered === n.id}
							<circle
								r={n.r + 4}
								fill="none"
								stroke={n.color}
								stroke-width="2"
								opacity="0.9"
							/>
						{/if}
						<circle
							r={n.r}
							fill={n.color}
							fill-opacity={hovered === n.id ? 1 : 0.88}
							{stroke}
							stroke-width={1.2}
						/>
						<text
							class="node-label"
							class:label-emph={hovered === n.id || selectedId === n.id}
							text-anchor="middle"
							dominant-baseline="central"
							y={-(n.r + 9)}
							font-size={hovered === n.id || selectedId === n.id
								? Math.max(11, Math.min(13, n.r * 0.7))
								: Math.max(8, Math.min(11, n.r * 0.6))}
						>
							{n.label}
						</text>
					</g>
				{/each}
			</g>
		</g>
	</svg>

	<!-- 우상단: 화면 배율/초기화만 (브랜드 버튼은 좌측 사이드바에) -->
	<button class="zoom-btn" onclick={resetView} title="화면 초기화 (더블클릭으로 reset)">
		{zoom.toFixed(1)}× ⟳
	</button>

	<!-- 범례: stream stroke -->
	<div class="legend">
		<div class="legend-item">
			<span class="legend-stroke up"></span>
			<span>upstream (상류)</span>
		</div>
		<div class="legend-item">
			<span class="legend-stroke mid"></span>
			<span>midstream (중류)</span>
		</div>
		<div class="legend-item">
			<span class="legend-stroke down"></span>
			<span>downstream (하류)</span>
		</div>
		<div class="legend-note">테두리 = 위치 / 채움 = 색상 기준 / 크기 = 매출</div>
	</div>

	{#if simNodes.length === 0}
		<div class="empty">표시할 회사가 없습니다 · 좌측 공정 필터를 확인하세요.</div>
	{/if}
</div>

<style>
	.drilldown-container {
		position: relative;
		width: 100%;
		height: 100%;
		background: radial-gradient(
				ellipse at center,
				rgba(30, 41, 59, 0.25) 0%,
				transparent 70%
			),
			#050811;
		overflow: hidden;
		cursor: grab;
	}
	.drilldown-container:active {
		cursor: grabbing;
	}
	svg {
		display: block;
	}
	.node {
		cursor: pointer;
		transition: opacity 0.15s;
	}
	.node circle {
		transition:
			r 400ms cubic-bezier(0.4, 0, 0.2, 1),
			fill 300ms ease,
			stroke 300ms ease,
			fill-opacity 200ms ease;
	}
	.edges line {
		transition:
			stroke 300ms ease,
			stroke-width 300ms ease,
			opacity 250ms ease;
	}
	.node-label {
		transition:
			font-size 300ms ease,
			fill 200ms ease,
			opacity 200ms ease;
	}
	.node.dim {
		opacity: 0.18;
	}
	.node.fixed circle {
		stroke-dasharray: 4 2;
	}
	.node:hover circle {
		filter: brightness(1.15);
	}
	@media (prefers-reduced-motion: reduce) {
		.node,
		.node circle,
		.edges line,
		.node-label {
			transition: none !important;
		}
	}
	.node-label {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 500;
		fill: #cbd5e1;
		paint-order: stroke fill;
		stroke: rgba(5, 8, 17, 0.95);
		stroke-width: 3px;
		stroke-linejoin: round;
		pointer-events: none;
		user-select: none;
	}
	.node-label.label-emph {
		fill: #f8fafc;
		font-weight: 700;
	}
	.node.dim .node-label {
		opacity: 0.35;
	}

	.zoom-btn {
		position: absolute;
		top: 16px;
		right: 16px;
		background: rgba(15, 18, 25, 0.85);
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #cbd5e1;
		font-size: 11px;
		font-family: monospace;
		padding: 6px 10px;
		height: 30px;
		cursor: pointer;
		backdrop-filter: blur(8px);
		z-index: 4;
	}
	.zoom-btn:hover {
		background: rgba(30, 36, 51, 0.95);
		border-color: #334155;
		color: #f1f5f9;
	}

	.legend {
		position: absolute;
		left: 16px;
		bottom: 16px;
		background: rgba(15, 18, 25, 0.85);
		border: 1px solid #1e2433;
		border-radius: 8px;
		padding: 10px 12px;
		font-size: 11px;
		color: #cbd5e1;
		backdrop-filter: blur(8px);
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.legend-stroke {
		display: inline-block;
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #050811;
	}
	.legend-stroke.up {
		border: 2px solid #8b5cf6;
	}
	.legend-stroke.mid {
		border: 2px solid #f8fafc;
	}
	.legend-stroke.down {
		border: 2px solid #f97316;
	}
	.legend-note {
		margin-top: 4px;
		color: #64748b;
		font-size: 10px;
	}
	.empty {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #64748b;
		font-size: 13px;
		pointer-events: none;
	}
</style>
