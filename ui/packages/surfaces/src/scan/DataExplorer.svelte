<script lang="ts">
	/**
	 * 데이터 탐색 모달 · screen builder + raw 테이블/노트북.
	 *
	 *   탭 1~8 = TableView (raw 테이블)
	 *   탭 9   = SQL Notebook (SqlNotebook · CodeMirror SQL 셀, duckdb 직질의)
	 *
	 * lazy load: parquet source 는 첫 진입 시 SELECT * LIMIT 1000.
	 * 메모리 source (ecosystem/prices/valuation/changes) 는 부모가 props 로 넘김.
	 */
	import { onMount } from 'svelte';
	import { Search, X } from 'lucide-svelte';
	import TableView from './TableView.svelte';
	import RowJsonModal from './RowJsonModal.svelte';
	import SqlNotebook from './SqlNotebook.svelte';
	import ScreenBuilder from './ScreenBuilder.svelte';
	import { TABLE_SOURCES, TABLE_SOURCES_BY_ID, resolveHfPath } from './tableSources';
	import type { TableSource } from './tableSources';
	import type { DartDb } from './duckSql';
	import type { PriceMetrics, ValuationMetrics, ChangeMetrics } from './duckSql';
	import type { FilterCond, ScanNode, SortKey } from './types';

	interface Props {
		open: boolean;
		onClose: () => void;
		nodes: ScanNode[];
		ecosystem: Array<Record<string, unknown>>;
		priceMap: Map<string, PriceMetrics>;
		valuationMap: Map<string, ValuationMetrics>;
		changesMap: Map<string, ChangeMetrics>;
		db: DartDb | null;
		onApplyScreen: (payload: { conds: FilterCond[]; sorts: SortKey[]; cols: string[] }) => void;
	}

	let {
		open,
		onClose,
		nodes,
		ecosystem,
		priceMap,
		valuationMap,
		changesMap,
		db,
		onApplyScreen
	}: Props = $props();

	let activeTabId = $state<string>('screen');
	let activeTab = $derived(TABLE_SOURCES_BY_ID.get(activeTabId) ?? TABLE_SOURCES[0]);

	// 각 탭의 row state
	const tabRows = $state<Record<string, Array<Record<string, unknown>>>>({});
	const tabLoading = $state<Record<string, boolean>>({});
	const tabSearch = $state<Record<string, string>>({});
	let rowJsonRow = $state<Record<string, unknown> | null>(null);

	// in-memory rows derived
	let memoryRows = $derived.by<Record<string, Array<Record<string, unknown>>>>(() => ({
		ecosystem: ecosystem,
		prices: Array.from(priceMap.entries()).map(([stockCode, p]) => ({ stockCode, ...p })),
		valuation: Array.from(valuationMap.entries()).map(([stockCode, v]) => ({ stockCode, ...v })),
		changes: Array.from(changesMap.entries()).map(([stockCode, c]) => ({ stockCode, ...c }))
	}));

	function getRowsForTab(t: TableSource): Array<Record<string, unknown>> {
		if (t.source === 'memory') {
			return memoryRows[t.id] ?? [];
		}
		return tabRows[t.id] ?? [];
	}

	async function loadParquetTab(t: TableSource) {
		if (!db || !t.hfPath || !t.viewName) return;
		if (tabLoading[t.id]) return;
		tabLoading[t.id] = true;
		try {
			const path = resolveHfPath(t.hfPath);
			await db.registerHfParquet(t.viewName, path);
			const limit = t.defaultLimit ?? 1000;
			const result = await db.query<Record<string, unknown>>(
				`SELECT * FROM "${t.viewName}" LIMIT ${limit}`
			);
			tabRows[t.id] = result;
		} catch (err) {
			console.warn(`[scan/data-explorer] ${t.id} 로드 실패`, err);
			tabRows[t.id] = [];
		} finally {
			tabLoading[t.id] = false;
		}
	}

	async function searchParquetTab(t: TableSource, query: string) {
		if (!db || !t.hfPath || !t.viewName) return;
		const trimmed = query.trim();
		if (!trimmed) {
			void loadParquetTab(t);
			return;
		}
		tabLoading[t.id] = true;
		try {
			// 검색 컬럼 ILIKE OR
			const cols = t.searchableColumns ?? [];
			if (cols.length === 0) {
				tabRows[t.id] = [];
				return;
			}
			const escaped = trimmed.replace(/'/g, "''");
			const where = cols.map((c) => `"${c}" ILIKE '%${escaped}%'`).join(' OR ');
			const limit = t.defaultLimit ?? 1000;
			const result = await db.query<Record<string, unknown>>(
				`SELECT * FROM "${t.viewName}" WHERE ${where} LIMIT ${limit}`
			);
			tabRows[t.id] = result;
		} catch (err) {
			console.warn(`[scan/data-explorer] ${t.id} 검색 실패`, err);
		} finally {
			tabLoading[t.id] = false;
		}
	}

	$effect(() => {
		if (!open) return;
		const t = activeTab;
		if (!t) return;
		if (t.source === 'parquet' && tabRows[t.id] === undefined && db) {
			void loadParquetTab(t);
		}
	});

	function handleSearch(t: TableSource, q: string) {
		tabSearch[t.id] = q;
		if (t.source === 'parquet') {
			void searchParquetTab(t, q);
		}
		// 'memory' source 는 TableView 가 frontend filter
	}

	function handleKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape' && !rowJsonRow) onClose();
	}

	function backdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onClose();
	}
</script>

