<script>
	import { cn } from "$lib/utils.js";
	import { searchCompany, fetchDataSources, fetchDataPreview, downloadExcel } from "$lib/api.js";
	import {
		X, Search, Database, ChevronRight, ChevronDown,
		Table2, FileText, Loader2, Download, ArrowLeft,
		Languages,
	} from "lucide-svelte";

	let { onClose } = $props();

	let searchQuery = $state("");
	let searchResults = $state([]);
	let searchLoading = $state(false);
	let searchTimer = null;

	let selectedCompany = $state(null);
	let sourceData = $state(null);
	let sourcesLoading = $state(false);
	let expandedCategories = $state(new Set());

	let activeModule = $state(null);
	let previewData = $state(null);
	let previewLoading = $state(false);

	let excelDownloading = $state(false);
	let useKoreanLabel = $state(true);

	function handleSearchInput() {
		const q = searchQuery.trim();
		if (searchTimer) clearTimeout(searchTimer);
		if (q.length < 2) { searchResults = []; return; }
		searchLoading = true;
		searchTimer = setTimeout(async () => {
			try {
				const data = await searchCompany(q);
				searchResults = data.results?.slice(0, 8) || [];
			} catch {
				searchResults = [];
			}
			searchLoading = false;
		}, 300);
	}

	async function selectCompany(item) {
		selectedCompany = item;
		searchQuery = "";
		searchResults = [];
		sourcesLoading = true;
		activeModule = null;
		previewData = null;
		try {
			sourceData = await fetchDataSources(item.stockCode);
			const cats = Object.keys(sourceData.categories || {});
			expandedCategories = new Set(cats.slice(0, 2));
		} catch {
			sourceData = null;
		}
		sourcesLoading = false;
	}

	function goBackToSearch() {
		selectedCompany = null;
		sourceData = null;
		activeModule = null;
		previewData = null;
	}

	async function selectModule(source) {
		if (!source.available) return;
		activeModule = source;
		previewLoading = true;
		previewData = null;
		try {
			previewData = await fetchDataPreview(selectedCompany.stockCode, source.name, 200);
		} catch (e) {
			previewData = { type: "error", error: e.message };
		}
		previewLoading = false;
	}

	function toggleCategory(cat) {
		const next = new Set(expandedCategories);
		if (next.has(cat)) next.delete(cat);
		else next.add(cat);
		expandedCategories = next;
	}

	async function handleDownloadExcel() {
		if (!selectedCompany) return;
		excelDownloading = true;
		try {
			await downloadExcel(selectedCompany.stockCode);
		} catch {}
		excelDownloading = false;
	}

	const CATEGORY_LABELS = {
		finance: "재무제표",
		report: "정기보고서",
		disclosure: "공시 서술",
		notes: "K-IFRS 주석",
		analysis: "분석",
		raw: "원본 데이터",
	};

	function categoryLabel(cat) {
		return CATEGORY_LABELS[cat] || cat;
	}

	function categoryStats(items) {
		const avail = items.filter(i => i.available).length;
		return `${avail}/${items.length}`;
	}

	function getAccountLabel(snakeId) {
		if (!previewData?.meta?.labels || !useKoreanLabel) return snakeId;
		return previewData.meta.labels[snakeId] || snakeId;
	}

	function getAccountLevel(snakeId) {
		if (!previewData?.meta?.levels) return 1;
		return previewData.meta.levels[snakeId] || 1;
	}

	function formatWon(val) {
		if (val === null || val === undefined) return "-";
		if (typeof val !== "number") return String(val);
		if (val === 0) return "0";
		const abs = Math.abs(val);
		const sign = val < 0 ? "-" : "";
		if (abs >= 1e12) return `${sign}${(abs / 1e12).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}조`;
		if (abs >= 1e8) return `${sign}${Math.round(abs / 1e8).toLocaleString("ko-KR")}억`;
		if (abs >= 1e4) return `${sign}${Math.round(abs / 1e4).toLocaleString("ko-KR")}만`;
		return val.toLocaleString("ko-KR");
	}

	function isYearValue(val) {
		return Number.isInteger(val) && val >= 1900 && val <= 2100;
	}

	function formatCellValue(val, unit) {
		if (val === null || val === undefined) return "-";
		if (typeof val === "number") {
			if (isYearValue(val)) return String(val);
			if (unit === "원" || unit === "백만원") {
				if (unit === "백만원") val = val * 1_000_000;
				return formatWon(val);
			}
			if (Number.isInteger(val) && Math.abs(val) >= 1000) {
				return val.toLocaleString("ko-KR");
			}
			if (!Number.isInteger(val)) {
				return val.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
			}
		}
		return String(val);
	}

	function getUnit() {
		if (previewData?.meta?.unit) return previewData.meta.unit;
		if (previewData?.unit) return previewData.unit;
		return "";
	}

	function isFinanceTimeseries() {
		return !!previewData?.meta?.labels;
	}

	function getDataColumns() {
		if (!previewData?.columns) return [];
		return previewData.columns.filter(c => c !== "계정명");
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 z-[200] flex flex-col bg-dl-bg-dark animate-fadeIn"
	onkeydown={(e) => { if (e.key === 'Escape') onClose?.(); }}
>
	<!-- ═══ Top Bar ═══ -->
	<div class="flex items-center justify-between px-5 py-3 flex-shrink-0 border-b border-dl-border/50 bg-dl-bg-card/80 backdrop-blur-sm">
		<div class="flex items-center gap-3">
			{#if selectedCompany}
				<button
					class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={goBackToSearch}
				>
					<ArrowLeft size={16} />
				</button>
				<div class="w-8 h-8 rounded-lg bg-dl-primary/15 flex items-center justify-center flex-shrink-0">
					<span class="text-[13px] font-bold text-dl-primary-light">{selectedCompany.corpName[0]}</span>
				</div>
				<div>
					<div class="text-[14px] font-semibold text-dl-text">{selectedCompany.corpName}</div>
					<div class="text-[10px] text-dl-text-dim">{selectedCompany.stockCode}{sourceData ? ` · ${sourceData.availableSources}개 데이터` : ""}</div>
				</div>
			{:else}
				<Database size={18} class="text-dl-primary-light" />
				<div class="text-[15px] font-semibold text-dl-text">데이터 탐색</div>
			{/if}
		</div>
		<div class="flex items-center gap-2">
			{#if selectedCompany && !activeModule}
				<button
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"
					onclick={handleDownloadExcel}
					disabled={excelDownloading}
				>
					{#if excelDownloading}
						<Loader2 size={12} class="animate-spin" />
					{:else}
						<Download size={12} />
					{/if}
					전체 Excel
				</button>
			{/if}
			<button
				class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
				onclick={() => onClose?.()}
			>
				<X size={16} />
			</button>
		</div>
	</div>

	<!-- ═══ Body ═══ -->
	<div class="flex-1 flex min-h-0">

		<!-- ═══ 검색 화면 ═══ -->
		{#if !selectedCompany}
			<div class="flex-1 overflow-y-auto px-5 py-8">
				<div class="max-w-lg mx-auto">
					<div class="relative mb-4">
						<Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim pointer-events-none" />
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="종목명 또는 종목코드 검색..."
							class="w-full pl-9 pr-4 py-3 bg-dl-bg-card border border-dl-border rounded-xl text-[13px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/40 transition-colors"
							oninput={handleSearchInput}
						/>
						{#if searchLoading}
							<Loader2 size={14} class="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim" />
						{/if}
					</div>

					{#if searchResults.length > 0}
						<div class="space-y-1">
							{#each searchResults as item}
								<button
									class="flex items-center gap-3 w-full px-4 py-3 rounded-xl border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all"
									onclick={() => selectCompany(item)}
								>
									<div class="w-8 h-8 rounded-lg bg-dl-primary/10 flex items-center justify-center flex-shrink-0">
										<span class="text-[12px] font-bold text-dl-primary-light">{item.corpName[0]}</span>
									</div>
									<div class="flex-1 min-w-0">
										<div class="text-[13px] font-medium text-dl-text">{item.corpName}</div>
										<div class="text-[10px] text-dl-text-dim">{item.stockCode} · {item.market || ""}</div>
									</div>
									{#if item.sector}
										<span class="text-[10px] text-dl-text-dim flex-shrink-0">{item.sector}</span>
									{/if}
									<ChevronRight size={14} class="text-dl-text-dim flex-shrink-0" />
								</button>
							{/each}
						</div>
					{:else if searchQuery.trim().length >= 2 && !searchLoading}
						<div class="text-center py-16 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>
					{:else}
						<div class="text-center py-24">
							<Database size={40} class="mx-auto mb-4 text-dl-text-dim/30" />
							<div class="text-[14px] text-dl-text-muted mb-1">종목을 검색하여 데이터를 탐색하세요</div>
							<div class="text-[12px] text-dl-text-dim/70">재무제표, 정기보고서, 공시 데이터를 직접 확인하고 Excel로 내보낼 수 있습니다</div>
						</div>
					{/if}
				</div>
			</div>

		<!-- ═══ 2패널: 좌측 모듈 + 우측 데이터 ═══ -->
		{:else}
			<!-- 좌측 모듈 목록 -->
			<div class="w-[240px] flex-shrink-0 border-r border-dl-border/50 overflow-y-auto bg-dl-bg-card/30">
				{#if sourcesLoading}
					<div class="flex items-center justify-center py-12 gap-2 text-[12px] text-dl-text-dim">
						<Loader2 size={14} class="animate-spin" />
						탐색 중...
					</div>
				{:else if sourceData}
					{#each Object.entries(sourceData.categories) as [cat, items]}
						<div class="mx-2 mb-0.5">
							<button
								class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left hover:bg-white/[0.03] transition-colors"
								onclick={() => toggleCategory(cat)}
							>
								{#if expandedCategories.has(cat)}
									<ChevronDown size={12} class="text-dl-text-dim flex-shrink-0" />
								{:else}
									<ChevronRight size={12} class="text-dl-text-dim flex-shrink-0" />
								{/if}
								<span class="text-[11px] font-medium text-dl-text-muted flex-1">{categoryLabel(cat)}</span>
								<span class="text-[9px] text-dl-text-dim">{categoryStats(items)}</span>
							</button>

							{#if expandedCategories.has(cat)}
								<div class="ml-2 border-l border-dl-border/30 pl-1">
									{#each items as source}
										<button
											class={cn(
												"flex items-center gap-1.5 w-full px-2 py-1 rounded-lg text-left text-[11px] transition-colors",
												!source.available && "opacity-30 cursor-default",
												source.available && activeModule?.name === source.name
													? "bg-dl-primary/10 text-dl-primary-light"
													: source.available
														? "text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text"
														: ""
											)}
											onclick={() => selectModule(source)}
											disabled={!source.available}
										>
											{#if source.dataType === "timeseries" || source.dataType === "table" || source.dataType === "dataframe"}
												<Table2 size={10} class="flex-shrink-0" />
											{:else}
												<FileText size={10} class="flex-shrink-0" />
											{/if}
											<span class="flex-1 min-w-0 truncate">{source.label}</span>
										</button>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>

			<!-- 우측 데이터 -->
			<div class="flex-1 flex flex-col min-w-0 min-h-0">
				{#if !activeModule}
					<div class="flex items-center justify-center h-full text-center">
						<div>
							<Table2 size={36} class="mx-auto mb-3 text-dl-text-dim/20" />
							<div class="text-[13px] text-dl-text-dim">좌측에서 모듈을 선택하세요</div>
						</div>
					</div>
				{:else if previewLoading}
					<div class="flex items-center justify-center h-full gap-2 text-[13px] text-dl-text-dim">
						<Loader2 size={16} class="animate-spin" />
						{activeModule.label} 로딩 중...
					</div>
				{:else if previewData}
					<!-- 미리보기 헤더 -->
					<div class="flex items-center justify-between px-4 py-2 flex-shrink-0 border-b border-dl-border/30 bg-dl-bg-card/50">
						<div class="flex items-center gap-2">
							<span class="text-[13px] font-medium text-dl-text">{activeModule.label}</span>
							{#if previewData.type === "table"}
								<span class="text-[10px] text-dl-text-dim">{previewData.totalRows}행 × {previewData.columns.length}열</span>
							{/if}
							{#if getUnit()}
								<span class="px-1.5 py-0.5 rounded bg-dl-border/50 text-[9px] text-dl-text-dim">
									{getUnit() === "원" ? "원" : getUnit()}
								</span>
							{/if}
						</div>
						<div class="flex items-center gap-1.5">
							{#if isFinanceTimeseries()}
								<button
									class={cn(
										"flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] transition-colors",
										useKoreanLabel
											? "bg-dl-primary/15 text-dl-primary-light"
											: "text-dl-text-dim hover:text-dl-text hover:bg-white/5"
									)}
									onclick={() => useKoreanLabel = !useKoreanLabel}
								>
									<Languages size={11} />
									{useKoreanLabel ? "한글" : "EN"}
								</button>
							{/if}
							{#if selectedCompany}
								<button
									class="flex items-center gap-1 px-2 py-1 rounded-lg bg-dl-success/10 text-dl-success text-[10px] hover:bg-dl-success/20 transition-colors"
									onclick={async () => { try { await downloadExcel(selectedCompany.stockCode, [activeModule.name]); } catch {} }}
								>
									<Download size={10} />
									Excel
								</button>
							{/if}
						</div>
					</div>

					<!-- 테이블 (finance 시계열) -->
					{#if previewData.type === "table" && isFinanceTimeseries()}
						<div class="flex-1 overflow-auto min-h-0">
							<table class="text-[11px] border-collapse">
								<thead class="sticky top-0 z-[5]">
									<tr>
										<th class="sticky left-0 z-[10] px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-r border-dl-border/30 whitespace-nowrap text-[10px] min-w-[180px]">
											계정명
										</th>
										{#each getDataColumns() as col}
											<th class="px-3 py-2 text-right text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px] min-w-[100px]">{col}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each previewData.rows as row}
										{@const snakeId = row["계정명"]}
										{@const level = getAccountLevel(snakeId)}
										<tr class="hover:bg-white/[0.02]">
											<td
												class={cn(
													"sticky left-0 z-[1] px-3 py-1.5 border-b border-r border-dl-border/10 whitespace-nowrap bg-dl-bg-dark/95",
													level === 1 && "font-semibold text-dl-text",
													level === 2 && "text-dl-text-muted",
													level === 3 && "text-dl-text-dim"
												)}
												style="padding-left: {8 + (level - 1) * 12}px"
											>
												{getAccountLabel(snakeId)}
											</td>
											{#each getDataColumns() as col}
												{@const val = row[col]}
												<td class={cn(
													"px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap text-right font-mono text-[10px]",
													val === null || val === undefined ? "text-dl-text-dim/30" :
													typeof val === "number" && val < 0 ? "text-dl-primary-light" :
													"text-dl-accent-light"
												)}>{formatCellValue(val, getUnit())}</td>
											{/each}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						{#if previewData.truncated}
							<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0">
								상위 {previewData.rows.length}행만 표시 (전체 {previewData.totalRows}행)
							</div>
						{/if}

					<!-- 일반 테이블 -->
					{:else if previewData.type === "table"}
						<div class="flex-1 overflow-auto min-h-0">
							<table class="w-full text-[11px] border-collapse">
								<thead class="sticky top-0 z-[5]">
									<tr>
										{#each previewData.columns as col}
											<th class="px-3 py-2 text-left text-dl-text-muted font-medium bg-dl-bg-darker border-b border-dl-border/30 whitespace-nowrap text-[10px]">{col}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each previewData.rows as row}
										<tr class="hover:bg-white/[0.02]">
											{#each previewData.columns as col}
												{@const val = row[col]}
												<td class={cn(
													"px-3 py-1.5 border-b border-dl-border/10 whitespace-nowrap",
													typeof val === "number" ? "text-right font-mono text-dl-accent-light text-[10px]" : "text-dl-text-muted"
												)}>{formatCellValue(val, getUnit())}</td>
											{/each}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						{#if previewData.truncated}
							<div class="px-4 py-1.5 text-[10px] text-dl-warning border-t border-dl-border/20 flex-shrink-0">
								상위 {previewData.rows.length}행만 표시 (전체 {previewData.totalRows}행)
							</div>
						{/if}

					<!-- dict -->
					{:else if previewData.type === "dict"}
						<div class="flex-1 overflow-auto min-h-0 p-4 space-y-1.5">
							{#each Object.entries(previewData.data) as [key, val]}
								<div class="flex gap-3 px-3 py-2 rounded-lg bg-dl-bg-card/50">
									<span class="text-[11px] text-dl-text-muted font-medium min-w-[160px] flex-shrink-0">{key}</span>
									<span class="text-[11px] text-dl-text-dim break-all">{val ?? "-"}</span>
								</div>
							{/each}
						</div>

					<!-- text -->
					{:else if previewData.type === "text"}
						<div class="flex-1 overflow-auto min-h-0 p-4">
							<pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap leading-relaxed">{previewData.text}</pre>
							{#if previewData.truncated}
								<div class="mt-2 text-[10px] text-dl-warning">내용이 잘려서 표시됩니다</div>
							{/if}
						</div>

					<!-- error -->
					{:else if previewData.type === "error"}
						<div class="flex items-center justify-center h-full text-[13px] text-dl-primary-light">
							{previewData.error || "데이터를 불러올 수 없습니다"}
						</div>

					<!-- unknown -->
					{:else}
						<div class="flex-1 overflow-auto min-h-0 p-4">
							<pre class="text-[11px] text-dl-text-muted whitespace-pre-wrap">{previewData.data || JSON.stringify(previewData, null, 2)}</pre>
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	</div>
</div>
