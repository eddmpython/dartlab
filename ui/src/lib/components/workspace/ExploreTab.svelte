<script>
	import { cn } from "$lib/utils.js";
	import {
		Search, Database, ChevronRight, ChevronDown, Table2, FileText, Loader2,
		Download, Languages
	} from "lucide-svelte";

	let {
		selectedCompany = null,
		sourceData = null,
		sourcesLoading = false,
		sourceError = "",
		categoryEntries = [],
		expandedCategories = $bindable(new Set()),
		activeModule = $bindable(null),
		previewData = null,
		previewLoading = false,
		previewHighlights = [],
		previewTextSummary = [],
		useKoreanLabel = $bindable(true),
		selectedModuleNames = $bindable(new Set()),
		selectedModuleList = [],
		selectedModuleRecords = [],
		excelDownloading = false,
		moduleQuery = $bindable(""),
		hasModuleFilter = false,
		availableSources = 0,
		onSelectModule,
		onToggleCategory,
		onToggleModuleSelection,
		onDownloadExcel,
		onAskAboutModule,
		formatCellValue,
		categoryLabel,
		categoryHint,
		categoryStats,
		getModuleDescription,
		getSuggestedQuestion,
		getAccountLabel,
		getAccountLevel,
		getUnit,
		isFinanceTimeseries,
		getDataColumns,
	} = $props();
</script>

