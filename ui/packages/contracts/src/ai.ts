// AI 계약. 3-티어 (02 §4) + AG-UI allowlist 16종 (emitter SSOT = server/agentGateway.py
// `_ALLOWED_EVENTS`, 수신 SSOT = ui/web streamAsk.ts). allowlist 가 계약이고 emit 은 부분집합.
import type { EvidenceRef, EvidenceSelection } from './evidence';

export type AiTier = 'advanced' | 'onDevice' | 'deterministic' | 'none';
// none = test fake 초기화 전 전용 — public 은 항상 deterministic 이상, local 무provider 도 deterministic.

export interface AiCapabilities {
	tier: AiTier;
	streaming: boolean;
	toolCalling: boolean;
	localWorkspace: boolean;
	deterministicAnswers: boolean; // 결정론 Q&A — public 에서도 항상 true
	providerLabel?: string;
	modelLabel?: string;
	upgradeHint?: string; // advanced 미만 tier 에서 로컬 업그레이드 안내 문구
	runtimeId?: string;
}

export type AiModeId = 'chat' | 'terminal';

export interface AiMode {
	id: AiModeId;
	label: string;
	description: string;
	available: boolean;
}

// AG-UI allowlist (16종. TOOL_CALL_ARGS·MESSAGES_SNAPSHOT·ACTIVITY_SNAPSHOT 은 reserved, 현재 미발행)

export type AgUiEventType =
	| 'TEXT_MESSAGE_START'
	| 'TEXT_MESSAGE_CONTENT'
	| 'TEXT_MESSAGE_END'
	| 'THINKING_DELTA'
	| 'TOOL_CALL_START'
	| 'TOOL_CALL_ARGS' // reserved
	| 'TOOL_CALL_RESULT'
	| 'TOOL_CALL_END'
	| 'STATE_SNAPSHOT'
	| 'STATE_DELTA'
	| 'MESSAGES_SNAPSHOT' // reserved
	| 'ACTIVITY_SNAPSHOT' // reserved
	| 'ACTIVITY_DELTA'
	| 'VIEW_SPEC'
	| 'APPROVAL_REQUESTED'
	| 'RUN_FINISHED'
	| 'RUN_ERROR';

export interface ToolResultBody {
	markdown?: string;
	stdout?: string;
	stderr?: string;
	values?: unknown;
	tableHead?: string[];
	tableRows?: unknown[][];
	body?: string;
	path?: string;
	durationMs?: number;
}

export interface AiStreamTextDelta {
	type: 'TEXT_MESSAGE_CONTENT';
	messageId: string;
	delta: string;
}

/** 추론(사고) 델타. reasoning 모델의 사고 흐름을 답변 본문과 분리 스트림 (접이식 추론 패널용). */
export interface AiStreamThinkingDelta {
	type: 'THINKING_DELTA';
	messageId: string;
	delta: string;
}

export interface AiStreamToolStart {
	type: 'TOOL_CALL_START';
	runId: string;
	messageId: string;
	toolCallId: string;
	toolName: string;
	args: Record<string, unknown>;
	status: 'running';
	passLabel?: string;
}

export interface AiStreamToolResult {
	type: 'TOOL_CALL_RESULT';
	runId: string;
	messageId: string;
	toolCallId: string;
	toolName: string;
	status: 'done' | 'error';
	summary: string;
	refs: string[];
	refDetails: EvidenceRef[];
	artifacts: Record<string, unknown>[];
	result: ToolResultBody | null;
	error: string | null;
	passLabel?: string;
}

export interface AiStreamActivity {
	type: 'ACTIVITY_DELTA';
	status: 'done' | 'running' | 'error';
	summary: string;
	refs: string[];
	passLabel?: string;
}

export interface AiStreamViewSpec {
	type: 'VIEW_SPEC';
	runId: string;
	messageId: string;
	id?: string;
	spec: unknown;
	title?: string;
	source?: string;
}

export interface AiStreamRunFinished {
	type: 'RUN_FINISHED';
	runId: string;
	status: 'ok' | 'failed';
	refs: string[];
	artifacts?: Record<string, unknown>[];
	suggestedQuestions: string[];
	responseMeta?: {
		responseStatus?: string;
		answerQuality?: {
			passed: boolean;
			contract: 'quantitative' | 'documentary';
			score: number;
			issues: string[];
			citedRefIds: string[];
			contractIds: string[];
			requiredEvidence: string[];
			readSkillCalls: number | null;
		};
		runtimeCoverage?: {
			readSkillCalls: number;
			contractIds: string[];
			requiredEvidence: string[];
			candidateCapabilityRefs: string[];
		};
	};
}

export interface AiStreamRunError {
	type: 'RUN_ERROR';
	runId: string;
	message: string;
	code?: string;
}

export interface AiStreamApprovalRequested {
	type: 'APPROVAL_REQUESTED';
	runId: string;
	sessionId: string;
	turnId: string;
	approvalId: string;
	request: Record<string, unknown>;
}

/** 기타 allowlist 이벤트(START/END/SNAPSHOT/DELTA 등)는 렌더 무관. surface 는 드롭. */
export interface AiStreamOther {
	type: Exclude<
		AgUiEventType,
		| 'TEXT_MESSAGE_CONTENT'
		| 'THINKING_DELTA'
		| 'TOOL_CALL_START'
		| 'TOOL_CALL_RESULT'
		| 'ACTIVITY_DELTA'
		| 'VIEW_SPEC'
		| 'APPROVAL_REQUESTED'
		| 'RUN_FINISHED'
		| 'RUN_ERROR'
	>;
	[key: string]: unknown;
}

export type AiStreamEvent =
	| AiStreamTextDelta
	| AiStreamThinkingDelta
	| AiStreamToolStart
	| AiStreamToolResult
	| AiStreamActivity
	| AiStreamViewSpec
	| AiStreamRunFinished
	| AiStreamRunError
	| AiStreamApprovalRequested
	| AiStreamOther;

/** 대화 히스토리 한 턴 (다중턴 컨텍스트 전달용). */
export interface AiHistoryTurn {
	role: 'user' | 'assistant';
	content: string;
}

export interface AiAskInput {
	prompt: string;
	mode: AiModeId;
	code?: string;
	evidence?: EvidenceSelection[];
	/** 이전 대화 턴들 (현재 prompt 제외). 게이트웨이가 LLM history 로 전달해 후속 질문 맥락 유지. */
	history?: AiHistoryTurn[];
	/** 설치형 agent runtime과 네이티브 transcript 세션 선택. */
	runtimeId?: string;
	sessionId?: string;
}

export interface AiAskResult {
	text: string;
	refs: EvidenceRef[];
}

export interface AiToolRunInput {
	toolName: string;
	args: Record<string, unknown>;
}

export interface AiToolRunResult {
	status: 'done' | 'error';
	summary: string;
	refs: EvidenceRef[];
	error: string | null;
}

export interface EvidenceExplainInput {
	selection: EvidenceSelection;
}

export interface EvidenceExplainResult {
	text: string;
	refs: EvidenceRef[];
}

export interface AiPort {
	capabilities(): Promise<AiCapabilities>;
	ask(input: AiAskInput): Promise<AiAskResult>;
	streamAsk(input: AiAskInput): AsyncIterable<AiStreamEvent>;
	runTool(input: AiToolRunInput): Promise<AiToolRunResult>;
	explainEvidence(input: EvidenceExplainInput): Promise<EvidenceExplainResult>;
	listModes(): Promise<AiMode[]>;
	setMode(mode: AiModeId): Promise<void>;
	getMode(): Promise<AiModeId>;
}
