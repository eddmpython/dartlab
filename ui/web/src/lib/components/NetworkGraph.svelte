<!--
	NetworkGraph — Ego network force-directed graph.
	d3-force for layout, Svelte for rendering (no direct DOM manipulation).
	Dark theme, dl-* CSS classes.
-->
<script>
	import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from "d3-force";
	import { ChevronDown, ChevronUp, Loader2, AlertTriangle, Users } from "lucide-svelte";

	let {
		data = null,       // ego network API response
		loading = false,
		centerCode = '',
		onNavigate = null, // (stockCode) => void
	} = $props();

	let expanded = $state(false);
	let svgEl = $state(null);
	let width = $state(640);
	let height = $state(400);
	let tooltip = $state({ show: false, x: 0, y: 0, text: "" });

	// Simulation state — Svelte-managed arrays for reactive rendering
	let simNodes = $state([]);
	let simEdges = $state([]);
	let simRef = null;

	// Group → color mapping
	const GROUP_COLORS = [
		"#60a5fa", "#f59e0b", "#10b981", "#f472b6", "#a78bfa",
		"#14b8a6", "#fb923c", "#e879f9", "#38bdf8", "#fbbf24",
		"#4ade80", "#f87171", "#818cf8", "#2dd4bf", "#fb7185",
	];
	let groupColorMap = $derived.by(() => {
		if (!data?.nodes) return {};
		const groups = [...new Set(data.nodes.map(n => n.group).filter(Boolean))];
		const map = {};
		groups.forEach((g, i) => { map[g] = GROUP_COLORS[i % GROUP_COLORS.length]; });
		return map;
	});

	function nodeColor(node) {
		if (node.id === centerCode) return "#818cf8";
		if (node.type === "person") return "#94a3b8";
		return groupColorMap[node.group] || "#475569";
	}

	function nodeRadius(node) {
		if (node.id === centerCode) return 18;
		if (node.type === "person") return 7;
		return Math.max(6, Math.min(14, 6 + (node.degree || 0) * 0.8));
	}

	function edgeStroke(edge) {
		if (edge.type === "investment") return "#60a5fa40";
		if (edge.type === "shareholder") return "#f59e0b30";
		return "#94a3b830";
	}

	function edgeDash(edge) {
		if (edge.type === "person_shareholder") return "3,3";
		if (edge.type === "shareholder") return "5,3";
		return "none";
	}

	function truncLabel(label, max = 6) {
		if (!label) return "";
		return label.length > max ? label.slice(0, max) + "…" : label;
	}

	// Resize observer
	$effect(() => {
		if (!svgEl) return;
		const ro = new ResizeObserver(entries => {
			for (const entry of entries) {
				width = entry.contentRect.width || 640;
			}
		});
		ro.observe(svgEl.parentElement);
		return () => ro.disconnect();
	});

	// Build & run simulation when data changes
	$effect(() => {
		if (!data?.nodes?.length || !expanded) {
			if (simRef) { simRef.stop(); simRef = null; }
			simNodes = [];
			simEdges = [];
			return;
		}

		const nodes = data.nodes.map(n => ({
			...n,
			x: n.id === centerCode ? width / 2 : undefined,
			y: n.id === centerCode ? height / 2 : undefined,
			fx: n.id === centerCode ? width / 2 : undefined,
			fy: n.id === centerCode ? height / 2 : undefined,
		}));
		const nodeMap = new Map(nodes.map(n => [n.id, n]));
		const edges = data.edges
			.filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
			.map(e => ({ ...e, source: e.source, target: e.target }));

		if (simRef) simRef.stop();

		const sim = forceSimulation(nodes)
			.force("link", forceLink(edges).id(d => d.id).distance(80).strength(0.4))
			.force("charge", forceManyBody().strength(-200))
			.force("center", forceCenter(width / 2, height / 2))
			.force("collide", forceCollide().radius(d => nodeRadius(d) + 4))
			.alphaDecay(0.03);

		sim.on("tick", () => {
			// Clamp to bounds
			for (const n of nodes) {
				const r = nodeRadius(n);
				n.x = Math.max(r, Math.min(width - r, n.x));
				n.y = Math.max(r, Math.min(height - r, n.y));
			}
			simNodes = [...nodes];
			simEdges = [...edges];
		});

		simRef = sim;
		return () => { sim.stop(); };
	});

	function showTooltip(e, node) {
		const rect = svgEl.getBoundingClientRect();
		const lines = [node.label];
		if (node.group) lines.push(`그룹: ${node.group}`);
		if (node.industry) lines.push(node.industry);
		if (node.type === "company") lines.push(`연결: ${node.degree || 0}개`);
		tooltip = { show: true, x: e.clientX - rect.left, y: e.clientY - rect.top - 10, text: lines.join("\n") };
	}

	function showEdgeTooltip(e, edge) {
		const rect = svgEl.getBoundingClientRect();
		const lines = [];
		const sLabel = typeof edge.source === "object" ? edge.source.label : edge.source;
		const tLabel = typeof edge.target === "object" ? edge.target.label : edge.target;
		lines.push(`${sLabel} → ${tLabel}`);
		if (edge.type === "investment") lines.push(`출자 (${edge.purpose || ""})`);
		else if (edge.type === "shareholder") lines.push("지분 보유");
		else lines.push("인물 지분");
		if (edge.ownershipPct != null) lines.push(`지분율: ${edge.ownershipPct.toFixed(1)}%`);
		tooltip = { show: true, x: e.clientX - rect.left, y: e.clientY - rect.top - 10, text: lines.join("\n") };
	}

	function hideTooltip() { tooltip = { show: false, x: 0, y: 0, text: "" }; }

	function handleNodeClick(node) {
		if (node.type === "company" && node.id !== centerCode && onNavigate) {
			onNavigate(node.id);
		}
	}

	// Summary stats
	let groupName = $derived(data?.nodes?.find(n => n.id === centerCode)?.group || "");
	let companyCount = $derived((data?.nodes || []).filter(n => n.type === "company").length);
	let personCount = $derived((data?.nodes || []).filter(n => n.type === "person").length);
	let edgeCount = $derived((data?.edges || []).length);
	let hasCycles = $derived((data?.meta?.cycleCount || 0) > 0);
