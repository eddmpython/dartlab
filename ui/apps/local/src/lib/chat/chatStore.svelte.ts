// 로컬 챗 스토어. 다중 대화 + localStorage 영속화 + AiPort.streamAsk(mode:'chat') 스트리밍.
// 옛 React ui/web features/chat/store/chat.ts (zustand persist) 를 Svelte 5 runes 로 옮긴 것.
// 터미널 모드와 같은 Ask engine 계약(AiPort)을 공유한다.
//
// Svelte 5 주의: $state 배열의 원소는 프록시다. 대화·메시지 변형은 항상 스토어의 conversations 프록시를
// 거친 참조(this.active, conv.messages[idx])로 해야 반응한다. 배열 재할당(new/delete/clearAll)만 = 로 교체.
import { isKrStockCode, type AiCapabilities, type AiPort, type AiStreamEvent, type EvidenceRef } from '@dartlab/ui-contracts';
import { cancelAgentSession, deleteAgentSession, resolveAgentApproval } from '$lib/runtime/agentRuntimeApi';

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
	quality: { passed: boolean; contract: 'quantitative' | 'documentary'; score: number } | null;
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
		void deleteAgentSession(id).catch(() => undefined);
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
		for (const conversation of this.conversations) {
			void deleteAgentSession(conversation.id).catch(() => undefined);
		}
		this.conversations = [];
		this.activeId = null;
		this.#persist();
	}

	async send(prompt: string): Promise<void> {
		const text = prompt.trim();
		if (!text || this.busy) return;
		this.busy = true;

		const conv = this.#ensureActive();
		if (conv.messages.length === 0) conv.title = this.#generatedTitle(conv.createdAt);
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
			streaming: false,
			quality: null
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
			streaming: true,
			quality: null
		});
		conv.updatedAt = Date.now();
		const idx = conv.messages.length - 1;

		// 지원 CLI가 없으면 heuristic 폴백 대신 설치 경로를 정직하게 안내한다.
		if (this.capabilitiesLoaded && !this.connected) {
			conv.messages[idx].text =
				'사용 가능한 근거 기반 agent CLI가 없습니다. 우측 상단 런타임 센터에서 지원 런타임의 설치와 연결 상태를 확인하세요.';
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

	setContextCode(code: string): void {
		const conversation = this.#ensureActive();
		conversation.code = isKrStockCode(code) ? code : '';
	}

	async cancel(): Promise<void> {
		const conversation = this.active;
		if (!conversation || !this.busy) return;
		try {
			await cancelAgentSession(conversation.id);
		} catch (error) {
			const message = conversation.messages.at(-1);
			if (message?.role === 'assistant') {
				message.error = error instanceof Error ? error.message : String(error);
			}
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
				// 원시 추론은 제품 UI와 브라우저 저장소에 노출하지 않는다.
				break;
			case 'TOOL_CALL_START':
				// 채팅에는 실행 상태만 보이고 원시 인자와 결과 payload는 보존하지 않는다.
				m.tools.push({
					id: ev.toolCallId,
					name: ev.toolName,
					args: {},
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
				if (ev.responseMeta?.answerQuality) {
					m.quality = {
						passed: ev.responseMeta.answerQuality.passed,
						contract: ev.responseMeta.answerQuality.contract,
						score: ev.responseMeta.answerQuality.score
					};
				}
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

	#generatedTitle(createdAt: number): string {
		return `대화 ${new Date(createdAt).toLocaleString('ko-KR', {
			month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
		})}`;
	}

	#load(): void {
		if (typeof localStorage === 'undefined') return;
		try {
			const raw = localStorage.getItem(LS_KEY);
			if (!raw) return;
			const data = JSON.parse(raw) as { conversations?: Conversation[]; activeId?: string | null };
			// 브라우저에는 내용 없는 세션 메타만 복원한다. 대화 본문은 CLI 네이티브 세션이 소유한다.
			this.conversations = (data.conversations ?? []).map((c) => ({
				id: c.id,
				title: this.#generatedTitle(c.createdAt ?? Date.now()),
				code: '',
				createdAt: c.createdAt ?? Date.now(),
				updatedAt: c.updatedAt ?? Date.now(),
				pinnedAt: c.pinnedAt ?? null,
				messages: []
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
				id: c.id,
				createdAt: c.createdAt,
				updatedAt: c.updatedAt,
				pinnedAt: c.pinnedAt
			}));
			localStorage.setItem(LS_KEY, JSON.stringify({ conversations, activeId: this.activeId }));
		} catch {
			// 용량 초과 등은 조용히 무시(다음 저장에서 복구).
		}
	}
}
