<script>
	import { ChevronRight, ChevronDown } from "lucide-svelte";

	let { block, collapsed = false, onToggle = null } = $props();

	const levelSizes = { 1: "text-[20px]", 2: "text-[18px]", 3: "text-[16px]", 4: "text-[14px]" };
	let fontSize = $derived(levelSizes[block.level] || "text-[14px]");
	let indent = $derived(block.depth * 16);
</script>

<div
	class="vw2-heading vw2-status-{block.status || 'none'}"
	style="padding-left: {indent}px"
>
	<button class="vw2-heading-toggle" onclick={onToggle}>
		{#if collapsed}
			<ChevronRight size={14} class="opacity-40" />
		{:else}
			<ChevronDown size={14} class="opacity-40" />
		{/if}
	</button>
	<span class="vw2-heading-text {fontSize} font-semibold">{block.base || block.compare || ""}</span>
</div>
