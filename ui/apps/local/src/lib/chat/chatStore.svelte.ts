// 로컬 챗 스토어. 다중 대화 + localStorage 영속화 + AiPort.streamAsk(mode:'chat') 스트리밍.
// 옛 React ui/web features/chat/store/chat.ts (zustand persist) 를 Svelte 5 runes 로 옮긴 것.
// 터미널 모드와 같은 Ask engine 계약(AiPort)을 공유한다.
//
// Svelte 5 주의: $state 배열의 원소는 프록시다. 대화·메시지 변형은 항상 스토어의 conversations 프록시를
// 거친 참조(this.active, conv.messages[idx])로 해야 반응한다. 배열 재할당(new/delete/clearAll)만 = 로 교체.
import type { AiCapabilities, AiPort, AiStreamEvent, EvidenceRef } from '@dartlab/ui-contracts';

export interface ChatActivity {
	id: string;
	summary: string;
	status: 'running' | 'done';
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	text: string;
	refs: EvidenceRef[];
	activities: ChatActivity[];
	suggested: string[];
	error: string | null;
	streaming: boolean;
}

export interface Conversation {
	id: string;
	title: string;
	/** 선택적 종목 컨텍스트(6자리). streamAsk 에 code 로 전달. */
	code: string;
	messages: ChatMessage[];
	createdAt: number;
	updatedAt: number;
	/** 고정 timestamp. null 이면 미고정. */
	pinnedAt: number | null;
}

const LS_KEY = 'dartlab-local-chat';

export class ChatStore {
	conversations = $state<Conversation[]>([]);
	activeId = $state<string | null>(null);
	capabilities = $state<AiCapabilities | null>(null);
	capabilitiesLoaded = $state(false);
	busy = $state(false);

	#ai: AiPort;
	#seq = 0;

	constructor(ai: AiPort) {
		this.#ai = ai;
		this.#load();
	}

	get active(): Conversation | null {
		return this.conversations.find((c) => c.id === this.activeId) ?? null;
	}

	/** 고정 먼저, 그 다음 updatedAt 내림차순. */
	get sorted(): Conversation[] {
		return [...this.conversations].sort((a, b) => {
			if (a.pinnedAt && !b.pinnedAt) return -1;
			if (!a.pinnedAt && b.pinnedAt) return 1;
			if (a.pinnedAt && b.pinnedAt) return b.pinnedAt - a.pinnedAt;
			return b.updatedAt - a.updatedAt;
		});
	}

	async loadCapabilities(): Promise<void> {
		try {
			this.capabilities = await this.#ai.capabilities();
		} catch {
			this.capabilities = null;
		} finally {
			this.capabilitiesLoaded = true;
		}
	}

	newConversation(): string {
		const now = Date.now();
		const c: Conversation = {
			id: this.#uid('c'),
			title: '새 대화',
			code: '',
			messages: [],
			createdAt: now,
			updatedAt: now,
			pinnedAt: null
		};
		this.conversations = [c, ...this.conversations];
		this.activeId = c.id;
		this.#persist();
		return c.id;
	}

	switchConversation(id: string): void {
		this.activeId = id;
		this.#persist();
	}

	deleteConversation(id: string): void {
		this.conversations = this.conversations.filter((c) => c.id !== id);
		if (this.activeId === id) this.activeId = this.conversations[0]?.id ?? null;
		this.#persist();
	}

	renameConversation(id: string, title: string): void {
		const t = title.trim().slice(0, 80) || '새 대화';
		const c = this.conversations.find((x) => x.id === id);
		if (c) {
			c.title = t;
			c.updatedAt = Date.now();
			this.#persist();
		}
	}

	togglePin(id: string): void {
		const c = this.conversations.find((x) => x.id === id);
		if (c) {
			c.pinnedAt = c.pinnedAt ? null : Date.now();
			this.#persist();
		}
	}

	clearAll(): void {
		this.conversations = [];
		this.activeId = null;
		this.#persist();
	}

