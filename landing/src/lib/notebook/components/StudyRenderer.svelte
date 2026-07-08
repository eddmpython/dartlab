<script lang="ts">
	import { BookOpen, PencilLine, List, Plus } from 'lucide-svelte';
	import type { Cell as CellType } from '../stores/notebookStore';
	import { notebook, activeCellId, addCell } from '../stores/notebookStore';
	import { groupStudyCells } from '../utils/groupStudyCells';
	import Cell from './Cell.svelte';

	let { learnOnly = false }: { learnOnly?: boolean } = $props();

	const grouped = $derived.by(() => {
		return groupStudyCells($notebook.cells, { learnOnly });
	});

	const isShowcase = $derived(
		$notebook.metadata?.layout === 'showcase' || $notebook.metadata?.layout === 'marimoFullIDE'
	);

	const tocEntries = $derived.by(() => {
		return grouped.sections
			.map((s) => {
				const block = s.headerCell.study?.block as Record<string, unknown> | undefined;
				const title = (block?.title as string) || '';
				return { id: s.id, text: title };
			})
			.filter((e) => e.text);
	});

	let tocOpen = $state(false);

	function scrollToSection(id: string) {
		activeCellId.set(id);
		const el = document.querySelector(`[data-cell-id="${id}"]`);
		if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
		tocOpen = false;
	}

	function hasPractice(section: { practiceCells: CellType[] }): boolean {
		return section.practiceCells.length > 0;
	}

	function handleAddInSection(
		type: CellType['type'],
		practiceCells: CellType[],
		learnCells: CellType[],
		sectionId: string
	) {
		if (practiceCells.length > 0) {
			addCell(type, practiceCells.at(-1)!.id);
			return;
		}
		if (learnCells.length > 0) {
			addCell(type, learnCells.at(-1)!.id);
			return;
		}
		addCell(type, sectionId);
	}
</script>

{#each grouped.preSectionCells as cell (cell.id)}
	<Cell {cell} />
{/each}

{#if tocEntries.length > 0}
	<div class="mobile-toc-card">
		<button class="mobile-toc-header" onclick={() => (tocOpen = !tocOpen)}>
			<List size={14} />
			<span>목차</span>
			<span class="mobile-toc-count">{tocEntries.length}</span>
		</button>
		{#if tocOpen}
			<div class="mobile-toc-list">
				{#each tocEntries as entry, i}
					<button class="mobile-toc-item" onclick={() => scrollToSection(entry.id)}>
						<span class="mobile-toc-num">{i + 1}</span>
						<span>{entry.text}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<div class="sections-wrapper" class:showcase-mode={isShowcase}>
{#each grouped.sections as section (section.id)}
	{#if isShowcase || !hasPractice(section)}
		<div class="showcase-section">
			<Cell cell={section.headerCell} />
			{#each section.learnCells as cell (cell.id)}
				<Cell {cell} />
			{/each}
			{#each section.practiceCells as cell (cell.id)}
				<Cell {cell} />
			{/each}
		</div>
	{:else}
		<div class="section-card">
			<Cell cell={section.headerCell} />

			{#if section.learnCells.length > 0}
				<div class="zone learn-zone">
					<div class="zone-label">
						<BookOpen size={13} />
						<span>학습하기</span>
					</div>
					<div class="zone-content">
						{#each section.learnCells as cell (cell.id)}
							<Cell {cell} />
						{/each}
					</div>
				</div>
			{/if}

			{#if !learnOnly}
				<div class="zone practice-zone">
					<div class="zone-label">
						<PencilLine size={13} />
						<span>실습하기</span>
					</div>
					<div class="zone-content">
						{#each section.practiceCells as cell (cell.id)}
							<Cell {cell} />
						{/each}
						<div class="practice-add-area">
							<button class="practice-add-btn" onclick={() => handleAddInSection('code', section.practiceCells, section.learnCells, section.headerCell.id)}>
								<Plus size={12} />
								<span>Code</span>
							</button>
							<button class="practice-add-btn" onclick={() => handleAddInSection('markdown', section.practiceCells, section.learnCells, section.headerCell.id)}>
								<Plus size={12} />
								<span>Markdown</span>
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
{/each}
</div>

{#each grouped.postSectionCells as cell (cell.id)}
	<Cell {cell} />
{/each}

<style>
	.sections-wrapper {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.sections-wrapper.showcase-mode {
		gap: 4rem;
	}

	.showcase-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.section-card {
		border: 1px solid var(--nb-border);
		border-radius: 12px;
		overflow: visible;
	}

	.zone {
		border-top: 1px solid var(--nb-border);
	}

	.zone-label {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 1.25rem;
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--nb-text-muted);
		letter-spacing: 0.04em;
	}

	.zone-content {
		display: flex;
		flex-direction: column;
		gap: 12px;
		padding: 0 1rem 1rem 1rem;
	}

	.practice-zone .zone-label {
		color: var(--nb-text-secondary);
	}

	.practice-zone .zone-content {
		padding: 0 1.5rem 1rem 1.5rem;
	}

	.practice-add-area {
		display: flex;
		justify-content: center;
		gap: 6px;
		padding: 4px 0;
	}

	.practice-add-btn {
		display: flex;
		align-items: center;
		gap: 3px;
		padding: 4px 12px;
		border: 1px dashed var(--nb-border);
		border-radius: 6px;
		background: transparent;
		color: var(--nb-text-muted);
		font-size: 11px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.practice-add-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.mobile-toc-card {
		display: none;
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		overflow: hidden;
	}

	.mobile-toc-header {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		padding: 10px 14px;
		border: none;
		background: var(--nb-card);
		color: var(--nb-text-secondary);
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
	}

	.mobile-toc-count {
		margin-left: auto;
		font-size: 11px;
		color: var(--nb-text-muted);
		font-weight: 400;
	}

	.mobile-toc-list {
		display: flex;
		flex-direction: column;
		border-top: 1px solid var(--nb-border);
	}

	.mobile-toc-item {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 8px 14px;
		border: none;
		background: transparent;
		color: var(--nb-text-muted);
		font-size: 12.5px;
		cursor: pointer;
		text-align: left;
		transition: all 0.1s ease;
	}

	.mobile-toc-item:hover {
		background: var(--nb-pink-subtle);
		color: var(--nb-text);
	}

	.mobile-toc-num {
		width: 18px;
		height: 18px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		background: var(--nb-surface);
		color: var(--nb-text-muted);
		font-size: 10px;
		font-weight: 600;
		flex-shrink: 0;
	}

	@media (max-width: 640px) {
		.section-card {
			border-radius: 8px;
		}

		.zone-content {
			padding: 0 0.75rem 0.75rem 0.75rem;
			gap: 4px;
		}

		.practice-zone .zone-content {
			padding: 0 1rem 0.75rem 1rem;
		}

		.mobile-toc-card {
			display: block;
		}
	}

	@media (min-width: 641px) {
		.mobile-toc-card {
			display: none !important;
		}
	}
</style>
