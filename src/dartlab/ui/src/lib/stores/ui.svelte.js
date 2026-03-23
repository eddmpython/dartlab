/**
 * 중앙 UI 상태 관리 — layout, modals, toast, provider 상태를 한 곳에서 관리.
 *
 * AI가 ui_action 이벤트로 레이아웃/뷰를 제어하기 위한 단일 진입점 역할.
 * App.svelte의 55+ 산발 상태변수를 이 store로 통합한다.
 */
import {
	fetchAiProfile,
	fetchModels,
	fetchStatus,
	subscribeAiProfileEvents,
	deleteDartKey,
	updateAiProfile,
	updateAiSecret,
	saveDartKey,
	validateProvider as validateProviderApi,
	validateDartKey as validateDartKeyApi,
	codexLogout,
	oauthAuthorize,
	oauthLogout,
	oauthStatus,
	pullOllamaModel,
	startChannelConnection,
	stopChannelConnection,
} from "$lib/api/ai.js";
import {
	applyProfileSnapshot,
	mergeProviderDetail,
	mergeProviderStatus,
	normalizeProvider,
} from "$lib/ai/providerProfile.js";

const CHAT_ROLE = "analysis";

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

export function createUiStore() {
	// ── Layout ──
	let sidebarOpen = $state(false);
	let viewerFullscreen = $state(false);
	let isMobile = $state(false);

	// ── Toast Queue ──
	let toastQueue = $state([]);
	let toastIdCounter = 0;

	function showToast(msg, type = "error", duration = 4000) {
		const id = ++toastIdCounter;
		const timer = setTimeout(() => dismissToast(id), duration);
		const entry = { id, message: msg, type, duration, timer };
		// max 5 toasts
		if (toastQueue.length >= 5) {
			const oldest = toastQueue[0];
			clearTimeout(oldest.timer);
			toastQueue = [...toastQueue.slice(1), entry];
		} else {
			toastQueue = [...toastQueue, entry];
		}
	}

	function dismissToast(id) {
		const idx = toastQueue.findIndex(t => t.id === id);
		if (idx >= 0) {
			clearTimeout(toastQueue[idx].timer);
			toastQueue = [...toastQueue.slice(0, idx), ...toastQueue.slice(idx + 1)];
		}
	}

	// ── Modals ──
	let settingsOpen = $state(false);
	let settingsSection = $state("providers");
	let deleteConfirmId = $state(null);
	let deleteConfirmMode = $state("single");

	// ── Provider / Model ──
	let providers = $state({});
	let activeProvider = $state(null);
	let activeModel = $state(null);
	let availableModels = $state([]);
	let expandedProvider = $state(null);
	let providerModels = $state({});
	let modelsLoading = $state({});
	let statusLoading = $state(true);
	let appVersion = $state("");
	let openDart = $state({});
	let channels = $state({});

	// API key
	let apiKeyInput = $state("");
	let apiKeyVerifying = $state(false);
	let apiKeyResult = $state(null);

	// OpenDART key
	let dartKeyInput = $state("");
	let dartKeyValidating = $state(false);
	let dartKeySaving = $state(false);
	let dartKeyResult = $state(null);

	// Ollama detail
	let ollamaDetail = $state({});
	let codexDetail = $state({});
	let oauthCodexDetail = $state({});
	let oauthLoginPending = $state(false);
	let channelBusy = $state({});
	let channelInputs = $state({
		telegram: { token: "" },
		slack: { botToken: "", appToken: "" },
		discord: { token: "" },
	});

	// Ollama pull
	let pullModelName = $state("");
	let isPulling = $state(false);
	let pullProgress = $state("");
	let pullPercent = $state(0);
	let pullHandle = $state(null);

	// SSE subscription
	let profileEvents = null;

	// ── Provider logic ──
	function providerSupportsRole(provider, role) {
		const normalized = normalizeProvider(provider);
		const supportedRoles = providers[normalized]?.supportedRoles;
		return !Array.isArray(supportedRoles) || supportedRoles.length === 0 || supportedRoles.includes(role);
	}

	async function validateProvider(provider, model = null, apiKey = null) {
		const result = await validateProviderApi(provider, model, apiKey);
		if (result?.provider) {
			const name = normalizeProvider(result.provider);
			providers = {
				...providers,
				[name]: {
					...(providers[name] || {}),
					checked: true,
					available: !!result.available,
					model: result.model || providers[name]?.model || model || null,
				},
			};
		}
		return result;
	}

	async function refreshProviderStatus(provider = null, probe = true) {
		const data = await fetchStatus(provider, probe);
		if (data.profile) providers = applyProfileSnapshot(providers, data.profile);
		providers = mergeProviderStatus(providers, data.providers || {});
		if (data.ollama) ollamaDetail = mergeProviderDetail(ollamaDetail, data.ollama, { preserveChecked: true });
		if (data.codex) codexDetail = mergeProviderDetail(codexDetail, data.codex);
		if (data.oauthCodex) oauthCodexDetail = mergeProviderDetail(oauthCodexDetail, data.oauthCodex, { preserveChecked: true });
		if (data.openDart) openDart = { ...openDart, ...data.openDart };
		if (data.channels) channels = data.channels;
		if (data.version) appVersion = data.version;
		return data;
	}

	async function handleProfileChanged(profile) {
		providers = applyProfileSnapshot(providers, profile);
		const nextProvider = normalizeProvider(profile?.defaultProvider || activeProvider || "codex");
		activeProvider = nextProvider;
		expandedProvider = nextProvider;
		apiKeyInput = "";
		apiKeyResult = null;
		await loadModelsFor(nextProvider);
		availableModels = providerModels[nextProvider] || [];
		const nextModel = profile?.providers?.[nextProvider]?.model || providers[nextProvider]?.model || availableModels[0] || null;
		activeModel = nextModel;
		if (nextModel && !profile?.providers?.[nextProvider]?.model) {
			try { await updateAiProfile({ provider: nextProvider, model: nextModel }); } catch {}
		}
		await refreshProviderStatus(nextProvider, true);
	}

	async function loadStatus() {
		statusLoading = true;
		try {
			const profile = await fetchAiProfile();
			providers = applyProfileSnapshot(providers, profile);
			const preferredProvider = normalizeProvider(profile?.defaultProvider || "codex");
			await refreshProviderStatus(preferredProvider, true);
			activeProvider = preferredProvider;
			expandedProvider = preferredProvider;
			apiKeyInput = "";
			await loadModelsFor(preferredProvider);
			const models = providerModels[preferredProvider] || [];
			availableModels = models;
			const savedModel = profile?.providers?.[preferredProvider]?.model || providers[preferredProvider]?.model || null;
			if (savedModel && (models.length === 0 || models.includes(savedModel))) {
				activeModel = savedModel;
			} else if (models.length > 0) {
				activeModel = models[0];
				await updateAiProfile({ provider: preferredProvider, model: activeModel });
			} else {
				activeModel = null;
			}
			if (!providers[preferredProvider]?.checked || providers[preferredProvider]?.available !== true) {
				try { await validateProvider(preferredProvider, activeModel || null, null); } catch (e) { console.warn("validateProvider:", e); }
			}
			if (!profileEvents) {
				profileEvents = subscribeAiProfileEvents({
					onProfileChanged(profilePayload) {
						handleProfileChanged(profilePayload).catch((e) => console.warn("profile_changed:", e));
					},
					onError(err) { console.warn("profile events:", err); },
				});
			}
		} catch (e) { console.error("loadStatus:", e); }
		statusLoading = false;
	}

	function cleanupProfileEvents() {
		if (profileEvents) {
			profileEvents.close?.();
			profileEvents = null;
		}
	}

	async function loadModelsFor(provider) {
		provider = normalizeProvider(provider);
		modelsLoading = { ...modelsLoading, [provider]: true };
		try {
			const data = await fetchModels(provider);
			providerModels = { ...providerModels, [provider]: data.models || [] };
		} catch (e) {
			console.warn("loadModelsFor:", e);
			providerModels = { ...providerModels, [provider]: [] };
		}
		modelsLoading = { ...modelsLoading, [provider]: false };
	}

	async function selectProvider(name) {
		name = normalizeProvider(name);
		activeProvider = name;
		activeModel = null;
		expandedProvider = name;
		apiKeyInput = "";
		apiKeyResult = null;
		await updateAiProfile({ provider: name });
		await refreshProviderStatus(name, true);
		await loadModelsFor(name);
		const models = providerModels[name] || [];
		availableModels = models;
		const savedModel = providers[name]?.model || null;
		if (savedModel && (models.length === 0 || models.includes(savedModel))) {
			activeModel = savedModel;
		} else if (models.length > 0) {
			activeModel = models[0];
			await updateAiProfile({ provider: name, model: activeModel });
		}
		if (!providerSupportsRole(name, CHAT_ROLE)) {
			showToast("Codex CLI는 코드 작업용입니다. GUI 대화/분석은 `GPT (ChatGPT 구독 계정)`을 권장합니다.", "error", 4500);
		}
		try { await validateProvider(name, activeModel, null); } catch {}
	}

	async function selectModel(model) {
		activeModel = model;
		await updateAiProfile({ provider: normalizeProvider(activeProvider), model });
		const configured = providers[activeProvider]?.secretConfigured;
		if (configured || activeProvider === "codex" || activeProvider === "oauth-codex" || activeProvider === "ollama") {
			try { await validateProvider(normalizeProvider(activeProvider), model, null); } catch {}
		}
	}

	function toggleExpandProvider(name) {
		name = normalizeProvider(name);
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
			const result = await validateProvider(normalizeProvider(activeProvider), activeModel, key);
			if (result.available) {
				await updateAiSecret(activeProvider, key, false);
				apiKeyResult = "success";
				if (!activeModel && result.model) {
					activeModel = result.model;
					await updateAiProfile({ provider: activeProvider, model: activeModel });
				}
				await loadModelsFor(activeProvider);
				availableModels = providerModels[activeProvider] || [];
				apiKeyInput = "";
				showToast("API 키 인증 성공", "success");
			} else {
				apiKeyResult = "error";
			}
		} catch {
			apiKeyResult = "error";
		}
		apiKeyVerifying = false;
	}

	async function handleCodexLogout() {
		try {
			await codexLogout();
			if (activeProvider === "codex") {
				providers = { ...providers, codex: { ...providers.codex, available: false } };
			}
			showToast("Codex 계정 로그아웃 완료", "success");
			await loadStatus();
		} catch {
			showToast("로그아웃 실패");
		}
	}

	async function handleOauthCodexLogin() {
		if (oauthLoginPending) return;
		oauthLoginPending = true;
		try {
			const { authUrl } = await oauthAuthorize();
			window.open(authUrl, "dartlab-oauth-codex", "popup=yes,width=540,height=760");
			const started = Date.now();
			while (Date.now() - started < 120000) {
				await new Promise((resolve) => setTimeout(resolve, 1000));
				const status = await oauthStatus();
				if (!status.done) continue;
				if (status.error) throw new Error(status.error);
				await refreshProviderStatus("oauth-codex", true);
				const profile = await fetchAiProfile();
				await handleProfileChanged(profile);
				showToast("ChatGPT OAuth 인증 완료", "success");
				oauthLoginPending = false;
				return;
			}
			throw new Error("oauth_timeout");
		} catch (e) {
			const message = e?.message === "oauth_timeout" ? "OAuth 인증 시간이 초과되었습니다" : `OAuth 인증 실패: ${e?.message || "unknown"}`;
			showToast(message);
		}
		oauthLoginPending = false;
	}

	async function handleOauthCodexLogout() {
		try {
			await oauthLogout();
			oauthCodexDetail = { ...oauthCodexDetail, authenticated: false, checked: true };
			const profile = await fetchAiProfile();
			await handleProfileChanged(profile);
			showToast("ChatGPT OAuth 로그아웃 완료", "success");
		} catch {
			showToast("OAuth 로그아웃 실패");
		}
	}

	// ── Ollama pull ──
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

	// ── Chat provider resolution ──
	async function resolveChatProvider() {
		const normalized = normalizeProvider(activeProvider);
		if (!normalized) return null;
		if (providerSupportsRole(normalized, CHAT_ROLE)) {
			return { provider: normalized, model: activeModel };
		}
		if (!providers["oauth-codex"]?.available) {
			showToast("Codex CLI는 GUI 일반 대화용이 아니라 코딩용입니다. 설정에서 `GPT (ChatGPT 구독 계정)` 또는 다른 분석용 provider를 선택하세요.");
			return null;
		}
		await loadModelsFor("oauth-codex");
		const models = providerModels["oauth-codex"] || [];
		const nextModel = activeModel && (models.length === 0 || models.includes(activeModel))
			? activeModel
			: providers["oauth-codex"]?.model || models[0] || null;
		activeProvider = "oauth-codex";
		expandedProvider = "oauth-codex";
		availableModels = models;
		activeModel = nextModel;
		try {
			if (nextModel) await updateAiProfile({ provider: "oauth-codex", model: nextModel });
			else await updateAiProfile({ provider: "oauth-codex" });
		} catch {}
		showToast("Codex CLI는 GUI 일반 대화용이 아니라 코딩용입니다. GPT OAuth provider로 전환해서 보냅니다.", "success", 4500);
		return { provider: "oauth-codex", model: nextModel };
	}

	// ── Theme ──
	let theme = $state(
		(typeof localStorage !== "undefined" && localStorage.getItem("dl-theme")) || "dark"
	);

	function setTheme(value) {
		theme = value;
		if (typeof document !== "undefined") {
			document.documentElement.setAttribute("data-theme", value);
		}
		if (typeof localStorage !== "undefined") {
			localStorage.setItem("dl-theme", value);
		}
	}

	function cycleTheme() {
		const order = ["dark", "light", "auto"];
		const next = order[(order.indexOf(theme) + 1) % order.length];
		setTheme(next);
	}

	// Apply saved theme on creation
	if (typeof document !== "undefined") {
		document.documentElement.setAttribute("data-theme", theme);
	}

	// ── Mobile detection ──
	function checkMobile() {
		isMobile = window.innerWidth <= 768;
		if (isMobile) sidebarOpen = false;
	}

	// ── Settings open ──
	function openSettings(section = "providers") {
		apiKeyInput = "";
		apiKeyResult = null;
		dartKeyInput = "";
		dartKeyResult = null;
		settingsSection = section || "providers";
		if (activeProvider) {
			expandedProvider = activeProvider;
		} else {
			const names = Object.keys(providers);
			expandedProvider = names.length > 0 ? names[0] : null;
		}
		settingsOpen = true;
		if (expandedProvider) loadModelsFor(expandedProvider);
	}

	function setChannelInput(platform, key, value) {
		channelInputs = {
			...channelInputs,
			[platform]: {
				...(channelInputs[platform] || {}),
				[key]: value,
			},
		};
	}

	async function startChannel(platform) {
		const payload = channelInputs[platform] || {};
		channelBusy = { ...channelBusy, [platform]: true };
		try {
			const result = await startChannelConnection(platform, payload);
			await refreshProviderStatus(null, false);
			if (result?.error) {
				showToast(result.error);
			} else {
				showToast(`${channels[platform]?.label || platform} 채널 연결 완료`, "success");
			}
		} catch (e) {
			showToast(e?.message || `${platform} 채널 연결 실패`);
		}
		channelBusy = { ...channelBusy, [platform]: false };
	}

	async function stopChannel(platform) {
		channelBusy = { ...channelBusy, [platform]: true };
		try {
			await stopChannelConnection(platform);
			await refreshProviderStatus(null, false);
			showToast(`${channels[platform]?.label || platform} 채널 종료`, "success");
		} catch (e) {
			showToast(e?.message || `${platform} 채널 종료 실패`);
		}
		channelBusy = { ...channelBusy, [platform]: false };
	}

	async function validateDartKey() {
		const key = dartKeyInput.trim();
		if (!key) return;
		dartKeyValidating = true;
		dartKeyResult = null;
		try {
			const result = await validateDartKeyApi(key);
			if (result.openDart) openDart = { ...openDart, ...result.openDart };
			dartKeyResult = "valid";
			showToast("OpenDART 키 검증 성공", "success");
		} catch (e) {
			dartKeyResult = "error";
			showToast(e?.message || "OpenDART 키 검증 실패");
		}
		dartKeyValidating = false;
	}

	async function submitDartKey() {
		const key = dartKeyInput.trim();
		if (!key) return;
		dartKeySaving = true;
		dartKeyResult = null;
		try {
			const result = await saveDartKey(key);
			if (result.openDart) openDart = { ...openDart, ...result.openDart };
			dartKeyInput = "";
			dartKeyResult = "saved";
			showToast("OpenDART 키 저장 완료", "success");
		} catch (e) {
			dartKeyResult = "error";
			showToast(e?.message || "OpenDART 키 저장 실패");
		}
		dartKeySaving = false;
	}

	async function removeDartKey() {
		dartKeySaving = true;
		dartKeyResult = null;
		try {
			const result = await deleteDartKey();
			if (result.openDart) openDart = { ...openDart, ...result.openDart };
			dartKeyInput = "";
			dartKeyResult = "deleted";
			showToast("프로젝트 .env의 OpenDART 키를 제거했습니다", "success");
		} catch (e) {
			dartKeyResult = "error";
			showToast(e?.message || "OpenDART 키 삭제 실패");
		}
		dartKeySaving = false;
	}

	// ── AI action entry point ──
	function applyAiAction(action) {
		if (!action || typeof action !== "object") return;
		const name = action.action || "";
		if (name === "layout") {
			const target = action.target;
			const value = action.value;
			if (target === "sidebar") {
				sidebarOpen = value === "toggle" ? !sidebarOpen : value === "open";
			} else if (target === "fullscreen") {
				viewerFullscreen = typeof value === "boolean" ? value : !viewerFullscreen;
			}
		} else if (name === "toast") {
			showToast(action.message || action.text || "", action.level || "info");
		} else if (name === "update" && action.target === "settings") {
			if (action.message) showToast(action.message, "info", 4500);
			openSettings(action.section || "providers");
			if (action.open === false) settingsOpen = false;
		}
	}

	return {
		// layout
		get sidebarOpen() { return sidebarOpen; },
		set sidebarOpen(v) { sidebarOpen = v; },
		get viewerFullscreen() { return viewerFullscreen; },
		set viewerFullscreen(v) { viewerFullscreen = v; },
		get isMobile() { return isMobile; },
		toggleSidebar() { sidebarOpen = !sidebarOpen; },
		checkMobile,

		// toast
		get toastQueue() { return toastQueue; },
		get toastMessage() { return toastQueue.length > 0 ? toastQueue[toastQueue.length - 1].message : ""; },
		get toastType() { return toastQueue.length > 0 ? toastQueue[toastQueue.length - 1].type : "error"; },
		get toastVisible() { return toastQueue.length > 0; },
		get toastDuration() { return toastQueue.length > 0 ? toastQueue[toastQueue.length - 1].duration : 4000; },
		showToast,
		dismissToast,

		// modals
		get settingsOpen() { return settingsOpen; },
		set settingsOpen(v) { settingsOpen = v; },
		get settingsSection() { return settingsSection; },
		get deleteConfirmId() { return deleteConfirmId; },
		set deleteConfirmId(v) { deleteConfirmId = v; },
		get deleteConfirmMode() { return deleteConfirmMode; },
		set deleteConfirmMode(v) { deleteConfirmMode = v; },
		openSettings,

		// provider
		get providers() { return providers; },
		get activeProvider() { return activeProvider; },
		get activeModel() { return activeModel; },
		get availableModels() { return availableModels; },
		get expandedProvider() { return expandedProvider; },
		get providerModels() { return providerModels; },
		get modelsLoading() { return modelsLoading; },
		get statusLoading() { return statusLoading; },
		get appVersion() { return appVersion; },
		get openDart() { return openDart; },
		get channels() { return channels; },
		get channelBusy() { return channelBusy; },
		get channelInputs() { return channelInputs; },

		// api key
		get apiKeyInput() { return apiKeyInput; },
		set apiKeyInput(v) { apiKeyInput = v; },
		get apiKeyVerifying() { return apiKeyVerifying; },
		get apiKeyResult() { return apiKeyResult; },

		// OpenDART key
		get dartKeyInput() { return dartKeyInput; },
		set dartKeyInput(v) { dartKeyInput = v; },
		get dartKeyValidating() { return dartKeyValidating; },
		get dartKeySaving() { return dartKeySaving; },
		get dartKeyResult() { return dartKeyResult; },

		// detail
		get ollamaDetail() { return ollamaDetail; },
		get codexDetail() { return codexDetail; },
		get oauthCodexDetail() { return oauthCodexDetail; },
		get oauthLoginPending() { return oauthLoginPending; },

		// pull
		get pullModelName() { return pullModelName; },
		set pullModelName(v) { pullModelName = v; },
		get isPulling() { return isPulling; },
		get pullProgress() { return pullProgress; },
		get pullPercent() { return pullPercent; },

		// provider methods
		selectProvider,
		selectModel,
		toggleExpandProvider,
		submitApiKey,
		validateDartKey,
		submitDartKey,
		removeDartKey,
		setChannelInput,
		startChannel,
		stopChannel,
		handleCodexLogout,
		handleOauthCodexLogin,
		handleOauthCodexLogout,
		startPullModel,
		cancelPull,
		loadStatus,
		loadModelsFor,
		providerSupportsRole,
		resolveChatProvider,
		cleanupProfileEvents,

		// constants
		CHAT_ROLE,
		OLLAMA_MODELS,

		// theme
		get theme() { return theme; },
		setTheme,
		cycleTheme,

		// AI action
		applyAiAction,
	};
}
