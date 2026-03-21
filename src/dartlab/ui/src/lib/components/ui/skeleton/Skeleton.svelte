<script>
	import { cn } from "$lib/utils.js";

	let { class: className } = $props();
</script>

<div
	class={cn(
		"animate-pulse rounded-lg bg-dl-bg-card-hover",
		className
	)}
	aria-hidden="true"
></div>
