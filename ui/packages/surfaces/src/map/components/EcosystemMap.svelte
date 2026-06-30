<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	let cleanupFns: Array<() => void> = [];
	onDestroy(() => {
		for (const fn of cleanupFns) fn();
	});

	interface NodeDatum {
		id: string;
		label: string;
		industry: string;
		industryName: string;
		stage: string;
		revenue: number;
		size: number;
		color: string;
		isIndustry?: boolean;
		nodeCount?: number;
		x?: number;
		y?: number;
	}

	interface LinkDatum {
		source: string;
		target: string;
		type: string;
		amount: number | null;
		ratio: number | null;
		product: string;
		confidence: number;
		source_tag: string;
		edgeCount?: number;
	}

	interface IndustryMeta {
		id: string;
		name: string;
		color: string;
		count: number;
		x?: number;
		y?: number;
		radius?: number;
		totalRevenue?: number;
	}
	interface IndustryFlow {
		fromIndustry: string;
		toIndustry: string;
		edgeCount: number;
		amount: number;
	}

	interface Props {
		nodes: NodeDatum[];
		links: LinkDatum[];
		isAtlas?: boolean;
		industriesProp?: IndustryMeta[];
		industryFlows?: IndustryFlow[];
		onNodeClick?: (node: NodeDatum | null) => void;
		onNodeHover?: (node: NodeDatum | null) => void;
		onIndustryClick?: (industryId: string) => void;
	}

	let {
		nodes,
		links,
		isAtlas = false,
		industriesProp = [],
		industryFlows = [],
		onNodeClick,
		onNodeHover,
		onIndustryClick
	}: Props = $props();

	let container: HTMLDivElement | null = $state(null);
	let graph: any = $state(null);
	let currentZoom = $state(1);
	let hoveredNode: NodeDatum | null = $state(null);
	let industryLabels: Array<{ name: string; color: string; x: number; y: number; count: number; totalRev: number; radius: number }> =
		$state([]);
	let companyLabels: Array<{ id: string; name: string; x: number; y: number; rev: number }> = $state([]);

	// semantic zoom · 산업 버블/flow 화면 좌표
	let industryNodesOnScreen: Array<{
		id: string; name: string; color: string; count: number;
		sx: number; sy: number; sr: number; revLabel: string;
	}> = $state([]);
	let flowsOnScreen: Array<{ key: string; path: string; width: number }> = $state([]);

	function fmtRev(v: number): string {
		if (v >= 1e12) return `${(v / 1e12).toFixed(0)}조`;
		if (v >= 1e8) return `${Math.round(v / 1e8).toLocaleString()}억`;
		return `${v.toLocaleString()}`;
	}

	function updateLabels() {
		if (!graph || !container) return;
		const positions = graph.getNodePositions();
		if (!positions) return;

		const zoom = currentZoom;

		// 산업별 집계
		const byIndustry: Record<
			string,
			{ xs: number[]; ys: number[]; name: string; color: string; totalRev: number }
		> = {};
		// 개별 회사 (줌 레벨에 따라 top N)
		const rendered: typeof companyLabels = [];
		const sortedByRev = [...nodes].sort((a, b) => (b.revenue || 0) - (a.revenue || 0));

		// atlas 뷰 (34개 산업): 모두 항상 라벨 표시. companies/industry: 줌에 따라 top N
		const topN = isAtlas
			? nodes.length
			: zoom < 1.5
				? 10
				: zoom < 3
					? 50
					: zoom < 5
						? 200
						: zoom < 8
							? 500
							: 1500;

		for (const n of nodes) {
			const pos = positions[n.id];
			if (!pos) continue;

			if (!byIndustry[n.industry]) {
				byIndustry[n.industry] = { xs: [], ys: [], name: n.industryName, color: n.color, totalRev: 0 };
			}
			byIndustry[n.industry].xs.push(pos.x);
			byIndustry[n.industry].ys.push(pos.y);
			byIndustry[n.industry].totalRev += n.revenue || 0;
		}

		// 산업 라벨
		const indLabels: typeof industryLabels = [];
		for (const [_id, d] of Object.entries(byIndustry)) {
			if (d.xs.length < 3) continue;
			const sx = [...d.xs].sort((a, b) => a - b);
			const sy = [...d.ys].sort((a, b) => a - b);
			const cx = sx[Math.floor(sx.length / 2)];
			const cy = sy[Math.floor(sy.length / 2)];
			const screen = graph.spaceToScreenPosition([cx, cy]);
			if (!screen) continue;
			// 반지름: 노드 좌표 분산으로 클러스터 크기 추정
			const maxDx = Math.max(...d.xs) - Math.min(...d.xs);
			const maxDy = Math.max(...d.ys) - Math.min(...d.ys);
			// 스크린 좌표 기준 반지름 (edge에서 다른 점으로 변환)
			const edgeScreen = graph.spaceToScreenPosition([cx + maxDx / 2, cy]);
			const screenRadius = edgeScreen ? Math.abs(edgeScreen[0] - screen[0]) + 10 : 40;

			indLabels.push({
				name: d.name,
				color: d.color,
				x: screen[0],
				y: screen[1],
				count: d.xs.length,
				totalRev: d.totalRev,
				radius: screenRadius,
			});
		}
		industryLabels = indLabels;

		// 회사 라벨 (매출 상위 N)
		if (topN > 0) {
			const visibleIds = new Set(sortedByRev.slice(0, topN).map((n) => n.id));
			for (const n of nodes) {
				if (!visibleIds.has(n.id)) continue;
				const pos = positions[n.id];
				if (!pos) continue;
				const screen = graph.spaceToScreenPosition([pos.x, pos.y]);
				if (!screen) continue;
				rendered.push({ id: n.id, name: n.label, x: screen[0], y: screen[1], rev: n.revenue || 0 });
			}
		}
		companyLabels = rendered;

		// semantic zoom: 산업 버블 + flow 화면 좌표
		if (!isAtlas && industriesProp.length > 0 && currentZoom < 2.5) {
			const indScreens: typeof industryNodesOnScreen = [];
			const indMap: Record<string, { sx: number; sy: number; sr: number; color: string }> = {};
			for (const ind of industriesProp) {
				if (ind.x == null || ind.y == null) continue;
				const c = graph.spaceToScreenPosition([ind.x, ind.y]);
				if (!c) continue;
				// 반지름: space 좌표계 → 화면 픽셀 (edge 점으로 변환해서 거리)
				const rEdge = graph.spaceToScreenPosition([ind.x + (ind.radius || 100), ind.y]);
				const sr = rEdge ? Math.abs(rEdge[0] - c[0]) : 40;
				indScreens.push({
					id: ind.id,
					name: ind.name,
					color: ind.color,
					count: ind.count,
					sx: c[0],
					sy: c[1],
					sr: Math.max(30, sr),
					revLabel: fmtRev(ind.totalRevenue || 0)
				});
				indMap[ind.id] = { sx: c[0], sy: c[1], sr: Math.max(30, sr), color: ind.color };
			}
			industryNodesOnScreen = indScreens;

			// flow 엣지 (산업 centroid 간 곡선)
			const flowList: typeof flowsOnScreen = [];
			const maxAmount = Math.max(...industryFlows.map((f) => f.amount || f.edgeCount || 1), 1);
			for (const f of industryFlows) {
				const a = indMap[f.fromIndustry];
				const b = indMap[f.toIndustry];
				if (!a || !b) continue;
				// 곡선 제어점: 중앙에서 수직으로 offset
				const mx = (a.sx + b.sx) / 2;
				const my = (a.sy + b.sy) / 2;
				const dx = b.sx - a.sx;
				const dy = b.sy - a.sy;
				const nx = -dy * 0.15;
				const ny = dx * 0.15;
				const path = `M${a.sx},${a.sy} Q${mx + nx},${my + ny} ${b.sx},${b.sy}`;
				const weight = (f.amount || f.edgeCount * 1e9) / maxAmount;
				const width = Math.max(1, Math.min(6, 0.8 + Math.log2(weight * 10 + 1) * 1.5));
				flowList.push({
					key: `${f.fromIndustry}→${f.toIndustry}`,
					path,
					width
				});
			}
			flowsOnScreen = flowList;
		} else if (industryNodesOnScreen.length > 0) {
			industryNodesOnScreen = [];
			flowsOnScreen = [];
		}
	}

	onMount(async () => {
		if (!container) return;

		// dynamic import to code-split Cosmos out of main bundle
		const { Graph } = await import('@cosmograph/cosmos');

		const canvas = document.createElement('canvas');
		container.appendChild(canvas);

		graph = new Graph(canvas, {
			spaceSize: 16384,
			backgroundColor: '#050811',
			nodeSize: (n: NodeDatum) => {
				if (n.isIndustry) return Math.max(10, Math.min(40, n.size * 2));
				return Math.max(3, Math.min(14, n.size * 1.5));
			},
			nodeColor: (n: NodeDatum) => n.color,
			nodeGreyoutOpacity: 0.12,
			linkColor: (l: LinkDatum) => {
				if (l.type === 'supplier') return l.amount ? '#fbbf24' : '#f97316';
				if (l.type === 'customer') return '#60a5fa';
				if (l.type === 'investor') return '#a78bfa';
				return '#6b7280';
			},
			linkWidth: (l: LinkDatum) => {
				if (l.edgeCount) {
					return Math.max(2.5, Math.min(9, 1.2 + Math.log2(l.edgeCount + 1) * 1.3));
				}
				if (!l.amount) return 1.5;
				return Math.max(1.5, Math.min(7, 1.5 + Math.log10(l.amount + 1) * 0.8));
			},
			// companies: 줌 아웃 시 엣지 짧아 숨김, 줌 인하면 화면상 길어져 표시
			linkGreyoutOpacity: isAtlas ? 0.25 : 0.35,
			linkArrows: false,
			linkVisibilityDistanceRange: isAtlas ? [300, 2000] : [30, 400],
			linkVisibilityMinTransparency: isAtlas ? 0.75 : 0.1,
			curvedLinks: true,
			curvedLinkSegments: 16,
			simulation: {
				repulsion: isAtlas ? 1.0 : 0,
				gravity: isAtlas ? 0.15 : 0,
				linkDistance: isAtlas ? 10 : 0,
				linkSpring: isAtlas ? 1 : 0,
				friction: isAtlas ? 0.85 : 1,
				decay: isAtlas ? 1000 : 1,
				onTick: () => updateLabels(),
			},
			events: {
				onClick: (node: NodeDatum | undefined) => {
					onNodeClick?.(node ?? null);
					if (node && graph) {
						graph.zoomToNodeById(node.id, 700, 6, false);
					}
				},
				onNodeMouseOver: (node: NodeDatum) => {
					hoveredNode = node;
					onNodeHover?.(node);
				},
				onNodeMouseOut: () => {
					hoveredNode = null;
					onNodeHover?.(null);
				},
				onZoom: () => {
					if (graph) {
						const prevZoom = currentZoom;
						currentZoom = graph.getZoomLevel();
						updateLabels();
						// companies 뷰: 줌 기반 엣지 토글 (임계값 2.5)
						if (!isAtlas) {
							const showCompanyEdges = currentZoom >= 2.5;
							const wasShowing = prevZoom >= 2.5;
							if (showCompanyEdges !== wasShowing) {
								graph.setData(nodes, showCompanyEdges ? links : []);
							}
						}
					}
				},
			},
		});

		// 초기: atlas는 링크 포함, companies는 축소 상태라 링크 없이 시작
		graph.setData(nodes, isAtlas ? links : []);

		// fit view after initial simulation
		setTimeout(() => graph?.fitView(400), 1200);

		// raf 루프로 라벨 위치 갱신 (simulation tick 외 팬/줌 시에도)
		let rafId: number;
		const tick = () => {
			updateLabels();
			rafId = requestAnimationFrame(tick);
		};
		rafId = requestAnimationFrame(tick);

		// ResizeObserver
		const ro = new ResizeObserver(() => {
			if (canvas && container) {
				canvas.width = container.clientWidth;
				canvas.height = container.clientHeight;
			}
		});
		ro.observe(container);

		cleanupFns.push(() => {
			cancelAnimationFrame(rafId);
			ro.disconnect();
			graph?.destroy?.();
		});
	});

	// props(nodes/links) 변경 시 Cosmograph 데이터 재설정
	$effect(() => {
		if (!graph) return;
		graph.setData(nodes, links);
	});

	// 외부 제어 함수
	export function zoomToNode(id: string) {
		graph?.zoomToNodeById(id, 700, 6, false);
	}
	export function resetView() {
		graph?.fitView(700);
	}
	export function setSelection(ids: string[] | null) {
		if (!graph) return;
		if (ids && ids.length) graph.selectNodesByIds(ids);
		else graph.unselectNodes();
	}
