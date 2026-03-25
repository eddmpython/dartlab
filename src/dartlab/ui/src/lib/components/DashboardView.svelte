<!--
	DashboardView — 인사이트 + 데이터 + 네트워크 통합 대시보드.
	3탭: 인사이트, 데이터, 네트워크.
-->
<script>
	import { BarChart3, Database, Users, Loader2, AlertCircle, Search } from "lucide-svelte";
	import { fetchCompanyInsights, fetchCompanyNetwork } from "$lib/api.js";
	import InsightDashboard from "./InsightDashboard.svelte";
	import NetworkGraph from "./NetworkGraph.svelte";
	import DataExplorer from "./DataExplorer.svelte";

	let {
		company = null,
		recentCompanies = [],
		toc = null,
		onCompanySelect = null,
		onNavigateTopic = null,
		onAskAboutModule = null,
		onNotify = null,
		onOpenSearch = null,
	} = $props();

	let activeTab = $state("insight"); // "insight" | "data" | "network"

	// Insight/Network 데이터
	let insightData = $state(null);
	let insightLoading = $state(false);
	let insightError = $state(null);
	let networkData = $state(null);
	let networkLoading = $state(false);
	let networkError = $state(null);
	let lastLoadedCode = null;

	const tabs = [
		{ id: "insight", icon: BarChart3, label: "인사이트" },
		{ id: "data", icon: Database, label: "데이터" },
		{ id: "network", icon: Users, label: "네트워크" },
	];

	$effect(() => {
		const code = company?.stockCode;
		if (!code || code === lastLoadedCode) return;
		lastLoadedCode = code;
		loadInsights(code);
		loadNetwork(code);
	});

	async function loadInsights(code) {
		insightLoading = true;
		insightError = null;
		try {
			insightData = await fetchCompanyInsights(code);
		} catch (e) {
			insightData = null;
			insightError = e?.message || "인사이트 데이터를 불러올 수 없습니다";
		}
		insightLoading = false;
	}

	async function loadNetwork(code) {
		networkLoading = true;
		networkError = null;
		try {
			networkData = await fetchCompanyNetwork(code);
		} catch (e) {
			networkData = null;
			networkError = e?.message || "네트워크 데이터를 불러올 수 없습니다";
		}
		networkLoading = false;
	}

	function handleInsightNavigate(topic) {
		onNavigateTopic?.(topic);
	}

	function handleRetry(type) {
		const code = company?.stockCode;
		if (!code) return;
		if (type === "insight") loadInsights(code);
		else if (type === "network") loadNetwork(code);
	}
</script>

<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark">
	{#if !company}
		<div class="flex flex-col items-center justify-center h-full gap-4 text-dl-text-dim px-8">
			<BarChart3 size={32} strokeWidth={1} class="opacity-20" />
			<p class="text-[13px]">종목을 선택하면 분석 대시보드를 표시합니다</p>
			{#if onOpenSearch}
				<button
					class="flex items-center gap-2 px-4 py-2 rounded-lg bg-dl-surface-card border border-dl-border/30 text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-border/50 transition-colors"
					onclick={onOpenSearch}
				>
					<Search size={13} />
					<span>종목 검색</span>
					<kbd class="ml-1 text-[10px] text-dl-text-dim opacity-60">Ctrl+K</kbd>
				</button>
			{/if}
		</div>
	{:else}
		<!-- 탭 헤더 -->
		<div class="dashboard-tab-bar">
			{#each tabs as tab}
				<button
					class="dashboard-tab {activeTab === tab.id ? 'active' : ''}"
					onclick={() => { activeTab = tab.id; }}
				>
					<svelte:component this={tab.icon} size={13} />
					<span>{tab.label}</span>
				</button>
			{/each}
		</div>

		<!-- 탭 콘텐츠 -->
		<div class="flex-1 overflow-y-auto min-h-0">
			{#if activeTab === "insight"}
				{#if insightError && !insightLoading}
					<div class="flex flex-col items-center justify-center h-48 gap-3 text-dl-text-dim">
						<AlertCircle size={20} class="text-dl-primary/60" />
						<p class="text-[12px]">{insightError}</p>
						<button
							class="px-3 py-1.5 rounded-md bg-dl-surface-card border border-dl-border/30 text-[11px] text-dl-text-muted hover:text-dl-text transition-colors"
							onclick={() => handleRetry("insight")}
						>재시도</button>
					</div>
				{:else}
					<div class="p-6 max-w-5xl mx-auto">
						<InsightDashboard
							data={insightData}
							loading={insightLoading}
							corpName={company.corpName || company.company || ""}
							{toc}
							onNavigateTopic={handleInsightNavigate}
						/>
					</div>
				{/if}
			{:else if activeTab === "data"}
				<DataExplorer
					selectedCompany={company}
					{recentCompanies}
					activeTab="explore"
					onSelectCompany={onCompanySelect}
					onAskAboutModule={onAskAboutModule}
					onNotify={onNotify}
					onChangeTab={() => {}}
					onClose={() => {}}
				/>
			{:else if activeTab === "network"}
				{#if networkError && !networkLoading}
					<div class="flex flex-col items-center justify-center h-48 gap-3 text-dl-text-dim">
						<AlertCircle size={20} class="text-dl-primary/60" />
						<p class="text-[12px]">{networkError}</p>
						<button
							class="px-3 py-1.5 rounded-md bg-dl-surface-card border border-dl-border/30 text-[11px] text-dl-text-muted hover:text-dl-text transition-colors"
							onclick={() => handleRetry("network")}
						>재시도</button>
					</div>
				{:else}
					<div class="p-6 max-w-5xl mx-auto">
						<NetworkGraph
							data={networkData}
							loading={networkLoading}
							centerCode={company?.stockCode}
							onNavigate={(code) => {
								if (code !== company?.stockCode) {
									onCompanySelect?.({ stockCode: code, corpName: code });
								}
							}}
						/>
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</div>
