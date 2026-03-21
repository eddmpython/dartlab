<script>
	import { Download, Sparkles } from "lucide-svelte";
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
		onCompanySelect,
		selectedCompany = null,
		viewerContext = null,   // B2: {topic, topicLabel, period} from viewer
		pendingBlockLabel = null,  // 뷰어에서 첨부된 블록 라벨
		onClearBlock = null,       // 블록 첨부 해제 콜백
		providerLabel = null,
		modelLabel = null,
	} = $props();

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
				data = { label: `${ev?.name || "도구"} ${ev?.type === "call" ? "호출" : "결과"}`, module: "tool", text: JSON.stringify(ev, null, 2) };
			}
			if (data) onOpenData?.(data);
		};
	}

	let chatContainer;
	let streamAnchor;
	let followStream = $state(true);
	let showJumpToLatest = $state(false);
	let isNearBottom = $state(true);

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

	// 스트리밍 중 rAF 루프로 부드럽게 스크롤 — scrollTrigger 과호출 제거
	let scrollRafId = null;
	function scrollLoop() {
		if (!streamAnchor) return;
		if (followStream || isNearBottom) {
			streamAnchor.scrollIntoView({ block: "end", behavior: "auto" });
			showJumpToLatest = false;
		}
		scrollRafId = requestAnimationFrame(scrollLoop);
	}

	$effect(() => {
		if (isLoading) {
			if (!scrollRafId) scrollRafId = requestAnimationFrame(scrollLoop);
		} else {
			if (scrollRafId) { cancelAnimationFrame(scrollRafId); scrollRafId = null; }
			// 완료 시 한 번 smooth 스크롤
			if (streamAnchor && (followStream || isNearBottom)) {
				streamAnchor.scrollIntoView({ block: "end", behavior: "smooth" });
				showJumpToLatest = false;
			}
		}
		return () => { if (scrollRafId) { cancelAnimationFrame(scrollRafId); scrollRafId = null; } };
	});

</script>

<!-- shared contract marker: onOpenEvidence={onOpenEvidence} -->
<div class="relative flex flex-col h-full min-h-0">
	<div class="flex-1 overflow-y-auto min-h-0" bind:this={chatContainer} onscroll={onScroll}>
		<div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8">
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
				{#each visibleMessages as msg}
					<MessageBubble
						message={msg}
						onRegenerate={isLastAssistant(msg) ? onRegenerate : undefined}
						onOpenEvidence={onOpenData ? bridgeEvidence(msg) : undefined}
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
			<!-- B2: Viewer context badge -->
			{#if viewerContext?.topic}
				<div class="flex items-center gap-1.5 px-3 py-1 text-[10px] text-dl-text-dim">
					<span class="px-1.5 py-0.5 rounded bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20 font-mono">
						{viewerContext.topicLabel || viewerContext.topic}{#if viewerContext.period}&nbsp;({viewerContext.period}){/if}
					</span>
					<span>보는 중 — AI가 이 섹션을 참조합니다</span>
				</div>
			{/if}
			<!-- 블록 첨부 표시 -->
			{#if pendingBlockLabel}
				<div class="flex items-center gap-1.5 px-3 py-1 text-[10px]">
					<span class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
						<Sparkles size={10} />
						{pendingBlockLabel}
					</span>
					<span class="text-dl-text-dim">블록 데이터 첨부됨</span>
					{#if onClearBlock}
						<button
							class="text-dl-text-dim/50 hover:text-dl-text-muted transition-colors"
							onclick={onClearBlock}
							title="첨부 해제"
						>✕</button>
					{/if}
				</div>
			{/if}
			<AutocompleteInput
				bind:inputText
				{isLoading}
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
