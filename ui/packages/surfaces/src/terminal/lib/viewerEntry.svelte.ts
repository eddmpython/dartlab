// 터미널 cross-panel 신호 · 중앙 "공시뷰어" 버튼(CenterStack)이 우측 ViewerOverlay(RightStack)를
// 전체화면으로 연다. 두 패널은 형제라 직접 prop 전달이 안 돼, module-level rune store 의 pulse 로 신호한다.
// counter 패턴: 구독측이 seen 값과 비교만 하므로 자기-clear 반응 루프가 없다.
export const viewerEntry = $state({ pulse: 0 });

/** 공시뷰어 전체화면 열기 요청 · RightStack 이 pulse 변화를 구독해 ViewerOverlay 를 연다. */
export function requestViewer(): void {
	viewerEntry.pulse += 1;
}
