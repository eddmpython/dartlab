<script lang="ts">
	/**
	 * 단일 raw 테이블 view · 자체 native <table>.
	 *
	 *   - sticky header (수직 스크롤 시 헤더 고정)
	 *   - 가로/세로 스크롤
	 *   - 검색 (frontend ILIKE 또는 SQL re-query · 부모가 결정)
	 *   - 컬럼 헤더 클릭 = 정렬 (asc/desc 토글)
	 *   - 컬럼 hide / 복원 (드롭다운)
	 *   - CSV export
	 *   - row 클릭 = onRowClick(row)
	 */
	import { downloadCsv } from './csvExport';
	import { Search, Columns, Download, X, Eye } from 'lucide-svelte';

	interface SortState {
		key: string;
		dir: 'asc' | 'desc';
	}

	interface Props {
		title: string;
		rows: Array<Record<string, unknown>>;
		defaultColumns?: string[];
		onSearch?: (query: string) => void;
		searchValue?: string;
		loading?: boolean;
		emptyHint?: string;
		onRowClick?: (row: Record<string, unknown>) => void;
		csvFilename?: string;
	}

	let {
		title,
		rows,
		defaultColumns,
		onSearch,
		searchValue = $bindable(''),
		loading = false,
		emptyHint = '데이터 없음',
		onRowClick,
		csvFilename
	}: Props = $props();

	let allColumns = $derived.by<string[]>(() => {
		if (defaultColumns && defaultColumns.length > 0) return defaultColumns;
		if (rows.length === 0) return [];
		const seen = new Set<string>();
		const out: string[] = [];
		for (const r of rows.slice(0, 50)) {
			for (const k of Object.keys(r)) {
				if (!seen.has(k)) {
					seen.add(k);
					out.push(k);
				}
			}
		}
		return out;
	});

	let hiddenColumns = $state<Set<string>>(new Set());
	let visibleColumns = $derived(allColumns.filter((c) => !hiddenColumns.has(c)));
	let localSort = $state<SortState | null>(null);
	let columnsMenuOpen = $state(false);

	let filteredRows = $derived.by(() => {
		if (onSearch) return rows;
		const q = searchValue.trim().toLowerCase();
		if (!q) return rows;
		return rows.filter((r) => {
			for (const k of allColumns) {
				const v = r[k];
				if (v == null) continue;
				if (String(v).toLowerCase().includes(q)) return true;
			}
			return false;
		});
	});

	let sortedRows = $derived.by(() => {
		if (!localSort) return filteredRows;
		const key = localSort.key;
		const dir = localSort.dir === 'asc' ? 1 : -1;
		const arr = filteredRows.slice();
		arr.sort((a, b) => {
			const va = a[key];
			const vb = b[key];
			if (va == null && vb == null) return 0;
			if (va == null) return 1;
			if (vb == null) return -1;
			if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
			return String(va).localeCompare(String(vb), 'ko-KR') * dir;
		});
		return arr;
	});

	function handleSort(key: string) {
		if (localSort?.key === key) {
			localSort = { key, dir: localSort.dir === 'asc' ? 'desc' : 'asc' };
		} else {
			localSort = { key, dir: 'desc' };
		}
	}

	function handleSearchInput(e: Event) {
		const v = (e.target as HTMLInputElement).value;
		searchValue = v;
		onSearch?.(v);
	}

	function toggleColumnHidden(col: string) {
		const next = new Set(hiddenColumns);
		if (next.has(col)) next.delete(col);
		else next.add(col);
		hiddenColumns = next;
	}

	function showAllColumns() {
		hiddenColumns = new Set();
	}

	function handleCsv() {
		if (sortedRows.length === 0) return;
		const filename = csvFilename || `${title}.csv`;
		downloadCsv(filename, visibleColumns, sortedRows);
	}

	function fmtCell(v: unknown): string {
		if (v === null || v === undefined) return '·';
		if (Array.isArray(v)) return `[${v.length}]`;
		if (typeof v === 'object') return JSON.stringify(v).slice(0, 80);
		if (typeof v === 'number') {
			if (!Number.isFinite(v)) return '·';
			return v.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
		}
		const s = String(v);
		return s.length > 100 ? s.slice(0, 100) + '…' : s;
	}

	function isNumericColumn(col: string): boolean {
		for (const r of sortedRows.slice(0, 20)) {
			const v = r[col];
			if (typeof v === 'number') return true;
			if (v != null && typeof v !== 'number') return false;
		}
		return false;
	}
</script>

