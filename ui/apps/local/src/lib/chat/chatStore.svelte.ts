// 로컬 챗 스토어. 다중 대화 + localStorage 영속화 + AiPort.streamAsk(mode:'chat') 스트리밍.
// 옛 React ui/web features/chat/store/chat.ts (zustand persist) 를 Svelte 5 runes 로 옮긴 것.
// 터미널 모드와 같은 Ask engine 계약(AiPort)을 공유한다.
//
// Svelte 5 주의: $state 배열의 원소는 프록시다. 대화·메시지 변형은 항상 스토어의 conversations 프록시를
// 거친 참조(this.active, conv.messages[idx])로 해야 반응한다. 배열 재할당(new/delete/clearAll)만 = 로 교체.
import {
	isKrStockCode,
	type AiCapabilities,
	type AiPort,
	type AiStreamEvent,
	type AnalysisConversationGuide,
	type EvidenceRef
} from '@dartlab/ui-contracts';
import { cancelAgentSession, deleteAgentSession, resolveAgentApproval } from '$lib/runtime/agentRuntimeApi';

/**
 * 답변 본문 한 문단. 도구가 끼어들면 그 뒤의 델타는 새 text part 로 열려서
 * "문단 -> 도구 -> 문단" 인터리브가 도착 순서 그대로 남는다.
 */
export interface TextPart {
	kind: 'text';
	id: string;
	text: string;
}

/**
 * 작업대 블록. LLM 이 자율 호출한 도구 한 건 (입력 args + 결과 표/마크다운/stdout).
 * 진행중이면 같은 줄에서 spinner, 완료되면 같은 자리에서 접힌 결과 줄로 바뀐다.
 */
export interface ToolPart {
	kind: 'tool';
	id: string;
	/** 게이트웨이가 START 와 RESULT 를 잇는 키. 같은 값이 재사용될 수 있어 id 와 분리한다. */
	toolCallId: string;
	name: string;
	args: Record<string, unknown>;
	status: 'running' | 'done' | 'error';
	summary: string;
	markdown: string | null;
	stdout: string | null;
	stderr: string | null;
	body: string | null;
	values: unknown;
	tableHead: unknown[] | null;
	tableRows: number | null;
	error: string | null;
	startedAt: number;
	durationMs: number | null;
}

/** 추론 델타 누적. 도착한 자리에서 흐르고 끝나면 "N초 동안 생각함" 한 줄로 접힌다. */
export interface ThinkingPart {
	kind: 'thinking';
	id: string;
	text: string;
	startedAt: number;
	/** 다음 part 가 열리거나 턴이 끝날 때 확정. null 이면 아직 흐르는 중이다. */
	endedAt: number | null;
}

/** 진행 상태 한 줄. 도구 카드보다 가벼운 배경 정보다. */
export interface ActivityPart {
	kind: 'activity';
	id: string;
	status: 'running' | 'done' | 'error';
	summary: string;
	refs: string[];
	passLabel?: string;
}

/**
 * 한 턴의 시간축. 이벤트가 도착한 순서 그대로 쌓이며 화면도 이 순서로 렌더한다.
 * 문자열 하나로 합치면 도구가 언제 불렸는지가 사라지므로 합치지 않는다.
 */
export type MessagePart = TextPart | ToolPart | ThinkingPart | ActivityPart;

export interface ChatViewSpec {
	id: string;
	title: string;
	source: string;
	spec: unknown;
}

export interface ChatArtifact {
	id: string;
	data: Record<string, unknown>;
}

export interface ChatRuntimeCoverage {
	readSkillCalls: number;
	contractIds: string[];
	requiredEvidence: string[];
	candidateCapabilityRefs: string[];
}

