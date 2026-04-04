<script>
	import { cn } from "$lib/utils.js";

	let { class: className, hover = false, children } = $props();
</script>

<div class={cn(
	"rounded-xl bg-dl-bg-card border border-dl-border p-5 transition-all duration-200",
	hover && "hover:border-dl-primary/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-dl-primary/5",
	className
)}>
	{@render children()}
</div>
