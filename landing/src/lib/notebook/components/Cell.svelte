<script lang="ts">
	import { Play, Square, Trash2, ChevronUp, ChevronDown, Plus, FileText, Code } from 'lucide-svelte';
	import type { Cell as CellType } from '../stores/notebookStore';
	import {
		activeCellId,
		cellOutputs,
		updateCellContent,
		removeCell,
		moveCell,
		changeCellType,
		addCell,
		focusNextCell,
	} from '../stores/notebookStore';
	import { executeCell, interruptExecution, runningCellId, reactiveQueue } from '../stores/executionStore';
	import { cellErrors } from '../stores/notebookStore';
	import CodeCell from './CodeCell.svelte';
	import MarkdownCell from './MarkdownCell.svelte';
	import OutputPanel from './OutputPanel.svelte';

	interface Props {
		cell: CellType;
	}

	let { cell }: Props = $props();

	let isEditingMarkdown = $state(false);

	const isActive = $derived($activeCellId === cell.id);
	const isRunning = $derived($runningCellId === cell.id);
	const isQueued = $derived($reactiveQueue.has(cell.id));
	const isMarkdown = $derived(cell.type === 'markdown');
	const multiDefVars = $derived($cellErrors.get(cell.id) ?? []);

	// 실행 중 경과시간(marimo 식): isRunning 이면 100ms 마다 갱신, 끝나면 최종 executionTime 로 대체.
	let elapsedMs = $state(0);
	$effect(() => {
		if (!isRunning) return;
		const start = performance.now();
		elapsedMs = 0;
		const id = setInterval(() => { elapsedMs = performance.now() - start; }, 100);
		return () => clearInterval(id);
	});

	function handleClick() {
		activeCellId.set(cell.id);
	}

	function handleRun() {
		executeCell(cell.id, cell.content);
	}

	function handleRunAction() {
		if (isRunning) {
			void interruptExecution();
			return;
		}
		handleRun();
	}

	function handleRunAndMove() {
		executeCell(cell.id, cell.content, true);
	}

	function formatTime(ms: number): string {
		if (ms < 1) return '<1ms';
		if (ms < 1000) return `${Math.round(ms)}ms`;
		if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
		return `${(ms / 60000).toFixed(1)}m`;
	}
</script>

<div
	class="cell-row"
	class:active={isActive}
	class:running={isRunning}
	class:queued={isQueued}
	data-cell-id={cell.id}
