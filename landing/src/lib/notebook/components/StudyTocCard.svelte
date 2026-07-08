<script lang="ts">
	import { notebook, activeCellId, studyMode } from '../stores/notebookStore';

	interface TocEntry {
		id: string;
		level: number;
		text: string;
	}

	const studyEntries = $derived.by(() => {
		const result: TocEntry[] = [];
		for (const cell of $notebook.cells) {
			if (cell.type !== 'study' || !cell.study) continue;
			const s = cell.study;
			if (s.blockType === 'intro') {
				const title = (s.block.title as string) || (s.block.metaTitle as string) || '';
				if (title) result.push({ id: cell.id, level: 1, text: title });
			} else if (s.blockType === 'sectionDivider' || s.blockType === 'sectionTitle' || s.blockType === 'sectionHeader') {
				const title = (s.block.title as string) || '';
				if (title) result.push({ id: cell.id, level: 2, text: title });
			}
		}
		return result;
	});

	const markdownEntries = $derived.by(() => {
		const result: TocEntry[] = [];
		for (const cell of $notebook.cells) {
			if (cell.type !== 'markdown') continue;
			const lines = cell.content.split('\n');
			for (const line of lines) {
				const match = line.match(/^(#{1,4})\s+(.+)$/);
				if (match) {
					result.push({
						id: cell.id,
						level: match[1].length,
						text: match[2].replace(/\*\*/g, '').trim()
					});
				}
			}
		}
		return result;
	});

	const entries = $derived($studyMode ? studyEntries : markdownEntries);

	function handleSelect(cellId: string) {
		activeCellId.set(cellId);
		const el = document.querySelector(`[data-cell-id="${cellId}"]`);
		if (el) {
			el.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}
</script>

{#if entries.length > 0}
	<nav class="toc-card" aria-label="Notebook table of contents">
		{#each entries as entry (entry.id + entry.text)}
			<button
				type="button"
				class:active={$activeCellId === entry.id}
				class={'toc-link level-' + Math.min(entry.level, 4)}
				onclick={() => handleSelect(entry.id)}
			>
				{entry.text}
			</button>
		{/each}
	</nav>
{/if}

<style>
	.toc-card {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 8px;
	}

	.toc-link {
		width: 100%;
		border: 0;
		background: transparent;
		color: var(--nb-text-muted);
		text-align: left;
		font-size: 12px;
		line-height: 1.35;
		padding: 5px 8px;
		border-radius: 6px;
		cursor: pointer;
	}

	.toc-link:hover,
	.toc-link.active {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.level-2 {
		padding-left: 16px;
	}

	.level-3,
	.level-4 {
		padding-left: 24px;
	}
</style>
