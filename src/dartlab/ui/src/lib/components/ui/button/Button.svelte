<script>
	import { cn } from "$lib/utils.js";

	let { variant = "default", size = "default", class: className, children, ...restProps } = $props();

	const variants = {
		default: "bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",
		secondary: "bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",
		ghost: "text-dl-text-muted hover:text-dl-text hover:bg-white/5",
		outline: "border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50",
	};

	const sizes = {
		default: "px-5 py-2 text-sm",
		sm: "px-3 py-1.5 text-xs",
		lg: "px-7 py-3 text-base",
		icon: "w-9 h-9",
	};
</script>

{#if restProps.href}
	<a
		class={cn(
			"inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline active:scale-95",
			variants[variant], sizes[size], className
		)}
		{...restProps}
	>
		{@render children()}
	</a>
{:else}
	<button
		class={cn(
			"inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer active:scale-95",
			variants[variant], sizes[size], className
		)}
		{...restProps}
	>
		{@render children()}
	</button>
{/if}
