// 로컬 챗 스토어. 다중 대화 + localStorage 영속화 + AiPort.streamAsk(mode:'chat') 스트리밍.
// 옛 React ui/web features/chat/store/chat.ts (zustand persist) 를 Svelte 5 runes 로 옮긴 것.
// 터미널 모드와 같은 Ask engine 계약(AiPort)을 공유한다.
//
// Svelte 5 주의: $state 배열의 원소는 프록시다. 대화·메시지 변형은 항상 스토어의 conversations 프록시를
// 거친 참조(this.active, conv.messages[idx])로 해야 반응한다. 배열 재할당(new/delete/clearAll)만 = 로 교체.
import { isKrStockCode, type AiCapabilities, type AiPort, type AiStreamEvent, type EvidenceRef } from '@dartlab/ui-contracts';
import { resolveAgentApproval } from '$lib/runtime/agentRuntimeApi';

/**
 * 작업대 블록. LLM 이 자율 호출한 도구 한 건 (입력 args + 결과 표/마크다운/stdout).
 * ChatGPT/Claude 의 tool-use 카드에 대응. 진행중 spinner, 완료 시 접힌 카드로 결과 확인.
 */
export interface ToolBlock {
	id: string;
	name: string;
	args: Record<string, unknown>;
	status: 'running' | 'done' | 'error';
	summary: string;
	markdown: string | null;
	stdout: string | null;
	tableHead: unknown[] | null;
	tableRows: number | null;
	error: string | null;
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	text: string;
	/** 추론(사고) 스트림. reasoning 모델의 사고 흐름 (접이식 추론 패널). */
	thinking: string;
	refs: EvidenceRef[];
	/** 작업대. 자율 도구 호출 카드 (근거를 만드는 과정). */
	tools: ToolBlock[];
	approvals: Array<{
		id: string;
		sessionId: string;
		summary: string;
		status: 'pending' | 'approved' | 'denied' | 'error';
	}>;
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

	/** 설치형 agent runtime이 실제 사용 가능한가. */
	get connected(): boolean {
		return this.capabilities?.tier === 'advanced' || this.capabilities?.tier === 'onDevice';
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
		// 이전 턴들(현재 질문 제외)을 히스토리로. 후속 질문("그럼 영업이익률은?")의 맥락 유지.
		// 로컬 모델 컨텍스트 창 보호를 위해 최근 12 턴으로 제한.
		const history = conv.messages
			.filter((m) => m.text && !m.error)
			.slice(-12)
			.map((m) => ({ role: m.role, content: m.text }));
		conv.messages.push({
			id: this.#uid('u'),
			role: 'user',
			text,
			thinking: '',
			refs: [],
			tools: [],
			approvals: [],
			suggested: [],
			error: null,
			streaming: false
		});
		conv.messages.push({
			id: this.#uid('a'),
			role: 'assistant',
			text: '',
			thinking: '',
			refs: [],
			tools: [],
			approvals: [],
			suggested: [],
			error: null,
			streaming: true
		});
		conv.updatedAt = Date.now();
		const idx = conv.messages.length - 1;

		// 지원 CLI가 없으면 heuristic 폴백 대신 설치 경로를 정직하게 안내한다.
		if (this.capabilitiesLoaded && !this.connected) {
			conv.messages[idx].text =
				'사용 가능한 agent CLI가 없습니다. 우측 상단 Runtime Center에서 Codex, Claude Code, Cline 중 하나의 설치 계획을 확인하세요.';
			conv.messages[idx].streaming = false;
			conv.updatedAt = Date.now();
			this.busy = false;
			this.#persist();
			return;
		}

		const code = conv.code.trim();
		try {
			for await (const ev of this.#ai.streamAsk({
				prompt: text,
				mode: 'chat',
				runtimeId: this.capabilities?.runtimeId,
				sessionId: conv.id,
				code: isKrStockCode(code) ? code : undefined,
				history
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

	async resolveApproval(message: ChatMessage, approvalId: string, allow: boolean): Promise<void> {
		const approval = message.approvals.find((item) => item.id === approvalId);
		if (!approval || approval.status !== 'pending') return;
		try {
			await resolveAgentApproval(approval.sessionId, approval.id, allow);
			approval.status = allow ? 'approved' : 'denied';
		} catch {
			approval.status = 'error';
		}
		this.#persist();
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
			case 'THINKING_DELTA':
				m.thinking += ev.delta;
				break;
			case 'TOOL_CALL_START':
				// 작업대 카드 신설 (진행중). args 를 보존해 펼쳤을 때 입력을 보여준다.
				m.tools.push({
					id: ev.toolCallId,
					name: ev.toolName,
					args: ev.args ?? {},
					status: 'running',
					summary: '',
					markdown: null,
					stdout: null,
					tableHead: null,
					tableRows: null,
					error: null
				});
				break;
			case 'TOOL_CALL_RESULT': {
				const t = m.tools.find((x) => x.id === ev.toolCallId);
				if (t) {
					t.status = ev.status === 'error' ? 'error' : 'done';
					if (ev.summary) t.summary = ev.summary;
					if (ev.error) t.error = ev.error;
					const r = ev.result;
					if (r) {
						if (typeof r.markdown === 'string' && r.markdown.trim()) t.markdown = r.markdown;
						if (typeof r.stdout === 'string' && r.stdout.trim()) t.stdout = r.stdout;
						if (Array.isArray(r.tableHead)) t.tableHead = r.tableHead;
						if (typeof r.tableRows === 'number') t.tableRows = r.tableRows;
						else if (Array.isArray(r.tableRows)) t.tableRows = r.tableRows.length;
					}
				}
				// 근거는 id 중복 제거해 누적 (같은 ref 가 여러 도구 결과에 반복 등장).
				if (ev.refDetails?.length) {
					const seen = new Set(m.refs.map((x) => x.id));
					for (const ref of ev.refDetails) {
						if (ref?.id && !seen.has(ref.id)) {
							seen.add(ref.id);
							m.refs.push(ref);
						}
					}
				}
				break;
			}
			case 'RUN_FINISHED':
				m.suggested = ev.suggestedQuestions ?? [];
				break;
			case 'RUN_ERROR':
				m.error = ev.message;
				break;
			case 'APPROVAL_REQUESTED':
				m.approvals.push({
					id: ev.approvalId,
					sessionId: ev.sessionId,
					summary: typeof ev.request?.reason === 'string' ? ev.request.reason : '에이전트가 추가 권한을 요청했습니다.',
					status: 'pending'
				});
				break;
			// 기타 allowlist 이벤트(START/END/SNAPSHOT/DELTA/VIEW_SPEC 등)는 챗 렌더 무관이라 드롭.
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
					thinking: m.thinking ?? '',
					approvals: (m.approvals ?? []).map((approval) => ({
						...approval,
						status: approval.status === 'pending' ? ('error' as const) : approval.status
					})),
					// 재시작 후 진행중이던 도구 카드는 완료 처리 (결과가 다시 오지 않으므로).
					tools: (m.tools ?? []).map((t) => ({
						...t,
						status: t.status === 'running' ? ('done' as const) : t.status
					}))
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
