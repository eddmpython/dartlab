<script lang="ts">
	import { Search, Loader2 } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { getDocstring, engineStatus } from '../../stores/executionStore';
	import type { DocResult } from '../../engine/executionEngine';

	let query = $state('');
	let loading = $state(false);
	let result = $state<DocResult | null>(null);
	let searched = $state(false);
	let engineReady = $state(false);

	onMount(() => {
		const unsub = engineStatus.subscribe((s) => {
			engineReady = s === 'ready';
		});
		return unsub;
	});

	async function handleSearch() {
		const name = query.trim();
		if (!name) return;

		loading = true;
		searched = true;
		result = await getDocstring(name);
		loading = false;
	}
</script>

<div class="docs-panel">
	<div class="search-row">
		<input
			class="doc-input"
			bind:value={query}
			onkeydown={(e) => e.key === 'Enter' && handleSearch()}
			placeholder="pd.DataFrame, print..."
			disabled={!engineReady}
		/>
		<button
			class="search-btn"
			onclick={handleSearch}
			disabled={loading || !query.trim() || !engineReady}
		>
			{#if loading}
				<Loader2 size={14} class="spin" />
			{:else}
				<Search size={14} />
			{/if}
		</button>
	</div>

	{#if !engineReady}
		<div class="doc-hint">Engine loading...</div>
	{:else if loading}
		<div class="doc-hint">Searching...</div>
	{:else if searched && !result}
		<div class="doc-hint">No documentation found for "{query}"</div>
	{:else if result}
		<div class="doc-result">
			<div class="doc-name">{result.name}</div>
			{#if result.signature}
				<div class="doc-sig">{result.name}{result.signature}</div>
			{/if}
			{#if result.docstring}
				<pre class="doc-body">{result.docstring}</pre>
			{:else}
				<div class="doc-hint">No docstring available</div>
			{/if}
		</div>
	{:else}
		<div class="doc-hint">Search for any Python object, function, or module to view its documentation</div>
	{/if}
</div>

<style>
	.docs-panel {
		padding: 0 8px;
	}

	.search-row {
		display: flex;
		gap: 4px;
		padding: 4px 0 8px;
	}

	.doc-input {
		flex: 1;
		padding: 6px 8px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text);
		font-size: 12px;
		outline: none;
		font-family: 'Fira Code', monospace;
	}

	.doc-input:focus {
		border-color: var(--nb-pink);
	}

	.doc-input::placeholder {
		color: var(--nb-text-muted);
	}

	.search-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.search-btn:hover:not(:disabled) {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.search-btn:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.search-btn :global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.doc-hint {
		padding: 16px 4px;
		text-align: center;
		color: var(--nb-text-muted);
		font-size: 12px;
		line-height: 1.5;
	}

	.doc-result {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.doc-name {
		font-size: 13px;
		font-weight: 600;
		color: var(--nb-pink);
		font-family: 'Fira Code', monospace;
		padding: 0 4px;
	}

	.doc-sig {
		font-size: 11px;
		color: var(--nb-text-secondary);
		font-family: 'Fira Code', monospace;
		padding: 4px 8px;
		background: var(--nb-card);
		border-radius: 4px;
		word-break: break-all;
		line-height: 1.4;
	}

	.doc-body {
		font-size: 11px;
		color: var(--nb-text);
		font-family: 'Fira Code', monospace;
		padding: 8px;
		background: var(--nb-card);
		border-radius: 6px;
		white-space: pre-wrap;
		word-break: break-word;
		line-height: 1.5;
		margin: 0;
		max-height: 400px;
		overflow-y: auto;
	}

	.doc-body::-webkit-scrollbar {
		width: 4px;
	}

	.doc-body::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 2px;
	}
</style>
