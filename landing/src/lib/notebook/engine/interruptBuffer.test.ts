import { afterEach, describe, expect, it, vi } from 'vitest';
import { isSharedInterruptBuffer } from './interruptBuffer';

describe('isSharedInterruptBuffer', () => {
	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it('SharedArrayBuffer 전역이 없는 일반 페이지에서는 false를 반환한다', () => {
		vi.stubGlobal('SharedArrayBuffer', undefined);
		expect(isSharedInterruptBuffer(null)).toBe(false);
	});

	it('공유 버퍼만 소프트 인터럽트 대상으로 인정한다', () => {
		if (typeof SharedArrayBuffer !== 'function') return;
		expect(isSharedInterruptBuffer(new Uint8Array(new SharedArrayBuffer(1)))).toBe(true);
		expect(isSharedInterruptBuffer(new Uint8Array(new ArrayBuffer(1)))).toBe(false);
	});
});
