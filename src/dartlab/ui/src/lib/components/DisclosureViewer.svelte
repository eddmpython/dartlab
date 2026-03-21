<!--
	DisclosureViewer — 공시 뷰어 메인 레이아웃.
	좌측: ViewerNav (목차 + 최근 본 topic + 북마크)
	우측: TopicRenderer (블록 렌더링)
	상단: 중앙 검색 바
-->
<script>
	import { Loader2, FileText, Search, X, AlertCircle, Clock, Building2, PanelLeftClose, PanelLeftOpen } from "lucide-svelte";
	import Skeleton from "$lib/components/ui/skeleton/Skeleton.svelte";
	import { fetchCompanySearch, searchCompany } from "$lib/api.js";
	import ViewerNav from "./ViewerNav.svelte";
	import TopicRenderer from "./TopicRenderer.svelte";
	import InsightDashboard from "./InsightDashboard.svelte";
	import NetworkGraph from "./NetworkGraph.svelte";
	import KeyboardHelp from "./KeyboardHelp.svelte";

	let {
		viewer = null,   // viewer store
		company = null,  // selected company
		onAskAI = null,  // (text) => void — AI에게 물어보기 콜백
		onTopicChange = null, // (topic, label) => void — workspace 동기화
		recentCompanies = [], // 최근 검색한 종목 목록
		onCompanySelect = null, // (company) => void — 종목 선택 콜백
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

	let showInsightPanel = $state(false);
	let navCollapsed = $state(false);

	// company 변경 시 자동 로드 — stockCode만 의존
	let lastLoadedCode = null;
	$effect(() => {
		const code = company?.stockCode;
		if (code && code !== lastLoadedCode && viewer) {
			lastLoadedCode = code;
			viewer.loadCompany(code);
		}
	});

	// topic 변경 시 workspace에 동기화 + 히스토리 기록 — topic 값만 의존
	let lastSyncedTopic = null;
	$effect(() => {
		const topic = viewer?.selectedTopic;
		const label = viewer?.topicData?.topicLabel || topic;
		if (topic && topic !== lastSyncedTopic) {
			lastSyncedTopic = topic;
			onTopicChange?.(topic, label);
			addToHistory(topic, label);
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

	// 종목 검색 (뷰어 탭 진입 시)
	let companySearchText = $state("");
	let companySearchResults = $state([]);
	let companySearchLoading = $state(false);
	let companySearchDebounce = null;
	let companySearchInput = $state(null);

	$effect(() => {
		const q = companySearchText.trim();
		if (!q || q.length < 1) { companySearchResults = []; return; }
		clearTimeout(companySearchDebounce);
		companySearchLoading = true;
		companySearchDebounce = setTimeout(async () => {
			try {
				const results = await searchCompany(q);
				if (companySearchText.trim() === q) {
					companySearchResults = results || [];
				}
			} catch { companySearchResults = []; }
			companySearchLoading = false;
		}, 200);
	});

	function selectCompanyResult(result) {
		companySearchText = "";
		companySearchResults = [];
		onCompanySelect?.(result);
	}

	// 검색 결과
	let searchResults = $state(null);
	let searchDisplayLimit = $state(15);
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

	// 검색 실행 — MiniSearch 우선, fallback 서버 검색
	$effect(() => {
		const q = searchQuery.trim();
		searchDisplayLimit = 15;
		if (!q || !company?.stockCode) {
			searchResults = null;
			return;
		}

		// MiniSearch가 준비되었으면 로컬 전문 검색 (fuzzy/prefix/BM25)
		if (viewer?.searchIndexReady) {
			const msResults = viewer.searchSections(q);
			searchResults = msResults.length > 0 ? msResults : null;
			return;
		}

		// fallback: TOC 라벨 매칭 + 서버 substring
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
			: `flex-shrink-0 transition-all duration-200 ${navCollapsed ? 'w-0 overflow-hidden' : 'w-56'}`} border-r border-dl-border/30 overflow-hidden bg-dl-bg-dark"
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

			<!-- company 없을 때: 최근 종목 목록 -->
			{#if !company && recentCompanies.length > 0}
				<div class="px-3 py-3 flex-1 overflow-y-auto">
					<div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2">최근 종목</div>
					{#each recentCompanies as rc}
						<button
							class="w-full text-left px-2 py-1.5 rounded-md text-[11px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-1.5"
							onclick={() => onCompanySelect?.(rc)}
						>
							<Building2 size={11} class="text-dl-text-dim/30 flex-shrink-0" />
							<span class="truncate">{rc.corpName || rc.company}</span>
							<span class="text-[9px] font-mono text-dl-text-dim/40 ml-auto">{rc.stockCode}</span>
						</button>
					{/each}
				</div>
			{/if}

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
				visitedTopics={viewer?.visitedTopics ?? new Set()}
			onToggleChapter={(chapter) => viewer?.toggleChapter(chapter)}
			onPrefetch={(topic) => viewer?.prefetchTopic(topic)}
			/>
		</div>
	</div>

	<!-- Right: Content -->
	<div class="flex-1 min-w-0 overflow-y-auto">
		<!-- 중앙 검색바 (항상 상단 노출) -->
		{#if company && !isMobileViewer}
			<div class="sticky top-0 z-20 px-6 py-2 bg-dl-bg-dark/95 backdrop-blur-sm border-b border-dl-border/10">
				<div class="flex items-center gap-2 max-w-2xl mx-auto">
					<button
						class="flex-shrink-0 p-1.5 rounded-md text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
						onclick={() => { navCollapsed = !navCollapsed; }}
						title={navCollapsed ? '목차 펼치기' : '목차 접기'}
					>
						{#if navCollapsed}
							<PanelLeftOpen size={15} />
						{:else}
							<PanelLeftClose size={15} />
						{/if}
					</button>
					<button
						class="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-lg border border-dl-border/20 bg-dl-bg-darker/60 text-[12px] text-dl-text-dim hover:border-dl-border/40 hover:bg-dl-bg-darker transition-colors"
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
							{#each searchResults.slice(0, searchDisplayLimit) as t}
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
							{#if searchResults.length > searchDisplayLimit}
								<button
									class="w-full py-2 text-[12px] text-dl-accent/70 hover:text-dl-accent hover:bg-white/3 transition-colors"
									onclick={() => { searchDisplayLimit += 15; }}
								>
									더보기 ({searchResults.length - searchDisplayLimit}개 남음)
								</button>
							{/if}
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
			<div class="flex flex-col items-center justify-center h-full text-center px-8 max-w-lg mx-auto">
				<FileText size={32} class="text-dl-text-dim/30 mb-3" />
				<div class="text-[14px] text-dl-text-muted mb-2">공시 뷰어</div>
				<div class="text-[12px] text-dl-text-dim mb-6">종목을 검색하여 공시 문서를 살펴보세요</div>

				<!-- 종목 검색 입력 -->
				<div class="w-full max-w-sm relative">
					<div class="flex items-center gap-2 px-3 py-2 rounded-lg border border-dl-border/30 bg-dl-bg-darker/60 focus-within:border-dl-accent/40 transition-colors">
						<Search size={14} class="text-dl-text-dim flex-shrink-0" />
						<input
							bind:this={companySearchInput}
							bind:value={companySearchText}
							placeholder="종목명 또는 종목코드..."
							class="flex-1 bg-transparent text-[13px] text-dl-text outline-none placeholder:text-dl-text-dim"
						/>
						{#if companySearchLoading}
							<Loader2 size={14} class="animate-spin text-dl-text-dim flex-shrink-0" />
						{/if}
					</div>

					<!-- 검색 결과 드롭다운 -->
					{#if companySearchResults.length > 0}
						<div class="absolute top-full mt-1 w-full bg-dl-bg-card border border-dl-border/30 rounded-lg shadow-xl overflow-hidden z-30 max-h-[300px] overflow-y-auto">
							{#each companySearchResults.slice(0, 10) as result}
								<button
									class="w-full text-left px-3 py-2 text-[13px] hover:bg-white/5 transition-colors flex items-center gap-2 border-b border-dl-border/5 last:border-b-0"
									onclick={() => selectCompanyResult(result)}
								>
									<Building2 size={13} class="text-dl-text-dim/40 flex-shrink-0" />
									<span class="text-dl-text truncate">{result.corpName || result.company}</span>
									<span class="text-[10px] font-mono text-dl-text-dim ml-auto flex-shrink-0">{result.stockCode}</span>
									{#if result.market}
										<span class="text-[9px] px-1 py-0.5 rounded bg-dl-border/10 text-dl-text-dim/60">{result.market}</span>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<!-- 최근 종목 -->
				{#if recentCompanies.length > 0}
					<div class="w-full max-w-sm mt-6">
						<div class="text-[10px] text-dl-text-dim uppercase tracking-wider font-semibold mb-2 text-left">최근 검색</div>
						<div class="space-y-0.5">
							{#each recentCompanies as rc}
								<button
									class="w-full text-left px-3 py-2 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors flex items-center gap-2"
									onclick={() => onCompanySelect?.(rc)}
								>
									<Clock size={12} class="text-dl-text-dim/30 flex-shrink-0" />
									<span class="truncate">{rc.corpName || rc.company}</span>
									<span class="text-[10px] font-mono text-dl-text-dim/50 ml-auto">{rc.stockCode}</span>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{:else if viewer?.tocLoading}
			<div class="max-w-7xl mx-auto px-6 py-6 space-y-6 animate-fadeIn">
				<Skeleton class="h-6 w-48" />
				<div class="space-y-3">
					<Skeleton class="h-4 w-full" />
					<Skeleton class="h-4 w-5/6" />
					<Skeleton class="h-4 w-4/5" />
				</div>
				<Skeleton class="h-24 w-full rounded-xl" />
				<div class="space-y-3">
					<Skeleton class="h-4 w-full" />
					<Skeleton class="h-4 w-3/4" />
				</div>
				<div class="text-[12px] text-dl-text-dim text-center">공시 데이터 로딩 중...</div>
			</div>
		{:else if viewer?.topicLoading && !viewer?.topicData}
			<div class="max-w-7xl mx-auto px-6 py-4 space-y-4 animate-fadeIn">
				<Skeleton class="h-5 w-2/3" />
				<Skeleton class="h-3 w-full" />
				<Skeleton class="h-3 w-5/6" />
				<Skeleton class="h-20 w-full rounded-xl" />
				<Skeleton class="h-3 w-4/5" />
				<Skeleton class="h-3 w-full" />
				<Skeleton class="h-16 w-full rounded-xl" />
			</div>
		{:else if viewer?.topicData}
			<!-- 로딩 중이면 이전 콘텐츠를 흐리게 유지 -->
			{#if viewer?.topicLoading}
				<div class="absolute top-0 left-0 right-0 h-0.5 bg-dl-accent/20 overflow-hidden z-10">
					<div class="h-full bg-dl-accent/60 animate-progress-bar"></div>
				</div>
			{/if}
			<div class="max-w-7xl mx-auto px-6 py-4 {viewer?.topicLoading ? 'opacity-40 pointer-events-none' : 'animate-fadeIn'} transition-opacity duration-200">
				<!-- 브레드크럼 -->
				{#if !isMobileViewer && (viewer?.corpName || viewer?.selectedChapter || viewer?.selectedTopic)}
					<nav class="flex items-center gap-1 text-[11px] text-dl-text-dim mb-3 overflow-x-auto" aria-label="경로">
						{#if viewer?.corpName}
							<span class="text-dl-text-muted font-medium truncate max-w-[160px]">{viewer.corpName}</span>
						{/if}
						{#if viewer?.selectedChapter}
							<span class="text-dl-border/60 mx-0.5">/</span>
							<span class="truncate max-w-[200px]">{viewer.selectedChapter}</span>
						{/if}
						{#if viewer?.topicData?.topicLabel || viewer?.selectedTopic}
							<span class="text-dl-border/60 mx-0.5">/</span>
							<span class="text-dl-text-muted truncate max-w-[200px]">{viewer.topicData?.topicLabel || viewer.selectedTopic}</span>
						{/if}
					</nav>
				{/if}
				<div class="mt-0">
					<TopicRenderer
						topicData={viewer.topicData}
						diffSummary={viewer.diffSummary}
						{viewer}
						{onAskAI}
						searchHighlight={viewer.searchHighlight}
					/>
				</div>

				<!-- Insight + Network: 콘텐츠 아래, 기본 접힘 -->
				{#if viewer.insightData || viewer.networkData || viewer.insightLoading || viewer.networkLoading}
					<div class="mt-8 border-t border-dl-border/10 pt-4">
						<button
							class="flex items-center gap-2 text-[12px] text-dl-text-dim hover:text-dl-text transition-colors mb-3"
							onclick={() => { showInsightPanel = !showInsightPanel; }}
						>
							<svg class="w-3 h-3 transition-transform {showInsightPanel ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
							</svg>
							투자 인사이트 · 관계도
						</button>
						{#if showInsightPanel}
							<div class="animate-fadeIn">
								<InsightDashboard
									data={viewer.insightData}
									loading={viewer.insightLoading}
									toc={viewer.toc}
									onNavigateTopic={handleInsightNavigate}
								/>
								<NetworkGraph
									data={viewer.networkData}
									loading={viewer.networkLoading}
									centerCode={company?.stockCode}
									onNavigate={(code) => {
										if (viewer && code !== company?.stockCode) {
											viewer.loadCompany(code);
										}
									}}
								/>
							</div>
						{/if}
					</div>
				{/if}
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
