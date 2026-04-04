<script>
	import { cn } from "$lib/utils.js";
	import { searchCompany } from "$lib/api.js";
	import { ArrowUp, Square, Search } from "lucide-svelte";

	let {
		inputText = $bindable(""),
		isLoading = false,
		large = false,
		placeholder = "메시지를 입력하세요...",
		enableCompanyAutocomplete = true,
		providerLabel = null,
		modelLabel = null,
		onSend,
		onStop,
		onCompanySelect,
		onCommand,
		selectedModules = $bindable([]),
	} = $props();

	let suggestions = $state([]);
	let showSuggestions = $state(false);
	let selectedIdx = $state(-1);
	let debounceTimer = null;
	let textareaEl = $state();

	// ── 슬래시 명령어 ──
	const SLASH_CMDS = [
		{ name: "new", label: "/new", desc: "새 대화" },
		{ name: "clear", label: "/clear", desc: "대화 초기화" },
		{ name: "provider", label: "/provider", desc: "프로바이더 설정" },
		{ name: "settings", label: "/settings", desc: "전체 설정" },
		{ name: "help", label: "/help", desc: "도움말" },
	];
	let showSlash = $state(false);
	let slashIdx = $state(0);
	let filteredCmds = $derived.by(() => {
		if (!inputText.startsWith("/")) return [];
		const q = inputText.slice(1).toLowerCase();
		return q ? SLASH_CMDS.filter(c => c.name.startsWith(q)) : SLASH_CMDS;
	});

	// ── 모듈 토글 ──
	const MODULE_OPTIONS = [
		{ id: "수익성", label: "수익성" },
		{ id: "밸류에이션", label: "밸류에이션" },
		{ id: "전망", label: "전망" },
		{ id: "비교", label: "비교" },
	];
	function toggleModule(id) {
		if (selectedModules.includes(id)) {
			selectedModules = selectedModules.filter(m => m !== id);
		} else if (selectedModules.length < 3) {
			selectedModules = [...selectedModules, id];
		}
		try { localStorage.setItem("dartlab-modules", JSON.stringify(selectedModules)); } catch {}
	}

	function shouldAutocompleteCompany(value) {
		if (!enableCompanyAutocomplete) return false;
		const trimmed = value.trim();
		if (trimmed.length < 2) return false;
		if (trimmed.length > 15) return false;
		if (/\s/.test(trimmed)) return false;
		if (/[?!.,/\\()[\]{}:;'"`~@#$%^&*_+=]/.test(trimmed)) return false;
		return true;
	}

	function execSlash(cmd) {
		inputText = "";
		showSlash = false;
		slashIdx = 0;
		onCommand?.(cmd.name);
	}

	function handleKeydown(e) {
		// 슬래시 메뉴 열려 있으면 우선
		if (showSlash && filteredCmds.length > 0) {
			if (e.key === "ArrowDown") { e.preventDefault(); slashIdx = (slashIdx + 1) % filteredCmds.length; return; }
			if (e.key === "ArrowUp") { e.preventDefault(); slashIdx = (slashIdx - 1 + filteredCmds.length) % filteredCmds.length; return; }
			if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); execSlash(filteredCmds[slashIdx]); return; }
			if (e.key === "Escape") { e.preventDefault(); showSlash = false; return; }
		}

		// 기업 자동완성
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
			// 슬래시 명령어인지 체크
			const trimmed = inputText.trim();
			if (trimmed.startsWith("/")) {
				const cmd = SLASH_CMDS.find(c => c.name === trimmed.slice(1).toLowerCase());
				if (cmd) { execSlash(cmd); return; }
			}
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

		// 슬래시 메뉴 판단
		if (val.startsWith("/")) {
			showSlash = filteredCmds.length > 0;
			slashIdx = 0;
			suggestions = [];
			showSuggestions = false;
			return;
		}
		showSlash = false;

		if (debounceTimer) clearTimeout(debounceTimer);

		if (shouldAutocompleteCompany(val) && !/\s/.test(val.slice(-1))) {
			debounceTimer = setTimeout(async () => {
				try {
					const data = await searchCompany(val.trim());
					if (data.results?.length > 0) {
						suggestions = data.results.slice(0, 6);
						showSuggestions = true;
						selectedIdx = -1;
					} else {
						suggestions = [];
						showSuggestions = false;
						selectedIdx = -1;
					}
				} catch {
					suggestions = [];
					showSuggestions = false;
					selectedIdx = -1;
				}
			}, 300);
		} else {
			suggestions = [];
			showSuggestions = false;
			selectedIdx = -1;
		}
	}

	function applySuggestion(item) {
		inputText = `${item.corpName} `;
		showSuggestions = false;
		selectedIdx = -1;
		onCompanySelect?.(item);
		if (textareaEl) textareaEl.focus();
	}

	function handleBlur() {
		setTimeout(() => { showSuggestions = false; showSlash = false; }, 200);
	}
</script>

<div class="relative w-full">
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
		<div class="flex items-center gap-1.5 flex-shrink-0">
			{#if providerLabel && !large}
				<span class="text-[10px] text-dl-text-dim/60 whitespace-nowrap select-none hidden sm:inline">
					{providerLabel}{#if modelLabel}<span class="text-dl-text-dim/40"> / </span><span class="max-w-[60px] truncate inline-block align-bottom">{modelLabel}</span>{/if}
				</span>
			{/if}
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
	</div>

	<!-- ── 모듈 토글 footer ── -->
	{#if !isLoading && !large}
		<div class="flex items-center gap-1.5 mt-1.5 px-1">
			{#each MODULE_OPTIONS as mod}
				<button
					class={cn(
						"px-2.5 py-1 rounded-full text-[10px] font-medium border transition-colors",
						selectedModules.includes(mod.id)
							? "border-dl-accent/40 bg-dl-accent/10 text-dl-accent-light"
							: "border-dl-border/30 text-dl-text-dim hover:border-dl-border/60 hover:text-dl-text-muted"
					)}
					onclick={() => toggleModule(mod.id)}
				>
					{mod.label}
				</button>
			{/each}
			{#if selectedModules.length > 0}
				<span class="text-[9px] text-dl-text-dim/50 ml-1">{selectedModules.length}/3</span>
			{/if}
		</div>
	{/if}

	<!-- ── 슬래시 명령어 메뉴 ── -->
	{#if showSlash && filteredCmds.length > 0}
		<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn">
			{#each filteredCmds as cmd, i}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={cn(
						"flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors",
						i === slashIdx ? "bg-dl-primary/10 text-dl-text" : "text-dl-text-muted hover:bg-white/[0.03]"
					)}
					onmousedown={() => execSlash(cmd)}
					onmouseenter={() => { slashIdx = i; }}
				>
					<span class="text-[13px] font-mono font-medium text-dl-accent">{cmd.label}</span>
					<span class="text-[12px] text-dl-text-dim">{cmd.desc}</span>
				</div>
			{/each}
		</div>
	{/if}

	<!-- ── 기업 자동완성 ── -->
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
