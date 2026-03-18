<script>
	import { Download } from "lucide-svelte";
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
		onOpenData,
		onCompanySelect,
		selectedCompany = null,
	} = $props();

	function bridgeEvidence(msg) {
		return (type, idx) => {
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
		<div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8">
					{#each messages as msg, idx}
					<MessageBubble
						message={msg}
						onRegenerate={isLastAssistant(idx) ? onRegenerate : undefined}
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
			<AutocompleteInput
				bind:inputText
				{isLoading}
				placeholder="메시지를 입력하세요..."
				onSend={onSend}
				onStop={onStop}
				{onCompanySelect}
			/>
		</div>
	</div>
</div>