</script>

{#if loading}
	<!-- Silent loading -->
{:else if data?.available !== false && data?.nodes?.length > 0}
	<div class="space-y-2">
		<!-- Header (collapsible) -->
		<button
			class="flex items-center gap-2 w-full px-1 py-1 text-left rounded-md hover:bg-white/3 transition-colors"
			onclick={() => { expanded = !expanded; }}
		>
			<Users size={13} class="text-dl-text-dim/60" />
			<span class="text-[11px] font-semibold text-dl-text-dim uppercase tracking-wider flex-1">관계 네트워크</span>
			{#if groupName}
				<span class="px-1.5 py-0.5 rounded text-[9px] font-medium border border-dl-border/20 text-dl-text-dim bg-dl-surface-card">
					{groupName}
				</span>
			{/if}
			<span class="text-[10px] text-dl-text-dim/50">{companyCount}사{#if personCount > 0} · {personCount}인{/if} · {edgeCount}연결</span>
			{#if expanded}
				<ChevronUp size={12} class="text-dl-text-dim/40" />
			{:else}
				<ChevronDown size={12} class="text-dl-text-dim/40" />
			{/if}
		</button>

		{#if expanded}
			<!-- Legend -->
			<div class="flex flex-wrap gap-3 px-1 text-[9px] text-dl-text-dim/60">
				<span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-blue-400/40 inline-block"></span>출자</span>
				<span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-amber-400/30 inline-block" style="border-bottom: 1px dashed"></span>지분</span>
				<span class="flex items-center gap-1"><span class="w-2 h-0.5 bg-slate-400/30 inline-block" style="border-bottom: 1px dotted"></span>인물</span>
				{#if hasCycles}
					<span class="flex items-center gap-1 text-amber-400/70"><AlertTriangle size={9} />순환출자 감지</span>
				{/if}
			</div>

			<!-- SVG Graph -->
			<div class="relative rounded-lg border border-dl-border/15 bg-dl-bg-darker/50 overflow-hidden" style="height: {height}px;">
				<svg bind:this={svgEl} class="w-full h-full" viewBox="0 0 {width} {height}">
					<!-- Arrow marker -->
					<defs>
						<marker id="arrow-inv" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse">
							<path d="M0,0 L10,3 L0,6" fill="#60a5fa40" />
						</marker>
						<marker id="arrow-sh" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="5" orient="auto-start-reverse">
							<path d="M0,0 L10,3 L0,6" fill="#f59e0b30" />
						</marker>
					</defs>

					<!-- Edges -->
					{#each simEdges as edge}
						{@const sx = typeof edge.source === "object" ? edge.source.x : 0}
						{@const sy = typeof edge.source === "object" ? edge.source.y : 0}
						{@const tx = typeof edge.target === "object" ? edge.target.x : 0}
						{@const ty = typeof edge.target === "object" ? edge.target.y : 0}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<line
							x1={sx} y1={sy} x2={tx} y2={ty}
							stroke={edgeStroke(edge)}
							stroke-width={edge.ownershipPct > 20 ? 2 : 1}
							stroke-dasharray={edgeDash(edge)}
							marker-end={edge.type === "investment" ? "url(#arrow-inv)" : edge.type === "shareholder" ? "url(#arrow-sh)" : ""}
							class="cursor-pointer hover:stroke-[#fff3]"
							onmouseenter={(e) => showEdgeTooltip(e, edge)}
							onmouseleave={hideTooltip}
						/>
					{/each}

					<!-- Nodes -->
					{#each simNodes as node}
						{@const r = nodeRadius(node)}
						{@const color = nodeColor(node)}
						{@const isCenter = node.id === centerCode}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<g
							class="cursor-pointer"
							transform="translate({node.x},{node.y})"
							onmouseenter={(e) => showTooltip(e, node)}
							onmouseleave={hideTooltip}
							onclick={() => handleNodeClick(node)}
						>
							{#if isCenter}
								<circle r={r + 3} fill="none" stroke="#818cf860" stroke-width="2" />
							{/if}
							<circle
								{r}
								fill={color}
								stroke={isCenter ? "#c4b5fd" : "#ffffff10"}
								stroke-width={isCenter ? 2 : 0.5}
								opacity={node.type === "person" ? 0.7 : 0.85}
							/>
							{#if r >= 8}
								<text
									y={r + 12}
									text-anchor="middle"
									class="fill-dl-text-dim/50 text-[8px] pointer-events-none select-none"
								>{truncLabel(node.label)}</text>
							{/if}
						</g>
					{/each}
				</svg>

				<!-- Tooltip -->
				{#if tooltip.show}
					<div
						class="absolute z-10 px-2 py-1 rounded-md bg-dl-bg-card/95 border border-dl-border/30 text-[10px] text-dl-text-muted whitespace-pre-line pointer-events-none shadow-lg"
						style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translate(-50%, -100%)"
					>{tooltip.text}</div>
				{/if}
			</div>
		{/if}
	</div>
{/if}
