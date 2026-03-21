import {
	applyUiActionSideEffect,
	collectViewsFromChartPayload,
	collectViewsFromUiAction,
} from "./uiActionBridge.js";

function getLastMessage(store) {
	const conv = store.active;
	if (!conv || conv.messages.length === 0) return null;
	return conv.messages[conv.messages.length - 1];
}

function appendMessageList(store, key, item) {
	const last = getLastMessage(store);
	const prev = last?.[key] || [];
	store.updateLastMessage({ [key]: [...prev, item] });
}

export function getLastAssistantStockCode(conv = null) {
	if (!conv) return null;
	for (let i = conv.messages.length - 1; i >= 0; i -= 1) {
		const message = conv.messages[i];
		if (message.role === "assistant" && message.meta?.stockCode) {
			return message.meta.stockCode;
		}
	}
	return null;
}

export function buildConversationHistory(conv = null) {
	const history = [];
	let lastAnalyzedCode = null;
	if (!conv) return { history, lastAnalyzedCode };

	const messages = conv.messages.slice(0, -2);
	for (const message of messages) {
		if (!["user", "assistant"].includes(message.role)) continue;
		if (!message.text || !message.text.trim() || message.error || message.loading) continue;

		const entry = { role: message.role, text: message.text };
		if (message.role === "assistant" && message.meta?.stockCode) {
			entry.meta = {
				company: message.meta.company || message.company,
				stockCode: message.meta.stockCode,
				modules: message.meta.includedModules || null,
				market: message.meta.market || null,
				topic: message.meta.topic || null,
				topicLabel: message.meta.topicLabel || null,
				dialogueMode: message.meta.dialogueMode || null,
				questionTypes: message.meta.questionTypes || null,
				userGoal: message.meta.userGoal || null,
			};
			lastAnalyzedCode = message.meta.stockCode;
		}
		history.push(entry);
	}

	return { history, lastAnalyzedCode };
}

export function createAskStreamCallbacks({
	store,
	workspace,
	viewerStore,
	uiStore,
	streamConvId,
	handleViewerNavigate,
	showToast,
	appendRenderViews,
	onStreamSettled,
	bumpScroll,
	onCompanySelect,
}) {
	const isStale = () => store.activeId !== streamConvId;
	const sideEffectContext = {
		workspace,
		viewerStore,
		uiStore,
		onNavigate: handleViewerNavigate,
		showToast,
		onCompanySelect,
	};

	return {
		onMeta(meta) {
			if (isStale()) return;
			const last = getLastMessage(store);
			const merged = { ...(last?.meta || {}), ...meta };
			const updates = { meta: merged };
			if (meta.company) {
				updates.company = meta.company;
				if (store.activeId && store.active?.title === "새 대화") {
					store.updateTitle(store.activeId, meta.company);
				}
			}
			if (meta.stockCode) updates.stockCode = meta.stockCode;
			if (meta.company || meta.stockCode) {
				workspace.syncCompanyFromMessage(meta, workspace.selectedCompany);
			}
			store.updateLastMessage(updates);
		},
		onSnapshot(snapshot) {
			if (isStale()) return;
			store.updateLastMessage({ snapshot });
		},
		onContext(ctx) {
			if (isStale()) return;
			appendMessageList(store, "contexts", {
				module: ctx.module,
				label: ctx.label,
				text: ctx.text,
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
			appendMessageList(store, "toolEvents", {
				type: "call",
				name: ev.name,
				arguments: ev.arguments,
			});
		},
		onToolResult(ev) {
			if (isStale()) return;
			appendMessageList(store, "toolEvents", {
				type: "result",
				name: ev.name,
				result: ev.result,
			});
		},
		onChart(data) {
			if (isStale()) return;
			appendRenderViews(collectViewsFromChartPayload(data));
		},
		onChunk(text) {
			if (isStale()) return;
			const last = getLastMessage(store);
			store.updateLastMessage({ text: `${last?.text || ""}${text}` });
			bumpScroll?.();
		},
		onDone() {
			if (isStale()) return;
			const last = getLastMessage(store);
			const duration = last?.startedAt
				? ((Date.now() - last.startedAt) / 1000).toFixed(1)
				: null;
			store.updateLastMessage({ loading: false, duration });
			store.flush();
			onStreamSettled?.();
			bumpScroll?.();
		},
		onUiAction(data) {
			if (isStale()) return;
			applyUiActionSideEffect(data, sideEffectContext);
			appendRenderViews(collectViewsFromUiAction(data));
		},
		onError(err, action) {
			if (isStale()) return;
			store.updateLastMessage({ text: `오류: ${err}`, loading: false, error: true });
			store.flush();
			if (action === "login") {
				showToast?.(`${err} — 설정에서 Codex 로그인을 확인하세요`);
			} else if (action === "install") {
				showToast?.(`${err} — 설정에서 Codex 설치 안내를 확인하세요`);
			} else {
				showToast?.(err);
			}
			onStreamSettled?.();
		},
	};
}
