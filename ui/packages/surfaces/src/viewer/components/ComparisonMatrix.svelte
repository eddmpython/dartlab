<script lang="ts">
	// 회사 간 비교 매트릭스 · 단일 PanelMatrix 와 같은 골격, 단 열 = period 대신 **회사**.
	// 각 회사의 섹션/블록 콘텐츠를 자기 열에 통째로(셀 = 본문). 한쪽만 = honest-gap(⌀).
	// 헤더 = 회사명·코드 + 원본(DART) 링크 + ✕(비교에서 빼기). 기간은 상단 타임라인이 담당하므로 헤더에 없음.
	import { X } from 'lucide-svelte';
	import CellContent from './CellContent.svelte';
	import type { AlignedRow } from '../lib/compare';

	interface CompareCol {
		code: string;
		corpName: string;
		dartUrl?: string | null; // 그 회사의 현재 시점 DART 원본 공시 링크
		isRef?: boolean; // 기준(보고 있는) 회사 · 빼기 불가
	}

	let {
		rows,
		companies,
		period,
		onRemove,
		removingCode = null
	}: {
		rows: AlignedRow[];
		companies: CompareCol[];
		period: string;
		onRemove?: (code: string) => void;
		removingCode?: string | null; // 빼는 중인 회사 · 그 ✕ 에 스피너
	} = $props();

	// 열 = 회사. 회사당 minmax(280px,1fr) · N≥5 가로 스크롤(.matrix-scroll overflow:auto).
	const template = $derived(`repeat(${companies.length}, minmax(280px, 1fr))`);
</script>

{#if !period}
	<div class="empty">기간을 선택하세요.</div>
{:else if rows.length === 0}
	<div class="empty">선택한 절·시점에는 비교할 공시 항목이 없습니다.</div>
{:else}
	<div class="matrix-scroll">
		<div class="matrix" style="grid-template-columns: {template}">
			<!-- 헤더: 회사명 + 원본 링크 + 빼기 -->
			{#each companies as c (c.code)}
				<div class="cell head company-head">
					<span class="corp">{c.corpName || c.code}</span>
					<span class="code">{c.code}</span>
					<span class="head-actions">
						{#if c.dartUrl}
							<a class="src-link" href={c.dartUrl} target="_blank" rel="noreferrer noopener" title={`${period} 원본 공시`}>원본 ↗</a>
						{/if}
						{#if onRemove && !c.isRef}
							<button
								type="button"
								class="rm-btn"
								onclick={() => onRemove?.(c.code)}
								disabled={c.code === removingCode}
								title="비교에서 빼기"
								aria-label={`${c.corpName} 비교에서 빼기`}
							>
								{#if c.code === removingCode}
									<span class="rm-spinner" aria-hidden="true"></span>
								{:else}
									<X size={11} />
								{/if}
							</button>
						{/if}
					</span>
				</div>
			{/each}

			<!-- 본문: 각 회사 셀(섹션/블록 콘텐츠 통째) -->
			{#each rows as r (r.alignKey)}
				{#each companies as c, ci (c.code)}
					<div class="cell body-cell" class:gap={r.cells[ci] == null}>
						{#if r.cells[ci] != null}
							<CellContent value={r.cells[ci] ?? ''} />
						{:else}
							<span class="gap-mark" title="이 회사엔 해당 공시가 없습니다">⌀ 해당 공시 없음</span>
						{/if}
					</div>
				{/each}
			{/each}
		</div>
	</div>
{/if}

<style>
	.empty {
		padding: 24px;
		text-align: center;
		font-size: 12px;
		color: #94a3b8;
	}
	.matrix-scroll {
		height: 100%;
		overflow: auto;
	}
	.matrix {
		display: grid;
		align-items: stretch;
	}
	.cell {
		border-bottom: 1px solid #1e2433;
		border-right: 1px solid #141a26;
		padding: 8px 10px;
		min-width: 0;
	}
	.head {
		position: sticky;
		top: 0;
		z-index: 20;
		background: #0a0e18;
		border-bottom: 1px solid #263145;
	}
	.company-head {
		display: flex;
		align-items: baseline;
		gap: 8px;
	}
	.corp {
		font-size: 14px;
		font-weight: 800;
		color: #f1f5f9;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.code {
		font-family: monospace;
		font-size: 10px;
		color: #94a3b8;
	}
	.head-actions {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}
	.src-link {
		font-size: 10px;
		color: #94a3b8;
		text-decoration: none;
		white-space: nowrap;
	}
	.src-link:hover {
		color: var(--amber);
	}
	.rm-btn {
		display: inline-flex;
		align-items: center;
		padding: 2px;
		background: none;
		border: none;
		border-radius: 3px;
		color: #64748b;
		cursor: pointer;
	}
	.rm-btn:hover {
		color: #f87171;
		background: rgba(248, 113, 113, 0.12);
	}
	.rm-btn:disabled {
		cursor: wait;
	}
	.rm-spinner {
		display: inline-block;
		width: 11px;
		height: 11px;
		border: 2px solid rgba(248, 113, 113, 0.3);
		border-top-color: #f87171;
		border-radius: 50%;
		animation: rm-spin 0.6s linear infinite;
	}
	@keyframes rm-spin {
		to {
			transform: rotate(360deg);
		}
	}
	.body-cell {
		color: #e2e8f0;
		max-height: 520px;
		overflow: auto;
	}
	.body-cell.gap {
		background: repeating-linear-gradient(45deg, transparent, transparent 6px, rgba(100, 116, 139, 0.04) 6px, rgba(100, 116, 139, 0.04) 12px);
	}
	.gap-mark {
		font-size: 11px;
		color: #64748b;
		font-style: italic;
	}
</style>
