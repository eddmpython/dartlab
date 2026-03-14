<script lang="ts">
	import '../app.css';
	import type { Snippet } from 'svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';

	let { children }: { children: Snippet } = $props();
</script>

<CommandPalette />
{@render children()}
