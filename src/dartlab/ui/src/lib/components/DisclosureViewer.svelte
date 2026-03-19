<!--
	DisclosureViewer — 공시 뷰어 메인 레이아웃.
	좌측: ViewerNav (목차)
	우측: TopicRenderer (블록 렌더링)
	상단: 검색 바
-->
<script>
	import { Loader2, FileText, Search, X, AlertCircle } from "lucide-svelte";
	import { fetchCompanySearch } from "$lib/api.js";
	import ViewerNav from "./ViewerNav.svelte";
	import TopicRenderer from "./TopicRenderer.svelte";

	let {
		viewer = null,   // viewer store
		company = null,  // selected company
		onAskAI = null,  // (text) => void — AI에게 물어보기 콜백
		onTopicChange = null, // (topic, label) => void — workspace 동기화
	} = $props();

	// 모바일 TOC 드로어
	let mobileNavOpen = $state(false);
	let isMobileViewer = $state(false);

	function checkMobileViewer() {
		isMobileViewer = typeof window !== "undefined" && window.innerWidth <= 768;
	}

	$effect(() => {
		checkMobileViewer();
		window.addEventListener("resize", checkMobileViewer);
		return () => window.removeEventListener("resize", checkMobileViewer);
	});

	// 뷰어 내 검색
	let searchOpen = $state(false);
	let searchQuery = $state("");
	let searchInput = $state(null);

	function toggleSearch() {
		searchOpen = !searchOpen;
		if (searchOpen) {
			requestAnimationFrame(() => searchInput?.focus());
		} else {
			searchQuery = "";
		}
	}

	// company 변경 시 자동 로드
	$effect(() => {
		if (company?.stockCode && viewer) {
			viewer.loadCompany(company.stockCode);
		}
	});

	// topic 변경 시 workspace에 동기화
	$effect(() => {
		if (viewer?.selectedTopic && viewer?.topicData) {
			onTopicChange?.(viewer.selectedTopic, viewer.topicData.topicLabel || viewer.selectedTopic);
		}
	});

	// 검색 결과
	let searchResults = $state(null);
	let searchLoading = $state(false);
	let searchDebounce = null;

	// 전체 topic 플랫 리스트 (키보드 탐색용)
	function flatTopics() {
		if (!viewer?.toc?.chapters) return [];
		const flat = [];
		for (const ch of viewer.toc.chapters) {
			for (const t of ch.topics) {
				flat.push({ topic: t.topic, chapter: ch.chapter });
			}
		}
		return flat;
	}

	// 키보드 단축키
	function handleKeydown(e) {
		if (e.key === "f" && (e.ctrlKey || e.metaKey) && company) {
			e.preventDefault();
			toggleSearch();
		}
		if (e.key === "Escape" && searchOpen) {
			searchOpen = false;
			searchQuery = "";
			searchResults = null;
		}
		// ↑↓ topic 탐색 (검색 열려있을 때 제외)
		if (!searchOpen && (e.key === "ArrowUp" || e.key === "ArrowDown") && viewer?.selectedTopic) {
			const flat = flatTopics();
			const idx = flat.findIndex(t => t.topic === viewer.selectedTopic);
			if (idx < 0) return;
			const next = e.key === "ArrowDown" ? idx + 1 : idx - 1;
			if (next >= 0 && next < flat.length) {
				e.preventDefault();
				viewer.selectTopic(flat[next].topic, flat[next].chapter);
			}
		}
	}

	// 검색 실행 (toc 라벨 + 서버 텍스트 병합)
	$effect(() => {
		const q = searchQuery.trim();
		if (!q || !company?.stockCode) {
			searchResults = null;
			return;
		}

		// toc 라벨 즉시 필터 (로컬)
		const localResults = [];
		if (viewer?.toc?.chapters) {
			const qLower = q.toLowerCase();
			for (const ch of viewer.toc.chapters) {
				for (const t of ch.topics) {
					if (t.label.toLowerCase().includes(qLower) || t.topic.toLowerCase().includes(qLower)) {
						localResults.push({ topic: t.topic, label: t.label, chapter: ch.chapter, snippet: "", matchCount: 0, source: "toc" });
					}
				}
			}
		}
		searchResults = localResults.length > 0 ? localResults : null;

		// 서버 텍스트 검색 (debounced)
		clearTimeout(searchDebounce);
		if (q.length >= 2) {
			searchLoading = true;
			searchDebounce = setTimeout(async () => {
				try {
					const res = await fetchCompanySearch(company.stockCode, q);
					if (searchQuery.trim() !== q) return; // stale
					const serverResults = (res.results || []).map(r => ({ ...r, source: "text" }));
					// 로컬 결과와 병합 (중복 제거)
					const seen = new Set(localResults.map(r => r.topic));
					const merged = [...localResults, ...serverResults.filter(r => !seen.has(r.topic))];
					searchResults = merged.length > 0 ? merged : null;
				} catch {
					// 서버 검색 실패 — 로컬 결과만 유지
				}
				searchLoading = false;
			}, 300);
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="flex h-full min-h-0 bg-dl-bg-dark relative">
	<!-- Mobile: TOC drawer overlay -->
	{#if isMobileViewer && mobileNavOpen}
		<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
		<div
			class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
			onclick={() => { mobileNavOpen = false; }}
		></div>
	{/if}

	<!-- Left: TOC nav (desktop: sidebar, mobile: drawer) -->
	<div
		class="{isMobileViewer
			? `fixed top-0 left-0 bottom-0 z-50 w-64 transition-transform duration-200 ${mobileNavOpen ? 'translate-x-0' : '-translate-x-full'}`
			: 'flex-shrink-0 w-56'} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark"
	>
		<div class="h-full flex flex-col">
			<!-- Company header -->
			<div class="px-3 py-2 border-b border-dl-border/20 flex-shrink-0">
				{#if company}
					<div class="flex items-center justify-between">
						<div class="min-w-0">
							<div class="text-[12px] font-semibold text-dl-text truncate">{company.corpName || company.company}</div>
							<div class="text-[10px] font-mono text-dl-text-dim">{company.stockCode}</div>
						</div>
						<div class="flex items-center gap-0.5 flex-shrink-0">
							<button
								class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"
								onclick={toggleSearch}
								title="검색 (Ctrl+F)"
							>
								<Search size={12} />
							</button>
							{#if isMobileViewer}
								<button
									class="p-1 rounded-md text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"
									onclick={() => { mobileNavOpen = false; }}
								>
									<X size={12} />
								</button>
							{/if}
						</div>
					</div>
				{:else}
					<div class="text-[12px] text-dl-text-dim">종목 미선택</div>
				{/if}
			</div>

			<!-- Search bar -->
			{#if searchOpen}
				<div class="px-2 py-1.5 border-b border-dl-border/20 flex-shrink-0">
					<div class="flex items-center gap-1 bg-dl-bg-darker rounded-md border border-dl-border/30 px-2 py-1">
						<Search size={11} class="text-dl-text-dim flex-shrink-0" />
						<input
							bind:this={searchInput}
							bind:value={searchQuery}
							placeholder="topic 검색..."
							class="flex-1 bg-transparent text-[11px] text-dl-text outline-none placeholder:text-dl-text-dim min-w-0"
						/>
						{#if searchQuery}
							<button class="text-dl-text-dim hover:text-dl-text" onclick={() => { searchQuery = ""; }}>
								<X size={10} />
							</button>
						{/if}
					</div>
					{#if searchResults || searchLoading}
						<div class="mt-1 max-h-48 overflow-y-auto">
							{#if searchLoading && !searchResults}
								<div class="flex items-center justify-center py-2 gap-1">
									<Loader2 size={10} class="animate-spin text-dl-text-dim" />
									<span class="text-[10px] text-dl-text-dim">검색 중...</span>
								</div>
							{:else if searchResults && searchResults.length === 0}
								<div class="text-[10px] text-dl-text-dim py-2 text-center">결과 없음</div>
							{:else if searchResults}
								{#each searchResults.slice(0, 20) as t}
									<button
										class="w-full text-left px-2 py-1 text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 rounded transition-colors"
										onclick={() => {
											viewer?.selectTopic(t.topic, t.chapter);
											searchOpen = false;
											searchQuery = "";
											searchResults = null;
										}}
									>
										<div class="truncate">
											<span class="text-dl-text-dim/60 text-[9px]">{t.chapter || ""}</span>
											<span class="ml-1">{t.label}</span>
										</div>
										{#if t.snippet}
											<div class="text-[10px] text-dl-text-dim truncate mt-0.5">{t.snippet}</div>
										{/if}
									</button>
								{/each}
								{#if searchLoading}
									<div class="flex items-center justify-center py-1">
										<Loader2 size={9} class="animate-spin text-dl-text-dim" />
									</div>
								{/if}
							{/if}
						</div>
					{/if}
				</div>
			{/if}

			<ViewerNav
				toc={viewer?.toc}
				loading={viewer?.tocLoading}
				selectedTopic={viewer?.selectedTopic}
				expandedChapters={viewer?.expandedChapters}
				onSelectTopic={(topic, chapter) => {
					viewer?.selectTopic(topic, chapter);
					if (isMobileViewer) mobileNavOpen = false;
				}}
				onToggleChapter={(chapter) => viewer?.toggleChapter(chapter)}
			/>
		</div>
	</div>

	<!-- Right: Content -->
	<div class="flex-1 min-w-0 overflow-y-auto">
		<!-- Mobile: TOC toggle -->
		{#if isMobileViewer && company}
			<div class="sticky top-0 z-30 flex items-center gap-2 px-3 py-1.5 bg-dl-bg-dark/95 border-b border-dl-border/20 backdrop-blur-sm">
				<button
					class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"
					onclick={() => { mobileNavOpen = true; }}
				>
					<FileText size={11} />
					<span>목차</span>
				</button>
				{#if viewer?.selectedTopic}
					<span class="text-[11px] text-dl-text-muted truncate">{viewer?.topicData?.topicLabel || viewer?.selectedTopic}</span>
				{/if}
			</div>
		{/if}
		{#if !company}
			<div class="flex flex-col items-center justify-center h-full text-center px-8">
				<FileText size={32} class="text-dl-text-dim/30 mb-3" />
				<div class="text-[14px] text-dl-text-muted mb-1">공시 뷰어</div>
				<div class="text-[12px] text-dl-text-dim">종목을 검색하여 공시 문서를 살펴보세요</div>
			</div>
		{:else if viewer?.tocLoading}
			<!-- Loading skeleton -->
			<div class="max-w-4xl mx-auto px-6 py-4 space-y-4 animate-fadeIn">
				<div class="skeleton-line w-48 h-5"></div>
				<div class="skeleton-line w-full h-3"></div>
				<div class="skeleton-line w-5/6 h-3"></div>
				<div class="skeleton-line w-full h-3"></div>
				<div class="skeleton-line w-4/6 h-3"></div>
				<div class="skeleton-line w-full h-16 mt-4"></div>
			</div>
		{:else if viewer?.topicLoading}
			<div class="max-w-4xl mx-auto px-6 py-4 space-y-3 animate-fadeIn">
				<div class="skeleton-line w-40 h-5"></div>
				<div class="skeleton-line w-full h-3"></div>
				<div class="skeleton-line w-3/4 h-3"></div>
				<div class="skeleton-line w-full h-3"></div>
			</div>
		{:else if viewer?.topicData}
			<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn">
				<TopicRenderer
					topicData={viewer.topicData}
					diffSummary={viewer.diffSummary}
					{onAskAI}
				/>
			</div>
		{:else if viewer?.toc && !viewer?.selectedTopic}
			<div class="flex flex-col items-center justify-center h-full text-center px-8">
				<FileText size={28} class="text-dl-text-dim/30 mb-3" />
				<div class="text-[13px] text-dl-text-dim">좌측 목차에서 항목을 선택하세요</div>
			</div>
		{:else if viewer?.toc?.chapters?.length === 0}
			<div class="flex flex-col items-center justify-center h-full text-center px-8">
				<AlertCircle size={28} class="text-dl-text-dim/30 mb-3" />
				<div class="text-[13px] text-dl-text-dim">이 종목의 공시 데이터가 없습니다</div>
			</div>
		{/if}
	</div>
</div>
