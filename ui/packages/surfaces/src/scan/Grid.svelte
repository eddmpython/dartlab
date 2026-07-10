<script lang="ts">
	/**
	 * Scan Studio 메인 그리드 · 가상 스크롤.
	 *
	 * 2,664 row × N 컬럼을 한 화면에. 자체 구현 가상 스크롤 (~120 LOC core)
	 * · 단축 axis 수직, 고정 row height, sticky 회사명 컬럼.
	 *
	 * 책임:
	 *  - 헤더 클릭 = 정렬 토글 (1차 정렬)
	 *  - 헤더 hover = HeaderTooltip (메트릭 정의)
	 *  - 행 click = onSelect (Detail 패널 · PR-D)
	 *  - 회사명 click = 행 선택
	 *  - 행 색 = qualGrade 톤 (subtle 6%)
	 *  - 등급 셀 = 색칩
	 *  - placeholder = `·`
	 */
	import HeaderTooltip from './HeaderTooltip.svelte';
	import HeaderFilterPopover from './HeaderFilterPopover.svelte';
	import Sparkline from './Sparkline.svelte';
	import { METRICS_BY_KEY, PINNED_COLUMNS } from './metrics';
	import type { FilterCond, ScanNode, SeriesMetric, SortKey } from './types';
	import { gradeTone, rowTintColor, toneColor } from './grade';
	import { marketColor, marketLabel, normalizeMarket } from './marketChip';

	interface CellHoverInfo {
		stockCode: string;
		label: string;
		metricKey: string;
		formattedValue: string;
		spark: number[];
		x: number;
		y: number;
	}

	interface Percentile {
		p10: number;
		p90: number;
		higherBetter?: boolean;
	}

	interface Props {
		nodes: ScanNode[] | Record<string, unknown>[];
		columns: string[];
		sorts?: SortKey[];
		filters?: FilterCond[];
		filterOptions?: Record<string, string[]>;
		percentiles?: Map<string, Percentile>;
		selectedId: string | null;
		/** 'screener' = 메인 그리드 (heatmap·hover·등급칩 활성)
		 *  'table'   = 단순 raw 테이블 (모달 내 · 모두 비활성, 동적 컬럼 width) */
		mode?: 'screener' | 'table';
		/** stockCode → 'KOSPI'/'KOSDAQ'/'KONEX' 같은 market 라벨. 노드 자체 market 없을 때 fallback. */
		markets?: Record<string, string>;
		/** 근접후보 종목 id. 통과 종목과 시각 격리(좌측 amber 마커)해 "통과했다" 오독을 막는다. */
		nearMissIds?: Set<string>;
		onSort: (s: SortKey, append: boolean) => void;
		onFilterChange?: (metric: string, conds: FilterCond[]) => void;
		onSelect: (id: string) => void;
		onCellHover?: (info: CellHoverInfo | null) => void;
	}

	let {
		nodes,
		columns,
		sorts = [],
		filters = [],
		filterOptions,
		percentiles,
		selectedId,
		mode = 'screener',
		markets,
		nearMissIds,
		onSort,
		onFilterChange,
		onSelect,
		onCellHover
	}: Props = $props();

	function rowMarket(rd: Record<string, unknown>, id: string): unknown {
		const m = (rd as any).market;
		if (m) return m;
		if (markets && id) return markets[id];
		return undefined;
	}
	let isTable = $derived(mode === 'table');

	/** 셀 분위 배경색 · p10 이하 / p90 이상 강조 (subtle 12%). */
	function cellHeatmapBg(key: string, v: unknown): string {
		if (typeof v !== 'number' || !Number.isFinite(v)) return 'transparent';
		const p = percentiles?.get(key);
		if (!p || p.p90 <= p.p10) return 'transparent';
		const ratio = Math.max(0, Math.min(1, (v - p.p10) / (p.p90 - p.p10)));
		const inverted = p.higherBetter === false;
		// 0~1 ratio. higherBetter true: 1 = good 녹, 0 = bad 적. inverted 면 반전.
		let color = '';
		let strength = 0;
		if (ratio >= 0.7) {
			strength = (ratio - 0.7) / 0.3;
			color = inverted ? '#ef4444' : '#22c55e';
		} else if (ratio <= 0.3) {
			strength = (0.3 - ratio) / 0.3;
			color = inverted ? '#22c55e' : '#ef4444';
		}
		if (strength === 0) return 'transparent';
		const pct = Math.round(strength * 14);
		return `color-mix(in srgb, ${color} ${pct}%, transparent)`;
	}

	const ROW_H = 36;
	const OVERSCAN = 6;

	let viewport: HTMLDivElement | undefined = $state(undefined);
	let viewportH = $state(800);
	let scrollTop = $state(0);

	$effect(() => {
		if (!viewport) return;
		const ro = new ResizeObserver((entries) => {
			for (const e of entries) {
				viewportH = e.contentRect.height;
			}
		});
		ro.observe(viewport);
		viewportH = viewport.clientHeight;
		return () => ro.disconnect();
	});

	let totalRows = $derived(nodes.length);
	let visibleCount = $derived(Math.ceil(viewportH / ROW_H) + OVERSCAN * 2);
	let startIdx = $derived(Math.max(0, Math.floor(scrollTop / ROW_H) - OVERSCAN));
	let endIdx = $derived(Math.min(totalRows, startIdx + visibleCount));
	let visibleRows = $derived(nodes.slice(startIdx, endIdx));
	let topPad = $derived(startIdx * ROW_H);
	let bottomPad = $derived((totalRows - endIdx) * ROW_H);

	function handleScroll(e: Event) {
		const el = e.target as HTMLDivElement;
		scrollTop = el.scrollTop;
	}

	function sortEntry(key: string): SortKey | null {
		return sorts.find((s) => s.key === key) ?? null;
	}

	function sortIndex(key: string): number {
		return sorts.findIndex((s) => s.key === key);
	}

	function filtersForMetric(key: string): FilterCond[] {
		return filters.filter((c) => c.metric === key);
	}

	function handleSortClick(e: MouseEvent, key: string) {
		const cur = sortEntry(key);
		if (cur) {
			onSort({ key, dir: cur.dir === 'asc' ? 'desc' : 'asc' }, e.shiftKey);
		} else {
			const def = METRICS_BY_KEY[key];
			onSort({ key, dir: def?.higherBetter === false ? 'asc' : 'desc' }, e.shiftKey);
		}
	}

	type RowData = Record<string, unknown>;

	function cellValue(node: RowData, key: string): unknown {
		return node[key];
	}

	function rowId(node: RowData, idx: number): string {
		const id = node['id'];
		return typeof id === 'string' ? id : String(idx);
	}

	function rowLabel(node: RowData): string {
		const lbl = node['label'];
		return typeof lbl === 'string' ? lbl : '';
	}

	function rowColor(node: RowData): string {
		const c = node['color'];
		return typeof c === 'string' ? c : '#475569';
	}

	function rowQualGrade(node: RowData): unknown {
		return node['qualGrade'];
	}

	function isPinned(key: string): boolean {
		return PINNED_COLUMNS.includes(key);
	}

	function colWidth(key: string): number {
		const def = METRICS_BY_KEY[key];
		if (key === 'label') return 168;
		if (key === 'id') return 86;
		if (key === 'market') return 82;
		if (key === 'industryName') return 124;
		if (key === 'product') return 220;
		if (key === 'currentPrice') return 120;
		if (key === 'marketCap') return 124;
		if (key === 'spark' || key === 'spark30' || key === 'spark60') return 110;
		if (def?.type === 'series') return 132;
		if (!def) return 110;
		if (def.type === 'enum' || def.type === 'text') return 110;
		return 110;
	}

	function colWidthCss(): string {
		return columns.map((k) => `${colWidth(k)}px`).join(' ');
	}

	let stickyOffsets = $derived.by(() => {
		const offsets: Record<string, number> = {};
		let acc = 0;
		for (const k of columns) {
			if (isPinned(k)) {
				offsets[k] = acc;
				acc += colWidth(k);
			}
		}
		return offsets;
	});

	// ── Cell hover dwell ──────────────────────────────
	let hoverTimer: ReturnType<typeof setTimeout> | null = null;
	function onCellMouseEnter(e: MouseEvent, node: RowData, key: string, formatted: string) {
		if (!onCellHover) return;
		if (isPinned(key)) return;
		if (hoverTimer) clearTimeout(hoverTimer);
		const target = e.currentTarget as HTMLElement;
		const rect = target.getBoundingClientRect();
		hoverTimer = setTimeout(() => {
			onCellHover?.({
				stockCode: rowId(node, 0),
				label: rowLabel(node),
				metricKey: key,
				formattedValue: formatted,
				spark: sparkForCell(node, key),
				x: Math.min(window.innerWidth - 260, rect.left + rect.width / 2 - 100),
				y: rect.top - 180
			});
		}, 200);
	}
	function onCellMouseLeave() {
		if (hoverTimer) clearTimeout(hoverTimer);
		hoverTimer = null;
		onCellHover?.(null);
	}

	function numberArray(value: unknown): number[] {
		return Array.isArray(value)
			? value.map((v) => Number(v)).filter((v) => Number.isFinite(v))
			: [];
	}

	function sparkForCell(node: RowData, key: string): number[] {
		const spark = numberArray(node.spark);
		const spark60 = numberArray(node.spark60);
		const spark30 = numberArray(node.spark30);
		if (key === 'spark30') {
			if (spark30.length >= 2) return spark30;
			if (spark60.length >= 2) return spark60.slice(-30);
			return spark.slice(-30);
		}
		if (key === 'spark60') {
			if (spark60.length >= 2) return spark60;
			if (spark.length >= 2) return spark.slice(-60);
			return spark30;
		}
		if (spark.length >= 2) return spark;
		if (spark60.length >= 2) return spark60;
		return spark30;
	}

	function seriesForCell(value: unknown): SeriesMetric | null {
		if (!value || typeof value !== 'object') return null;
		const series = value as SeriesMetric;
		return Array.isArray(series.values) ? series : null;
	}

	function seriesTrend(series: SeriesMetric): string {
		const values = series.values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
		if (values.length < 2) return '#94a3b8';
		const first = values[0];
		const last = values[values.length - 1];
		if (first === 0) return last >= 0 ? '#ef4444' : '#3b82f6';
		if (last > first * 1.005) return '#ef4444';
		if (last < first * 0.995) return '#3b82f6';
		return '#94a3b8';
	}
