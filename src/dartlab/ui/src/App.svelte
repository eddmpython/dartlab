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
	import { createViewerStore } from "$lib/stores/viewer.svelte.js";
	import { createUiStore } from "$lib/stores/ui.svelte.js";
	import { createRoomStore } from "$lib/stores/room.svelte.js";
	import Sidebar from "$lib/components/Sidebar.svelte";
	import EmptyState from "$lib/components/EmptyState.svelte";
	import ChatArea from "$lib/components/ChatArea.svelte";
	import RightPanel from "$lib/components/RightPanel.svelte";
	// 동적 import — 코드 스플리팅
	// DisclosureViewer, DashboardView, SettingsPanel은 사용자가 탭 전환/설정 열기 시 로드
	import SearchModal from "$lib/components/SearchModal.svelte";
	import DeleteDialog from "$lib/components/DeleteDialog.svelte";
	import ToastNotification from "$lib/components/ToastNotification.svelte";
	import PanelResizer from "$lib/components/PanelResizer.svelte";
	import {
		Menu, PanelLeftClose, Coffee, Github, FileText, Search,
		Loader2, Settings, AlertCircle,
		MessageSquare, BookOpen, BarChart3, Users
	} from "lucide-svelte";
	import RoomBar from "$lib/components/room/RoomBar.svelte";
	import RoomChat from "$lib/components/room/RoomChat.svelte";
	import FloatingReactions from "$lib/components/room/FloatingReactions.svelte";

	// ── Stores ──
	const ui = createUiStore();
	const store = createConversationsStore();
	const workspace = createWorkspaceStore();
	const viewerStore = createViewerStore();
	const room = createRoomStore(ui);

	// ── State (App-specific only) ──
	let inputText = $state("");
	let isLoading = $state(false);
	let currentStream = $state(null);
	let pendingBlockData = $state(null);
	let suggestedQuestions = $state([]);
	let onboardingDataReady = $state(null);
	let suggestionLoading = $state(false);
	let showSearchModal = $state(false);
	let showRoomChat = $state(false);
	let showRoomJoin = $state(false);
	let suggestRequestId = 0;
	const suggestionCache = new Map();

	// ── 리사이저블 패널 ──
	let sidebarWidth = $state(260);
	let rightPanelPct = $state(null);  // null = 기본값 사용

	function handleSidebarResize(delta) {
		sidebarWidth = Math.max(180, Math.min(400, sidebarWidth + delta));
	}

	function handleRightPanelResize(delta) {
		const total = window.innerWidth;
		const currentPct = rightPanelPct ?? 50;
		// delta가 음수면 패널 커짐 (왼쪽으로 드래그)
		const newPct = Math.max(25, Math.min(85, currentPct - (delta / total) * 100));
		rightPanelPct = newPct;
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
	let panelWidth = $derived(
		rightPanelPct != null ? `${rightPanelPct}%` : "50%"
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
		if (!statusLoaded) { statusLoaded = true; ui.loadStatus(); room.checkRoom(); }
	});

	// Room: 네비게이션 인바운드 (SSE → workspace)
	$effect(() => {
		const nav = room.navState;
		if (!nav || !room.joined || room.isNavFromRemote === false) return;
		if (nav.stockCode) {
			handleCompanySelectForViewer({ stockCode: nav.stockCode, corpName: nav.stockCode });
		}
		if (nav.topic) {
			workspace.setViewerTopic(nav.topic, nav.topicLabel || nav.topic);
		}
	});

	// Room: 페이지 떠날 때 정리
	$effect(() => {
		if (!room.joined) return;
		const onUnload = () => { room.leave(); };
		window.addEventListener("beforeunload", onUnload);
		return () => window.removeEventListener("beforeunload", onUnload);
	});

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
	// 패널 모드 변경 시 커스텀 폭 리셋
	$effect(() => {
		workspace.panelMode;  // track
		rightPanelPct = null;
	});

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
			bumpScroll: null,
			onCompanySelect: handleCompanySelectForViewer,
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
		// 편집한 사용자 메시지 이후의 모든 메시지를 제거하고 재전송
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

	// ── Navigation ──
	function handleCompanySelectForChat(company) {
		workspace.selectCompany(company);
		workspace.switchView("chat");
		pendingBlockData = null;
		if (room.joined) room.navigate({ stockCode: company.stockCode });
	}

	function handleCompanySelectForViewer(company) {
		workspace.openViewer(company);
		if (room.joined) room.navigate({ stockCode: company.stockCode });
	}

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
		if (room.joined) room.navigate({ topic: data.topic });
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
			if (e.key === '3') { workspace.switchView('dashboard'); return; }
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
			<aside class="surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden" style="{ui.sidebarOpen ? `width: ${sidebarWidth}px` : 'width: 52px'}">
				{#if ui.sidebarOpen}
					<div class="flex flex-col h-full" style="min-width: {sidebarWidth}px">
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
									onclick={() => { handleCompanySelectForViewer(company); if (ui.isMobile) ui.sidebarOpen = false; }}
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
				width={sidebarWidth}
				version={ui.appVersion}
				onNewChat={() => { handleNewChat(); if (ui.isMobile) ui.sidebarOpen = false; }}
				onSelect={(id) => { handleSelectConversation(id); if (ui.isMobile) ui.sidebarOpen = false; }}
				onDelete={handleDeleteConversation}
				onDeleteAll={handleDeleteAllConversations}
				onRename={(id, title) => { if (title) store.updateTitle(id, title); }}
				onOpenSearch={() => { showSearchModal = true; }}
			/>
		{/if}
		{#if !ui.isMobile && ui.sidebarOpen}
			<PanelResizer onResize={handleSidebarResize} />
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

			<!-- View tabs (모바일은 하단 탭 바 사용) -->
			<div class="items-center ml-2 rounded-lg bg-dl-bg-card/60 border border-dl-border/20 p-0.5 {ui.isMobile ? 'hidden' : 'flex'}">
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
				<button
					class="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors {workspace.activeView === 'dashboard'
						? 'text-dl-text bg-dl-surface-active font-medium'
						: 'text-dl-text-dim hover:text-dl-text-muted'}"
					onclick={() => workspace.switchView('dashboard')}
				>
					<BarChart3 size={12} />
					<span>Dashboard</span>
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

		<!-- Room 참여 안내 (데스크톱, 미참여 시) -->
		{#if !ui.isMobile && room.roomAvailable && !room.joined}
			<button
				class="flex items-center justify-center gap-2 h-7 bg-dl-accent/10 border-b border-dl-accent/20 text-xs text-dl-accent hover:bg-dl-accent/15 transition-colors"
				onclick={() => { showRoomJoin = true; }}
			>
				<Users size={12} />
				<span>협업 세션이 활성 중입니다 — 클릭하여 참여</span>
			</button>
		{/if}

		<!-- Room Bar (데스크톱) -->
		{#if !ui.isMobile && room.joined}
			<RoomBar
				{room}
				onToggleChat={() => { showRoomChat = !showRoomChat; if (showRoomChat) room.markRoomViewed(); }}
				onLeave={() => room.leave()}
			/>
		{/if}

		<!-- Content -->
		<div class="flex flex-1 min-h-0">
			{#if workspace.activeView === "room" && room.joined}
				<div class="min-w-0 flex-1">
					<RoomChat {room} showMembers={true} />
				</div>
			{:else if workspace.activeView === "viewer"}
				<div class="min-w-0 flex-1">
					{#await import("$lib/components/DisclosureViewer.svelte") then { default: DisclosureViewer }}
						<DisclosureViewer
							viewer={viewerStore}
							company={workspace.selectedCompany}
							recentCompanies={workspace.recentCompanies}
							onCompanySelect={handleCompanySelectForViewer}
							onAskAI={handleAskFromViewer}
							onTopicChange={(topic, label) => workspace.setViewerTopic(topic, label)}
						/>
					{/await}
				</div>
			{:else if workspace.activeView === "dashboard"}
				<div class="min-w-0 flex-1">
					{#await import("$lib/components/DashboardView.svelte") then { default: DashboardView }}
						<DashboardView
							company={workspace.selectedCompany}
							recentCompanies={workspace.recentCompanies}
							toc={viewerStore?.toc}
							onCompanySelect={handleCompanySelectForViewer}
							onNavigateTopic={(topic) => handleViewerNavigate({ topic })}
							onAskAboutModule={(mod) => {
								workspace.switchView("chat");
								inputText = `${mod} 모듈에 대해 설명해줘`;
							}}
							onNotify={(msg, type) => ui.showToast(msg, type)}
						onOpenSearch={() => { showSearchModal = true; }}
						/>
					{/await}
				</div>
			{:else}
				<!-- Chat -->
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
							viewerContext={workspace.viewerTopic ? { topic: workspace.viewerTopic, topicLabel: workspace.viewerTopicLabel, period: workspace.viewerPeriod } : null}
							pendingBlockLabel={pendingBlockData ? (pendingBlockData.topicLabel || pendingBlockData.topic || "블록") : null}
							onClearBlock={() => { pendingBlockData = null; }}
							providerLabel={ui.providers[ui.activeProvider]?.label || ui.activeProvider || null}
							modelLabel={ui.activeModel || null}
							onSend={sendMessage}
							onStop={stopStream}
							onRegenerate={handleRegenerate}
							onExport={handleExport}
							onOpenData={handleOpenData}
							onOpenEvidence={handleOpenEvidence}
							onOpenArtifact={(view) => workspace.openArtifact(view)}
							onEditResend={handleEditResend}
							onCompanySelect={handleCompanySelectForChat}
						/>
					{:else}
						<EmptyState
							bind:inputText
							selectedCompany={workspace.selectedCompany}
							suggestions={suggestedQuestions}
							dataReady={onboardingDataReady}
							suggestionLoading={suggestionLoading}
							onSend={sendMessage}
							onCompanySelect={handleCompanySelectForChat}
							onOpenViewer={handleCompanySelectForViewer}
						/>
					{/if}
				</div>

				{#if !ui.isMobile && workspace.panelOpen}
					<PanelResizer onResize={handleRightPanelResize} />
					<div
						class="flex-shrink-0 transition-all duration-300"
						style="width: {panelWidth}; min-width: 360px; max-width: 85vw;"
					>
						<RightPanel
							mode={workspace.panelMode}
							data={workspace.panelData}
							onClose={() => workspace.closePanel()}
							artifactHistory={workspace.artifactHistory}
							artifactIndex={workspace.artifactIndex}
							onNavigateArtifact={(idx) => workspace.navigateArtifact(idx)}
						/>
					</div>
				{/if}
			{/if}

			<!-- 데스크톱 Room Chat 사이드 패널 -->
			{#if !ui.isMobile && showRoomChat && room.joined}
				<div class="flex-shrink-0 w-72 border-l border-dl-border/30">
					<RoomChat {room} showMembers={false} />
				</div>
			{/if}
		</div>
	</div>

	<!-- 모바일 하단 탭 바 -->
	{#if ui.isMobile}
		<nav class="flex items-center justify-around h-12 border-t border-dl-border/30 bg-dl-bg-darker/95 backdrop-blur-sm flex-shrink-0 safe-area-bottom" aria-label="메인 탐색">
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors {workspace.activeView === 'chat' ? 'text-dl-accent' : 'text-dl-text-dim'}"
				onclick={() => workspace.switchView('chat')}
			>
				<MessageSquare size={18} />
				<span class="text-[9px] font-medium">Chat</span>
			</button>
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors {workspace.activeView === 'viewer' ? 'text-dl-accent' : 'text-dl-text-dim'}"
				onclick={() => workspace.switchView('viewer')}
			>
				<BookOpen size={18} />
				<span class="text-[9px] font-medium">Viewer</span>
			</button>
			<button
				class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors {workspace.activeView === 'dashboard' ? 'text-dl-accent' : 'text-dl-text-dim'}"
				onclick={() => workspace.switchView('dashboard')}
			>
				<BarChart3 size={18} />
				<span class="text-[9px] font-medium">분석</span>
			</button>
			{#if room.roomAvailable || room.joined}
				<button
					class="flex flex-col items-center gap-0.5 flex-1 py-1.5 transition-colors relative
						{workspace.activeView === 'room' ? 'text-dl-accent' : 'text-dl-text-dim'}"
					onclick={() => {
						if (!room.joined) { showRoomJoin = true; }
						else { workspace.switchView('room'); room.markRoomViewed(); }
					}}
				>
					<Users size={18} />
					<span class="text-[9px] font-medium">Room</span>
					{#if room.unreadCount > 0}
						<span class="absolute top-0.5 right-1/4 w-3.5 h-3.5 rounded-full bg-dl-primary text-white text-[8px] flex items-center justify-center font-bold">
							{room.unreadCount > 9 ? "9+" : room.unreadCount}
						</span>
					{/if}
				</button>
			{/if}
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
	onSelect={handleCompanySelectForViewer}
	onAction={(id) => {
		if (id === "newChat") handleNewChat();
		else if (id === "viewChat") workspace.switchView("chat");
		else if (id === "viewViewer") workspace.switchView("viewer");
		else if (id === "viewDashboard") workspace.switchView("dashboard");
		else if (id === "openSettings") ui.openSettings();
		else if (id === "exportChat") handleExport();
	}}
/>
{#if showRoomJoin && room.roomAvailable}
	{#await import("$lib/components/room/RoomJoinDialog.svelte") then { default: RoomJoinDialog }}
		<RoomJoinDialog {room} onClose={() => { showRoomJoin = false; }} />
	{/await}
{/if}
{#if room.joined}
	<FloatingReactions reactions={room.reactions} />
{/if}
<DeleteDialog {ui} onConfirm={confirmDelete} />
<ToastNotification {ui} />
