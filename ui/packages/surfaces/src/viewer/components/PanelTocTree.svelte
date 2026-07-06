<script lang="ts">
	// 목차 · chapter > sectionLeaf > (활성 섹션이면) blockLeaf 트리. landing 디자인(다크 네이비 + 오렌지).
	// 최근 XBRL 주석은 개별 주석(일반사항·재무위험관리·유형자산…)이 blockLeaf(NT_ 키)로 상세 분해 · 활성 섹션
	// 아래 그 blocks 를 펼쳐 주석 단위 네비게이션. 주석 클릭 시 격자가 그 주석만(기간별)으로 필터.
	import type { PanelTocResponse } from '../lib/types';

	let {
		toc,
		activeSectionKey,
		activeBlock,
		onpick,
		onpickBlock
	}: {
		toc: PanelTocResponse;
		activeSectionKey: string | undefined;
		activeBlock: string | null;
		onpick: (sectionKey: string) => void;
		onpickBlock: (sectionKey: string, blockLeaf: string) => void;
	} = $props();
</script>

<nav class="toc-tree">
	{#each toc.chapters as ch (ch.chapter)}
		<div class="chapter">
			<div class="chapter-label">{ch.chapter}</div>
			<div class="sections">
				{#each ch.sections as sec (sec.sectionKey)}
					<button
						type="button"
						class="section"
						class:active={sec.sectionKey === activeSectionKey && !activeBlock}
						class:open={sec.sectionKey === activeSectionKey}
						onclick={() => onpick(sec.sectionKey)}
						title={sec.sectionLeaf}
					>
						<span class="section-name">{sec.sectionLeaf}</span>
						{#if sec.blocks.length > 1}<span class="count">{sec.blocks.length}</span>{/if}
					</button>
					{#if sec.sectionKey === activeSectionKey && sec.blocks.length > 1}
						<div class="blocks">
							{#each sec.blocks as b (b.blockLeaf)}
								<button
									type="button"
									class="block"
									class:active={activeBlock === b.blockLeaf}
									onclick={() => onpickBlock(sec.sectionKey, b.blockLeaf)}
									title={b.blockLeaf}
								>
									<span class="block-name">{b.blockLeaf}</span>
								</button>
							{/each}
						</div>
					{/if}
				{/each}
			</div>
		</div>
	{/each}
</nav>

<style>
	.toc-tree {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.chapter-label {
		padding: 5px 6px 3px;
		font-size: 10px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #94a3b8;
	}
	.sections {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.section {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		text-align: left;
		padding: 5px 8px;
		border: 1px solid transparent;
		border-radius: 5px;
		background: transparent;
		color: #cbd5e1;
		font: inherit;
		font-size: 12px;
		cursor: pointer;
		transition: background 0.12s, color 0.12s, border-color 0.12s;
	}
	.section:hover {
		background: rgba(var(--amber-rgb), 0.06);
		color: #e2e8f0;
	}
	.section.active {
		background: rgba(var(--amber-rgb), 0.1);
		border-color: rgba(var(--amber-rgb), 0.5);
		color: #f8fafc;
		font-weight: 600;
	}
	.section.open:not(.active) {
		color: #e2e8f0;
	}
	.section-name {
		flex: 1 1 auto;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.count {
		flex-shrink: 0;
		min-width: 18px;
		padding: 0 5px;
		border-radius: 9px;
		background: rgba(148, 163, 184, 0.12);
		color: #94a3b8;
		font-size: 10px;
		font-weight: 600;
		text-align: center;
		font-variant-numeric: tabular-nums;
	}
	.blocks {
		display: flex;
		flex-direction: column;
		gap: 1px;
		margin: 1px 0 3px 8px;
		padding-left: 8px;
		border-left: 1px solid #1e2433;
	}
	.block {
		display: block;
		width: 100%;
		text-align: left;
		padding: 4px 8px;
		border: 1px solid transparent;
		border-radius: 5px;
		background: transparent;
		color: #94a3b8;
		font: inherit;
		font-size: 11.5px;
		cursor: pointer;
		transition: background 0.12s, color 0.12s, border-color 0.12s;
	}
	.block:hover {
		background: rgba(var(--amber-rgb), 0.06);
		color: #e2e8f0;
	}
	.block.active {
		background: rgba(var(--amber-rgb), 0.12);
		border-color: rgba(var(--amber-rgb), 0.45);
		color: #f8fafc;
		font-weight: 600;
	}
	.block-name {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