	async send(prompt: string): Promise<void> {
		const text = prompt.trim();
		if (!text || this.busy) return;
		this.busy = true;

		const conv = this.#ensureActive();
		if (conv.messages.length === 0) conv.title = text.slice(0, 24);
		conv.messages.push({
			id: this.#uid('u'),
			role: 'user',
			text,
			refs: [],
			activities: [],
			suggested: [],
			error: null,
			streaming: false
		});
		conv.messages.push({
			id: this.#uid('a'),
			role: 'assistant',
			text: '',
			refs: [],
			activities: [],
			suggested: [],
			error: null,
			streaming: true
		});
		conv.updatedAt = Date.now();
		const idx = conv.messages.length - 1;

		const code = conv.code.trim();
		try {
			for await (const ev of this.#ai.streamAsk({
				prompt: text,
				mode: 'chat',
				code: /^\d{6}$/.test(code) ? code : undefined
			})) {
				this.#apply(conv, idx, ev);
			}
		} catch (e) {
			conv.messages[idx].error = e instanceof Error ? e.message : String(e);
		} finally {
			conv.messages[idx].streaming = false;
			conv.updatedAt = Date.now();
			this.busy = false;
			this.#persist();
		}
	}

	#ensureActive(): Conversation {
		if (!this.active) this.newConversation();
		return this.active as Conversation;
	}

	#apply(conv: Conversation, idx: number, ev: AiStreamEvent): void {
		const m = conv.messages[idx];
		if (!m) return;
		switch (ev.type) {
			case 'TEXT_MESSAGE_CONTENT':
				m.text += ev.delta;
				break;
			case 'TOOL_CALL_START':
				m.activities.push({ id: ev.toolCallId, summary: ev.toolName, status: 'running' });
				break;
			case 'TOOL_CALL_RESULT': {
				const a = m.activities.find((x) => x.id === ev.toolCallId);
				if (a) {
					a.status = 'done';
					if (ev.summary) a.summary = ev.summary;
				}
				if (ev.refDetails?.length) m.refs.push(...ev.refDetails);
				break;
			}
			case 'ACTIVITY_DELTA':
				m.activities.push({ id: this.#uid('act'), summary: ev.summary, status: ev.status });
				break;
			case 'RUN_FINISHED':
				m.suggested = ev.suggestedQuestions ?? [];
				break;
			case 'RUN_ERROR':
				m.error = ev.message;
				break;
			// 기타 allowlist 이벤트(START/END/SNAPSHOT/VIEW_SPEC 등)는 챗 렌더 무관이라 드롭.
		}
	}

	#uid(p: string): string {
		this.#seq += 1;
		return `${p}-${Date.now().toString(36)}-${this.#seq}`;
	}

	#load(): void {
		if (typeof localStorage === 'undefined') return;
		try {
			const raw = localStorage.getItem(LS_KEY);
			if (!raw) return;
			const data = JSON.parse(raw) as { conversations?: Conversation[]; activeId?: string | null };
			// 재시작 후 stale streaming/running 은 정리한다(결과가 다시 오지 않으므로).
			this.conversations = (data.conversations ?? []).map((c) => ({
				id: c.id,
				title: c.title ?? '새 대화',
				code: c.code ?? '',
				createdAt: c.createdAt ?? Date.now(),
				updatedAt: c.updatedAt ?? Date.now(),
				pinnedAt: c.pinnedAt ?? null,
				messages: (c.messages ?? []).map((m) => ({
					...m,
					streaming: false,
					activities: (m.activities ?? []).map((a) => ({ ...a, status: 'done' as const }))
				}))
			}));
			this.activeId = data.activeId ?? this.conversations[0]?.id ?? null;
		} catch {
			// 손상된 저장분은 무시하고 빈 상태로 시작.
		}
	}

	#persist(): void {
		if (typeof localStorage === 'undefined') return;
		try {
			const conversations = this.conversations.map((c) => ({
				...c,
				messages: c.messages.map((m) => ({ ...m, streaming: false }))
			}));
			localStorage.setItem(LS_KEY, JSON.stringify({ conversations, activeId: this.activeId }));
		} catch {
			// 용량 초과 등은 조용히 무시(다음 저장에서 복구).
		}
	}
}
