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
	'rounded-xl bg-dl-bg-card border border-dl-border p-6 transition-all duration-300',
	hover && 'hover:border-dl-primary/50 hover:-translate-y-1 hover:shadow-lg hover:shadow-dl-primary/5',
	className
)}>
	{@render children()}
</div>
