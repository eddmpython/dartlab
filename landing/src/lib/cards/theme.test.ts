// AccentText 헬퍼 · 기존 SNS 캐러셀 AccentText.tsx 와 동일 규약(`[[구절]]`=강조).
import { describe, it, expect } from 'vitest';
import { accentParts, stripDots } from './theme';

describe('accentParts · [[구절]] 강조 분해', () => {
	it('마커 안은 accent, 밖은 일반', () => {
		expect(accentParts('본업 [[현금]]이 받친다')).toEqual([
			{ text: '본업 ', accent: false },
			{ text: '현금', accent: true },
			{ text: '이 받친다', accent: false }
		]);
	});
	it('마커 없으면 통째로 일반', () => {
		expect(accentParts('강조 없음')).toEqual([{ text: '강조 없음', accent: false }]);
	});
	it('빈/널 안전', () => {
		expect(accentParts('')).toEqual([]);
	});
});

describe('stripDots · 줄 끝 마침표 제거(소수점·쉼표 보존)', () => {
	it('줄 끝 마침표만 제거', () => {
		expect(stripDots('판매량보다 이익률 방어가 질문입니다.')).toBe('판매량보다 이익률 방어가 질문입니다');
	});
	it('줄별로 처리(여러 줄)·쉼표는 유지', () => {
		expect(stripDots('질문입니다.\n많이 파는 회사인지,\n비싸게 남기는 회사인지 봅니다.')).toBe(
			'질문입니다\n많이 파는 회사인지,\n비싸게 남기는 회사인지 봅니다'
		);
	});
	it('소수점·천단위는 줄 중간이라 보존', () => {
		expect(stripDots('판매 대수는 77만 9,741대였습니다.')).toBe('판매 대수는 77만 9,741대였습니다');
		expect(stripDots('영업이익률 7.5%')).toBe('영업이익률 7.5%');
	});
	it('빈/널 안전', () => {
		expect(stripDots('')).toBe('');
		expect(stripDots(undefined as unknown as string)).toBe('');
	});
});
