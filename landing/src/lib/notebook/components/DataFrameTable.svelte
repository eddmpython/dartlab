<script lang="ts">
	import {
		ArrowUp,
		ArrowDown,
		ChevronsUpDown,
		ChevronsLeft,
		ChevronsRight,
		ChevronLeft,
		ChevronRight,
		Search,
		Hash,
		Type as TypeIcon,
		Calendar,
		ToggleLeft,
		Braces
	} from 'lucide-svelte';

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
	let pageSize = $state(10);
	let searchQuery = $state('');
	let showSearch = $state(false);

	const filteredRows = $derived.by(() => {
		let rows = data.data.map((row, i) => ({ idx: data.index[i], values: row }));
		if (searchQuery.trim()) {
			const q = searchQuery.toLowerCase();
			rows = rows.filter(
				(r) =>
					r.idx.toLowerCase().includes(q) ||
					r.values.some((v) => String(v ?? '').toLowerCase().includes(q))
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
			if (typeof va === 'number' && typeof vb === 'number') return asc ? va - vb : vb - va;
			return asc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
		});
	});

	const totalFiltered = $derived(sortedRows.length);
	const totalPages = $derived(Math.max(1, Math.ceil(totalFiltered / pageSize)));
	const pagedRows = $derived(sortedRows.slice(page * pageSize, (page + 1) * pageSize));

	function handleSort(colIdx: number) {
		if (sortCol === colIdx) sortAsc = !sortAsc;
		else {
			sortCol = colIdx;
			sortAsc = true;
		}
		page = 0;
	}

	function formatCell(value: unknown): string {
		if (value === null || value === undefined) return 'null';
		if (typeof value === 'number') {
			if (Number.isInteger(value)) return value.toLocaleString('en-US');
			return value.toLocaleString('en-US', { maximumFractionDigits: 6 });
		}
		return String(value);
	}

	type Kind = 'number' | 'string' | 'date' | 'bool' | 'unknown';
	function dtypeKind(dtype: string): Kind {
		if (/int|float|double|decimal|num|i8|i16|i32|i64|u8|u16|u32|u64|f32|f64/i.test(dtype))
			return 'number';
		if (/bool/i.test(dtype)) return 'bool';
		if (/datetime|timestamp|date|time/i.test(dtype)) return 'date';
		if (/object|str|utf|categor/i.test(dtype)) return 'string';
		return 'unknown';
	}
	function dtypeShort(dtype: string): string {
		if (/int64|i64/i.test(dtype)) return 'i64';
		if (/int32|i32/i.test(dtype)) return 'i32';
		if (/int/i.test(dtype)) return 'int';
		if (/float64|f64/i.test(dtype)) return 'f64';
		if (/float32|f32/i.test(dtype)) return 'f32';
		if (/float/i.test(dtype)) return 'float';
		if (/bool/i.test(dtype)) return 'bool';
		if (/datetime|timestamp/i.test(dtype)) return 'datetime';
		if (/date/i.test(dtype)) return 'date';
		if (/object|str|utf/i.test(dtype)) return 'str';
		if (/categor/i.test(dtype)) return 'cat';
		return dtype.slice(0, 6);
	}
</script>

