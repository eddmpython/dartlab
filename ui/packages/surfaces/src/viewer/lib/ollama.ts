// 로컬 Ollama(http://localhost:11434) 연동 · 사용자 PC에서 도는 더 큰 모델로 품질 향상(옵션 레인).
// 자동 프로브 금지: detectOllama 는 반드시 사용자 제스처(연결 버튼 클릭) 뒤에만 호출 · Chrome 142+
//   Local Network Access(LNA) 권한 팝업이 제스처를 요구한다(제스처 없이 부르면 조용히 차단).
// 외부 전송 0(localhost loopback). 모델 본문(근거)은 buildEvidenceBlock 의 untrusted 마커로 이미 감싸져 옴.
// 호출 허용 엔드포인트는 정확히 2개: GET /api/tags(감지), POST /api/chat(스트리밍). pull/delete/create/push 등 금지.

const OLLAMA_URL = 'http://localhost:11434';

// pull 안내와 동일 우선순위(작고 한국어 강한 모델 먼저). detect 가 실제 설치된 것 중 첫 일치를 고른다.
// exaone3.5 는 한국어 품질 우위지만 ~4.8GB → 설치돼 있으면 우선, 기본 pull 안내는 가벼운 qwen2.5:3b.
const PREFERRED = ['exaone3.5:7.8b', 'qwen2.5:7b', 'qwen2.5:3b', 'gemma2:2b', 'llama3.2:3b'];

// Chrome 142+ LNA + mixed-content(https→http://localhost) 예외를 같은 메커니즘으로 적용시키는 비표준
// RequestInit 확장. 표준 DOM lib 타입에 없어 캐스팅으로 주입(미지원 브라우저는 무시).
type LocalRequestInit = RequestInit & { targetAddressSpace?: 'local' };

export interface OllamaStatus {
	ok: boolean;
	models: string[]; // 설치된 모델 태그 전체 (예: ["qwen2.5:3b", "exaone3.5:7.8b"])
	pick: string | null; // 자동 선택 모델(PREFERRED 우선, 없으면 models[0])
	reason?: 'unreachable' | 'cors' | 'no-model' | 'timeout';
}

export interface OllamaChatMessage {
	role: 'system' | 'user' | 'assistant';
	content: string;
}

// 사용자 클릭 시에만 호출. /api/tags 로 살아있음+모델목록 확인. 2초 타임아웃(미실행 시 TCP 대기 방지).
export async function detectOllama(): Promise<OllamaStatus> {
	try {
		const res = await fetch(`${OLLAMA_URL}/api/tags`, {
			method: 'GET',
			targetAddressSpace: 'local',
			signal: AbortSignal.timeout(2000)
		} as LocalRequestInit);
		if (!res.ok) return { ok: false, models: [], pick: null, reason: 'unreachable' };
		const data = (await res.json()) as { models?: { name: string }[] };
		const models: string[] = (data.models ?? []).map((m) => m.name);
		if (!models.length) return { ok: false, models, pick: null, reason: 'no-model' };
		// 정확 태그 일치 → 같은 family(태그 접두) 일치 → 첫 모델.
		const pick =
			PREFERRED.find((p) => models.includes(p)) ??
			PREFERRED.find((p) => models.some((m) => m.startsWith(p.split(':')[0] + ':'))) ??
			models[0];
		return { ok: true, models, pick };
	} catch (e) {
		// TimeoutError = 타임아웃. 나머지 TypeError("Failed to fetch") = 미실행/CORS(OLLAMA_ORIGINS 미설정)/LNA 거부
		// · 브라우저가 셋을 구분 안 줌. UX 는 한 메시지(cors)로 통일.
		const reason = e instanceof Error && e.name === 'TimeoutError' ? 'timeout' : 'cors';
		return { ok: false, models: [], pick: null, reason };
	}
}

// 스트리밍 채팅 · POST /api/chat. messages 는 buildChatMessages 산출(provider 무관, OpenAI 호환 형식).
// Ollama 는 NDJSON(줄당 1 JSON) 반환. 청크 경계가 줄 경계와 무관하므로 buf 에 모아 \n 으로만 잘라 파싱.
export async function ollamaChat(
	messages: OllamaChatMessage[],
	model: string,
	opts: { onToken?: (delta: string) => void; signal?: AbortSignal } = {}
): Promise<string> {
	const res = await fetch(`${OLLAMA_URL}/api/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		targetAddressSpace: 'local',
		body: JSON.stringify({
			model,
			messages,
			stream: true,
			options: { temperature: 0.4, num_predict: 640 }
		}),
		signal: opts.signal
	} as LocalRequestInit);
	if (!res.ok || !res.body) throw new Error(`Ollama 응답 오류 (${res.status})`);

	const reader = res.body.getReader();
	const dec = new TextDecoder();
	let buf = '';
	let full = '';
	for (;;) {
		const { done, value } = await reader.read();
		if (done) break;
		buf += dec.decode(value, { stream: true }); // {stream:true} → 멀티바이트 한글 분할 안전
		let nl: number;
		while ((nl = buf.indexOf('\n')) !== -1) {
			const line = buf.slice(0, nl).trim();
			buf = buf.slice(nl + 1);
			if (!line) continue;
			let j: { message?: { content?: string }; done?: boolean };
			try {
				j = JSON.parse(line);
			} catch {
				continue; // 부분/깨진 줄 방어
			}
			const delta = j.message?.content ?? '';
			if (delta) {
				full += delta;
				opts.onToken?.(delta);
			}
			if (j.done) return full.trim(); // done:true 줄 = 종료 신호
		}
	}
	return full.trim();
}
