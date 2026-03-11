<script>
	import { cn } from "$lib/utils.js";
	import { Download, Database } from "lucide-svelte";
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
	} = $props();

	let chatContainer;
	let userScrolledUp = false;

	function onScroll() {
		if (!chatContainer) return;
		const { scrollTop, scrollHeight, clientHeight } = chatContainer;
		userScrolledUp = scrollHeight - scrollTop - clientHeight > 80;
	}

	$effect(() => {
		scrollTrigger;
		if (!chatContainer || userScrolledUp) return;
		requestAnimationFrame(() => {
			if (!chatContainer) return;
			chatContainer.scrollTop = chatContainer.scrollHeight;
		});
	});

</script>

<div class="flex flex-col h-full min-h-0">
	<div class="flex-1 overflow-y-auto min-h-0" bind:this={chatContainer} onscroll={onScroll}>
		<div class="max-w-[720px] mx-auto px-5 pt-14 pb-8 space-y-8">
			{#each messages as msg, idx}
				<MessageBubble
					message={msg}
					onRegenerate={isLastAssistant(idx) ? onRegenerate : undefined}
				/>
			{/each}
		</div>
	</div>

	<div class="flex-shrink-0 px-5 pb-4 pt-2">
		<div class="max-w-[720px] mx-auto">
			{#if !isLoading}
				<div class="flex justify-end gap-2 mb-1.5">
					<button
						class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
						onclick={() => onOpenExplorer?.()}
					>
						<Database size={10} />
						데이터
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
