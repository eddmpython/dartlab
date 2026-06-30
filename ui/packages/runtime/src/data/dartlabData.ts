import { readJsonCache, writeJsonCache } from './cache/cacheStore';
import { RequestDedup } from './cache/requestDedup';

// HF resolve base URL 은 origin.ts SSOT 에서 (내부 사용 + consumers 호환 위해 re-export).
import { HF_RESOLVE } from './origins/hf';
export { HF_RESOLVE };

// static 경로 base · 옛 `$app/paths base` 의존을 주입으로 대체 (runtime 패키지는 SvelteKit 을 모른다).
// 과도기: 앱 shell(landing +layout)이 1회 호출. 4a-2 에서 RuntimeEnvironment.basePath 로 정식화.
let base = '';
export function setStaticBase(value: string): void {
	base = value.replace(/\/+$/, '');
}
const DEFAULT_TTL_MS = 6 * 60 * 60 * 1000;

export type FetchLike = typeof fetch;

export interface LoadJsonOptions {
	fetchFn: FetchLike;
	ttlMs?: number;
	required?: boolean;
	preferLocal?: boolean;
}

function normalizePath(path: string): string {
	return path.replace(/^\/+/, '');
}

function hasHfLandingJson(path: string): boolean {
	return (
		// dashboards · mapBuild 가 매일 HF publish (git 정적 사본 4/22 동결 사고 후 신설 경로)
		path === 'dashboards/finance.json' ||
		path === 'dashboards/quarters.json' ||
		path === 'dashboards/macro.json' ||
		path === 'dashboards/meta.json' ||
		path === 'map/atlas.json' ||
		path === 'map/ecosystem.json' ||
		path === 'map/industryStats.json' ||
		path === 'map/insights.json' ||
		path === 'map/meta.json' ||
		path === 'map/movers.json' ||
		path === 'map/prices-snapshot.json' ||
		path === 'map/search-index.json' ||
		path === 'map/timeline.json' ||
		path.startsWith('map/companies/') ||
		path.startsWith('map/industries/')
	);
}

function shouldCacheJson(path: string): boolean {
	return (
		path !== 'map/ecosystem.json' &&
		path !== 'map/prices-snapshot.json' &&
		// macro 도 캐시 제외 · HF-first 신선본이 6h 캐시에 가려지는 지연 차단 (소형 파일이라 비용 0)
		path !== 'dashboards/macro.json' &&
		// industryStats 도 제외 · 분포 지표가 점증(revCagr 등 신규 metric 추가)되므로 6h 캐시가 옛 스키마를
		// 붙들면 신규 지표 의존 뷰(산업 지형도 y=매출 CAGR)가 통째 빈다. 소형(~250KB)이라 비용 0.
		path !== 'map/industryStats.json' &&
		path !== 'landing/map/ecosystem.json' &&
		path !== 'landing/map/prices-snapshot.json' &&
		path !== 'landing/map/industryStats.json' &&
		path !== 'landing/dashboards/macro.json'
	);
}

async function fetchJson<T>(url: string, fetchFn: FetchLike): Promise<T | null> {
	try {
		const resp = await fetchFn(url);
		if (!resp.ok) return null;
		return (await resp.json()) as T;
	} catch {
		return null;
	}
}

// in-flight dedup · 동시 동일 자원(여러 패널·워밍업)이 cacheStore 읽기·fetch 사다리를 1회만 공유.
// 옛 loadJson 은 dedup 이 없어 첫 페인트에 같은 JSON 을 중복 fetch 했다(소비자 per-file Map 이 그 구멍을
// 메우던 이유). 데이터 워크벤치 코어의 RequestDedup 을 JSON arm 에도 재사용(dual-SSOT · 코어로 접지 않고
// 같은 패키지 sibling arm 으로, base 전역·다중URL 폴백은 loadJson 에 남김. mainPlan/_done/data-workbench-ssot).
const jsonDedup = new RequestDedup();

export async function loadJson<T>(
	path: string,
	{ fetchFn, ttlMs = DEFAULT_TTL_MS, required = false, preferLocal = false }: LoadJsonOptions
): Promise<T | null> {
	const normalized = normalizePath(path);
	// 키에 preferLocal 포함 · 미스 시 local↔HF 우선순위가 달라 승자 자원이 갈릴 수 있다. required 는
	// 자원 동일성과 무관(전부 실패 시 throw 여부만)이라 공유 계산 밖에서 호출자별 적용.
	const result = (await jsonDedup.run(`${normalized}:${preferLocal ? 'L' : 'H'}`, () =>
		resolveJson<T>(normalized, fetchFn, ttlMs, preferLocal)
	)) as T | null;
	if (result == null && required) throw new Error(`${normalized} 로드 실패`);
	return result;
}

// cacheStore(영속·6h·stale 폴백) + local↔HF 폴백 사다리 · dedup 안에서 실행(동시 호출 공유). 순서 불변.
async function resolveJson<T>(
	normalized: string,
	fetchFn: FetchLike,
	ttlMs: number,
	preferLocal: boolean
): Promise<T | null> {
	const cacheable = shouldCacheJson(normalized);
	const cached = cacheable ? await readJsonCache<T>(normalized, ttlMs) : null;
	if (cached != null) return cached;

	if (preferLocal) {
		const local = await fetchJson<T>(`${base}/${normalized}`, fetchFn);
		if (local != null) {
			if (cacheable) void writeJsonCache(normalized, local);
			return local;
		}
	}

	if (hasHfLandingJson(normalized)) {
		const hf = await fetchJson<T>(`${HF_RESOLVE}/landing/${normalized}`, fetchFn);
		if (hf != null) {
			if (cacheable) void writeJsonCache(normalized, hf);
			return hf;
		}
	}

	if (!preferLocal) {
		const local = await fetchJson<T>(`${base}/${normalized}`, fetchFn);
		if (local != null) {
			if (cacheable) void writeJsonCache(normalized, local);
			return local;
		}
	}

	if (!hasHfLandingJson(normalized)) {
		const hf = await fetchJson<T>(`${HF_RESOLVE}/landing/${normalized}`, fetchFn);
		if (hf != null) {
			if (cacheable) void writeJsonCache(normalized, hf);
			return hf;
		}
	}

	// 전부 실패 → 만료본이라도(stale 폴백). 없으면 null(호출자 required 가 throw 판정).
	return cacheable ? await readJsonCache<T>(normalized, ttlMs, { allowStale: true }) : null;
}

export async function loadHfJson<T>(
	path: string,
	{ fetchFn, ttlMs = DEFAULT_TTL_MS, required = false }: LoadJsonOptions
): Promise<T | null> {
	const normalized = normalizePath(path);
	const cacheKey = `hf/${normalized}`;
	const cacheable = shouldCacheJson(normalized);
	const cached = cacheable ? await readJsonCache<T>(cacheKey, ttlMs) : null;
	if (cached != null) return cached;

	const hf = await fetchJson<T>(`${HF_RESOLVE}/${normalized}`, fetchFn);
	if (hf != null) {
		if (cacheable) void writeJsonCache(cacheKey, hf);
		return hf;
	}

	const stale = cacheable ? await readJsonCache<T>(cacheKey, ttlMs, { allowStale: true }) : null;
	if (stale != null) return stale;

	if (required) throw new Error(`${normalized} HF 로드 실패`);
	return null;
}

export function prewarmJson(paths: string[], fetchFn: FetchLike, ttlMs = DEFAULT_TTL_MS): void {
	for (const path of paths) {
		void loadJson(path, { fetchFn, ttlMs, required: false });
	}
}
