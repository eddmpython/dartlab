import { describe, expect, it } from 'vitest';

import { isAssignment, wrapLastExpression } from './lastExpression';

const wrapped = (code: string) => wrapLastExpression(code).includes('__eddmlab_result__');

describe('isAssignment', () => {
	it('괄호 안 키워드 인자를 대입으로 오인하지 않는다', () => {
		// 이것이 셀 출력을 통째로 삼키던 회귀. 옛 정규식 `^[a-zA-Z_]\w*[\[.].*=` 가 여기서 참을 냈다.
		expect(isAssignment('c.select("IS", ["매출액"], freq="Y")')).toBe(false);
		expect(isAssignment('c.select("IS", ["매출액"], freq="Y").df')).toBe(false);
		expect(isAssignment('c.panel("BS", scope="separate").shape')).toBe(false);
		expect(isAssignment('f(a=1, b=2)')).toBe(false);
	});

	it('진짜 대입은 대입이다', () => {
		expect(isAssignment('x = 1')).toBe(true);
		expect(isAssignment('x += 1')).toBe(true);
		expect(isAssignment('x: int = 5')).toBe(true);
		expect(isAssignment('d["k"] = 1')).toBe(true);
		expect(isAssignment('obj.attr = 2')).toBe(true);
		expect(isAssignment('a, b = 1, 2')).toBe(true);
		expect(isAssignment('bs = c.panel("BS")')).toBe(true);
	});

	it('비교 연산과 walrus 는 대입이 아니다', () => {
		expect(isAssignment('x == y')).toBe(false);
		expect(isAssignment('x != y')).toBe(false);
		expect(isAssignment('x >= y')).toBe(false);
		expect(isAssignment('x <= y')).toBe(false);
		expect(isAssignment('lambda x=1: x')).toBe(false);
	});

	it('따옴표와 주석 안의 = 는 세지 않는다', () => {
		expect(isAssignment('print("a = b")')).toBe(false);
		expect(isAssignment('c.market   # KR 이면 DART, US 면 EDGAR')).toBe(false);
	});
});

describe('wrapLastExpression', () => {
	it('마지막 식을 결과로 잡는다', () => {
		expect(wrapped('c.market')).toBe(true);
		expect(wrapped('import dartlab\nc = dartlab.Company("005930")\nc.panel("IS").head(3)')).toBe(true);
		expect(wrapped('c.select("IS", ["매출액"], freq="Y")')).toBe(true);
	});

	it('마지막 줄이 문이면 건드리지 않는다', () => {
		expect(wrapped('x = 1')).toBe(false);
		expect(wrapped('import dartlab')).toBe(false);
		expect(wrapped('for i in range(3):\n    print(i)')).toBe(false);
		expect(wrapped('c.market  # 주석만 남은 줄이 아니다')).toBe(true);
		expect(wrapped('# 주석뿐')).toBe(false);
	});

	it('결과 변수는 마지막 줄만 바꾼다', () => {
		const out = wrapLastExpression('a = 1\nb = 2\na + b');
		expect(out).toContain('a = 1\nb = 2\n__eddmlab_result__ = a + b');
	});
});
