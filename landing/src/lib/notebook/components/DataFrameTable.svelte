<script lang="ts">
	import { ChevronUp, ChevronDown, ChevronsLeft, ChevronsRight, ChevronLeft, ChevronRight, Search } from 'lucide-svelte';

	interface ColumnInfo {
		name: string;
		dtype: string;
	}

	interface DataFrameData {
		type: 'dataframe' | 'series';
		totalRows: number;
		totalCols: number;
		columns: ColumnInfo[];
		index: string[];
		data: unknown[][];
	}

	interface Props {
		data: DataFrameData;
		stdout?: string;
	}

	let { data, stdout }: Props = $props();

	let sortCol = $state<number | null>(null);
	let sortAsc = $state(true);
	let page = $state(0);
	let pageSize = $state(25);
	let searchQuery = $state('');
	let showSearch = $state(false);

	const filteredRows = $derived.by(() => {
		let rows = data.data.map((row, i) => ({ idx: data.index[i], values: row }));
		if (searchQuery.trim()) {
			const q = searchQuery.toLowerCase();
			rows = rows.filter(
				(r) => r.idx.toLowerCase().includes(q) || r.values.some((v) => String(v ?? '').toLowerCase().includes(q))
			);
		}
		return rows;
	});

	const sortedRows = $derived.by(() => {
		if (sortCol === null) return filteredRows;
		const col = sortCol;
		const asc = sortAsc;
		return [...filteredRows].sort((a, b) => {
			const va = a.values[col];
			const vb = b.values[col];
			if (va === null || va === undefined) return 1;
			if (vb === null || vb === undefined) return -1;
			if (typeof va === 'number' && typeof vb === 'number') {
				return asc ? va - vb : vb - va;
			}
			const sa = String(va);
			const sb = String(vb);
			return asc ? sa.localeCompare(sb) : sb.localeCompare(sa);
		});
	});

	const totalFiltered = $derived(sortedRows.length);
	const totalPages = $derived(Math.max(1, Math.ceil(totalFiltered / pageSize)));
	const pagedRows = $derived(sortedRows.slice(page * pageSize, (page + 1) * pageSize));

	function handleSort(colIdx: number) {
		if (sortCol === colIdx) {
			sortAsc = !sortAsc;
		} else {
			sortCol = colIdx;
			sortAsc = true;
		}
		page = 0;
	}

	function formatCell(value: unknown): string {
		if (value === null || value === undefined) return '';
		if (typeof value === 'number') {
			if (Number.isInteger(value)) return value.toLocaleString();
			return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
		}
		return String(value);
	}

	function isNumeric(dtype: string): boolean {
		return /int|float|double|decimal|num/i.test(dtype);
	}

	function dtypeLabel(dtype: string): string {
		if (/int64/i.test(dtype)) return 'i64';
		if (/int32/i.test(dtype)) return 'i32';
		if (/float64/i.test(dtype)) return 'f64';
		if (/float32/i.test(dtype)) return 'f32';
		if (/bool/i.test(dtype)) return 'bool';
		if (/object/i.test(dtype)) return 'str';
		if (/datetime/i.test(dtype)) return 'dt';
		if (/category/i.test(dtype)) return 'cat';
		return dtype.slice(0, 4);
	}
</script>

