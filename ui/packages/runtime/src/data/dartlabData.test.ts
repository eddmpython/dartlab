import { describe, expect, it } from 'vitest';
import { HF_RESOLVE, loadJson, setStaticBase } from './dartlabData';

describe('loadJson public policy wiring', () => {
	it('퍼블릭 JSON은 화면 호출 옵션 없이 HF 최신본을 먼저 읽는다', async () => {
		const urls: string[] = [];
		const fetchFn = (async (input: RequestInfo | URL) => {
			urls.push(String(input));
			return new Response(JSON.stringify({ source: 'hf' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			});
		}) as typeof fetch;

		const value = await loadJson<{ source: string }>('map/policy-wiring-test.json', { fetchFn });

		expect(value).toEqual({ source: 'hf' });
		expect(urls).toEqual([`${HF_RESOLVE}/landing/map/policy-wiring-test.json`]);
	});

	it('HF 실패 때만 같은 정책의 정적 폴백을 사용한다', async () => {
		setStaticBase('/dartlab');
		const urls: string[] = [];
		const fetchFn = (async (input: RequestInfo | URL) => {
			const url = String(input);
			urls.push(url);
			if (url.startsWith(HF_RESOLVE)) return new Response(null, { status: 503 });
			return new Response(JSON.stringify({ source: 'local' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			});
		}) as typeof fetch;

		const value = await loadJson<{ source: string }>('map/policy-fallback-test.json', { fetchFn });

		expect(value).toEqual({ source: 'local' });
		expect(urls).toEqual([
			`${HF_RESOLVE}/landing/map/policy-fallback-test.json`,
			'/dartlab/map/policy-fallback-test.json'
		]);
	});
});
