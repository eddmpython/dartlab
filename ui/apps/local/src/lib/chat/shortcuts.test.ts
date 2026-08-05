import { describe, expect, it } from 'vitest';
import { actionForEvent, modLabel, shortcutLabel, SHORTCUTS } from './shortcuts';

/**
 * 라벨과 실제 바인딩이 어긋난 안내는 없느니만 못하다. 표 하나에서 둘 다 나오는지 고정한다.
 */
const press = (key: string, mods: Partial<Record<'ctrlKey' | 'metaKey' | 'shiftKey' | 'altKey', boolean>> = {}) => ({
	key,
	ctrlKey: false,
	metaKey: false,
	shiftKey: false,
	altKey: false,
	...mods
});

describe('shortcuts', () => {
	it('mac 은 Command, 그 외는 Control 을 mod 로 쓴다', () => {
		expect(actionForEvent(press('j', { metaKey: true }), 'MacIntel')).toBe('newChat');
		expect(actionForEvent(press('j', { ctrlKey: true }), 'MacIntel')).toBeNull();
		expect(actionForEvent(press('j', { ctrlKey: true }), 'Win32')).toBe('newChat');
		expect(actionForEvent(press('j', { metaKey: true }), 'Win32')).toBeNull();
	});

	it('라벨이 플랫폼에 따라 바뀐다', () => {
		expect(modLabel('MacIntel')).toBe('Cmd');
		expect(modLabel('Win32')).toBe('Ctrl');
		const newChat = SHORTCUTS.find((item) => item.action === 'newChat');
		expect(newChat).toBeDefined();
		expect(shortcutLabel(newChat!, 'Win32')).toBe('Ctrl+J');
	});

	it('Alt 가 섞인 조합은 우리 것이 아니다', () => {
		expect(actionForEvent(press('j', { ctrlKey: true, altKey: true }), 'Win32')).toBeNull();
	});

	it('mod 없는 맨 글자는 가로채지 않는다', () => {
		expect(actionForEvent(press('j'), 'Win32')).toBeNull();
	});

	it('표의 모든 동작이 서로 다른 조합을 쓴다', () => {
		const combos = SHORTCUTS.map((item) => `${item.mod}:${Boolean(item.shift)}:${item.key}`);
		expect(new Set(combos).size).toBe(SHORTCUTS.length);
	});

	it('표의 라벨이 비어 있지 않다', () => {
		for (const spec of SHORTCUTS) {
			expect(spec.label.trim().length).toBeGreaterThan(0);
			expect(shortcutLabel(spec, 'Win32')).toMatch(/^Ctrl\+/);
		}
	});
});
