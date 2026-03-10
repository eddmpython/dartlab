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
	import { fetchStatus, configure, askStream, fetchModels, pullOllamaModel, oauthAuthorize, oauthStatus, oauthLogout } from "$lib/api.js";
	import { cn } from "$lib/utils.js";
	import { createConversationsStore } from "$lib/stores/conversations.svelte.js";
	import Sidebar from "$lib/components/Sidebar.svelte";
	import EmptyState from "$lib/components/EmptyState.svelte";
	import ChatArea from "$lib/components/ChatArea.svelte";
	import {
		Menu, PanelLeftClose, Coffee, Github, FileText,
		Download, X, Loader2, Settings, Check, ExternalLink,
		Key, AlertCircle, CheckCircle2, Terminal, LogIn, LogOut
	} from "lucide-svelte";

	// ── State ──
	let inputText = $state("");
	let isLoading = $state(false);
	let currentStream = $state(null);
	let providers = $state({});
	let ollamaDetail = $state({});
	let activeProvider = $state(null);
	let activeModel = $state(null);
	let availableModels = $state([]);
	let sidebarOpen = $state(true);
	let scrollTrigger = $state(0);

	// Initial loading
	let statusLoading = $state(true);
	let appVersion = $state("");

	// Settings modal
	let showSettings = $state(false);
	let expandedProvider = $state(null); // 현재 펼쳐진 provider

	// Per-provider model cache
	let providerModels = $state({}); // { "ollama": ["gemma2", ...], "openai": [...] }
	let modelsLoading = $state({}); // { "ollama": true }

	// API key input
	let apiKeyInput = $state("");
	let apiKeyVerifying = $state(false);
	let apiKeyResult = $state(null); // null | "success" | "error"

	// Ollama model download
	let pullModelName = $state("");
	let isPulling = $state(false);
	let pullProgress = $state("");
	let pullPercent = $state(0);
	let pullHandle = $state(null);

	// OAuth login
	let oauthLoggingIn = $state(false);
	let chatgptDetail = $state({});

	// Mobile
	let isMobile = $state(false);

	function checkMobile() {
		isMobile = window.innerWidth <= 768;
		if (isMobile) sidebarOpen = false;
	}

	$effect(() => {
		checkMobile();
		window.addEventListener("resize", checkMobile);
		return () => window.removeEventListener("resize", checkMobile);
	});

	// Delete confirmation
	let deleteConfirmId = $state(null);

	// Toast
	let toastMessage = $state("");
	let toastType = $state("error");
	let toastVisible = $state(false);

	function showToast(message, type = "error", duration = 4000) {
		toastMessage = message;
		toastType = type;
		toastVisible = true;
		setTimeout(() => { toastVisible = false; }, duration);
	}

	// ── Conversations store ──
	const store = createConversationsStore();

	// ── Provider/Model logic ──
	$effect(() => { loadStatus(); });

	let codexDetail = $state({});
	let claudeCodeDetail = $state({});

	async function loadStatus() {
		statusLoading = true;
		try {
			const data = await fetchStatus();
			providers = data.providers || {};
			ollamaDetail = data.ollama || {};
			codexDetail = data.codex || {};
			claudeCodeDetail = data.claudeCode || {};
			chatgptDetail = data.chatgpt || {};
			if (data.version) appVersion = data.version;

			const savedProvider = localStorage.getItem("dartlab-provider");
			const savedModel = localStorage.getItem("dartlab-model");

			if (savedProvider && providers[savedProvider]?.available) {
				activeProvider = savedProvider;
				expandedProvider = savedProvider;
				await configure(savedProvider, savedModel);
				await loadModelsFor(savedProvider);
				const models = providerModels[savedProvider] || [];
				if (savedModel && models.includes(savedModel)) {
					activeModel = savedModel;
				} else if (models.length > 0) {
					activeModel = models[0];
					localStorage.setItem("dartlab-model", activeModel);
				}
				availableModels = models;
				statusLoading = false;
				return;
			}

			if (savedProvider && providers[savedProvider]) {
				activeProvider = savedProvider;
				expandedProvider = savedProvider;
				await loadModelsFor(savedProvider);
				const models = providerModels[savedProvider] || [];
				availableModels = models;
				if (savedModel && models.includes(savedModel)) {
					activeModel = savedModel;
				} else if (models.length > 0) {
					activeModel = models[0];
				}
				statusLoading = false;
				return;
			}

			for (const name of ["chatgpt", "codex", "ollama"]) {
				if (providers[name]?.available) {
					activeProvider = name;
					expandedProvider = name;
					await configure(name);
					await loadModelsFor(name);
					const models = providerModels[name] || [];
					availableModels = models;
					activeModel = providers[name]?.model || (models.length > 0 ? models[0] : null);
					if (activeModel) localStorage.setItem("dartlab-model", activeModel);
					break;
				}
			}
		} catch {}
		statusLoading = false;
	}

	async function loadModelsFor(provider) {
		modelsLoading = { ...modelsLoading, [provider]: true };
		try {
			const data = await fetchModels(provider);
			providerModels = { ...providerModels, [provider]: data.models || [] };
		} catch {
			providerModels = { ...providerModels, [provider]: [] };
		}
		modelsLoading = { ...modelsLoading, [provider]: false };
	}

	async function selectProvider(name) {
		activeProvider = name;
		activeModel = null;
		expandedProvider = name;
		localStorage.setItem("dartlab-provider", name);
		localStorage.removeItem("dartlab-model");
		apiKeyInput = "";
		apiKeyResult = null;
		try {
			await configure(name);
		} catch {}
		// 항상 모델 목록 로드 (API 키 없어도 fallback 제공)
		await loadModelsFor(name);
		const models = providerModels[name] || [];
		availableModels = models;
		if (models.length > 0) {
			activeModel = providers[name]?.model || models[0];
			localStorage.setItem("dartlab-model", activeModel);
			try { await configure(name, activeModel); } catch {}
		}
	}

	async function selectModel(model) {
		activeModel = model;
		localStorage.setItem("dartlab-model", model);
		try { await configure(activeProvider, model); } catch {}
	}

	function toggleExpandProvider(name) {
		if (expandedProvider === name) {
			expandedProvider = null;
		} else {
			expandedProvider = name;
			loadModelsFor(name);
		}
	}

	async function submitApiKey() {
		const key = apiKeyInput.trim();
		if (!key || !activeProvider) return;

		apiKeyVerifying = true;
		apiKeyResult = null;
		try {
			const result = await configure(activeProvider, activeModel, key);
			if (result.available) {
				apiKeyResult = "success";
				providers[activeProvider] = { ...providers[activeProvider], available: true, model: result.model };
				if (!activeModel && result.model) activeModel = result.model;
				await loadModelsFor(activeProvider);
				availableModels = providerModels[activeProvider] || [];
				showToast("API 키 인증 성공", "success");
			} else {
				apiKeyResult = "error";
			}
		} catch {
			apiKeyResult = "error";
		}
		apiKeyVerifying = false;
	}

	async function startOAuthLogin() {
		if (oauthLoggingIn) return;
		oauthLoggingIn = true;
		try {
			const { authUrl } = await oauthAuthorize();
			window.open(authUrl, "dartlab-oauth", "width=600,height=700");

			const pollInterval = setInterval(async () => {
				try {
					const result = await oauthStatus();
					if (result.done) {
						clearInterval(pollInterval);
						oauthLoggingIn = false;
						if (result.error) {
							showToast(`인증 실패: ${result.error}`);
						} else {
							showToast("ChatGPT 인증 성공", "success");
							await loadStatus();
							if (providers["chatgpt"]?.available) {
								await selectProvider("chatgpt");
							}
						}
					}
				} catch {
					clearInterval(pollInterval);
					oauthLoggingIn = false;
				}
			}, 2000);

			setTimeout(() => {
				clearInterval(pollInterval);
				if (oauthLoggingIn) {
					oauthLoggingIn = false;
					showToast("인증 시간이 초과되었습니다. 다시 시도해주세요.");
				}
			}, 120000);
		} catch (err) {
			oauthLoggingIn = false;
			showToast(`OAuth 시작 실패: ${err.message}`);
		}
	}

	async function handleOAuthLogout() {
		try {
			await oauthLogout();
			chatgptDetail = { authenticated: false };
			if (activeProvider === "chatgpt") {
				providers = { ...providers, chatgpt: { ...providers.chatgpt, available: false } };
			}
			showToast("ChatGPT 로그아웃 완료", "success");
			await loadStatus();
		} catch {
			showToast("로그아웃 실패");
		}
	}

	function startPullModel() {
		const name = pullModelName.trim();
		if (!name || isPulling) return;

		isPulling = true;
		pullProgress = "준비 중...";
		pullPercent = 0;

		pullHandle = pullOllamaModel(name, {
			onProgress(data) {
				if (data.total && data.completed !== undefined) {
					pullPercent = Math.round((data.completed / data.total) * 100);
					pullProgress = `다운로드 중... ${pullPercent}%`;
				} else if (data.status) {
					pullProgress = data.status;
				}
			},
			async onDone() {
				isPulling = false;
				pullHandle = null;
				pullModelName = "";
				pullProgress = "";
				pullPercent = 0;
				showToast(`${name} 다운로드 완료`, "success");
				await loadModelsFor("ollama");
				availableModels = providerModels["ollama"] || [];
				if (availableModels.includes(name)) {
					await selectModel(name);
				}
			},
			onError(err) {
				isPulling = false;
				pullHandle = null;
				pullProgress = "";
				pullPercent = 0;
				showToast(`다운로드 실패: ${err}`);
			},
		});
	}

	function cancelPull() {
		if (pullHandle) { pullHandle.abort(); pullHandle = null; }
		isPulling = false;
		pullModelName = "";
		pullProgress = "";
		pullPercent = 0;
	}

	// ── UI Actions ──
	function toggleSidebar() { sidebarOpen = !sidebarOpen; }

	function openSettings() {
		apiKeyInput = "";
		apiKeyResult = null;
		if (activeProvider) {
			expandedProvider = activeProvider;
		} else {
			// 아무 provider도 선택 안 됐으면 첫 번째를 펼침
			const names = Object.keys(providers);
			expandedProvider = names.length > 0 ? names[0] : null;
		}
		showSettings = true;
		// 펼쳐진 provider의 모델 목록 로드
		if (expandedProvider) loadModelsFor(expandedProvider);
	}

	function handleNewChat() {
		store.createConversation();
		inputText = "";
		isLoading = false;
		if (currentStream) { currentStream.abort(); currentStream = null; }
	}

	function handleSelectConversation(id) {
		store.setActive(id);
		inputText = "";
		isLoading = false;
		if (currentStream) { currentStream.abort(); currentStream = null; }
	}

	function handleDeleteConversation(id) { deleteConfirmId = id; }

	function confirmDelete() {
		if (deleteConfirmId) {
			store.deleteConversation(deleteConfirmId);
			deleteConfirmId = null;
		}
	}

	function getLastStockCode() {
		const conv = store.active;
		if (!conv) return null;
		for (let i = conv.messages.length - 1; i >= 0; i--) {
			const m = conv.messages[i];
			if (m.role === "assistant" && m.meta?.stockCode) return m.meta.stockCode;
		}
		return null;
	}

	async function sendMessage() {
		const question = inputText.trim();
		if (!question || isLoading) return;

		if (!activeProvider || !providers[activeProvider]?.available) {
			showToast("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요.");
			openSettings();
			return;
		}

		if (!store.activeId) store.createConversation();
		const streamConvId = store.activeId;

		store.addMessage("user", question);
		inputText = "";
		isLoading = true;

		store.addMessage("assistant", "");
		store.updateLastMessage({ loading: true, startedAt: Date.now() });
		scrollTrigger++;

		const conv = store.active;
		const history = [];
		let lastAnalyzedCode = null;
		if (conv) {
			const msgs = conv.messages.slice(0, -2);
			for (const m of msgs) {
				if ((m.role === "user" || m.role === "assistant") && m.text && m.text.trim() && !m.error && !m.loading) {
					const entry = { role: m.role, text: m.text };
					if (m.role === "assistant" && m.meta?.stockCode) {
						entry.meta = {
							company: m.meta.company || m.company,
							stockCode: m.meta.stockCode,
							modules: m.meta.includedModules || null,
						};
						lastAnalyzedCode = m.meta.stockCode;
					}
					history.push(entry);
				}
			}
		}

		const companyHint = lastAnalyzedCode || getLastStockCode();

		function isStale() { return store.activeId !== streamConvId; }

		const stream = askStream(
			companyHint, question, { provider: activeProvider, model: activeModel },
			{
				onMeta(meta) {
					if (isStale()) return;
					const conv = store.active;
					const last = conv?.messages[conv.messages.length - 1];
					const merged = { ...(last?.meta || {}), ...meta };
					const updates = { meta: merged };
					if (meta.company) {
						updates.company = meta.company;
						if (store.activeId && store.active?.title === "새 대화") {
							store.updateTitle(store.activeId, meta.company);
						}
					}
					if (meta.stockCode) updates.stockCode = meta.stockCode;
					store.updateLastMessage(updates);
				},
				onSnapshot(snapshot) {
					if (isStale()) return;
					store.updateLastMessage({ snapshot });
				},
				onContext(ctx) {
					if (isStale()) return;
					const conv = store.active;
					if (!conv) return;
					const last = conv.messages[conv.messages.length - 1];
					const prev = last?.contexts || [];
					store.updateLastMessage({
						contexts: [...prev, { module: ctx.module, label: ctx.label, text: ctx.text }],
					});
				},
				onSystemPrompt(data) {
					if (isStale()) return;
					store.updateLastMessage({
						systemPrompt: data.text,
						userContent: data.userContent || null,
					});
				},
				onToolCall(ev) {
					if (isStale()) return;
					const conv = store.active;
					if (!conv) return;
					const last = conv.messages[conv.messages.length - 1];
					const prev = last?.toolEvents || [];
					store.updateLastMessage({
						toolEvents: [...prev, { type: "call", name: ev.name, arguments: ev.arguments }],
					});
				},
				onToolResult(ev) {
					if (isStale()) return;
					const conv = store.active;
					if (!conv) return;
					const last = conv.messages[conv.messages.length - 1];
					const prev = last?.toolEvents || [];
					store.updateLastMessage({
						toolEvents: [...prev, { type: "result", name: ev.name, result: ev.result }],
					});
				},
				onChunk(text) {
					if (isStale()) return;
					const conv = store.active;
					if (!conv) return;
					const last = conv.messages[conv.messages.length - 1];
					store.updateLastMessage({ text: (last?.text || "") + text });
					scrollTrigger++;
				},
				onDone() {
					if (isStale()) return;
					const conv = store.active;
					const last = conv?.messages[conv.messages.length - 1];
					const duration = last?.startedAt
						? ((Date.now() - last.startedAt) / 1000).toFixed(1)
						: null;
					store.updateLastMessage({ loading: false, duration });
					store.flush();
					isLoading = false;
					currentStream = null;
					scrollTrigger++;
				},
				onError(err, action, detail) {
					if (isStale()) return;
					store.updateLastMessage({ text: `오류: ${err}`, loading: false, error: true });
					store.flush();
					if (action === "relogin" || action === "login") {
						showToast(`${err} — 설정에서 재로그인하세요`);
						openSettings();
					} else if (action === "check_headers" || action === "check_endpoint" || action === "check_client_id") {
						showToast(`${err} — ChatGPT API 변경 감지. 업데이트를 확인하세요`);
					} else if (action === "rate_limit") {
						showToast("요청이 너무 많습니다. 잠시 후 다시 시도해주세요");
					} else {
						showToast(err);
					}
					isLoading = false;
					currentStream = null;
				},
			},
			history
		);
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
			if (conv.messages[i].role === "user") {
				lastUserMsg = conv.messages[i].text;
				break;
			}
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
			if (msg.role === "user") {
				md += `## You\n\n${msg.text}\n\n`;
			} else if (msg.role === "assistant" && msg.text) {
				md += `## DartLab\n\n${msg.text}\n\n`;
			}
		}
		const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${conv.title || "dartlab-chat"}.md`;
		a.click();
		URL.revokeObjectURL(url);
		showToast("대화가 마크다운으로 내보내졌습니다", "success");
	}

	// Keyboard shortcuts
	function handleGlobalKeydown(e) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
			e.preventDefault();
			handleNewChat();
		}
		if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'S') {
			e.preventDefault();
			toggleSidebar();
		}
		if (e.key === 'Escape' && deleteConfirmId) {
			deleteConfirmId = null;
		} else if (e.key === 'Escape' && showSettings) {
			showSettings = false;
		}
	}

	let activeMessages = $derived(store.active?.messages || []);
	let hasConversation = $derived(store.active && store.active.messages.length > 0);
	let noProviderAvailable = $derived(!statusLoading && (!activeProvider || !providers[activeProvider]?.available));

	const OLLAMA_MODELS = [
		{ name: "gemma3",       size: "3B",  gb: "2.3",  desc: "Google, 빠르고 가벼움",         tag: "추천" },
		{ name: "gemma3:12b",   size: "12B", gb: "8.1",  desc: "Google, 균형잡힌 성능" },
		{ name: "llama3.1",     size: "8B",  gb: "4.7",  desc: "Meta, 범용 최강",              tag: "추천" },
		{ name: "qwen2.5",      size: "7B",  gb: "4.7",  desc: "Alibaba, 한국어 우수" },
		{ name: "qwen2.5:14b",  size: "14B", gb: "9.0",  desc: "Alibaba, 한국어 최고 수준" },
		{ name: "deepseek-r1",  size: "7B",  gb: "4.7",  desc: "추론 특화, 분석에 적합" },
		{ name: "phi4",         size: "14B", gb: "9.1",  desc: "Microsoft, 수학/코드 강점" },
		{ name: "mistral",      size: "7B",  gb: "4.1",  desc: "Mistral AI, 가볍고 빠름" },
		{ name: "exaone3.5",    size: "8B",  gb: "4.9",  desc: "LG AI, 한국어 특화",           tag: "한국어" },
	];
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="flex h-screen bg-dl-bg-dark overflow-hidden">
	<!-- Sidebar -->
	{#if isMobile && sidebarOpen}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="sidebar-overlay" onclick={() => { sidebarOpen = false; }} onkeydown={() => {}}></div>
	{/if}
	<div class={isMobile ? (sidebarOpen ? "sidebar-mobile" : "hidden") : ""}>
		<Sidebar
			conversations={store.conversations}
			activeId={store.activeId}
			open={isMobile ? true : sidebarOpen}
			version={appVersion}
			onNewChat={() => { handleNewChat(); if (isMobile) sidebarOpen = false; }}
			onSelect={(id) => { handleSelectConversation(id); if (isMobile) sidebarOpen = false; }}
			onDelete={handleDeleteConversation}
		/>
	</div>

	<!-- Main -->
	<div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg">
		<!-- Header bar (floating, transparent) -->
		<div class="absolute top-0 left-0 right-0 z-10 pointer-events-none">
			<div class="flex items-center justify-between px-3 h-11 pointer-events-auto"
				style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"
			>
				<!-- Left: sidebar toggle -->
				<button
					class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={toggleSidebar}
				>
					{#if sidebarOpen}
						<PanelLeftClose size={18} />
					{:else}
						<Menu size={18} />
					{/if}
				</button>

				<!-- Right: links + settings -->
				<div class="flex items-center gap-1">
					<a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer"
						class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee">
						<Coffee size={15} />
					</a>
					<a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer"
						class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation">
						<FileText size={15} />
					</a>
					<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer"
						class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub">
						<Github size={15} />
					</a>

					<div class="w-px h-4 bg-dl-border mx-1"></div>

					<!-- Provider/Model button → opens settings modal -->
					<button
						class={cn(
							"flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",
							statusLoading
								? "text-dl-text-dim"
								: noProviderAvailable
									? "text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15"
									: "text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"
						)}
						onclick={() => openSettings()}
					>
						{#if statusLoading}
							<Loader2 size={12} class="animate-spin" />
							<span>확인 중...</span>
						{:else if noProviderAvailable}
							<AlertCircle size={12} />
							<span>설정 필요</span>
						{:else}
							<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span>
							<span>{activeProvider}</span>
							{#if activeModel}
								<span class="text-dl-text-dim">/</span>
								<span class="max-w-[80px] truncate">{activeModel}</span>
							{/if}
							{#if isPulling}
								<Loader2 size={10} class="animate-spin text-dl-primary-light" />
							{/if}
						{/if}
						<Settings size={12} />
					</button>
				</div>
			</div>

			<!-- Loading / No provider warning banner -->
			{#if statusLoading && !showSettings}
				<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto">
					<Loader2 size={16} class="text-dl-text-dim animate-spin flex-shrink-0" />
					<div class="flex-1">
						<div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div>
					</div>
				</div>
			{:else if noProviderAvailable && !showSettings}
				<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto">
					<AlertCircle size={16} class="text-dl-primary-light flex-shrink-0" />
					<div class="flex-1">
						<div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div>
						<div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div>
					</div>
					<button
						class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0"
						onclick={() => openSettings()}
					>
						설정하기
					</button>
				</div>
			{/if}
		</div>

		<!-- Content (full height, scrolls under header) -->
		{#if hasConversation}
			<ChatArea
				messages={activeMessages}
				{isLoading}
				{scrollTrigger}
				bind:inputText
				onSend={sendMessage}
				onStop={stopStream}
				onRegenerate={handleRegenerate}
				onExport={handleExport}
			/>
		{:else}
			<EmptyState
				bind:inputText
				onSend={sendMessage}
			/>
		{/if}
	</div>
</div>

<!-- ═══════════════════════════════════════ -->
<!-- Settings Modal                         -->
<!-- ═══════════════════════════════════════ -->
{#if showSettings}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) showSettings = false; }}
		onkeydown={() => {}}
	>
		<div class="w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden">
			<!-- Modal Header -->
			<div class="flex items-center justify-between px-6 pt-5 pb-3">
				<div class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div>
				<button
					class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={() => showSettings = false}
				>
					<X size={18} />
				</button>
			</div>

			<div class="px-6 pb-5 max-h-[70vh] overflow-y-auto">
				<div class="space-y-2.5">
					{#each Object.entries(providers) as [name, info]}
						{@const isActive = name === activeProvider}
						{@const isExpanded = expandedProvider === name}
						{@const needsKey = info.auth === "api_key"}
						{@const needsCli = info.auth === "cli"}
						{@const models = providerModels[name] || []}
						{@const isModelsLoading = modelsLoading[name]}
						<div class={cn(
							"rounded-xl border transition-all",
							isActive ? "border-dl-primary/40 bg-dl-primary/[0.03]" : "border-dl-border"
						)}>
							<!-- Provider header (clickable to expand) -->
							<button
								class="flex items-center gap-3 w-full px-4 py-3 text-left"
								onclick={() => {
									if (info.available) {
										if (name === activeProvider) {
											// 이미 활성 → 토글만
											toggleExpandProvider(name);
										} else {
											selectProvider(name);
										}
									} else if (needsKey) {
										if (name === activeProvider) {
											toggleExpandProvider(name);
										} else {
											selectProvider(name);
										}
									} else {
										toggleExpandProvider(name);
									}
								}}
							>
								<span class={cn(
									"w-2.5 h-2.5 rounded-full flex-shrink-0",
									info.available ? "bg-dl-success" : needsKey ? "bg-amber-400" : "bg-dl-text-dim"
								)}></span>
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2">
										<span class="text-[13px] font-medium text-dl-text">{info.label || name}</span>
										{#if isActive}
											<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>
										{/if}
									</div>
									<div class="text-[11px] text-dl-text-dim mt-0.5">{info.desc || ""}</div>
								</div>
								<div class="flex items-center gap-2 flex-shrink-0">
									{#if info.available}
										<CheckCircle2 size={16} class="text-dl-success" />
									{:else if needsKey}
										<Key size={14} class="text-amber-400" />
										<span class="text-[10px] text-amber-400">인증 필요</span>
									{:else if needsCli && !info.available}
										<Terminal size={14} class="text-dl-text-dim" />
										<span class="text-[10px] text-dl-text-dim">미설치</span>
									{/if}
								</div>
							</button>

							<!-- ═══ Expanded content ═══ -->
							{#if isExpanded || isActive}

								<!-- API Key 입력 (API 기반 provider, not available) -->
								{#if needsKey && !info.available}
									<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
										<div class="text-[11px] text-dl-text-muted mb-2">
											{info.envKey ? `환경변수 ${info.envKey}로도 설정 가능합니다` : "API 키를 입력하세요"}
										</div>
										<div class="flex items-center gap-2">
											<input
												type="password"
												bind:value={apiKeyInput}
												placeholder={name === "openai" ? "sk-..." : name === "claude" ? "sk-ant-..." : "API Key"}
												class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
												onkeydown={(e) => { if (e.key === 'Enter') submitApiKey(); }}
											/>
											<button
												class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
												onclick={submitApiKey}
												disabled={!apiKeyInput.trim() || apiKeyVerifying}
											>
												{#if apiKeyVerifying}
													<Loader2 size={12} class="animate-spin" />
												{:else}
													<Key size={12} />
												{/if}
												인증
											</button>
										</div>
										{#if apiKeyResult === "error"}
											<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light">
												<AlertCircle size={12} />
												API 키가 유효하지 않습니다. 다시 확인해주세요.
											</div>
										{/if}
									</div>
								{/if}

								<!-- API Key 인증됨 표시 -->
								{#if needsKey && info.available}
									<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
										<div class="flex items-center gap-2">
											<CheckCircle2 size={13} class="text-dl-success" />
											<span class="text-[11px] text-dl-success">인증됨</span>
											<span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span>
										</div>
										<div class="flex items-center gap-2 mt-2">
											<input
												type="password"
												bind:value={apiKeyInput}
												placeholder="새 API 키 (변경 시에만)"
												class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
												onkeydown={(e) => { if (e.key === 'Enter') submitApiKey(); }}
											/>
											{#if apiKeyInput.trim()}
												<button
													class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
													onclick={submitApiKey}
													disabled={apiKeyVerifying}
												>
													{#if apiKeyVerifying}<Loader2 size={10} class="animate-spin" />{:else}변경{/if}
												</button>
											{/if}
										</div>
									</div>
								{/if}

								<!-- Ollama 설치 안내 -->
								{#if name === "ollama" && !ollamaDetail.installed}
									<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
										<div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div>
										<a
											href="https://ollama.com/download"
											target="_blank"
											rel="noopener noreferrer"
											class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"
										>
											<Download size={14} />
											Ollama 다운로드 (ollama.com)
											<ExternalLink size={10} class="ml-auto" />
										</a>
										<div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div>
									</div>
								{:else if name === "ollama" && ollamaDetail.installed && !ollamaDetail.running}
									<div class="px-4 pb-3 border-t border-dl-border/50 pt-3">
										<div class="flex items-center gap-2 text-[12px] text-amber-400">
											<AlertCircle size={14} />
											Ollama가 설치되었지만 실행되지 않고 있습니다
										</div>
										<div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div>
									</div>
								{/if}

								<!-- CLI provider 설치 안내 -->
								{#if needsCli && !info.available}
									<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
										{#if name === "codex"}
											<div class="text-[12px] text-dl-text mb-2.5">
												{codexDetail.installed ? "Codex CLI가 설치되었지만 인증이 필요합니다" : "Codex CLI 설치가 필요합니다"}
											</div>
											<div class="space-y-2">
												{#if !codexDetail.installed}
													<div class="flex items-start gap-2.5">
														<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span>
														<div class="flex-1">
															<div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div>
															<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
																npm install -g @openai/codex
															</div>
														</div>
													</div>
												{/if}
												<div class="flex items-start gap-2.5">
													<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">{codexDetail.installed ? "1." : "2."}</span>
													<div class="flex-1">
														<div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div>
														<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
															codex
														</div>
													</div>
												</div>
											</div>
											<div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
												<AlertCircle size={12} class="text-amber-400 flex-shrink-0" />
												<span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span>
											</div>
										{:else if name === "claude-code"}
											<div class="text-[12px] text-dl-text mb-2.5">
												{claudeCodeDetail.installed && !claudeCodeDetail.authenticated ? "Claude Code가 설치되었지만 인증이 필요합니다" : "Claude Code CLI 설치가 필요합니다"}
											</div>
											<div class="space-y-2">
												{#if !claudeCodeDetail.installed}
													<div class="flex items-start gap-2.5">
														<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span>
														<div class="flex-1">
															<div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div>
															<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
																npm install -g @anthropic-ai/claude-code
															</div>
														</div>
													</div>
												{/if}
												<div class="flex items-start gap-2.5">
													<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">{claudeCodeDetail.installed ? "1." : "2."}</span>
													<div class="flex-1">
														<div class="text-[10px] text-dl-text-dim mb-1">인증</div>
														<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
															claude auth login
														</div>
													</div>
												</div>
											</div>
											<div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
												<AlertCircle size={12} class="text-amber-400 flex-shrink-0" />
												<span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span>
											</div>
										{/if}
										<div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div>
									</div>
								{/if}

								<!-- OAuth 로그인 (chatgpt provider) -->
								{#if info.auth === "oauth" && !info.available}
									<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
										<div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div>
										<button
											class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
											onclick={startOAuthLogin}
											disabled={oauthLoggingIn}
										>
											{#if oauthLoggingIn}
												<Loader2 size={14} class="animate-spin" />
												브라우저에서 로그인 중...
											{:else}
												<LogIn size={14} />
												OpenAI 계정으로 로그인
											{/if}
										</button>
										<div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
											<AlertCircle size={12} class="text-amber-400 flex-shrink-0" />
											<span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span>
										</div>
									</div>
								{/if}

								<!-- OAuth 인증됨 + 로그아웃 (chatgpt provider) -->
								{#if info.auth === "oauth" && info.available}
									<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
										<div class="flex items-center justify-between">
											<div class="flex items-center gap-2">
												<CheckCircle2 size={13} class="text-dl-success" />
												<span class="text-[11px] text-dl-success">ChatGPT 인증됨</span>
											</div>
											<button
												class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"
												onclick={handleOAuthLogout}
											>
												<LogOut size={11} />
												로그아웃
											</button>
										</div>
									</div>
								{/if}

								<!-- ═══ Inline Model Selection ═══ -->
								{#if info.available || needsKey || needsCli || info.auth === "oauth"}
									<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
										<div class="flex items-center justify-between mb-2.5">
											<span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span>
											{#if isModelsLoading}
												<Loader2 size={12} class="animate-spin text-dl-text-dim" />
											{/if}
										</div>

										{#if isModelsLoading && models.length === 0}
											<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim">
												<Loader2 size={14} class="animate-spin" />
												모델 목록 불러오는 중...
											</div>
										{:else if models.length > 0}
											<div class="flex flex-wrap gap-1.5">
												{#each models as model}
													<button
														class={cn(
															"px-3 py-1.5 rounded-lg text-[11px] border transition-all",
															model === activeModel && isActive
																? "border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium"
																: "border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"
														)}
														onclick={() => {
															if (name !== activeProvider) selectProvider(name);
															selectModel(model);
														}}
													>
														{model}
														{#if model === activeModel && isActive}
															<Check size={10} class="inline ml-1" />
														{/if}
													</button>
												{/each}
											</div>
										{:else}
											<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>
										{/if}

										<!-- Ollama 모델 다운로드 (inline) -->
										{#if name === "ollama"}
											<div class="mt-3 pt-3 border-t border-dl-border/30">
												<div class="flex items-center justify-between mb-2">
													<span class="text-[11px] text-dl-text-muted">모델 다운로드</span>
													<a
														href="https://ollama.com/library"
														target="_blank"
														rel="noopener noreferrer"
														class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors"
													>
														전체 목록 <ExternalLink size={9} />
													</a>
												</div>

												{#if isPulling}
													<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker">
														<div class="flex items-center justify-between mb-1.5">
															<span class="text-[11px] text-dl-text flex items-center gap-1.5">
																<Loader2 size={12} class="animate-spin text-dl-primary-light" />
																다운로드 중
															</span>
															<button
																class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors"
																onclick={cancelPull}
															>
																취소
															</button>
														</div>
														<div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden">
															<div
																class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"
																style="width: {pullPercent}%"
															></div>
														</div>
														<div class="text-[10px] text-dl-text-dim mt-1">{pullProgress}</div>
													</div>
												{:else}
													<div class="flex items-center gap-1.5">
														<input
															type="text"
															bind:value={pullModelName}
															placeholder="모델명 (예: gemma3)"
															class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
															onkeydown={(e) => { if (e.key === 'Enter') startPullModel(); }}
														/>
														<button
															class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
															onclick={startPullModel}
															disabled={!pullModelName.trim()}
														>
															<Download size={12} />
															받기
														</button>
													</div>

													<div class="mt-2.5 space-y-1">
													{#each OLLAMA_MODELS as m}
														{@const installed = models.some(i => i === m.name || i === m.name.split(":")[0])}
														{#if !installed}
															<button
																class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"
																onclick={() => { pullModelName = m.name; startPullModel(); }}
															>
																<div class="flex-1 min-w-0">
																	<div class="flex items-center gap-1.5">
																		<span class="text-[11px] font-medium text-dl-text">{m.name}</span>
																		<span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim">{m.size}</span>
																		{#if m.tag}
																			<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light">{m.tag}</span>
																		{/if}
																	</div>
																	<div class="text-[10px] text-dl-text-dim mt-0.5">{m.desc}</div>
																</div>
																<div class="flex items-center gap-1.5 flex-shrink-0">
																	<span class="text-[9px] text-dl-text-dim">{m.gb} GB</span>
																	<Download size={12} class="text-dl-text-dim group-hover:text-dl-primary-light transition-colors" />
																</div>
															</button>
														{/if}
													{/each}
												</div>
												{/if}
											</div>
										{/if}
									</div>
								{/if}
							{/if}
						</div>
					{/each}
				</div>
			</div>

			<!-- Modal Footer -->
			<div class="flex items-center justify-between px-6 py-3 border-t border-dl-border">
				<div class="text-[10px] text-dl-text-dim">
					{#if activeProvider && activeModel}
						현재: {providers[activeProvider]?.label || activeProvider} / {activeModel}
					{:else if activeProvider}
						현재: {providers[activeProvider]?.label || activeProvider}
					{/if}
				</div>
				<button
					class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors"
					onclick={() => showSettings = false}
				>
					닫기
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Delete confirmation -->
{#if deleteConfirmId}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) deleteConfirmId = null; }}
		onkeydown={() => {}}
	>
		<div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5">
			<div class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div>
			<div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div>
			<div class="flex items-center justify-end gap-2">
				<button
					class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={() => deleteConfirmId = null}
				>
					취소
				</button>
				<button
					class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors"
					onclick={confirmDelete}
				>
					삭제
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Toast -->
{#if toastVisible}
	<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn">
		<div class={cn(
			"px-4 py-3 rounded-xl border text-[13px] shadow-2xl max-w-sm",
			toastType === "error" ? "bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light" :
			toastType === "success" ? "bg-dl-success/10 border-dl-success/30 text-dl-success" :
			"bg-dl-bg-card border-dl-border text-dl-text"
		)}>
			{toastMessage}
		</div>
	</div>
{/if}
