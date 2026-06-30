// 단순 TTL 캐시 · 어댑터 구현 공용. BoundedCache 원칙(상한 필수 · 무한 증식 금지).

export interface RuntimeCacheOptions {
	maxEntries: number;
	ttlMs: number;
}

interface Entry<V> {
	value: V;
	expiresAt: number;
}

export class RuntimeCache<V> {
	#map = new Map<string, Entry<V>>();
	#opts: RuntimeCacheOptions;

	constructor(opts: RuntimeCacheOptions) {
		this.#opts = opts;
	}

	get(key: string, now: number = Date.now()): V | undefined {
		const e = this.#map.get(key);
		if (!e) return undefined;
		if (e.expiresAt < now) {
			this.#map.delete(key);
			return undefined;
		}
		// LRU 갱신
		this.#map.delete(key);
		this.#map.set(key, e);
		return e.value;
	}

	set(key: string, value: V, now: number = Date.now()): void {
		if (this.#map.size >= this.#opts.maxEntries) {
			const oldest = this.#map.keys().next().value;
			if (oldest !== undefined) this.#map.delete(oldest);
		}
		this.#map.set(key, { value, expiresAt: now + this.#opts.ttlMs });
	}

	clear(): void {
		this.#map.clear();
	}
}
