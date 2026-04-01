<script>
	import { cn } from "$lib/utils.js";
	import { fetchExportModules, fetchTemplates, downloadExcel, saveTemplate, deleteTemplate, searchCompany } from "$lib/api.js";
	import {
		FileSpreadsheet, Download, Loader2, X, CheckSquare, Square,
		ChevronDown, ChevronUp, Trash2, Save, LayoutTemplate, Search
	} from "lucide-svelte";

	let { stockCode: initialStockCode = null, corpName: initialCorpName = "", onClose } = $props();

	let activeStockCode = $state(null);
	let activeCorpName = $state("");

	let searchQuery = $state("");
	let searchResults = $state([]);
	let searchLoading = $state(false);
	let searchSelectedIdx = $state(-1);
	let showSearchResults = $state(false);
	let searchDebounce = null;

	$effect(() => {
		if (initialStockCode) {
			activeStockCode = initialStockCode;
			activeCorpName = initialCorpName;
		}
	});

	function handleSearchInput() {
		const q = searchQuery.trim();
		if (searchDebounce) clearTimeout(searchDebounce);
		if (q.length < 2) { showSearchResults = false; return; }
		searchDebounce = setTimeout(async () => {
			searchLoading = true;
			try {
				const data = await searchCompany(q);
				if (data.results?.length > 0) {
					searchResults = data.results.slice(0, 8);
					showSearchResults = true;
					searchSelectedIdx = -1;
				} else {
					showSearchResults = false;
				}
			} catch {
				showSearchResults = false;
			}
			searchLoading = false;
		}, 250);
	}

	function handleSearchKeydown(e) {
		if (showSearchResults && searchResults.length > 0) {
			if (e.key === "ArrowDown") { e.preventDefault(); searchSelectedIdx = (searchSelectedIdx + 1) % searchResults.length; return; }
			if (e.key === "ArrowUp") { e.preventDefault(); searchSelectedIdx = searchSelectedIdx <= 0 ? searchResults.length - 1 : searchSelectedIdx - 1; return; }
			if (e.key === "Enter" && searchSelectedIdx >= 0) { e.preventDefault(); selectSearchResult(searchResults[searchSelectedIdx]); return; }
			if (e.key === "Escape") { showSearchResults = false; return; }
		}
	}

	function selectSearchResult(item) {
		activeStockCode = item.stockCode;
		activeCorpName = item.corpName;
		searchQuery = "";
		showSearchResults = false;
		searchResults = [];
	}

	/** @type {"template" | "custom"} */
	let mode = $state("template");
	let modules = $state([]);
	let selected = $state(new Set());
	let templates = $state([]);
	let selectedTemplate = $state(null);
	let loading = $state(false);
	let downloading = $state(false);
	let error = $state("");
	let expanded = $state(false);
	let showNewTemplate = $state(false);
	let newTemplateName = $state("");

	const FINANCE_GROUP = new Set(["IS", "BS", "CF", "ratios"]);

	let financeModules = $derived(modules.filter(m => FINANCE_GROUP.has(m.name)));
	let otherModules = $derived(modules.filter(m => !FINANCE_GROUP.has(m.name)));
	let allSelected = $derived(selected.size === modules.length && modules.length > 0);

	$effect(() => {
		if (activeStockCode) {
			loadModules();
			loadTemplates();
		}
	});

	async function loadModules() {
		loading = true;
		error = "";
		try {
			const data = await fetchExportModules(activeStockCode);
			modules = data.modules || [];
			selected = new Set(modules.map(m => m.name));
		} catch (e) {
			error = e.message;
		}
		loading = false;
	}

	async function loadTemplates() {
		try {
			const data = await fetchTemplates();
			templates = data.templates || [];
		} catch {}
	}

	function toggle(name) {
		const next = new Set(selected);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		selected = next;
	}

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(modules.map(m => m.name));
		}
	}

	function toggleGroup(group) {
		const names = group.map(m => m.name);
		const allIn = names.every(n => selected.has(n));
		const next = new Set(selected);
		if (allIn) {
			for (const n of names) next.delete(n);
		} else {
			for (const n of names) next.add(n);
		}
		selected = next;
	}

	function selectTemplate(t) {
		selectedTemplate = t;
	}

	async function handleDownload() {
		if (downloading) return;
		downloading = true;
		error = "";
		try {
			if (mode === "template" && selectedTemplate) {
				await downloadExcel(activeStockCode, null, selectedTemplate.templateId);
			} else {
				if (selected.size === 0) { downloading = false; return; }
				const mods = allSelected ? null : [...selected];
				await downloadExcel(activeStockCode, mods);
			}
		} catch (e) {
			error = e.message;
		}
		downloading = false;
	}

	async function handleSaveAsTemplate() {
		if (!newTemplateName.trim() || selected.size === 0) return;
		error = "";
		try {
			const sheets = [...selected].map(name => {
				const mod = modules.find(m => m.name === name);
				return { source: name, label: mod?.label || name };
			});
			await saveTemplate({
				name: newTemplateName.trim(),
				sheets,
				description: `${activeCorpName} 기준 커스텀 양식`,
			});
			newTemplateName = "";
			showNewTemplate = false;
			await loadTemplates();
		} catch (e) {
			error = e.message;
		}
	}

	async function handleDeleteTemplate(tid) {
		error = "";
		try {
			await deleteTemplate(tid);
			if (selectedTemplate?.templateId === tid) selectedTemplate = null;
			await loadTemplates();
		} catch (e) {
			error = e.message;
		}
	}

	let canDownload = $derived(
		activeStockCode && (
			mode === "template"
				? selectedTemplate !== null
				: selected.size > 0
		)
	);
