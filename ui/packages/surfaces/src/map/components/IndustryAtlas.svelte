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

	interface IndustryNode {
		id: string;
		name: string;
		revenue: number; // 억 단위
		nodeCount: number;
		color: string;
		stageMix?: Record<string, number>;
		stages?: any[];
	}

	interface FlowEdge {
		fromIndustry: string;
		toIndustry: string;
		edgeCount: number;
		amount: number;
	}

	interface Props {
		industries: IndustryNode[];
		flows: FlowEdge[];
		onSelect?: (ind: IndustryNode) => void;
		colorMetric?: string;
		// 타임라인 · 선택 연도의 산업별 totalRevenue (원 단위)
		timelineYear?: string;
		industryTotalsByYear?: Record<string, Record<string, { totalRevenue: number; count: number; avgOpm: number | null }>>;
		// 변화감지 렌즈 · 산업별 movers 카운트 (>0 면 펄스 링)
		moversByIndustry?: Map<string, number>;
	}

	let {
		industries,
		flows,
		onSelect,
		colorMetric = 'industry',
		timelineYear = '',
		industryTotalsByYear = {},
		moversByIndustry = new Map()
	}: Props = $props();

	function metricLabel(ind: IndustryNode): string {
		if (colorMetric === 'industry') return '';
		const v = (ind as any).metricValue;
		if (v === null || v === undefined || Number.isNaN(v)) return '';
		if (colorMetric === 'govGrade' || colorMetric === 'qualGrade') {
			return `${v.toFixed(1)}/4`;
		}
		if (colorMetric === 'revenue') {
			// 원 단위 합 → 억/조 표기
			const eok = v / 1e8;
			if (eok >= 10000) return `${(eok / 10000).toFixed(1)}조`;
			return `${Math.round(eok).toLocaleString()}억`;
		}
		if (colorMetric === 'empCount') {
			return `${Math.round(v).toLocaleString()}명`;
		}
		// %
		return `${v.toFixed(1)}%`;
	}

	let container: HTMLDivElement | null = $state(null);
	let w = $state(1200);
	let h = $state(800);
	let simNodes: any[] = $state([]);
	let simLinks: any[] = $state([]);
	let hovered: string | null = $state(null);
	let simulation: any = null;

	// 팬·줌 상태
	let zoom = $state(1);
	let panX = $state(0);
	let panY = $state(0);
	let isPanning = $state(false);
	let panStart = { x: 0, y: 0, px: 0, py: 0 };

	// 노드 드래그 상태
	let dragNode: any = $state(null);
	let dragMoved = $state(false);

	function onWheel(e: WheelEvent) {
		e.preventDefault();
		const factor = e.deltaY > 0 ? 0.9 : 1.1;
		const newZoom = Math.max(0.3, Math.min(5, zoom * factor));
		if (!container) return;
		const rect = container.getBoundingClientRect();
		const mx = e.clientX - rect.left;
		const my = e.clientY - rect.top;
		panX = mx - (mx - panX) * (newZoom / zoom);
		panY = my - (my - panY) * (newZoom / zoom);
		zoom = newZoom;
	}

	function onSvgMouseDown(e: MouseEvent) {
		if ((e.target as Element).closest('.node')) return; // 노드는 별도 처리
		isPanning = true;
		panStart = { x: e.clientX, y: e.clientY, px: panX, py: panY };
	}

	function onNodeMouseDown(e: MouseEvent, n: any) {
		e.stopPropagation();
		dragNode = n;
		dragMoved = false;
		// simulation 고정
		n.fx = n.x;
		n.fy = n.y;
	}

	function onWindowMouseMove(e: MouseEvent) {
		if (dragNode && container) {
			dragMoved = true;
			const rect = container.getBoundingClientRect();
			// 역변환: 화면 좌표 → simulation 좌표
			const mx = (e.clientX - rect.left - panX) / zoom;
			const my = (e.clientY - rect.top - panY) / zoom;
			dragNode.fx = mx;
			dragNode.fy = my;
			dragNode.x = mx;
			dragNode.y = my;
			simulation?.alpha(0.3).restart();
			// Svelte 반응
			simNodes = [...simNodes];
		} else if (isPanning) {
			panX = panStart.px + (e.clientX - panStart.x);
			panY = panStart.py + (e.clientY - panStart.y);
		}
	}

	function onWindowMouseUp() {
		if (dragNode && !dragMoved) {
			// 클릭으로 간주 · 고정 해제 + select
			dragNode.fx = null;
			dragNode.fy = null;
			onSelect?.(dragNode);
		} else if (dragNode) {
			// 드래그 완료 · 고정 해제 (force 다시 흘러가게 하려면 null, 고정하려면 유지)
			// 사용자가 배치한 위치 유지: fx/fy 그대로. 두 번 클릭하면 해제.
		}
		dragNode = null;
		isPanning = false;
	}

	function onNodeDoubleClick(n: any) {
		// 고정 해제 → force 재시작
		n.fx = null;
		n.fy = null;
		simulation?.alpha(0.3).restart();
	}

	function resetView() {
		zoom = 1;
		panX = 0;
		panY = 0;
		// 모든 고정 해제
		for (const n of simNodes) {
			n.fx = null;
			n.fy = null;
		}
		simulation?.alpha(0.5).restart();
	}

	function radius(nodeCount: number): number {
		return Math.max(18, Math.min(90, 9 + Math.sqrt(nodeCount) * 4.5));
	}

	// 산업별 표시용 (timelineYear 있으면 해당 연도, 없으면 현재 정적 값)
	function effectiveStats(ind: IndustryNode): { count: number; revOk: number } {
		if (timelineYear && industryTotalsByYear[timelineYear]) {
			const t = industryTotalsByYear[timelineYear][ind.id];
			if (t) {
				return {
					count: t.count ?? ind.nodeCount,
					revOk: t.totalRevenue ? t.totalRevenue / 1e8 : (ind.revenue || 0)
				};
			}
		}
		return { count: ind.nodeCount, revOk: ind.revenue || 0 };
	}

	function build() {
		if (!container) return;
		const rect = container.getBoundingClientRect();
		w = rect.width;
		h = rect.height;

		// 원형 배치 초기화 (nodeCount 큰 순으로 시계방향)
		const sorted = [...industries].sort((a, b) => b.nodeCount - a.nodeCount);
		const R = Math.min(w, h) * 0.33;
		simNodes = sorted.map((ind, i) => {
			const theta = (i / sorted.length) * Math.PI * 2 - Math.PI / 2;
			const { count, revOk } = effectiveStats(ind);
			// 반지름은 항상 회사 수 기준 (범례 "원 크기 = 소속 회사 수" 일관)
			const r = radius(count);
			return {
				...ind,
				effectiveCount: count,
				effectiveRevenue: revOk,
				r,
				x: w / 2 + R * Math.cos(theta),
				y: h / 2 + R * Math.sin(theta)
			};
		});

		const byId = new Map(simNodes.map((n: any) => [n.id, n]));
		simLinks = flows
			.filter((f) => byId.has(f.fromIndustry) && byId.has(f.toIndustry))
			.map((f) => ({
				source: f.fromIndustry,
				target: f.toIndustry,
				edgeCount: f.edgeCount,
				amount: f.amount
			}));

		// 허브 산업 식별 (연결 차수 상위 20%)
		const degree = new Map<string, number>();
		for (const l of simLinks) {
			degree.set(l.source, (degree.get(l.source) || 0) + 1);
			degree.set(l.target, (degree.get(l.target) || 0) + 1);
		}
		const degreeValues = [...degree.values()].sort((a, b) => b - a);
		const hubThreshold = degreeValues[Math.floor(degreeValues.length * 0.2)] || 0;
		for (const n of simNodes) {
			n.degree = degree.get(n.id) || 0;
			n.isHub = n.degree >= hubThreshold && n.degree > 0;
		}

		simulation?.stop();
		simulation = forceSimulation(simNodes)
			.force(
				'charge',
				forceManyBody<any>()
					.strength((d: any) => -d.r * 18)
					.distanceMax(600)
			)
			.force(
				'collide',
				forceCollide<any>()
					.radius((d: any) => d.r + 14)
					.strength(1.0)
					.iterations(4)
			)
			.force('center', forceCenter(w / 2, h / 2).strength(0.08))
			.force('x', forceX(w / 2).strength(0.06))
			.force('y', forceY(h / 2).strength(0.06))
			.force(
				'link',
				forceLink<any, any>(simLinks)
					.id((d: any) => d.id)
					.distance(200)
					.strength(0.05)
			)
			.alphaDecay(0.028)
			.on('tick', () => {
				// reassign to trigger reactivity
				simNodes = [...simNodes];
				simLinks = [...simLinks];
			});
	}

	let builtSignature = '';
	// $derived로 반응성 보장 · timelineYear 변경 시 자동 재계산
	let currentSignature = $derived.by(() => {
		const indIds = industries
			.map((i) => i.id)
			.sort()
			.join(',');
		const flowIds = flows
			.map((f) => `${f.fromIndustry}>${f.toIndustry}:${f.edgeCount}`)
			.sort()
			.join(',');
		return `${industries.length}|${indIds}|${flows.length}|${flowIds}|tl=${timelineYear}`;
	});

	onMount(() => {
		build();
		builtSignature = currentSignature;
		const ro = new ResizeObserver(() => {
			if (!container) return;
			const rect = container.getBoundingClientRect();
			// 크기만 바뀐 경우 포스 중심만 재설정 (시뮬레이션 재시작 안 함)
			if (Math.abs(rect.width - w) > 4 || Math.abs(rect.height - h) > 4) {
				w = rect.width;
				h = rect.height;
				simulation
					?.force('center', forceCenter(w / 2, h / 2).strength(0.08))
					.force('x', forceX(w / 2).strength(0.06))
					.force('y', forceY(h / 2).strength(0.06))
					.alpha(0.3)
					.restart();
			}
		});
		if (container) ro.observe(container);
		return () => {
			ro.disconnect();
			simulation?.stop();
		};
	});

	onDestroy(() => {
		simulation?.stop();
	});

	$effect(() => {
		// $derived.by인 currentSignature를 읽어 반응성 추적
		const sig = currentSignature;
		if (!container) return;
		if (sig !== builtSignature) {
			build();
			builtSignature = sig;
		}
	});

	// 색 동기화 · industries prop 의 color 만 바뀌면 위치/시뮬 유지하고 색만 갱신
	// (signature 가 안 바뀌어 build() 안 도는 케이스 · 예: colorMetric 변경)
	$effect(() => {
		const colorById = new Map<string, string>();
		for (const i of industries) colorById.set(i.id, i.color);
		let changed = false;
		for (const n of simNodes) {
			const c = colorById.get(n.id);
			if (c && n.color !== c) {
				n.color = c;
				changed = true;
			}
		}
		if (changed) simNodes = [...simNodes];
	});

	function formatRev(amountEok: number): string {
		// amount is in 억원
		if (amountEok >= 10000) return `${(amountEok / 10000).toFixed(1)}조`;
		return `${Math.round(amountEok).toLocaleString()}억`;
	}

	function edgeWidth(e: any): number {
		return Math.max(2.5, Math.min(10, 1.2 + Math.log2((e.edgeCount || 1) + 1) * 1.3));
	}

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
</script>

