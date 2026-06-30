// 공시 레일 ↔ 우측 공시 패널 클릭 동기화 신호 · 주가차트 하단 공시 dot 클릭 시, 우측 정기/비정기
// 공시 목록에서 그 "날짜" 행을 스크롤·하이라이트한다(원문 링크 이동이 아니라 위치 찾기). CenterStack(차트)과
// RightStack(공시목록)은 형제라 직접 prop 전달이 안 돼, module-level rune store 의 pulse 로 신호한다.
// counter 패턴: 구독측(RightStack)이 seen pulse 와 비교만 하므로 자기-clear 반응 루프가 없다(viewerEntry 동일).
export const disclosureFocus = $state<{ date: string; pulse: number }>({ date: '', pulse: 0 });

/** 그 날짜(YYYYMMDD)로 우측 공시 패널을 스크롤·하이라이트하도록 요청 · 같은 날짜 재클릭도 pulse 증가로 재발화. */
export function focusDisclosure(date: string): void {
	disclosureFocus.date = date;
	disclosureFocus.pulse += 1;
}
