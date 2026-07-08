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
		cellWidth,
		studyMode,
		studyLayout,
		setStudyLayout,
	} from './stores/notebookStore';
	import type { Notebook, Cell as CellType } from './stores/notebookStore';
	import { initEngine, executeAllCells, engineStatus } from './stores/executionStore';
	import NotebookToolbar from './toolbar/NotebookToolbar.svelte';
	import Cell from './components/Cell.svelte';
	import StudyRenderer from './components/StudyRenderer.svelte';
	import StudySplitRenderer from './components/StudySplitRenderer.svelte';
	import Sidebar from './sidebar/Sidebar.svelte';
	import StudyTocCard from './components/StudyTocCard.svelte';

	import type { Snippet } from 'svelte';

	interface Props {
		embedded?: boolean;
		showHome?: boolean;
		homeHref?: string;
		initialNotebook?: Notebook | null;
		showSidebar?: boolean;
		showToolbar?: boolean;
		footer?: Snippet;
	}

	let {
		embedded = false,
		showHome = true,
		homeHref = '/',
		initialNotebook = null,
		showSidebar = true,
		showToolbar = true,
		footer,
	}: Props = $props();

	let isMobile = $state(false);

	function checkMobile() {
		isMobile = window.innerWidth <= 640;
	}

	$effect(() => {
		if (!$studyMode || $studyLayout !== 'horizontal') return;
		const hasPractice = $notebook.cells.some(
			(c) => (c.type === 'code' || c.type === 'guide') && !c.study
		);
		if (!hasPractice) setStudyLayout('vertical');
	});

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
			engineStarted = true;
			initEngine();

			unsubEngine = engineStatus.subscribe((status) => {
				if (engineStarted && status === 'idle') {
					initEngine();
				}
			});

			checkMobile();
			window.addEventListener('resize', checkMobile);
			document.addEventListener('keydown', handleGlobalKeydown);
		})();

		return () => {
			mounted = false;
			unsubEngine?.();
			window.removeEventListener('resize', checkMobile);
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

<div class="notebook-editor" class:embedded>
	{#if showSidebar}
		<Sidebar />
	{/if}
	{#if showToolbar}
		<NotebookToolbar {showHome} {homeHref} />
	{/if}
	<div class="desktop-toc-wrapper">
		<StudyTocCard />
	</div>

	{#if $studyMode && $studyLayout === 'horizontal' && !isMobile}
		<StudySplitRenderer {footer} />
	{:else}
		<main class="notebook-content width-{$cellWidth}">
			{#if $studyMode}
				<StudyRenderer />
			{:else}
				{#each $notebook.cells as cell (cell.id)}
					<Cell {cell} />
				{/each}

				{#if $notebook.cells.length > 0}
					<div class="add-cell-area">
						<button class="add-cell-btn" onclick={() => handleAddCell('code')}>+ Code</button>
						<button class="add-cell-btn" onclick={() => handleAddCell('markdown')}>+ Markdown</button>
					</div>
				{/if}
			{/if}

			{#if $notebook.cells.length === 0}
				<div class="empty-state">
					<div class="empty-icon">&#9997;</div>
					<p class="empty-title">eddmlab</p>
					<p class="empty-sub">Start coding in Python</p>
					<div class="empty-actions">
						<button class="empty-btn" onclick={() => handleAddCell('code')}>+ Code</button>
						<button class="empty-btn" onclick={() => handleAddCell('markdown')}>+ Markdown</button>
					</div>
				</div>
			{/if}
		</main>
		{#if $studyMode && footer}
			{@render footer()}
		{/if}
	{/if}
</div>

<style>
	.notebook-editor {
		--nb-pink: #ff2d95;
		--nb-pink-bright: #ff5cb0;
		--nb-pink-dim: rgba(255, 45, 149, 0.25);
		--nb-pink-subtle: rgba(255, 45, 149, 0.08);
		--nb-bg: #09090b;
		--nb-surface: #0c0c0e;
		--nb-card: #18181b;
		--nb-border: #27272a;
		--nb-text: #e8e8f0;
		--nb-text-secondary: #9898b0;
		--nb-text-muted: #6b7094;
		--nb-code-bg: #18181b;
		--nb-code-text: #e4e4e7;
		--nb-success: #22c55e;
		--nb-error: #ff4466;
		--nb-toc-top: 80px;

		min-height: 100vh;
		background: var(--nb-bg);
		color: var(--nb-text);
		font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
	}

	:global([data-theme="light"]) .notebook-editor,
	:global(:not([data-theme="dark"])) .notebook-editor {
		--nb-pink: #d6336c;
		--nb-pink-bright: #e8478a;
		--nb-pink-dim: rgba(214, 51, 108, 0.2);
		--nb-pink-subtle: rgba(214, 51, 108, 0.06);
		--nb-bg: #ffffff;
		--nb-surface: #f8f9fa;
		--nb-card: #ffffff;
		--nb-border: #e5e7eb;
		--nb-text: #1a1a2e;
		--nb-text-secondary: #4b5563;
		--nb-text-muted: #9ca3af;
		--nb-code-bg: #f5f5f5;
		--nb-code-text: #1f2937;
		--nb-success: #16a34a;
		--nb-error: #dc2626;
	}

	:global([data-theme="dark"]) .notebook-editor {
		--nb-pink: #ff2d95;
		--nb-pink-bright: #ff5cb0;
		--nb-pink-dim: rgba(255, 45, 149, 0.25);
		--nb-pink-subtle: rgba(255, 45, 149, 0.08);
		--nb-bg: #09090b;
		--nb-surface: #0c0c0e;
		--nb-card: #18181b;
		--nb-border: #27272a;
		--nb-text: #e8e8f0;
		--nb-text-secondary: #9898b0;
		--nb-text-muted: #6b7094;
		--nb-code-bg: #18181b;
		--nb-code-text: #e4e4e7;
		--nb-success: #22c55e;
		--nb-error: #ff4466;
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
		max-width: 640px;
	}

	.notebook-content.width-medium {
		max-width: 800px;
	}

	.notebook-content.width-full {
		max-width: 1200px;
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
