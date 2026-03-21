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
	import { askStream } from "$lib/api.js";
	import {
		buildConversationHistory,
		createAskStreamCallbacks,
		getLastAssistantStockCode,
	} from "$lib/ai/chatStream.js";
	import { normalizeProvider } from "$lib/ai/providerProfile.js";
	import { cn } from "$lib/utils.js";
	import { createConversationsStore } from "$lib/stores/conversations.svelte.js";
	import { createWorkspaceStore } from "$lib/stores/workspace.svelte.js";
	import { createViewerStore } from "$lib/stores/viewer.svelte.js";
	import { createUiStore } from "$lib/stores/ui.svelte.js";
	import Sidebar from "$lib/components/Sidebar.svelte";
	import EmptyState from "$lib/components/EmptyState.svelte";
	import ChatArea from "$lib/components/ChatArea.svelte";
	import RightPanel from "$lib/components/RightPanel.svelte";
	import DisclosureViewer from "$lib/components/DisclosureViewer.svelte";
	import SettingsPanel from "$lib/components/SettingsPanel.svelte";
	import SearchModal from "$lib/components/SearchModal.svelte";
	import DeleteDialog from "$lib/components/DeleteDialog.svelte";
	import ToastNotification from "$lib/components/ToastNotification.svelte";
	import {
		Menu, PanelLeftClose, Coffee, Github, FileText, Search,
		Loader2, Settings, AlertCircle,
		MessageSquare, BookOpen
	} from "lucide-svelte";

	// ── Stores ──
	const ui = createUiStore();
	const store = createConversationsStore();
	const workspace = createWorkspaceStore();
	const viewerStore = createViewerStore();

	// ── State (App-specific only) ──
	let inputText = $state("");
	let isLoading = $state(false);
	let currentStream = $state(null);
	let pendingBlockData = $state(null);
	let scrollTrigger = $state(0);
	let showSearchModal = $state(false);

	// ── Derived ──
	let panelWidth = $derived(
		ui.viewerFullscreen ? "100%" :
		workspace.panelMode === "viewer" ? "65%" : "50%"
	);
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
	$effect(() => {
		if (!statusLoaded) { statusLoaded = true; ui.loadStatus(); }
	});

	$effect(() => {
		ui.checkMobile();
		const onResize = () => ui.checkMobile();
		window.addEventListener("resize", onResize);
		return () => window.removeEventListener("resize", onResize);
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
		if (!conv) return;
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
	}

	// ── Chat actions ──
	function handleNewChat() {
		store.createConversation();
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

	function handleDeleteConversation(id) { ui.deleteConfirmId = id; }

	function confirmDelete() {
		if (ui.deleteConfirmId) {
			store.deleteConversation(ui.deleteConfirmId);
			ui.deleteConfirmId = null;
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
		scrollTrigger++;

		const conv = store.active;
		const { history, lastAnalyzedCode } = buildConversationHistory(conv);
		const companyHint = workspace.selectedCompany?.stockCode || lastAnalyzedCode || getLastAssistantStockCode(conv);

		const viewContext = workspace.getViewContext();
		if (pendingBlockData && viewContext) { viewContext.data = pendingBlockData; }
		pendingBlockData = null;

		const requestOptions = {
			provider: chatProvider.provider,
			role: ui.CHAT_ROLE,
			model: chatProvider.model,
			viewContext,
		};
		const handleStreamSettled = () => { isLoading = false; currentStream = null; };
		const callbacks = createAskStreamCallbacks({
			store, workspace, viewerStore, uiStore: ui, streamConvId,
			handleViewerNavigate,
			showToast: (msg, type) => ui.showToast(msg, type),
			appendRenderViews,
			onStreamSettled: handleStreamSettled,
			bumpScroll: () => { scrollTrigger += 1; },
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

	// ── Navigation ──
	function handleCompanySelect(company) { workspace.openViewer(company); }

	function handleOpenData(data) { workspace.openData(data); }
	function handleOpenEvidence(section, index = null) { workspace.openEvidence(section, index); }

	function handleAskFromViewer(selectedText, blockData = null) {
		workspace.switchView("chat");
		const topicLabel = viewerStore.topicData?.topicLabel || "";
		const prefix = topicLabel ? `[${topicLabel}] ` : "";
		if (blockData) {
			pendingBlockData = blockData;
			inputText = `${prefix}이 블록을 분석해줘`;
		} else {
			pendingBlockData = null;
			inputText = `${prefix}"${selectedText}" — 이 내용에 대해 설명해줘`;
		}
		requestAnimationFrame(() => {
			const textarea = document.querySelector(".input-textarea");
			if (textarea) textarea.focus();
		});
	}

	async function handleViewerNavigate(data) {
		if (data?.stockCode && workspace.selectedCompany?.stockCode !== data.stockCode) {
			const nextCompany = {
				...(workspace.selectedCompany || {}),
				stockCode: data.stockCode,
				corpName: data.company || workspace.selectedCompany?.corpName || data.stockCode,
				company: data.company || workspace.selectedCompany?.company || data.stockCode,
				market: workspace.selectedCompany?.market || "",
			};
			workspace.selectCompany(nextCompany);
			await viewerStore.loadCompany?.(data.stockCode);
		}
		if (!data?.topic) return;
		workspace.switchView("viewer");
		await viewerStore.selectTopic?.(data.topic, data.chapter || null);
	}

	// ── Keyboard shortcuts ──
	function handleGlobalKeydown(e) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'n') { e.preventDefault(); handleNewChat(); }
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); showSearchModal = true; }
		if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'S') { e.preventDefault(); ui.toggleSidebar(); }
		if (e.key === 'Escape' && showSearchModal) { showSearchModal = false; }
		else if (e.key === 'Escape' && ui.settingsOpen) { ui.settingsOpen = false; }
		else if (e.key === 'Escape' && ui.deleteConfirmId) { ui.deleteConfirmId = null; }
		else if (e.key === 'Escape' && workspace.panelOpen) { workspace.closePanel(); }

		const tag = e.target?.tagName;
		const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || e.target?.isContentEditable;
		if (!isInput && !e.ctrlKey && !e.metaKey && !e.altKey) {
			if (e.key === '1') { workspace.switchView('chat'); return; }
			if (e.key === '2') { workspace.switchView('viewer'); return; }
		}
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="flex h-screen bg-dl-bg-dark overflow-hidden">
	<!-- Sidebar -->
	{#if ui.isMobile && ui.sidebarOpen}
		<button class="sidebar-overlay" onclick={() => { ui.sidebarOpen = false; }} aria-label="사이드바 닫기"></button>
	{/if}
	<div class={ui.isMobile ? (ui.sidebarOpen ? "sidebar-mobile" : "hidden") : ""}>
		{#if workspace.activeView === "viewer"}
			<!-- Viewer sidebar: 최근 종목 -->
			<aside class="surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden {ui.sidebarOpen ? 'w-[260px]' : 'w-[52px]'}">
				{#if ui.sidebarOpen}
					<div class="flex flex-col h-full min-w-[260px]">
						<div class="border-b border-dl-border/40 px-4 pt-4 pb-3">
							<div class="flex items-center gap-2.5">
								<img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm" />
								<div>
									<div class="text-sm font-semibold text-dl-text">공시뷰어</div>
									<div class="text-[10px] text-dl-text-dim">Disclosure Viewer</div>
								</div>
							</div>
						</div>
						<div class="flex-1 overflow-y-auto px-2 py-2">
							<div class="text-[10px] text-dl-text-dim uppercase tracking-widest font-semibold px-2 mb-2">최근 종목</div>
							{#each workspace.recentCompanies || [] as company}
								<button
									class="w-full text-left px-3 py-2 rounded-lg text-[12px] transition-colors mb-0.5
										{workspace.selectedCompany?.stockCode === company.stockCode
											? 'bg-dl-accent/10 text-dl-accent-light border border-dl-accent/20'
											: 'text-dl-text-muted hover:bg-white/5 hover:text-dl-text'}"
									onclick={() => { handleCompanySelect(company); if (ui.isMobile) ui.sidebarOpen = false; }}
								>
									<div class="font-medium">{company.name}</div>
									<div class="text-[10px] text-dl-text-dim">{company.stockCode}</div>
								</button>
							{:else}
								<div class="px-3 py-4 text-[11px] text-dl-text-dim text-center">
									아직 조회한 종목이 없습니다
								</div>
							{/each}
						</div>
						{#if ui.appVersion}
							<div class="border-t border-dl-border/30 px-4 py-2 text-[10px] text-dl-text-dim/50">
								v{ui.appVersion}
							</div>
						{/if}
					</div>
				{:else}
					<div class="flex flex-col items-center py-4 gap-2">
						<img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full opacity-60" />
					</div>
				{/if}
			</aside>
		{:else}
			<Sidebar
				conversations={store.conversations}
				activeId={store.activeId}
				open={ui.isMobile ? true : ui.sidebarOpen}
				version={ui.appVersion}
				onNewChat={() => { handleNewChat(); if (ui.isMobile) ui.sidebarOpen = false; }}
				onSelect={(id) => { handleSelectConversation(id); if (ui.isMobile) ui.sidebarOpen = false; }}
				onDelete={handleDeleteConversation}
				onOpenSearch={() => { showSearchModal = true; }}
			/>
		{/if}
	</div>

	<!-- Main -->
	<div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg">
		<!-- Top-left: sidebar toggle + view tabs -->
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

			<!-- View tabs -->
			<div class="flex items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5">
				<button
					class="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors {workspace.activeView === 'chat'
						? 'text-dl-text bg-dl-surface-active font-medium'
						: 'text-dl-text-dim hover:text-dl-text-muted'}"
					onclick={() => workspace.switchView('chat')}
				>
					<MessageSquare size={12} />
					<span>Chat</span>
				</button>
				<button
					class="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors {workspace.activeView === 'viewer'
						? 'text-dl-text bg-dl-surface-active font-medium'
						: 'text-dl-text-dim hover:text-dl-text-muted'}"
					onclick={() => workspace.switchView('viewer')}
				>
					<BookOpen size={12} />
					<span>Viewer</span>
				</button>
			</div>
		</div>

		<!-- Top-right fixed controls -->
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

		<!-- Content -->
		<div class="flex flex-1 min-h-0">
			{#if workspace.activeView === "viewer"}
				<div class="min-w-0 flex-1 pt-10">
					<DisclosureViewer
						viewer={viewerStore}
						company={workspace.selectedCompany}
						recentCompanies={workspace.recentCompanies}
						onCompanySelect={handleCompanySelect}
						onAskAI={handleAskFromViewer}
						onTopicChange={(topic, label) => workspace.setViewerTopic(topic, label)}
					/>
				</div>
			{:else}
				<div class="min-w-0 flex-1 flex flex-col">
					{#if hasConversation}
						<ChatArea
							messages={activeMessages}
							{isLoading}
							{scrollTrigger}
							bind:inputText
							selectedCompany={workspace.selectedCompany}
							viewerContext={workspace.viewerTopic ? { topic: workspace.viewerTopic, topicLabel: workspace.viewerTopicLabel, period: workspace.viewerPeriod } : null}
							pendingBlockLabel={pendingBlockData ? (pendingBlockData.topicLabel || pendingBlockData.topic || "블록") : null}
							onClearBlock={() => { pendingBlockData = null; }}
							onSend={sendMessage}
							onStop={stopStream}
							onRegenerate={handleRegenerate}
							onExport={handleExport}
							onOpenData={handleOpenData}
							onOpenEvidence={handleOpenEvidence}
							onCompanySelect={handleCompanySelect}
						/>
					{:else}
						<EmptyState
							bind:inputText
							onSend={sendMessage}
							onCompanySelect={handleCompanySelect}
						/>
					{/if}
				</div>

				{#if !ui.isMobile && workspace.panelOpen}
					<div
						class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"
						style="width: {panelWidth}; min-width: 360px; {ui.viewerFullscreen ? '' : 'max-width: 75vw;'}"
					>
						<RightPanel
							mode={workspace.panelMode}
							company={workspace.selectedCompany}
							data={workspace.panelData}
							onClose={() => { ui.viewerFullscreen = false; workspace.closePanel(); }}
							onTopicChange={(topic, label) => workspace.setViewerTopic(topic, label)}
							onFullscreen={() => { ui.viewerFullscreen = !ui.viewerFullscreen; }}
							isFullscreen={ui.viewerFullscreen}
						/>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- Modals -->
<SettingsPanel {ui} />
<SearchModal bind:open={showSearchModal} recentCompanies={workspace.recentCompanies} onSelect={handleCompanySelect} />
<DeleteDialog {ui} onConfirm={confirmDelete} />
<ToastNotification {ui} />
