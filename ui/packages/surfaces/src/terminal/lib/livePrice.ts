// 라이브 시세 훅 (증권사 API) · 키 노출 금지 설계.
// 정적 사이트에 증권사 API 키를 직접 넣을 수 없으므로(공개=탈취), 키는 엣지 Worker 시크릿에만 둔다.
// 프론트는 그 Worker URL 만 호출 → Worker 가 REST quote 프록시 또는 KIS websocket approval_key 발급.
//
//   VITE_DARTLAB_QUOTE_WORKER = https://<your-worker>.workers.dev   (미설정 시 라이브 비활성)
//
// 키 발급 전(또는 미설정) → null 반환 → 호출측은 EOD(전일 종가)까지만 표시. ("키 없으면 어제까지")
const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)

// vite 환경 안전 캐스트 · 빌드타임 설정(셸 무관 이식성, origin.ts VITE_DARTLAB_HF_RESOLVE 동일 패턴)
const viteEnv = (import.meta as { env?: Record<string, string | undefined> }).env;
const WORKER_URL = viteEnv?.VITE_DARTLAB_QUOTE_WORKER ?? '';

export interface LiveQuote {
	code: string;
	last: number;
	change: number; // %
	at: number; // epoch ms
}

export function liveEnabled(): boolean {
	return browser && !!WORKER_URL;
}

/** 라이브 last 시세. Worker 미설정/실패 → null (EOD fallback). */
export async function fetchLiveQuote(stockCode: string): Promise<LiveQuote | null> {
	if (!liveEnabled()) return null;
	try {
		const r = await fetch(`${WORKER_URL.replace(/\/+$/, '')}/quote/${encodeURIComponent(stockCode)}`);
		if (!r.ok) return null;
		return (await r.json()) as LiveQuote;
	} catch {
		return null;
	}
}
