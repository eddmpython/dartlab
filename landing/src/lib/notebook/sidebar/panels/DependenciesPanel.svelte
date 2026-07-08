<script lang="ts">
	import { RefreshCw } from 'lucide-svelte';
	import { notebook } from '../../stores/notebookStore';
	import { analyzeCell, buildGraph } from '../../engine/dataflow';

	interface DepNode {
		cellId: string;
		index: number;
		label: string;
		defines: string[];
		uses: string[];
	}

	let nodes = $state<DepNode[]>([]);
	let edges = $state<{ from: number; to: number; variable: string }[]>([]);

	function refresh() {
		const cells = $notebook.cells;
		const codeCells = cells
			.map((c, i) => ({ cell: c, index: i }))
			.filter((x) => x.cell.type === 'code');

		const graph = buildGraph(cells.map((c) => ({ id: c.id, type: c.type, content: c.content })));

		nodes = codeCells.map((x) => {
			const analysis = graph.analyses.get(x.cell.id);
			const code = x.cell.content || '';
			const firstLine = code.split('\n')[0]?.trim() || '';
			const label = firstLine.length > 30 ? firstLine.slice(0, 27) + '...' : firstLine || '(empty)';

			return {
				cellId: x.cell.id,
				index: x.index,
				label,
				defines: analysis ? [...analysis.defines] : [],
				uses: analysis ? [...analysis.uses] : [],
			};
		});

		const newEdges: { from: number; to: number; variable: string }[] = [];
		for (let i = 0; i < nodes.length; i++) {
			const childSet = graph.children.get(nodes[i].cellId);
			if (!childSet) continue;
			for (const childId of childSet) {
				const j = nodes.findIndex((n) => n.cellId === childId);
				if (j < 0) continue;
				const childAnalysis = graph.analyses.get(childId);
				const parentAnalysis = graph.analyses.get(nodes[i].cellId);
				if (!childAnalysis || !parentAnalysis) continue;
				for (const varName of childAnalysis.uses) {
					if (parentAnalysis.defines.has(varName)) {
						newEdges.push({ from: i, to: j, variable: varName });
					}
				}
			}
		}
		edges = newEdges;
	}

	$effect(() => {
		$notebook.cells;
		refresh();
	});
</script>

<div class="deps-panel">
	<div class="panel-actions">
		<button class="refresh-btn" onclick={refresh} aria-label="Refresh">
			<RefreshCw size={13} />
		</button>
	</div>

	{#if nodes.length === 0}
		<div class="dep-empty">No code cells</div>
	{:else}
		<div class="dep-graph">
			{#each nodes as node, i}
				<div class="dep-node">
					<div class="node-header">
						<span class="node-index">In [{node.index + 1}]</span>
						<span class="node-label">{node.label}</span>
					</div>

					{#if node.defines.length > 0}
						<div class="node-vars">
							<span class="var-label">defines</span>
							<div class="var-tags">
								{#each node.defines as d}
									<span class="var-tag define">{d}</span>
								{/each}
							</div>
						</div>
					{/if}

					{#if node.uses.length > 0}
						{@const externalUses = node.uses.filter((u) => nodes.some((n) => n !== node && n.defines.includes(u)))}
						{#if externalUses.length > 0}
							<div class="node-vars">
								<span class="var-label">uses</span>
								<div class="var-tags">
									{#each externalUses as u}
										<span class="var-tag use">{u}</span>
									{/each}
								</div>
							</div>
						{/if}
					{/if}
				</div>

				{#each edges.filter((e) => e.from === i) as edge}
					<div class="dep-edge">
						<span class="edge-line">&#8627;</span>
						<span class="edge-var">{edge.variable}</span>
						<span class="edge-arrow">&#8594;</span>
						<span class="edge-target">In [{nodes[edge.to].index + 1}]</span>
					</div>
				{/each}
			{/each}
		</div>
	{/if}
</div>

<style>
	.deps-panel {
		padding: 0 8px;
	}

	.panel-actions {
		display: flex;
		justify-content: flex-end;
		padding: 4px 0 8px;
	}

	.refresh-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 26px;
		height: 26px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.refresh-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.dep-empty {
		padding: 16px 4px;
		text-align: center;
		color: var(--nb-text-muted);
		font-size: 12px;
	}

	.dep-graph {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.dep-node {
		padding: 6px 8px;
		border-radius: 6px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
	}

	.node-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 4px;
	}

	.node-index {
		font-size: 10px;
		font-weight: 700;
		color: var(--nb-pink);
		font-family: var(--dl-font-mono);
		white-space: nowrap;
	}

	.node-label {
		font-size: 11px;
		color: var(--nb-text-muted);
		font-family: var(--dl-font-mono);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.node-vars {
		display: flex;
		align-items: flex-start;
		gap: 6px;
		margin-top: 3px;
	}

	.var-label {
		font-size: 9px;
		color: var(--nb-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding-top: 2px;
		white-space: nowrap;
	}

	.var-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 3px;
	}

	.var-tag {
		font-size: 10px;
		font-family: var(--dl-font-mono);
		padding: 1px 5px;
		border-radius: 3px;
	}

	.var-tag.define {
		background: var(--nb-pink-subtle);
		color: var(--nb-pink);
	}

	.var-tag.use {
		background: rgba(59, 130, 246, 0.1);
		color: #60a5fa;
	}

	.dep-edge {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 12px;
		font-size: 10px;
		color: var(--nb-text-muted);
	}

	.edge-line {
		color: var(--nb-border);
	}

	.edge-var {
		font-family: var(--dl-font-mono);
		color: var(--nb-text-secondary);
	}

	.edge-arrow {
		color: var(--nb-border);
	}

	.edge-target {
		font-family: var(--dl-font-mono);
		color: var(--nb-pink);
		font-weight: 600;
	}
</style>
