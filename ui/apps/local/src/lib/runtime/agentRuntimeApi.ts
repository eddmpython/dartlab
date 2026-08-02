import type { ProductOutcomeReceipt, RuntimeProbe } from '$lib/generated/agentRuntime';

export interface AgentRuntimeInfo extends RuntimeProbe {
	displayName: string;
	driver: string;
	protocol: string;
	officialUrl: string;
	mcp: { connected: boolean; mode?: string; detail?: string | null };
	groundedReady: boolean;
}

export interface RuntimePlan {
	runtimeId: string;
	argv: string[];
	digest: string;
	officialUrl?: string;
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
	const value = await requestJson<{ runtimes: AgentRuntimeInfo[] }>(`/api/agent/runtimes?refresh=${refresh}`);
	return value.runtimes;
}

export function planRuntimeInstall(runtimeId: string): Promise<RuntimePlan> {
	return requestJson(`/api/agent/runtimes/${runtimeId}/install/plan`, { method: 'POST' });
}

export function planRuntimeMcp(runtimeId: string): Promise<RuntimePlan> {
	return requestJson(`/api/agent/runtimes/${runtimeId}/mcp/plan`, { method: 'POST' });
}

export function applyRuntimePlan(kind: 'install' | 'mcp', plan: RuntimePlan): Promise<{ ok: boolean; stdout: string }> {
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

export function verifyOutcomeEvidence(outcomeId: string, refId: string): Promise<ProductOutcomeReceipt> {
	return requestJson(`/api/agent/product-outcomes/${encodeURIComponent(outcomeId)}/verify`, {
		method: 'POST',
		body: JSON.stringify({ refId })
	});
}
