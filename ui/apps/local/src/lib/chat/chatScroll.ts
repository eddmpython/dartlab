// 대화 스크롤 고정 판정. DOM 을 모르는 순수 함수로 두어 규칙을 시험할 수 있게 한다.
//
// 왜 분리했나. 옛 구현은 반응 효과 안에서 메시지 수와 마지막 part 의 길이를 손으로 읽어
// 재실행을 유도했다. 그 목록은 높이가 느는 경로를 다 담지 못한다. 표가 렌더되거나 도구
// 결과가 도착하거나 지연 렌더가 끝날 때도 높이는 늘어나는데 그때는 메시지 수도 텍스트
// 길이도 변하지 않는다. 그래서 실제 크기 변화를 관찰하는 쪽으로 옮기고, 판정은 여기 둔다.

/** 하단 근접으로 볼 여유. 이 안이면 사용자가 최신을 보고 있다고 본다. */
export const NEAR_BOTTOM_PX = 120;

export interface ScrollGeometry {
	scrollTop: number;
	scrollHeight: number;
	clientHeight: number;
}

/** 바닥까지 남은 거리. 음수가 나오지 않게 0 에서 자른다. */
export function distanceFromBottom(geometry: ScrollGeometry): number {
	return Math.max(0, geometry.scrollHeight - geometry.scrollTop - geometry.clientHeight);
}

/** 사용자가 최신을 보고 있는가. 여기가 참이면 새 내용이 와도 따라 내려도 된다. */
export function isNearBottom(geometry: ScrollGeometry, threshold: number = NEAR_BOTTOM_PX): boolean {
	return distanceFromBottom(geometry) <= threshold;
}

/**
 * "최신으로" 알약을 띄울 것인가.
 *
 * 위로 올라간 사용자에게만 띄운다. 바닥에 있는 사람에게 띄우면 화면만 가린다.
 * 내용이 화면보다 짧으면 스크롤 자체가 없으므로 띄우지 않는다.
 */
export function shouldShowJumpToLatest(geometry: ScrollGeometry, threshold: number = NEAR_BOTTOM_PX): boolean {
	if (geometry.scrollHeight <= geometry.clientHeight) return false;
	return !isNearBottom(geometry, threshold);
}