<div class="df-wrapper">
	{#if stdout}
		<pre class="df-stdout">{stdout}</pre>
	{/if}

	<div class="df-header">
		<span class="df-shape">
			{data.totalRows.toLocaleString('en-US')} rows
			{#if data.type === 'dataframe'}&times; {data.totalCols} cols{:else}(Series){/if}
			{#if data.totalRows > data.data.length}
				<span class="df-truncated">· showing {data.data.length.toLocaleString('en-US')}</span>
			{/if}
		</span>
		<div class="df-controls">
			<button
				class="df-ctrl-btn"
				class:active={showSearch}
				onclick={() => {
					showSearch = !showSearch;
					if (!showSearch) {
						searchQuery = '';
						page = 0;
					}
				}}
				title="검색"
				aria-label="검색 토글"><Search size={13} /></button
			>
			<select class="df-page-select" bind:value={pageSize} onchange={() => (page = 0)}>
				<option value={5}>5</option>
				<option value={10}>10</option>
				<option value={25}>25</option>
				<option value={50}>50</option>
				<option value={100}>100</option>
			</select>
		</div>
	</div>

	{#if showSearch}
		<div class="df-search-bar">
			<Search size={12} />
			<input
				class="df-search-input"
				bind:value={searchQuery}
				oninput={() => (page = 0)}
				placeholder="모든 열 검색..."
			/>
		</div>
	{/if}

	<div class="df-scroll">
		<table class="df-table">
			<thead>
				<tr>
					<th class="df-th df-idx-th">&nbsp;</th>
					{#each data.columns as col, i (col.name + i)}
						{@const kind = dtypeKind(col.dtype)}
						<th
							class="df-th"
							class:numeric={kind === 'number'}
							class:sorted={sortCol === i}
							onclick={() => handleSort(i)}
						>
							<div class="df-th-inner">
								<div class="df-th-top">
									<span class="df-th-name">{col.name}</span>
									<span class="df-th-sort" class:on={sortCol === i}>
										{#if sortCol === i}
											{#if sortAsc}<ArrowUp size={12} />{:else}<ArrowDown size={12} />{/if}
										{:else}<ChevronsUpDown size={12} />{/if}
									</span>
								</div>
								<div class="df-th-type">
									{#if kind === 'number'}<Hash size={10} />{:else if kind === 'string'}<TypeIcon
											size={10}
										/>{:else if kind === 'date'}<Calendar size={10} />{:else if kind === 'bool'}<ToggleLeft
											size={10}
										/>{:else}<Braces size={10} />{/if}
									<span>{dtypeShort(col.dtype)}</span>
								</div>
							</div>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each pagedRows as row (row.idx)}
					<tr>
						<td class="df-td df-idx-td">{row.idx}</td>
						{#each row.values as val, ci (ci)}
							{@const kind = dtypeKind(data.columns[ci].dtype)}
							<td
								class="df-td"
								class:numeric={kind === 'number'}
								class:nullv={val === null || val === undefined}
								title={typeof val === 'string' && val.length > 40 ? val : undefined}
							>
								{formatCell(val)}
							</td>
						{/each}
					</tr>
				{/each}
				{#if pagedRows.length === 0}
					<tr>
						<td class="df-empty" colspan={data.columns.length + 1}>
							{searchQuery ? '일치하는 행 없음' : '빈 DataFrame'}
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>

	{#if totalPages > 1}
		<div class="df-pagination">
			<span class="df-page-info">
				{(page * pageSize + 1).toLocaleString('en-US')}-{Math.min(
					(page + 1) * pageSize,
					totalFiltered
				).toLocaleString('en-US')} of {totalFiltered.toLocaleString('en-US')}
			</span>
			<div class="df-page-btns">
				<button class="df-page-btn" disabled={page === 0} onclick={() => (page = 0)} aria-label="첫 페이지"
					><ChevronsLeft size={13} /></button
				>
				<button class="df-page-btn" disabled={page === 0} onclick={() => page--} aria-label="이전"
					><ChevronLeft size={13} /></button
				>
				<span class="df-page-num">Page {page + 1} of {totalPages}</span>
				<button
					class="df-page-btn"
					disabled={page >= totalPages - 1}
					onclick={() => page++}
					aria-label="다음"><ChevronRight size={13} /></button
				>
				<button
					class="df-page-btn"
					disabled={page >= totalPages - 1}
					onclick={() => (page = totalPages - 1)}
					aria-label="마지막 페이지"><ChevronsRight size={13} /></button
				>
			</div>
		</div>
	{/if}
</div>

<style>
	/* marimo 인터랙티브 테이블 재현: sans + tabular-nums, 2줄 헤더(이름+타입아이콘),
	   연한 세로 컬럼선, zebra 없음, hover 정렬 화살표. 색은 dartlab --dl-* 토큰. */
	.df-wrapper {
		width: fit-content;
		max-width: 100%;
	}

	.df-stdout {
		margin: 0 0 6px;
		font-family: var(--dl-font-mono);
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
		gap: 12px;
		padding: 2px 2px 6px;
	}
	.df-shape {
		font-family: var(--dl-font-ui);
		font-size: 11px;
		color: var(--nb-text-muted);
	}
	.df-truncated {
		color: var(--nb-pink);
		margin-left: 2px;
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
		width: 24px;
		height: 22px;
		border: 1px solid var(--nb-border);
		border-radius: var(--dl-r-sm);
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.12s ease;
	}
	.df-ctrl-btn:hover,
	.df-ctrl-btn.active {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}
	.df-page-select {
		font-family: var(--dl-font-ui);
		font-size: 11px;
		height: 22px;
		padding: 0 4px;
		border: 1px solid var(--nb-border);
		border-radius: var(--dl-r-sm);
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
		border-radius: var(--dl-r-sm);
		background: var(--nb-surface);
		color: var(--nb-text-muted);
	}
	.df-search-input {
		flex: 1;
		border: none;
		background: transparent;
		color: var(--nb-text);
		font-family: var(--dl-font-ui);
		font-size: 12px;
		outline: none;
	}
	.df-search-input::placeholder {
		color: var(--nb-text-muted);
	}

	.df-scroll {
		overflow: auto;
		max-height: 440px;
		border: 1px solid var(--nb-border);
		border-radius: var(--dl-r-md);
		width: fit-content;
		max-width: 100%;
	}
	.df-scroll::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	.df-scroll::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 4px;
	}

	.df-table {
		width: auto;
		border-collapse: separate;
		border-spacing: 0;
		font-family: var(--dl-font-ui);
		font-size: 13px;
		color: var(--nb-text);
	}

	/* ── 헤더 ── */
	.df-table thead {
		position: sticky;
		top: 0;
		z-index: 2;
	}
	.df-th {
		height: 40px;
		padding: 0 12px;
		text-align: left;
		vertical-align: middle;
		background: var(--nb-surface);
		border-bottom: 1px solid var(--nb-border);
		border-right: 1px solid var(--dl-line);
		white-space: nowrap;
		cursor: pointer;
		user-select: none;
		transition: background 0.1s ease;
	}
	.df-th:hover {
		background: var(--nb-card);
	}
	.df-th.numeric .df-th-inner {
		align-items: flex-end;
	}
	.df-th-inner {
		display: flex;
		flex-direction: column;
		gap: 1px;
		justify-content: center;
	}
	.df-th-top {
		display: flex;
		align-items: center;
		gap: 5px;
	}
	.df-th-name {
		font-weight: 600;
		font-size: 12.5px;
		color: var(--nb-text);
	}
	.df-th-sort {
		display: inline-flex;
		color: var(--nb-text-muted);
		opacity: 0;
		transition: opacity 0.12s ease;
	}
	.df-th:hover .df-th-sort {
		opacity: 0.7;
	}
	.df-th-sort.on {
		opacity: 1;
		color: var(--nb-pink);
	}
	.df-th-type {
		display: flex;
		align-items: center;
		gap: 3px;
		color: var(--nb-text-muted);
		font-size: 9.5px;
		font-weight: 500;
		opacity: 0.8;
	}

	/* ── 셀 ── */
	.df-td {
		height: 30px;
		padding: 0 12px;
		border-bottom: 1px solid var(--nb-border);
		border-right: 1px solid var(--dl-line);
		color: var(--nb-text);
		white-space: nowrap;
		max-width: 320px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.df-td.numeric {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.df-td.nullv {
		color: var(--nb-text-muted);
		font-style: italic;
		opacity: 0.6;
	}
	.df-table tbody tr:last-child .df-td {
		border-bottom: none;
	}
	.df-table tbody tr:hover .df-td {
		background: var(--nb-surface);
	}

	/* ── 인덱스 열 ── */
	.df-idx-th,
	.df-idx-td {
		position: sticky;
		left: 0;
		z-index: 1;
		width: 1px;
		text-align: right;
		background: var(--nb-surface);
		color: var(--nb-text-muted);
		font-size: 11px;
		font-variant-numeric: tabular-nums;
	}
	.df-idx-th {
		z-index: 3;
		cursor: default;
	}
	.df-table tbody tr:hover .df-idx-td {
		background: var(--nb-card);
	}

	.df-empty {
		text-align: center;
		color: var(--nb-text-muted);
		padding: 24px;
		font-size: 12px;
		font-family: var(--dl-font-ui);
	}

	.df-pagination {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 8px 2px 2px;
	}
	.df-page-info {
		font-family: var(--dl-font-ui);
		font-size: 11px;
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
		width: 24px;
		height: 24px;
		border: 1px solid var(--nb-border);
		border-radius: var(--dl-r-sm);
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.12s ease;
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
		font-family: var(--dl-font-ui);
		font-size: 11px;
		color: var(--nb-text-muted);
		padding: 0 8px;
		white-space: nowrap;
	}
</style>
