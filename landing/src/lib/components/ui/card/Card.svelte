<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		hover?: boolean;
		children: Snippet;
	}

	let { class: className, hover = true, children }: Props = $props();
</script>

<div class={cn(
	'rounded-lg bg-dl-bg-card border border-dl-border p-6 transition-colors duration-200',
	hover && 'hover:border-dl-primary/30',
	className
)}>
	{@render children()}
</div>