<svelte:window onmousemove={onWindowMouseMove} onmouseup={onWindowMouseUp} />

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
	bind:this={container}
	class="atlas-container"
	onwheel={onWheel}
	onmousedown={onSvgMouseDown}
	role="application"
	aria-label="산업 지도"
>
	<svg width={w} height={h} viewBox="0 0 {w} {h}">
		<g transform="translate({panX}, {panY}) scale({zoom})">
		<defs>
			<filter id="flow-glow" x="-50%" y="-50%" width="200%" height="200%">
				<feGaussianBlur stdDeviation="2" result="blur" />
				<feMerge>
					<feMergeNode in="blur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
			<filter id="hub-glow" x="-50%" y="-50%" width="200%" height="200%">
				<feGaussianBlur stdDeviation="4" result="blur" />
				<feMerge>
					<feMergeNode in="blur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
			<marker
				id="arrow"
				markerWidth="8"
				markerHeight="8"
				refX="6"
				refY="4"
				orient="auto"
				markerUnits="strokeWidth"
			>
				<path d="M0,0 L0,8 L8,4 z" fill="#fbbf24" />
			</marker>
		</defs>

		<!-- 엣지: supplier flow -->
		<g class="flows" filter="url(#flow-glow)">
			{#each simLinks as l, i (i)}
				{@const sx = l.source.x ?? 0}
				{@const sy = l.source.y ?? 0}
				{@const tx = l.target.x ?? 0}
				{@const ty = l.target.y ?? 0}
				{@const mx = (sx + tx) / 2}
				{@const my = (sy + ty) / 2 - Math.abs(tx - sx) * 0.18}
				<path
					d="M{sx},{sy} Q{mx},{my} {tx},{ty}"
					fill="none"
					stroke="#fbbf24"
					stroke-width={edgeWidth(l)}
					stroke-linecap="round"
					opacity={edgeConnected(l) ? (hovered ? 0.95 : 0.7) : 0.12}
					marker-end="url(#arrow)"
				/>
			{/each}
		</g>

		<!-- 노드 -->
		<g class="nodes">
			{#each simNodes as n (n.id)}
				{@const moverCount = moversByIndustry.get(n.id) || 0}
				<g
					class="node"
					class:dim={!isConnected(n.id)}
					class:fixed={n.fx != null}
					transform="translate({n.x ?? 0}, {n.y ?? 0})"
					onmouseenter={() => (hovered = n.id)}
					onmouseleave={() => (hovered = null)}
					onmousedown={(e: MouseEvent) => onNodeMouseDown(e, n)}
					ondblclick={() => onNodeDoubleClick(n)}
					role="button"
					tabindex="0"
					onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && onSelect?.(n)}
				>
					<!-- 허브 glow -->
					{#if n.isHub}
						<circle
							r={n.r + 4}
							fill="none"
							stroke={n.color}
							stroke-width="1.5"
							opacity="0.5"
							filter="url(#hub-glow)"
						/>
					{/if}
					<!-- 변화 감지 렌즈 · movers 있는 산업에 펄스 링 -->
					{#if moverCount > 0}
						<circle
							class="movers-pulse"
							r={n.r + 6}
							fill="none"
							stroke="#f87171"
							stroke-width="2"
							opacity="0.85"
						/>
					{/if}
					<!-- 외곽 링(hover 강조) -->
					{#if hovered === n.id}
						<circle r={n.r + 8} fill="none" stroke={n.color} stroke-width="2.5" opacity="0.9" />
					{/if}
					<circle
						r={n.r}
						fill={n.color}
						fill-opacity={hovered === n.id ? 0.95 : 0.85}
						stroke={n.isHub ? '#f8fafc' : n.color}
						stroke-width={n.isHub ? 2.5 : 1.5}
					/>
					<!-- 변화 감지 렌즈 · movers 카운트 배지 -->
					{#if moverCount > 0}
						<g class="mover-badge" transform="translate({n.r * 0.7}, {-n.r * 0.7})">
							<circle r="9" fill="#ef4444" stroke="#0f1219" stroke-width="1.5" />
							<text
								text-anchor="middle"
								dominant-baseline="central"
								y="0.5"
								font-size="10"
								font-weight="700"
								fill="#fff"
								style="pointer-events: none; user-select: none;"
							>
								{moverCount}
							</text>
						</g>
					{/if}
					<!-- 산업명 -->
					<text
						class="ind-label"
						text-anchor="middle"
						dominant-baseline="central"
						y={-4}
						font-size={Math.max(11, Math.min(16, n.r * 0.28))}
					>
						{n.name}
					</text>
					<!-- 회사 수 + 매출 -->
					<text
						class="ind-sub"
						text-anchor="middle"
						dominant-baseline="central"
						y={Math.max(11, Math.min(16, n.r * 0.28)) * 0.85 + 2}
						font-size={Math.max(9, Math.min(12, n.r * 0.2))}
					>
						{n.effectiveCount ?? n.nodeCount}사 · {formatRev(n.effectiveRevenue ?? n.revenue)}
					</text>
					<!-- metric 숫자 (colorMetric != industry 일 때) -->
					{#if colorMetric !== 'industry'}
						{@const ml = metricLabel(n)}
						{#if ml}
							<text
								class="ind-metric"
								text-anchor="middle"
								dominant-baseline="central"
								y={Math.max(11, Math.min(16, n.r * 0.28)) * 0.85 + 14}
								font-size="10"
							>
								{ml}
							</text>
						{/if}
					{/if}
				</g>
			{/each}
		</g>
		</g>
	</svg>

	<!-- 팬·줌 컨트롤 + 초기화 -->
	<div class="controls">
		<button class="ctl" onclick={resetView} title="화면 초기화 + 노드 고정 해제">
			{zoom.toFixed(1)}× ⟳
		</button>
	</div>

	<!-- 범례 -->
	<div class="legend">
		<div class="legend-item">
			<span class="legend-swatch flow"></span>
			<span>공급 플로우 · 굵기 = 거래 수</span>
		</div>
		<div class="legend-item">
			<span class="legend-swatch node"></span>
			<span>원 크기 = 소속 회사 수</span>
		</div>
		<div class="legend-note">산업 클릭 → 내부 드릴다운</div>
	</div>
</div>

<style>
	.atlas-container {
		position: relative;
		width: 100%;
		height: 100%;
		background: radial-gradient(
				ellipse at center,
				rgba(30, 41, 59, 0.3) 0%,
				transparent 70%
			),
			#050811;
		overflow: hidden;
		cursor: grab;
	}
	.atlas-container:active {
		cursor: grabbing;
	}
	.controls {
		position: absolute;
		top: 16px;
		right: 16px;
		display: flex;
		gap: 6px;
		z-index: 5;
	}
	.ctl {
		padding: 6px 10px;
		background: rgba(15, 18, 25, 0.85);
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #cbd5e1;
		font-size: 11px;
		font-family: monospace;
		cursor: pointer;
		backdrop-filter: blur(8px);
	}
	.ctl:hover {
		background: rgba(30, 36, 51, 0.95);
		border-color: #334155;
		color: #f1f5f9;
	}
	svg {
		display: block;
	}
	.node {
		cursor: grab;
		transition: opacity 0.2s;
	}
	.node circle {
		transition:
			r 400ms cubic-bezier(0.4, 0, 0.2, 1),
			fill 300ms ease,
			stroke 300ms ease,
			stroke-width 300ms ease,
			fill-opacity 200ms ease;
	}
	.flows path {
		transition:
			stroke-width 400ms cubic-bezier(0.4, 0, 0.2, 1),
			opacity 250ms ease;
	}
	.node.dim {
		opacity: 0.25;
	}
	.node:active {
		cursor: grabbing;
	}
	.node.fixed circle {
		stroke-dasharray: 4 2;
	}
	.node:hover circle {
		filter: brightness(1.15);
	}
	@keyframes movers-pulse {
		0%, 100% {
			opacity: 0.3;
			stroke-width: 1.5;
		}
		50% {
			opacity: 0.95;
			stroke-width: 3;
		}
	}
	.movers-pulse {
		animation: movers-pulse 1.6s ease-in-out infinite;
		pointer-events: none;
	}
	.mover-badge {
		pointer-events: none;
	}
	@media (prefers-reduced-motion: reduce) {
		.node,
		.node circle,
		.flows path {
			transition: none !important;
		}
		.movers-pulse {
			animation: none;
			opacity: 0.7;
		}
	}
	.ind-label {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 700;
		fill: #f8fafc;
		paint-order: stroke fill;
		stroke: rgba(5, 8, 17, 0.85);
		stroke-width: 3px;
		stroke-linejoin: round;
		letter-spacing: -0.02em;
		pointer-events: none;
		user-select: none;
	}
	.ind-metric {
		font-family: monospace;
		font-weight: 700;
		fill: #fbbf24;
		paint-order: stroke fill;
		stroke: rgba(5, 8, 17, 0.9);
		stroke-width: 2.5px;
		stroke-linejoin: round;
		pointer-events: none;
		user-select: none;
	}
	.ind-sub {
		font-family: 'Pretendard Variable', sans-serif;
		font-weight: 500;
		fill: rgba(248, 250, 252, 0.85);
		paint-order: stroke fill;
		stroke: rgba(5, 8, 17, 0.85);
		stroke-width: 2.5px;
		stroke-linejoin: round;
		pointer-events: none;
		user-select: none;
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
	.legend-swatch {
		display: inline-block;
		width: 18px;
		height: 4px;
		border-radius: 2px;
	}
	.legend-swatch.flow {
		background: var(--amber);
	}
	.legend-swatch.node {
		background: linear-gradient(to right, #0ea5e9, #f97316);
		height: 10px;
		border-radius: 50%;
		width: 10px;
	}
	.legend-note {
		margin-top: 4px;
		color: #64748b;
		font-size: 10px;
	}
</style>
