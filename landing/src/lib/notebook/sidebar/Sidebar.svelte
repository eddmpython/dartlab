<script lang="ts">
	import { Box, Variable, FolderTree, TextSearch, Network } from 'lucide-svelte';
	import { sidebarOpen, activePanel, openPanel, closeSidebar } from '../stores/sidebarStore';
	import type { PanelId } from '../stores/sidebarStore';
	import { currentUser } from '../stores/userStore';
	import PackagesPanel from './panels/PackagesPanel.svelte';
	import VariablesPanel from './panels/VariablesPanel.svelte';
	import FilesPanel from './panels/FilesPanel.svelte';
	import DocsPanel from './panels/DocsPanel.svelte';
	import DependenciesPanel from './panels/DependenciesPanel.svelte';

	const panels: { id: PanelId; icon: typeof Box; label: string; requiresAuth?: boolean }[] = [
		{ id: 'packages', icon: Box, label: 'Packages' },
		{ id: 'variables', icon: Variable, label: 'Variables' },
		{ id: 'files', icon: FolderTree, label: 'Files', requiresAuth: true },
		{ id: 'docs', icon: TextSearch, label: 'Docs' },
		{ id: 'dependencies', icon: Network, label: 'Dependencies' },
	];

	function handleIconClick(id: PanelId) {
		const panel = panels.find((p) => p.id === id);
		if (panel?.requiresAuth && !$currentUser) return;
		if ($activePanel === id && $sidebarOpen) {
			closeSidebar();
		} else {
			openPanel(id);
		}
	}
</script>

<div class="sidebar" class:open={$sidebarOpen}>
	<div class="sidebar-icons">
		{#each panels as panel}
			{@const disabled = panel.requiresAuth && !$currentUser}
			<button
				class="icon-btn"
				class:active={$sidebarOpen && $activePanel === panel.id}
				class:disabled-auth={disabled}
				onclick={() => handleIconClick(panel.id)}
				title={disabled ? 'Login required' : panel.label}
				aria-label={panel.label}
			>
				<panel.icon size={18} />
			</button>
		{/each}
	</div>

	{#if $sidebarOpen}
		<div class="sidebar-panel">
			<div class="panel-header">
				<span class="panel-title">{panels.find((p) => p.id === $activePanel)?.label}</span>
				<button class="panel-close" onclick={closeSidebar}>&#215;</button>
			</div>
			<div class="panel-body">
				{#if $activePanel === 'packages'}
					<PackagesPanel />
				{:else if $activePanel === 'variables'}
					<VariablesPanel />
				{:else if $activePanel === 'files'}
					<FilesPanel />
				{:else if $activePanel === 'docs'}
					<DocsPanel />
				{:else if $activePanel === 'dependencies'}
					<DependenciesPanel />
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.sidebar {
		position: fixed;
		left: 0;
		top: 0;
		bottom: 0;
		display: flex;
		z-index: 25;
	}

	.sidebar-icons {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		padding: 60px 4px 16px;
		background: var(--nb-bg);
		width: 40px;
	}

	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		border-radius: 6px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.icon-btn:hover {
		color: var(--nb-text);
		background: var(--nb-surface);
	}

	.icon-btn.active {
		color: var(--nb-text);
		background: var(--nb-surface);
	}

	.icon-btn.disabled-auth {
		cursor: not-allowed;
	}

	.icon-btn.disabled-auth:hover {
		color: var(--nb-text-muted);
		background: transparent;
	}

	.sidebar-panel {
		width: 260px;
		background: var(--nb-surface);
		border-right: 1px solid var(--nb-border);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
	}

	.panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 12px 8px;
		border-bottom: 1px solid var(--nb-border);
	}

	.panel-title {
		font-size: 12px;
		font-weight: 600;
		color: var(--nb-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.panel-close {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		font-size: 16px;
		line-height: 1;
	}

	.panel-close:hover {
		color: var(--nb-text);
		background: var(--nb-card);
	}

	.panel-body {
		flex: 1;
		overflow-y: auto;
		padding: 8px 0;
	}

	@media (max-width: 640px) {
		.sidebar {
			display: none;
		}
	}
</style>