>
	<div class="left-actions" aria-hidden="true">
		<button
			class="side-btn add-above"
			onclick={(e) => { e.stopPropagation(); addCell('code', undefined, cell.id); }}
			aria-label="Add cell above"
		>
			<Plus size={12} />
		</button>
		<button
			class="side-btn add-below"
			onclick={(e) => { e.stopPropagation(); addCell('code', cell.id); }}
			aria-label="Add cell below"
		>
			<Plus size={12} />
		</button>
	</div>

	<div class="cell-body">
		<div class="cell-card-wrapper">
			<div class="cell-actions">
				{#if cell.type === 'code'}
					<button
						class="action-btn run-btn"
						onclick={(e) => { e.stopPropagation(); handleRunAction(); }}
						aria-label={isRunning ? 'Stop execution' : 'Run (Ctrl+Enter)'}
					>
						{#if isRunning}
							<Square size={13} />
						{:else}
							<Play size={13} />
						{/if}
					</button>
				{/if}
				<button
					class="action-btn"
					onclick={(e) => { e.stopPropagation(); moveCell(cell.id, 'up'); }}
					aria-label="Move up"
				>
					<ChevronUp size={13} />
				</button>
				<button
					class="action-btn"
					onclick={(e) => { e.stopPropagation(); moveCell(cell.id, 'down'); }}
					aria-label="Move down"
				>
					<ChevronDown size={13} />
				</button>
				{#if isMarkdown}
					<button
						class="action-btn convert-btn"
						onclick={(e) => { e.stopPropagation(); changeCellType(cell.id, 'code'); }}
						aria-label="Convert to Code"
					>
						<Code size={13} />
					</button>
				{:else}
					<button
						class="action-btn convert-btn"
						onclick={(e) => { e.stopPropagation(); changeCellType(cell.id, 'markdown'); }}
						aria-label="Convert to Markdown"
					>
						<FileText size={13} />
					</button>
				{/if}
				<button
					class="action-btn delete-btn"
					onclick={(e) => { e.stopPropagation(); removeCell(cell.id); }}
					aria-label="Delete cell"
				>
					<Trash2 size={13} />
				</button>
			</div>

			<div
				class="cell-card"
				class:markdown-card={isMarkdown}
				onclick={handleClick}
				role="button"
				tabindex="0"
				onkeydown={(e) => e.key === 'Enter' && handleClick()}
			>
				{#if cell.type === 'code'}
					<CodeCell
						content={cell.content}
						{isActive}
						{isRunning}
						onContentChange={(content) => updateCellContent(cell.id, content)}
						onRun={handleRun}
						onRunAndMove={handleRunAndMove}
					/>
				{:else if cell.type === 'markdown'}
					<MarkdownCell
						content={cell.content}
						{isActive}
						isEditing={isEditingMarkdown}
						onContentChange={(content) => updateCellContent(cell.id, content)}
						onStartEdit={() => (isEditingMarkdown = true)}
						onStopEdit={() => (isEditingMarkdown = false)}
						onShiftEnter={() => focusNextCell(cell.id)}
					/>
				{/if}

				{#if cell.type === 'code'}
				{@const output = $cellOutputs.get(cell.id)}
				{#if output || multiDefVars.length > 0}
					<OutputPanel {output} {multiDefVars} />
				{/if}
			{/if}
			</div>
		</div>

		{#if cell.type === 'code'}
			{#if isRunning}
				<span class="exec-time running-time" aria-label="Elapsed time">{formatTime(elapsedMs)}</span>
			{:else if cell.executionTime != null}
				<span class="exec-time">{formatTime(cell.executionTime)}</span>
			{/if}
		{/if}
	</div>
</div>

<style>
	.cell-row {
		position: relative;
	}

	.left-actions {
		position: absolute;
		left: -24px;
		top: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		width: 20px;
		padding: 2px 0;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.cell-row:hover .left-actions {
		opacity: 1;
	}

	.cell-card-wrapper {
		position: relative;
		flex: 1;
		min-width: 0;
	}

	.cell-actions {
		position: absolute;
		top: -12px;
		right: 8px;
		display: flex;
		align-items: center;
		gap: 0;
		padding: 2px 4px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		opacity: 0;
		transition: opacity 0.15s ease;
		z-index: 10;
	}

	.cell-row:hover .cell-actions {
		opacity: 0.9;
	}

	.cell-actions:hover {
		opacity: 1 !important;
	}

	.cell-card {
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		overflow: hidden;
		outline: none;
		transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
		background: var(--nb-card);
	}

	.cell-row:hover .cell-card {
		border-color: var(--nb-text-muted);
	}

	.cell-row.active .cell-card {
		border-color: var(--nb-pink);
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
	}

	.cell-row.running .cell-card {
		border-color: var(--nb-pink);
		animation: pulse-border 1.5s ease-in-out infinite;
	}

	.cell-row.queued .cell-card {
		border-color: #facc15;
		animation: pulse-queued 1.2s ease-in-out infinite;
	}

	@keyframes pulse-border {
		0%, 100% { border-color: var(--nb-pink); }
		50% { border-color: var(--nb-pink-bright); }
	}

	@keyframes pulse-queued {
		0%, 100% { border-color: #facc15; }
		50% { border-color: rgba(250, 204, 21, 0.3); }
	}

	.action-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: none;
		border-radius: 5px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.action-btn:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.run-btn {
		color: var(--nb-pink);
	}

	.run-btn:hover {
		background: var(--nb-pink-subtle);
		color: var(--nb-pink-bright);
	}

	.delete-btn {
		color: var(--nb-error);
	}

	.delete-btn:hover {
		background: rgba(239, 68, 68, 0.1);
	}

	.side-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		border: none;
		border-radius: 50%;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.add-above,
	.add-below {
		width: 18px;
		height: 18px;
		opacity: 0;
		transition: opacity 0.1s ease;
	}

	.cell-row:hover .add-above,
	.cell-row:hover .add-below {
		opacity: 0.5;
	}

	.add-above:hover,
	.add-below:hover {
		opacity: 1 !important;
		background: var(--nb-pink-subtle);
		color: var(--nb-pink);
	}

	.convert-btn:hover {
		background: var(--nb-pink-subtle);
		color: var(--nb-pink);
	}

	.markdown-card {
		border-color: transparent;
		background: transparent;
	}


	.cell-row:hover .markdown-card {
		border-color: var(--nb-border);
		background: var(--nb-card);
	}


	.cell-row.active .markdown-card {
		border-color: var(--nb-pink);
		background: var(--nb-card);
	}


	.cell-body {
		position: relative;
	}

	.cell-card-wrapper .cell-card {
		width: 100%;
	}

	.exec-time {
		position: absolute;
		right: -4px;
		top: 6px;
		transform: translateX(100%);
		font-family: var(--dl-font-mono);
		font-size: 10px;
		color: var(--nb-text-muted);
		user-select: none;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	/* 실행 중: 핀 색 + 은은한 깜빡임(marimo 식 진행 표시). */
	.running-time {
		color: var(--nb-pink);
		animation: running-pulse 1.2s ease-in-out infinite;
	}

	@keyframes running-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.45; }
	}

	@media (max-width: 640px) {
		.left-actions {
			display: none;
		}

		.cell-actions {
			position: relative;
			top: auto;
			right: auto;
			justify-content: flex-end;
			border: none;
			box-shadow: none;
			background: transparent;
			opacity: 1;
			padding: 2px 0;
		}

		.exec-time {
			display: none;
		}
	}
</style>
