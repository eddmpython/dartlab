<!--
	종목 검색 모달 — Cmd+K / Ctrl+K Spotlight 스타일.
-->
<script>
	import { Search, FileText } from "lucide-svelte";
	import { searchCompany as searchCompanyApi } from "$lib/api.js";
	import { cn } from "$lib/utils.js";

	let { open = $bindable(false), recentCompanies = [], onSelect } = $props();

	let searchText = $state("");
	let results = $state([]);
	let selectedIdx = $state(-1);
	let debounceTimer = null;
	let inputEl = $state(null);

	$effect(() => {
		if (!open || !inputEl) return;
		requestAnimationFrame(() => inputEl?.focus());
	});

	// 열릴 때 초기화
	$effect(() => {
		if (open) {
			searchText = "";
			results = [];
			selectedIdx = -1;
		}
	});

	function handleInput() {
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
		const items = results.length > 0 ? results : recentCompanies;
		if (e.key === "ArrowDown") { e.preventDefault(); selectedIdx = Math.min(selectedIdx + 1, items.length - 1); }
		else if (e.key === "ArrowUp") { e.preventDefault(); selectedIdx = Math.max(selectedIdx - 1, -1); }
		else if (e.key === "Enter" && selectedIdx >= 0 && items[selectedIdx]) {
			e.preventDefault();
			selectItem(items[selectedIdx]);
		}
		else if (e.key === "Escape") { open = false; }
	}

	function selectItem(item) {
		open = false;
		searchText = "";
		results = [];
		selectedIdx = -1;
		onSelect?.(item);
	}
</script>

{#if open}
	<div
		class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) open = false; }}
		role="presentation"
	>
		<div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden">
			<!-- 검색 입력 -->
			<div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40">
				<Search size={18} class="text-dl-text-dim flex-shrink-0" />
				<input
					bind:this={inputEl}
					type="text"
					bind:value={searchText}
					placeholder="종목명 또는 종목코드 검색..."
					class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"
					oninput={handleInput}
					onkeydown={handleKeydown}
				/>
				<kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd>
			</div>

			<!-- 결과 목록 -->
			<div class="max-h-[50vh] overflow-y-auto">
				{#if results.length > 0}
					<div class="px-3 pt-2 pb-1">
						<div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div>
					</div>
					{#each results as item, i}
						<button
							class={cn(
								"flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",
								i === selectedIdx ? "bg-dl-primary/10" : "hover:bg-white/[0.03]"
							)}
							onclick={() => selectItem(item)}
							onmouseenter={() => { selectedIdx = i; }}
						>
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
						</button>
					{/each}
				{:else if searchText.trim().length === 0 && recentCompanies.length > 0}
					<div class="px-3 pt-2 pb-1">
						<div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div>
					</div>
					{#each recentCompanies as item, i}
						<button
							class={cn(
								"flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",
								i === selectedIdx ? "bg-dl-primary/10" : "hover:bg-white/[0.03]"
							)}
							onclick={() => selectItem(item)}
							onmouseenter={() => { selectedIdx = i; }}
						>
							<div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0">
								{(item.corpName || "?").charAt(0)}
							</div>
							<div class="flex-1 min-w-0">
								<div class="text-[14px] font-medium text-dl-text truncate">{item.corpName}</div>
								<div class="text-[11px] text-dl-text-dim">{item.stockCode} · {item.market || ""}</div>
							</div>
						</button>
					{/each}
				{:else if searchText.trim().length > 0}
					<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">
						검색 결과가 없습니다
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim">
						<Search size={24} class="mb-2 opacity-40" />
						<div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div>
						<div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div>
					</div>
				{/if}
			</div>

			<!-- 하단 힌트 -->
			<div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim">
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span>
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span>
				<span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span>
			</div>
		</div>
	</div>
{/if}
