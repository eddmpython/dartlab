<!--
	DisclosureViewer — 공시 뷰어 메인 레이아웃.
	좌측: ViewerNav (목차 + 최근 본 topic + 북마크)
	우측: TopicRenderer (블록 렌더링)
	상단: 중앙 검색 바
-->
<script>
	import { Loader2, FileText, Search, X, AlertCircle, Clock } from "lucide-svelte";
	import { fetchCompanySearch } from "$lib/api.js";
	import ViewerNav from "./ViewerNav.svelte";
	import TopicRenderer from "./TopicRenderer.svelte";
	import InsightDashboard from "./InsightDashboard.svelte";
	import KeyboardHelp from "./KeyboardHelp.svelte";

	let {
		viewer = null,   // viewer store
		company = null,  // selected company
		onAskAI = null,  // (text) => void — AI에게 물어보기 콜백
		onTopicChange = null, // (topic, label) => void — workspace 동기화
	} = $props();

	// 모바일 TOC 드로어
	let mobileNavOpen = $state(false);
	let isMobileViewer = $state(false);

	// P5: 키보드 도움말
	let showKeyboardHelp = $state(false);

	function checkMobileViewer() {
		isMobileViewer = typeof window !== "undefined" && window.innerWidth <= 768;
	}

	$effect(() => {
		checkMobileViewer();
		window.addEventListener("resize", checkMobileViewer);
		return () => window.removeEventListener("resize", checkMobileViewer);
	});

	// 중앙 검색
	let searchOpen = $state(false);
	let searchQuery = $state("");
	let searchInput = $state(null);

	function toggleSearch() {
		searchOpen = !searchOpen;
		if (searchOpen) {
			requestAnimationFrame(() => searchInput?.focus());
		} else {
			searchQuery = "";
			searchResults = null;
		}
	}

	// company 변경 시 자동 로드
	$effect(() => {
		if (company?.stockCode && viewer) {
			viewer.loadCompany(company.stockCode);
		}
	});

	// topic 변경 시 workspace에 동기화 + 히스토리 기록
	$effect(() => {
		if (viewer?.selectedTopic && viewer?.topicData) {
			onTopicChange?.(viewer.selectedTopic, viewer.topicData.topicLabel || viewer.selectedTopic);
			// 최근 본 topic 히스토리에 추가
			addToHistory(viewer.selectedTopic, viewer.topicData.topicLabel || viewer.selectedTopic);
		}
	});

	// 최근 본 topic 히스토리 (localStorage)
	let recentHistory = $state([]);
	const MAX_HISTORY = 8;

	function loadHistory() {
		try {
			const raw = localStorage.getItem("dartlab-viewer-history");
			const all = raw ? JSON.parse(raw) : {};
			return all[company?.stockCode] || [];
		} catch { return []; }
	}

	function saveHistory(items) {
		try {
			const raw = localStorage.getItem("dartlab-viewer-history");
			const all = raw ? JSON.parse(raw) : {};
			all[company?.stockCode] = items;
			localStorage.setItem("dartlab-viewer-history", JSON.stringify(all));
		} catch {}
	}

	function addToHistory(topic, label) {
		if (!company?.stockCode) return;
		const filtered = recentHistory.filter(h => h.topic !== topic);
		recentHistory = [{ topic, label, time: Date.now() }, ...filtered].slice(0, MAX_HISTORY);
		saveHistory(recentHistory);
	}

	$effect(() => {
		if (company?.stockCode) {
			recentHistory = loadHistory();
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

	// P8: insight → topic 이동
	function handleInsightNavigate(topic) {
		if (!viewer?.toc?.chapters) return;
		for (const ch of viewer.toc.chapters) {
			const found = ch.topics.find(t => t.topic === topic);
			if (found) {
				viewer.selectTopic(topic, ch.chapter);
				return;
			}
		}
	}

	function navigateToTopic(topic) {
		if (!viewer?.toc?.chapters) return;
		for (const ch of viewer.toc.chapters) {
			const found = ch.topics.find(t => t.topic === topic);
			if (found) {
				// B3: 검색어 하이라이트를 viewer에 전달
				const highlightQuery = searchQuery.trim();
				viewer.selectTopic(topic, ch.chapter);
				if (highlightQuery) {
					viewer.setSearchHighlight?.(highlightQuery);
				}
				searchOpen = false;
				searchQuery = "";
				searchResults = null;
				return;
			}
		}
	}

	// 키보드 단축키
	function handleKeydown(e) {
		const tag = e.target?.tagName;
		const isInput = tag === "INPUT" || tag === "TEXTAREA" || e.target?.isContentEditable;

		if (e.key === "f" && (e.ctrlKey || e.metaKey) && company) {
			e.preventDefault();
			toggleSearch();
			return;
		}
		if (e.key === "Escape") {
			if (showKeyboardHelp) { showKeyboardHelp = false; return; }
			if (searchOpen) { searchOpen = false; searchQuery = ""; searchResults = null; return; }
			return;
		}

		if (isInput) return;

		if (e.key === "?") {
			showKeyboardHelp = !showKeyboardHelp;
			return;
		}

		// /: 검색 열기
		if (e.key === "/" && company) {
			e.preventDefault();
			toggleSearch();
			return;
		}

		// J/K/↑↓ topic 탐색
		if (!searchOpen && (e.key === "ArrowUp" || e.key === "ArrowDown" || e.key === "j" || e.key === "k") && viewer?.selectedTopic) {
			const flat = flatTopics();
			const idx = flat.findIndex(t => t.topic === viewer.selectedTopic);
			if (idx < 0) return;
			const down = e.key === "ArrowDown" || e.key === "j";
			const next = down ? idx + 1 : idx - 1;
			if (next >= 0 && next < flat.length) {
				e.preventDefault();
				viewer.selectTopic(flat[next].topic, flat[next].chapter);
			}
			return;
		}

		if (e.key === "b" && viewer?.selectedTopic) {
			viewer.toggleBookmark(viewer.selectedTopic);
			return;
		}
	}

	// 검색 실행 (toc 라벨 + 서버 텍스트 병합)
	$effect(() => {
		const q = searchQuery.trim();
		if (!q || !company?.stockCode) {
			searchResults = null;
			return;
		}

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

		clearTimeout(searchDebounce);
		if (q.length >= 2) {
			searchLoading = true;
			searchDebounce = setTimeout(async () => {
				try {
					const res = await fetchCompanySearch(company.stockCode, q);
					if (searchQuery.trim() !== q) return;
					const serverResults = (res.results || []).map(r => ({ ...r, source: "text" }));
					const seen = new Set(localResults.map(r => r.topic));
					const merged = [...localResults, ...serverResults.filter(r => !seen.has(r.topic))];
					searchResults = merged.length > 0 ? merged : null;
				} catch {}
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

			<ViewerNav
				toc={viewer?.toc}
				loading={viewer?.tocLoading}
				selectedTopic={viewer?.selectedTopic}
				expandedChapters={viewer?.expandedChapters}
				bookmarks={viewer?.getBookmarks?.() ?? []}
				{recentHistory}
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
		<!-- 중앙 검색바 (항상 상단 노출) -->
		{#if company && !isMobileViewer}
			<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10">
				<div class="max-w-2xl mx-auto">
					<button
						class="flex items-center gap-2 w-full px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"
						onclick={toggleSearch}
					>
						<Search size={13} class="flex-shrink-0" />
						<span class="flex-1 text-left">공시 섹션 검색... <kbd class="ml-2 px-1 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono">/</kbd></span>
					</button>
				</div>
			</div>
		{/if}

		<!-- 검색 모달 -->
		{#if searchOpen}
			<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
			<div class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm" onclick={() => { searchOpen = false; searchQuery = ""; searchResults = null; }}>
				<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
				<div class="w-full max-w-xl bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl overflow-hidden" onclick={(e) => e.stopPropagation()}>
					<div class="flex items-center gap-2 px-4 py-3 border-b border-dl-border/20">
						<Search size={16} class="text-dl-text-dim flex-shrink-0" />
						<input
							bind:this={searchInput}
							bind:value={searchQuery}
							placeholder="섹션, topic, 키워드 검색..."
							class="flex-1 bg-transparent text-[14px] text-dl-text outline-none placeholder:text-dl-text-dim"
						/>
						{#if searchQuery}
							<button class="p-1 text-dl-text-dim hover:text-dl-text" onclick={() => { searchQuery = ""; }}>
								<X size={14} />
							</button>
						{/if}
						<kbd class="px-1.5 py-0.5 rounded bg-dl-border/15 text-[10px] font-mono text-dl-text-dim">Esc</kbd>
					</div>

					<div class="max-h-[50vh] overflow-y-auto">
						{#if searchResults}
							{#each searchResults.slice(0, 15) as t}
								<button
									class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-start gap-2 border-b border-dl-border/5"
									onclick={() => navigateToTopic(t.topic)}
								>
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2">
											<span class="text-dl-text">{t.label}</span>
											<span class="text-[10px] text-dl-text-dim/50 font-mono">{t.topic}</span>
										</div>
										{#if t.chapter}
											<div class="text-[10px] text-dl-text-dim/60 mt-0.5">{t.chapter}</div>
										{/if}
										{#if t.snippet}
											<div class="text-[11px] text-dl-text-dim truncate mt-0.5">{t.snippet}</div>
										{/if}
									</div>
									{#if t.matchCount > 0}
										<span class="text-[10px] text-dl-accent font-mono flex-shrink-0">{t.matchCount}건</span>
									{/if}
								</button>
							{/each}
							{#if searchLoading}
								<div class="flex items-center justify-center py-3">
									<Loader2 size={14} class="animate-spin text-dl-text-dim" />
								</div>
							{/if}
						{:else if searchLoading}
							<div class="flex items-center justify-center py-6 gap-2">
								<Loader2 size={14} class="animate-spin text-dl-text-dim" />
								<span class="text-[12px] text-dl-text-dim">검색 중...</span>
							</div>
						{:else if searchQuery.trim()}
							<div class="text-center py-6 text-[12px] text-dl-text-dim">결과 없음</div>
						{:else}
							<!-- 검색어 없을 때: 최근 본 topic -->
							{#if recentHistory.length > 0}
								<div class="px-4 py-2 text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold">최근 본 섹션</div>
								{#each recentHistory as h}
									<button
										class="w-full text-left px-4 py-2 text-[13px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"
										onclick={() => navigateToTopic(h.topic)}
									>
										<Clock size={12} class="text-dl-text-dim/40 flex-shrink-0" />
										<span>{h.label}</span>
										<span class="text-[10px] text-dl-text-dim/40 font-mono ml-auto">{h.topic}</span>
									</button>
								{/each}
							{/if}
						{/if}
					</div>
				</div>
			</div>
		{/if}

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
				<button
					class="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors border border-dl-border/30"
					onclick={toggleSearch}
				>
					<Search size={11} />
					<span>검색</span>
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
			<div class="flex flex-col items-center justify-center h-full">
				<Loader2 size={24} class="animate-spin text-dl-text-dim/40 mb-3" />
				<div class="text-[12px] text-dl-text-dim">공시 데이터 로딩 중...</div>
			</div>
		{:else if viewer?.topicLoading}
			<div class="flex flex-col items-center justify-center h-full">
				<Loader2 size={20} class="animate-spin text-dl-text-dim/40 mb-2" />
				<div class="text-[11px] text-dl-text-dim">섹션 로딩 중...</div>
			</div>
		{:else if viewer?.topicData}
			<div class="max-w-4xl mx-auto px-6 py-4 animate-fadeIn">
				<!-- P1: Insight Dashboard -->
				<InsightDashboard
					data={viewer.insightData}
					loading={viewer.insightLoading}
					toc={viewer.toc}
					onNavigateTopic={handleInsightNavigate}
				/>

				<div class="mt-4">
					<TopicRenderer
						topicData={viewer.topicData}
						diffSummary={viewer.diffSummary}
						{viewer}
						{onAskAI}
						searchHighlight={viewer.searchHighlight}
					/>
				</div>
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

<!-- P5: Keyboard help modal -->
<KeyboardHelp show={showKeyboardHelp} onClose={() => { showKeyboardHelp = false; }} />
