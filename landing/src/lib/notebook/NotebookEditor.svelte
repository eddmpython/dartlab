<script lang="ts">
	import { onMount } from 'svelte';
	import {
		notebook,
		activeCellId,
		editMode,
		addCell,
		loadFromStorage,
		loadNotebook,
		saveToServer,
		cellWidth
	} from './stores/notebookStore';
	import type { Notebook, Cell as CellType } from './stores/notebookStore';
	import {
		initEngine,
		executeAllCells,
		engineStatus,
		setReactiveMode
	} from './stores/executionStore';
	import { resolveNotebookExecutionPolicy } from './executionPolicy';
	import NotebookToolbar from './toolbar/NotebookToolbar.svelte';
	import Cell from './components/Cell.svelte';
	import Sidebar from './sidebar/Sidebar.svelte';
	import { sidebarOpen } from './stores/sidebarStore';

	interface Props {
		embedded?: boolean;
		homeHref?: string;
		initialNotebook?: Notebook | null;
		showSidebar?: boolean;
		showToolbar?: boolean;
	}

	let {
		embedded = false,
		homeHref = '/',
		initialNotebook = null,
		showSidebar = true,
		showToolbar = true
	}: Props = $props();

	let engineStarted = false;

	onMount(() => {
		let unsubEngine: (() => void) | null = null;
		let mounted = true;

		void (async () => {
			if (initialNotebook) {
				loadNotebook(initialNotebook);
			} else if (!embedded) {
				await loadFromStorage();
			}
			if (!mounted) return;
			const execution = resolveNotebookExecutionPolicy($notebook);
			setReactiveMode(execution.mode === 'reactive');
			engineStarted = true;
			void initEngine(execution.autoRun);

			unsubEngine = engineStatus.subscribe((status) => {
				if (engineStarted && status === 'idle') {
					// 죽은 워커를 다시 띄우는 복구 경로에서 셀 전체를 뜻밖에 재실행하지 않는다.
					void initEngine(false);
				}
			});

			document.addEventListener('keydown', handleGlobalKeydown);
		})();

		return () => {
			mounted = false;
			unsubEngine?.();
			document.removeEventListener('keydown', handleGlobalKeydown);
		};
	});

	function handleGlobalKeydown(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && e.key === 's') {
			e.preventDefault();
			saveToServer();
		}

		if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'Enter') {
			e.preventDefault();
			executeAllCells($notebook.cells);
		}

		if (!$editMode) {
			if (e.key === 'a') {
				e.preventDefault();
				if ($activeCellId) addCell('code', undefined);
			}
			if (e.key === 'b') {
				e.preventDefault();
				if ($activeCellId) addCell('code', $activeCellId);
			}
		}
	}

	function handleAddCell(type: CellType['type'], afterId?: string) {
		addCell(type, afterId);
	}
</script>