export interface ChatAnswerQuality {
	passed: boolean;
	contract: 'quantitative' | 'documentary';
	score: number;
	issues: string[];
	citedRefIds: string[];
	contractIds: string[];
	requiredEvidence: string[];
	readSkillCalls: number | null;
	requiredClaimCells: number;
	coveredClaimCells: number;
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	/** 시간축 본문. 텍스트·도구·사고·상태가 도착 순서대로 한 배열에 들어간다. */
	parts: MessagePart[];
	refs: EvidenceRef[];
	viewSpecs: ChatViewSpec[];
	artifacts: ChatArtifact[];
	verifiedRefIds: string[];
	candidateRefIds: string[];
	// 중개 모델의 검증 뱃지. 답변은 항상 전달되고 이 값이 신뢰 수준을 표시한다.
	// verified = 근거 계약 충족, unverified = 답은 왔으나 계약 미충족(사유는 notes),
	// failed = 런타임 실패나 빈 답변.
	verificationStatus: 'verified' | 'unverified' | 'failed' | null;
	evidenceCount: number;
	verificationNotes: string[];
	repairAttempt: number;
	approvals: Array<{
		id: string;
		sessionId: string;
		summary: string;
		status: 'pending' | 'approved' | 'denied' | 'error';
	}>;
	suggested: string[];
	error: string | null;
	streaming: boolean;
	quality: ChatAnswerQuality | null;
	runtimeCoverage: ChatRuntimeCoverage | null;
	conversationGuide: AnalysisConversationGuide | null;
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
	/** 첫 전송 시 고정되며 기존 native session에서는 바뀌지 않는 런타임. */
	runtimeId: string | null;
}

/**
 * 답변 본문만 이어붙인 평문. 복사·재시도처럼 시간축이 필요 없는 곳에서만 쓴다.
 * 사고와 도구는 본문이 아니므로 빠진다.
 */
