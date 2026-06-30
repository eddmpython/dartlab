// 동시 동일 요청 중복 제거 · in-flight Promise 공유. 어댑터 구현 공용.

export class RequestDedup {
	#inflight = new Map<string, Promise<unknown>>();

	run<T>(key: string, fn: () => Promise<T>): Promise<T> {
		const existing = this.#inflight.get(key);
		if (existing) return existing as Promise<T>;
		const p = fn().finally(() => {
			this.#inflight.delete(key);
		});
		this.#inflight.set(key, p);
		return p;
	}
}
