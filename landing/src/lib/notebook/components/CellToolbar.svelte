<script lang="ts">
	import type { Cell } from '../stores/notebookStore';

	interface Props {
		cell: Cell;
		onRun?: () => void;
		onDelete: () => void;
		onMoveUp: () => void;
		onMoveDown: () => void;
		onChangeType: (type: Cell['type']) => void;
	}

	let { cell, onRun, onDelete, onMoveUp, onMoveDown, onChangeType }: Props = $props();

	const typeLabels: Record<Cell['type'], string> = {
		code: 'Code',
		markdown: 'Markdown',
	};
</script>

<div class="cell-toolbar">
	<div class="toolbar-left">
		<select
			class="type-select"
			value={cell.type}
			onchange={(e) => onChangeType((e.target as HTMLSelectElement).value as Cell['type'])}
		>
			{#each Object.entries(typeLabels) as [value, label]}
				<option {value}>{label}</option>
			{/each}
		</select>
	</div>

	<div class="toolbar-right">
		{#if cell.type === 'code' && onRun}
			<button class="tb-btn run-btn" onclick={onRun} title="Run (Ctrl+Enter)">
				&#9654;
			</button>
		{/if}
		<button class="tb-btn" onclick={onMoveUp} title="Move up">&#9650;</button>
		<button class="tb-btn" onclick={onMoveDown} title="Move down">&#9660;</button>
		<button class="tb-btn delete-btn" onclick={onDelete} title="Delete cell">&#10005;</button>
	</div>
</div>

<style>
	.cell-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 4px 8px;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	:global(.cell-wrapper:hover) .cell-toolbar,
	:global(.cell-wrapper.active) .cell-toolbar {
		opacity: 1;
	}

	.toolbar-left,
	.toolbar-right {
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.type-select {
		padding: 2px 6px;
		border: 1px solid var(--nb-border);
		border-radius: var(--radius-sm);
		background: var(--nb-card);
		color: var(--nb-text-muted);
		font-size: 11px;
		outline: none;
		cursor: pointer;
	}

	.tb-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--nb-text-muted);
		font-size: 11px;
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.tb-btn:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.run-btn {
		color: var(--nb-pink);
	}

	.run-btn:hover {
		background: var(--nb-pink-subtle);
	}

	.delete-btn:hover {
		background: var(--nb-pink-subtle);
		color: var(--nb-error);
	}
</style>
