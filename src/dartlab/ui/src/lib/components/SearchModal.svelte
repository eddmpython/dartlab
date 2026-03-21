<!--
	커맨드 팔레트 — Cmd+K / Ctrl+K.
	종목 검색 + 빠른 액션 통합. ">" prefix로 액션 모드.
-->
<script>
	import {
		Search, FileText, Plus, MessageSquare, BookOpen,
		Settings, Download, ArrowRight,
	} from "lucide-svelte";
	import { searchCompany as searchCompanyApi } from "$lib/api.js";
	import { cn } from "$lib/utils.js";

	let {
		open = $bindable(false),
		recentCompanies = [],
		onSelect,
		onAction,  // (actionId: string) => void
	} = $props();

	let searchText = $state("");
	let results = $state([]);
	let selectedIdx = $state(-1);
	let debounceTimer = null;
	let inputEl = $state(null);

	// 빠른 액션 정의
	const ACTIONS = [
		{ id: "newChat", label: "새 대화", hint: "Ctrl+N", icon: Plus, group: "대화" },
		{ id: "viewChat", label: "Chat 뷰로 전환", hint: "1", icon: MessageSquare, group: "탐색" },
		{ id: "viewViewer", label: "Viewer 뷰로 전환", hint: "2", icon: BookOpen, group: "탐색" },
		{ id: "openSettings", label: "설정 열기", hint: "", icon: Settings, group: "설정" },
		{ id: "exportChat", label: "대화 내보내기", hint: "", icon: Download, group: "대화" },
	];

	// ">" prefix → 액션 모드
	let isActionMode = $derived(searchText.trimStart().startsWith(">"));
	let actionQuery = $derived(isActionMode ? searchText.trimStart().slice(1).trim().toLowerCase() : "");

	let filteredActions = $derived(
		isActionMode
			? (actionQuery
				? ACTIONS.filter(a => a.label.toLowerCase().includes(actionQuery))
				: ACTIONS)
			: []
	);

	// 현재 표시 아이템 목록 (통합 인덱스)
	let displayItems = $derived.by(() => {
		if (isActionMode) return filteredActions.map(a => ({ type: "action", ...a }));
		if (results.length > 0) return results.map(r => ({ type: "company", ...r }));
		if (searchText.trim().length === 0) {
			const items = [];
			// 빠른 액션 (상위 3개)
			for (const a of ACTIONS.slice(0, 3)) items.push({ type: "action", ...a });
			// 최근 종목
			for (const c of recentCompanies) items.push({ type: "company", ...c });
			return items;
		}
		return [];
	});

	$effect(() => {
		if (!open || !inputEl) return;
		requestAnimationFrame(() => inputEl?.focus());
	});

	$effect(() => {
		if (open) {
			searchText = "";
			results = [];
			selectedIdx = -1;
		}
	});

	function handleInput() {
		selectedIdx = -1;
		if (isActionMode) return;  // 액션 모드는 API 호출 불필요

		if (debounceTimer) clearTimeout(debounceTimer);
		if (searchText.trim().length >= 1) {
			debounceTimer = setTimeout(async () => {
				try {
					const data = await searchCompanyApi(searchText.trim());
					results = data.results?.slice(0, 8) || [];
				} catch { results = []; }
			}, 250);
		} else {
			results = [];
		}
	}

	function handleKeydown(e) {
		if (e.key === "ArrowDown") {
			e.preventDefault();
			selectedIdx = Math.min(selectedIdx + 1, displayItems.length - 1);
		} else if (e.key === "ArrowUp") {
			e.preventDefault();
			selectedIdx = Math.max(selectedIdx - 1, -1);
		} else if (e.key === "Enter" && selectedIdx >= 0 && displayItems[selectedIdx]) {
			e.preventDefault();
			executeItem(displayItems[selectedIdx]);
		} else if (e.key === "Escape") {
			open = false;
		}
	}

	function executeItem(item) {
		open = false;
		searchText = "";
		results = [];
		selectedIdx = -1;
		if (item.type === "action") {
			onAction?.(item.id);
		} else {
			onSelect?.(item);
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) open = false; }}
		role="dialog"
		aria-modal="true"
		aria-label="커맨드 팔레트"
	>
		<div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden" role="listbox">
			<!-- 검색 입력 -->
			<div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40">
				<Search size={18} class="text-dl-text-dim flex-shrink-0" />
				<input
					bind:this={inputEl}
					type="text"
					bind:value={searchText}
					placeholder={isActionMode ? "액션 검색..." : "종목 검색 또는 > 입력으로 액션..."}
					class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"
					oninput={handleInput}
					onkeydown={handleKeydown}
				/>
				{#if isActionMode}
					<span class="px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-accent bg-dl-accent/10 border border-dl-accent/20">액션</span>
				{/if}
				<kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd>
			</div>

			<!-- 결과 목록 -->
			<div class="max-h-[50vh] overflow-y-auto">
				{#if displayItems.length > 0}
					{@const hasActions = displayItems.some(i => i.type === "action")}
					{@const hasCompanies = displayItems.some(i => i.type === "company")}

					{#if !isActionMode && hasActions && searchText.trim().length === 0}
						<div class="px-3 pt-2 pb-1">
							<div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">빠른 액션</div>
						</div>
					{/if}

					{#each displayItems as item, i}
						{@const isFirstCompany = item.type === "company" && (i === 0 || displayItems[i - 1]?.type !== "company")}
						{#if isFirstCompany && !isActionMode}
							<div class="px-3 pt-2 pb-1">
								<div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">
									{results.length > 0 ? "검색 결과" : "최근 조회"}
								</div>
							</div>
						{/if}

						<button
							style="--stagger-index: {i}"
							class={cn(
								"flex items-center gap-3 w-full px-5 py-2.5 text-left transition-colors animate-stagger-in",
								i === selectedIdx ? "bg-dl-primary/10" : "hover:bg-white/[0.03]"
							)}
							onclick={() => executeItem(item)}
							onmouseenter={() => { selectedIdx = i; }}
							role="option"
							aria-selected={i === selectedIdx}
						>
							{#if item.type === "action"}
								<div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center flex-shrink-0">
									<svelte:component this={item.icon} size={14} class="text-dl-text-muted" />
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-[14px] font-medium text-dl-text">{item.label}</div>
								</div>
								{#if item.hint}
									<kbd class="px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/40 bg-dl-bg-darker">{item.hint}</kbd>
								{/if}
								<ArrowRight size={12} class="text-dl-text-dim flex-shrink-0" />
							{:else}
								<div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0">
									{(item.corpName || "?").charAt(0)}
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-[14px] font-medium text-dl-text truncate">{item.corpName}</div>
									<div class="text-[11px] text-dl-text-dim">{item.stockCode} · {item.market || ""}{item.sector ? ` · ${item.sector}` : ""}</div>
								</div>
								<div class="flex items-center gap-2 flex-shrink-0">
									<span class="text-[10px] text-dl-text-dim">공시 보기</span>
									<FileText size={14} class="text-dl-text-dim" />
								</div>
							{/if}
						</button>
					{/each}
				{:else if searchText.trim().length > 0 && !isActionMode}
					<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">
						검색 결과가 없습니다
					</div>
				{:else if isActionMode && filteredActions.length === 0}
					<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">
						일치하는 액션이 없습니다
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim">
						<Search size={24} class="mb-2 opacity-40" />
						<div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div>
						<div class="text-[11px] mt-1 opacity-60">> 입력으로 액션 실행</div>
					</div>
				{/if}
			</div>

			<!-- 하단 힌트 -->
			<div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim">
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span>
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span>
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">></kbd> 액션</span>
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span>
			</div>
		</div>
	</div>
{/if}
