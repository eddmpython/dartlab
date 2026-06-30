// 터미널 cross-panel 신호 · 우측 레일 도시에 섹션(인력·주주환원)의 '상세보기'가 중앙 FinFullscreen 을
// 특정 탭(people·shareholder)으로 연다. 형제 패널(RightStack↔CenterStack)은 직접 prop 전달이 안 돼,
// module-level rune store 의 pulse 로 신호한다(viewerEntry 동일 패턴 · 구독측 seen 비교라 자기-clear 루프 없음).
export const finFullEntry = $state({ pulse: 0, tab: 'all' });

/** FinFullscreen 전체화면을 특정 탭으로 열기 요청 · CenterStack 이 pulse 변화를 구독해 연다. */
export function requestFinFull(tab: string): void {
	finFullEntry.tab = tab;
	finFullEntry.pulse += 1;
}
