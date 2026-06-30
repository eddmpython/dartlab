// 옛 `$app/environment browser` 의존 제거 · runtime 패키지는 SvelteKit 을 모른다.
const browser = typeof window !== 'undefined';

const CACHE_NAME = 'dartlab-data-json-v1';
const HEADER_TS = 'x-dartlab-cache-ts';

function canUseCache(): boolean {
	return browser && typeof caches !== 'undefined' && typeof location !== 'undefined';
}

function cacheRequest(path: string): Request {
	const normalized = path.replace(/^\/+/, '');
	const url = `${location.origin}/__dartlab_data_cache__/${encodeURIComponent(normalized)}`;
	return new Request(url);
}

export async function readJsonCache<T>(
	path: string,
	ttlMs: number,
	options: { allowStale?: boolean } = {}
): Promise<T | null> {
	if (!canUseCache()) return null;
	try {
		const cache = await caches.open(CACHE_NAME);
		const resp = await cache.match(cacheRequest(path));
		if (!resp) return null;

		const ts = Number(resp.headers.get(HEADER_TS)) || 0;
		const fresh = Date.now() - ts <= ttlMs;
		if (!fresh && !options.allowStale) return null;

		return (await resp.json()) as T;
	} catch {
		return null;
	}
}

export async function writeJsonCache(path: string, value: unknown): Promise<void> {
	if (!canUseCache()) return;
	try {
		const cache = await caches.open(CACHE_NAME);
		const headers = new Headers({
			'content-type': 'application/json',
			[HEADER_TS]: String(Date.now())
		});
		await cache.put(cacheRequest(path), new Response(JSON.stringify(value), { headers }));
	} catch {
		// Cache quota or private-mode failures must not block rendering.
	}
}
