import { readJsonCache, writeJsonCache } from './cache/cacheStore';
import { RequestDedup } from './cache/requestDedup';
import { originUrl, publicJsonPolicy, type PublicJsonPolicy, type PublicJsonSource } from './origins/registry';

// HF resolve base URL 은 origin.ts SSOT 에서 (내부 사용 + consumers 호환 위해 re-export).
import { HF_RESOLVE } from './origins/hf';
export { HF_RESOLVE };

// static 경로 base · 옛 `$app/paths base` 의존을 주입으로 대체 (runtime 패키지는 SvelteKit 을 모른다).
// 과도기: 앱 shell(landing +layout)이 1회 호출. 4a-2 에서 RuntimeEnvironment.basePath 로 정식화.
let base = '';
export function setStaticBase(value: string): void {
	base = value.replace(/\/+$/, '');
}
export type FetchLike = typeof fetch;

export interface LoadJsonOptions {
	fetchFn: FetchLike;
	required?: boolean;
	/** @deprecated Source order is owned by publicJsonPolicy and cannot be overridden. */
	preferLocal?: boolean;
	/** @deprecated Cache lifetime is owned by publicJsonPolicy and cannot be overridden. */
	ttlMs?: number;
}

function normalizePath(path: string): string {
	return path.replace(/^\/+/, '');
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
// 옛 loadJson 은 dedup 이 없어 첫 페인트에 같은 JSON 을 중복 fetch 했다. 원본·캐시 정책은
// origins/registry.publicJsonPolicy SSOT, 여기서는 실행과 동시요청 공유만 담당한다.
const jsonDedup = new RequestDedup();

export async function loadJson<T>(
	path: string,
	{ fetchFn, required = false }: LoadJsonOptions
): Promise<T | null> {
	const normalized = normalizePath(path);
	const policy = publicJsonPolicy(normalized);
	// 원본 순서가 경로 정책으로 고정됐으므로 같은 path 는 모든 화면에서 같은 in-flight 요청을 공유한다.
	const result = (await jsonDedup.run(normalized, () =>
		resolveJson<T>(normalized, fetchFn, policy)
	)) as T | null;
	if (result == null && required) throw new Error(`${normalized} 로드 실패`);
	return result;
}

function jsonSourceUrl(source: PublicJsonSource, normalized: string): string {
	return source === 'hfLanding' ? originUrl('hf', `landing/${normalized}`) : `${base}/${normalized}`;
}

// cacheStore + registry 가 정한 원본 폴백 사다리 실행. 호출 화면별 분기 금지.
async function resolveJson<T>(
	normalized: string,
	fetchFn: FetchLike,
	policy: PublicJsonPolicy
): Promise<T | null> {
	const cacheable = policy.cache.scope === 'persistent';
	const cached = cacheable ? await readJsonCache<T>(normalized, policy.cache.ttlMs) : null;
	if (cached != null) return cached;

	for (const source of policy.sourceOrder) {
		const value = await fetchJson<T>(jsonSourceUrl(source, normalized), fetchFn);
		if (value != null) {
			if (cacheable) void writeJsonCache(normalized, value);
			return value;
		}
	}

	return cacheable && policy.cache.staleOnError
		? await readJsonCache<T>(normalized, policy.cache.ttlMs, { allowStale: true })
		: null;
}

export async function loadHfJson<T>(
	path: string,
	{ fetchFn, required = false }: LoadJsonOptions
): Promise<T | null> {
	const normalized = normalizePath(path);
	const cacheKey = `hf/${normalized}`;
	const policy = publicJsonPolicy(normalized);
	const cacheable = policy.cache.scope === 'persistent';
	const cached = cacheable ? await readJsonCache<T>(cacheKey, policy.cache.ttlMs) : null;
	if (cached != null) return cached;

	const hf = await fetchJson<T>(originUrl('hf', normalized), fetchFn);
	if (hf != null) {
		if (cacheable) void writeJsonCache(cacheKey, hf);
		return hf;
	}

	const stale = cacheable && policy.cache.staleOnError
		? await readJsonCache<T>(cacheKey, policy.cache.ttlMs, { allowStale: true })
		: null;
	if (stale != null) return stale;

	if (required) throw new Error(`${normalized} HF 로드 실패`);
	return null;
}

export function prewarmJson(paths: string[], fetchFn: FetchLike): void {
	for (const path of paths) {
		void loadJson(path, { fetchFn, required: false });
	}
}
