// 로컬 게이트 SSE 경로 · 에이전트 실행(POST /api/agent/runs)을 AiStreamEvent 스트림으로 매핑.
// SSE 는 캐시·dedup 부적합(streaming)이라 데이터 코어 request() 와 분리된 게이트 전용 경로다(02 §5).
// 서버 emitter(agentGateway._event)가 data 에 type + 계약 필드명을 그대로 실어 보내므로(AG-UI allowlist
// = ai.ts 계약 SSOT) 파싱한 객체를 그대로 통과시킨다.
import type { AiAskInput, AiStreamEvent } from '@dartlab/ui-contracts';

function buildRequestBody(input: AiAskInput): string {
	// history(이전 턴들) + 현재 prompt. 게이트웨이가 마지막 user 를 question, 나머지를 LLM history 로 분리.
	const messages = [...(input.history ?? []), { role: 'user', content: input.prompt }];
	return JSON.stringify({
		messages,
		agentId: 'dartlab-research',
		stream: true,
		workspaceContext: input.code ? { stockCode: input.code, mode: input.mode } : { mode: input.mode }
	});
}

// SSE 블록(`event:`/`data:` 라인 묶음) → AiStreamEvent. data JSON 의 type 으로 판별, 계약 필드명 일치라 그대로 통과.
function parseSseBlock(raw: string): AiStreamEvent | null {
	if (!raw.trim()) return null;
	const dataLines: string[] = [];
	for (const line of raw.split('\n')) {
		if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
	}
	const dataStr = dataLines.join('\n');
	if (!dataStr) return null;
	let obj: Record<string, unknown>;
	try {
		obj = JSON.parse(dataStr) as Record<string, unknown>;
	} catch {
		return null;
	}
	if (typeof obj.type !== 'string') return null;
	return obj as unknown as AiStreamEvent;
}

/**
 * 에이전트 SSE 스트림 · POST(SSE) → AiStreamEvent 제너레이터.
 *
 * @param endpoint 게이트가 합성한 절대(또는 same-origin) URL(예: `${apiBase}/api/agent/runs`).
 * @param input 질의 입력(prompt·code·mode).
 * @returns AiStreamEvent async generator. 네트워크/HTTP 실패는 RUN_ERROR 이벤트로 정직 표기 후 종료.
 *
 * @example
 * for await (const ev of streamSse('/api/agent/runs', input)) { ... }
 */
export async function* streamSse(endpoint: string, input: AiAskInput): AsyncGenerator<AiStreamEvent> {
	let resp: Response;
	try {
		resp = await fetch(endpoint, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
			body: buildRequestBody(input)
		});
	} catch (e) {
		yield { type: 'RUN_ERROR', runId: '', message: String(e), code: 'network_error' };
		return;
	}
	if (!resp.ok || !resp.body) {
		yield { type: 'RUN_ERROR', runId: '', message: `HTTP ${resp.status}`, code: 'http_error' };
		return;
	}
	const reader = resp.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	for (;;) {
		const { value, done } = await reader.read();
		if (done) break;
		buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
		let sep = buffer.indexOf('\n\n');
		while (sep !== -1) {
			const block = buffer.slice(0, sep);
			buffer = buffer.slice(sep + 2);
			const ev = parseSseBlock(block);
			if (ev) yield ev;
			sep = buffer.indexOf('\n\n');
		}
	}
}