<svelte:window onkeydown={handleKey} />

{#if open}
	<div
		class="de-backdrop"
		role="dialog"
		aria-modal="true"
		aria-label="데이터 탐색"
		onclick={backdropClick}
		onkeydown={handleKey}
		tabindex="-1"
	>
		<div class="de-modal" role="document">
			<header class="de-head">
				<span class="de-title">
					<Search size={14} />
					데이터 탐색
				</span>
				<span class="de-sub">스크린 빌더 + prebuild raw 테이블 + SQL Notebook</span>
				<button type="button" class="de-close" onclick={onClose} aria-label="닫기 (Esc)">
					<X size={16} />
				</button>
			</header>

			<div class="de-body">
				<!-- 좌측 탭 list -->
				<aside class="de-tabs" aria-label="테이블 list">
					{#each TABLE_SOURCES as t (t.id)}
						{@const Icon = t.icon}
						<button
							type="button"
							class="de-tab"
							class:active={t.id === activeTabId}
							onclick={() => (activeTabId = t.id)}
							title={t.desc}
						>
							<span class="de-tab-icon">
								{#if Icon}<Icon size={14} />{/if}
							</span>
							<span class="de-tab-label">{t.label}</span>
							{#if t.source === 'parquet' && tabRows[t.id]}
								<span class="de-tab-count">{tabRows[t.id].length.toLocaleString('ko-KR')}</span>
							{:else if t.source === 'memory'}
								<span class="de-tab-count">
									{(memoryRows[t.id]?.length ?? 0).toLocaleString('ko-KR')}
								</span>
							{:else if t.source === 'parquet' && tabLoading[t.id]}
								<span class="de-tab-count loading">…</span>
							{/if}
						</button>
					{/each}
				</aside>

				<!-- 우측 테이블 -->
				<section class="de-main">
					{#if activeTab.source === 'screen'}
						<ScreenBuilder {nodes} onApply={onApplyScreen} />
					{:else if activeTab.source === 'notebook'}
						<SqlNotebook {db} {ecosystem} />
					{:else}
						<TableView
							title={activeTab.label}
							rows={getRowsForTab(activeTab)}
							onSearch={activeTab.source === 'parquet' ? (q) => handleSearch(activeTab, q) : undefined}
							searchValue={tabSearch[activeTab.id] ?? ''}
							loading={tabLoading[activeTab.id] ?? false}
							emptyHint={activeTab.source === 'parquet' && !db
								? 'db 가 아직 준비 안 됐습니다 (그리드 로드 후 다시 열기).'
								: '데이터 없음'}
							csvFilename={`scan_${activeTab.id}.csv`}
							onRowClick={(row) => (rowJsonRow = row)}
						/>
					{/if}
				</section>
			</div>
		</div>
	</div>
{/if}

<RowJsonModal row={rowJsonRow} onClose={() => (rowJsonRow = null)} />

<style>
	.de-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.65);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 24px;
	}
	.de-modal {
		width: min(1400px, 95vw);
		height: min(900px, 92vh);
		display: flex;
		flex-direction: column;
		background: #0a0e18;
		border: 1px solid #334155;
		border-radius: 8px;
		box-shadow: 0 32px 64px -12px rgba(0, 0, 0, 0.8);
		overflow: hidden;
	}
	.de-head {
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding: 12px 16px;
		background: #0f172a;
		border-bottom: 1px solid #1e2433;
	}
	.de-title {
		font-size: 14px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.de-sub {
		font-size: 11px;
		color: #64748b;
		flex: 1;
	}
	.de-close {
		background: transparent;
		border: none;
		color: #64748b;
		cursor: pointer;
		font-size: 16px;
		padding: 4px 8px;
	}
	.de-close:hover {
		color: var(--amber);
	}

	.de-body {
		flex: 1;
		min-height: 0;
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 0;
	}
	.de-tabs {
		border-right: 1px solid #1e2433;
		overflow-y: auto;
		padding: 8px 6px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		background: #050811;
	}
	.de-tab {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 10px;
		background: transparent;
		border: 1px solid transparent;
		border-radius: 4px;
		color: #cbd5e1;
		cursor: pointer;
		font-family: inherit;
		font-size: 12px;
		text-align: left;
	}
	.de-tab:hover {
		background: rgba(255, 255, 255, 0.03);
		border-color: #1e2433;
	}
	.de-tab.active {
		background: rgba(var(--amber-rgb), 0.1);
		border-color: rgba(var(--amber-rgb), 0.4);
		color: var(--amber);
		font-weight: 600;
	}
	.de-tab-icon {
		display: inline-flex;
		align-items: center;
		flex-shrink: 0;
		color: #94a3b8;
	}
	.de-tab.active .de-tab-icon {
		color: var(--amber);
	}
	.de-tab-label {
		flex: 1;
		font-family: monospace;
		font-size: 11px;
	}
	.de-tab-count {
		font-family: monospace;
		font-size: 9px;
		color: #64748b;
	}
	.de-tab-count.loading {
		color: #fbbf24;
		animation: pulse 1.4s ease-in-out infinite;
	}
	.de-tab.active .de-tab-count {
		color: var(--amber);
	}

	.de-main {
		min-width: 0;
		min-height: 0;
		padding: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	@keyframes pulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}

	@media (max-width: 768px) {
		.de-modal {
			width: 100vw;
			height: 100vh;
			border-radius: 0;
		}
		.de-body {
			grid-template-columns: 1fr;
		}
		.de-tabs {
			display: none;
		}
	}
</style>
