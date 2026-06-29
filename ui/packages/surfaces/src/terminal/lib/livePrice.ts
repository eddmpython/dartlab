// 라이브 시세 훅 — 키 노출 금지 설계.
// 로컬 DartLab 서버가 KIS/네이버 quote·minute endpoint 를 서버측 프록시로 호출한다.
// 공개 정적 빌드에서 유료 증권사/KIS 키를 브라우저에 넣지 않는다.
//
//   로컬: same-origin /api/dartlab/live/*
//   선택: VITE_DARTLAB_QUOTE_WORKER = https://<your-worker>.workers.dev
//
// 서버/Worker 미설정 또는 실패 → null 반환 → 호출측은 EOD 가격을 유지한다.
const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)

// vite 환경 안전 캐스트 — 빌드타임 설정(셸 무관 이식성, origin.ts VITE_DARTLAB_HF_RESOLVE 동일 패턴)
const viteEnv = (import.meta as { env?: Record<string, string | undefined> }).env;
const WORKER_URL = viteEnv?.VITE_DARTLAB_QUOTE_WORKER ?? '';

export interface LiveQuote {
	code: string;
	name?: string;
	price: number;
	changeAmount: number;
	changeRate: number;
	open?: number | null;
	high?: number | null;
	low?: number | null;
	volume?: number | null;
	tradedValue?: number | null;
	marketCap?: number | null;
	marketStatus?: string;
	marketStatusLabel?: string;
	isLive: boolean;
	provider: 'kis' | 'naver' | string;
	refreshIntervalMs?: number;
	tradedAt: string;
	updatedAt: string;
}

export type MinuteTimeframe = '1m' | '3m' | '5m';

export interface MinuteBar {
	t: string;
	o: number;
	h: number;
	l: number;
	c: number;
	v: number;
}

export interface MinuteBarsResponse {
	code: string;
	provider: 'kis' | 'naver' | string;
	currency: 'KRW' | string;
	basisDate: string;
	isFallbackDate?: boolean;
	timeframe: MinuteTimeframe;
	bars: MinuteBar[];
	updatedAt: string;
}

function localApi(path: string): string {
	return path;
}

function workerApi(path: string): string {
	return `${WORKER_URL.replace(/\/+$/, '')}${path}`;
}

export function liveEnabled(): boolean {
	return browser;
}

/** 라이브 last 시세. Worker 미설정/실패 → null (EOD fallback). */
export async function fetchLiveQuote(stockCode: string): Promise<LiveQuote | null> {
	if (!liveEnabled()) return null;
	const path = `/api/dartlab/live/quote?code=${encodeURIComponent(stockCode)}`;
	const urls = [localApi(path), ...(WORKER_URL ? [workerApi(`/quote/${encodeURIComponent(stockCode)}`)] : [])];
	for (const url of urls) {
		try {
			const r = await fetch(url, { cache: 'no-store' });
			if (!r.ok) continue;
			const data = (await r.json()) as LiveQuote;
			if (data && Number.isFinite(data.price)) return data;
		} catch {
			// try next source
		}
	}
	return null;
}

/** 단일 종목 1/3/5분봉. 실패 → null (기존 차트 유지). */
export async function fetchMinuteBars(stockCode: string, timeframe: MinuteTimeframe): Promise<MinuteBarsResponse | null> {
	if (!liveEnabled()) return null;
	try {
		const qs = new URLSearchParams({ code: stockCode, timeframe });
		const r = await fetch(localApi(`/api/dartlab/live/minute?${qs.toString()}`), { cache: 'no-store' });
		if (!r.ok) return null;
		const data = (await r.json()) as MinuteBarsResponse;
		return Array.isArray(data.bars) && data.bars.length ? data : null;
	} catch {
		return null;
	}
}
