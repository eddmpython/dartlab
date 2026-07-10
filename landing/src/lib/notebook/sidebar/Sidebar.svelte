<script lang="ts">
	import { Box, Variable, FolderTree, TextSearch, Network, BookOpen } from 'lucide-svelte';
	import { sidebarOpen, activePanel, openPanel, closeSidebar } from '../stores/sidebarStore';
	import type { PanelId } from '../stores/sidebarStore';
	import PackagesPanel from './panels/PackagesPanel.svelte';
	import VariablesPanel from './panels/VariablesPanel.svelte';
	import FilesPanel from './panels/FilesPanel.svelte';
	import DocsPanel from './panels/DocsPanel.svelte';
	import DependenciesPanel from './panels/DependenciesPanel.svelte';
	import StoriesPanel from './panels/StoriesPanel.svelte';

	// requiresAuth 게이트를 뺐다. 인증은 서버 개념인데 landing 은 adapter-static 무서버라
	// currentUser 가 영원히 null 이었고, 그래서 Files 패널이 항상 비활성이었다.
	const panels: { id: PanelId; icon: typeof Box; label: string }[] = [
		{ id: 'stories', icon: BookOpen, label: 'dartlab 이야기' },
		{ id: 'packages', icon: Box, label: 'Packages' },
		{ id: 'variables', icon: Variable, label: 'Variables' },
		{ id: 'files', icon: FolderTree, label: 'Files' },
		{ id: 'docs', icon: TextSearch, label: 'Docs' },
		{ id: 'dependencies', icon: Network, label: 'Dependencies' },
	];

	function handleIconClick(id: PanelId) {
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
			<button
				class="icon-btn"
				class:active={$sidebarOpen && $activePanel === panel.id}
				onclick={() => handleIconClick(panel.id)}
				title={panel.label}
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
				{#if $activePanel === 'stories'}
					<StoriesPanel />
				{:else if $activePanel === 'packages'}
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
	/* 상단 스트립(--nb-top) 아래에서 시작한다. top:0 이던 시절 패널 헤더가 좌상단 브랜드와
	   같은 자리에 놓여 글자가 겹쳐 찍혔다. 아이콘 레일의 padding-top 60px 도 그 회피용이었다. */
	.sidebar {
		position: fixed;
		left: 0;
		top: var(--nb-top, 48px);
		bottom: 0;
		display: flex;
		z-index: 25;
	}

	.sidebar-icons {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		padding: 8px 4px 16px;
		background: var(--nb-bg);
		width: var(--nb-rail, 40px);
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

	.sidebar-panel {
		width: var(--nb-panel, 260px);
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
