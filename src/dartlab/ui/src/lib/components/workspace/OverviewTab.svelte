<script>
	import { cn } from "$lib/utils.js";
	import { Database, Sparkles } from "lucide-svelte";

	let {
		selectedCompany = null,
		companyInfo = null,
		overviewLoading = false,
		overviewCards = [],
		overviewHighlights = [],
		overviewTrend = [],
		overviewNarrative = [],
		overviewSourceLabel = "",
		overviewError = "",
		overviewActions = [],
		availableSources = 0,
		availableCategoryCount = 0,
		recommendedModules = [],
		onSetTab,
		onSelectModule,
		formatCellValue,
		categoryLabel,
		getModuleDescription,
	} = $props();
</script>

{#if !selectedCompany}
	<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
		<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
		<div class="text-[13px] font-medium text-dl-text">회사별 워크스페이스 준비</div>
		<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
			회사를 먼저 선택하면 추후 대시보드가 들어갈 Overview 슬롯과 추천 모듈 요약을 바로 볼 수 있습니다.
		</div>
	</div>
{:else}
	<div class="space-y-3">
		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="flex items-start justify-between gap-3">
				<div>
					<div class="text-[14px] font-semibold text-dl-text">{companyInfo?.corpName || selectedCompany.corpName || selectedCompany.company || selectedCompany.stockCode}</div>
					<div class="mt-1 text-[10px] text-dl-text-dim">
						{companyInfo?.stockCode || selectedCompany.stockCode}
						{#if companyInfo?.market || selectedCompany.market} · {companyInfo?.market || selectedCompany.market}{/if}
						{#if companyInfo?.sector || selectedCompany.sector} · {companyInfo?.sector || selectedCompany.sector}{/if}
					</div>
				</div>
				<span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">Overview</span>
			</div>
			<div class="mt-3 grid grid-cols-2 gap-2">
				<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3">
					<div class="text-[10px] text-dl-text-dim">사용 가능 데이터</div>
					<div class="mt-1 text-[22px] font-semibold text-dl-text">{availableSources}</div>
				</div>
				<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3">
					<div class="text-[10px] text-dl-text-dim">활성 카테고리</div>
					<div class="mt-1 text-[22px] font-semibold text-dl-text">{availableCategoryCount}</div>
				</div>
			</div>
		</div>

		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="flex items-center gap-2 text-[12px] font-medium text-dl-text">
				<Sparkles size={13} class="text-dl-accent" />
				핵심 재무 카드
			</div>
			{#if overviewLoading}
				<div class="mt-3 space-y-2">
					<div class="skeleton-line w-full"></div>
					<div class="skeleton-line w-[82%]"></div>
					<div class="skeleton-line w-[68%]"></div>
				</div>
			{:else if overviewCards.length > 0}
				<div class="mt-3 grid grid-cols-2 gap-2">
					{#each overviewCards as card}
						<div class="rounded-xl bg-dl-bg-card/60 p-3">
							<div class="text-[10px] text-dl-text-dim">{card.label}</div>
							<div class="mt-1 text-[13px] font-semibold text-dl-text">{card.value}</div>
							<div class="mt-1 text-[9px] text-dl-text-dim">{card.period}</div>
						</div>
					{/each}
				</div>
				{#if overviewSourceLabel}
					<div class="mt-2 text-[10px] text-dl-text-dim">출처: {overviewSourceLabel}</div>
				{/if}
				{#if overviewTrend.length > 0}
					<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3">
						<div class="mb-2 text-[10px] uppercase tracking-wide text-dl-text-dim">매출 추세</div>
						<div class="flex items-end gap-2">
							{#each overviewTrend as point}
								<div class="flex flex-1 flex-col items-center gap-1">
									<div
										class="w-full rounded-t-md bg-gradient-to-t from-dl-primary to-dl-accent transition-all"
										style={`height: ${point.ratio || 8}px`}
										title={point.value === null ? "-" : formatCellValue(point.value, "원")}
									></div>
									<div class="text-[9px] text-dl-text-dim">{point.label}</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			{:else}
				<div class="mt-2 text-[11px] leading-relaxed text-dl-text-dim">
					핵심 재무 카드를 자동으로 만들 수 있는 시계열 데이터가 부족합니다. Explore에서 원본 모듈을 먼저 확인하는 흐름이 적합합니다.
				</div>
			{/if}
			{#if overviewError}
				<div class="mt-3 rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light">
					{overviewError}
				</div>
			{/if}
		</div>

		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 text-[12px] font-medium text-dl-text">Overview 노트</div>
			<div class="space-y-2">
				{#each overviewNarrative as line}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/40 px-3 py-2 text-[11px] leading-relaxed text-dl-text-muted">
						{line}
					</div>
				{/each}
			</div>
		</div>

		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 text-[12px] font-medium text-dl-text">읽기 포인트</div>
			<div class="space-y-2">
				{#each overviewHighlights as item}
					<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2 text-[11px] text-dl-text-muted">
						{item}
					</div>
				{/each}
			</div>
		</div>

		{#if overviewActions.length > 0}
			<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
				<div class="mb-2 text-[12px] font-medium text-dl-text">추천 액션</div>
				<div class="space-y-2">
					{#each overviewActions as action}
						<button
							class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"
							onclick={() => onSetTab?.(action.tab)}
						>
							<div class="text-[11px] font-medium text-dl-text">{action.label}</div>
							<div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim">{action.description}</div>
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 text-[12px] font-medium text-dl-text">추천 모듈</div>
			<div class="space-y-2">
				{#each recommendedModules as module}
					<button
						class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"
						onclick={() => onSelectModule?.(module)}
					>
						<div class="flex items-center justify-between gap-3">
							<div class="min-w-0">
								<div class="truncate text-[12px] font-medium text-dl-text">{module.label}</div>
								<div class="mt-0.5 text-[10px] text-dl-text-dim">{getModuleDescription(module)}</div>
							</div>
							<span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">
								{categoryLabel(module.category)}
							</span>
						</div>
					</button>
				{/each}
			</div>
		</div>

		<div class="flex gap-2">
			<button
				class="flex-1 rounded-xl bg-dl-primary/20 px-3 py-2 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30"
				onclick={() => onSetTab?.("explore")}
			>
				모듈 탐색
			</button>
			<button
				class="flex-1 rounded-xl border border-dl-border/60 px-3 py-2 text-[11px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-text"
				onclick={() => onSetTab?.("evidence")}
			>
				현재 근거 보기
			</button>
		</div>
	</div>
{/if}
