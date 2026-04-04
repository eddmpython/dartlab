/**
 * 대화 메모리 스토어 (localStorage 기반)
 *
 * 구조:
 * {
 *   conversations: [{ id, title, messages: [{role, text, meta?, company?, error?}], createdAt, updatedAt }],
 *   activeId: string | null
 * }
 */

const STORAGE_KEY = "dartlab-conversations";
const MAX_CONVERSATIONS = 50;

function generateId() {
	return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function loadFromStorage() {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return { conversations: [], activeId: null };
		return JSON.parse(raw);
	} catch {
		return { conversations: [], activeId: null };
	}
}

const EPHEMERAL_KEYS = ["systemPrompt", "userContent", "contexts", "snapshot", "toolEvents", "startedAt", "loading", "renderViews"];

function stripEphemeral(convs) {
	return convs.map(c => ({
		...c,
		messages: c.messages.map(m => {
			if (m.role !== "assistant") return m;
			const cleaned = {};
			for (const [k, v] of Object.entries(m)) {
				if (!EPHEMERAL_KEYS.includes(k)) cleaned[k] = v;
			}
			return cleaned;
		}),
	}));
}

function saveToStorage(data) {
	try {
		const slim = {
			conversations: stripEphemeral(data.conversations),
			activeId: data.activeId,
		};
		localStorage.setItem(STORAGE_KEY, JSON.stringify(slim));
	} catch {
		if (data.conversations.length > 5) {
			data.conversations = data.conversations.slice(0, data.conversations.length - 5);
			try {
				const slim = {
					conversations: stripEphemeral(data.conversations),
					activeId: data.activeId,
				};
				localStorage.setItem(STORAGE_KEY, JSON.stringify(slim));
			} catch (e) { console.warn("conversations persist:", e); }
		}
	}
}

/** 대화 목록 + 활성 대화 관리 */
export function createConversationsStore() {
	const stored = loadFromStorage();
	const initialConversations = stored.conversations || [];
	const initialActiveId = initialConversations.find(c => c.id === stored.activeId) ? stored.activeId : null;
	let conversations = $state(initialConversations);
	let activeId = $state(initialActiveId);

	let persistTimer = null;
	function persist() {
		if (persistTimer) clearTimeout(persistTimer);
		persistTimer = setTimeout(() => {
			saveToStorage({ conversations, activeId });
			persistTimer = null;
		}, 300);
	}

	function persistNow() {
		if (persistTimer) clearTimeout(persistTimer);
		persistTimer = null;
		saveToStorage({ conversations, activeId });
	}

	function getActive() {
		return conversations.find(c => c.id === activeId) || null;
	}

	function createConversation() {
		const conv = {
			id: generateId(),
			title: "새 대화",
			messages: [],
			createdAt: Date.now(),
			updatedAt: Date.now(),
		};
		conversations = [conv, ...conversations];

		// 최대 개수 초과 시 오래된 것 삭제
		if (conversations.length > MAX_CONVERSATIONS) {
			conversations = conversations.slice(0, MAX_CONVERSATIONS);
		}

		activeId = conv.id;
		persistNow();
		return conv.id;
	}

	function setActive(id) {
		if (conversations.find(c => c.id === id)) {
			activeId = id;
			persistNow();
		}
	}

	function addMessage(role, text, meta = null) {
		const conv = getActive();
		if (!conv) return;

		const msg = { role, text };
		if (meta) msg.meta = meta;

		conv.messages = [...conv.messages, msg];
		conv.updatedAt = Date.now();

		if (conv.title === "새 대화" && role === "user") {
			conv.title = text.length > 30 ? text.slice(0, 30) + "..." : text;
		}

		conversations = [...conversations];
		persistNow();
	}

	function updateLastMessage(updates) {
		const conv = getActive();
		if (!conv || conv.messages.length === 0) return;

		const last = conv.messages[conv.messages.length - 1];
		Object.assign(last, updates);
		conv.updatedAt = Date.now();
		conversations = [...conversations];
		persist();
	}

	function deleteConversation(id) {
		conversations = conversations.filter(c => c.id !== id);
		if (activeId === id) {
			activeId = conversations.length > 0 ? conversations[0].id : null;
		}
		persistNow();
	}

	function removeLastMessage() {
		const conv = getActive();
		if (!conv || conv.messages.length === 0) return;
		conv.messages = conv.messages.slice(0, -1);
		conv.updatedAt = Date.now();
		conversations = [...conversations];
		persistNow();
	}

	function updateTitle(id, title) {
		const conv = conversations.find(c => c.id === id);
		if (conv) {
			conv.title = title;
			conversations = [...conversations];
			persistNow();
		}
	}

	function clearAll() {
		conversations = [];
		activeId = null;
		persistNow();
	}

	return {
		get conversations() { return conversations; },
		get activeId() { return activeId; },
		get active() { return getActive(); },
		createConversation,
		setActive,
		addMessage,
		updateLastMessage,
		removeLastMessage,
		deleteConversation,
		updateTitle,
		clearAll,
		flush: persistNow,
	};
}