</script>

<div bind:this={container} class="ecosystem-container">
	<!-- 라벨 오버레이 -->
	<svg class="label-overlay" xmlns="http://www.w3.org/2000/svg">
		<!-- 산업 semantic zoom 레이어 (줌 < 2.5에서 atlas처럼 보임) -->
		{#if !isAtlas && industryNodesOnScreen.length > 0}
			{@const overlayOpacity = currentZoom < 2 ? 1 : currentZoom < 2.5 ? (2.5 - currentZoom) * 2 : 0}
			{#if overlayOpacity > 0}
				<g class="industry-layer" style="opacity:{overlayOpacity}; pointer-events:{currentZoom < 2.5 ? 'auto' : 'none'}">
					<!-- 산업간 flow 엣지 (곡선) -->
					{#each flowsOnScreen as flow (flow.key)}
						<path
							d={flow.path}
							fill="none"
							stroke="#fbbf24"
							stroke-width={flow.width}
							stroke-opacity={0.55}
							stroke-linecap="round"
						/>
					{/each}
					<!-- 산업 큰 버블 -->
					{#each industryNodesOnScreen as ind (ind.id)}
						<circle
							cx={ind.sx}
							cy={ind.sy}
							r={ind.sr}
							fill={ind.color}
							fill-opacity="0.25"
							stroke={ind.color}
							stroke-width="2"
							stroke-opacity="0.9"
							class="ind-bubble"
							onclick={() => onIndustryClick?.(ind.id)}
						/>
						<text
							x={ind.sx}
							y={ind.sy - 4}
							text-anchor="middle"
							dominant-baseline="central"
							font-size={Math.max(14, Math.min(32, ind.sr / 3))}
							font-weight="700"
							fill={ind.color}
							class="ind-label"
							pointer-events="none"
						>{ind.name}</text>
						<text
							x={ind.sx}
							y={ind.sy + Math.max(14, Math.min(32, ind.sr / 3)) - 2}
							text-anchor="middle"
							dominant-baseline="central"
							font-size="11"
							fill="#cbd5e1"
							pointer-events="none"
						>{ind.count}사 · {ind.revLabel}</text>
					{/each}
				</g>
			{/if}
		{/if}
		<!-- 기존 회사 클러스터 배경 (줌 인 시) -->
		{#if currentZoom >= 2 && currentZoom < 6 && !isAtlas}
			{#each industryLabels as label (label.name)}
				<circle
					cx={label.x}
					cy={label.y}
					r={label.radius}
					fill={label.color}
					opacity={currentZoom < 3 ? 0.06 : 0.04}
					stroke={label.color}
					stroke-width="0.5"
					stroke-opacity="0.12"
				/>
			{/each}
		{/if}
		<!-- 산업 클러스터 라벨 (줌 아웃~중간) -->
		{#if currentZoom < 4}
			{#each industryLabels as label (label.name)}
				<g transform="translate({label.x}, {label.y})">
					<text
						class="industry-label"
						text-anchor="middle"
						dominant-baseline="central"
						font-size={Math.max(16, Math.min(36, 14 + Math.log2(label.count) * 3))}
						fill={label.color}
						opacity={currentZoom < 2 ? 0.95 : currentZoom < 3 ? 0.7 : 0.4}
					>
						{label.name}
					</text>
					<text
						class="industry-sub"
						text-anchor="middle"
						dominant-baseline="central"
						y={Math.max(18, Math.min(28, 14 + Math.log2(label.count) * 2))}
						font-size="10"
						fill="#94a3b8"
						opacity={currentZoom < 2 ? 0.8 : 0.4}
					>
						{label.count}사 · {label.totalRev >= 1e13
							? `${(label.totalRev / 1e12).toFixed(0)}조`
							: label.totalRev >= 1e11
								? `${(label.totalRev / 1e12).toFixed(1)}조`
								: `${Math.round(label.totalRev / 1e8)}억`}
					</text>
				</g>
			{/each}
		{/if}

		<!-- 회사 라벨 (줌 인 상태) -->
		{#if currentZoom >= 2}
			{#each companyLabels as label (label.id)}
				<text
					class="company-label"
					x={label.x}
					y={label.y - 10}
					text-anchor="middle"
					font-size={Math.min(13, 8 + currentZoom * 0.3)}
					opacity={currentZoom < 4 ? 0.7 : 0.95}
				>
					{label.name}
				</text>
			{/each}
		{/if}
	</svg>

	{#if hoveredNode}
		<div class="hover-chip">
			<strong>{hoveredNode.label}</strong>
			<span class="industry">{hoveredNode.industryName}</span>
			{#if hoveredNode.stage}
				<span class="stage">{hoveredNode.stage}</span>
			{/if}
			{#if hoveredNode.revenue > 0}
				<span class="revenue">
					{hoveredNode.revenue >= 1e12
						? `${(hoveredNode.revenue / 1e12).toFixed(1)}조`
						: `${Math.round(hoveredNode.revenue / 1e8).toLocaleString()}억`}원
				</span>
			{/if}
		</div>
	{/if}

	<div class="zoom-indicator" title="마우스 휠 / 트랙패드로 확대·축소">
		{currentZoom.toFixed(1)}×
	</div>
</div>

<style>
	.ecosystem-container {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
		background: #050811;
	}
	:global(.ecosystem-container canvas) {
		display: block;
		width: 100%;
		height: 100%;
	}
	.industry-layer {
		transition: opacity 300ms ease;
	}
	.ind-bubble {
		cursor: pointer;
		transition: fill-opacity 150ms ease;
	}
	.ind-bubble:hover {
		fill-opacity: 0.4;
	}
	.ind-label {
		font-family: 'Pretendard Variable', sans-serif;
		letter-spacing: -0.02em;
	}
	.label-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	.industry-label {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 700;
		letter-spacing: -0.02em;
		paint-order: stroke fill;
		stroke: #050811;
		stroke-width: 4px;
		stroke-linejoin: round;
		transition: opacity 0.2s;
	}
	.industry-sub {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 500;
		paint-order: stroke fill;
		stroke: #050811;
		stroke-width: 3px;
		stroke-linejoin: round;
		transition: opacity 0.2s;
	}
	.company-label {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 500;
		fill: #f1f5f9;
		paint-order: stroke fill;
		stroke: #050811;
		stroke-width: 2.5px;
		stroke-linejoin: round;
		transition: opacity 0.2s;
		pointer-events: none;
	}
	.hover-chip {
		position: absolute;
		bottom: 16px;
		left: 50%;
		transform: translateX(-50%);
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 9999px;
		padding: 8px 16px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
		font-size: 13px;
		color: #f1f5f9;
		display: flex;
		gap: 8px;
		align-items: center;
		pointer-events: none;
		white-space: nowrap;
	}
	.hover-chip .industry {
		color: #a78bfa;
		font-size: 11px;
		padding: 2px 6px;
		background: rgba(167, 139, 250, 0.15);
		border-radius: 4px;
	}
	.hover-chip .stage {
		color: #34d399;
		font-size: 11px;
		padding: 2px 6px;
		background: rgba(52, 211, 153, 0.15);
		border-radius: 4px;
	}
	.hover-chip .revenue {
		color: var(--amber);
		font-weight: 600;
	}
	.zoom-indicator {
		position: absolute;
		top: 16px;
		right: 16px;
		background: rgba(15, 18, 25, 0.85);
		border: 1px solid #1e2433;
		border-radius: 6px;
		padding: 6px 10px;
		font-size: 11px;
		color: #94a3b8;
		font-family: monospace;
		backdrop-filter: blur(8px);
		cursor: help;
		z-index: 4;
	}
</style>