<div class="df-wrapper">
	{#if stdout}
		<pre class="df-stdout">{stdout}</pre>
	{/if}

	<div class="df-header">
		<span class="df-shape">
			{data.totalRows.toLocaleString()} rows
			{#if data.type === 'dataframe'}
				&times; {data.totalCols} cols
			{:else}
				(Series)
			{/if}
			{#if data.totalRows > data.data.length}
				<span class="df-truncated">showing {data.data.length.toLocaleString()}</span>
			{/if}
		</span>
		<div class="df-controls">
			<button
				class="df-ctrl-btn"
				class:active={showSearch}
				onclick={() => { showSearch = !showSearch; if (!showSearch) { searchQuery = ''; page = 0; } }}
				title="Search"
				aria-label="Toggle search"
			>
				<Search size={12} />
			</button>
			<select class="df-page-select" bind:value={pageSize} onchange={() => { page = 0; }}>
				<option value={10}>10</option>
				<option value={25}>25</option>
				<option value={50}>50</option>
				<option value={100}>100</option>
			</select>
		</div>
	</div>

	{#if showSearch}
		<div class="df-search-bar">
			<Search size={11} />
			<input
				class="df-search-input"
				bind:value={searchQuery}
				oninput={() => { page = 0; }}
				placeholder="Search all columns..."
			/>
		</div>
	{/if}

	<div class="df-table-scroll">
		<table class="df-table">
			<thead>
				<tr>
					<th class="df-idx-col">&nbsp;</th>
					{#each data.columns as col, i}
						<th
							class="df-col-header"
							class:numeric={isNumeric(col.dtype)}
							class:sorted={sortCol === i}
							onclick={() => handleSort(i)}
						>
							<span class="df-col-name">{col.name}</span>
							<span class="df-col-dtype">{dtypeLabel(col.dtype)}</span>
							{#if sortCol === i}
								<span class="df-sort-icon">
									{#if sortAsc}
										<ChevronUp size={10} />
									{:else}
										<ChevronDown size={10} />
									{/if}
								</span>
							{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each pagedRows as row}
					<tr>
						<td class="df-idx-cell">{row.idx}</td>
						{#each row.values as val, ci}
							<td class:numeric={isNumeric(data.columns[ci].dtype)} class:null-val={val === null || val === undefined}>
								{formatCell(val)}
							</td>
						{/each}
					</tr>
				{/each}
				{#if pagedRows.length === 0}
					<tr>
						<td class="df-empty" colspan={data.columns.length + 1}>
							{searchQuery ? 'No matching rows' : 'Empty DataFrame'}
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>

	{#if totalPages > 1}
		<div class="df-pagination">
			<span class="df-page-info">
				{(page * pageSize + 1).toLocaleString()}-{Math.min((page + 1) * pageSize, totalFiltered).toLocaleString()} of {totalFiltered.toLocaleString()}
			</span>
			<div class="df-page-btns">
				<button class="df-page-btn" disabled={page === 0} onclick={() => { page = 0; }} aria-label="First page">
					<ChevronsLeft size={12} />
				</button>
				<button class="df-page-btn" disabled={page === 0} onclick={() => { page--; }} aria-label="Previous page">
					<ChevronLeft size={12} />
				</button>
				<span class="df-page-num">{page + 1} / {totalPages}</span>
				<button class="df-page-btn" disabled={page >= totalPages - 1} onclick={() => { page++; }} aria-label="Next page">
					<ChevronRight size={12} />
				</button>
				<button class="df-page-btn" disabled={page >= totalPages - 1} onclick={() => { page = totalPages - 1; }} aria-label="Last page">
					<ChevronsRight size={12} />
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.df-wrapper {
		width: 100%;
	}

	.df-stdout {
		margin: 0 0 6px;
		font-family: 'Fira Code', monospace;
		font-size: 13px;
		line-height: 1.5;
		color: var(--nb-text);
		white-space: pre-wrap;
		word-break: break-word;
	}

	.df-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 4px 0 6px;
	}

	.df-shape {
		font-family: 'Fira Code', monospace;
		font-size: 11px;
		color: var(--nb-text-muted);
	}

	.df-truncated {
		color: var(--nb-pink);
		margin-left: 6px;
		font-size: 10px;
	}

	.df-controls {
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.df-ctrl-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.df-ctrl-btn:hover, .df-ctrl-btn.active {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.df-page-select {
		font-family: 'Fira Code', monospace;
		font-size: 10px;
		padding: 2px 4px;
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		background: var(--nb-card);
		color: var(--nb-text);
		cursor: pointer;
		outline: none;
	}

	.df-search-bar {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		margin-bottom: 4px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-surface);
		color: var(--nb-text-muted);
	}

	.df-search-input {
		flex: 1;
		border: none;
		background: transparent;
		color: var(--nb-text);
		font-family: 'Fira Code', monospace;
		font-size: 11px;
		outline: none;
	}

	.df-search-input::placeholder {
		color: var(--nb-text-muted);
	}

	.df-table-scroll {
		overflow-x: auto;
		max-height: 400px;
		overflow-y: auto;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
	}

	.df-table-scroll::-webkit-scrollbar {
		width: 5px;
		height: 5px;
	}

	.df-table-scroll::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 3px;
	}

	.df-table {
		width: 100%;
		border-collapse: collapse;
		font-family: 'Fira Code', monospace;
		font-size: 12px;
	}

	.df-table thead {
		position: sticky;
		top: 0;
		z-index: 2;
	}

	.df-col-header {
		background: var(--nb-surface);
		padding: 6px 10px;
		text-align: left;
		border-bottom: 2px solid var(--nb-border);
		white-space: nowrap;
		cursor: pointer;
		user-select: none;
		transition: background 0.1s ease;
	}

	.df-col-header:hover {
		background: var(--nb-pink-subtle);
	}

	.df-col-header.sorted {
		background: var(--nb-pink-subtle);
	}

	.df-col-header.numeric {
		text-align: right;
	}

	.df-col-name {
		color: var(--nb-text);
		font-weight: 600;
		font-size: 11px;
	}

	.df-col-dtype {
		color: var(--nb-text-muted);
		font-size: 9px;
		font-weight: 400;
		margin-left: 4px;
		opacity: 0.7;
	}

	.df-sort-icon {
		display: inline-flex;
		color: var(--nb-pink);
		margin-left: 2px;
		vertical-align: middle;
	}

	.df-idx-col {
		background: var(--nb-surface);
		padding: 6px 8px;
		border-bottom: 2px solid var(--nb-border);
		width: 1px;
		white-space: nowrap;
		position: sticky;
		left: 0;
		z-index: 3;
	}

	.df-idx-cell {
		background: var(--nb-surface);
		color: var(--nb-text-muted);
		font-size: 10px;
		font-weight: 500;
		text-align: right;
		padding: 3px 8px;
		border-right: 1px solid var(--nb-border);
		border-bottom: 1px solid var(--nb-border);
		white-space: nowrap;
		position: sticky;
		left: 0;
		z-index: 1;
	}

	.df-table tbody td {
		padding: 3px 10px;
		border-bottom: 1px solid var(--nb-border);
		color: var(--nb-text);
		white-space: nowrap;
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.df-table tbody td.numeric {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	.df-table tbody td.null-val {
		color: var(--nb-text-muted);
		font-style: italic;
		opacity: 0.5;
	}

	.df-table tbody tr:hover td,
	.df-table tbody tr:hover .df-idx-cell {
		background: var(--nb-pink-subtle);
	}

	.df-table tbody tr:nth-child(even) td {
		background: rgba(255, 255, 255, 0.015);
	}

	.df-table tbody tr:nth-child(even):hover td {
		background: var(--nb-pink-subtle);
	}

	.df-table tbody tr:nth-child(even) .df-idx-cell {
		background: var(--nb-surface);
	}

	.df-table tbody tr:nth-child(even):hover .df-idx-cell {
		background: var(--nb-pink-subtle);
	}

	.df-empty {
		text-align: center;
		color: var(--nb-text-muted);
		padding: 20px;
		font-size: 12px;
	}

	.df-pagination {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 6px 0 2px;
	}

	.df-page-info {
		font-family: 'Fira Code', monospace;
		font-size: 10px;
		color: var(--nb-text-muted);
	}

	.df-page-btns {
		display: flex;
		align-items: center;
		gap: 2px;
	}

	.df-page-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.df-page-btn:hover:not(:disabled) {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.df-page-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.df-page-num {
		font-family: 'Fira Code', monospace;
		font-size: 10px;
		color: var(--nb-text-muted);
		padding: 0 6px;
		min-width: 50px;
		text-align: center;
	}
</style>
