<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		children: Snippet;
	}

	let { title, children }: Props = $props();
</script>

<div class="max-w-2xl mx-auto rounded-lg overflow-hidden bg-dl-bg-card border border-dl-border shadow-lg shadow-black/20 text-left">
	<div class="flex items-center gap-1.5 px-4 py-3 bg-white/[0.03] border-b border-dl-border">
		<span class="w-2.5 h-2.5 rounded-full bg-red-500"></span>
		<span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
		<span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
		<span class="ml-2 text-xs text-dl-text-dim">{title}</span>
	</div>
	<div class="p-5 font-mono text-sm leading-7 text-slate-200">
		{@render children()}
	</div>
</div>
