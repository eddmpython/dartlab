<script>
	import { Download } from "lucide-svelte";
	import { summarizeDataReady } from "$lib/ai/dataReady.js";
	import MessageBubble from "./MessageBubble.svelte";
	import AutocompleteInput from "./AutocompleteInput.svelte";

	function isLastAssistant(msg) {
		if (isLoading) return false;
		for (let i = messages.length - 1; i >= 0; i--) {
			if (messages[i].role === "assistant" && !messages[i].error && messages[i].text) {
				return messages[i] === msg;
			}
		}
		return false;
	}

	let {
		messages = [],
		isLoading = false,
		inputText = $bindable(""),
		onSend,
		onStop,
		onRegenerate,
		onExport,
		onOpenData,
		onOpenEvidence,
		onOpenArtifact,
		onEditResend,
		onCompanySelect,
		selectedCompany = null,
		suggestions = [],
		dataReady = null,
		suggestionLoading = false,
		providerLabel = null,
		modelLabel = null,
		watchlist = [],
		onAddWatch,
		onRemoveWatch,
	} = $props();

	const DEFAULT_COMPANY_PROMPTS = [
		"이 회사의 핵심 투자 포인트를 한눈에 정리해주세요",
		"최근 공시에서 꼭 읽어야 할 문서를 우선순위로 골라주세요",
		"재무건전성과 현금흐름을 함께 점검해주세요",
	];

	let dataReadyInfo = $derived(summarizeDataReady(dataReady));
	let promptChips = $derived(suggestions?.length > 0 ? suggestions : DEFAULT_COMPANY_PROMPTS);

	function bridgeEvidence(msg) {
		return (type, idx) => {
			onOpenEvidence?.(type, idx);
			let data;
			if (type === "contexts") data = msg.contexts?.[idx];
			else if (type === "snapshot") data = { label: "핵심 수치", module: "snapshot", text: JSON.stringify(msg.snapshot, null, 2) };
			else if (type === "system") data = { label: "시스템 프롬프트", module: "system", text: msg.systemPrompt };
			else if (type === "input") data = { label: "LLM 입력", module: "input", text: msg.userContent };
			else if (type === "tool-calls" || type === "tool-results") {
				const ev = msg.toolEvents?.[idx];
				const isResult = ev?.type === "result";
				const displayText = isResult && ev?.result ? ev.result : JSON.stringify(ev, null, 2);
				data = { label: `${ev?.name || "도구"} ${isResult ? "결과" : "호출"}`, module: "tool", text: displayText };
			}
			if (data) onOpenData?.(data);
		};
	}

	let chatContainer;
	let streamAnchor;
	let followStream = $state(true);
	let showJumpToLatest = $state(false);
	let isNearBottom = $state(true);
	let autoScrollRafId = $state(null);

	// 스태거 애니메이션: 초기 로드 시에만 적용
	let staggerReady = $state(true);
	let prevMsgCount = $state(0);
	$effect(() => {
		if (messages.length !== prevMsgCount) {
			if (prevMsgCount > 0 && messages.length > prevMsgCount) {
				// 새 메시지 추가됨 — 스태거 비활성화
				staggerReady = false;
			}
			prevMsgCount = messages.length;
		}
	});

	// Load more: 최근 PAGE_SIZE개만 렌더, 위로 스크롤 시 더 불러오기
	const PAGE_SIZE = 30;
	let displayCount = $state(PAGE_SIZE);
	let loadMoreSentinel = $state(null);

	// 대화 변경 시 displayCount 초기화
	$effect(() => {
		if (messages.length) displayCount = PAGE_SIZE;
	});

	let visibleMessages = $derived.by(() => {
		if (messages.length <= displayCount) return messages;
		return messages.slice(messages.length - displayCount);
	});

	let hasMore = $derived(messages.length > displayCount);

	function loadMore() {
		if (!hasMore) return;
		// 스크롤 위치 보존을 위해 현재 높이 기억
		const prevHeight = chatContainer?.scrollHeight || 0;
		displayCount = Math.min(displayCount + PAGE_SIZE, messages.length);
		// 새 메시지 로드 후 스크롤 위치 복원
		requestAnimationFrame(() => {
			if (chatContainer) {
				const newHeight = chatContainer.scrollHeight;
				chatContainer.scrollTop += (newHeight - prevHeight);
			}
		});
	}

	// IntersectionObserver로 상단 감지 → 자동 load more
	$effect(() => {
		if (!loadMoreSentinel || !hasMore) return;
		const obs = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting) loadMore();
		}, { rootMargin: "200px" });
		obs.observe(loadMoreSentinel);
		return () => obs.disconnect();
	});

	function onScroll() {
		if (!chatContainer) return;
		const { scrollTop, scrollHeight, clientHeight } = chatContainer;
		isNearBottom = scrollHeight - scrollTop - clientHeight < 96;
		if (isNearBottom) {
			followStream = true;
			showJumpToLatest = false;
		} else {
			followStream = false;
			showJumpToLatest = true;
		}
	}

	function scrollToLatest(behavior = "smooth") {
		if (!streamAnchor) return;
		streamAnchor.scrollIntoView({ block: "end", behavior });
		followStream = true;
		showJumpToLatest = false;
	}

	function stopAutoScroll() {
		if (autoScrollRafId) {
			cancelAnimationFrame(autoScrollRafId);
			autoScrollRafId = null;
		}
	}

	const SCROLL_INTERVAL_MS = 120;
	let lastScrollTime = 0;

	function autoScrollLoop() {
		if (!isLoading || !followStream || !streamAnchor) {
			autoScrollRafId = null;
			return;
		}
		const now = performance.now();
		if (now - lastScrollTime >= SCROLL_INTERVAL_MS) {
			streamAnchor.scrollIntoView({ block: "end" });
			showJumpToLatest = false;
			lastScrollTime = now;
		}
		autoScrollRafId = requestAnimationFrame(autoScrollLoop);
	}

	function startAutoScroll() {
		if (!streamAnchor || autoScrollRafId) return;
		lastScrollTime = 0;
		autoScrollRafId = requestAnimationFrame(autoScrollLoop);
	}

	$effect(() => {
		if (isLoading && followStream) {
			startAutoScroll();
		} else {
			stopAutoScroll();
		}
	});

	$effect(() => {
		if (!isLoading && streamAnchor && (followStream || isNearBottom)) {
			requestAnimationFrame(() => {
				streamAnchor?.scrollIntoView({ block: "end" });
				showJumpToLatest = false;
			});
		}
	});

	$effect(() => {
		return () => stopAutoScroll();
	});

