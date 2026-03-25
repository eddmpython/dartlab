<!--
	CompanyContextBar — 상단 종목 맥락 바.
	모든 Activity에서 공통으로 보이며, 현재 선택된 종목 + 최근 종목 + 검색/외부링크.
-->
<script>
	import {
		Search, FileText, Coffee, Github, X, ChevronDown,
		Loader2, AlertCircle, Settings, Building2, Clock,
	} from "lucide-svelte";

	let {
		selectedCompany = null,
		recentCompanies = [],
		onCompanySelect = null,
		onOpenSearch = null,
		onOpenSettings = null,
		// Provider
		providerLabel = null,
		activeModel = null,
		providerAvailable = false,
		statusLoading = false,
		noProvider = false,
		// Version
		version = "",
		isMobile = false,
	} = $props();

	let showRecent = $state(false);

	function handleCompanyClick() {
		if (recentCompanies.length > 0) {
			showRecent = !showRecent;
		}
	}

	function selectRecent(company) {
		showRecent = false;
		onCompanySelect?.(company);
	}

	function handleKeydown(e) {
		if (e.key === "Escape" && showRecent) {
			showRecent = false;
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if !isMobile}
<div class="context-bar">
	<div class="context-bar-left">
		<!-- Company chip -->
		{#if selectedCompany}
			<div class="relative">
				<button
					class="context-bar-company"
					onclick={handleCompanyClick}
					aria-expanded={showRecent}
					aria-haspopup="menu"
				>
					<Building2 size={13} class="opacity-50" />
					<span class="font-medium">{selectedCompany.corpName || selectedCompany.company}</span>
					<span class="context-bar-code">{selectedCompany.stockCode}</span>
					{#if recentCompanies.length > 1}
						<ChevronDown size={11} class="opacity-40" />
					{/if}
				</button>
				{#if showRecent}
					<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
					<div class="fixed inset-0 z-40" onclick={() => { showRecent = false; }}></div>
					<div class="context-bar-dropdown" role="menu">
						{#each recentCompanies.filter(c => c.stockCode !== selectedCompany?.stockCode) as rc}
							<button
								class="context-bar-dropdown-item"
								role="menuitem"
								onclick={() => selectRecent(rc)}
							>
								<Clock size={11} class="opacity-30 flex-shrink-0" />
								<span class="truncate">{rc.corpName || rc.company}</span>
								<span class="text-[10px] font-mono opacity-40 ml-auto">{rc.stockCode}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<span class="text-[11px] text-dl-text-dim">종목을 선택하세요</span>
		{/if}
	</div>

	<div class="context-bar-right">
		<button
			class="context-bar-icon"
			onclick={onOpenSearch}
			title="종목 검색 (Ctrl+K)"
		>
			<Search size={14} />
		</button>
		<a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer"
			class="context-bar-icon" title="Documentation">
			<FileText size={14} />
		</a>
		<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer"
			class="context-bar-icon" title="GitHub">
			<Github size={14} />
		</a>
		<a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer"
			class="context-bar-icon coffee" title="Buy me a coffee">
			<Coffee size={14} />
		</a>
	</div>
</div>
{:else}
<!-- 모바일: 간소 context bar -->
<div class="context-bar-mobile">
	{#if selectedCompany}
		<div class="flex items-center gap-1.5 min-w-0">
			<Building2 size={12} class="opacity-50 flex-shrink-0" />
			<span class="text-[11px] font-medium text-dl-text truncate">{selectedCompany.corpName || selectedCompany.company}</span>
			<span class="text-[9px] font-mono text-dl-text-dim flex-shrink-0">{selectedCompany.stockCode}</span>
		</div>
	{/if}
	<button
		class="context-bar-icon"
		onclick={onOpenSearch}
		title="종목 검색"
	>
		<Search size={14} />
	</button>
</div>
{/if}
