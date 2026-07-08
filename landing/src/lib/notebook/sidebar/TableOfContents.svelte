<script lang="ts">
	import { notebook, activeCellId } from '../stores/notebookStore';

	interface TocEntry {
		id: string;
		level: number;
		text: string;
	}

	let entries = $derived.by(() => {
		const result: TocEntry[] = [];
		for (const cell of $notebook.cells) {
			if (cell.type !== 'markdown') continue;
			const lines = cell.content.split('\n');
			for (const line of lines) {
				const match = line.match(/^(#{1,6})\s+(.+)$/);
				if (match) {
					result.push({
						id: cell.id,
						level: match[1].length,
						text: match[2].trim()
					});
				}
			}
		}
		return result;
	});

	let visible = $derived(entries.length > 0);

	function scrollToCell(cellId: string) {
		activeCellId.set(cellId);
		const el = document.querySelector(`[data-cell-id="${cellId}"]`);
		if (el) {
			el.scrollIntoView({ behavior: 'smooth', block: 'center' });
		}
	}
</script>

{#if visible}
	<div class="toc">
		<div class="toc-title">OUTLINE</div>
		<div class="toc-list">
			{#each entries as entry}
				<button
					class="toc-item level-{entry.level}"
					class:active={$activeCellId === entry.id}
					onclick={() => scrollToCell(entry.id)}
				>
					{entry.text}
				</button>
			{/each}
		</div>
	</div>
{/if}

<style>
	.toc {
		position: fixed;
		right: 24px;
		top: var(--nb-toc-top, 80px);
		width: 180px;
		max-height: calc(100vh - var(--nb-toc-top, 80px) - 40px);
		overflow-y: auto;
		z-index: 20;
	}

	.toc-title {
		font-size: 10px;
		font-weight: 600;
		color: var(--nb-text-muted);
		letter-spacing: 0.08em;
		padding: 0 8px 8px;
	}

	.toc-list {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.toc-item {
		display: block;
		width: 100%;
		text-align: left;
		border: none;
		background: transparent;
		color: var(--nb-text-muted);
		font-size: 12px;
		padding: 3px 8px;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.1s ease;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		line-height: 1.5;
	}

	.toc-item:hover {
		color: var(--nb-text);
		background: var(--nb-surface);
	}

	.toc-item.active {
		color: var(--nb-pink);
		background: var(--nb-pink-subtle);
	}

	.toc-item.level-1 { padding-left: 8px; font-weight: 600; }
	.toc-item.level-2 { padding-left: 16px; }
	.toc-item.level-3 { padding-left: 24px; font-size: 11px; }
	.toc-item.level-4 { padding-left: 32px; font-size: 11px; }
	.toc-item.level-5 { padding-left: 40px; font-size: 11px; }
	.toc-item.level-6 { padding-left: 48px; font-size: 11px; }

	.toc::-webkit-scrollbar {
		width: 3px;
	}

	.toc::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 2px;
	}

	@media (max-width: 1024px) {
		.toc {
			display: none;
		}
	}
</style>