</script>

<div class="grid-wrap">
	<!-- viewport (scrollable) · header 도 안에 두고 sticky-top 처리 -->
	<div
		class="viewport"
		bind:this={viewport}
		onscroll={handleScroll}
		role="grid"
		aria-rowcount={totalRows}
	>
		<!-- header row (sticky top + scrolls horizontally with rows) -->
		<div class="grid-header" style:grid-template-columns={colWidthCss()}>
			{#each columns as key (key)}
				{@const def = METRICS_BY_KEY[key]}
				{@const sortState = sortEntry(key)}
				{@const sortDir = sortState?.dir ?? null}
				{@const sortRank = sortIndex(key)}
				<div
					class="hcell"
					class:pinned={isPinned(key)}
					class:numeric={def?.type === 'number'}
					style:left={isPinned(key) ? `${stickyOffsets[key]}px` : ''}
				>
					<button
						type="button"
						class="hbtn"
						onclick={(e) => handleSortClick(e, key)}
						aria-label="{def?.label ?? key} 정렬"
					>
						<HeaderTooltip metric={def} fallbackKey={key} />
						{#if sortDir}
							<span class="sort-arr" aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>
							<span class="sort-rank" aria-hidden="true">{sortRank + 1}</span>
						{/if}
					</button>
					{#if onFilterChange && def && def.type !== 'series'}
						<HeaderFilterPopover
							metric={def}
							fallbackKey={key}
							activeConds={filtersForMetric(key)}
							values={filterOptions?.[key] ?? []}
							onApply={onFilterChange}
							onClear={(metric) => onFilterChange?.(metric, [])}
						/>
					{/if}
				</div>
			{/each}
		</div>
		{#if topPad > 0}<div style:height="{topPad}px" aria-hidden="true"></div>{/if}

		{#each visibleRows as node, i (rowId(node as RowData, startIdx + i))}
			{@const idx = startIdx + i}
			{@const rd = node as RowData}
			{@const id = rowId(rd, idx)}
			{@const tint = isTable ? 'transparent' : rowTintColor(rowQualGrade(rd))}
			{@const isSel = id === selectedId}
			<div
				class="row"
				class:selected={isSel}
				class:nearmiss={nearMissIds?.has(id)}
				role="row"
				aria-rowindex={idx + 2}
				aria-selected={isSel}
				style:grid-template-columns={colWidthCss()}
				style:--row-tint={tint}
				onclick={() => onSelect(id)}
				onkeydown={(e) => {
					if (e.key === 'Enter') onSelect(id);
				}}
				tabindex="0"
			>
				{#each columns as key (key)}
					{@const def = METRICS_BY_KEY[key]}
					{@const v = cellValue(rd, key)}
					{@const formatted = def?.format
						? def.format(v)
						: v == null || v === ''
							? '·'
							: String(v)}
					{@const heatBg = !isTable && def?.type === 'number' && !isPinned(key) ? cellHeatmapBg(key, v) : 'transparent'}
					<div
						class="cell"
						class:pinned={isPinned(key)}
						class:numeric={def?.type === 'number'}
						class:enum={!isTable && def?.type === 'enum'}
						class:spark-cell={key === 'spark' || key === 'spark30' || key === 'spark60'}
						style:left={isPinned(key) ? `${stickyOffsets[key]}px` : ''}
						style:background={isPinned(key) ? undefined : heatBg}
						role="gridcell"
						tabindex="-1"
						title={key === 'product' && typeof rd.productRaw === 'string' ? rd.productRaw : typeof formatted === 'string' ? formatted : undefined}
						onmouseenter={(e) => !isTable && onCellMouseEnter(e, rd, key, formatted)}
						onmouseleave={onCellMouseLeave}
					>
						{#if key === 'label'}
							<button
								type="button"
								class="company-link"
								title="{rowLabel(rd)} ({id})"
								onclick={(e) => {
									e.stopPropagation();
									onSelect(id);
								}}
							>
								<span class="ind-dot" style:background={rowColor(rd)}></span>
								<span class="company-name">{rowLabel(rd)}</span>
							</button>
						{:else if key === 'id'}
							<span class="code-cell">{id}</span>
						{:else if key === 'market'}
							{@const rawMarket = rowMarket(rd, id)}
							{@const market = normalizeMarket(rawMarket)}
							{#if market !== 'UNKNOWN'}
								<span
									class="market-tag market-{market.toLowerCase()}"
									style:color={marketColor(rawMarket)}
									style:border-color={marketColor(rawMarket) + '55'}
									style:background={marketColor(rawMarket) + '14'}
								>{marketLabel(rawMarket)}</span>
							{:else}
								<span class="dim">·</span>
							{/if}
						{:else if key === 'spark' || key === 'spark30' || key === 'spark60'}
							{@const sparkData = sparkForCell(rd, key)}
							{#if Array.isArray(sparkData) && sparkData.length >= 2}
								{@const trend =
									sparkData[sparkData.length - 1] > sparkData[0] * 1.005
										? '#ef4444'
										: sparkData[sparkData.length - 1] < sparkData[0] * 0.995
											? '#3b82f6'
											: '#94a3b8'}
								<span class="spark-wrap" style:color={trend}>
									<Sparkline data={sparkData} width={88} height={24} stroke="currentColor" smooth />
								</span>
							{:else}
								<span class="dim">·</span>
							{/if}
						{:else if def?.type === 'series'}
							{@const series = seriesForCell(v)}
							{#if series && series.values.filter((x) => typeof x === 'number' && Number.isFinite(x)).length >= 2}
								<span class="series-wrap" style:color={seriesTrend(series)} title={formatted}>
									<Sparkline data={series.values} width={82} height={22} stroke="currentColor" smooth />
									<span class="series-latest">{formatted}</span>
								</span>
							{:else}
								<span class="dim">·</span>
							{/if}
						{:else if def?.type === 'enum'}
							{@const tone = gradeTone(key, v)}
							{#if v && v !== ''}
								<span class="chip" style:color={toneColor(tone)} style:border-color={toneColor(tone)}>
									{v}
								</span>
							{:else}
								<span class="dim">·</span>
							{/if}
						{:else if def?.format}
							<span class:dim={v == null}>{formatted}</span>
						{:else if v == null || v === ''}
							<span class="dim">·</span>
						{:else}
							<span>{formatted}</span>
						{/if}
					</div>
				{/each}
			</div>
		{/each}

		{#if bottomPad > 0}<div style:height="{bottomPad}px" aria-hidden="true"></div>{/if}

		{#if totalRows === 0}
			<div class="empty">
				<p>조건과 일치하는 회사가 없습니다.</p>
				<p class="hint">필터를 줄이거나 산업 선택을 늘려보세요.</p>
			</div>
		{/if}
	</div>

	<!-- footer count -->
	<div class="grid-footer">
		<span class="count">{totalRows.toLocaleString('ko-KR')} 사</span>
		{#if sorts.length > 0}
			<span class="sort-hint">
				정렬:
				{#each sorts as s, i (s.key)}
					{#if i > 0} › {/if}{METRICS_BY_KEY[s.key]?.label ?? s.key} {s.dir === 'asc' ? '↑' : '↓'}
				{/each}
			</span>
		{/if}
	</div>
</div>

<style>
	.grid-wrap {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		overflow: hidden;
	}

	.grid-header {
		display: grid;
		position: sticky;
		top: 0;
		width: max-content;
		min-width: 100%;
		height: 40px;
		flex-shrink: 0;
		background: #0a0e18;
		border-bottom: 1px solid #1e2433;
		z-index: 10;
	}
	.hcell {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 0 8px;
		border-right: 1px solid #1e2433;
		overflow: visible;
		position: relative;
	}
	.hcell.numeric {
		justify-content: flex-end;
	}
	.hcell.pinned {
		position: sticky;
		z-index: 30;
		background: #0a0e18;
		box-shadow: 1px 0 0 #1e2433;
	}
	.hbtn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		min-width: 0;
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
		padding: 0;
		font-family: inherit;
		line-height: 1.15;
		white-space: pre;
	}
	.sort-arr {
		font-size: 9px;
		color: var(--amber);
	}
	.sort-rank {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 14px;
		height: 14px;
		border: 1px solid rgba(var(--amber-rgb), 0.5);
		border-radius: 50%;
		color: var(--amber);
		font-size: 9px;
		font-weight: 700;
	}

	.viewport {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		overflow-x: auto;
		position: relative;
	}

	.row {
		display: grid;
		width: max-content;
		min-width: 100%;
		height: 36px;
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
		position: relative;
		cursor: pointer;
		background: color-mix(in srgb, var(--row-tint, transparent) 4%, transparent);
		transition: background 0.1s;
	}
	.row:hover {
		background: color-mix(in srgb, var(--row-tint, #94a3b8) 10%, rgba(255, 255, 255, 0.02));
	}
	.row.selected {
		background: color-mix(in srgb, var(--row-tint, var(--amber)) 14%, rgba(var(--amber-rgb), 0.06));
	}
	/* 근접후보 = 통과가 아니다. 좌측 마커로 격리해 랭킹과 섞이지 않게 한다. */
	.row.nearmiss {
		box-shadow: inset 3px 0 0 var(--dl-warn, #fbbf24);
		opacity: 0.82;
	}
	.row:focus-visible {
		outline: 1px solid var(--amber);
		outline-offset: -1px;
	}

	.cell {
		display: flex;
		align-items: center;
		padding: 0 10px;
		font-size: 12px;
		color: #cbd5e1;
		border-right: 1px solid rgba(30, 36, 51, 0.4);
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
		font-variant-numeric: tabular-nums;
	}
	.cell.numeric {
		justify-content: flex-end;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
	}
	.cell.enum {
		justify-content: flex-start;
	}
	.cell.spark-cell {
		justify-content: center;
		padding: 0 6px;
	}
	.spark-wrap {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	.series-wrap {
		display: inline-grid;
		grid-template-columns: 82px minmax(0, 1fr);
		align-items: center;
		gap: 4px;
		width: 120px;
		min-width: 0;
	}
	.series-latest {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 10px;
		color: #cbd5e1;
	}
	.cell.pinned {
		position: sticky;
		z-index: 20;
		background: #050811;
		box-shadow: 1px 0 0 rgba(30, 36, 51, 0.8);
	}
	.row:hover .cell.pinned {
		background: #0b1120;
	}
	.row.selected .cell.pinned {
		background: #101827;
	}

	.dim {
		color: #475569;
	}

	.chip {
		display: inline-block;
		padding: 1px 7px;
		font-size: 10px;
		font-weight: 600;
		border: 1px solid currentColor;
		border-radius: 3px;
		background: transparent;
		letter-spacing: -0.01em;
	}

	.company-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		background: transparent;
		border: none;
		color: #f1f5f9;
		cursor: pointer;
		font-family: inherit;
		font-size: 12px;
		font-weight: 500;
		padding: 0;
		text-align: left;
	}
	.company-link:hover .company-name {
		color: var(--amber);
		text-decoration: underline;
	}
	.market-tag {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0 5px;
		height: 16px;
		min-width: 46px;
		border-radius: 3px;
		border: 1px solid;
		font-size: 9px;
		font-weight: 600;
		letter-spacing: 0.04em;
		flex-shrink: 0;
	}
	.code-cell {
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		color: #cbd5e1;
	}
	.ind-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.company-name {
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.empty {
		padding: 40px 20px;
		text-align: center;
		color: #64748b;
		font-size: 13px;
	}
	.empty .hint {
		font-size: 11px;
		color: #475569;
		margin-top: 6px;
	}

	.grid-footer {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 6px 12px;
		background: #0a0e18;
		border-top: 1px solid #1e2433;
		font-size: 11px;
		color: #94a3b8;
		font-family: monospace;
	}
	.count {
		color: #f1f5f9;
		font-weight: 600;
	}
	.sort-hint {
		color: #64748b;
	}
</style>
