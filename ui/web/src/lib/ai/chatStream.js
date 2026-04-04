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

function isMissingDartKeyToolResult(name, result) {
	if (!["list_live_filings", "read_filing"].includes(name)) return false;
	if (typeof result !== "string") return false;
	return result.includes("OpenDART API 키") || result.includes("DART_API_KEY");
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
	uiStore,
	streamConvId,
	showToast,
	appendRenderViews,
	onStreamSettled,
	bumpScroll,
	onCompanySelect,
}) {
	const isStale = () => store.activeId !== streamConvId;
	const sideEffectContext = {
		workspace,
		uiStore,
		showToast,
		onCompanySelect,
	};

	// ── chunk 배치 처리: 토큰당 → 프레임당 1회 DOM 업데이트 ──
	let chunkBuffer = "";
	let chunkRafId = null;

	function flushChunkBuffer() {
		if (!chunkBuffer) return;
		const batch = chunkBuffer;
		chunkBuffer = "";
		chunkRafId = null;
		const last = getLastMessage(store);
		store.updateLastMessage({ text: `${last?.text || ""}${batch}` });
		bumpScroll?.();
	}

	function cancelChunkRaf() {
		if (chunkRafId) {
			cancelAnimationFrame(chunkRafId);
			chunkRafId = null;
		}
	}

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
			if (isMissingDartKeyToolResult(ev.name, ev.result)) {
				showToast?.("OpenDART API 키가 필요합니다. 설정 화면을 엽니다.", "warning", 5000);
				uiStore?.openSettings?.("openDart");
			}
		},
		onCodeRound(data) {
			if (isStale()) return;
			const last = getLastMessage(store);
			const rounds = [...(last?.codeRounds ?? [])];
			// Replace existing round (prevent duplicates on reconnect)
			const idx = rounds.findIndex(r => r.round === data.round);
			if (idx >= 0) rounds[idx] = data;
			else rounds.push(data);
			store.updateLastMessage({ codeRounds: rounds });
			bumpScroll?.();
		},
		onChart(data) {
			if (isStale()) return;
			appendRenderViews(collectViewsFromChartPayload(data));
		},
		onChunk(text) {
			if (isStale()) return;
			chunkBuffer += text;
			if (chunkRafId) return;
			chunkRafId = requestAnimationFrame(flushChunkBuffer);
		},
		onDone(data) {
			if (isStale()) return;
			cancelChunkRaf();
			flushChunkBuffer();
			const last = getLastMessage(store);
			const duration = last?.startedAt
				? ((Date.now() - last.startedAt) / 1000).toFixed(1)
				: null;
			const updates = { loading: false, duration };
			if (data?.dataReady) {
				updates.meta = { ...(last?.meta || {}), dataReady: data.dataReady };
			}
			if (!last?.text?.trim()) {
				updates.text = "응답을 받지 못했습니다. AI 서버가 일시적으로 응답하지 않았을 수 있습니다.";
				updates.error = true;
				updates.retryable = true;
			}
			if (data?.pluginHints?.length) {
				updates.pluginHints = data.pluginHints;
			}
			store.updateLastMessage(updates);
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
			cancelChunkRaf();
			chunkBuffer = "";
			const retryable = ["retry", "rate_limit"].includes(action);
			store.updateLastMessage({ text: err, loading: false, error: true, errorAction: action || "", retryable });
			store.flush();
			onStreamSettled?.();
		},
	};
}
