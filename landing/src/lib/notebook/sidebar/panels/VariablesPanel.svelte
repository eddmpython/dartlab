<script lang="ts">
	import { Loader2, RefreshCw } from 'lucide-svelte';
	import { getVariablesWithInfo, engineStatus, runningCellId } from '../../stores/executionStore';
	import type { VariableInfo } from '../../engine/executionEngine';
	import { onMount } from 'svelte';

	let variables = $state<VariableInfo[]>([]);
	let loading = $state(false);
	let prevRunning: string | null = null;

	async function refresh() {
		loading = true;
		variables = await getVariablesWithInfo();
		loading = false;
	}

	onMount(() => {
		const unsub1 = engineStatus.subscribe((status) => {
			if (status === 'ready') refresh();
		});
		const unsub2 = runningCellId.subscribe((id) => {
			if (prevRunning && !id) {
				setTimeout(refresh, 100);
			}
			prevRunning = id;
		});
		return () => {
			unsub1();
			unsub2();
		};
	});
</script>

<div class="variables-panel">
	<div class="panel-actions">
		<button class="refresh-btn" onclick={refresh} disabled={loading} aria-label="Refresh">
			{#if loading}
				<Loader2 size={13} class="spin" />
			{:else}
				<RefreshCw size={13} />
			{/if}
		</button>
	</div>

	{#if loading && variables.length === 0}
		<div class="var-loading">Loading...</div>
	{:else if variables.length === 0}
		<div class="var-empty">No variables defined</div>
	{:else}
		<div class="var-list">
			{#each variables as v}
				<div class="var-item">
					<div class="var-header">
						<span class="var-name">{v.name}</span>
						<span class="var-type">{v.type}</span>
					</div>
					<div class="var-value">{v.value}</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.variables-panel {
		padding: 0 8px;
	}

	.panel-actions {
		display: flex;
		justify-content: flex-end;
		padding: 4px 0 8px;
	}

	.refresh-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 26px;
		height: 26px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.refresh-btn:hover:not(:disabled) {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.refresh-btn:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.refresh-btn :global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.var-loading,
	.var-empty {
		padding: 16px 4px;
		text-align: center;
		color: var(--nb-text-muted);
		font-size: 12px;
	}

	.var-list {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.var-item {
		padding: 6px 8px;
		border-radius: 6px;
		transition: background 0.1s ease;
	}

	.var-item:hover {
		background: var(--nb-card);
	}

	.var-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2px;
	}

	.var-name {
		font-size: 12px;
		font-weight: 600;
		color: var(--nb-text);
		font-family: 'Fira Code', monospace;
	}

	.var-type {
		font-size: 10px;
		color: var(--nb-pink);
		font-family: 'Fira Code', monospace;
		background: var(--nb-pink-subtle);
		padding: 1px 6px;
		border-radius: 4px;
	}

	.var-value {
		font-size: 11px;
		color: var(--nb-text-muted);
		font-family: 'Fira Code', monospace;
		word-break: break-all;
		line-height: 1.4;
	}
</style>
