<script>
	import { renderMarkdown } from "$lib/markdown.js";

	let { block } = $props();

	let indent = $derived(block.depth * 16);
	let table = $derived(block.base);
	let isStructured = $derived(table && table.headers && table.rows);
	let cellDiffMap = $derived(() => {
		const map = new Map();
		if (block.cellDiffs) {
			for (const cd of block.cellDiffs) {
				map.set(`${cd.row}-${cd.col}`, cd);
			}
		}
		return map;
	});

	function isNumeric(val) {
		if (val == null || val === "") return false;
		return /^-?[\d,]+(\.\d+)?$/.test(String(val).replace(/[,\s]/g, ""));
	}
</script>

<div
	class="vw2-table vw2-status-{block.status || 'none'}"
	style="padding-left: {indent}px"
>
	{#if block.path}
		<div class="vw2-text-path">{block.path}</div>
	{/if}

	{#if isStructured}
		<div class="vw2-table-wrap">
			<div class="overflow-x-auto">
				<table class="vw2-styled-table">
					<thead>
						<tr>
							{#each table.headers as header, ci}
								<th class="{ci === 0 ? 'sticky left-0 z-[2] bg-dl-bg-card text-left' : 'text-right'}">{header}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each table.rows as row, ri}
							<tr class="{ri % 2 === 1 ? 'bg-white/[0.012]' : ''}">
								{#each row as cell, ci}
									{@const diff = cellDiffMap().get(`${ri}-${ci}`)}
									{@const num = ci > 0 && isNumeric(cell)}
									<td
										class="{ci === 0 ? 'sticky left-0 z-[1] bg-dl-bg-dark font-medium text-dl-text' : ''} {num ? 'text-right tabular-nums font-mono text-[11.5px]' : ''} {diff ? 'vw2-cell-changed' : ''}"
										title={diff ? `${diff.from} → ${diff.to}` : null}
									>{cell}</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{:else if table?.raw}
		<div class="vw2-table-raw">
			{@html renderMarkdown(table.raw)}
		</div>
	{:else if typeof block.base === "string"}
		<div class="vw2-table-raw">
			{@html renderMarkdown(block.base)}
		</div>
	{/if}
</div>
