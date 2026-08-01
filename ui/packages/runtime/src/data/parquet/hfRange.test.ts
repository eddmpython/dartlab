import { describe, expect, it } from 'vitest';
import { HfReadError, isHfNotFound } from './hfRange';

// 404(원천 미존재)와 그 밖의 실패를 호출측이 갈라야 안내 문구가 갈린다.
// 공시뷰어에서 정기보고서를 제출하지 않는 종목(집합투자기구 등)이 404 로 오는데,
// 이것을 "로드 실패" 로 뭉뚱그리면 원천 부재가 우리 버그로 읽힌다.
describe('HfReadError', () => {
	it('message 는 기존 포맷을 유지한다 (문자열 소비처 하위호환)', () => {
		const e = new HfReadError('dart/panel/088980.parquet', 404, 'range probe 실패');
		expect(e.message).toBe('dart/panel/088980.parquet range probe 실패: 404');
		expect(e.path).toBe('dart/panel/088980.parquet');
		expect(e.status).toBe(404);
		expect(e).toBeInstanceOf(Error);
	});
});

describe('isHfNotFound', () => {
	it('404 만 true', () => {
		expect(isHfNotFound(new HfReadError('a.parquet', 404, 'range probe 실패'))).toBe(true);
	});

	it('그 밖의 상태는 false (재시도 여지가 있는 실패)', () => {
		for (const status of [403, 429, 500, 502, 503]) {
			expect(isHfNotFound(new HfReadError('a.parquet', status, '전체 읽기 실패'))).toBe(false);
		}
	});

	it('HfReadError 가 아닌 값은 false', () => {
		expect(isHfNotFound(new Error('a.parquet range probe 실패: 404'))).toBe(false);
		expect(isHfNotFound('404')).toBe(false);
		expect(isHfNotFound(null)).toBe(false);
		expect(isHfNotFound(undefined)).toBe(false);
	});
});
