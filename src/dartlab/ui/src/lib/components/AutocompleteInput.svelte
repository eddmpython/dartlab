<script>
	import { cn } from "$lib/utils.js";
	import { searchCompany } from "$lib/api.js";
	import { ArrowUp, Square, Search } from "lucide-svelte";

	let {
		inputText = $bindable(""),
		isLoading = false,
		large = false,
		placeholder = "메시지를 입력하세요...",
		onSend,
		onStop,
	} = $props();

	let suggestions = $state([]);
	let showSuggestions = $state(false);
	let selectedIdx = $state(-1);
	let debounceTimer = null;
	let textareaEl = $state();

	function handleKeydown(e) {
		if (showSuggestions && suggestions.length > 0) {
			if (e.key === "ArrowDown") {
				e.preventDefault();
				selectedIdx = (selectedIdx + 1) % suggestions.length;
				return;
			}
			if (e.key === "ArrowUp") {
				e.preventDefault();
				selectedIdx = selectedIdx <= 0 ? suggestions.length - 1 : selectedIdx - 1;
				return;
			}
			if (e.key === "Enter" && selectedIdx >= 0) {
				e.preventDefault();
				applySuggestion(suggestions[selectedIdx]);
				return;
			}
			if (e.key === "Escape") {
				showSuggestions = false;
				selectedIdx = -1;
				return;
			}
		}

		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			showSuggestions = false;
			onSend?.();
		}
	}

	function autoResize(e) {
		e.target.style.height = "auto";
		e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
	}

	function handleInput(e) {
		autoResize(e);
		const val = inputText;

		if (debounceTimer) clearTimeout(debounceTimer);

		if (val.length >= 2 && !/\s/.test(val.slice(-1))) {
			debounceTimer = setTimeout(async () => {
				try {
					const data = await searchCompany(val.trim());
					if (data.results?.length > 0) {
						suggestions = data.results.slice(0, 6);
						showSuggestions = true;
						selectedIdx = -1;
					} else {
						showSuggestions = false;
					}
				} catch {
					showSuggestions = false;
				}
			}, 300);
		} else {
			showSuggestions = false;
		}
	}

	function applySuggestion(item) {
		inputText = `${item.corpName} `;
		showSuggestions = false;
		selectedIdx = -1;
		if (textareaEl) textareaEl.focus();
	}

	function handleBlur() {
		setTimeout(() => { showSuggestions = false; }, 200);
	}
</script>

<div class="relative">
	<div class={cn("input-box", large && "large")}>
		<textarea
			bind:this={textareaEl}
			bind:value={inputText}
			{placeholder}
			rows="1"
			onkeydown={handleKeydown}
			oninput={handleInput}
			onblur={handleBlur}
			class="input-textarea"
		></textarea>
		{#if isLoading && onStop}
			<button class="send-btn active" onclick={onStop}>
				<Square size={14} />
			</button>
		{:else}
			<button
				class={cn("send-btn", inputText.trim() && "active")}
				onclick={() => { showSuggestions = false; onSend?.(); }}
				disabled={!inputText.trim()}
			>
				<ArrowUp size={large ? 18 : 16} strokeWidth={2.5} />
			</button>
		{/if}
	</div>

	{#if showSuggestions && suggestions.length > 0}
		<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn">
			{#each suggestions as item, i}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={cn(
						"flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",
						i === selectedIdx ? "bg-dl-primary/10 text-dl-text" : "text-dl-text-muted hover:bg-white/[0.03]"
					)}
					onmousedown={() => applySuggestion(item)}
					onmouseenter={() => { selectedIdx = i; }}
				>
					<Search size={13} class="flex-shrink-0 text-dl-text-dim" />
					<div class="flex-1 min-w-0">
						<div class="text-[13px] font-medium truncate">{item.corpName}</div>
						<div class="text-[10px] text-dl-text-dim">{item.stockCode} · {item.market || ""}</div>
					</div>
					{#if item.sector}
						<span class="text-[10px] text-dl-text-dim flex-shrink-0">{item.sector}</span>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
