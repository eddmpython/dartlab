<!--
	TableRenderer — 테이블 블록 전용 렌더러.
	finance: sticky 첫 컬럼, 숫자 포맷, 핵심 행 하이라이트, 다중 정렬, 변화율 화살표
	structured/report: 일반 테이블
	raw_markdown: 기간 전환 + 마크다운 렌더링
	기능: 다중 정렬(Shift+클릭), CSV 내보내기, 열 필터
-->
<script>
	import { renderMarkdown } from "$lib/markdown.js";
	import { Download, Filter, X } from "lucide-svelte";
	import TimelineBar from "./TimelineBar.svelte";
	import VirtualScroller from "./VirtualScroller.svelte";

	let {
		block = null,      // viewerBlock
		maxRows = 100,     // 최대 표시 행
	} = $props();

	let selectedPeriod = $state(null);
	let showAll = $state(false);

	// ── 다중 정렬: [{col, dir}] ──
	let sortKeys = $state([]);

	function handleSort(col, e) {
		if (e.shiftKey) {
			// Shift+클릭: 기존 정렬에 추가/토글
			const idx = sortKeys.findIndex(k => k.col === col);
			if (idx >= 0) {
				const newKeys = [...sortKeys];
				if (newKeys[idx].dir === "asc") {
					newKeys[idx] = { col, dir: "desc" };
				} else {
					newKeys.splice(idx, 1);
				}
				sortKeys = newKeys;
			} else {
				sortKeys = [...sortKeys, { col, dir: "asc" }];
			}
		} else {
			// 일반 클릭: 단일 정렬
			if (sortKeys.length === 1 && sortKeys[0].col === col) {
				sortKeys = [{ col, dir: sortKeys[0].dir === "asc" ? "desc" : "asc" }];
			} else {
				sortKeys = [{ col, dir: "asc" }];
			}
		}
	}

	function sortIndicator(col) {
		const idx = sortKeys.findIndex(k => k.col === col);
		if (idx < 0) return "";
		const arrow = sortKeys[idx].dir === "asc" ? "▲" : "▼";
		return sortKeys.length > 1 ? ` ${arrow}${idx + 1}` : ` ${arrow}`;
	}

	// ── 열 필터 ──
	let filterCol = $state(null);
	let filterText = $state("");
	let filterMin = $state("");
	let filterMax = $state("");

	// 필터 대상 열이 숫자 열인지 감지
	let isFilterNumeric = $derived.by(() => {
		if (!filterCol) return false;
		const rows = block?.data?.rows ?? [];
		let numCount = 0;
		for (let i = 0; i < Math.min(5, rows.length); i++) {
			if (isNumeric(rows[i]?.[filterCol])) numCount++;
		}
		return numCount >= 2;
	});

	function toggleFilter(col) {
		if (filterCol === col) {
			filterCol = null;
			filterText = "";
			filterMin = "";
			filterMax = "";
		} else {
			filterCol = col;
			filterText = "";
			filterMin = "";
			filterMax = "";
		}
	}

	// Finance 핵심 행 (한글/영문)
	const KEY_ROWS = new Set([
		"매출액", "revenue", "영업이익", "operating_income",
		"당기순이익", "net_income", "자산총계", "total_assets",
		"부채총계", "total_liabilities", "자본총계", "total_equity",
		"영업활동현금흐름", "operating_cash_flow",
		"매출총이익", "gross_profit", "EBITDA",
	]);

	function isKeyRow(row, columns) {
		if (!columns?.length) return false;
		const firstVal = String(row[columns[0]] ?? "").trim();
		return KEY_ROWS.has(firstVal);
	}

	function formatNumber(val) {
		if (val == null || val === "" || val === "-") return val ?? "";
		if (typeof val === "number") {
			return Math.abs(val) >= 1 ? val.toLocaleString("ko-KR") : val.toString();
		}
		const s = String(val).trim();
		if (/^-?[\d,]+(\.\d+)?$/.test(s)) {
			const num = parseFloat(s.replace(/,/g, ""));
			if (!isNaN(num)) return Math.abs(num) >= 1 ? num.toLocaleString("ko-KR") : num.toString();
		}
		return val;
	}

	function isNegative(val) {
		if (typeof val === "number") return val < 0;
		const s = String(val ?? "").trim().replace(/,/g, "");
		return /^-\d/.test(s);
	}

	function isNumeric(val) {
		if (typeof val === "number") return true;
		return typeof val === "string" && /^-?[\d,]+(\.\d+)?$/.test(val.trim());
	}

	function toNum(val) {
		if (typeof val === "number") return val;
		return parseFloat(String(val ?? "").replace(/,/g, ""));
	}

	function isFinanceBlock(b) {
		return b?.kind === "finance";
	}

	// raw_markdown 기간 관련
	function rawPeriods(b) {
		if (!b?.rawMarkdown) return [];
		return Object.keys(b.rawMarkdown);
	}

	function rawDisplayPeriod(b) {
		const periods = rawPeriods(b);
		if (selectedPeriod && periods.includes(selectedPeriod)) return selectedPeriod;
		return periods[0] ?? null;
	}

	// ── 필터 + 다중 정렬 파이프라인 ──
	let filteredRows = $derived.by(() => {
		let rows = block?.data?.rows ?? [];
		if (filterCol) {
			if (isFilterNumeric) {
				const min = filterMin !== "" ? parseFloat(filterMin) : null;
				const max = filterMax !== "" ? parseFloat(filterMax) : null;
				if (min != null || max != null) {
					rows = rows.filter(r => {
						const n = toNum(r[filterCol]);
						if (isNaN(n)) return false;
						if (min != null && n < min) return false;
						if (max != null && n > max) return false;
						return true;
					});
				}
			} else if (filterText.trim()) {
				const q = filterText.trim().toLowerCase();
				rows = rows.filter(r => {
					const v = String(r[filterCol] ?? "").toLowerCase();
					return v.includes(q);
				});
			}
		}
		return rows;
	});

	let sortedRows = $derived.by(() => {
		if (sortKeys.length === 0) return filteredRows;
		return [...filteredRows].sort((a, b) => {
			for (const { col, dir } of sortKeys) {
				let va = a[col], vb = b[col];
				const na = toNum(va), nb = toNum(vb);
				let cmp = 0;
				if (!isNaN(na) && !isNaN(nb)) {
					cmp = na - nb;
				} else {
					cmp = String(va ?? "").localeCompare(String(vb ?? ""));
				}
				if (cmp !== 0) return dir === "asc" ? cmp : -cmp;
			}
			return 0;
		});
	});

	let useVirtual = $derived(sortedRows.length > 100);
	let displayRows = $derived(showAll || useVirtual ? sortedRows : sortedRows.slice(0, maxRows));

	// ── 열 리사이즈 ──
	let colWidths = $state({});
	let resizing = $state(null); // { col, startX, startWidth }

	function onResizeStart(col, e) {
		e.preventDefault();
		e.stopPropagation();
		const th = e.target.closest("th");
		const startWidth = colWidths[col] || th?.offsetWidth || 120;
		resizing = { col, startX: e.clientX, startWidth };

		function onMove(ev) {
			const delta = ev.clientX - resizing.startX;
			colWidths = { ...colWidths, [resizing.col]: Math.max(60, resizing.startWidth + delta) };
		}
		function onUp() {
			resizing = null;
			window.removeEventListener("pointermove", onMove);
			window.removeEventListener("pointerup", onUp);
		}
		window.addEventListener("pointermove", onMove);
		window.addEventListener("pointerup", onUp);
	}

	// ── CSV 내보내기 ──
	function exportCSV() {
		const cols = block?.data?.columns ?? [];
		const rows = sortedRows;
		if (!cols.length) return;

		const escape = (v) => {
			const s = String(v ?? "");
			return s.includes(",") || s.includes('"') || s.includes("\n")
				? `"${s.replace(/"/g, '""')}"` : s;
		};

		const lines = [cols.map(escape).join(",")];
		for (const row of rows) {
			lines.push(cols.map(c => escape(row[c])).join(","));
		}

		const blob = new Blob(["\uFEFF" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${block?.title || "table"}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}

	// ── 변화율 계산 (finance 테이블: 인접 기간 열 비교) ──
	function changeRate(row, columns, ci) {
		if (ci < 2) return null; // 첫 열(계정명)과 마지막 기간 열은 비교 불가
		const cur = toNum(row[columns[ci]]);
		const prev = toNum(row[columns[ci - 1]]);
		if (isNaN(cur) || isNaN(prev) || prev === 0) return null;
		return ((cur - prev) / Math.abs(prev)) * 100;
	}
</script>

{#if block}
	{#if block.kind === "raw_markdown" && block.rawMarkdown}
		{@const periods = rawPeriods(block)}
		{@const displayP = rawDisplayPeriod(block)}
		{#if periods.length > 0}
			{#if periods.length > 1}
				<div class="mb-1">
					<TimelineBar
						{periods}
						selected={displayP}
						onSelect={(p) => { selectedPeriod = p; }}
					/>
				</div>
			{/if}
			<div class="text-[10px] text-dl-text-dim mb-1 font-mono">{displayP}</div>
			<div class="prose-dartlab overflow-x-auto">
				{@html renderMarkdown(block.rawMarkdown[displayP])}
			</div>
		{/if}
	{:else if (isFinanceBlock(block) || block.data?.rows) && block.data?.columns}
		<!-- Finance / Structured table -->
		<div class="overflow-x-auto rounded-lg border border-dl-border/10" style={useVirtual && !showAll ? "max-height: 500px; overflow-y: auto" : ""}>
			<!-- 툴바 -->
			<div class="flex items-center gap-2 px-2 py-1 border-b border-dl-border/10 bg-dl-bg-card/30">
				{#if filterCol}
					<div class="flex items-center gap-1 flex-1">
						<Filter size={11} class="text-dl-text-dim shrink-0" />
{#if isFilterNumeric}
							<input type="number" bind:value={filterMin} placeholder="Min" class="w-20 bg-transparent border-none outline-none text-[11px] text-dl-text placeholder:text-dl-text-dim" />
							<span class="text-[10px] text-dl-text-dim">~</span>
							<input type="number" bind:value={filterMax} placeholder="Max" class="w-20 bg-transparent border-none outline-none text-[11px] text-dl-text placeholder:text-dl-text-dim" />
						{:else}
							<input
								type="text"
								bind:value={filterText}
								placeholder="{filterCol} 필터..."
								class="flex-1 bg-transparent border-none outline-none text-[11px] text-dl-text placeholder:text-dl-text-dim"
							/>
						{/if}
						<button
							class="p-0.5 rounded text-dl-text-dim hover:text-dl-text transition-colors"
							onclick={() => { filterCol = null; filterText = ""; }}
						>
							<X size={11} />
						</button>
					</div>
				{:else}
					<span class="text-[10px] text-dl-text-dim flex-1">
						{sortedRows.length}행
						{#if sortKeys.length > 0}
							· 정렬 {sortKeys.length}열
						{/if}
					</span>
				{/if}
				<button
					class="p-1 rounded text-dl-text-dim hover:text-dl-text transition-colors"
					onclick={exportCSV}
					title="CSV 내보내기"
				>
					<Download size={12} />
				</button>
			</div>

			<table class={isFinanceBlock(block) ? "finance-table" : "structured-table"}>
				<thead>
					<tr>
						{#each block.data.columns as col, ci}
							<th
								class="{ci === 0 && !isFinanceBlock(block) ? 'col-sticky' : ''} cursor-pointer select-none group relative"
								style={colWidths[col] ? `width: ${colWidths[col]}px; min-width: ${colWidths[col]}px` : ""}
								aria-sort={sortKeys.find(k => k.col === col)?.dir === "asc" ? "ascending" : sortKeys.find(k => k.col === col)?.dir === "desc" ? "descending" : "none"}
							>
								<span class="hover:text-dl-text" onclick={(e) => handleSort(col, e)}>
									{col}{sortIndicator(col)}
								</span>
								<button
									class="ml-1 opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity p-0.5"
									onclick={() => toggleFilter(col)}
									title="{col} 필터"
								>
									<Filter size={9} />
								</button>
								<!-- svelte-ignore a11y_no_static_element_interactions -->
								<div
									class="col-resize-handle"
									onpointerdown={(e) => onResizeStart(col, e)}
								></div>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each displayRows as row}
						{@const isKey = isFinanceBlock(block) && isKeyRow(row, block.data.columns)}
						<tr class={isKey ? "row-key" : ""}>
							{#each block.data.columns as col, ci}
								{@const val = row[col]}
								{@const isNum = ci > 0 && isNumeric(val)}
								{@const rate = isFinanceBlock(block) && isNum ? changeRate(row, block.data.columns, ci) : null}
								<td class="{ci === 0 && !isFinanceBlock(block) ? 'col-sticky' : ''} {isNum ? (isNegative(val) ? 'val-neg' : 'val-pos') : ''}">
									{isNum ? formatNumber(val) : (val ?? "")}
									{#if rate != null}
										<span class="text-[9px] ml-1 {rate >= 0 ? 'text-dl-success/70' : 'text-dl-primary/70'}">
											{rate >= 0 ? "▲" : "▼"}{Math.abs(rate).toFixed(1)}%
										</span>
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			{#if !showAll && (block.data.rows.length > maxRows || filteredRows.length < (block.data.rows?.length ?? 0))}
				<button
					class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"
					onclick={() => { showAll = true; }}
				>
					{#if filteredRows.length < block.data.rows.length}
						{filteredRows.length} / {block.data.rows.length}행 표시 중
					{:else}
						외 {block.data.rows.length - maxRows}행 더 보기
					{/if}
				</button>
			{/if}
		</div>
		{#if block.meta?.scale || block.meta?.unit}
			<div class="text-[10px] text-dl-text-dim mt-1">
				단위: {block.meta.unit || ""} {block.meta.scale ? `(${block.meta.scale})` : ""}
			</div>
		{/if}
	{/if}
{/if}
