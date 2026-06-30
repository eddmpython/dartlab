// 로컬 StoragePort · 브라우저 localStorage 백엔드(네임스페이스 접두로 충돌 방지). 비브라우저(SSR)는 in-memory 폴백.
// 로컬 앱은 ssr=false SPA 라 실사용은 항상 브라우저 · 폴백은 컴파일/타입 안전용.
import type { RuntimeStorageKey, StoragePort } from '@dartlab/ui-contracts';

const PREFIX = 'dartlab:';

export function localStoragePort(): StoragePort {
	const browser = typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
	const subs = new Map<string, Set<(v: unknown) => void>>();
	const mem = new Map<string, unknown>();
	return {
		async get<T>(key: RuntimeStorageKey): Promise<T | null> {
			if (!browser) return (mem.get(key) as T | undefined) ?? null;
			const raw = window.localStorage.getItem(PREFIX + key);
			if (raw == null) return null;
			try {
				return JSON.parse(raw) as T;
			} catch {
				return null;
			}
		},
		async set<T>(key: RuntimeStorageKey, value: T): Promise<void> {
			if (browser) window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
			else mem.set(key, value);
			subs.get(key)?.forEach((cb) => cb(value));
		},
		async remove(key: RuntimeStorageKey): Promise<void> {
			if (browser) window.localStorage.removeItem(PREFIX + key);
			else mem.delete(key);
			subs.get(key)?.forEach((cb) => cb(null));
		},
		subscribe<T>(key: RuntimeStorageKey, cb: (value: T | null) => void): () => void {
			const set = subs.get(key) ?? new Set<(v: unknown) => void>();
			set.add(cb as (v: unknown) => void);
			subs.set(key, set);
			return () => set.delete(cb as (v: unknown) => void);
		}
	};
}
