<!--
	ViewerNav — 공시뷰어 좌측 목차.
	toc API 응답을 chapter/topic 트리로 렌더링한다.
	활성 topic 자동 스크롤, 데이터 유무 인디케이터.
-->
<script>
	import { ChevronRight, ChevronDown, FileText, BarChart3, Loader2, Table2 } from "lucide-svelte";
	import { tick } from "svelte";

	let {
		toc = null,
		loading = false,
		selectedTopic = null,
		expandedChapters = new Set(),
		onSelectTopic = null,
		onToggleChapter = null,
	} = $props();

	const FINANCE_TOPICS = new Set(["BS", "IS", "CIS", "CF", "SCE", "ratios"]);

	function kindIcon(topic) {
		return FINANCE_TOPICS.has(topic) ? BarChart3 : FileText;
	}

	function topicIndicator(t) {
		if (t.tableCount > 0 && t.textCount > 0) return "both";
		if (t.tableCount > 0) return "table";
		if (t.textCount > 0) return "text";
		return "empty";
	}

	// 활성 topic 변경 시 자동 스크롤
	$effect(() => {
		if (selectedTopic) {
			tick().then(() => {
				const el = document.querySelector(".viewer-nav-active-item");
				if (el) el.scrollIntoView({ block: "nearest", behavior: "smooth" });
			});
		}
	});
</script>

<nav class="flex flex-col h-full min-h-0 overflow-y-auto py-2 px-1">
	{#if loading}
		<div class="flex flex-col items-center justify-center py-8 gap-2">
			<Loader2 size={18} class="animate-spin text-dl-text-dim" />
			<span class="text-[11px] text-dl-text-dim">목차 로딩 중...</span>
		</div>
	{:else if toc?.chapters}
		{#each toc.chapters as ch, ci}
			<div class="mb-0.5">
				<!-- Chapter header -->
				<button
					class="flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-left text-[11px] font-semibold uppercase tracking-wider text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"
					onclick={() => onToggleChapter?.(ch.chapter)}
				>
					{#if expandedChapters.has(ch.chapter)}
						<ChevronDown size={12} />
					{:else}
						<ChevronRight size={12} />
					{/if}
					<span class="truncate">{ch.chapter}</span>
					<span class="ml-auto text-[9px] text-dl-text-dim/60 font-mono">{ch.topics.length}</span>
				</button>

				<!-- Topics -->
				{#if expandedChapters.has(ch.chapter)}
					<div class="ml-2 border-l border-dl-border/20 pl-1">
						{#each ch.topics as t}
							{@const Icon = kindIcon(t.topic)}
							{@const indicator = topicIndicator(t)}
							{@const isActive = selectedTopic === t.topic}
							<button
								class="{isActive ? 'viewer-nav-active-item' : ''} viewer-nav-active flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left text-[12px] transition-colors {isActive
									? 'text-dl-text bg-dl-surface-active font-medium'
									: 'text-dl-text-muted hover:text-dl-text hover:bg-white/5'}"
								onclick={() => onSelectTopic?.(t.topic, ch.chapter)}
							>
								<Icon size={12} class="flex-shrink-0 opacity-50" />
								<span class="truncate">{t.label}</span>
								<span class="ml-auto flex items-center gap-0.5">
									{#if t.hasChanges}
										<span class="w-1.5 h-1.5 rounded-full bg-emerald-400/70" title="최근 변경"></span>
									{/if}
									{#if indicator === "table" || indicator === "both"}
										<Table2 size={9} class="text-dl-text-dim/40" />
									{/if}
									{#if t.tableCount > 0}
										<span class="text-[9px] text-dl-text-dim/60 font-mono">{t.tableCount}</span>
									{/if}
								</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	{:else}
		<div class="px-3 py-6 text-center text-[12px] text-dl-text-dim">
			종목을 선택하면 목차가 표시됩니다
		</div>
	{/if}
</nav>
