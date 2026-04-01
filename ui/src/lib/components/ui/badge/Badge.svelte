<script>
	import { cn } from "$lib/utils.js";

	let { variant = "default", class: className, children } = $props();

	const variants = {
		default: "bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",
		accent: "bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",
		success: "bg-dl-success/10 text-dl-success border-dl-success/20",
		muted: "bg-dl-bg-card-hover text-dl-text-muted border-dl-border",
		dim: "bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50",
	};
</script>

<span class={cn(
	"inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",
	variants[variant], className
)}>
	{@render children()}
</span>
