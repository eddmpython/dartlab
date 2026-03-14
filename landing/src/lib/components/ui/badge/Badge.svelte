<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';

	type Variant = 'default' | 'accent' | 'success' | 'warning';

	interface Props {
		variant?: Variant;
		class?: string;
		children: Snippet;
	}

	let { variant = 'default', class: className, children }: Props = $props();

	const variants: Record<Variant, string> = {
		default: 'bg-dl-primary/10 text-dl-primary-light border-dl-primary/20',
		accent: 'bg-dl-accent/10 text-dl-accent-light border-dl-accent/20',
		success: 'bg-dl-success/10 text-dl-success border-dl-success/20',
		warning: 'bg-dl-warning/10 text-dl-warning border-dl-warning/20'
	};
</script>

<span class={cn(
	'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium border',
	variants[variant],
	className
)}>
	{@render children()}
</span>
