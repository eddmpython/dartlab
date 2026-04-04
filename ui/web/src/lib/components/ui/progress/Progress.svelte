<script>
	import { cn } from "$lib/utils.js";

	let { value = 0, max = 100, variant = "default", size = "default", indeterminate = false, class: className } = $props();

	const pct = $derived(Math.min(100, Math.max(0, (value / max) * 100)));

	const variants = {
		default: "bg-dl-primary",
		accent: "bg-dl-accent",
		success: "bg-dl-success",
	};

	const sizes = {
		sm: "h-1",
		default: "h-2",
		lg: "h-3",
	};
</script>

<div
	role="progressbar"
	aria-valuenow={indeterminate ? undefined : value}
	aria-valuemin={0}
	aria-valuemax={max}
	class={cn(
		"w-full overflow-hidden rounded-full bg-dl-bg-card-hover",
		sizes[size], className
	)}
>
	{#if indeterminate}
		<div class={cn(
			"h-full w-1/3 rounded-full animate-[progress-slide_1.5s_ease-in-out_infinite]",
			variants[variant]
		)}></div>
	{:else}
		<div
			class={cn(
				"h-full rounded-full transition-all duration-300 ease-out",
				variants[variant]
			)}
			style="width: {pct}%"
		></div>
	{/if}
</div>

<style>
	@keyframes progress-slide {
		0% { transform: translateX(-100%); }
		50% { transform: translateX(200%); }
		100% { transform: translateX(-100%); }
	}
</style>
