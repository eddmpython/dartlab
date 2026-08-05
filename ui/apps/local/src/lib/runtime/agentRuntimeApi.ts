import type { ProductOutcomeReceipt, RuntimeProbe } from '$lib/generated/agentRuntime';

export interface AgentRuntimeInfo extends RuntimeProbe {
	displayName: string;
	driver: string;
	protocol: string;
	officialUrl: string;
	mcp: { connected: boolean; mode?: string; detail?: string | null };
	auth: { state: 'authenticated' | 'authRequired' | 'unsupported' | 'missing' | 'unavailable'; authenticated?: boolean | null };
	groundedReady: boolean;
	embeddedGrounding: boolean;
	canInstall: boolean;
	canConnect: boolean;
	canLogin: boolean;
	primaryAction: 'install' | 'login' | 'connect' | 'select' | 'unsupported';
	readiness: {
		install: string;
		auth: string;
		protocol: string;
		grounding: string;
		ready: boolean;
	};
	blockingReason?: string | null;
	recommendedAction?: string | null;
	semanticToolsReady?: boolean;
	investmentContractReady?: boolean;
	investmentReady?: boolean;
}

export interface RuntimePlan {
	runtimeId: string;
	argv: string[];
	digest?: string;
	officialUrl?: string;
}

export interface AgentRuntimeStatus {
	runtimes: AgentRuntimeInfo[];
	defaultRuntimeId?: string | null;
}

export interface RuntimeSetupPlan {
	runtimeId: string;
	displayName: string;
	changes: string[];
	requiresLogin: boolean;
	alreadyReady: boolean;
	approvalRequired: boolean;
	prerequisitePlan?: { key: string; displayName: string; argv: string[] } | null;
	installPlan?: RuntimePlan | null;
	mcpPlan?: RuntimePlan | null;
}

export interface RuntimeSetupResult {
	runtimeId: string;
	state: 'ready' | 'authPending' | 'blocked' | 'cancelled';
	investmentReady: boolean;
	mutationCount: number;
	approvalCount: number;
	steps: Array<{ key: string; status: string; detail: string }>;
	readiness: Record<string, boolean>;
	nextAction?: string | null;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(path, {
		...init,
		headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }
	});
	const value = (await response.json()) as T & { detail?: string };
	if (!response.ok) throw new Error(value.detail ?? `HTTP ${response.status}`);
	return value;
}

export async function listAgentRuntimes(refresh = false): Promise<AgentRuntimeInfo[]> {
	const value = await getAgentRuntimeStatus(refresh);
	return value.runtimes;
}

export function getAgentRuntimeStatus(refresh = false): Promise<AgentRuntimeStatus> {
	return requestJson(`/api/agent/runtimes?refresh=${refresh}`);
}

export function selectDefaultRuntime(runtimeId: string): Promise<{ ok: boolean; defaultRuntimeId: string }> {
	return requestJson('/api/agent/runtimes/default', {
		method: 'POST',
		body: JSON.stringify({ runtimeId })
	});
}

export function planRuntimeSetup(runtimeId?: string): Promise<RuntimeSetupPlan> {
	return requestJson('/api/agent/runtimes/setup/plan', {
		method: 'POST',
		body: JSON.stringify({ runtimeId: runtimeId || null, approved: false })
	});
}

export function applyRuntimeSetup(runtimeId: string): Promise<RuntimeSetupResult> {
	return requestJson('/api/agent/runtimes/setup/apply', {
		method: 'POST',
		body: JSON.stringify({ runtimeId, approved: true })
	});
}

export function planRuntimeInstall(runtimeId: string): Promise<RuntimePlan> {
	return requestJson(`/api/agent/runtimes/${runtimeId}/install/plan`, { method: 'POST' });
}

export function planRuntimeLogin(runtimeId: string): Promise<RuntimePlan> {
	return requestJson(`/api/agent/runtimes/${runtimeId}/login/plan`, { method: 'POST' });
}

export function planRuntimeMcp(runtimeId: string): Promise<RuntimePlan> {
	return requestJson(`/api/agent/runtimes/${runtimeId}/mcp/plan`, { method: 'POST' });
}

export function applyRuntimePlan(kind: 'install' | 'mcp', plan: RuntimePlan): Promise<{ ok: boolean; stdout: string }> {
	if (!plan.digest) return Promise.reject(new Error('승인 digest가 없는 계획은 실행할 수 없습니다.'));
	return requestJson(`/api/agent/runtimes/${kind}/apply`, {
		method: 'POST',
		body: JSON.stringify({ runtimeId: plan.runtimeId, approvedDigest: plan.digest })
	});
}

export function resolveAgentApproval(sessionId: string, approvalId: string, allow: boolean): Promise<{ ok: boolean }> {
	return requestJson(`/api/agent/sessions/${encodeURIComponent(sessionId)}/approval`, {
		method: 'POST',
		body: JSON.stringify({ approvalId, allow })
	});
}

export function cancelAgentSession(sessionId: string): Promise<{ ok: boolean }> {
	return requestJson(`/api/agent/sessions/${encodeURIComponent(sessionId)}/cancel`, { method: 'POST' });
}

export function deleteAgentSession(sessionId: string): Promise<{ ok: boolean }> {
	return requestJson(`/api/agent/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}

export function verifyOutcomeEvidence(outcomeId: string, refId: string): Promise<{
	evidence: { id: string; title?: string; source?: string; payload?: Record<string, unknown> };
	receipt: ProductOutcomeReceipt;
}> {
	return requestJson(`/api/agent/product-outcomes/${encodeURIComponent(outcomeId)}/verify`, {
		method: 'POST',
		body: JSON.stringify({ refId })
	});
}

export function resolveOutcomeEvidence(outcomeId: string, refId: string): Promise<{
	evidence: { id: string; title?: string; source?: string; payload?: Record<string, unknown> };
}> {
	return requestJson(
		`/api/agent/product-outcomes/${encodeURIComponent(outcomeId)}/evidence/${encodeURIComponent(refId)}`
	);
}

export interface OpenDartStatus {
	configured: boolean;
	source: string;
	keyCount: number;
	envPath: string;
	writable: boolean;
}

export interface DataStats {
	[key: string]: unknown;
}

/** 설정 화면의 OpenDART 키 상태. /api/status 의 openDart 블록을 그대로 쓴다. */
export async function getOpenDartStatus(): Promise<OpenDartStatus> {
	const value = await requestJson<{ openDart: OpenDartStatus }>('/api/status?probe=0');
	return value.openDart;
}

/** OpenDART 키 저장. 서버가 프로젝트 .env 에 기록한다. */
export function saveDartKey(apiKey: string): Promise<{ ok: boolean; envPath: string; openDart: OpenDartStatus }> {
	return requestJson('/api/openapi/dart-key', {
		method: 'PUT',
		body: JSON.stringify({ api_key: apiKey })
	});
}

/** OpenDART 키 제거. */
export function clearDartKey(): Promise<{ ok: boolean; envPath: string; openDart: OpenDartStatus }> {
	return requestJson('/api/openapi/dart-key', { method: 'DELETE' });
}

/** 로컬 데이터 현황(종목 수, 용량 등). */
export function getDataStats(): Promise<DataStats> {
	return requestJson('/api/data/stats');
}
