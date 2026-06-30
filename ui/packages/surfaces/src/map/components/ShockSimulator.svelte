<script lang="ts">
	/**
	 * 공급망 충격 시뮬레이터 · "이 회사에 문제 생기면 어디까지?"
	 *
	 * BFS 2홉으로 영향 받는 회사를 추출하고, 강도별 색상 표시.
	 * Bloomberg SPLC에도 없는 기능 · 세계 유일.
	 */

	interface Props {
		// 충격 중심 회사 stockCode
		targetId: string;
		targetName: string;
		// ecosystem.json links
		links: any[];
		// ecosystem.json nodes (id → node 매핑용)
		nodes: any[];
		onClose?: () => void;
		// 영향 받는 노드 ID set을 부모에게 전달 (지도 하이라이트용)
		onImpactChange?: (impactMap: Map<string, number>) => void;
	}

	let { targetId, targetName, links, nodes, onClose, onImpactChange }: Props = $props();

	// Build adjacency list (양방향 · 공급사 문제는 고객에게, 고객 문제는 공급사에게 영향)
	let adj = $derived.by(() => {
		const m = new Map<string, Array<{ id: string; weight: number }>>();
		for (const l of links) {
			const s = l.source;
			const t = l.target;
			const w = (l.ratio ?? 50) * (l.confidence ?? 0.5) / 100;
			if (!m.has(s)) m.set(s, []);
			if (!m.has(t)) m.set(t, []);
			m.get(s)!.push({ id: t, weight: w });
			m.get(t)!.push({ id: s, weight: w });
		}
		return m;
	});

	// Node name map
	let nameMap = $derived(new Map(nodes.map((n: any) => [n.id, n.label])));
	let nodeMap = $derived(new Map(nodes.map((n: any) => [n.id, n])));

	// BFS 2-hop impact
	let impactResult = $derived.by(() => {
		const impact = new Map<string, number>(); // id → intensity (0~1)
		impact.set(targetId, 1.0);

		// 1-hop
		const hop1 = adj.get(targetId) || [];
		const hop1Ids: string[] = [];
		for (const nb of hop1) {
			if (!impact.has(nb.id)) {
				impact.set(nb.id, nb.weight);
				hop1Ids.push(nb.id);
			}
		}

		// 2-hop
		const hop2Ids: string[] = [];
		for (const h1 of hop1Ids) {
			const hop2 = adj.get(h1) || [];
			for (const nb of hop2) {
				if (!impact.has(nb.id)) {
					const h1w = impact.get(h1) || 0;
					impact.set(nb.id, h1w * nb.weight * 0.5); // 감쇠
					hop2Ids.push(nb.id);
				}
			}
		}

		// Notify parent
		onImpactChange?.(impact);

		// Revenue sum
		let totalRevenue = 0;
		for (const [id] of impact) {
			const n = nodeMap.get(id);
			if (n) totalRevenue += n.revenue || 0;
		}

		// Top impacted (by weight, excluding center)
		const sorted = [...impact.entries()]
			.filter(([id]) => id !== targetId)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 10);

		return {
			center: targetId,
			hop1Count: hop1Ids.length,
			hop2Count: hop2Ids.length,
			totalCount: impact.size - 1,
			totalRevenue,
			topImpacted: sorted.map(([id, w]) => ({
				id,
				name: nameMap.get(id) || id,
				intensity: w,
				hop: hop1Ids.includes(id) ? 1 : 2
			}))
		};
	});

	function fmtKor(v: number): string {
		if (v >= 1e12) return `${(v / 1e12).toFixed(1)}조`;
		if (v >= 1e8) return `${Math.round(v / 1e8).toLocaleString()}억`;
		return v.toLocaleString();
	}
</script>