{#if !selectedCompany}
	<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
		<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
		<div class="text-[13px] font-medium text-dl-text">회사를 선택하면 탐색이 시작됩니다</div>
		<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
			채팅 없이도 검색 후 모듈을 열어 표, 요약, 텍스트를 직접 확인할 수 있습니다.
		</div>
	</div>
{:else}
	<div class="space-y-3">
		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
				<div class="flex items-center justify-between gap-2">
					<div>
						<div class="text-[12px] font-medium text-dl-text">데이터 탐색</div>
						<div class="mt-0.5 text-[10px] text-dl-text-dim">카테고리를 열고 모듈을 선택하면 우측에서 바로 미리볼 수 있습니다.</div>
					</div>
					<div class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] text-dl-primary-light">
						{availableSources}개 모듈
					</div>
				</div>
			</div>

			<div class="sticky top-0 z-[8] mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/92 px-3 py-2 backdrop-blur-sm">
				<div>
					<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Download Actions</div>
					<div class="mt-1 text-[11px] text-dl-text-muted">
						{selectedModuleList.length > 0 ? `${selectedModuleList.length}개 모듈 선택됨` : "다운로드할 모듈을 선택하거나 전체 Excel을 받으세요."}
					</div>
				</div>
				<div class="mt-2 flex items-center gap-2">
					<button
						class="flex items-center gap-1 rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"
						onclick={() => onDownloadExcel?.(selectedModuleList)}
						disabled={excelDownloading || selectedModuleList.length === 0}
					>
						{#if excelDownloading && selectedModuleList.length > 0}
							<Loader2 size={11} class="animate-spin" />
						{:else}
							<Download size={11} />
						{/if}
						선택 다운로드
					</button>
					<button
						class="rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"
						onclick={() => selectedModuleNames = new Set()}
						disabled={selectedModuleList.length === 0}
					>
						선택 해제
					</button>
					<button
						class="flex items-center gap-1 rounded-lg bg-dl-success/10 px-2.5 py-1.5 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20 disabled:opacity-40"
						onclick={() => onDownloadExcel?.()}
						disabled={excelDownloading}
					>
						{#if excelDownloading && selectedModuleList.length === 0}
							<Loader2 size={11} class="animate-spin" />
						{:else}
							<Download size={11} />
						{/if}
						전체 Excel
					</button>
				</div>
			</div>

			{#if selectedModuleList.length > 0}
				<div class="mb-3 flex flex-wrap gap-1.5 rounded-xl border border-dl-border/40 bg-dl-bg-card/40 p-2">
					{#each selectedModuleRecords as module}
						<button
							class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[10px] text-dl-primary-light"
							onclick={() => selectedModuleNames = new Set(selectedModuleList.filter((item) => item !== module.name))}
						>
							{module.label} ×
						</button>
					{/each}
					<button
						class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
						onclick={() => selectedModuleNames = new Set()}
					>
						선택 해제
					</button>
				</div>
			{/if}

			<div class="space-y-2">
				<div class="relative">
					<Search size={12} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim" />
					<input
						type="text"
						bind:value={moduleQuery}
						placeholder="모듈 이름 또는 설명 필터"
						class="w-full rounded-xl border border-dl-border bg-dl-bg-card/50 py-2 pl-8 pr-3 text-[11px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"
					/>
				</div>
				{#if sourceError}
					<div class="rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light">
						{sourceError}
					</div>
				{/if}
				{#if sourcesLoading}
					<div class="flex items-center gap-2 py-4 text-[11px] text-dl-text-dim">
						<Loader2 size={14} class="animate-spin" />
						모듈 목록을 불러오는 중...
					</div>
				{:else if categoryEntries.length === 0 && hasModuleFilter}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30 px-3 py-4 text-[11px] text-dl-text-dim">
						필터와 일치하는 모듈이 없습니다.
					</div>
				{:else}
					{#each categoryEntries as [category, items]}
						<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30">
							<button
								class="flex w-full items-start gap-2 px-3 py-2.5 text-left"
								onclick={() => onToggleCategory?.(category)}
							>
								{#if expandedCategories.has(category)}
									<ChevronDown size={13} class="mt-0.5 flex-shrink-0 text-dl-text-dim" />
								{:else}
									<ChevronRight size={13} class="mt-0.5 flex-shrink-0 text-dl-text-dim" />
								{/if}
								<div class="min-w-0 flex-1">
									<div class="flex items-center justify-between gap-2">
										<span class="text-[11px] font-medium text-dl-text">{categoryLabel(category)}</span>
										<span class="text-[9px] text-dl-text-dim">{categoryStats(items)}</span>
									</div>
									<div class="mt-0.5 text-[10px] leading-relaxed text-dl-text-dim">{categoryHint(category)}</div>
								</div>
							</button>

							{#if expandedCategories.has(category)}
								<div class="space-y-1 border-t border-dl-border/30 px-2 pb-2 pt-1">
									{#each items as source}
										<div
											class={cn(
												"flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all",
												!source.available && "cursor-default opacity-35",
												source.available && activeModule?.name === source.name
													? "border-dl-primary/40 bg-dl-primary/[0.08]"
													: source.available
														? "border-transparent bg-white/[0.01] hover:border-dl-primary/20 hover:bg-white/[0.03]"
														: "border-transparent bg-transparent"
											)}
										>
											{#if source.available}
												<button
													type="button"
													class={cn(
														"flex h-4 w-4 items-center justify-center rounded border flex-shrink-0",
														selectedModuleNames.has(source.name)
															? "border-dl-primary bg-dl-primary/20 text-dl-primary-light"
															: "border-dl-border text-transparent"
													)}
													onclick={() => onToggleModuleSelection?.(source)}
													aria-label={`${source.label} 선택`}
												>
													✓
												</button>
											{:else}
												<span class="h-4 w-4 flex-shrink-0"></span>
											{/if}
											<button
												type="button"
												class="flex min-w-0 flex-1 items-center gap-2 text-left"
												disabled={!source.available}
												onclick={() => onSelectModule?.({ ...source, category })}
											>
												{#if source.dataType === "timeseries" || source.dataType === "table" || source.dataType === "dataframe"}
													<Table2 size={11} class="flex-shrink-0 text-dl-text-dim" />
												{:else}
													<FileText size={11} class="flex-shrink-0 text-dl-text-dim" />
												{/if}
												<div class="min-w-0 flex-1">
													<div class="truncate text-[11px] font-medium text-dl-text">{source.label}</div>
													<div class="mt-0.5 text-[10px] text-dl-text-dim">{getModuleDescription(source)}</div>
												</div>
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70">
			{#if !activeModule}
				<div class="p-4 text-center">
					<Table2 size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
					<div class="text-[13px] font-medium text-dl-text">모듈을 선택하세요</div>
					<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
						선택한 모듈은 표 미리보기와 함께 질문으로 이어갈 수 있습니다.
					</div>
				</div>
			{:else if previewLoading}
				<div class="flex items-center gap-2 p-4 text-[11px] text-dl-text-dim">
					<Loader2 size={14} class="animate-spin" />
					{activeModule.label} 미리보기 로딩 중...
				</div>
			{:else if previewData}
				<div class="border-b border-dl-border/40 px-4 py-3">
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="text-[13px] font-medium text-dl-text">{activeModule.label}</div>
							<div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim">{getModuleDescription(activeModule)}</div>
						</div>
						<div class="flex items-center gap-1.5">
							{#if isFinanceTimeseries()}
								<button
									class={cn(
										"rounded-lg px-2 py-1 text-[10px] transition-colors",
										useKoreanLabel ? "bg-dl-primary/15 text-dl-primary-light" : "text-dl-text-dim hover:bg-white/5 hover:text-dl-text"
									)}
									onclick={() => useKoreanLabel = !useKoreanLabel}
								>
									<Languages size={11} class="inline mr-1" />
									{useKoreanLabel ? "한글" : "EN"}
								</button>
							{/if}
							<button
								class="rounded-lg bg-dl-success/10 px-2 py-1 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20"
								onclick={() => onDownloadExcel?.([activeModule.name])}
							>
								<Download size={11} class="inline mr-1" />
								Excel
							</button>
						</div>
					</div>

					<div class="mt-3 flex flex-wrap gap-1.5">
						{#each previewHighlights as highlight}
							<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[9px] text-dl-text-muted">{highlight}</span>
						{/each}
					</div>

					<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3">
						<div class="text-[10px] uppercase tracking-wide text-dl-text-dim">추천 질문</div>
						<div class="mt-1 text-[11px] leading-relaxed text-dl-text-muted">{getSuggestedQuestion(activeModule)}</div>
						<button
							class="mt-3 rounded-lg bg-dl-primary/20 px-3 py-1.5 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30"
							onclick={onAskAboutModule}
						>
							이 데이터로 질문하기
						</button>
					</div>
				</div>

				{#if previewData.type === "table" && isFinanceTimeseries()}
					<div class="max-h-[360px] overflow-auto">
						<table class="w-full border-collapse text-[11px]">
							<thead class="sticky top-0 z-[5]">
								<tr>
									<th class="sticky left-0 z-[6] min-w-[180px] border-b border-r border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">계정명</th>
									{#each getDataColumns() as col}
										<th class="min-w-[96px] border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-right text-[10px] font-medium text-dl-text-muted">{col}</th>
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
												"sticky left-0 border-b border-r border-dl-border/10 bg-dl-bg-card/95 px-3 py-1.5 whitespace-nowrap",
												level === 1 && "font-semibold text-dl-text",
												level === 2 && "text-dl-text-muted",
												level >= 3 && "text-dl-text-dim"
											)}
											style={`padding-left: ${8 + (level - 1) * 12}px`}
										>
											{getAccountLabel(snakeId)}
										</td>
										{#each getDataColumns() as col}
											{@const val = row[col]}
											<td class={cn(
												"border-b border-dl-border/10 px-3 py-1.5 text-right font-mono text-[10px]",
												val === null || val === undefined ? "text-dl-text-dim/30" :
												typeof val === "number" && val < 0 ? "text-dl-primary-light" : "text-dl-accent-light"
											)}>
												{formatCellValue(val, getUnit())}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else if previewData.type === "table"}
					<div class="max-h-[360px] overflow-auto">
						<table class="w-full border-collapse text-[11px]">
							<thead class="sticky top-0 z-[5]">
								<tr>
									{#each previewData.columns as col}
										<th class="border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">{col}</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each previewData.rows as row}
									<tr class="hover:bg-white/[0.02]">
										{#each previewData.columns as col}
											{@const val = row[col]}
											<td class={cn(
												"border-b border-dl-border/10 px-3 py-1.5 whitespace-nowrap",
												typeof val === "number" ? "text-right font-mono text-[10px] text-dl-accent-light" : "text-dl-text-muted"
											)}>
												{formatCellValue(val, getUnit())}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else if previewData.type === "dict"}
					<div class="space-y-1.5 p-4">
						{#each Object.entries(previewData.data || {}) as [key, value]}
							<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2">
								<div class="text-[10px] text-dl-text-dim">{key}</div>
								<div class="mt-1 text-[11px] text-dl-text-muted">{value ?? "-"}</div>
							</div>
						{/each}
					</div>
				{:else if previewData.type === "text"}
					<div class="p-4">
						{#if previewTextSummary.length > 0}
							<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 p-3">
								<div class="mb-2 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">핵심 문장</div>
								<div class="space-y-2">
									{#each previewTextSummary as sentence}
										<div class="text-[11px] leading-relaxed text-dl-text-muted">{sentence}</div>
									{/each}
								</div>
							</div>
						{/if}
						<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{previewData.text}</pre>
					</div>
				{:else if previewData.type === "error"}
					<div class="p-4 text-[11px] text-dl-primary-light">{previewData.error || "데이터를 불러올 수 없습니다."}</div>
				{:else}
					<div class="p-4">
						<pre class="whitespace-pre-wrap text-[11px] text-dl-text-muted">{previewData.data || JSON.stringify(previewData, null, 2)}</pre>
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}