</script>

<!-- shared contract marker: onOpenEvidence={onOpenEvidence} -->
<div class="relative flex flex-col h-full min-h-0">
	<div class="flex-1 overflow-y-auto min-h-0" bind:this={chatContainer} onscroll={onScroll} role="log" aria-live="polite" aria-label="대화 내용">
		<div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-12 pb-10 space-y-8">
				{#if hasMore}
					<div bind:this={loadMoreSentinel} class="flex justify-center py-3">
						<button
							class="px-3 py-1.5 rounded-full text-[11px] text-dl-text-dim hover:text-dl-text-muted border border-white/8 hover:border-white/14 transition-colors"
							onclick={loadMore}
						>
							이전 메시지 불러오기
						</button>
					</div>
				{/if}
				{#each visibleMessages as msg, i}
					<MessageBubble
						message={msg}
						staggerIndex={staggerReady && i < 15 ? i : 0}
						onRegenerate={isLastAssistant(msg) ? onRegenerate : undefined}
						onOpenEvidence={onOpenData ? bridgeEvidence(msg) : undefined}
						{onOpenArtifact}
						onEditResend={msg.role === "user" ? onEditResend : undefined}
						{onAddWatch}
						{onRemoveWatch}
						isWatched={!!msg.meta?.stockCode && watchlist.some(w => w.code === msg.meta.stockCode)}
					/>
				{/each}
				<div bind:this={streamAnchor} class="h-px w-full"></div>
			</div>
		</div>

	{#if showJumpToLatest}
		<div class="pointer-events-none absolute bottom-28 right-6 z-20">
			<button
				class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light"
				onclick={() => scrollToLatest("smooth")}
			>
				최신 응답으로 이동
			</button>
		</div>
	{/if}

	<div class="flex-shrink-0 px-5 pb-4 pt-2">
		<div class="max-w-[720px] mx-auto">
			{#if !isLoading}
				<div class="flex justify-end gap-2 mb-1.5">
					{#if messages.length > 1 && onExport}
						<button
							class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
							onclick={onExport}
						>
							<Download size={10} />
							마크다운
						</button>
					{/if}
				</div>
			{/if}
			{#if !isLoading && selectedCompany?.stockCode}
				<div class="mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/30 px-3 py-3">
					<div class="flex flex-wrap items-center gap-2">
						<span class="rounded-full border border-dl-accent/20 bg-dl-accent/10 px-2.5 py-0.5 text-[11px] font-medium text-dl-accent-light">
							{selectedCompany.corpName || selectedCompany.company || selectedCompany.stockCode}
						</span>
						<span class="rounded-full border border-dl-border/50 bg-dl-bg-card/60 px-2.5 py-0.5 text-[10px] text-dl-text-dim">
							{selectedCompany.stockCode}
						</span>
						{#if dataReadyInfo}
							<span class="rounded-full border px-2.5 py-0.5 text-[10px] {dataReadyInfo.allReady ? 'border-emerald-500/20 bg-emerald-500/[0.08] text-emerald-400' : 'border-amber-500/20 bg-amber-500/[0.08] text-amber-300'}">
								{dataReadyInfo.label}
							</span>
						{/if}
					</div>
					{#if dataReadyInfo}
						<div class="mt-2 text-[11px] leading-relaxed text-dl-text-dim">
							{dataReadyInfo.summary}
						</div>
					{/if}
					<div class="mt-3 flex flex-wrap items-center gap-2">
						<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">
							추천 질문
						</div>
						{#if suggestionLoading}
							<span class="text-[11px] text-dl-text-dim">준비 중...</span>
						{/if}
					</div>
					<div class="mt-2 flex flex-wrap gap-2">
						{#each promptChips as suggestion}
							<button
								class="rounded-full border border-dl-border/40 bg-dl-bg-card/70 px-3 py-1.5 text-left text-[11px] text-dl-text transition-colors hover:border-dl-primary/35 hover:text-dl-primary-light"
								onclick={() => onSend?.(suggestion)}
							>
								{suggestion}
							</button>
						{/each}
					</div>
				</div>
			{/if}
			<AutocompleteInput
				bind:inputText
				{isLoading}
				enableCompanyAutocomplete={false}
				{providerLabel}
				{modelLabel}
				placeholder="메시지를 입력하세요..."
				onSend={onSend}
				onStop={onStop}
				{onCompanySelect}
			/>
		</div>
	</div>
</div>
