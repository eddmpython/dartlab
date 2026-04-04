<script>
	let { block } = $props();

	let indent = $derived(block.depth * 16);
</script>

<div
	class="vw2-text vw2-status-{block.status || 'none'}"
	style="padding-left: {indent}px"
>
	{#if block.path}
		<div class="vw2-text-path">{block.path}</div>
	{/if}

	{#if block.status === "modified" && block.diff?.length > 0}
		<div class="vw2-text-body vw2-diff-inline">
			{#each block.diff as op}
				{#if op.type === "equal"}
					<span>{op.text}</span>
				{:else if op.type === "insert"}
					<span class="vw2-diff-ins">{op.text}</span>
				{:else if op.type === "delete"}
					<span class="vw2-diff-del">{op.text}</span>
				{/if}
			{/each}
		</div>
	{:else if block.status === "removed"}
		<div class="vw2-text-body vw2-text-removed">{block.compare || ""}</div>
	{:else}
		<div class="vw2-text-body">{block.base || ""}</div>
	{/if}
</div>
