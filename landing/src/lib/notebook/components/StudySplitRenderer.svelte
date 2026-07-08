<script lang="ts">
	import { Plus } from 'lucide-svelte';
	import type { Snippet } from 'svelte';
	import type { Cell as CellType } from '../stores/notebookStore';
	import { notebook, addCell } from '../stores/notebookStore';
	import StudyRenderer from './StudyRenderer.svelte';
	import Cell from './Cell.svelte';

	let { footer }: { footer?: Snippet } = $props();

	const practiceCells = $derived.by(() => {
		return $notebook.cells.filter(
			(c) => (c.type === 'code' || c.type === 'markdown') && !c.study
		);
	});

	function handleAdd(type: CellType['type']) {
		const last = practiceCells.at(-1);
		addCell(type, last?.id);
	}
</script>

<div class="split-layout">
	<div class="split-left">
		<div class="split-left-content">
			<StudyRenderer learnOnly />
			{#if footer}
				{@render footer()}
			{/if}
		</div>
	</div>

	<div class="split-divider"></div>

	<div class="split-right">
		<div class="split-right-content">
			{#each practiceCells as cell (cell.id)}
				<Cell {cell} />
			{/each}

			<div class="add-cell-area">
				<button class="add-cell-btn" onclick={() => handleAdd('code')}>
					<Plus size={14} />
					<span>Code</span>
				</button>
				<button class="add-cell-btn" onclick={() => handleAdd('markdown')}>
					<Plus size={14} />
					<span>Markdown</span>
				</button>
			</div>
		</div>
	</div>
</div>

<style>
	.split-layout {
		display: flex;
		height: 100vh;
		overflow: hidden;
	}

	.split-left {
		flex: 1;
		min-width: 0;
		overflow-y: auto;
		overflow-x: hidden;
		padding: 0 24px;
		display: flex;
		flex-direction: column;
	}

	.split-left-content {
		display: flex;
		flex-direction: column;
		gap: 16px;
		padding: 16px 0 40px;
	}

	.split-divider {
		width: 1px;
		background: var(--nb-border);
		flex-shrink: 0;
	}

	.split-right {
		flex: 1;
		min-width: 0;
		overflow-y: auto;
	}

	.split-right-content {
		padding: 80px 56px 100px;
		max-width: 800px;
		margin: 0 auto;
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 16px;
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

	.split-left::-webkit-scrollbar,
	.split-right::-webkit-scrollbar {
		width: 4px;
	}

	.split-left::-webkit-scrollbar-track,
	.split-right::-webkit-scrollbar-track {
		background: transparent;
	}

	.split-left::-webkit-scrollbar-thumb,
	.split-right::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 2px;
	}

	.split-left::-webkit-scrollbar-thumb:hover,
	.split-right::-webkit-scrollbar-thumb:hover {
		background: var(--nb-text-muted);
	}
</style>
