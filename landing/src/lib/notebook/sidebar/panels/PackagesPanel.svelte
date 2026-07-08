<script lang="ts">
	import { onMount } from 'svelte';
	import { Download, Loader2 } from 'lucide-svelte';
	import { installPackage, getInstalledPackages, engineStatus } from '../../stores/executionStore';
	import type { PackageInfo } from '../../engine/executionEngine';

	let packages = $state<PackageInfo[]>([]);
	let inputValue = $state('');
	let installing = $state(false);
	let loading = $state(false);
	let installError = $state('');

	async function refresh() {
		loading = true;
		packages = await getInstalledPackages();
		loading = false;
	}

	async function handleInstall() {
		const name = inputValue.trim();
		if (!name) return;

		installing = true;
		installError = '';
		try {
			await installPackage(name);
			inputValue = '';
			await refresh();
		} catch (err) {
			installError = String(err).split('\n')[0];
		}
		installing = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			handleInstall();
		}
	}

	onMount(() => {
		const unsub = engineStatus.subscribe((status) => {
			if (status === 'ready') refresh();
		});
		return unsub;
	});
</script>

<div class="packages-panel">
	<div class="install-row">
		<input
			class="pkg-input"
			bind:value={inputValue}
			onkeydown={handleKeydown}
			placeholder="Package name..."
			disabled={installing}
		/>
		<button
			class="install-btn"
			onclick={handleInstall}
			disabled={installing || !inputValue.trim()}
		>
			{#if installing}
				<Loader2 size={14} class="spin" />
			{:else}
				<Download size={14} />
			{/if}
		</button>
	</div>

	{#if installError}
		<div class="pkg-error">{installError}</div>
	{/if}

	{#if loading}
		<div class="pkg-loading">Loading...</div>
	{:else if packages.length === 0}
		<div class="pkg-empty">No packages installed</div>
	{:else}
		<div class="pkg-list">
			{#each packages as pkg}
				<div class="pkg-item">
					<span class="pkg-name">{pkg.name}</span>
					<span class="pkg-version">{pkg.version}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.packages-panel {
		padding: 0 8px;
	}

	.install-row {
		display: flex;
		gap: 4px;
		padding: 4px 0 8px;
	}

	.pkg-input {
		flex: 1;
		padding: 6px 8px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text);
		font-size: 12px;
		outline: none;
		font-family: var(--dl-font-mono);
	}

	.pkg-input:focus {
		border-color: var(--nb-pink);
	}

	.pkg-input::placeholder {
		color: var(--nb-text-muted);
	}

	.install-btn {
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

	.install-btn:hover:not(:disabled) {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.install-btn:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.install-btn :global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.pkg-error {
		padding: 4px 8px;
		font-size: 11px;
		color: var(--nb-error);
		word-break: break-word;
	}

	.pkg-loading,
	.pkg-empty {
		padding: 16px 4px;
		text-align: center;
		color: var(--nb-text-muted);
		font-size: 12px;
	}

	.pkg-list {
		display: flex;
		flex-direction: column;
	}

	.pkg-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 4px 4px;
		border-radius: 4px;
		transition: background 0.1s ease;
	}

	.pkg-item:hover {
		background: var(--nb-card);
	}

	.pkg-name {
		font-size: 12px;
		color: var(--nb-text);
		font-family: var(--dl-font-mono);
	}

	.pkg-version {
		font-size: 11px;
		color: var(--nb-text-muted);
		font-family: var(--dl-font-mono);
	}
</style>
