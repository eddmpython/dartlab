<!--
	TableRenderer — 테이블 블록 전용 렌더러.
	finance: sticky 첫 컬럼, 숫자 포맷, 핵심 행 하이라이트
	structured/report: 일반 테이블
	raw_markdown: 기간 전환 + 마크다운 렌더링
-->
<script>
	import { renderMarkdown } from "$lib/markdown.js";
	import TimelineBar from "./TimelineBar.svelte";

	let {
		block = null,      // viewerBlock
		maxRows = 100,     // 최대 표시 행
	} = $props();

	let selectedPeriod = $state(null);
	let showAll = $state(false);

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
			const formatted = Math.abs(val) >= 1
				? val.toLocaleString("ko-KR")
				: val.toString();
			return formatted;
		}
		// string that looks numeric
		const s = String(val).trim();
		if (/^-?[\d,]+(\.\d+)?$/.test(s)) {
			const num = parseFloat(s.replace(/,/g, ""));
			if (!isNaN(num)) {
				return Math.abs(num) >= 1
					? num.toLocaleString("ko-KR")
					: num.toString();
			}
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

	let displayRows = $derived(showAll ? (block?.data?.rows ?? []) : (block?.data?.rows ?? []).slice(0, maxRows));
</script>

{#if block}
	{#if block.kind === "raw_markdown" && block.rawMarkdown}
		{@const periods = rawPeriods(block)}
		{@const displayP = rawDisplayPeriod(block)}
		{#if periods.length > 0}
			<!-- Period timeline for raw_markdown -->
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
	{:else if isFinanceBlock(block) && block.data?.rows}
		<!-- Finance table — professional rendering -->
		<div class="overflow-x-auto rounded-lg border border-dl-border/10">
			<table class="finance-table">
				<thead>
					<tr>
						{#each block.data.columns ?? [] as col, ci}
							<th>{col}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each displayRows as row}
						{@const isKey = isKeyRow(row, block.data.columns)}
						<tr class={isKey ? "row-key" : ""}>
							{#each block.data.columns ?? [] as col, ci}
								{@const val = row[col]}
								{@const isNum = ci > 0 && isNumeric(val)}
								<td class="{isNum ? (isNegative(val) ? 'val-neg' : 'val-pos') : ''}">
									{isNum ? formatNumber(val) : (val ?? "")}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			{#if !showAll && block.data.rows.length > maxRows}
				<button
					class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"
					onclick={() => { showAll = true; }}
				>
					외 {block.data.rows.length - maxRows}행 더 보기
				</button>
			{/if}
		</div>
		{#if block.meta?.scale || block.meta?.unit}
			<div class="text-[10px] text-dl-text-dim mt-1">
				단위: {block.meta.unit || ""} {block.meta.scale ? `(${block.meta.scale})` : ""}
			</div>
		{/if}
	{:else if block.data?.rows}
		<!-- Structured / report table -->
		<div class="overflow-x-auto rounded-lg border border-dl-border/10">
			<table class="prose-dartlab w-full text-[12px]">
				<thead>
					<tr>
						{#each block.data.columns ?? [] as col}
							<th>{col}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each displayRows as row}
						<tr>
							{#each block.data.columns ?? [] as col}
								<td class={isNumeric(row[col]) ? "num" : ""}>{row[col] ?? ""}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			{#if !showAll && block.data.rows.length > maxRows}
				<button
					class="w-full text-[11px] text-dl-text-dim text-center py-2 border-t border-dl-border/10 hover:text-dl-text-muted hover:bg-white/3 transition-colors"
					onclick={() => { showAll = true; }}
				>
					외 {block.data.rows.length - maxRows}행 더 보기
				</button>
			{/if}
		</div>
		{#if block.meta?.scale}
			<div class="text-[10px] text-dl-text-dim mt-1">
				단위: {block.meta.unit || ""} {block.meta.scale ? `(${block.meta.scale})` : ""}
			</div>
		{/if}
	{/if}
{/if}