export function messageText(message: ChatMessage): string {
	return message.parts
		.filter((part): part is TextPart => part.kind === 'text')
		.map((part) => part.text)
		.join('\n\n')
		.trim();
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
			pinnedAt: null,
			runtimeId: this.capabilities?.runtimeId ?? null
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
		conv.messages.push(this.#blankMessage('u', 'user', [{ kind: 'text', id: this.#uid('part'), text }]));
		conv.messages.push(this.#blankMessage('a', 'assistant', []));
		conv.messages[conv.messages.length - 1].streaming = true;
		conv.updatedAt = Date.now();
		const idx = conv.messages.length - 1;

		// 지원 CLI가 없으면 heuristic 폴백 대신 설치 경로를 정직하게 안내한다.
		if (this.capabilitiesLoaded && !this.connected) {
			conv.messages[idx].parts.push({
				kind: 'text',
				id: this.#uid('part'),
				text: '사용 가능한 근거 기반 agent CLI가 없습니다. 우측 상단 런타임 센터에서 지원 런타임의 설치와 연결 상태를 확인하세요.'
			});
			conv.messages[idx].streaming = false;
			conv.updatedAt = Date.now();
			this.busy = false;
			this.#persist();
			return;
		}

		const code = conv.code.trim();
		conv.runtimeId ??= this.capabilities?.runtimeId ?? null;
		try {
			for await (const ev of this.#ai.streamAsk({
				prompt: text,
				mode: 'chat',
				runtimeId: conv.runtimeId ?? undefined,
				sessionId: conv.id,
				code: isKrStockCode(code) ? code : undefined,
			})) {
				this.#apply(conv, idx, ev);
			}
		} catch (e) {
			conv.messages[idx].error = e instanceof Error ? e.message : String(e);
		} finally {
			// 스트림이 끊겨도 열려 있던 사고·도구는 닫아 준다. 안 닫으면 화면이 영원히 진행중으로 남는다.
			this.#sealOpenParts(conv.messages[idx]);
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

	async retry(messageId: string): Promise<void> {
		const conversation = this.active;
		if (!conversation || this.busy) return;
		const messageIndex = conversation.messages.findIndex((message) => message.id === messageId);
		if (messageIndex < 0) return;
		for (let index = messageIndex - 1; index >= 0; index -= 1) {
			const message = conversation.messages[index];
			const prompt = messageText(message);
			if (message.role === 'user' && prompt) {
				await this.send(prompt);
				return;
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
			case 'TEXT_MESSAGE_CONTENT': {
				// 마지막 part 가 본문이면 이어 쓰고, 도구·사고가 끼어든 뒤라면 새 문단을 연다.
				const last = m.parts.at(-1);
				if (last?.kind === 'text') last.text += ev.delta;
				else {
					this.#sealThinking(m);
					m.parts.push({ kind: 'text', id: this.#uid('part'), text: ev.delta });
				}
				break;
			}
			case 'THINKING_DELTA': {
				const last = m.parts.at(-1);
				if (last?.kind === 'thinking' && last.endedAt === null) last.text += ev.delta;
				else {
					m.parts.push({
						kind: 'thinking',
						id: this.#uid('part'),
						text: ev.delta,
						startedAt: Date.now(),
						endedAt: null
					});
				}
				break;
			}
			case 'TOOL_CALL_START':
				this.#sealThinking(m);
				m.parts.push({
					kind: 'tool',
					id: this.#uid('part'),
					toolCallId: ev.toolCallId,
					name: ev.toolName,
					args: ev.args ?? {},
					status: 'running',
					summary: '',
					markdown: null,
					stdout: null,
					stderr: null,
					body: null,
					values: null,
					tableHead: null,
					tableRows: null,
					error: null,
					startedAt: Date.now(),
					durationMs: null
				});
				break;
			case 'TOOL_CALL_RESULT': {
				const t = this.#findToolPart(m, ev.toolCallId);
				if (t) {
					t.status = ev.status === 'error' ? 'error' : 'done';
					if (ev.summary) t.summary = ev.summary;
					if (ev.error) t.error = ev.error;
					const body = ev.result;
					if (body) {
						t.markdown = body.markdown ?? null;
						t.stdout = body.stdout ?? null;
						t.stderr = body.stderr ?? null;
						t.body = body.body ?? null;
						t.values = body.values ?? null;
						t.tableHead = body.tableHead ?? null;
						t.tableRows = body.tableRows ?? null;
					}
					t.durationMs = body?.durationMs ?? Date.now() - t.startedAt;
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
				this.#appendArtifacts(m, ev.artifacts);
				break;
			}
			case 'ACTIVITY_DELTA': {
				// 같은 문구가 연달아 오면 줄만 늘고 뜻은 그대로다. 마지막 줄을 갱신한다.
				const last = m.parts.at(-1);
				if (last?.kind === 'activity' && last.summary === ev.summary) {
					last.status = ev.status;
					last.refs = ev.refs ?? [];
					break;
				}
				this.#sealThinking(m);
				m.parts.push({
					kind: 'activity',
					id: this.#uid('part'),
					status: ev.status,
					summary: ev.summary,
					refs: ev.refs ?? [],
					passLabel: ev.passLabel
				});
				break;
			}
			case 'VIEW_SPEC': {
				const id = ev.id || `${ev.runId}:${ev.messageId}:${m.viewSpecs.length + 1}`;
				if (!m.viewSpecs.some((item) => item.id === id)) {
					m.viewSpecs.push({
						id,
						title: ev.title || '시각 분석',
						source: ev.source || '',
						spec: ev.spec
					});
				}
				break;
			}
			case 'RUN_FINISHED':
				m.suggested = ev.suggestedQuestions ?? [];
				m.conversationGuide = ev.responseMeta?.analysisConversation ?? m.conversationGuide;
				m.candidateRefIds = ev.candidateRefs ?? [];
				m.verificationStatus = ev.responseMeta?.verificationStatus ?? null;
				m.evidenceCount = ev.responseMeta?.evidenceCount ?? 0;
				m.verificationNotes = ev.responseMeta?.verificationNotes ?? [];
				m.repairAttempt = ev.responseMeta?.repairAttempt ?? 0;
				if (ev.candidateRefDetails?.length) {
					const seen = new Set(m.refs.map((ref) => ref.id));
					for (const ref of ev.candidateRefDetails) {
						if (ref.id && !seen.has(ref.id)) {
							seen.add(ref.id);
							m.refs.push(ref);
						}
					}
				}
				this.#appendArtifacts(m, ev.artifacts);
				if (ev.responseMeta?.answerQuality) {
					const quality = ev.responseMeta.answerQuality;
					m.quality = {
						passed: quality.passed,
						contract: quality.contract,
						score: quality.score,
						issues: quality.issues ?? [],
						citedRefIds: quality.citedRefIds ?? [],
						contractIds: quality.contractIds ?? [],
						requiredEvidence: quality.requiredEvidence ?? [],
						readSkillCalls: quality.readSkillCalls ?? null,
						requiredClaimCells: quality.requiredClaimCells ?? 0,
						coveredClaimCells: quality.coveredClaimCells ?? 0
					};
				}
				if (ev.responseMeta?.runtimeCoverage) {
					const coverage = ev.responseMeta.runtimeCoverage;
					m.runtimeCoverage = {
						readSkillCalls: coverage.readSkillCalls,
						contractIds: coverage.contractIds ?? [],
						requiredEvidence: coverage.requiredEvidence ?? [],
						candidateCapabilityRefs: coverage.candidateCapabilityRefs ?? []
					};
				}
				break;
			case 'STATE_DELTA':
				if (
					'analysisConversation' in ev &&
					ev.analysisConversation &&
					typeof ev.analysisConversation === 'object'
				) {
					m.conversationGuide = ev.analysisConversation as AnalysisConversationGuide;
				}
				if ('runtimeId' in ev && typeof ev.runtimeId === 'string' && ev.runtimeId) {
					if (conv.runtimeId === null) conv.runtimeId = ev.runtimeId;
					else if (conv.runtimeId !== ev.runtimeId) m.error = '이 대화에 고정된 런타임과 서버 세션이 일치하지 않습니다.';
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
			// 기타 allowlist 이벤트(START/END/SNAPSHOT/DELTA)는 챗 렌더 무관이라 드롭.
		}
	}

	/** 빈 메시지 한 통. 필드가 많아 두 곳에 손으로 적으면 한쪽만 늘어난다. */
	#blankMessage(prefix: string, role: 'user' | 'assistant', parts: MessagePart[]): ChatMessage {
		return {
			id: this.#uid(prefix),
			role,
			parts,
			refs: [],
			viewSpecs: [],
			artifacts: [],
			verifiedRefIds: [],
			candidateRefIds: [],
			verificationStatus: null,
			evidenceCount: 0,
			verificationNotes: [],
			repairAttempt: 0,
			approvals: [],
			suggested: [],
			error: null,
			streaming: false,
			quality: null,
			runtimeCoverage: null,
			conversationGuide: null
		};
	}

	/**
	 * 흐르던 사고를 닫는다. 다음 part 가 열리는 순간이 사고가 멈춘 순간이다.
	 * 닫아야 화면이 "생각 중" 에서 "N초 동안 생각함" 으로 접힌다.
	 */
	#sealThinking(message: ChatMessage): void {
		const now = Date.now();
		for (const part of message.parts) {
			if (part.kind === 'thinking' && part.endedAt === null) part.endedAt = now;
		}
	}

	/**
	 * 턴이 끝날 때만 부른다. 사고를 닫고, 결과를 못 받은 도구를 중단으로 확정한다.
	 * 도구는 병렬로 열릴 수 있으므로 part 가 하나 열렸다고 해서 앞 도구를 닫지 않는다.
	 */
	#sealOpenParts(message: ChatMessage): void {
		this.#sealThinking(message);
		const now = Date.now();
		for (const part of message.parts) {
			if (part.kind !== 'tool' || part.status !== 'running') continue;
			part.status = 'error';
			part.error ||= '결과가 도착하기 전에 실행이 중단되었습니다.';
			part.durationMs ??= now - part.startedAt;
		}
	}

	/**
	 * 결과가 붙을 도구 part 찾기. 게이트웨이가 id 없는 도구에 이름을 대신 쓰므로
	 * toolCallId 가 재사용될 수 있다. 뒤에서부터 진행중인 것을 먼저 집는다.
	 */
	#findToolPart(message: ChatMessage, toolCallId: string): ToolPart | null {
		let fallback: ToolPart | null = null;
		for (let index = message.parts.length - 1; index >= 0; index -= 1) {
			const part = message.parts[index];
			if (part.kind !== 'tool' || part.toolCallId !== toolCallId) continue;
			if (part.status === 'running') return part;
			fallback ??= part;
		}
		return fallback;
	}

	#appendArtifacts(message: ChatMessage, artifacts: Record<string, unknown>[] | undefined): void {
		for (const artifact of artifacts ?? []) {
			if (!artifact || typeof artifact !== 'object') continue;
			const candidate = artifact.id ?? artifact.url ?? artifact.href ?? artifact.path ?? artifact.filename;
			const id = typeof candidate === 'string' && candidate ? candidate : this.#uid('artifact');
			if (!message.artifacts.some((item) => item.id === id)) {
				message.artifacts.push({ id, data: artifact });
			}
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
				runtimeId: typeof c.runtimeId === 'string' ? c.runtimeId : null,
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
				pinnedAt: c.pinnedAt,
				runtimeId: c.runtimeId
			}));
			localStorage.setItem(LS_KEY, JSON.stringify({ conversations, activeId: this.activeId }));
		} catch {
			// 용량 초과 등은 조용히 무시(다음 저장에서 복구).
		}
	}
}
