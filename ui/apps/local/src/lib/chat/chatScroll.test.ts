import { describe, expect, it } from 'vitest';
import { distanceFromBottom, isNearBottom, shouldShowJumpToLatest } from './chatScroll';

/**
 * 스크롤 고정 판정은 DOM 없이 시험할 수 있어야 한다. 옛 구현은 반응 효과 안에서 메시지 수와
 * 마지막 part 길이를 손으로 읽어 재실행을 유도했고, 그 목록이 표 렌더처럼 높이만 느는 경로를
 * 통째로 놓쳤다. 규칙을 순수 함수로 떼어 두면 그 종류의 누락이 시험 대상이 된다.
 */
const geometry = (scrollTop: number, scrollHeight: number, clientHeight: number) => ({
	scrollTop,
	scrollHeight,
	clientHeight
});

describe('chatScroll', () => {
	it('바닥에 붙어 있으면 남은 거리가 0 이다', () => {
		expect(distanceFromBottom(geometry(900, 1500, 600))).toBe(0);
	});

	it('반올림 오차로 음수가 나와도 0 으로 자른다', () => {
		expect(distanceFromBottom(geometry(900.4, 1500, 600))).toBe(0);
	});

	it('여유 안이면 최신을 보고 있다고 본다', () => {
		expect(isNearBottom(geometry(820, 1500, 600))).toBe(true);
		expect(isNearBottom(geometry(700, 1500, 600))).toBe(false);
	});

	it('위로 올라간 경우에만 알약을 띄운다', () => {
		expect(shouldShowJumpToLatest(geometry(200, 1500, 600))).toBe(true);
		expect(shouldShowJumpToLatest(geometry(900, 1500, 600))).toBe(false);
	});

	it('내용이 화면보다 짧으면 스크롤이 없으므로 띄우지 않는다', () => {
		expect(shouldShowJumpToLatest(geometry(0, 400, 600))).toBe(false);
	});
});
