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
	providers?: Record<
		string,
		{
			available?: boolean | null;
			secretConfigured?: boolean;
			selected?: boolean;
			label?: string;
			model?: string;
		}
	>;
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
			const status = await api.getJson<StatusProbe>('/api/status');
			const providers = status?.providers ?? {};
			// 연결상태는 *선택된* provider 의 실제 available 로만 판정한다. secretConfigured 만 보면
			// 세션만료·미로그인 provider 를 advanced 로 오보한다(게이트웨이는 LLM 없는 heuristic 으로 도는데 UI 만 연결된 척).
			const selected = Object.values(providers).find((p) => p?.selected) ?? null;
			const connected = selected?.available === true;
			if (connected) {
				return {
					tier: 'advanced',
					streaming: true,
					toolCalling: true,
					localWorkspace: true,
					deterministicAnswers: true,
					providerLabel: selected?.label ?? 'local',
					modelLabel: selected?.model
				};
			}
			// LLM 미연결(선택 provider 사용불가·미선택). heuristic 폴백은 신뢰 낮으므로 미연결로 안내한다.
			return {
				tier: 'deterministic',
				streaming: true,
				toolCalling: false,
				localWorkspace: true,
				deterministicAnswers: false,
				providerLabel: selected?.label,
				upgradeHint: 'AI 공급자가 연결되어 있지 않습니다. 설정에서 공급자(예 Ollama·Gemini)를 연결하세요.'
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
