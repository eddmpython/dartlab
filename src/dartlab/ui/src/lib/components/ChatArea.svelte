<script>
	import { Download, Database, Search } from "lucide-svelte";
	import MessageBubble from "./MessageBubble.svelte";
	import AutocompleteInput from "./AutocompleteInput.svelte";

	function isLastAssistant(idx) {
		if (isLoading) return false;
		for (let i = messages.length - 1; i >= 0; i--) {
			if (messages[i].role === "assistant" && !messages[i].error && messages[i].text) {
				return i === idx;
			}
		}
		return false;
	}

	let {
		messages = [],
		isLoading = false,
		inputText = $bindable(""),
		scrollTrigger = 0,
		onSend,
		onStop,
		onRegenerate,
		onExport,
		onOpenExplorer,
		onOpenEvidence,
		selectedCompany = null,
	} = $props();

	let chatContainer;
	let streamAnchor;
	let followStream = $state(true);
	let showJumpToLatest = $state(false);
	let isNearBottom = $state(true);

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

	$effect(() => {
		scrollTrigger;
		if (!chatContainer || !streamAnchor) return;
		requestAnimationFrame(() => {
			if (!chatContainer || !streamAnchor) return;
			if (followStream || isNearBottom) {
				streamAnchor.scrollIntoView({
					block: "end",
					behavior: isLoading ? "auto" : "smooth",
				});
				showJumpToLatest = false;
			} else {
				showJumpToLatest = true;
			}
		});
	});

</script>

<div class="relative flex flex-col h-full min-h-0">
	<div class="flex-1 overflow-y-auto min-h-0" bind:this={chatContainer} onscroll={onScroll}>
		<div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-14 pb-10 space-y-8">
			{#if selectedCompany}
				<div class="surface-panel flex flex-wrap items-center gap-2 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] px-4 py-3">
					<div class="flex items-center gap-2 text-[12px] text-dl-text">
						<Database size={13} class="text-dl-primary-light" />
						<span class="font-medium">{selectedCompany.corpName || selectedCompany.company || "선택된 회사"}</span>
						<span class="text-dl-text-dim">{selectedCompany.stockCode}</span>
					</div>
					<div class="flex flex-wrap gap-1.5 ml-auto">
						<button
							class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
							onclick={() => onOpenExplorer?.("overview")}
						>
							<Database size={10} class="inline mr-1" />
							Overview
						</button>
						<button
							class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
							onclick={() => onOpenExplorer?.("explore")}
						>
							<Search size={10} class="inline mr-1" />
							Explore
						</button>
						<button
							class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
							onclick={() => onOpenExplorer?.("evidence")}
						>
							<Database size={10} class="inline mr-1" />
							Evidence
						</button>
					</div>
				</div>
			{/if}
				{#each messages as msg, idx}
					<MessageBubble
						message={msg}
						onRegenerate={isLastAssistant(idx) ? onRegenerate : undefined}
						onOpenEvidence={onOpenEvidence}
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
					<button
						class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
						onclick={() => onOpenExplorer?.("explore")}
					>
						<Search size={10} />
						탐색
					</button>
					<button
						class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
						onclick={() => onOpenExplorer?.("evidence")}
					>
						<Database size={10} />
						근거
					</button>
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
			<AutocompleteInput
				bind:inputText
				{isLoading}
				placeholder="메시지를 입력하세요..."
				onSend={onSend}
				onStop={onStop}
			/>
		</div>
	</div>
</div>
