/**
 * Scan Studio 클라이언트 캐시 · IndexedDB 기반.
 *
 * priceMap / valuationMap / changesMap 결과를 직렬화 후 저장.
 * 재방문 시 즉시 hit → 0초 first-paint of 가격·시총·1Y·sparkline.
 *
 * TTL: 6시간 (HF parquet 매일 KST 17:00~18:00 갱신, 그 후 만료시 fresh fetch).
 * 저장 부피: priceMap 약 800KB (sparkline 포함) · IndexedDB 한계 대비 안전.
 */

const DB_NAME = 'dartlab-scan';
const DB_VERSION = 1;
const STORE = 'cache';
const TTL_MS = 6 * 60 * 60 * 1000;

interface CacheEntry<T> {
	key: string;
	ts: number;
	data: T;
}

let _dbPromise: Promise<IDBDatabase | null> | null = null;

function openDb(): Promise<IDBDatabase | null> {
	if (typeof window === 'undefined' || !window.indexedDB) {
		return Promise.resolve(null);
	}
	if (_dbPromise) return _dbPromise;
	_dbPromise = new Promise((resolve) => {
		const req = indexedDB.open(DB_NAME, DB_VERSION);
		req.onupgradeneeded = () => {
			const db = req.result;
			if (!db.objectStoreNames.contains(STORE)) {
				db.createObjectStore(STORE, { keyPath: 'key' });
			}
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => {
			console.warn('[scan/cache] IndexedDB open 실패', req.error);
			resolve(null);
		};
	});
	return _dbPromise;
}

/** 캐시에서 Map 으로 hydrate. 만료/없음 시 null. */
export async function readCachedMap<V>(key: string): Promise<Map<string, V> | null> {
	const db = await openDb();
	if (!db) return null;
	return new Promise((resolve) => {
		try {
			const tx = db.transaction(STORE, 'readonly');
			const req = tx.objectStore(STORE).get(key);
			req.onsuccess = () => {
				const entry = req.result as CacheEntry<Array<[string, V]>> | undefined;
				if (!entry) return resolve(null);
				if (Date.now() - entry.ts > TTL_MS) {
					console.info(`[scan/cache] ${key} 만료 · refresh 필요`);
					return resolve(null);
				}
				const map = new Map<string, V>(entry.data);
				console.info(
					`[scan/cache] ✅ ${key} hit · ${map.size}사 (${((Date.now() - entry.ts) / 1000 / 60).toFixed(0)}분 전 저장)`
				);
				resolve(map);
			};
			req.onerror = () => resolve(null);
		} catch (err) {
			console.warn('[scan/cache] read 예외', err);
			resolve(null);
		}
	});
}

/** Map 을 캐시에 저장 (기존 entry 덮어쓰기). */
export async function writeCachedMap<V>(key: string, map: Map<string, V>): Promise<void> {
	const db = await openDb();
	if (!db) return;
	return new Promise((resolve) => {
		try {
			const tx = db.transaction(STORE, 'readwrite');
			const entry: CacheEntry<Array<[string, V]>> = {
				key,
				ts: Date.now(),
				data: Array.from(map.entries())
			};
			const req = tx.objectStore(STORE).put(entry);
			req.onsuccess = () => {
				console.info(`[scan/cache] ${key} 저장 · ${map.size}사`);
				resolve();
			};
			req.onerror = () => {
				console.warn(`[scan/cache] ${key} 저장 실패`, req.error);
				resolve();
			};
		} catch (err) {
			console.warn('[scan/cache] write 예외', err);
			resolve();
		}
	});
}

/** 모든 캐시 삭제 (디버그용). */
export async function clearScanCache(): Promise<void> {
	const db = await openDb();
	if (!db) return;
	return new Promise((resolve) => {
		try {
			const tx = db.transaction(STORE, 'readwrite');
			const req = tx.objectStore(STORE).clear();
			req.onsuccess = () => resolve();
			req.onerror = () => resolve();
		} catch {
			resolve();
		}
	});
}

export const CACHE_KEYS = {
	prices: 'priceMap.v5',
	valuation: 'valuationMap.v5',
	changes: 'changesMap.v5'
} as const;