<div class="tv">
	<header class="tv-head">
		<div class="tv-title">
			<span class="tv-name">{title}</span>
			<span class="tv-count">
				{#if loading}로드 중…{:else}{sortedRows.length.toLocaleString('ko-KR')} row{/if}
				{#if hiddenColumns.size > 0}· {hiddenColumns.size} 숨김{/if}
			</span>
		</div>
		<div class="tv-actions">
			<div class="tv-search-wrap">
				<Search size={12} />
				<input
					type="text"
					class="tv-search"
					value={searchValue}
					oninput={handleSearchInput}
					placeholder={onSearch ? 'SQL 검색…' : '필터'}
					aria-label="검색"
				/>
			</div>
			<div class="tv-cols-wrap">
				<button
					type="button"
					class="tv-btn"
					onclick={() => (columnsMenuOpen = !columnsMenuOpen)}
					aria-haspopup="menu"
				>
					<Columns size={12} />
					<span>컬럼 {visibleColumns.length}/{allColumns.length}</span>
				</button>
				{#if columnsMenuOpen}
					<div class="tv-cols-menu" role="menu">
						<button type="button" class="tv-cols-all" onclick={showAllColumns}>
							<Eye size={12} /> 모두 보기
						</button>
						{#each allColumns as c (c)}
							<label class="tv-cols-item">
								<input
									type="checkbox"
									checked={!hiddenColumns.has(c)}
									onchange={() => toggleColumnHidden(c)}
								/>
								<span>{c}</span>
							</label>
						{/each}
					</div>
				{/if}
			</div>
			<button type="button" class="tv-btn" onclick={handleCsv} disabled={sortedRows.length === 0}>
				<Download size={12} />
				<span>CSV</span>
			</button>
		</div>
	</header>

	<div class="tv-body">
		{#if loading}
			<div class="tv-empty">로드 중…</div>
		{:else if sortedRows.length === 0}
			<div class="tv-empty">{emptyHint}</div>
		{:else}
			<table>
				<thead>
					<tr>
						{#each visibleColumns as col (col)}
							{@const sortDir = localSort?.key === col ? localSort.dir : null}
							{@const isNum = isNumericColumn(col)}
							<th class:numeric={isNum}>
								<button
									type="button"
									class="th-btn"
									onclick={() => handleSort(col)}
									title="정렬: {col}"
								>
									<span class="th-name">{col}</span>
									{#if sortDir === 'asc'}
										<span class="th-arr">▲</span>
									{:else if sortDir === 'desc'}
										<span class="th-arr">▼</span>
									{/if}
								</button>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each sortedRows.slice(0, 1000) as row, i (i)}
						<tr
							class:clickable={!!onRowClick}
							onclick={() => onRowClick?.(row)}
							onkeydown={(e) => {
								if (e.key === 'Enter') onRowClick?.(row);
							}}
							tabindex="0"
						>
							{#each visibleColumns as col (col)}
								{@const isNum = isNumericColumn(col)}
								<td class:numeric={isNum}>{fmtCell(row[col])}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			{#if sortedRows.length > 1000}
				<div class="tv-more">… 1000 row 표시 (전체 {sortedRows.length.toLocaleString()} row, CSV 는 전체)</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.tv {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		gap: 8px;
	}
	.tv-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
		flex-shrink: 0;
	}
	.tv-title {
		display: flex;
		align-items: baseline;
		gap: 10px;
		min-width: 0;
	}
	.tv-name {
		font-size: 13px;
		font-weight: 700;
		color: #f1f5f9;
		font-family: monospace;
	}
	.tv-count {
		font-size: 11px;
		color: #64748b;
		font-family: monospace;
	}
	.tv-actions {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.tv-search-wrap {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 10px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 4px;
		color: #64748b;
	}
	.tv-search-wrap:focus-within {
		border-color: var(--amber);
	}
	.tv-search {
		width: 160px;
		background: transparent;
		border: none;
		color: #f1f5f9;
		font-size: 11px;
		font-family: inherit;
		outline: none;
	}
	.tv-btn {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 10px;
		font-size: 11px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 4px;
		color: #cbd5e1;
		cursor: pointer;
		font-family: inherit;
	}
	.tv-btn:hover:not(:disabled) {
		border-color: var(--amber);
		color: var(--amber);
	}
	.tv-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
	.tv-cols-wrap {
		position: relative;
	}
	.tv-cols-menu {
		position: absolute;
		top: calc(100% + 4px);
		right: 0;
		min-width: 220px;
		max-height: 320px;
		overflow-y: auto;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 5px;
		box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.7);
		z-index: 50;
		padding: 4px;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.tv-cols-all {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 5px 8px;
		font-size: 10px;
		background: rgba(var(--amber-rgb), 0.08);
		border: 1px solid rgba(var(--amber-rgb), 0.3);
		border-radius: 3px;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
		margin-bottom: 4px;
	}
	.tv-cols-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		font-size: 11px;
		color: #cbd5e1;
		cursor: pointer;
		border-radius: 3px;
	}
	.tv-cols-item:hover {
		background: rgba(255, 255, 255, 0.04);
	}
	.tv-cols-item input {
		accent-color: var(--amber);
	}

	.tv-body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		overflow: auto;
	}
	.tv-empty {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #475569;
		font-size: 12px;
	}
	.tv-more {
		padding: 8px 12px;
		font-size: 10px;
		color: #64748b;
		text-align: center;
		font-family: monospace;
		border-top: 1px solid #1e2433;
		flex-shrink: 0;
	}

	table {
		border-collapse: collapse;
		font-size: 11px;
		font-variant-numeric: tabular-nums;
		min-width: 100%;
		width: max-content;
	}
	thead th {
		position: sticky;
		top: 0;
		background: #0a0e18;
		color: #cbd5e1;
		text-align: left;
		padding: 0;
		border-bottom: 1px solid #1e2433;
		font-size: 10px;
		font-weight: 600;
		z-index: 5;
		min-width: 100px;
	}
	thead th.numeric {
		text-align: right;
	}
	.th-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		width: 100%;
		padding: 7px 10px;
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
		font-family: monospace;
		font-size: 10px;
		font-weight: 600;
		text-align: inherit;
	}
	thead th.numeric .th-btn {
		justify-content: flex-end;
	}
	.th-btn:hover .th-name {
		color: var(--amber);
	}
	.th-arr {
		font-size: 9px;
		color: var(--amber);
	}

	tbody td {
		padding: 5px 10px;
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
		color: #cbd5e1;
		white-space: nowrap;
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
		font-family: 'JetBrains Mono', monospace;
	}
	tbody td.numeric {
		text-align: right;
	}
	tbody tr.clickable {
		cursor: pointer;
	}
	tbody tr:hover td {
		background: rgba(255, 255, 255, 0.02);
	}
	tbody tr:focus-visible {
		outline: 1px solid var(--amber);
		outline-offset: -1px;
	}
</style>
