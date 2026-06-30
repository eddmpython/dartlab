// 로컬 전용 provider 게이트 · 로컬 Python 서버(:8400 /api) 호출이 모이는 단일 진입점(02 §5, 03 §2 api/).
// 데이터 코어(createDataCore = HF/캐시 가능 레인)와 분리된 별도 로컬 레인이다 · /api 는 SSE·blob·CRUD 라
// HF parquet 캐시 모델에 부적합하므로 코어를 통과시키지 않는다. 여기만 raw fetch 가 허용되는 곳이며
// (sources/ 가드 밖), 로컬 source(filing panel·ai·export·price-events)는 이 게이트만 호출한다.
//
// 계약: getJson/postJson 은 실패(4xx/5xx/네트워크) = null 정직 표기 · 호출측이 null/빈값으로 해석한다.
// silent fallback 금지(runtime.ts 규약) · 단일 경로의 부재만 null 로 표기하고 다른 소스로 우회하지 않는다.
// blob/SSE 등 비 JSON 응답은 raw Response 가 필요하므로 fetchRaw 로 노출(호출측이 ok/blob/headers 해석).
import { streamSse } from './stream';
import type { AiAskInput, AiStreamEvent } from '@dartlab/ui-contracts';

export interface LocalApi {
	/** apiBase + path 합성 절대(또는 same-origin 상대) URL. */
	url(path: string): string;
	/** GET → JSON. 실패 = null(정직 표기). */
	getJson<T>(path: string): Promise<T | null>;
	/** POST(JSON body) → JSON. 실패 = null(정직 표기). 200 이지만 비 JSON 이면 null. */
	postJson<T>(path: string, body: unknown): Promise<T | null>;
	/** raw fetch · blob/CRUD 등 JSON 아닌 응답·헤더가 필요한 호출용(export). 게이트가 URL 합성만 담당. */
	fetchRaw(path: string, init?: RequestInit): Promise<Response>;
	/** 에이전트 SSE 스트림(POST /api/agent/runs) · 캐시 부적합 전용 경로. */
	streamAgentRun(input: AiAskInput): AsyncGenerator<AiStreamEvent>;
}

/**
 * 로컬 provider 게이트 생성 · apiBase 1개로 모든 /api 호출 헬퍼를 묶는다.
 *
 * @param apiBase API 베이스(기본 '' = same-origin; dev 는 vite proxy 가 127.0.0.1:8400 으로).
 * @returns LocalApi 게이트(런타임 인스턴스당 1개를 createLocalRuntime 이 만들어 source 에 주입).
 *
 * @example
 * const api = createLocalApi('');
 * const status = await api.getJson<StatusProbe>('/api/status');
 */
export function createLocalApi(apiBase: string): LocalApi {
	const url = (path: string): string => `${apiBase}${path}`;

	async function getJson<T>(path: string): Promise<T | null> {
		try {
			const r = await fetch(url(path));
			if (!r.ok) return null;
			return (await r.json()) as T;
		} catch {
			return null;
		}
	}

	async function postJson<T>(path: string, body: unknown): Promise<T | null> {
		try {
			const r = await fetch(url(path), {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(body)
			});
			if (!r.ok) return null;
			return (await r.json()) as T;
		} catch {
			return null;
		}
	}

	function fetchRaw(path: string, init?: RequestInit): Promise<Response> {
		return fetch(url(path), init);
	}

	return {
		url,
		getJson,
		postJson,
		fetchRaw,
		streamAgentRun(input) {
			return streamSse(url('/api/agent/runs'), input);
		}
	};
}
