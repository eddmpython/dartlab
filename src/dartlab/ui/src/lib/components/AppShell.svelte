<!--
	AppShell — dartlab AI 레이아웃 래퍼

	3가지 기능을 하나의 커맨드 센터로:
	1. 공시 뷰어 (메인, AI 없이 독립)
	2. AI 대화 (우측 패널, 토글)
	3. 데이터 탐색 + 엑셀 (우측 패널 탭)

	기존 컴포넌트 전부 재사용. 배치만 변경.
-->
<script>
	import { cn } from "$lib/utils.js";
	import SectionsViewer from "./SectionsViewer.svelte";
	import ChatArea from "./ChatArea.svelte";
	import DataExplorer from "./DataExplorer.svelte";
	import Sidebar from "./Sidebar.svelte";
	import AutocompleteInput from "./AutocompleteInput.svelte";
	import {
		MessageSquare, PanelRightClose, PanelRightOpen,
		Database, FileText, Download, Settings, Menu,
		PanelLeftClose, X, Github
	} from "lucide-svelte";

	let {
		// 상태 — App.svelte에서 주입
		store,
		workspace,
		// 회사
		selectedCompany = null,
		recentCompanies = [],
		// AI
		inputText = $bindable(""),
		isLoading = false,
		activeProvider = null,
		activeModel = null,
		providers = {},
		currentStream = null,
		// scrollTrigger removed — ChatArea uses rAF loop now
		// 콜백
		onSendMessage,
		onStopStream,
		onRegenerateResponse,
		onSelectCompany,
		onClearConversation,
		onDeleteConversation,
		onNotify,
		// 탭
		onAskAboutModule,
		// 이벤트
		evidenceMessage = null,
		activeEvidenceSection = null,
		selectedEvidenceIndex = null,
		// 설정
		showSettings = $bindable(false),
		// 버전
		version = "0.0.0",
	} = $props();

	// ── 패널 상태 ──
	let rightPanelOpen = $state(true);
	let rightPanelTab = $state("chat"); // "chat" | "data" | "history"
	let sidebarOpen = $state(false); // 모바일용
	let isMobile = $state(false);

	$effect(() => {
		const check = () => { isMobile = window.innerWidth < 768; };
		check();
		window.addEventListener("resize", check);
		return () => window.removeEventListener("resize", check);
	});

	// 대화가 있는지
	let hasMessages = $derived(store?.messages?.length > 0);

	function toggleRightPanel() {
		rightPanelOpen = !rightPanelOpen;
	}

	function setRightTab(tab) {
		rightPanelTab = tab;
		if (!rightPanelOpen) rightPanelOpen = true;
	}
</script>

