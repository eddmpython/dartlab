<script>
	import { Loader2, Star } from "lucide-svelte";
	import { summarizeDataReady } from "$lib/ai/dataReady.js";
	import AutocompleteInput from "./AutocompleteInput.svelte";

	let {
		onSend,
		inputText = $bindable(""),
		onCompanySelect,
		selectedCompany = null,
		suggestions = [],
		dataReady = null,
		suggestionLoading = false,
		watchlist = [],
		onWatchlistClick,
		onCommand,
	} = $props();

	const STARTERS = [
		"지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘",
		"EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘",
		"OpenDart와 OpenEdgar로 가능한 일을 비교해줘",
		"GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘",
	];

	const DEFAULT_COMPANY_PROMPTS = [
		"이 회사의 핵심 투자 포인트를 한눈에 정리해주세요",
		"최근 공시에서 꼭 읽어야 할 문서를 우선순위로 골라주세요",
		"재무건전성과 현금흐름을 함께 점검해주세요",
	];

	let dataReadyInfo = $derived(summarizeDataReady(dataReady));
	let promptChips = $derived(selectedCompany ? (suggestions.length > 0 ? suggestions : DEFAULT_COMPANY_PROMPTS) : STARTERS);
</script>

<div class="flex-1 flex flex-col items-center justify-center px-5">
	<div class="w-full max-w-[640px] flex flex-col items-center">
		<div class="relative mb-6">
			<div class="absolute inset-0 rounded-full blur-2xl opacity-30" style="background: radial-gradient(circle, rgba(234,70,71,0.5) 0%, rgba(251,146,60,0.2) 50%, transparent 70%); transform: scale(1.8);"></div>
			<img src="/avatar.png" alt="DartLab" class="relative w-14 h-14 rounded-full" />
		</div>

		{#if selectedCompany?.stockCode}
			<h1 class="text-xl font-bold text-dl-text mb-1">{selectedCompany.corpName || selectedCompany.company || selectedCompany.stockCode}</h1>
			<p class="text-[13px] text-dl-text-muted mb-3">종목이 선택되었습니다. 바로 질문하거나 추천 질문으로 시작하세요.</p>
			<div class="mb-3 flex flex-wrap items-center justify-center gap-2">
				<span class="rounded-full border border-dl-accent/20 bg-dl-accent/10 px-3 py-1 text-[11px] font-medium text-dl-accent-light">
					{selectedCompany.stockCode}
				</span>
				{#if selectedCompany.market}
					<span class="rounded-full border border-dl-border/50 bg-dl-bg-card/50 px-3 py-1 text-[11px] text-dl-text-dim">
						{selectedCompany.market}
					</span>
				{/if}
			</div>
			{#if dataReadyInfo}
				<div class="mb-4 w-full max-w-[560px] rounded-xl border px-3 py-2.5 text-left {dataReadyInfo.allReady ? 'border-emerald-500/20 bg-emerald-500/[0.06]' : 'border-amber-500/20 bg-amber-500/[0.06]'}">
					<div class="text-[10px] font-semibold uppercase tracking-[0.18em] {dataReadyInfo.allReady ? 'text-emerald-400' : 'text-amber-300'}">{dataReadyInfo.label}</div>
					<div class="mt-1.5 text-[12px] leading-relaxed text-dl-text-muted">{dataReadyInfo.summary}</div>
				</div>
			{/if}
		{:else}
			<h1 class="text-xl font-bold text-dl-text mb-1">무엇을 분석할까요?</h1>
			<p class="text-[13px] text-dl-text-muted mb-5">종목명이나 질문을 입력하세요</p>

			<!-- ── 관심종목 워치리스트 ── -->
			{#if watchlist.length > 0}
				<div class="mb-4 w-full max-w-[520px]">
					<div class="mb-1.5 flex items-center justify-center gap-1.5">
						<Star size={11} class="text-yellow-400 fill-yellow-400" />
						<span class="text-[9px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">관심종목</span>
					</div>
					<div class="flex flex-wrap justify-center gap-1.5">
						{#each watchlist as item}
							<button
								class="rounded-full border border-yellow-500/20 bg-yellow-500/5 px-2.5 py-1 text-[11px] text-dl-text-muted transition-colors hover:border-yellow-400/40 hover:text-yellow-300"
								onclick={() => onWatchlistClick?.(item)}
							>
								<span class="font-medium">{item.name}</span>
								<span class="text-dl-text-dim ml-1">{item.code}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<div class="mb-5 max-w-[520px] rounded-xl border border-dl-border/40 bg-dl-bg-card/40 px-3.5 py-2.5 text-left">
				<div class="text-[10px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div>
				<div class="mt-1.5 text-[12px] leading-relaxed text-dl-text-muted">
					재무 수치와 원문 근거를 동시에 확인합니다. DART/EDGAR 40개+ 모듈을 AI가 자동으로 조합합니다.
				</div>
			</div>
		{/if}

		<div class="w-full">
			<AutocompleteInput
				bind:inputText
				large={true}
				enableCompanyAutocomplete={!selectedCompany?.stockCode}
				placeholder={selectedCompany?.stockCode ? "예: 최근 공시에서 중요한 변화만 요약해줘" : "삼성전자 재무 건전성을 분석해줘..."}
				{onSend}
				{onCompanySelect}
				{onCommand}
			/>
			<!-- 단축키 힌트 -->
			<div class="flex items-center justify-center gap-3 mt-2 text-[10px] text-dl-text-dim/40">
				<span class="flex items-center gap-1">
					<kbd class="px-1 py-0.5 rounded border border-dl-border/30 bg-dl-bg-card/50 text-[9px] font-mono">Ctrl</kbd>
					<span>+</span>
					<kbd class="px-1 py-0.5 rounded border border-dl-border/30 bg-dl-bg-card/50 text-[9px] font-mono">K</kbd>
					<span class="ml-0.5">검색</span>
				</span>
				<span class="flex items-center gap-1">
					<kbd class="px-1 py-0.5 rounded border border-dl-border/30 bg-dl-bg-card/50 text-[9px] font-mono">/</kbd>
					<span class="ml-0.5">명령어</span>
				</span>
			</div>
		</div>

		<div class="mt-4 w-full">
			<div class="mb-1.5 flex items-center justify-center gap-2">
				<div class="text-[9px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">
					{selectedCompany?.stockCode ? "추천 질문" : "바로 시작"}
				</div>
				{#if suggestionLoading && selectedCompany?.stockCode}
					<span class="inline-flex items-center gap-1 text-[10px] text-dl-text-dim">
						<Loader2 size={10} class="animate-spin" />
						준비 중
					</span>
				{/if}
			</div>
			<div class="flex w-full flex-wrap justify-center gap-1.5">
				{#each promptChips as prompt}
					<button
						class="rounded-full border border-dl-border/50 bg-dl-bg-card/30 px-2.5 py-1 text-[11px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"
						onclick={() => onSend?.(prompt)}
					>
						{prompt}
					</button>
				{/each}
			</div>
		</div>
	</div>
</div>
