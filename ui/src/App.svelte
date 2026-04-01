<!--
	[최우선 UX 원칙] 데이터 투명성 — 절대 제거 금지

	SSE 스트리밍 콜백(onMeta, onSnapshot, onContext, onSystemPrompt, onToolCall, onToolResult)은
	LLM이 보는 모든 데이터를 사용자에게 투명하게 전달하는 핵심 경로다.
	이 콜백들을 제거하거나 무시하면 안 된다.

	각 SSE 이벤트는 message 객체에 저장되어 MessageBubble에서 뱃지/카드/모달로 표시된다:
	  onMeta        → message.meta (company, stockCode, includedModules, dataYearRange)
	  onSnapshot    → message.snapshot (핵심 수치 카드)
	  onContext     → message.contexts[] (모듈별 데이터 뱃지)
	  onSystemPrompt → message.systemPrompt, message.userContent
	  onToolCall    → message.toolEvents[] (도구 호출 뱃지)
	  onToolResult  → message.toolEvents[] (도구 결과)
-->
<script>
	import "./app.css";
	import { askStream, fetchAiSuggestions } from "$lib/api.js";
	import {
		buildConversationHistory,
		createAskStreamCallbacks,
		getLastAssistantStockCode,
	} from "$lib/ai/chatStream.js";
	import { normalizeProvider } from "$lib/ai/providerProfile.js";
	import { cn, createSwipeHandler } from "$lib/utils.js";
	import { createConversationsStore } from "$lib/stores/conversations.svelte.js";
	import { createWorkspaceStore } from "$lib/stores/workspace.svelte.js";
	import { createUiStore } from "$lib/stores/ui.svelte.js";
	import Sidebar from "$lib/components/Sidebar.svelte";
	import EmptyState from "$lib/components/EmptyState.svelte";
	import ChatArea from "$lib/components/ChatArea.svelte";
	import SearchModal from "$lib/components/SearchModal.svelte";
	import DeleteDialog from "$lib/components/DeleteDialog.svelte";
	import ToastNotification from "$lib/components/ToastNotification.svelte";
	import PanelResizer from "$lib/components/PanelResizer.svelte";
	import {
		Menu, PanelLeftClose, Coffee, Github, FileText, Search,
		Loader2, Settings, AlertCircle,
	} from "lucide-svelte";

	// ── Stores ──
	const ui = createUiStore();
	const store = createConversationsStore();
	const workspace = createWorkspaceStore();

	// ── State ──
	let inputText = $state("");
	let isLoading = $state(false);
	let currentStream = $state(null);
	let suggestedQuestions = $state([]);
	let onboardingDataReady = $state(null);
	let suggestionLoading = $state(false);
	let showSearchModal = $state(false);
	let suggestRequestId = 0;
	const suggestionCache = new Map();

	// ── 워치리스트 ──
	let watchlist = $state(JSON.parse(localStorage.getItem("dartlab-watchlist") || "[]"));
	function persistWatchlist() { localStorage.setItem("dartlab-watchlist", JSON.stringify(watchlist)); }
	function addToWatchlist(code, name) {
		if (watchlist.some(w => w.code === code)) return;
		watchlist = [...watchlist, { code, name }];
		persistWatchlist();
	}
	function removeFromWatchlist(code) {
		watchlist = watchlist.filter(w => w.code !== code);
		persistWatchlist();
	}
	// ── 리사이저블 사이드바 ──
	let sidebarWidth = $state(260);
	function handleSidebarResize(delta) {
		sidebarWidth = Math.max(180, Math.min(400, sidebarWidth + delta));
	}

	// ── 모바일 스와이프 ──
	$effect(() => {
		if (!ui.isMobile) return;
		return createSwipeHandler(document.body, {
			edgeOnly: true,
			edgeWidth: 30,
			onSwipeRight: () => { if (!ui.sidebarOpen) ui.sidebarOpen = true; },
			onSwipeLeft: () => { if (ui.sidebarOpen) ui.sidebarOpen = false; },
		});
	});

	// ── Derived ──
	let activeMessages = $derived(store.active?.messages || []);
	let hasConversation = $derived(store.active && store.active.messages.length > 0);
	let noProviderAvailable = $derived(
		!ui.statusLoading && (
			!ui.activeProvider
			|| !ui.providers[ui.activeProvider]?.available
			|| !ui.providerSupportsRole(ui.activeProvider, ui.CHAT_ROLE)
		)
	);

	// ── Init ──
	let statusLoaded = false;
	$effect(() => { if (!statusLoaded) { statusLoaded = true; ui.loadStatus(); } });

	$effect(() => {
		ui.checkMobile();
		const onResize = () => ui.checkMobile();
		window.addEventListener("resize", onResize);
		return () => window.removeEventListener("resize", onResize);
	});

	$effect(() => {
		const stockCode = workspace.selectedCompany?.stockCode || "";
		if (!stockCode) {
			suggestedQuestions = [];
			onboardingDataReady = null;
			suggestionLoading = false;
			return;
		}

		const cached = suggestionCache.get(stockCode);
		if (cached) {
			suggestedQuestions = cached.suggestions;
			onboardingDataReady = cached.dataReady;
			suggestionLoading = false;
			return;
		}

		const requestId = ++suggestRequestId;
		suggestedQuestions = [];
		onboardingDataReady = null;
		suggestionLoading = true;
		fetchAiSuggestions(stockCode)
			.then((payload) => {
				if (requestId !== suggestRequestId) return;
				const next = {
					suggestions: payload?.suggestions || [],
					dataReady: payload?.dataReady || null,
				};
				suggestionCache.set(stockCode, next);
				suggestedQuestions = next.suggestions;
				onboardingDataReady = next.dataReady;
				suggestionLoading = false;
			})
			.catch(() => {
				if (requestId !== suggestRequestId) return;
				suggestedQuestions = [];
				onboardingDataReady = null;
				suggestionLoading = false;
			});
	});

	// ── Helpers ──
	function appendRenderViews(views) {
		if (!views?.length) return;
		const conv = store.active;
		if (!conv) return;
		const last = conv.messages[conv.messages.length - 1];
		const prev = last?.renderViews || [];
		store.updateLastMessage({ renderViews: [...prev, ...views] });
	}

	function syncSelectedCompanyFromConversation(conv) {
		if (!conv) {
			workspace.clearSelectedCompany();
			return;
		}
		for (let i = conv.messages.length - 1; i >= 0; i--) {
			const msg = conv.messages[i];
			if (msg.role === "assistant" && (msg.meta?.stockCode || msg.meta?.company || msg.company)) {
				workspace.syncCompanyFromMessage(
					{ company: msg.meta?.company || msg.company, stockCode: msg.meta?.stockCode },
					workspace.selectedCompany
				);
				return;
			}
		}
		workspace.clearSelectedCompany();
	}

	// ── Chat actions ──
	function handleNewChat() {
		store.createConversation();
		workspace.resetChatContext();
		inputText = "";
		isLoading = false;
		if (currentStream) { currentStream.abort(); currentStream = null; }
	}

	function handleSelectConversation(id) {
		store.setActive(id);
		syncSelectedCompanyFromConversation(store.active);
		inputText = "";
		isLoading = false;
		if (currentStream) { currentStream.abort(); currentStream = null; }
	}

	function handleDeleteConversation(id) {
		ui.deleteConfirmMode = "single";
		ui.deleteConfirmId = id;
	}
	function handleDeleteAllConversations() {
		ui.deleteConfirmMode = "all";
		ui.deleteConfirmId = "__all__";
	}

	function confirmDelete() {
		if (ui.deleteConfirmId) {
			if (ui.deleteConfirmMode === "all") {
				store.clearAll();
				workspace.resetChatContext();
				inputText = "";
				isLoading = false;
				if (currentStream) { currentStream.abort(); currentStream = null; }
				ui.deleteConfirmId = null;
				ui.deleteConfirmMode = "single";
				return;
			}
			store.deleteConversation(ui.deleteConfirmId);
			if (store.active) syncSelectedCompanyFromConversation(store.active);
			else workspace.resetChatContext();
			ui.deleteConfirmId = null;
			ui.deleteConfirmMode = "single";
		}
	}

	async function sendMessage(prefilledQuestion = null) {
		const question = (prefilledQuestion ?? inputText).trim();
		if (!question || isLoading) return;

		if (!ui.activeProvider || !ui.providers[ui.activeProvider]?.available) {
			ui.showToast("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요.");
			ui.openSettings();
			return;
		}
		const chatProvider = await ui.resolveChatProvider();
		if (!chatProvider) { ui.openSettings(); return; }

		if (!store.activeId) store.createConversation();
		const streamConvId = store.activeId;

		store.addMessage("user", question);
		inputText = "";
		isLoading = true;

		store.addMessage("assistant", "");
		store.updateLastMessage({ loading: true, startedAt: Date.now() });

		const conv = store.active;
		const { history, lastAnalyzedCode } = buildConversationHistory(conv);
		const companyHint = workspace.selectedCompany?.stockCode || lastAnalyzedCode || getLastAssistantStockCode(conv);

		const requestOptions = {
			provider: chatProvider.provider,
			role: ui.CHAT_ROLE,
			model: chatProvider.model,
		};
		const handleStreamSettled = () => { isLoading = false; currentStream = null; };
		const callbacks = createAskStreamCallbacks({
			store, workspace, uiStore: ui, streamConvId,
			showToast: (msg, type) => ui.showToast(msg, type),
			appendRenderViews,
			onStreamSettled: handleStreamSettled,
			bumpScroll: null,
			onCompanySelect: handleCompanySelect,
		});

		const stream = askStream(companyHint, question, requestOptions, callbacks, history);
		currentStream = stream;
	}

	function stopStream() {
		if (currentStream) {
			currentStream.abort();
			currentStream = null;
			isLoading = false;
			store.updateLastMessage({ loading: false });
			store.flush();
		}
	}

	function handleEditResend(newText) {
		if (!newText || isLoading) return;
		sendMessage(newText);
	}

	function handleRegenerate() {
		const conv = store.active;
		if (!conv || conv.messages.length < 2) return;
		let lastUserMsg = "";
		for (let i = conv.messages.length - 1; i >= 0; i--) {
			if (conv.messages[i].role === "user") { lastUserMsg = conv.messages[i].text; break; }
		}
		if (!lastUserMsg) return;
		store.removeLastMessage();
		store.removeLastMessage();
		inputText = lastUserMsg;
		requestAnimationFrame(() => { sendMessage(); });
	}

	function handleExport() {
		const conv = store.active;
		if (!conv) return;
		let md = `# ${conv.title}\n\n`;
		for (const msg of conv.messages) {
			if (msg.role === "user") md += `## You\n\n${msg.text}\n\n`;
			else if (msg.role === "assistant" && msg.text) md += `## DartLab\n\n${msg.text}\n\n`;
		}
		const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${conv.title || "dartlab-chat"}.md`;
		a.click();
		URL.revokeObjectURL(url);
		ui.showToast("대화가 마크다운으로 내보내졌습니다", "success");
	}

	function handleCompanySelect(company) {
		workspace.selectCompany(company);
	}

	// ── Keyboard shortcuts ──
	function handleGlobalKeydown(e) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'n') { e.preventDefault(); handleNewChat(); }
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); showSearchModal = true; }
		if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'S') { e.preventDefault(); ui.toggleSidebar(); }
		if (e.key === 'Escape' && showSearchModal) { showSearchModal = false; }
		else if (e.key === 'Escape' && ui.settingsOpen) { ui.settingsOpen = false; }
		else if (e.key === 'Escape' && ui.deleteConfirmId) { ui.deleteConfirmId = null; }
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="flex h-screen bg-dl-bg-dark overflow-hidden">
	<!-- Sidebar -->
	{#if ui.isMobile && ui.sidebarOpen}
		<button class="sidebar-overlay" onclick={() => { ui.sidebarOpen = false; }} aria-label="사이드바 닫기"></button>
	{/if}
	<div class={ui.isMobile ? (ui.sidebarOpen ? "sidebar-mobile" : "hidden") : ""}>
		<Sidebar
			conversations={store.conversations}
			activeId={store.activeId}
			open={ui.isMobile ? true : ui.sidebarOpen}
			width={sidebarWidth}
			version={ui.appVersion}
			onNewChat={() => { handleNewChat(); if (ui.isMobile) ui.sidebarOpen = false; }}
			onSelect={(id) => { handleSelectConversation(id); if (ui.isMobile) ui.sidebarOpen = false; }}
			onDelete={handleDeleteConversation}
			onDeleteAll={handleDeleteAllConversations}
			onRename={(id, title) => { if (title) store.updateTitle(id, title); }}
			onOpenSearch={() => { showSearchModal = true; }}
		/>
		{#if !ui.isMobile && ui.sidebarOpen}
			<PanelResizer onResize={handleSidebarResize} />
		{/if}
	</div>

	<!-- Main -->
	<div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg">
		<!-- Top-left: sidebar toggle -->
		<div class="absolute top-2 left-3 z-20 pointer-events-auto flex items-center gap-1">
			<button
				class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"
				onclick={() => ui.toggleSidebar()}
			>
				{#if ui.sidebarOpen}
					<PanelLeftClose size={18} />
				{:else}
					<Menu size={18} />
				{/if}
			</button>
		</div>

		<!-- Top-right controls -->
		<div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto">
			<button
				class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors"
				onclick={() => { showSearchModal = true; }}
				title="종목 검색 (Ctrl+K)"
			>
				<Search size={14} />
			</button>
			<a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer"
				class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation">
				<FileText size={14} />
			</a>
			<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer"
				class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub">
				<Github size={14} />
			</a>
			<a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer"
				class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee">
				<Coffee size={14} />
			</a>
			<button
				class={cn(
					"flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",
					ui.statusLoading
						? "text-dl-text-dim"
						: noProviderAvailable
							? "text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15"
							: "text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"
				)}
				onclick={() => ui.openSettings()}
			>
				{#if ui.statusLoading}
					<Loader2 size={12} class="animate-spin" />
					<span>확인 중...</span>
				{:else if noProviderAvailable}
					<AlertCircle size={12} />
					<span>설정 필요</span>
				{:else}
					<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span>
					<span>{ui.providers[ui.activeProvider]?.label || ui.activeProvider}</span>
					{#if ui.activeModel}
						<span class="text-dl-text-dim">/</span>
						<span class="max-w-[80px] truncate">{ui.activeModel}</span>
					{/if}
				{/if}
				<Settings size={12} />
			</button>
		</div>

		<!-- Content: Chat only -->
		<div class="flex flex-1 min-h-0">
			<div class="min-w-0 flex-1 flex flex-col">
				{#if hasConversation}
					<ChatArea
						messages={activeMessages}
						{isLoading}
						bind:inputText
						selectedCompany={workspace.selectedCompany}
						suggestions={suggestedQuestions}
						dataReady={onboardingDataReady}
						suggestionLoading={suggestionLoading}
						providerLabel={ui.providers[ui.activeProvider]?.label || ui.activeProvider || null}
						modelLabel={ui.activeModel || null}
						onSend={sendMessage}
						onStop={stopStream}
						onRegenerate={handleRegenerate}
						onExport={handleExport}
						onEditResend={handleEditResend}
						onCompanySelect={handleCompanySelect}
						{watchlist}
						onAddWatch={addToWatchlist}
						onRemoveWatch={removeFromWatchlist}
					/>
				{:else}
					<EmptyState
						bind:inputText
						selectedCompany={workspace.selectedCompany}
						suggestions={suggestedQuestions}
						dataReady={onboardingDataReady}
						suggestionLoading={suggestionLoading}
						onSend={sendMessage}
						onCompanySelect={handleCompanySelect}
						{watchlist}
						onWatchlistClick={(item) => {
							handleCompanySelect({ stockCode: item.code, corpName: item.name, company: item.name });
						}}
					/>
				{/if}
			</div>
		</div>
	</div>

	<!-- 모바일 하단 탭 바 -->
	{#if ui.isMobile}
		<nav class="flex items-center justify-around h-12 border-t border-dl-border/30 bg-dl-bg-darker/95 backdrop-blur-sm flex-shrink-0 safe-area-bottom" aria-label="메인 탐색">
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors text-dl-text-dim"
				onclick={() => ui.toggleSidebar()}
			>
				<Menu size={18} />
				<span class="text-[9px] font-medium">대화</span>
			</button>
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors text-dl-text-dim"
				onclick={() => { showSearchModal = true; }}
			>
				<Search size={18} />
				<span class="text-[9px] font-medium">검색</span>
			</button>
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors text-dl-text-dim"
				onclick={() => ui.openSettings()}
			>
				<Settings size={18} />
				<span class="text-[9px] font-medium">설정</span>
			</button>
		</nav>
	{/if}
</div>

<!-- Modals -->
{#if ui.settingsOpen}
	{#await import("$lib/components/SettingsPanel.svelte") then { default: SettingsPanel }}
		<SettingsPanel {ui} />
	{/await}
{/if}
<SearchModal
	bind:open={showSearchModal}
	recentCompanies={workspace.recentCompanies}
	onSelect={handleCompanySelect}
	onAction={(id) => {
		if (id === "newChat") handleNewChat();
		else if (id === "openSettings") ui.openSettings();
		else if (id === "exportChat") handleExport();
	}}
/>
<DeleteDialog {ui} onConfirm={confirmDelete} />
<ToastNotification {ui} />
