<script>
	import { fetchCompanySections, fetchViewer } from "$lib/api.js";
	import { ChevronRight, ChevronDown, FileText, Loader2, BookOpen, BarChart3, Maximize2, Minimize2 } from "lucide-svelte";
	import { topicLabel, chapterLabel, romanToInt } from "$lib/viewer/topicLabels.js";
	import ViewerContent from "./viewer/ViewerContent.svelte";
	import "$lib/viewer/viewer.css";

	let { stockCode = null, onTopicChange = null } = $props();

	let sections = $state(null);
	let loading = $state(false);
	let expandedChapters = $state(new Set());
	let selectedTopic = $state(null);
	let selectedChapter = $state(null);
	let viewerDoc = $state(null);
	let contentLoading = $state(false);
	let isFullscreen = $state(false);
	let docCache = new Map();

	$effect(() => { if (stockCode) loadData(); });

	async function loadData() {
		loading = true;
		sections = null;
		selectedTopic = null;
		selectedChapter = null;
		viewerDoc = null;
		docCache = new Map();
		try {
			const secRes = await fetchCompanySections(stockCode);
			sections = secRes.payload;
			const tree = buildTocTree(sections?.rows);
			if (tree.length > 0) {
				expandedChapters = new Set([tree[0].chapter]);
				if (tree[0].topics.length > 0) {
					selectTopic(tree[0].topics[0].topic, tree[0].chapter);
				}
			}
		} catch (e) { console.error("viewer load error:", e); }
		loading = false;
	}

	async function selectTopic(topic, chapter) {
		if (selectedTopic === topic) return;
		selectedTopic = topic;
		selectedChapter = chapter || null;
		onTopicChange?.(topic, topicLabel(topic));
		if (docCache.has(topic)) {
			viewerDoc = docCache.get(topic);
			return;
		}
		viewerDoc = null;
		contentLoading = true;
		try {
			const doc = await fetchViewer(stockCode, topic);
			viewerDoc = doc;
			docCache.set(topic, doc);
		} catch (e) { console.error("viewer load error:", e); viewerDoc = null; }
		contentLoading = false;
	}

	async function handlePeriodChange(base, compare) {
		if (!selectedTopic) return;
		contentLoading = true;
		try {
			const doc = await fetchViewer(stockCode, selectedTopic, base, compare);
			viewerDoc = doc;
			docCache.set(`${selectedTopic}:${base}:${compare}`, doc);
		} catch (e) { console.error("period change error:", e); }
		contentLoading = false;
	}

	function toggleChapter(ch) {
		const next = new Set(expandedChapters);
		if (next.has(ch)) next.delete(ch); else next.add(ch);
		expandedChapters = next;
	}

	function buildTocTree(rows) {
		if (!rows) return [];
		const chapterMap = new Map();
		const seenTopics = new Set();
		for (const row of rows) {
			const ch = row.chapter || "";
			if (!chapterMap.has(ch)) chapterMap.set(ch, { chapter: ch, topics: [] });
			if (!seenTopics.has(row.topic)) {
				seenTopics.add(row.topic);
				chapterMap.get(ch).topics.push({ topic: row.topic, source: row.source || "docs" });
			}
		}
		return [...chapterMap.values()].sort((a, b) => romanToInt(a.chapter) - romanToInt(b.chapter));
	}

	function getTopicChapter(topic) {
		if (!sections?.rows) return null;
		return sections.rows.find(r => r.topic === topic)?.chapter || null;
	}
</script>

<div class="flex flex-col h-full font-sans bg-dl-bg-dark">
	{#if loading}
		<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim">
			<Loader2 size={18} class="animate-spin" />
			<span class="text-[13px]">공시 데이터 로딩 중...</span>
		</div>

	{:else if sections?.rows}
		<div class="flex flex-1 overflow-hidden min-h-0">
			<!-- 좌측 목차 -->
			{#if !isFullscreen}
			<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50">
				<div class="px-3 py-2.5 border-b border-dl-border/20">
					<div class="text-[11px] text-dl-text-dim">
						{buildTocTree(sections.rows).reduce((n, g) => n + g.topics.length, 0)}개 섹션
					</div>
				</div>
				{#each buildTocTree(sections.rows) as group}
					<div>
						<button
							class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
							onclick={() => toggleChapter(group.chapter)}
						>
							{#if expandedChapters.has(group.chapter)}
								<ChevronDown size={11} class="flex-shrink-0 opacity-40" />
							{:else}
								<ChevronRight size={11} class="flex-shrink-0 opacity-40" />
							{/if}
							<span class="truncate">{chapterLabel(group.chapter)}</span>
							<span class="ml-auto text-[9px] opacity-30 font-normal">{group.topics.length}</span>
						</button>
						{#if expandedChapters.has(group.chapter)}
							<div class="py-0.5">
								{#each group.topics as item}
									<button
										class="group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											{selectedTopic === item.topic
												? 'bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]'
												: 'text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent'}"
										onclick={() => selectTopic(item.topic, group.chapter)}
									>
										{#if item.source === "finance"}
											<BarChart3 size={11} class="flex-shrink-0 text-blue-400/40" />
										{:else if item.source === "report"}
											<BookOpen size={11} class="flex-shrink-0 text-emerald-400/40" />
										{:else}
											<FileText size={11} class="flex-shrink-0 opacity-30" />
										{/if}
										<span class="truncate flex-1">{topicLabel(item.topic)}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				{/each}
			</nav>
			{/if}

			<!-- 우측 본문 -->
			<main class="flex-1 overflow-y-auto min-w-0">
				{#if !selectedTopic}
					<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim">
						<FileText size={32} strokeWidth={1} class="opacity-20" />
						<p class="text-[13px]">좌측에서 섹션을 선택하세요</p>
					</div>
				{:else}
					<!-- topic 헤더 (sticky) -->
					<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center">
						<div class="flex-1 min-w-0">
							{#if selectedChapter || getTopicChapter(selectedTopic)}
								<div class="text-[10px] text-dl-text-dim/50 mb-0.5">{chapterLabel(selectedChapter || getTopicChapter(selectedTopic))}</div>
							{/if}
							<h3 class="text-[16px] font-semibold text-dl-text">{topicLabel(selectedTopic)}</h3>
						</div>
						<button
							class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"
							onclick={() => isFullscreen = !isFullscreen}
							title="{isFullscreen ? '목차 표시' : '전체화면'}"
						>
							{#if isFullscreen}
								<Minimize2 size={15} />
							{:else}
								<Maximize2 size={15} />
							{/if}
						</button>
					</div>

					{#if contentLoading}
						<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim">
							<Loader2 size={16} class="animate-spin" />
						</div>
					{:else}
						<article class="py-6 px-8">
							{#if viewerDoc}
								<ViewerContent doc={viewerDoc} onPeriodChange={handlePeriodChange} />
							{:else}
								<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>
							{/if}
						</article>
					{/if}
				{/if}
			</main>
		</div>

	{:else}
		<div class="flex items-center justify-center h-full text-dl-text-dim">
			<p class="text-[13px]">공시 데이터가 없습니다</p>
		</div>
	{/if}
</div>
