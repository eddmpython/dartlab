// 로컬 AiPort · 로컬 provider 게이트(adapters/local/api) 경유로 로컬 Python 서버(AG-UI 게이트웨이) 연결.
// capabilities() 는 /api/status 로 provider 구성 여부 probe → 있으면 advanced, 없으면 deterministic(throw 금지·정직 강등).
// streamAsk 는 게이트 SSE 경로(api.streamAgentRun) · SSE 파싱/요청 본문 구성은 게이트(api/stream.ts)에 있다.
// raw fetch·SSE 파싱은 이 source 가 직접 갖지 않는다(로컬 /api 호출 단일 게이트 집결, 02 §5).
import type {
	AiAskInput,
	AiAskResult,
	AiCapabilities,
	AiMode,
	AiModeId,
	AiPort,
	AiStreamEvent,
	AiToolRunInput,
	AiToolRunResult,
	EvidenceExplainResult,
	EvidenceRef
} from '@dartlab/ui-contracts';
import type { LocalApi } from '../api/localApi';

interface StatusProbe {
	runtimes?: Array<{
		runtimeId: string;
		displayName: string;
		state: string;
		version?: string | null;
		mcp?: { connected?: boolean };
		groundedReady?: boolean;
	}>;
}

async function collectAsk(api: LocalApi, input: AiAskInput): Promise<AiAskResult> {
	let text = '';
	const refs: EvidenceRef[] = [];
	for await (const ev of api.streamAgentRun(input)) {
		if (ev.type === 'TEXT_MESSAGE_CONTENT') text += ev.delta;
		else if (ev.type === 'TOOL_CALL_RESULT') refs.push(...ev.refDetails);
		else if (ev.type === 'RUN_ERROR') throw new Error(ev.message);
	}
	return { text, refs };
}

export function localAiPort(api: LocalApi): AiPort {
	let mode: AiModeId = 'terminal';
	return {
		async capabilities(): Promise<AiCapabilities> {
			const status = await api.getJson<StatusProbe>('/api/agent/runtimes');
			const runtimes = status?.runtimes ?? [];
			const preferred = typeof localStorage !== 'undefined' ? localStorage.getItem('dartlab-agent-runtime') : null;
			const selected = runtimes.find((item) => item.runtimeId === preferred && item.groundedReady === true)
				?? runtimes.find((item) => item.groundedReady === true)
				?? null;
			if (selected) {
				return {
					tier: 'advanced',
					streaming: true,
					toolCalling: selected.mcp?.connected === true,
					localWorkspace: true,
					deterministicAnswers: false,
					providerLabel: selected.displayName,
					modelLabel: selected.version ?? undefined,
					runtimeId: selected.runtimeId
				};
			}
			return {
				tier: 'deterministic',
				streaming: true,
				toolCalling: false,
				localWorkspace: true,
				deterministicAnswers: false,
				upgradeHint: '지원하는 agent CLI가 없습니다. Runtime Center에서 설치 계획을 확인하세요.'
			};
		},
		ask(input) {
			return collectAsk(api, input);
		},
		streamAsk(input): AsyncGenerator<AiStreamEvent> {
			return api.streamAgentRun(input);
		},
		// 로컬은 단일 도구 직접 실행 엔드포인트 미보유(도구는 streamAsk 내부에서 에이전트가 실행) · honest error(throw 아님).
		async runTool(input: AiToolRunInput): Promise<AiToolRunResult> {
			return {
				status: 'error',
				summary: `단일 도구 직접 실행은 미지원: ${input.toolName}`,
				refs: [],
				error: 'runTool_unsupported'
			};
		},
		async explainEvidence(): Promise<EvidenceExplainResult> {
			return { text: '', refs: [] };
		},
		async listModes(): Promise<AiMode[]> {
			return [
				{ id: 'chat', label: '챗', description: '일반 대화·질의', available: true },
				{ id: 'terminal', label: '터미널', description: '터미널 운영 모드', available: true }
			];
		},
		async setMode(next) {
			mode = next;
		},
		async getMode() {
			return mode;
		}
	};
}