</script>

<div class="rounded-xl border border-dl-border bg-dl-bg-card/60 backdrop-blur-sm overflow-hidden animate-fadeIn">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/50">
		<div class="flex items-center gap-2">
			<FileSpreadsheet size={16} class="text-dl-success" />
			<span class="text-[13px] font-medium text-dl-text">Excel 내보내기</span>
			{#if activeCorpName}
				<span class="text-[11px] text-dl-text-dim">— {activeCorpName}</span>
				<button
					class="text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
					onclick={() => { activeStockCode = null; activeCorpName = ""; modules = []; selected = new Set(); }}
				>
					변경
				</button>
			{/if}
		</div>
		<div class="flex items-center gap-1.5">
			<button
				class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"
				onclick={handleDownload}
				disabled={!canDownload || downloading || loading}
			>
				{#if downloading}
					<Loader2 size={12} class="animate-spin" />
					다운로드 중
				{:else}
					<Download size={12} />
					다운로드
				{/if}
			</button>
			{#if onClose}
				<button
					class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={onClose}
				>
					<X size={16} />
				</button>
			{/if}
		</div>
	</div>

	<!-- Mode Tabs -->
	<div class="flex border-b border-dl-border/30 px-4">
		<button
			class={cn(
				"px-3 py-2 text-[11px] font-medium border-b-2 transition-colors",
				mode === "template"
					? "border-dl-success text-dl-success"
					: "border-transparent text-dl-text-dim hover:text-dl-text-muted"
			)}
			onclick={() => mode = "template"}
		>
			<div class="flex items-center gap-1.5">
				<LayoutTemplate size={12} />
				템플릿
			</div>
		</button>
		<button
			class={cn(
				"px-3 py-2 text-[11px] font-medium border-b-2 transition-colors",
				mode === "custom"
					? "border-dl-success text-dl-success"
					: "border-transparent text-dl-text-dim hover:text-dl-text-muted"
			)}
			onclick={() => mode = "custom"}
		>
			<div class="flex items-center gap-1.5">
				<CheckSquare size={12} />
				직접 선택
			</div>
		</button>
	</div>

	<!-- Content -->
	<div class="px-4 py-3">
		{#if !activeStockCode}
			<!-- 종목 검색 -->
			<div class="relative">
				<div class="flex items-center gap-2 mb-2">
					<Search size={14} class="text-dl-text-dim flex-shrink-0" />
					<span class="text-[12px] text-dl-text-muted">종목을 검색하세요</span>
				</div>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="종목명 또는 종목코드 (예: 삼성전자, 005930)"
					class="w-full bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2.5 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-success/50 transition-colors"
					oninput={handleSearchInput}
					onkeydown={handleSearchKeydown}
					onblur={() => { setTimeout(() => { showSearchResults = false; }, 200); }}
				/>
				{#if searchLoading}
					<div class="absolute right-3 top-[calc(50%+10px)] -translate-y-1/2">
						<Loader2 size={14} class="animate-spin text-dl-text-dim" />
					</div>
				{/if}
				{#if showSearchResults && searchResults.length > 0}
					<div class="absolute left-0 right-0 top-full mt-1 z-10 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn max-h-[240px] overflow-y-auto">
						{#each searchResults as item, i}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div
								class={cn(
									"flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors",
									i === searchSelectedIdx ? "bg-dl-success/10 text-dl-text" : "text-dl-text-muted hover:bg-white/[0.03]"
								)}
								onmousedown={() => selectSearchResult(item)}
								onmouseenter={() => { searchSelectedIdx = i; }}
							>
								<div class="flex-1 min-w-0">
									<div class="text-[12px] font-medium truncate">{item.corpName}</div>
									<div class="text-[10px] text-dl-text-dim">{item.stockCode} · {item.market || ""}</div>
								</div>
								{#if item.sector}
									<span class="text-[10px] text-dl-text-dim flex-shrink-0">{item.sector}</span>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else if loading}
			<div class="flex items-center gap-2 py-4 justify-center text-[12px] text-dl-text-dim">
				<Loader2 size={14} class="animate-spin" />
				데이터 로드 중...
			</div>
		{:else if error}
			<div class="text-[12px] text-dl-primary-light py-2">{error}</div>
		{:else if mode === "template"}
			<!-- Template Mode -->
			<div class="space-y-2">
				{#each templates as t}
					<button
						class={cn(
							"w-full text-left px-3 py-2.5 rounded-lg border transition-all",
							selectedTemplate?.templateId === t.templateId
								? "border-dl-success/50 bg-dl-success/8"
								: "border-dl-border/50 hover:border-dl-border hover:bg-white/[0.02]"
						)}
						onclick={() => selectTemplate(t)}
					>
						<div class="flex items-center justify-between">
							<div>
								<span class={cn(
									"text-[12px] font-medium",
									selectedTemplate?.templateId === t.templateId ? "text-dl-success" : "text-dl-text"
								)}>
									{t.name}
								</span>
								<span class="text-[10px] text-dl-text-dim ml-2">{t.sheets?.length || 0}개 시트</span>
							</div>
							<div class="flex items-center gap-1">
								{#if t.templateId?.startsWith("preset_")}
									<span class="text-[9px] px-1.5 py-0.5 rounded bg-dl-text-dim/10 text-dl-text-dim">프리셋</span>
								{:else}
									<!-- svelte-ignore node_invalid_placement_ssr -->
									<span
										role="button"
										tabindex="0"
										class="p-1 rounded text-dl-text-dim hover:text-red-400 transition-colors cursor-pointer"
										onclick={(e) => { e.stopPropagation(); handleDeleteTemplate(t.templateId); }}
										onkeydown={(e) => { if (e.key === "Enter") { e.stopPropagation(); handleDeleteTemplate(t.templateId); } }}
										title="삭제"
									>
										<Trash2 size={11} />
									</span>
								{/if}
							</div>
						</div>
						{#if t.description}
							<div class="text-[10px] text-dl-text-dim mt-0.5">{t.description}</div>
						{/if}
						{#if selectedTemplate?.templateId === t.templateId && t.sheets?.length > 0}
							<div class="flex flex-wrap gap-1 mt-2">
								{#each t.sheets as s}
									<span class="px-1.5 py-0.5 rounded text-[9px] bg-dl-success/10 text-dl-success/80">
										{s.label || s.source}
									</span>
								{/each}
							</div>
						{/if}
					</button>
				{/each}
			</div>
		{:else if modules.length > 0}
			<!-- Custom Mode -->
			<div class="flex items-center justify-between mb-2">
				<button
					class="flex items-center gap-1.5 text-[11px] text-dl-text-muted hover:text-dl-text transition-colors"
					onclick={toggleAll}
				>
					{#if allSelected}
						<CheckSquare size={13} class="text-dl-success" />
					{:else}
						<Square size={13} />
					{/if}
					전체 선택
				</button>
				<div class="flex items-center gap-2">
					{#if !showNewTemplate}
						<button
							class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-success transition-colors disabled:opacity-40"
							onclick={() => showNewTemplate = true}
							disabled={selected.size === 0}
							title="현재 선택을 템플릿으로 저장"
						>
							<Save size={11} />
							템플릿 저장
						</button>
					{/if}
					<button
						class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
						onclick={() => expanded = !expanded}
					>
						{expanded ? "접기" : "펼치기"}
						{#if expanded}
							<ChevronUp size={12} />
						{:else}
							<ChevronDown size={12} />
						{/if}
					</button>
				</div>
			</div>

			<!-- Save as template -->
			{#if showNewTemplate}
				<div class="flex items-center gap-2 mb-3 p-2 rounded-lg bg-dl-success/5 border border-dl-success/20">
					<input
						type="text"
						class="flex-1 px-2 py-1 rounded text-[11px] bg-transparent border border-dl-border/50 text-dl-text placeholder:text-dl-text-dim focus:outline-none focus:border-dl-success/50"
						placeholder="템플릿 이름"
						bind:value={newTemplateName}
						onkeydown={(e) => e.key === "Enter" && handleSaveAsTemplate()}
					/>
					<button
						class="px-2 py-1 rounded text-[10px] bg-dl-success/20 text-dl-success hover:bg-dl-success/30 transition-colors disabled:opacity-40"
						onclick={handleSaveAsTemplate}
						disabled={!newTemplateName.trim()}
					>
						저장
					</button>
					<button
						class="p-1 rounded text-dl-text-dim hover:text-dl-text transition-colors"
						onclick={() => { showNewTemplate = false; newTemplateName = ""; }}
					>
						<X size={12} />
					</button>
				</div>
			{/if}

			<!-- Finance group -->
			{#if financeModules.length > 0}
				<div class="mb-2">
					<button
						class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors"
						onclick={() => toggleGroup(financeModules)}
					>
						재무제표
					</button>
					<div class="flex flex-wrap gap-1">
						{#each financeModules as m}
							<button
								class={cn(
									"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
									selected.has(m.name)
										? "border-dl-success/40 bg-dl-success/10 text-dl-success"
										: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
								)}
								onclick={() => toggle(m.name)}
							>
								{m.label}
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Other modules -->
			{#if otherModules.length > 0}
				<div>
					<button
						class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors"
						onclick={() => toggleGroup(otherModules)}
					>
						보고서/공시 ({otherModules.length})
					</button>
					{#if expanded}
						<div class="flex flex-wrap gap-1">
							{#each otherModules as m}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
										selected.has(m.name)
											? "border-dl-success/40 bg-dl-success/10 text-dl-success"
											: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
									)}
									onclick={() => toggle(m.name)}
								>
									{m.label}
								</button>
							{/each}
						</div>
					{:else}
						<div class="flex flex-wrap gap-1">
							{#each otherModules.slice(0, 6) as m}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
										selected.has(m.name)
											? "border-dl-success/40 bg-dl-success/10 text-dl-success"
											: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
									)}
									onclick={() => toggle(m.name)}
								>
									{m.label}
								</button>
							{/each}
							{#if otherModules.length > 6}
								<button
									class="px-2 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
									onclick={() => expanded = true}
								>
									+{otherModules.length - 6}개 더
								</button>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		{:else}
			<div class="text-[12px] text-dl-text-dim py-2">내보낼 수 있는 데이터가 없습니다</div>
		{/if}
	</div>
</div>
