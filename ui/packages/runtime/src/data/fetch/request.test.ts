// fetch 코어 단위 테스트 · fetchFn·now 주입으로 네트워크 없이 결정론 검증.
// 캐시 적중 / in-flight dedup / 에러 비캐시 / TTL 만료 / scope 'none' 5 케이스.
import { describe, it, expect } from 'vitest';
import { createDataCore } from './request';
import type { FetchLike } from '../parquet/hfRange';

// 호출 횟수를 세는 fake fetch · 항상 200 OK + JSON payload 반환.
function countingFetch(payload: unknown): { fetchFn: FetchLike; calls: () => number } {
	let n = 0;
	const fetchFn = (async () => {
		n += 1;
		return new Response(JSON.stringify(payload), {
			status: 200,
			headers: { 'content-type': 'application/json' }
		});
	}) as FetchLike;
	return { fetchFn, calls: () => n };
}

const jsonParse = (r: Response) => r.json();

describe('createDataCore.request', () => {
	it('memory cache hit · 동일 키 두 번 호출 시 fetchFn 1 회', async () => {
		const { fetchFn, calls } = countingFetch({ v: 1 });
		const core = createDataCore({ fetchFn, now: () => 0 });
		const spec = { origin: 'hf' as const, path: 'x.json', parse: jsonParse, cacheKey: 'k-hit' };

		const a = await core.request<{ v: number }>(spec);
		const b = await core.request<{ v: number }>(spec);

		expect(calls()).toBe(1);
		expect(a).toEqual({ v: 1 });
		expect(b).toEqual({ v: 1 });
	});

	it('in-flight dedup · 동시 동일 키 2 건 시 fetchFn 1 회', async () => {
		let n = 0;
		let release!: () => void;
		const gate = new Promise<void>((r) => (release = r));
		const fetchFn = (async () => {
			n += 1;
			await gate; // 첫 호출을 in-flight 로 붙잡아 두 번째가 dedup 에 합류하도록.
			return new Response(JSON.stringify({ v: 2 }), { status: 200 });
		}) as FetchLike;

		const core = createDataCore({ fetchFn, now: () => 0 });
		const spec = { origin: 'hf' as const, path: 'y.json', parse: jsonParse, cacheKey: 'k-dedup' };

		const p1 = core.request<{ v: number }>(spec); // await 하지 않음 · in-flight 유지
		const p2 = core.request<{ v: number }>(spec);
		release();
		const [a, b] = await Promise.all([p1, p2]);

		expect(n).toBe(1);
		expect(a).toEqual({ v: 2 });
		expect(b).toEqual({ v: 2 });
	});

	it('error not cached · parse throw 후 재호출이 fetchFn 재실행', async () => {
		const { fetchFn, calls } = countingFetch({ v: 3 });
		const core = createDataCore({ fetchFn, now: () => 0 });
		let parseCalls = 0;
		// 첫 parse 는 throw(에러 전파), 두 번째는 정상값 · 에러가 캐시되지 않았음을 증명.
		const parse = async (r: Response) => {
			parseCalls += 1;
			if (parseCalls === 1) throw new Error('parse boom');
			return r.json() as Promise<{ v: number }>;
		};
		const spec = { origin: 'hf' as const, path: 'z.json', parse, cacheKey: 'k-err' };

		await expect(core.request<{ v: number }>(spec)).rejects.toThrow('parse boom');
		expect(calls()).toBe(1);

		// 실패가 캐시되지 않았으므로 두 번째 호출은 fetchFn 을 다시 부른다.
		const ok = await core.request<{ v: number }>(spec);
		expect(calls()).toBe(2);
		expect(ok).toEqual({ v: 3 });
	});

	it('TTL expiry · ttl 경과 후 재요청 시 fetchFn 2 회', async () => {
		const { fetchFn, calls } = countingFetch({ v: 4 });
		let t = 0;
		const core = createDataCore({ fetchFn, now: () => t });
		const spec = {
			origin: 'hf' as const,
			path: 'ttl.json',
			parse: jsonParse,
			cacheKey: 'k-ttl',
			cache: { scope: 'memory' as const, ttlMs: 1000, maxEntries: 8 }
		};

		await core.request<{ v: number }>(spec); // t=0 set, expiresAt=1000
		expect(calls()).toBe(1);

		t = 1500; // 만료(expiresAt < now)
		await core.request<{ v: number }>(spec);
		expect(calls()).toBe(2);
	});

	it("scope 'none' · 매 호출 refetch", async () => {
		const { fetchFn, calls } = countingFetch({ v: 5 });
		const core = createDataCore({ fetchFn, now: () => 0 });
		const spec = {
			origin: 'hf' as const,
			path: 'none.json',
			parse: jsonParse,
			cacheKey: 'k-none',
			dedup: false as const, // 순차 호출이 in-flight 공유 없이 매번 새로 실행되도록.
			cache: { scope: 'none' as const, ttlMs: 0 }
		};

		await core.request<{ v: number }>(spec);
		await core.request<{ v: number }>(spec);
		await core.request<{ v: number }>(spec);

		expect(calls()).toBe(3);
	});
});