<div class="notebook-editor" class:embedded class:sidebar-open={showSidebar && $sidebarOpen}>
	{#if showSidebar}
		<Sidebar />
	{/if}
	{#if showToolbar}
		<NotebookToolbar {homeHref} />
	{/if}
	<main class="notebook-content width-{$cellWidth}">
		{#each $notebook.cells as cell (cell.id)}
			<Cell {cell} />
		{/each}

		{#if $notebook.cells.length > 0}
			<div class="add-cell-area">
				<button class="add-cell-btn" onclick={() => handleAddCell('code')}>+ Code</button>
				<button class="add-cell-btn" onclick={() => handleAddCell('markdown')}>+ Markdown</button>
			</div>
		{/if}

		{#if $notebook.cells.length === 0}
			<div class="empty-state">
				<div class="empty-icon">&#9997;</div>
				<p class="empty-title">dartlab notebook</p>
				<p class="empty-sub">Start coding in Python</p>
				<div class="empty-actions">
					<button class="empty-btn" onclick={() => handleAddCell('code')}>+ Code</button>
					<button class="empty-btn" onclick={() => handleAddCell('markdown')}>+ Markdown</button>
				</div>
			</div>
		{/if}
	</main>
</div>

<style>
	/* 색상 SSOT = dartlab tokens.css(--dl-*) 위임. light/dark 는 --dl-* 가 data-theme 로 자동 처리. */
	.notebook-editor {
		--nb-pink: var(--dl-accent);
		--nb-pink-bright: var(--dl-accent-dim);
		--nb-pink-dim: rgba(var(--dl-accent-rgb), 0.25);
		--nb-pink-subtle: rgba(var(--dl-accent-rgb), 0.1);
		--nb-bg: var(--dl-bg-deep);
		--nb-surface: var(--dl-bg-base);
		--nb-card: var(--dl-bg-raised);
		--nb-border: var(--dl-line-strong);
		--nb-text: var(--dl-ink);
		--nb-text-secondary: var(--dl-ink-mute);
		--nb-text-muted: var(--dl-ink-dim);
		--nb-code-bg: var(--dl-bg-raised);
		--nb-code-text: var(--dl-ink);
		--nb-success: var(--dl-good);
		--nb-error: var(--dl-bad);
		--nb-toc-top: 80px;

		/* 상단 스트립 높이. 좌상단 브랜드(top 12px + 32px)가 여기 산다.
		   사이드바는 이 아래에서 시작해야 브랜드와 겹치지 않는다. */
		--nb-top: 48px;
		--nb-rail: 40px;
		--nb-panel: 260px;

		min-height: 100vh;
		background: var(--nb-bg);
		color: var(--nb-text);
		font-family: var(--dl-font-ui);
		transition: padding-left 0.16s ease;
	}

	/* 패널이 열리면 본문을 밀어 낸다. 덮으면 코드가 가려진다. */
	.notebook-editor.sidebar-open {
		padding-left: var(--nb-panel);
	}
	@media (max-width: 640px) {
		.notebook-editor.sidebar-open {
			padding-left: 0;
		}
	}

	.notebook-content {
		padding: 80px 24px 100px;
		padding-left: 64px;
		max-width: 800px;
		margin: 0 auto;
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 16px;
		transition: max-width 0.2s ease;
	}

	.notebook-content.width-compact {
		max-width: 860px;
	}

	.notebook-content.width-medium {
		max-width: 1120px;
	}

	.notebook-content.width-full {
		max-width: none;
		padding-right: 40px;
	}

	.notebook-content.split-mode {
		max-width: 100%;
		padding: 0;
		gap: 0;
	}

	.add-cell-area {
		display: flex;
		justify-content: center;
		gap: 8px;
		padding: 8px 0;
	}

	.add-cell-btn {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 6px 16px;
		border: 1px dashed var(--nb-border);
		border-radius: 8px;
		background: transparent;
		color: var(--nb-text-muted);
		font-size: 12px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.add-cell-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.empty-state {
		text-align: center;
		padding: 120px 20px;
		color: var(--nb-text-muted);
	}

	.empty-icon {
		font-size: 40px;
		margin-bottom: 16px;
		opacity: 0.3;
	}

	.empty-title {
		font-size: 22px;
		font-weight: 700;
		color: var(--nb-pink);
		margin-bottom: 4px;
		letter-spacing: -0.02em;
	}

	.empty-sub {
		margin-bottom: 24px;
		font-size: 14px;
		color: var(--nb-text-muted);
	}

	.empty-actions {
		display: flex;
		gap: 8px;
		justify-content: center;
	}

	.empty-btn {
		padding: 10px 24px;
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		background: var(--nb-card);
		color: var(--nb-text-secondary);
		font-size: 14px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.empty-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.notebook-editor.embedded {
		min-height: auto;
		height: 100%;
		border-radius: 8px;
		overflow: hidden;
		--nb-toc-top: 16px;
	}

	.notebook-editor.embedded .notebook-content {
		padding: 48px 16px 80px;
		padding-left: 16px;
	}

	@media (max-width: 640px) {
		.notebook-content {
			padding: 60px 12px 80px;
			padding-left: 12px;
			gap: 4px;
		}

		.desktop-toc-wrapper {
			display: none;
		}
	}
</style>