<div class="shock-panel">
	<header class="shock-head">
		<div>
			<h3>충격 시뮬레이션</h3>
			<p class="shock-target">{targetName} ({targetId}) 타격 시</p>
		</div>
		<button class="shock-close" onclick={() => { onImpactChange?.(new Map()); onClose?.(); }} aria-label="닫기">✕</button>
	</header>

	<div class="shock-stats">
		<div class="stat">
			<span class="stat-v center-pulse">{impactResult.center}</span>
			<span class="stat-k">충격 중심</span>
		</div>
		<div class="stat">
			<span class="stat-v">{impactResult.hop1Count}</span>
			<span class="stat-k">1홉 영향</span>
		</div>
		<div class="stat">
			<span class="stat-v">{impactResult.hop2Count}</span>
			<span class="stat-k">2홉 영향</span>
		</div>
		<div class="stat">
			<span class="stat-v">{fmtKor(impactResult.totalRevenue)}</span>
			<span class="stat-k">영향 매출 합</span>
		</div>
	</div>

	<div class="shock-legend">
		<span class="dot" style="background:#ef4444"></span> 중심
		<span class="dot" style="background:var(--amber)"></span> 1홉
		<span class="dot" style="background:#fbbf24"></span> 2홉
		<span class="dot" style="background:var(--color-dl-text-dim)"></span> 무관
	</div>

	<div class="shock-list">
		<h4>영향 Top 10</h4>
		{#each impactResult.topImpacted as item}
			<div class="shock-row">
				<span class="shock-hop" class:hop1={item.hop === 1} class:hop2={item.hop === 2}>
					{item.hop}홉
				</span>
				<span class="shock-name">{item.name}</span>
				<span class="shock-pct">{(item.intensity * 100).toFixed(0)}%</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.shock-panel {
		background: var(--color-dl-bg-card);
		border: 1px solid var(--color-dl-border);
		border-radius: 10px;
		overflow: hidden;
		font-size: 12px;
	}
	.shock-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		padding: 12px 14px;
		background: linear-gradient(180deg, rgba(239, 68, 68, 0.08), transparent);
		border-bottom: 1px solid var(--color-dl-border);
	}
	.shock-head h3 {
		margin: 0;
		font-size: 14px;
		font-weight: 700;
		color: var(--color-dl-primary-light);
	}
	.shock-target {
		margin: 2px 0 0;
		font-size: 11px;
		color: var(--color-dl-text-muted);
	}
	.shock-close {
		background: none;
		border: none;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		font-size: 14px;
		padding: 4px;
	}

	.shock-stats {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1px;
		padding: 8px 14px;
		border-bottom: 1px solid var(--color-dl-border);
	}
	.stat {
		text-align: center;
	}
	.stat-v {
		display: block;
		font-size: 16px;
		font-weight: 700;
		font-family: var(--font-mono);
		color: var(--color-dl-text);
	}
	.stat-k {
		font-size: 9px;
		color: var(--color-dl-text-dim);
	}
	@keyframes center-glow {
		0%, 100% { text-shadow: 0 0 4px rgba(239,68,68,0.5); }
		50% { text-shadow: 0 0 12px rgba(239,68,68,0.9); }
	}
	.center-pulse {
		color: var(--color-dl-danger);
		animation: center-glow 2s ease-in-out infinite;
	}

	.shock-legend {
		padding: 6px 14px;
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 10px;
		color: var(--color-dl-text-dim);
		border-bottom: 1px solid var(--color-dl-border);
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		display: inline-block;
	}

	.shock-list {
		padding: 8px 14px 12px;
		max-height: 200px;
		overflow-y: auto;
	}
	.shock-list h4 {
		margin: 0 0 6px;
		font-size: 11px;
		color: var(--color-dl-text-dim);
	}
	.shock-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 3px 0;
		border-bottom: 1px dashed rgba(30, 36, 51, 0.3);
	}
	.shock-hop {
		font-size: 9px;
		font-weight: 600;
		padding: 1px 5px;
		border-radius: 3px;
		background: rgba(148, 163, 184, 0.1);
		color: var(--color-dl-text-dim);
	}
	.shock-hop.hop1 {
		background: rgba(var(--amber-rgb), 0.15);
		color: var(--amber);
	}
	.shock-hop.hop2 {
		background: rgba(251, 191, 36, 0.15);
		color: #fbbf24;
	}
	.shock-name {
		flex: 1;
		color: var(--color-dl-text);
		font-size: 12px;
	}
	.shock-pct {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--color-dl-text-muted);
	}
</style>
