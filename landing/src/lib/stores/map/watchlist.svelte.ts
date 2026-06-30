/**
 * 워치리스트 · localStorage 기반 익명 저장.
 *
 * - 최대 20개 stockCode
 * - 페이지 새로고침/재방문 시 복원
 * - URL 공유: `?watch=AAA,BBB,...` 로 export/import
 * - 구독·계정 불필요 · 로컬 저장
 *
 * 사용:
 * ```ts
 * import { watchlist } from '$lib/stores/map/watchlist.svelte';
 * watchlist.add('005930');
 * watchlist.has('005930'); // true
 * watchlist.items;         // ['005930', ...]
 * ```
 */

const KEY = 'dartlab.map.watchlist';
const MAX = 20;

function _load(): string[] {
	if (typeof localStorage === 'undefined') return [];
	try {
		const raw = localStorage.getItem(KEY);
		if (!raw) return [];
		const arr = JSON.parse(raw);
		if (!Array.isArray(arr)) return [];
		return arr.filter((x) => typeof x === 'string').slice(0, MAX);
	} catch {
		return [];
	}
}

function _save(items: string[]) {
	if (typeof localStorage === 'undefined') return;
	try {
		localStorage.setItem(KEY, JSON.stringify(items));
	} catch {
		/* noop */
	}
}

class WatchlistStore {
	items = $state<string[]>(_load());

	get count(): number {
		return this.items.length;
	}
	get isFull(): boolean {
		return this.items.length >= MAX;
	}
	has(stockCode: string): boolean {
		return this.items.includes(stockCode);
	}
	add(stockCode: string): boolean {
		if (!stockCode || this.has(stockCode) || this.isFull) return false;
		this.items = [...this.items, stockCode];
		_save(this.items);
		return true;
	}
	remove(stockCode: string) {
		this.items = this.items.filter((x) => x !== stockCode);
		_save(this.items);
	}
	toggle(stockCode: string): boolean {
		return this.has(stockCode) ? (this.remove(stockCode), false) : this.add(stockCode);
	}
	clear() {
		this.items = [];
		_save(this.items);
	}
	/** URL 공유용 문자열 · `?watch=005930,000660,...` */
	toQuery(): string {
		return this.items.join(',');
	}
	/** URL 에서 복원 (기존 덮어쓰기) */
	fromQuery(q: string) {
		if (!q) return;
		const codes = q.split(',').map((x) => x.trim()).filter(Boolean).slice(0, MAX);
		this.items = codes;
		_save(this.items);
	}
}

export const watchlist = new WatchlistStore();
