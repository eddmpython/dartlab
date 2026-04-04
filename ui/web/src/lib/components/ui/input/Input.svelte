<script>
	import { cn } from "$lib/utils.js";

	let { type = "text", variant = "default", size = "default", class: className, ...restProps } = $props();

	const variants = {
		default: "bg-dl-bg-card border-dl-border text-dl-text placeholder:text-dl-text-dim focus:border-dl-primary/50 focus:ring-2 focus:ring-dl-ring",
		ghost: "bg-transparent border-transparent text-dl-text placeholder:text-dl-text-dim focus:bg-dl-bg-card focus:border-dl-border",
	};

	const sizes = {
		default: "h-9 px-3 py-2 text-sm",
		sm: "h-8 px-2.5 py-1.5 text-xs",
		lg: "h-11 px-4 py-3 text-base",
	};
</script>

<input
	{type}
	class={cn(
		"w-full rounded-lg border outline-none transition-all duration-[var(--motion-fast)]",
		"disabled:cursor-not-allowed disabled:opacity-50",
		"file:border-0 file:bg-transparent file:text-sm file:font-medium",
		variants[variant], sizes[size], className
	)}
	{...restProps}
/>