<div class="dl-shell">
	<!-- ═══ 상단 바 ═══ -->
	<header class="dl-topbar">
		<div class="dl-topbar-left">
			{#if isMobile}
				<button class="dl-icon-btn" onclick={() => sidebarOpen = !sidebarOpen}>
					<Menu size={18} />
				</button>
			{/if}
			<div class="dl-brand">
				<span class="dl-brand-mark">D</span>
				<span class="dl-brand-text">DartLab</span>
			</div>

			<!-- 종목 검색 -->
			<div class="dl-company-area">
				{#if selectedCompany}
					<div class="dl-company-chip">
						<span class="dl-company-code">{selectedCompany.stockCode}</span>
						<span class="dl-company-name">{selectedCompany.corpName}</span>
					</div>
				{/if}
			</div>
		</div>

		<div class="dl-topbar-right">
			<!-- 우측 패널 탭 -->
			<div class="dl-panel-tabs">
				<button
					class={cn("dl-panel-tab", rightPanelTab === "chat" && rightPanelOpen && "active")}
					onclick={() => setRightTab("chat")}
				>
					<MessageSquare size={14} />
					<span>AI</span>
					{#if hasMessages}
						<span class="dl-dot"></span>
					{/if}
				</button>
				<button
					class={cn("dl-panel-tab", rightPanelTab === "data" && rightPanelOpen && "active")}
					onclick={() => setRightTab("data")}
				>
					<Database size={14} />
					<span>데이터</span>
				</button>
			</div>

			<button class="dl-icon-btn" onclick={toggleRightPanel}>
				{#if rightPanelOpen}
					<PanelRightClose size={16} />
				{:else}
					<PanelRightOpen size={16} />
				{/if}
			</button>

			<button class="dl-icon-btn" onclick={() => showSettings = true}>
				<Settings size={16} />
			</button>
		</div>
	</header>

	<!-- ═══ 메인 영역 ═══ -->
	<div class="dl-body">
		<!-- ── 좌측: 공시 뷰어 (메인) ── -->
		<main class={cn("dl-viewer-area", rightPanelOpen && "with-panel")}>
			{#if selectedCompany}
				<SectionsViewer
					stockCode={selectedCompany.stockCode}
					corpName={selectedCompany.corpName}
				/>
			{:else}
				<!-- 빈 상태 — 검색 유도 -->
				<div class="dl-empty-state">
					<div class="dl-empty-glow"></div>
					<div class="dl-empty-content">
						<div class="dl-empty-icon">
							<FileText size={40} strokeWidth={1} />
						</div>
						<h2>전자공시 탐색</h2>
						<p>종목을 검색하여 사업보고서를 분석하세요</p>
						<div class="dl-empty-search">
							<AutocompleteInput
								placeholder="종목명 또는 종목코드 검색..."
								onSubmit={(text) => {}}
								bind:value={inputText}
							/>
						</div>
						<div class="dl-empty-samples">
							<button onclick={() => onSelectCompany?.({ stockCode: "005930", corpName: "삼성전자" })}>
								삼성전자
							</button>
							<button onclick={() => onSelectCompany?.({ stockCode: "000660", corpName: "SK하이닉스" })}>
								SK하이닉스
							</button>
							<button onclick={() => onSelectCompany?.({ stockCode: "035420", corpName: "NAVER" })}>
								NAVER
							</button>
						</div>
					</div>
				</div>
			{/if}

			<!-- 버전 표시 -->
			<div class="dl-version">
				<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener" class="dl-version-link">
					<Github size={12} />
					<span>v{version}</span>
				</a>
			</div>
		</main>

		<!-- ── 우측: AI + 데이터 패널 ── -->
		{#if rightPanelOpen}
			<aside class="dl-right-panel">
				{#if rightPanelTab === "chat"}
					<!-- AI 대화 -->
					<div class="dl-panel-content">
						{#if hasMessages}
							<ChatArea
								messages={store.messages}
								{isLoading}
								{activeProvider}
								{activeModel}
								{selectedCompany}
								{recentCompanies}
								bind:inputText
								onSend={onSendMessage}
								onStop={onStopStream}
								onRegenerate={onRegenerateResponse}
								onSelectCompany={onSelectCompany}
								onOpenExplorer={() => setRightTab("data")}
								onOpenEvidence={() => setRightTab("data")}
								{onAskAboutModule}
								{onNotify}
							/>
						{:else}
							<div class="dl-chat-empty">
								<MessageSquare size={28} strokeWidth={1} class="text-dl-text-dim/40" />
								<p class="text-[13px] text-dl-text-dim mt-2">AI에게 질문하세요</p>
								<p class="text-[11px] text-dl-text-dim/60 mt-1">
									선택한 종목의 공시를 분석합니다
								</p>
								<div class="dl-chat-input-wrap">
									<AutocompleteInput
										placeholder="질문을 입력하세요..."
										onSubmit={onSendMessage}
										bind:value={inputText}
										loading={isLoading}
									/>
								</div>
							</div>
						{/if}
					</div>

				{:else if rightPanelTab === "data"}
					<!-- 데이터 탐색 -->
					<div class="dl-panel-content">
						<DataExplorer
							{selectedCompany}
							{recentCompanies}
							activeTab={workspace?.activeTab || "explore"}
							{evidenceMessage}
							{activeEvidenceSection}
							{selectedEvidenceIndex}
							onSelectCompany={onSelectCompany}
							onChangeTab={(tab) => workspace?.setTab?.(tab)}
							{onAskAboutModule}
							{onNotify}
							onClose={() => { rightPanelOpen = false; }}
						/>
					</div>
				{/if}
			</aside>
		{/if}
	</div>

	<!-- 모바일 사이드바 오버레이 -->
	{#if isMobile && sidebarOpen}
		<div class="dl-overlay" onclick={() => sidebarOpen = false}></div>
		<div class="dl-mobile-sidebar">
			<Sidebar
				conversations={store.conversations}
				activeId={store.activeId}
				onSelect={(id) => { store.setActive(id); sidebarOpen = false; }}
				onNew={() => { store.newConversation(); sidebarOpen = false; }}
				onDelete={onDeleteConversation}
				onClear={onClearConversation}
			/>
		</div>
	{/if}
</div>

<style>
	/* ═══ Shell ═══ */
	.dl-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}

	/* ═══ 상단 바 ═══ */
	.dl-topbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		height: 44px;
		padding: 0 12px;
		background: var(--color-dl-bg-card);
		border-bottom: 1px solid var(--color-dl-border);
		flex-shrink: 0;
		z-index: 20;
	}
	.dl-topbar-left {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.dl-topbar-right {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	/* 브랜드 */
	.dl-brand {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.dl-brand-mark {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--color-dl-primary), var(--color-dl-accent));
		border-radius: 6px;
		font-weight: 800;
		font-size: 13px;
		color: white;
	}
	.dl-brand-text {
		font-weight: 700;
		font-size: 15px;
		color: var(--color-dl-text);
		letter-spacing: -0.3px;
	}

	/* 회사 칩 */
	.dl-company-area {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.dl-company-chip {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 3px 10px;
		background: var(--color-dl-surface-active);
		border: 1px solid rgba(234, 70, 71, 0.2);
		border-radius: 6px;
	}
	.dl-company-code {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--color-dl-primary-light);
	}
	.dl-company-name {
		font-size: 12px;
		font-weight: 600;
		color: var(--color-dl-text);
	}

	/* 패널 탭 */
	.dl-panel-tabs {
		display: flex;
		gap: 2px;
		background: var(--color-dl-bg-darker);
		border-radius: 8px;
		padding: 2px;
	}
	.dl-panel-tab {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 4px 10px;
		border: none;
		border-radius: 6px;
		background: transparent;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		font-size: 11px;
		transition: all var(--motion-fast);
		position: relative;
	}
	.dl-panel-tab:hover {
		color: var(--color-dl-text-muted);
	}
	.dl-panel-tab.active {
		background: var(--color-dl-bg-card);
		color: var(--color-dl-text);
		box-shadow: var(--shadow-soft);
	}
	.dl-dot {
		width: 5px;
		height: 5px;
		background: var(--color-dl-primary);
		border-radius: 50%;
	}

	/* 아이콘 버튼 */
	.dl-icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		transition: all var(--motion-fast);
	}
	.dl-icon-btn:hover {
		background: var(--color-dl-bg-card-hover);
		color: var(--color-dl-text);
	}

	/* ═══ 메인 ═══ */
	.dl-body {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	/* 공시 뷰어 영역 */
	.dl-viewer-area {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		position: relative;
		transition: all var(--motion-base);
	}

	/* 빈 상태 */
	.dl-empty-state {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		overflow: hidden;
	}
	.dl-empty-glow {
		position: absolute;
		width: 600px;
		height: 600px;
		background: radial-gradient(circle, rgba(234,70,71,0.04) 0%, transparent 70%);
		border-radius: 50%;
		pointer-events: none;
	}
	.dl-empty-content {
		position: relative;
		text-align: center;
		max-width: 400px;
		padding: 20px;
	}
	.dl-empty-icon {
		color: var(--color-dl-text-dim);
		opacity: 0.4;
		margin-bottom: 16px;
	}
	.dl-empty-content h2 {
		font-size: 20px;
		font-weight: 700;
		color: var(--color-dl-text);
		margin: 0 0 8px;
	}
	.dl-empty-content p {
		font-size: 13px;
		color: var(--color-dl-text-dim);
		margin: 0;
	}
	.dl-empty-search {
		margin-top: 24px;
		max-width: 320px;
		margin-left: auto;
		margin-right: auto;
	}
	.dl-empty-samples {
		display: flex;
		gap: 8px;
		justify-content: center;
		margin-top: 16px;
	}
	.dl-empty-samples button {
		padding: 4px 12px;
		border: 1px solid var(--color-dl-border);
		border-radius: 6px;
		background: var(--color-dl-bg-card);
		color: var(--color-dl-text-muted);
		cursor: pointer;
		font-size: 12px;
		transition: all var(--motion-fast);
	}
	.dl-empty-samples button:hover {
		border-color: var(--color-dl-primary);
		color: var(--color-dl-primary-light);
		background: var(--color-dl-surface-active);
	}

	/* 버전 */
	.dl-version {
		position: absolute;
		bottom: 8px;
		left: 12px;
		z-index: 5;
	}
	.dl-version-link {
		display: flex;
		align-items: center;
		gap: 4px;
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--color-dl-text-dim);
		text-decoration: none;
		opacity: 0.5;
		transition: opacity var(--motion-fast);
	}
	.dl-version-link:hover {
		opacity: 1;
		color: var(--color-dl-text-muted);
	}

	/* ═══ 우측 패널 ═══ */
	.dl-right-panel {
		width: 420px;
		display: flex;
		flex-direction: column;
		background: var(--color-dl-bg-card);
		border-left: 1px solid var(--color-dl-border);
		flex-shrink: 0;
		overflow: hidden;
		animation: dl-slide-in var(--motion-base) ease-out;
	}
	@keyframes dl-slide-in {
		from { transform: translateX(20px); opacity: 0; }
		to { transform: translateX(0); opacity: 1; }
	}

	.dl-panel-content {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	/* AI 빈 상태 */
	.dl-chat-empty {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}
	.dl-chat-input-wrap {
		margin-top: 20px;
		width: 100%;
		max-width: 340px;
	}

	/* ═══ 모바일 ═══ */
	.dl-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0,0,0,0.6);
		z-index: 40;
	}
	.dl-mobile-sidebar {
		position: fixed;
		left: 0;
		top: 0;
		bottom: 0;
		width: 280px;
		z-index: 50;
		background: var(--color-dl-bg-card);
		border-right: 1px solid var(--color-dl-border);
		animation: dl-slide-in-left var(--motion-base) ease-out;
	}
	@keyframes dl-slide-in-left {
		from { transform: translateX(-100%); }
		to { transform: translateX(0); }
	}

	@media (max-width: 768px) {
		.dl-right-panel {
			position: fixed;
			right: 0;
			top: 44px;
			bottom: 0;
			width: 100%;
			z-index: 30;
		}
		.dl-brand-text { display: none; }
		.dl-panel-tabs span { display: none; }
	}
</style>
