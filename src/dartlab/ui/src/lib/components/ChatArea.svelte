<script>
	import { cn } from "$lib/utils.js";
	import { Download, FileSpreadsheet } from "lucide-svelte";
	import MessageBubble from "./MessageBubble.svelte";
	import AutocompleteInput from "./AutocompleteInput.svelte";
	import ExcelExportPanel from "./ExcelExportPanel.svelte";

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
	} = $props();

	let showExcelPanel = $state(false);

	let lastStockCode = $derived.by(() => {
		for (let i = messages.length - 1; i >= 0; i--) {
			const m = messages[i];
			if (m.role === "assistant" && m.meta?.stockCode) return m.meta.stockCode;
		}
		return null;
	});

	let lastCorpName = $derived.by(() => {
		for (let i = messages.length - 1; i >= 0; i--) {
			const m = messages[i];
			if (m.role === "assistant" && m.meta?.company) return m.meta.company;
		}
		return "";
	});

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
			{#if messages.length > 1 && !isLoading}
				<div class="flex justify-end gap-2 mb-1.5">
					{#if lastStockCode}
						<button
							class={cn(
								"flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] transition-colors",
								showExcelPanel
									? "text-dl-success bg-dl-success/10"
									: "text-dl-text-dim hover:text-dl-success"
							)}
							onclick={() => showExcelPanel = !showExcelPanel}
						>
							<FileSpreadsheet size={10} />
							Excel
						</button>
					{/if}
					{#if onExport}
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
			{#if showExcelPanel && lastStockCode}
				<div class="mb-2">
					<ExcelExportPanel
						stockCode={lastStockCode}
						corpName={lastCorpName}
						onClose={() => showExcelPanel = false}
					/>
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
