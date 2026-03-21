<script>
	import { cn } from "$lib/utils.js";

	let { orientation = "horizontal", class: className } = $props();
</script>

<div
	role="separator"
	aria-orientation={orientation}
	class={cn(
		"shrink-0 bg-dl-border",
		orientation === "horizontal" ? "h-px w-full" : "h-full w-px",
		className
	)}
></div>
